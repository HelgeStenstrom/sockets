#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Fungerar i python3.

# From https://docs.python.org/3/library/socket.html#example

# TODO: läs http://stackoverflow.com/questions/31864168/mocking-a-socket-connection-in-python

"""
Mimic a Vötsch climate chamber, such as it appears on the local IP network.
"""

import argparse
# Echo server program
import socket
import socketserver
from abc import abstractmethod, ABCMeta


class MyTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        print("{} wrote:".format(self.client_address[0]))
        print(self.data)
        # just send back the same data, but upper-cased
        self.request.sendall(self.data.upper())


class socketInstrument(metaclass=ABCMeta):
    def __init__(self):
        self.port = 2049

    @abstractmethod
    def responseFunction(self, command):
        pass

    def theSocket(self):
        # TODO: flytta till en annan klass, så att den här klassen bara handlar om in-och utdata från Vötsch
        HOST = ''  # Symbolic name meaning all available interfaces
        PORT = self.port  # Vötsch standard port. According to Wikipedia, it's usually used for nfs.
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))
            s.listen(1)
            conn, addr = s.accept()
            with conn:
                print('Connected by', addr, "\n")
                while True:
                    data = conn.recv(1024)
                    receivedCommand = data.decode('utf-8')
                    print("Received: ", receivedCommand.strip(), "")
                    if not data: break
                    response = bytes(self.responseFunction(data.decode('utf-8')) + '\r\n', 'utf-8')
                    conn.sendall(response)

        print("Socket is shut down or closed. Please restart.")


class vötschBySocket(socketInstrument):
    def __init__(self):
        super(vötschBySocket, self).__init__()
        self.temp = 27.1
        self.CcType = 'Vc'

    def setTempActual(self, temp):
        self.temp = temp

    def format(self, x):
        return "%06.1f " % x

    def responseFunction(self, command):
        command = command.strip()
        if command.startswith("$01I"):
            # Depending on Vötsch model, the format is different.
            # Vt 3 7060: n = 14
            # Vc 3 7060: n = 12
            n = {'Vc': 12, 'Vt': 14}[self.CcType]
            response = self.format(self.temp) + "0019.8 " + n * "0000.1 " + 32 * "0" + "\r"
            return response
        elif command.startswith("$01?"):
            return "ASCII description of the protocol"
        elif command.startswith("$01E"):
            # print("Received command '", command[:-1], "'\n")
            return ""
        else:
            return "'" + command + "' is an unknown command."


class RotaryDiscBySocket(socketInstrument):
    def __init__(self):
        super(RotaryDiscBySocket, self).__init__()
        self.idnString = "innco GmbH,CO3000,9711016,1.02.62"

    def format(self, x):
        return "%06.1f " % x

    def responseFunction(self, command):
        command = command.strip()
        if command.upper() ==( "*IDN?"):
            response = self.idnString
            return response
        elif command.startswith("$01?"):
            return "ASCII description of the protocol"
        elif command.startswith("$01E"):
            return ""
        else:
            return "'" + command + "' is an unknown command."


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    parser.add_argument('CcType', help='Type of Vötsch model', choices=['Vc', 'Vt', 'RotaryDisc'])
    args = parser.parse_args()

    if args.CcType in ['Vc', 'Vt']:
        attachedInstrument = vötschBySocket()
        attachedInstrument.CcType = args.CcType

    elif args.CcType in ['RotaryDisc']:
        attachedInstrument = RotaryDiscBySocket()

    else:
        raise NotImplementedError

    attachedInstrument.theSocket()


if __name__ == '__main__':
    main()
