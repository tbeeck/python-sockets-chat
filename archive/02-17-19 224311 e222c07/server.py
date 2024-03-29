#!/usr/bin/env python3

import socket, threading, re
from queue import Queue

HOST = '127.0.0.1'
PORT = 8555

g_clientList = list()
g_clientDict = dict()
g_msgQueue = Queue()
lock_clientList = threading.Lock()
lock_clientDict = threading.Lock()
lock_msgQueue = threading.Lock()

def verifyNick(nick):
    if ':' not in nick:
        return True
    return False

def enqueueMessage(msg):
    lock_msgQueue.acquire()
    g_msgQueue.put(msg.encode())
    lock_msgQueue.release()

def handleCommand(cmd, sock):
    nick, command = re.match(r'(.+): /(.+)', cmd).groups()

    print('Received command {} from {}'.format(command, nick))

    # Commands
    if command == 'hello':
        lock_clientDict.acquire()
        g_clientDict[nick] = sock
        lock_clientDict.release()
        enqueueMessage('{} has connected!'.format(nick))

def client_thread(sock, address, nick):
    while True:
        msg = sock.recv(1024).decode()
        if len(msg) is 0: # Detect abrupt disconnect
            break
        print(address, ' ', msg)

        # The / of a command should be 2 characters right of :
        if len(msg) == len(nick) + 3 and msg[msg.index(':') + 2] is '/':
            handleCommand(msg, sock)
            continue

        enqueueMessage(msg)

    sock.send('\nGoodbye!'.encode())
    sock.close()
    # lock_clientList.acquire()
    # g_clientList.remove(sock)
    # print('Removed {} from clientList'.format(sock))
    # lock_clientList.release()
    lock_clientDict.acquire()
    g_clientDict.pop(nick)
    lock_clientDict.release()
    print('Removed {} from clientDict'.format(nick))
    return 0

def broadcast_thread():
    # Send all enqueued messages to each client
    while True:
        while not g_msgQueue.empty():
            lock_msgQueue.acquire()
            msg = g_msgQueue.get()
            lock_msgQueue.release()

            # lock_clientList.acquire()
            # for client in g_clientList:
            #     client.send(msg)
            # lock_clientList.release()
            lock_clientDict.acquire()
            for key, sock in g_clientDict.items():
                sock.send(msg)
            lock_clientDict.release()

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
        #Accept connections from within while loop
        conn, address = s.accept() 
        conn.settimeout(3)
        try:
            nick = conn.recv(1024).decode()
            if not verifyNick(nick):
                raise Exception('Invalid nickname: {}'.format(nick))
        except Exception as ex:
            print(ex)
            conn.close()
            continue

        conn.settimeout(None)
        conn.send('OK'.encode()) # Send OK signal
        # print('Waiting for handshake from: {}'.format(address))
        # lock_clientList.acquire()
        # g_clientList.append(conn)
        # lock_clientList.release()
        lock_clientDict.acquire()
        g_clientDict[nick] = conn
        lock_clientDict.release()
        # Start a thread for the client.
        t1 = threading.Thread(target=client_thread, args=(conn, address, nick))
        t1.start()


if __name__ == '__main__':
    server()