#!/usr/bin/env python3
from multiprocessing import Process, Queue
import socket as sk
import json


SERVER_ADDRESS = "127.0.0.1"
PORT = 37863

def can_interface_process():
    with sk.socket(sk.AF_INET, sk.SOCK_STREAM) as s:
        s.connect((SERVER_ADDRESS, PORT))
        try:
            data = s.recv(1024)
            print("Il server ha chiesto \"{}\"".format(data.decode("utf-8")))
            while True:
                x = input("Inserire i dati da inviare al server\n")
                if x == "fine":
                    break
                else:
                    s.sendall(bytes(x, "UTF-8"))
        except ConnectionError or ConnectionResetError:
            print("La connessione è stata interrotta prematuramente")

def web_interface_process():
    with sk.socket(sk.AF_INET, sk.SOCK_STREAM) as s:
        s.connect((SERVER_ADDRESS, PORT))
        try:
            data = s.recv(1024)
            print("Il server ha chiesto \"{}\"".format(data.decode("utf-8")))
            while True:
                x = input("Inserire i dati da inviare al server\n")
                if x == "fine":
                    break
                elif x == "WEB_SERVER":
                    s.sendall(bytes(x, "UTF-8"))
                else:
                    recipient = "AAAAABBBBCCCC DDDD"
                    command = {"recipient": recipient, "command": x}
                    command_json = json.dumps(command)
                    print("Sent {}".format(command_json))
                    s.sendall(bytes(command_json, "UTF-8"))
        except ConnectionError or ConnectionResetError:
            print("La connessione è stata interrotta prematuramente")


if __name__ == "__main__":
    """
    web_to_can_queue = Queue()
    can_to_web_queue = Queue()
    print("AVVIO PROCESSI")
    can_process = Process(target=can_interface_process, args=(web_to_can_queue, can_to_web_queue))
    #web_process = Process(target=web_interface_process, args=(can_to_web_queue, web_to_can_queue))
    can_process.daemon = True
    can_process.start()
    #web_process.start()
    #web_process.join()
    while True:
        x = input("Inserire il comando da rete-socket\n")
        if x == "fine":
            web_to_can_queue.put("END")
            break
        else:
            web_to_can_queue.put(x)
    can_process.join()
    print("TUTTI I PROCESSI CONCLUSI. Scrittura coda inviata dal CAN")
    while not can_to_web_queue.empty():
        print(can_to_web_queue.get())
    """
    can_interface_process()

