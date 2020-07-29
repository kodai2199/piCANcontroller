import os
from threading import Thread
import time
import json
import logging

# TODO: logging
import django


class ConnectedClient:

    COMMAND_ID = "WEB_SERVER"
    COMMAND_END = "WEB_CLOSE"

    def __init__(self, connection, address, queue):
        # Prepare django
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "website.settings")
        django.setup()
        from app.models import Installation

        # Initialize parameters
        self.connection = connection
        self.address = address
        self.queue = queue
        self.id = None
        self.is_command_server = False
        self.Installation = Installation

        # Ask for identity
        if not self.identify():
            raise ConnectionError()

        # Run appropriate worker
        if self.is_command_server:
            self.command_server_worker()
        else:
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
            print("{} closed the connection or did not provide and ID.".format(self.address))
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
            if client_id == self.COMMAND_ID:
                self.is_command_server = True
                print("{} is a Command Server.".format(self.address))
            else:
                print("{} is a Raspberry Pi.".format(self.address))
            self.id = client_id
        except ConnectionError:
            print("Could not identify {}.".format(self.address))
            return False
        return True

    def command_server_worker(self):
        # Django command server process
        # If the client has been recognized to be a Command Server,
        # we can now listen for the commands. A generous 5 seconds
        # timeout is given. The connection can be closed after
        # any amount of commands gracefully by sending <COMMAND_END>

        # Commands
        while True:
            try:
                # Get and decode the command
                self.send("COMMAND_SUPPLICANT")
                command_json = self.receive(5)
                command = json.loads(command_json)

                # Prepare the command to be sent on queue
                recipient = command["recipient"]
                message = command["command"]
                command = (recipient, message)

                print("Adding {} to the command queue".format(command))
                # Put the command on the queue
                self.queue.put(command)
            except ConnectionError:
                print("Command Server {} did not send any more commands.".format(self.address))
                break

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
                print("RPi {} did not reply to GET_INFO.".format(self.address))
                break

            # Phase b: check if the queue contains a command for this
            # RPi and execute it
            try:
                tasks = list(self.queue.queue.queue)
                print("{} tasks scheduled.".format(len(list)))
            except ConnectionError:
                print("RPi {} did not receive the last command sent.".format(self.address))
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








