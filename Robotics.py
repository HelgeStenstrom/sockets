import math
import re
import time

from socketInstrument import SocketInstrument


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


class SubDevice:
    def __init__(self, name):
        self.name = name
        self.busy = False


class OneRotaryDisc(SubDevice):
    def __init__(self, name, slowDown=0):
        super().__init__(name)
        self.currentPosition = 0
        self.startPosition = 0
        self.speedInDegPerSecond = 4.9
        self.speed = 3
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


class AntennaStand(SubDevice):
    def __init__(self, name):
        super().__init__(name)
        self.polarization = "H"

    def setPolarization(self, p):
        if p not in ['V', 'H']:
            raise ValueError
        self.polarization = p

    def getPolarization(self):
        return self.polarization


class MaturoNCD(SocketInstrument):

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
        try:
            return "%.0f" % self.currentDevice.speedInDegPerSecond
        except AttributeError:
            return "E - V"

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

    def PH_response(self):
        dev = self.currentDevice
        if isinstance(dev, AntennaStand):
            dev.polarization = "H"
            return ""
        else:
            return "E - V"

    def PV_response(self):
        dev = self.currentDevice
        if isinstance(dev, AntennaStand):
            dev.polarization = "V"
            return ""
        else:
            return "E - V"

    def P_response(self):
        try:
            pol = self.currentDevice.polarization
            assert pol in ["H", "V"]
            if pol == "V":
                return "1"
            return "0"
        except AttributeError:
            return "E - V"

    @staticmethod
    def badCommand():
        return "E - x"

    patterns_to_select_command = {
        # Just enough to recognize which command is being sent. Extraction of values is done in other places.
        "en re": "vad den matchar",
        "\*IDN\?": Idn_response,
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
        "LD [-]?\d+(\.\d+)? SP": LD_SP_response,
        "PH": PH_response,
        "PV": PV_response,
        "P\?": P_response
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
            try:
                return command(self)
            except AttributeError:
                return "E - V"
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

        # Unit tests rely on devices 1 and 3 being RotaryDiscs, and 0 an AntennaStand.
        self.devNamesToAttach = ['3', '1', '0']
        self.attachedDevices = [OneRotaryDisc('1'), OneRotaryDisc('3'), AntennaStand('0')]
        self.command = ""
        self.offset = 0
        self.farDistance = 10
        self.maxTries = 5
        self.triesCount = 0
        # self.limit_clockwise = 90
        # self.limit_anticlockwise = -90
        self.currentDevice = self.attachedDevices[2]


class Optimus(SocketInstrument):

    def __init__(self):
        self.x, self.y, self.phi, self.theta = (None, None, None, None)
        self.xStatus, self.yStatus, self.phiStatus, self.thetaStatus = (0, 0, 0, 0)
        self.sensorPower = 0
        self.motorPower = 0
        self.command = None
        self.vendor = "Ericsson"
        self.model = "Optimus"
        self.serial = "123"
        self.firmwareRevision = "PA1"
        super().__init__()

    def Idn_response(self):
        # idnString = ','.join([self.vendor, self.model, self.serial, self.firmware])
        idnString = self.vendor + ', ' + self.model + ', ' + self.serial + ', ' + self.firmwareRevision
        return idnString

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
        return "%d, %d, %.1f (%d), %.1f (%d), %.1f (%d), %.1f (%d)" % (self.sensorPower, self.motorPower,
                                                                       self.x, self.xStatus, self.y, self.yStatus,
                                                                       self.phi, self.phiStatus, self.theta,
                                                                       self.thetaStatus)

    def zeroResponse(self):
        # TODO: Remove, not present in Optimus.
        self.x, self.y, self.phi, self.theta = (0, 0, 0, 0)
        return "ack"

    def xToResponse(self):
        self.x = self.numberFromCommand(self.command)
        return "ok"

    def yToResponse(self):
        self.y = self.numberFromCommand(self.command)
        return "ok"

    def phiToResponse(self):
        self.phi = self.numberFromCommand(self.command)
        return "ok"

    def thetaToResponse(self):
        self.theta = self.numberFromCommand(self.command)
        return "ok"

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
        "move_x_to [-]?\d+(\.\d+)?": xToResponse,
        "move_y_to [-]?\d+(\.\d+)?": yToResponse,
        "rotate_phi_to [-]?\d+(\.\d+)?": phiToResponse,
        "rotate_theta_to [-]?\d+(\.\d+)?": thetaToResponse,
        "\*IDN\?": Idn_response,
        "status": statusResponse
    }
