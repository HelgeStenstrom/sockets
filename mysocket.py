#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import time

class mysocket:
    '''demonstration class only
      - coded for clarity, not efficiency
    '''

    def __init__(self, sock=None):
        if sock is None:
            self.sock = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock

    def connect(self, host, port):
        self.sock.connect((host, port))

    def mysend(self, msg):
        totalsent = 0
        while totalsent < MSGLEN:
            sent = self.sock.send(msg[totalsent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent

    def myreceive(self):
        chunks = []
        bytes_recd = 0
        while bytes_recd < MSGLEN:
            chunk = self.sock.recv(min(MSGLEN - bytes_recd, 2048))
            if chunk == '':
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
        return ''.join(chunks)


class myServer:

    def __init__(self):
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serversocket.bind(socket.gethostname(), 7432)
        self.serversocket.listen(5)

    def listen(self):
        while True:
            (clientsocket, address) = self.serversocket.accept()
            ct = client_thread(clientsocket)
            ct.run()


def usesocket(s):
    while True:
        s.mysend("The medium is the message.")
        time.sleep(0.2)
    

MSGLEN = 5
ms = mysocket()
ms.connect('localhost', 80)
usesocket()
