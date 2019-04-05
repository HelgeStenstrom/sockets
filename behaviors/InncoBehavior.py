import re
import time

from behaviors.Behaviors import OneRotaryDisc
from socketInstrument import SocketInstrument


class InncoBehavior(SocketInstrument):

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
        "\*IDN\?": Idn_response,
        "\*OPT\?": OPT_response,
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