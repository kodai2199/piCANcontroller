#!/usr/bin/env python3
from multiprocessing import Process
from threading import Thread
import socket as sk
from datetime import datetime
from pathlib import Path
import logging
from server.connectedclient import ConnectedClient
import os
import django


class AppSocketServer(Thread):
    """
    Terminology:
        - <CODE>: a simple string to identify the client
        - <QUEUE>: a multiprocessing.Queue for every command sent
        from the web interface to the RPi. Since there are
        multiple RPis and connections, the content of the queue
        is a tuple ("recipient", "message").

    This class allows communication between the django server and the
    Raspberry Pi clients. The basic idea is that this server will
    always be running as a separate thread.

    As soon as Raspberry Pis (RPis) are connected
    to the Internet, they must establish a connection with this
    server. Since the RPis may not have a public IP address, they
    need to start the connection, and the connection must be always
    active in order to send commands from the web interface to them
    without using some sort of polling. If a connection to a RPi is
    lost, then it must be showed on the web interface, as commands
    cannot be sent.

    Every time a client establishes a connection, the following
    communication protocol is used:

    1) The server sends a "ID_SUPPLICANT" command.

    2) The client sends a specific <ID>. If the client is a RPi,
       the <ID> must be the IMEI of it's GSM SIM.
       This allows to identify the client and what needs to be done
       next. If the IMEI is not in the Installations list, then a
       new record is created. This allows client-server
       auto-configuration.

    3) If the client is a RPi, a loop will start:
        a) The server sends "GET_INFO" and waits for the RPi
           to send updated data about its installation. As soon as
           the server receives that data, it will be used to update
           the Installation model.

        b) The server reads from the database for Commands.
           If something can be read, the command is sent to the RPi
           and the element is removed from the db.

    This is implemented with the help of ConnectedClient.
    """

    def __init__(self, host="", port=37863):
        """
        The constructor intializes all the variables, including the
        logger.

        :param host:
        :param port:
        """
        super(AppSocketServer, self).__init__()
        now = datetime.now()
        directory = Path("logs/")
        filename = now.strftime("%Y-%m-%d_%H-%M-%S")
        filename += "_server.log"
        filename = directory / filename
        logging.basicConfig(level=logging.DEBUG, filename=filename,
                            format="[%(asctime)s][%(levelname)s] %(message)s")
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Logger ready")
        self.logger.info('Socket server started')
        print("Socket server started")

        # Configure parameters
        self.host = host
        self.port = port

    def listen_for_connections(self) -> None:
        """
        Creates a socket and listens for connections on it. When a
        client connects, the identification and all the other
        phases are delegated to self.connection_process, started as a
        separated Process. Every process is marked as daemonic so that
        no process are left hanging if the programs terminates.

        :return: None
        """
        with sk.socket(sk.AF_INET, sk.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            while True:
                s.listen()
                self.logger.info("Socket server listening for a new connection")
                con, addr = s.accept()
                self.logger.info("New connection from {}. Launching process.".format(addr))
                with con:
                    p = Process(target=self.connection_process, args=(con, addr))
                    p.daemon = True
                    p.start()

    @staticmethod
    def set_all_offline() -> None:
        """
        Sets the "online" field of every Installation to "offline".
        This should be used only at startup, to clear any possible
        error caused by Installations not being properly set as
        offline when the program terminated last time.
        :return: None
        """
        # Set all the installations as "offline" to ensure
        # a correct startup
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "website.settings")
        django.setup()
        from app.models import Installation

        matching_count = Installation.objects.filter(online=True).count()
        if matching_count > 0:
            i = Installation.objects.get(online=True)
            i.online = False
            i.save()

    def connection_process(self, connection: sk.socket, address) -> None:
        """
        A method that delegates all the client management to the
        ConnectedClient class. It takes care of returning in case of
        errors.

        :param connection: a socket object with the TCP connection to
            the client.
        :param address: the address of the connected client, as
            returned by socket.accept()
        :return:
        """
        self.logger.info("Process for {} started. Identifying client.".format(address))
        try:
            c = ConnectedClient(connection, address)
        except ConnectionError:
            self.logger.warning("Connection error. Process for {} terminating.".format(address))
            return
        self.logger.debug("Process for {} terminating.".format(address))

    def run(self) -> None:
        """
        To be called via Process.start(). Sets all the Installation
        as offline and start listening for connections.
        :return:
        """
        self.set_all_offline()
        self.listen_for_connections()
