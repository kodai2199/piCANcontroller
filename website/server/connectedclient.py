import os
from threading import Thread
import time
import json
import logging
import django
import socket as sk


class ConnectedClient:
    """
    This class represents one of the connected RPis. Every RPi should
    have an instance of ConnectedClient. A ConnectedClient object
    takes a socket connection and the address of the RPi and manages
    every communication with the RPi, from the identification to
    command sending. Since many concurrent RPi will try to connect
    it is best to launch a ConnectedClient instance in a separate
    process, as no interaction with the parent process is needed.

    Please note that this class relies on django's ORM to deal with
    Installations and Commands.
    """

    def __init__(self, connection: sk.socket, address):
        """
        The constructor initializes all the variables and prepares the
        django ORM, and the logger. Then, it asks the client to
        identify itself. If it doesn't identify successfully then
        a ConnectionError is raised, otherwise the installation is
        initialized (and a record created if none was present with the
        provided IMEI) and worker method is started.

        When the worker method returns (mainly for connection errors),
        the Installation is set as offline and the ConnectedClient
        terminates.

        :param connection: A socket object holding the TCP connection
              with the RPi client.
        :param address: The address of the RPi client as returned by
            socket.accept()
        """
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "website.settings")
        django.setup()
        from app.models import Installation, Command

        # Initialize parameters
        self.connection = connection
        self.address = address
        self.id = None
        self.logger = logging.getLogger(f'{__name__}.{self.address}')
        self.is_command_server = False
        self.Installation = Installation
        self.Command = Command

        # Ask for identity
        if not self.identify():
            raise ConnectionError()

        self.initialize_installation()
        self.raspberry_pi_worker()
        # If this point is reached, it means the RPi closed the
        # connection. So the corresponding value must be set
        # to "offline"
        i = self.Installation.objects.get(imei=self.id)
        i.online = False
        i.save()

    def send(self, message):
        """
        Encodes the message and sends it. If a problem happens,
        the connection is closed.

        :param message: The message to encode and send
        :return: True if message was successfully sent, False otherwise
        """
        # Encode and send the message
        try:
            self.logger.debug(f"Sending {message} to {self.address}")
            data = message.encode()
            self.connection.send(data)
        except ConnectionError:
            self.logger.error(f"Could not send data to {self.address}")
            self.connection.close()
            raise ConnectionError()
        except:
            self.logger.error(f"Critical error while sending data to {self.address}")
            self.connection.close()
            raise ConnectionError()

    def receive_thread(self, buffer_size, data):
        """
        This function is meant to be used as a separate thread, to
        implement a reliable timeout for socket.recv. It just calls
        socket.recv with the specified buffer_size and puts it
        in to the first position of the given list. If an unknown
        error happens, the connection is shut down.

        :param buffer_size: The buffer size for the recv call. Usually
            it's 1024 bytes.
        :param data: A list. This needs to be a mutable object so
            that it's synchronized with the parent thread, and it
            can receive information.
        :return: None
        """
        try:
            data[0] = self.connection.recv(buffer_size)
        except ConnectionError or ConnectionAbortedError:
            pass
        except:
            self.logger.error(f"Critical error while receiving data from {self.address}")
            self.connection.close()
            raise ConnectionError()

    def receive(self, timeout=0, buffer_size=1024):
        """
        Listens for data on the connection and decodes it. Optional
        parameters are timeout and buffer_size, which may be
        customized to make the function behave as necessary. In
        order to implement a reliable timeout for socket.recv, the
        call is wrapped in a thread. If it doesn't return before the
        timeout mark, then the thread is terminated by closing the
        connection and the function returns.

        :param timeout: Time in seconds to wait before closing the
                        connection if no data is sent. Timeout = 0
                        is default and means no timeout.
        :param buffer_size: The buffer size in bytes. Default is 1024
                            and should not be changed unless
                            necessary.
        :return:
        """
        data = [None]
        rec_thread = Thread(target=self.receive_thread, args=(buffer_size, data))
        rec_thread.daemon = True
        rec_thread.start()

        timer = 0
        if timeout > 0:
            while timer <= timeout:
                if not (data[0] is None):
                    break
                time.sleep(1)
                timer += 1
            if timer > timeout:
                self.connection.close()
                raise ConnectionAbortedError()
        else:
            rec_thread.join()

        data = data[0]
        if not data or data is None:
            self.logger.warning(f"{self.address} closed the connection or did not send anything before timeout")
            raise ConnectionAbortedError()
        else:
            # Data should be an array of bytes!
            message = data.decode("UTF-8")
            self.logger.debug(f"{self.address} sent {bytes(message, 'utf-8')}")
            return message

    def identify(self):
        """
        To be called only during handshake to identify the client. If
        used when the connection is already estabilished the function
        will return true immediately.

        At first "ID_SUPPLICANT" is sent. Then the reply is decoded
        and assigned to self.id.

        IMPORTANT Note that the IMEI is not perfectly checked.
                Any string with 15 or more digits will work!

        :return: True if client was successfully identified, False
                otherwise.
        """
        if self.id is not None:
            return True
        # Send a "ID_SUPPLICANT" and use the reply to identify the client
        try:
            self.send("ID_SUPPLICANT")
            # The client has up to one second to respond
            client_id = self.receive(2)
            if client_id.isdigit() and len(client_id) >= 15:
                self.id = client_id
                self.logger.info(f"{self.address} is a Raspberry Pi with IMEI {self.id}.")
            else:
                self.logger.error(f"{self.address} tried to identify with an invalid IMEI."
                                  " Closing connection")
                raise PermissionError(f"{self.address} tried to identify with an invalid IMEI."
                                      " Closing connection")
        except ConnectionError:
            self.logger.warning(f"Could not identify {self.address}.")
            return False
        return True

    def raspberry_pi_worker(self) -> None:
        """
        Process that handles an alive connection with a Raspberry Pi.
        The process is a simple loop:
        a) the server sends "GET_INFO" and waits for the RPi to send
           updated data about its installation. As soon as the
           server receives that data, it will be used to update the
           Installation instance. If no data has to be updated, then
           the server wil wait for a second before going to b).

        b) the server checks the Command instance with the
           corresponding IMEI. If there are any commands, they are
           sent to the client. The command will be considered
           "executed" only if the client answers with "OK".
           If no commands are found, then the server will
           wait a second before returning to point a).

        :return:
        """
        while True:
            # Phase a: Update information about installation
            try:
                self.send("GET_INFO")
                info = self.receive(5)
                # To reduce data usage, we will reply NO_UPDATE or NU (to save data) if
                # the data sent on the last GET_INFO is still valid
                if info != "NO_UPDATE" and info != "NU":
                    info = json.loads(info)
                    i = self.Installation.objects.get(imei=self.id)
                    # Only update elements that changed, and were
                    # included the reply
                    for key, value in info.items():
                        setattr(i, key, value)
                    i.save()
            except ConnectionError:
                self.logger.warning(f"RPi {self.id} did not reply to GET_INFO.")
                break
            # Phase b) check if the database contains a command for
            # this RPi and execute it
            try:
                self.logger.debug("Checking command queue for imei {}.".format(self.id))
                matching_commands = self.Command.objects.filter(imei=self.id)
                matching_commands_count = matching_commands.count()

                # Command found
                if matching_commands_count > 0:
                    matching_command = self.Command.objects.get(imei=self.id)
                    self.logger.info(matching_command.command_string)
                    self.send(matching_command.command_string)
                    message = self.receive(5)
                    if message == "OK":
                        self.logger.info(f"{self.id} completed execution of {matching_command.command_string}")
                        matching_command.delete()
                else:
                    # If no commands are found, wait before checking
                    # again.
                    time.sleep(1)
            except ConnectionError:
                self.logger.warning(f"RPi {self.address} did not receive the last command sent or did not reply to it.")
                print(f"RPi {self.address} did not receive the last command sent or did not reply to it.")
                break

    def initialize_installation(self) -> None:
        """
        Set the Installation with the given IMEI as online. If no
        Installation with such IMEI exists, create a new one first.

        :return: None
        """
        # If the given ID (IMEI) exists in the database,
        # just set the Installation to appear as "online",
        # else create a new record.
        matching_installations = self.Installation.objects.filter(imei=self.id)
        if matching_installations.count() == 0:
            i = self.Installation(imei=self.id, online=True)
        else:
            i = self.Installation.objects.get(imei=self.id)
            i.online = True
        i.save()








