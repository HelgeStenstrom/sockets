#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Helge Stenström 2016, 2017, 2018

# Needs Python3.

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

from abc import abstractmethod, ABCMeta
import Communicator


class SocketInstrument(metaclass=ABCMeta):
    def __init__(self):
        self.port = 2049  # Should be overridden by subclass.
        self.responseEOL = "\r"
        self.communicator = Communicator.SocketCommunicator(self.responseFunction)

    @abstractmethod
    def responseFunction(self, command):
        pass


def toPrintable(stringWithControlChars):
    result = ""
    for char in stringWithControlChars:
        if char == '\r':
            result += '<CR>'
        elif char == '\n':
            result += '<LF>'
        else:
            result += char
    return result
