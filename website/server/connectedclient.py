import os
from threading import Thread
import time
import json
import logging
import django


class ConnectedClient:

    def __init__(self, connection, address):
        # Prepare django
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "website.settings")
        django.setup()
        from app.models import Installation, Command

        # Initialize parameters
        self.connection = connection
        self.address = address
        self.id = None
        self.is_command_server = False
        self.Installation = Installation
        self.Command = Command

        # Ask for identity
        if not self.identify():
            raise ConnectionError()

        # Run appropriate worker
        self.initialize_installation()
        self.raspberry_pi_worker()
        # If this point is reached, it means the RPi closed the
        # connection. So the corresponding value must be set
        # to "offline"
        i = self.Installation.objects.get(imei=self.id)
        i.online = False
        i.save()

    def send(self, message):
        # Encode and send the message
        try:
            print("Sending {} to {}".format(message, self.address))
            data = bytes(message, "UTF-8")
            self.connection.send(data)
        except ConnectionError:
            print("Could not send data to {}".format(self.address))
            self.connection.close()
            raise ConnectionError()

    def receive_thread(self, buffer_size, data):
        # A simple wrapper for socket.recv to allow
        # thread execution and exception silencing
        try:
            data[0] = self.connection.recv(buffer_size)
        except ConnectionError:
            pass

    def receive(self, timeout=0, buffer_size=1024):
        # In order to implement reliable timeout for socket.recv,
        # the call is wrapped in a thread. If it doesn't return before
        # the timeout mark, then the thread is terminated by
        # closing the connection and the function returns.

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
            print("{} closed the connection or did not send anything before timeout".format(self.address))
            raise ConnectionAbortedError()
        else:
            message = data.decode("UTF-8")
            print("{} sent {}".format(self.address, message))
            return message

    def identify(self):
        # Send a "ID_SUPPLICANT" and use the reply to identify the client
        try:
            self.send("ID_SUPPLICANT")
            # The client has up to two seconds to respond
            client_id = self.receive(2)
            self.id = client_id
            print("{} is a Raspberry Pi with IMEI {}.".format(self.address, self.id))
        except ConnectionError:
            print("Could not identify {}.".format(self.address))
            return False
        return True

    def raspberry_pi_worker(self):
        # Raspberry process
        # If the client has been recognized to be a Raspberry Pi,
        # a loop will start:
        # a) The server sends "GET_INFO" and waits for the RPi
        #    to send updated data about its installation. As soon as
        #    the server receives that data, it will be used to update
        #    the Installation model.

        while True:
            # Phase a: Update informations about installation
            try:
                self.send("GET_INFO")

                # Two seconds are enough
                info_json = self.receive(2)

                # To reduce data usage, we will reply NO_UPDATE if
                # the data sent on the last GET_INFO is still valid
                #info = json.loads(info_json)
                print(info_json)
            except ConnectionError:
                print("RPi {} did not reply to GET_INFO.".format(self.id))
                break
            # Phase b: check if the database contains a command for
            # this RPi and execute it
            try:
                matching_commands = self.Command.objects.filter(imei=self.id)
                matching_commands_count = matching_commands.count()

                # Command found
                if matching_commands_count > 0:
                    # Getting command
                    matching_command = self.Command.objects.get(imei=self.id)
                    print(matching_command.command_string)

                    # Sending command
                    self.send(matching_command.command_string)

                    # Waiting for the reply
                    # It may take some time for the raspberry Pi to
                    # complete the command so more time will be left
                    message = self.receive(10)
                    if message == "OK":
                        print("{} completed execution of {}".format(self.id, matching_command.command_string))
                else:
                    # If no commands are found, wait before checking
                    # again
                    time.sleep(1)
            except ConnectionError:
                print("RPi {} did not receive the last command sent or did not reply to it.".format(self.address))
                break

    def initialize_installation(self):
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








