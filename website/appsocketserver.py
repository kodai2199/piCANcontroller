from multiprocessing import Process, Queue
import socket as sk
from datetime import datetime
from pathlib import Path
import logging
from server.connectedclient import ConnectedClient
import os
import django

class AppSocketServer:
    """
    Terminology:
        - <CODE>: a simple string to identify the client
        - <QUEUE>: a multiprocessing.Queue for every command sent
        from the web interface to the RPi. Since there are
        multiple RPis and connections, the content of the queue
        is a tuple ("recipient", "message").

    This class allows communication between the django server and the
    Raspberry Pi clients. The basic idea is that this server will
    always be running. As soon as Raspberry Pis (RPis) are connected
    to the Internet, they must establish a connection with this
    server. Since the RPis may not have a public IP address, they
    need to start the connection, and the connection must be always
    active in order to send commands from the web interface to them
    without using some sort of polling. In order for the django server
    to send commands, however, it also needs to connect to this socket
    server. The main difference is that the django server only needs
    to be connected to send the command, and can then disconnect,
    while the RPis cannot disconnect. If a connection to a RPi is
    lost, then it must be showed on the web interface, as commands
    cannot be sent.

    Every time a client establishes a connection, the following
    communication protocol is used:

    1) The server sends a "ID_SUPPLICANT" command.

    2) The client sends a specific <ID>. If the client is a RPi,
       the <ID> must be the IMEI of it's GSM SIM else, if the client
       is the django server itself, <ID> will be <COMMAND_ID>.
       This allows to identify the client and what needs to be done
       next. If the IMEI is not in the Installations list, then a
       new record is created. This allows client-server
       auto-configuration.

    3.DJANGO) If the client is the django server, it has to send the
     command. The command will then be unpacked and added to the
     <QUEUE> of pending commands. Commands have to be sent following
     JSON encoding

    3.RPi) If the client is a RPi, a loop will start:
        a) The server sends "GET_INFO" and waits for the RPi
           to send updated data about its installation. As soon as
           the server receives that data, it will be used to update
           the Installation model.

        b) The server reads from the <QUEUE>, with a timeout of one
        second. If the timeout is reached, the loop restarts from a).
        If something can be read from <QUEUE>, it will be checked if
        the recipient is equal to the IMEI of this RPi. If it is,
        then the command is sent to the RPi and the element is removed
        from the <QUEUE>.

    4.DJANGO) The client disconnects.

    This is implemented with the help of ConnectedClient
    """

    HOST = "127.0.0.1"
    PORT = 37863

    def __init__(self, host=None, port=None):
        print("Socket server started")

        # Set all the installations as "offline" to ensure
        # a correct startup
        matching_count = Installation.objects.filter(online=True).count()
        if matching_count > 0:
            i = Installation.objects.get(online=True)
            i.online = False
            i.save()

        # Configure parameters
        self.HOST = host or self.HOST
        self.PORT = port or self.PORT

        # Prepare logger
        now = datetime.now()
        directory = Path("logs/")
        filename = now.strftime("%Y-%m-%d_%H-%M-%S")
        filename += "_app.log"
        filename = directory/filename
        logging.basicConfig(level=logging.DEBUG, filename=filename, format="[%(asctime)s][%(levelname)s] %(message)s")
        logging.debug("Logger ready")

        # Prepare the queue
        q = Queue()
        print("QUEUE:")
        print(list(q.queue))

        # Prepare the socket
        connection_counter = 0
        with sk.socket(sk.AF_INET, sk.SOCK_STREAM) as s:
            s.bind((self.HOST, self.PORT))
            while True:
                s.listen()
                logging.debug("Socket server listening for a new connection")
                con, addr = s.accept()
                connection_counter += 1
                logging.info("New connection from {}. Launching process.".format(addr))
                with con:
                    p = Process(target=self.connection_process, args=(con, addr, q))
                    p.daemon = True
                    p.start()

    def connection_process(self, connection, address, queue):
        logging.debug("Process for {} started. Identifying client.".format(address))
        try:
            c = ConnectedClient(connection, address, queue)
        except ConnectionError:
            logging.debug("Connection error. Process for {} terminating.".format(address))
            return
        logging.debug("Process for {} terminating.".format(address))


if __name__ == "__main__":
    # Prepare django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "website.settings")
    django.setup()
    from app.models import Installation
    ss = AppSocketServer()