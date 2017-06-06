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
# import socketserver
from abc import abstractmethod, ABCMeta
import time
import math


class SocketInstrument(metaclass=ABCMeta):
    def __init__(self):
        self.port = 2049  # Vötsch standard port. According to Wikipedia, it's usually used for nfs.

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
                    if not data:
                        break
                    r = self.responseFunction(data.decode('utf-8'))
                    response = bytes(r + '\r\n', 'utf-8')
                    print("Sent:     %s" % r)
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

    @staticmethod
    def format(x):
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
        self.vendor = "innco GmbH"
        self.model = "CO3000"
        self.serial = "python"
        self.firmware = "1.02.62"
        self.currentPosition = 0
        self.startPosition = 0
        self.speedInDegPerSecond = 4.9
        self.busy = False
        self.devices = ['AS1', 'DS1']
        self.command = ""
        self.targetPosition = 1
        self.movementStartTime = time.time()

    def Idn_response(self):
        idnString = ','.join([self.vendor, self.model, self.serial, self.firmware])
        return idnString

    def OPT_response(self):
        return ','.join(self.devices)

    def startMovement_response(self):
        command = self.command
        assert command != ""
        self.startPosition = self.currentPosition
        self.busy = True
        self.targetPosition = self.numberFromInncoCommand(command)
        self.movementStartTime = time.time()
        return str(self.targetPosition)

    def movementDurationSoFar(self):
        return time.time() - self.movementStartTime

    def isBusy(self):
        "business"
        return self.busy

    def BU_Response(self):
        "business"
        self.updatePositionAndBusiness()
        if self.busy:
            return "1"
        else:
            return "0"

    def CP_response(self):
        "current position"
        self.updatePositionAndBusiness()
        return "%.1f" % self.currentPosition

    def NSP_response(self):
        "new numeric speed"
        self.speedInDegPerSecond = self.numberFromInncoCommand(self.command)
        return str(self.speedInDegPerSecond)

    @staticmethod
    def badCommand():
        return "E - x"

    def signedSpeed(self):
        return math.copysign(1, self.targetPosition - self.startPosition) * self.speedInDegPerSecond

    def updatePositionAndBusiness(self):
        elapsed = self.movementDurationSoFar()
        dist = elapsed * self.speedInDegPerSecond
        distToTravel = self.currentPosition - self.targetPosition
        if self.isBusy():
            if dist > abs(distToTravel):
                self.currentPosition = self.targetPosition
                self.busy = False
            else:
                self.currentPosition = self.startPosition + self.signedSpeed() * elapsed

    patterns_to_select_command = {
        "en re": "vad den matchar",
        "\*IDN\?":   Idn_response,
        "\*OPT\?":   OPT_response,
        "CP": CP_response,
        "LD [-]?\d+(\.\d+)? NP GO": startMovement_response,
        "(\ )*BU(\ )*": BU_Response,
        "LD [-]?\d+(\.\d+)? NSP": NSP_response
    }

    def matchOf(self, commandString):
        rePatterns = self.patterns_to_select_command.keys()
        for p in rePatterns:
            if re.search(p, commandString):
                return self.patterns_to_select_command[p]
        return "no match"

    def getIdnString(self):
        idnString = self.vendor + ',' + self.model + ',' + self.serial + ',' + self.firmware
        return idnString

    def finalizeMovement(self):
        assert self.targetPosition is not None
        self.currentPosition = self.targetPosition
        self.busy = False

    def responseFunction(self, command):
        command = command.strip()
        for rePattern in self.patterns_to_select_command:
            if re.search(rePattern, command):
                self.command = command
                func = self.patterns_to_select_command[rePattern]
                return func(self)
        return self.badCommand()

    @staticmethod
    def numberFromInncoCommand(s):
        "Extract a number from a command string such as 'LD -123.4 NP GO'. "

        # All relevant Innco Commands seem to have the number at the second position.
        words = s.split()
        return float(words[1])


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    parser.add_argument('CcType', help='Type of instrument or Vötsch model', choices=['Vc', 'Vt', 'RotaryDisc'])
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
