from socketInstrument import SocketInstrument


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