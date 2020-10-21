import time
from multiprocessing import Process
from threading import Thread


def p1():
    while True:
        time.sleep(1)
        print('process p1 writing')


def p2():
    newp = Process(target=p1)
    newp.daemon = True
    newp.start()
    while True:
        time.sleep(1)
        print('process p2 writing')

if __name__ == '__main__':
    p = Thread(target=p2)
    p.daemon = True
    p.start()
    while True:
        x = input('Inserire qualcosa: ')
        print(f"L'utente ha scritto {x}");
        if x == "exit":
            break