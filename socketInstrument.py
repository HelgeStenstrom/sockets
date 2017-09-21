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

import argparse
import re
import socket
# import socketserver
from abc import abstractmethod, ABCMeta
import time
import math


class Instrument:
    # TODO: hitta på unit test för det här. Just nu är idéerna ganska vaga.
    # Tanken är att klassen inte ska innehålla kod för både specifikt instrument
    # och för socket eller annat transportlager, inte ens i en basklass.
    # Istället ska transporter och/eller konkret instrument läggas till
    # som objektattribut.
    # Målet är att kunna använda koden som modellerar ett instrument i unit tests,
    # utan att blanda in transportlagret.

    # Åtminstone med Socket, så är det transportlagret som anropar
    # instrumentsimulatorn (respons-funktionen), och inte tvärt om.
    # Därför kan man ersätta transportlagret med ett enklare, och testa att
    # responsfunktioner blir anropade.

    def __init__(self, transporter):
        self.transporter = transporter


class SocketInstrument(metaclass=ABCMeta):
    def __init__(self):
        self.port = 2049  # Vötsch standard port. According to Wikipedia, it's usually used for nfs.

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
            conn, addr = s.accept()
            with conn:
                print('Connected by', addr, "\n")
                while True:
                    data = conn.recv(1024)
                    try:
                        receivedCommand = data.decode('utf-8')
                    except UnicodeDecodeError:
                        break
                    receivedText = receivedCommand.strip()
                    # assert '\r' not in receivedText
                    print("Received: '%s'" % prettify(receivedText))
                    if not data:
                        print("Received empty command")
                        break
                    r = self.responseFunction(data.decode('utf-8'))
                    response = bytes(r + '\r\n', 'utf-8')

                    # TODO: unit test this behavior, which is new. Only send a response if there is one.
                    # Don't send empty responses.
                    if r:
                        print("Sent:     '%s' (length: %d)" % (r, len(response)))
                        conn.sendall(response)

        print("Socket is shut down or closed. Please restart.")


class PaRsBBA150(SocketInstrument):
    def __init__(self):
        super().__init__()
        self.port = 5025  # According to R&S manual

    def responseFunction(self, command):
        command = command.strip()

        if command.upper() == "*IDN?":
            return "Rohde & Schwarz,simulated BBA150,102044,SW:01.96,FPGA:01.05"

        elif command.upper() == "SENS:NFR?":
            return "2600000000,5900000000"

        elif command.upper() == "UNIT:POW DBM":
            return ""

        elif command.upper() == "SENS:NPOW?":
            return "47.7"

        elif command.upper() == "SYST:ERR?":
            return "Simulated error"

        elif command.upper() == "CONT1:AMOD:FGA?":
            return "47.7"

        elif command[-1] == "?":
            return "example BBS150 response value for '%s'" % command
        else:
            return ""


class PaEmpower(SocketInstrument):
    def __init__(self):
        super().__init__()
        self.port = 5025  # According to R&S manual, guessing Empower has the same.
        self.gain = 0
        self.mode = "VVA"
        self.active = False

    def responseFunction(self, command):
        command = command.strip()

        if command == "IN?":
            return "BBS3G6QHM"
        elif command == "IM":
            return " Empower RF Systems, Inc."

        elif command == "IS?":
            return "4711"

        elif command == "IV?":
            return "4.2"

        elif command == "G?":
            return "%i" % self.gain*100

        elif command.startswith("G"):
            g = int(float(command[1:]))
            self.gain = g/100.0
            print("Gain is %d * 0.01 dB = %g dB." % (g, self.gain))
            return ""

        elif command == "MA":
            print("Setting mode to ALC")
            self.mode = "ALC"
            return ""

        elif command == "MV":
            print("Setting mode to VVA")
            self.mode = "VVA"
            return ""

        elif command == "MS":
            print("Standby")
            self.active = False
            return ""

        elif command == "MO":
            print("Active")
            self.active = True
            return ""

        elif command == "M?":
            if self.mode == "VVA":
                return "VOA"
            elif self.mode == "ALC":
                return "AOA"
            else:
                raise Exception

        return "Default Empower response value"


class votschBySocket(SocketInstrument):
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

    # DONE: implementera NSP
    # DONE: implementera LD # NSP
    # DONE: implementera att förställa målvärde från kommandoraden

    def Idn_response(self):
        idnString = ','.join([self.vendor, self.model, self.serial, self.firmware])
        return idnString

    def OPT_response(self):
        deviceNames = [dev.name for dev in self.attachedDevices]
        return ','.join(deviceNames)

    def LD_NP_GO_response(self):
        command = self.command
        assert command != ""
        cd = self.currentDevice
        cd.startPosition = cd.currentPosition
        cd.busy = True
        normalTarget = self.numberFromInncoCommand(command)
        adjust = self.adjustment(normalTarget)
        cd.targetPosition = normalTarget + adjust
        cd.movementStartTime = time.time()
        return str(normalTarget)

    def adjustment(self, normalTarget):
        if self.isDistant(normalTarget):
            self.triesCount = 0
            adjust = self.offset
        elif self.triesCount < self.maxTries:
            self.triesCount += 1
            adjust = self.offset
        else:
            adjust = 0
        return adjust

    def isBusy(self):
        """"the whole unit is busy, because one device is."""
        devices = self.attachedDevices
        states = [dev.busy for dev in devices]
        busy = any(states)
        return busy

    def isDistant(self, target):
        distance = abs(target - self.currentDevice.currentPosition)
        return distance > self.farDistance

    def BU_Response(self):
        """"business"""
        self.currentDevice.update()
        if self.isBusy():
            return "1"
        else:
            return "0"

    def CP_response(self):
        """"current position"""
        self.currentDevice.update()
        return "%.1f" % self.currentDevice.currentPosition

    def WL_response(self):
        """"clockwise limit"""
        return "%.1f" % self.currentDevice.limit_clockwise

    def CL_response(self):
        """"anticlockwise limit"""
        return "%.1f" % self.currentDevice.limit_anticlockwise

    def NSP_response(self):
        """"current speed"""
        # self.updatePositionAndBusiness()
        return "%.1f" % self.currentDevice.speedInDegPerSecond

    def LD_NSP_response(self):
        """"new numeric speed"""
        self.currentDevice.speedInDegPerSecond = self.numberFromInncoCommand(self.command)
        return "%.1f" % self.currentDevice.speedInDegPerSecond

    def LD_dev_DV_response(self):
        """"set active device"""
        # For now, this returns a plausible value; the index of the selected device in the attached-device list

        cmd = self.command
        devname = cmd.split()[1]
        self.currentDevice = self.deviceByName(devname)
        return "1"

    @staticmethod
    def badCommand():
        return "E - x"

    patterns_to_select_command = {
        # Just enough to recognize which command is being sent. Extraction of values is done in other places.
        "en re": "vad den matchar",
        "\*IDN\?":   Idn_response,
        "\*OPT\?":   OPT_response,
        "^CP\ *": CP_response,
        "^WL\ *": WL_response,
        "^CL\ *": CL_response,
        "^NSP": NSP_response,
        "LD [-]?\d+(\.\d+)? DG NP GO": LD_NP_GO_response,
        "LD DS. DV": LD_dev_DV_response,  # TODO: regexp som tar olika värden istället för DS1
        "^BU(\ )*": BU_Response,
        "LD [-]?\d+(\.\d+)? NSP": LD_NSP_response
    }

    def commandFor(self, commandString):
        rePatterns = self.patterns_to_select_command
        for rePattern in rePatterns:
            if re.match(rePattern, commandString):
                return self.patterns_to_select_command[rePattern]
        return None  # "no match"

    def responseFunction(self, commandString):
        commandString = commandString.strip()
        command = self.commandFor(commandString)
        if command:
            self.command = commandString
            return command(self)
        return self.badCommand()

    @staticmethod
    def numberFromInncoCommand(s):
        """"Extract a number from a command string such as 'LD -123.4 NP GO'. """

        # All relevant Innco Commands seem to have the number at the second position.
        words = s.split()
        return float(words[1])

    def deviceByName(self, name):
        d = {}
        for dev in self.attachedDevices:
            devName = dev.name
            d[devName] = dev
        return d[name]

    def __init__(self):
        super().__init__()
        self.port = 2049  # Vötsch standard port. According to Wikipedia, it's usually used for nfs.
        # Since we only use GPIB for the Innco RotaryDisc, this port will only be used for development tests
        self.vendor = "innco GmbH"
        self.model = "CO3000"
        self.serial = "python"
        self.firmware = "1.02.62"
        self.devNamesToAttach = ['DS1', 'DS2', 'AS3']
        self.attachedDevices = [OneRotaryDisc(d) for d in self.devNamesToAttach]
        self.command = ""
        self.offset = 0
        self.farDistance = 10
        self.maxTries = 5
        self.triesCount = 0
        self.limit_clockwise = 400
        self.limit_anticlockwise = -120
        self.currentDevice = self.attachedDevices[0]


class OneRotaryDisc:
    def __init__(self, name, slowDown=0):
        self.name = name
        self.currentPosition = 0
        self.startPosition = 0
        self.initialSpeedInDegPerSecond = 4.9
        self.speedInDegPerSecond = self.initialSpeedInDegPerSecond
        self.initialSpeed = 3
        self.speed = self.initialSpeed
        self.busy = False
        self.targetPosition = 1
        self.movementStartTime = time.time()
        self.triesCount = 0
        self.limit_clockwise = 90
        self.limit_anticlockwise = -91
        self.slowDown = slowDown

    def get_currentPosition(self):
        """"current position"""
        self.update()
        return self.currentPosition

    def start_movement(self, target):
        """"start moving a device"""
        self.startPosition = self.currentPosition
        self.targetPosition = target
        self.busy = True

    def update(self):
        slowDown = 0.8
        elapsed = time.time() - self.movementStartTime
        dist = slowDown * elapsed * self.speedInDegPerSecond
        distToTravel = self.startPosition - self.targetPosition
        if self.busy:
            if dist > abs(distToTravel):
                self.currentPosition = self.targetPosition
                self.busy = False
            else:
                self.currentPosition = self.startPosition + slowDown * self.signedSpeed() * elapsed

    def signedSpeed(self):
        return math.copysign(1, self.targetPosition - self.startPosition) * self.speedInDegPerSecond

    def finalizeMovement(self):
        self.currentPosition = self.targetPosition
        self.busy = False


class MaturoNcdBySocket(SocketInstrument):

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

    # DONE: implementera NSP
    # DONE: implementera LD # NSP
    # DONE: implementera att förställa målvärde från kommandoraden

    def Idn_response(self):
        # idnString = ','.join([self.vendor, self.model, self.serial, self.firmware])
        idnString = self.vendor + ',' + self.model + '_' + self.serial
        return idnString

    def LD_NP_GO_response(self):
        command = self.command
        assert command != ""
        cd = self.currentDevice
        cd.startPosition = cd.currentPosition
        cd.busy = True
        normalTarget = self.numberFromInncoCommand(command)
        adjust = self.adjustment(normalTarget)
        cd.targetPosition = normalTarget + adjust
        cd.movementStartTime = time.time()
        return ""

    def adjustment(self, normalTarget):
        if self.isDistant(normalTarget):
            self.triesCount = 0
            adjust = self.offset
        elif self.triesCount < self.maxTries:
            self.triesCount += 1
            adjust = self.offset
        else:
            adjust = 0
        return adjust

    def isBusy(self):
        """"the whole unit is busy, because one device is."""
        devices = self.attachedDevices
        states = [dev.busy for dev in devices]
        busy = any(states)
        return busy

    def isDistant(self, target):
        distance = abs(target - self.currentDevice.currentPosition)
        return distance > self.farDistance

    def BU_Response(self):
        """"business"""
        self.currentDevice.update()
        if self.isBusy():
            return "1"
        else:
            return "0"

    def CP_response(self):
        """"current position"""
        self.currentDevice.update()
        return "%.0f" % self.currentDevice.currentPosition

    def RP_response(self):
        """"current position"""
        self.currentDevice.update()
        return "%.2f" % self.currentDevice.currentPosition

    def WL_response(self):
        """"clockwise limit"""
        return "%.2f" % self.currentDevice.limit_clockwise

    def CL_response(self):
        """"anticlockwise limit"""
        return "%.2f" % self.currentDevice.limit_anticlockwise

    def SP_response(self):
        """"current speed"""
        # self.updatePositionAndBusiness()
        return "%.0f" % self.currentDevice.speedInDegPerSecond

    def ST_response(self):
        self.currentDevice.busy = False
        return ""

    def LD_SP_response(self):
        """"new numeric speed"""
        self.currentDevice.speedInDegPerSecond = self.numberFromInncoCommand(self.command)
        return ""

    def LD_dev_DV_response(self):
        """"set active device"""
        # For now, this returns a plausible value; the index of the selected device in the attached-device list

        cmd = self.command
        devname = cmd.split()[1]
        self.currentDevice = self.deviceByName(devname)
        return ""

    def LD_x_DG_WL_response(self):
        command = self.command
        cd = self.currentDevice
        limit = self.numberFromInncoCommand(command)
        cd.limit_clockwise = limit
        return ""

    def LD_x_DG_CL_response(self):
        command = self.command
        cd = self.currentDevice
        limit = self.numberFromInncoCommand(command)
        cd.limit_anticlockwise = limit
        return ""



    @staticmethod
    def badCommand():
        return "E - x"

    patterns_to_select_command = {
        # Just enough to recognize which command is being sent. Extraction of values is done in other places.
        "en re": "vad den matchar",
        "\*IDN\?":   Idn_response,
        "^CP\ *": CP_response,
        "^RP\ *": RP_response,
        "^WL\ *": WL_response,
        "^CL\ *": CL_response,
        "^SP": SP_response,
        "^ST": ST_response,
        "LD [-]?\d+(\.\d+)? DG NP GO": LD_NP_GO_response,
        "LD [-]?\d+(\.\d+)? DG WL": LD_x_DG_WL_response,
        "LD [-]?\d+(\.\d+)? DG CL": LD_x_DG_CL_response,
        "LD \d DV": LD_dev_DV_response,
        "^BU(\ )*": BU_Response,
        "LD [-]?\d+(\.\d+)? SP": LD_SP_response
    }

    def commandFor(self, commandString):
        rePatterns = self.patterns_to_select_command
        for rePattern in rePatterns:
            if re.match(rePattern, commandString):
                return self.patterns_to_select_command[rePattern]
        return None  # "no match"

    def responseFunction(self, commandString):
        commandString = commandString.strip()
        command = self.commandFor(commandString)
        if command:
            self.command = commandString
            return command(self)
        return self.badCommand()

    @staticmethod
    def numberFromInncoCommand(s):
        """Extract a number from a command string such as 'LD -123.4 NP GO'. """

        # All relevant Innco Commands seem to have the number at the second position.
        words = s.split()
        return float(words[1])

    def deviceByName(self, name):
        d = {}
        for dev in self.attachedDevices:
            devName = dev.name
            d[devName] = dev
        return d[name]

    def __init__(self):
        super().__init__()
        self.port = 2049  # Vötsch standard port. According to Wikipedia, it's usually used for nfs.
        # Since we only use GPIB for the Innco RotaryDisc, this port will only be used for development tests
        self.vendor = "Maturo"
        self.model = "NCD"
        self.serial = "266"
        # self.firmware = "1.02.62"
        self.devNamesToAttach = ['1', '2', '3']
        self.attachedDevices = [OneRotaryDisc(d) for d in self.devNamesToAttach]
        self.command = ""
        self.offset = 0
        self.farDistance = 10
        self.maxTries = 5
        self.triesCount = 0
        # self.limit_clockwise = 90
        # self.limit_anticlockwise = -90
        self.currentDevice = self.attachedDevices[0]


class LundBox(SocketInstrument):

    def __init__(self):
        self.h, self.v, self.t, self.f = (None, None, None, None)
        self.command = None
        super().__init__()


    def commandFor(self, commandString):
        rePatterns = self.patterns_to_select_command
        for rePattern in rePatterns:
            if re.match(rePattern, commandString):
                return self.patterns_to_select_command[rePattern]
        return None  # "no match"

    def responseFunction(self, commandString):
        commandString = commandString.strip()
        command = self.commandFor(commandString)
        if command:
            self.command = commandString
            return command(self)
        return self.badCommand()

    def statusResponse(self):
        return "%.1f, %.1f, %.1f, %.1f" % (self.h, self.v, self.t, self.f)

    def zeroResponse(self):
        self.h, self.v, self.t, self.f = (0, 0, 0, 0)
        return "ack"

    def hToResponse(self):
        self.h = self.numberFromCommand(self.command)
        return "ack"

    def vToResponse(self):
        self.v = self.numberFromCommand(self.command)
        return "ack"

    def tToResponse(self):
        self.t = self.numberFromCommand(self.command)
        return "ack"

    def fToResponse(self):
        self.f = self.numberFromCommand(self.command)
        return "ack"

    @staticmethod
    def badCommand():
        return "nack"

    @staticmethod
    def numberFromCommand(s):
        """Extract a number from a command string such as 'move_h_to -123.4'. """

        # All relevant commands seem to have the number at the second position.
        words = s.split()
        return float(words[1])


    patterns_to_select_command = {
        # Just enough to recognize which command is being sent. Extraction of values is done in other places.
        "en re": "vad den matchar",
        "mv_to_zero": zeroResponse,
        "move_h_to [-]?\d+(\.\d+)?": hToResponse,
        "move_v_to [-]?\d+(\.\d+)?": vToResponse,
        "move_t_to [-]?\d+(\.\d+)?": tToResponse,
        "move_f_to [-]?\d+(\.\d+)?": fToResponse,
        "status": statusResponse
    }


def prettify(unpretty):
    result = ""
    for char in unpretty:
        if char == '\r':
            result += '<CR>'
        elif char == '\n':
            result += '<LF>'
        else:
            result += char
    return result


def main():
    attachedInstrument = instrumentTypeArgument()

    attachedInstrument.theSocket()


def instrumentTypeArgument():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    parser.add_argument('InstrumentType', help='Type of instrument or Vötsch model',
                        choices=['Vc', 'Vt', 'RotaryDisc', 'NCD', 'BBA150', 'Empower', 'Lund'])
    parser.add_argument('--offset', help="How far the used target pos is from the requested one.", type=float)
    args = parser.parse_args()
    if args.InstrumentType in ['Vc', 'Vt']:
        attachedInstrument = votschBySocket()
        attachedInstrument.CcType = args.InstrumentType

    elif args.InstrumentType in ['RotaryDisc']:
        attachedInstrument = RotaryDiscBySocket()
        if args.offset:
            attachedInstrument.offset = args.offset

    elif args.InstrumentType == 'NCD':
        attachedInstrument = MaturoNcdBySocket()

    elif args.InstrumentType in ['BBA150']:
        attachedInstrument = PaRsBBA150()

    elif args.InstrumentType in ['Empower']:
        attachedInstrument = PaEmpower()

    elif args.InstrumentType == "Lund":
        attachedInstrument = LundBox()

    else:
        raise NotImplementedError
    return attachedInstrument


if __name__ == '__main__':
    main()
