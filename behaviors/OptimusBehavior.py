import re

from socketInstrument import SocketInstrument


class OptimusBehavior(SocketInstrument):

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