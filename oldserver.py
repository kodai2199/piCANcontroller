#!/usr/bin/env python3
import socket as sk
from multiprocessing import Process

HOST = "127.0.0.1"
PORT = 37863

def client_connected(con, addr):
    # A client has connected
    # Communication & handshake protocol:
    # 1. The client sends out IMEI (every IMEI must be in the MySQL database or it will be created)
    # 2. The client waits for commands
    # 3. If the command is "GET_INFO" then the client must send updated data about his system
    # 4. If the command is something else then the client will reply with a return code (success or failure)
    # 5. The connection must be always alive, in order for the client to immediately receive commands.

    print("Connesso il client {}".format(addr))
    try:
        while True:
            data = con.recv(1024)
            if not data:
                break
            con.send(bytes("ACK! Ho ricevuto {}".format(data.decode("utf-8")), "UTF-8"))
        print("Il client {} ha terminato la connessione".format(addr))
    except ConnectionError or ConnectionResetError:
        print("La connessione con il client {} è stata terminata in modo anomalo".format(addr))


if __name__ == "__main__":
    # We will use different processes in order to use multiple systems at the same time
    # A reference for each process will be kept in a dictionary that has the IMEI as its key
    processes = []
    with sk.socket(sk.AF_INET, sk.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        while True:
            s.listen()
            print("In ascolto")
            con, addr = s.accept()
            with con:
                client_process = Process(target=client_connected, args=(con, addr))
                client_process.daemon = True
                client_process.start()

