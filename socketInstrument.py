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


# TODO: Skapa Behavior-klass, och flytta instrument-specifika saker dit.

class SocketInstrument(metaclass=ABCMeta):
    def __init__(self):
        self.port = 2049  # Vötsch standard port. According to Wikipedia, it's usually used for nfs.
        self.responseEOL = "\r"

    @abstractmethod
    def responseFunction(self, command):
        pass

    def theSocket(self):
        # DONE: se till att avslutning fungerar snyggare, utan felmeddelanden till terminalen
        # DONE: Se till att en session kan startas direkt efter att föregående har brutits.

        HOST = ''  # Symbolic name meaning all available interfaces
        PORT = self.port
        print("port is ", PORT)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((HOST, PORT))
            s.listen(1)
            while True:
                conn, addr = s.accept()
                print('Connected by', addr, "\n")
                with conn:
                    while True:
                        data = conn.recv(1024)
                        try:
                            receivedCommand = data.decode('utf-8')
                        except UnicodeDecodeError:
                            print("UnicodeDecodeError")
                            continue
                        receivedText = receivedCommand.strip()
                        if not data:
                            print(".", end='', flush=True)
                            time.sleep(0.1) # Sleep for 100 ms before continuing
                            # TODO: See if there is a better way to wait for commands without choking the CPU.
                            break
                        print("Received: '%s'" % toPrintable(receivedText))
                        r = self.responseFunction(data.decode('utf-8'))
                        response = bytes(r + self.responseEOL, 'utf-8') # At least Vötsch doesn't send LF after response string.
                        # TODO: Use a configurable post-response string that can be overridden.

                        # Don't send empty responses.
                        if r:
                            # TODO: Don't print embedded CR characters on the same lime as the length info.
                            print("Sent:     '%s' (length: %d)" % (r.strip(), len(response)))
                            print
                            conn.sendall(response)
                print ("Exited 'with conn'")
            print ("Exited 'while True:' loop")

        print("Socket is shut down or closed. Please restart.")


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
