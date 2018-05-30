#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Helge Stenström 2016-2017

# Fungerar i python3.

# From
# https://docs.python.org/3/library/socket.html#example
# https://docs.python.org/3.3/library/socketserver.html#examples


"""
Mimic an instrument, and let it respond to commands.
Usually instruments are attached by VISA over GPIB or TRP/IP.
Here we use VISA over Socket, to be able to simulate instrument responses to commands.

Implemented instruments:
- Vötsch climate chamber models Vt 3 7060 and Vc 3 7060.
- innco GmbH IN3000 RotaryDisc.
"""

import socket
# import socketserver
from abc import abstractmethod, ABCMeta
import time

import Communicator


# TODO: Skapa Behavior-klass, och flytta instrument-specifika saker dit.

class SocketInstrument(metaclass=ABCMeta):
    def __init__(self):
        self.port = 2049  # Vötsch standard port. According to Wikipedia, it's usually used for nfs.
        self.responseEOL = "\r"
        self.communicator = Communicator.SocketCommunicator(self.responseFunction)

    @abstractmethod
    def responseFunction(self, command):
        pass


def toPrintable(unpretty):
    result = ""
    for char in unpretty:
        if char == '\r':
            result += '<CR>'
        elif char == '\n':
            result += '<LF>'
        else:
            result += char
    return result
