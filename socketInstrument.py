#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Fungerar i python3.

# From
# https://docs.python.org/3/library/socket.html#example
# https://docs.python.org/3.3/library/socketserver.html#examples

# TODO: läs http://stackoverflow.com/questions/31864168/mocking-a-socket-connection-in-python

"""
Mimic an instrument, and let it respond to commands.
Usually instruments are attached by VISA over GPIB or TRP/IP.
Here we use VISA over Socket, to be able to simulate instrument responses to commands.

Implemented instruments:
- Vötsch climate chamber models Vt 3 7060 and Vc 3 7060.
- innco GmbH IN3000 RotaryDisc.
"""

import argparse
import re
# Echo server program
import socket
import socketserver
from abc import abstractmethod, ABCMeta


# class MyTCPHandler(socketserver.BaseRequestHandler):
#     # TODO: varför finns denna klass? Den används ju inte!
#     # Den kommer nog från exempel i https://docs.python.org/3.3/library/socketserver.html#examples
#     def __init__(self):
#         print("This is not unit tested. It's the __init__ function of MyTCPHandler.")
#         # TODO: Ta bort utskrift så fort jag vet när denna klass används.
#         super().__init__()
#         pass
#
#     def handle(self):
#         # self.request is the TCP socket connected to the client
#         self.data = self.request.recv(1024).strip()
#         print("{} wrote:".format(self.client_address[0]))
#         print(self.data)
#         # just send back the same data, but upper-cased
#         self.request.sendall(self.data.upper())


class SocketInstrument(metaclass=ABCMeta):
    def __init__(self):
        self.port = 2049 # Vötsch standard port. According to Wikipedia, it's usually used for nfs.

    @abstractmethod
    def responseFunction(self, command):
        pass

    def theSocket(self):
        HOST = ''  # Symbolic name meaning all available interfaces
        PORT = self.port
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


class vötschBySocket(SocketInstrument):
    def __init__(self):
        super().__init__()
        self.port = 2049  # Vötsch standard port. According to Wikipedia, it's usually used for nfs.
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



class RotaryDiscBySocket(SocketInstrument):

    # Current problems (related to OneTE VisaConnector):

    # The OneTE VisaConnector sends unsupported commands, such as "*SRE 52", "*ESE 61" and "*CLS"
    # They must be handled, or ignored gracefully.

    # The OneTE VisaConnector use OPC (operation complete) functionality.
    # There is something weird with the STB (status byte), causing an error in one of
    # the Query.vi subVIs.

    # Despite the errors, OneTE Query.vi returns a result. This result is the concatenation of several
    # values returned by this driver. We don't want that. We want one result per query.

    # We want to emulate a GPIB-attached instrument. To which extent can that be made, using sockets?
    # It's the same VisaConnector.

    def __init__(self):
        super().__init__()
        self.port = 2049  # Vötsch standard port. According to Wikipedia, it's usually used for nfs.
        # Since we only use GPIB for the Innco RotaryDisc, this port will only be used for development tests
        self.idnString = "innco GmbH,CO3000,python,1.02.62"
        self.vendor = "innco GmbH"
        self.model = "CO3000"
        self.serial = "python"
        self.firmware = "1.02.62"
        self.position = 0
        self.speed = 2
        self.degPerSecond = 4.9
        self.busy = False
        self.devices = ['AS1', 'DS1']
        self.command = ""
        self.targetPosition = None


    def Idn(self):
        idnString = ','.join([self.vendor, self.model, self.serial, self.firmware])
        return idnString

    def Options(self):
        return ','.join(self.devices)

    def startMovement(self):
        command = self.command
        assert command != ""
        self.busy = True
        self.targetPosition = self.numberFromInncoCommand(command)

    def isBusy(self):
        return self.busy

    def badCommand(self):
        return "error message"

    patterns_to_select_command = {
        "en re": "vad den matchar",
        "\*IDN\?" : Idn,
        "\*OPT\?" : Options,
        "CP" : "current position",
        "LD [-]?\d+(\.\d+)? NP GO" : startMovement,
        "(\ )*BU(\ )*" : isBusy
    }

    def matchOf(self, commandString):
        rePatterns = self.patterns_to_select_command.keys()
        for p in rePatterns:
            # print("pattern %s" % p)
            if re.search(p, commandString):
                return self.patterns_to_select_command[p]
        return "no match"

    def getIdnString(self):
        idnString = self.vendor + ',' + self.model + ',' +  self.serial + ',' + self.firmware
        return idnString

    def finalizeMovement(self):
        assert self.targetPosition != None
        self.position = self.targetPosition
        self.busy = False

    def QresponseFunction(self, command):
        command = command.strip()
        # print("got command '%s'" % command)
        if command.upper().startswith( "*IDN?"):
            response = self.getIdnString()
            return response
        else:
            return "'" + command + "' is an unknown command.\n"

    def responseFunction(self, command):
        command = command.strip()
        for rePattern in self.patterns_to_select_command:
            if re.search(rePattern, command):
                self.command = command
                func =  self.patterns_to_select_command[rePattern]
                return func(self)
        return self.badCommand()

    def numberFromInncoCommand(self, s):
        "Extract a number from a command string such as 'LD -123.4 NP GO'. "

        # All relevant Innco Commands seem to have the number at the second position.
        words = s.split()
        return float(words[1])


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
