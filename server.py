#!/usr/bin/env python3

import socket, threading
from queue import Queue

HOST = '127.0.0.1'
PORT = 8555

clientList = list()
msgQueue = Queue()

def client_thread(sock, address):
    while True:
        msg = sock.recv(1024).decode()
        if not msg:
            break
        print(address, " ", msg)

        msgQueue.put(msg.encode())

    sock.close()

def broadcast_thread():
    while True:
        while not msgQueue.empty():
            for client in clientList:
                client.send(msgQueue.get())

def server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print('Starting server at {}'.format(HOST))
    s.bind((HOST, PORT))

    s.listen(5)

    # Open thread to broadcast to connected clients
    broadcastThread = threading.Thread(target=broadcast_thread)
    broadcastThread.start()


    # Accept connections and open a thread for each one
    while True:
        conn, address = s.accept() #Accept connections from within while loop
        print("Connection from: {}".format(address))
        clientList.append(conn)
        t1 = threading.Thread(target=client_thread, args=((conn, address)))
        t1.start() # Start a thread for the client.

    conn.close()


if __name__ == '__main__':
    server()