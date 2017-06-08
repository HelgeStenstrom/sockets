# -*- coding: utf-8 -*-
"""
Created on Tue Feb 21 10:41:04 2017

@author: thomask
"""

import socket
# import io
# import numpy as np
import time
# import sys

"""
Socket communication to the instrument
"""

TCP_IP = '192.168.22.3'
TCP_PORT = 4000
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def Connect():
    global s
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((TCP_IP, TCP_PORT))


def Disconnect():
    global s
    s.close()


def Send(msg):
    global s
    emsg = bytes(msg + "\r\n", "UTF-8")
    s.send(emsg)


def Read(com):
    global s
    Send(com)
    res = s.recv(1024)
    return res


Connect()
for i in range(100):
    t1 = time.perf_counter()
    ret = Read("XPS")
    t2 = time.perf_counter()
    print(ret, "; ", (t2 - t1), " s")
    time.sleep(0.1)
Disconnect()
