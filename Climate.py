from socketInstrument import SocketInstrument
import time


class VotschBase(SocketInstrument):
    def __init__(self):
        super().__init__()
        self.command = None
        self.port = 2049  # Vötsch standard port. According to Wikipedia, it's usually used for nfs.
        self.CcType = 'Vc'
        self.nominalTemp = 0
        self.actualTemperature = 0
        self.nominalHumidity = 0
        self.actualHumidity = 0
        self.fanSpeed = 0
        self.command = None
        self.bits = None
        self.currentWantedTemp = None
        self.tempUp, self.tempDown = 0, 0
        self.humUp, self.humDown = 0, 0
        self.rampStartTime = time.time()
        self.tempStart = self.nominalTemp
        self.chamberTempOffset = 3
        self.startBit = False
        self.humidityBit = False

    def setTempActual(self, temperature):
        self.actualTemperature = temperature

    @staticmethod
    def decimal(x):
        return "%06.1f" % x

    def responseFunction(self, command):
        command = command.strip()
        parts = command.split(" ")
        cmd = parts[0]
        self.command = cmd
        if cmd == "$01I":
            return self.getActualValues()
        elif cmd == "$01?":
            return self.helpText()
        elif cmd == "$01E":
            return self.setTargetsCommand(parts)

        elif cmd == "$01U":
            return self.setSlopeCommand(parts[1:])

        else:
            return "'" + command + "' is an unknown command."

    def getMovingSetpoint(self):
        if self.tempUp == 0 and self.tempDown == 0:
            return self.nominalTemp
        dtime = time.time() - self.rampStartTime
        if self.tempUp > 0:
            dtemp = self.tempUp/60 * dtime
            movingSetpoint = self.tempStart + dtemp
            return min(movingSetpoint, self.nominalTemp)
        if self.tempDown > 0:
            dtemp = - self.tempDown/60 * dtime
            movingSetpoint = self.tempStart + dtemp
            return min(movingSetpoint, self.nominalTemp)
        raise ValueError("Values must be non-negative")

    def getActualValues(self):
        # Depending on Vötsch model, the format is different.
        # Vt 3 7060: n = 14
        # Vc 3 7060: n = 12
        n = {'Vc': 12, 'Vt': 14}[self.CcType]
        # noinspection PyPep8
        response = self.decimal(self.nominalTemp) + " " + \
                   self.decimal(self.actualTemperature) + " " + \
                   n * "0000.1 " + 32 * "0"
        # The calling function theSocket adds + "\r"
        return response

    def chamberTempOffsetFunc(self):
        return self.chamberTempOffset

    # @abstractmethod
    def setTargetsCommand(self, command):
        raise NotImplementedError
        # TODO: Implement Vc and Vt as subclasses. Raising an error or marking method as abstract makes class abstract.

    def setSlopeCommand(self, parameters):
        """Called by the $01U command"""
        if len(parameters) == 4:
            try:
                tu, td, hu, hd = [float(p) for p in parameters]
                if not (tu == 0 or td == 0):  # Only one slope parameter can be active at a time
                    raise ValueError
                if not (hu == 0 or hd == 0):  # Only one slope parameter can be active at a time
                    raise ValueError
                self.tempUp, self.tempDown, self.humUp, self.humDown = tu, td, hu, hd
                self.rampStartTime = time.time()
                return "0"
            except ValueError:
                return ""
        else:
            return ""

    @staticmethod
    def makeBits(temp: bool, humidity: bool) -> str:
        tbit = "1" if temp else "0"
        hbit = "1" if humidity else "0"
        return "0" + tbit + hbit + 29 * "0"

    def helpText(self):
        return """ASCII description of the protocol
Contains multiple lines
        """


class Vc37060(VotschBase):
    """The Vc37060 supports both temperature and humidity.
    The number of parameters of the E-command a I-command are (see help text)
    E-command: 7 decimal numbers, 32 bits
    I-command: 14 decimal numbers, 32 bits
    """

    def __init__(self):
        """Initialize a Vc3 7060 chamber object"""
        super().__init__()
        self.CcType = 'Vc'

    def getActualValues(self):
        # noinspection PyPep8
        pp = [self.getMovingSetpoint(), self.actualTemperature, self.nominalHumidity, self.actualHumidity, self.fanSpeed] \
             + 9*[0]
        values = [self.decimal(part) for part in pp]
        response = " ".join(values) + " " + 32 * "0"
        return response

    def helpText(self):
        # noinspection PyPep8
        return """STANDARD ASCII 2 PROTOCOL FOR E-STRING AND CHAMBERS WITH 2 CONTROLLED VALUES  
EXAMPLE OF AN ASCII E-STRING 
$01E CV01 CV02 SV01 MV01 MV02 MV03 MV04 DO00 DO01 DO02 DO17 DO18 DO19 DO20 DO21 DO22 DO23 DO24 DO25 DO26 DO27 DO28 DO29 DO30 DO31 <CR>

 DESCRIPTION: 
CV01  value min:  -77.0   Value max:  182.0   Temperature 
CV02  value min:    0.0   Value max:  100.0   Humidity 
SV01  value min:   50.0   Value max:  100.0   Fan speed
MV01  0000.0 unused
MV02  0000.0 unused
MV03  0000.0 unused
MV04  0000.0 unused
DO00  unused
DO01  Start
DO02  Humidity
DO03  Custom O1
DO04  Custom O2
DO05  Custom O3
DO06  Custom O4
DO07  Cond.protect
DO08  Clarificat.
DO09  Cap. sensor
DO10  Comp.air/GN2
DO11  Dryer
DO12  Cont. Spec.
DO13  Dewingtest
DO14  Add.humidif.
DO15  Sprinkling
DO16  Clim.-Cycles
DO17  unused
DO18  unused
DO19  unused
DO20  unused
DO21  unused
DO22  unused
DO23  unused
DO24  unused
DO25  unused
DO26  unused
DO27  unused
DO28  unused
DO29  unused
DO30  unused
DO31  unused
EXAMPLE OF A ASCII E-STRING 
$01E 0050.0 0080.0 0090.0 0000.0 0000.0 0000.0 0000.0 01010101010101010101010101010101<CR>

------------------------------------------------------------------------------

STANDARD ASCII 2 PROTOCOL FOR I-STRING AND CHAMBERS WITH 2 CONTROLLED VALUES  
EXAMPLE OF AN ASCII I-STRING 
$01I<CR>
CV01 CV01 CV02 CV02 SV01 SV01 MV01 MV01 MV02 MV02 MV03 MV03 MV04 MV04 DO00 DO01 DO02 DO03 DO04 DO05 DO06 DO07 DO08 DO09 DO10 DO11 DO12 DO13 DO14 DO15 DO16 DO17 DO18 DO19 DO20 DO21 DO22 DO23 DO24 DO25 DO26 DO27 DO28 DO29 DO30 DO31 DESCRIPTION: 
CV01  nominal value Temperature 
CV01  actual value  Temperature 
CV02  nominal value Humidity 
CV02  actual value  Humidity 
SV01  set value     Fan speed
SV01  set value     Fan speed
MV01  unused  	    
MV01  actual value  
MV02  unused  	    
MV02  actual value  
MV03  unused  	    
MV03  actual value  
MV04  unused  	    
MV04  actual value  
DO00  unused
DO01  Start
DO02  Humidity
DO03  Custom O1
DO04  Custom O2
DO05  Custom O3
DO06  Custom O4
DO07  Cond.protect
DO08  Clarificat.
DO09  Cap. sensor
DO10  Comp.air/GN2
DO11  Dryer
DO12  Cont. Spec.
DO13  Dewingtest
DO14  Add.humidif.
DO15  Sprinkling
DO16  Clim.-Cycles
DO17  unused
DO18  unused
DO19  unused
DO20  unused
DO21  unused
DO22  unused
DO23  unused
DO24  unused
DO25  unused
DO26  unused
DO27  unused
DO28  unused
DO29  unused
DO30  unused
DO31  unused
EXAMPLE OF AN ASCII I-STRING 
$01I<CR>
0050.0 0024.6 0080.0 0066.7 0090.0 0090.0 0000.0 0023.8 0000.0 0022.2 0000.0 0025.5 0000.0 0024.4 01100000000000000000000000000000<CR>

        """

    def setTargetsCommand(self, parts):
        self.command = parts[0]

        self.tempStart = self.nominalTemp
        self.nominalTemp = float(parts[1])
        self.actualTemperature = self.nominalTemp + self.chamberTempOffsetFunc()
        self.nominalHumidity = float(parts[2])
        self.actualHumidity = self.nominalHumidity + 5
        self.fanSpeed = float(parts[3])
        # four unused parts
        float(parts[4])
        float(parts[5])
        float(parts[6])
        float(parts[7])
        self.bits = parts[8]
        self.startBit = (self.bits[1] == "1")
        self.humidityBit = (self.bits[2] == "1")

        return "0"

class Vt37060ExtCab(Vc37060):
    """The Vt37060ExtCab is a modified Vt3 7060 with external cabinet. The main chamber
    has two large holes in the side, to which air ducts to the external cabinet can be connected.
    The number of parameters of the E-command a I-command are (see help text)
    E-command: 9 decimal numbers, 32 bits
    I-command: 16 decimal numbers, 32 bits
    """

    # TODO: Verify that all known physical Vt37060ExtCab have the same command syntax
    #

    def __init__(self):
        super().__init__()
        self.extCabinetTempOffset = 0.3
        self.chamberTempOffset = 4.0
        self.actualCabinetTemp = 0

    def getActualValues(self):
        """The I-command response contains the following numbers:
        [0] CV01 nominal chamber temp
        [1] CV01 actual chamber temp
        [2] CV02 nominal external temp 1
        [3] CV02 actual  external temp 1
        [4] CV03 nominal external temp 2
        [5] CV03 actual  external temp 2
        [6] SV01
        [7] SV02
        [8] MV01 unused setpoint
        [9] MV01 not supported
        [10] MV02 unused setpoint
        [11] MV02 not supported
        [12] MV03 unused setpoint
        [13] MV03 not supported
        [14] MV04 unused setpoint
        [15] MV04 not supported
        [16] bits
        """

        parameters = [self.getMovingSetpoint(), self.actualTemperature,
              self.getMovingSetpoint(), self.actualCabinetTemp,
              0, 0, # CV03 values, exernal and unused
              self.fanSpeed] \
             + 9*[0]
        values = [self.decimal(parameter) for parameter in parameters]
        # TODO: Replace bits with actual values
        response = " ".join(values) + " " + self.makeBits(self.startBit, self.humidityBit)
        return response

    def helpText(self):
        # noinspection PyPep8
        return """ASCII-2 PROTOCOL CONFIGURATION

Example of an ASCII E-String:
$01E CV01 CV02 CV03 SV01 SV02 MV01 MV02 MV03 MV04 DO00 DO01 DO02 DO03 DO04 DO05 DO06 DO07 DO08 DO09 DO10 DO11 DO12 DO13 DO14 DO15 DO16 DO17 DO18 DO19 DO20 DO21 DO22 DO23 DO24 DO25 DO26 DO27 DO28 DO29 DO30 DO31 <CR>

Description:
CV01  value min:  -77.0   value max:  182.0   Temperature
CV02  value min:  -55.0   value max:  150.0   T.external
CV03  value min:  -55.0   value max:  150.0   T.external
SV01  value min:    2.0   value max:   30.0   T.shift
SV02  value min:    2.0   value max:   30.0   T.shift
MV01  0000.0 unused setpoint
MV02  0000.0 unused setpoint
MV03  0000.0 unused setpoint
MV04  0000.0 unused setpoint
DO00  unused
DO01  Start
DO02  Humidity
DO03  Cond.protect
DO04  not supported
DO05  not supported
DO06  not supported
DO07  not supported
DO08  not supported
DO09  Custom 1
DO10  Custom 2
DO11  Custom 3
DO12  Custom 4
DO13  unused
DO14  unused
DO15  unused
DO16  unused
DO17  unused
DO18  unused
DO19  unused
DO20  unused
DO21  unused
DO22  unused
DO23  unused
DO24  unused
DO25  unused
DO26  unused
DO27  unused
DO28  unused
DO29  unused
DO30  unused
DO31  unused
--------------------------------------------------------------------------------
Example of  an ASCII I-String:
$01I<CR>
CV01 CV01 CV02 CV02 CV03 CV03 SV01 SV02 MV01 MV01 MV02 MV02 MV03 MV03 MV04 MV04 DO00 DO01 DO02 DO03 DO04 DO05 DO06 DO07 DO08 DO09 DO10 DO11 DO12 DO13 DO14 DO15 DO16 DO17 DO18 DO19 DO20 DO21 DO22 DO23 DO24 DO25 DO26 DO27 DO28 DO29 DO30 DO31 <CR>

Description:
CV01  nominal value Temperature
CV01  actual value  Temperature
CV02  nominal value T.external
CV02  actual value  T.external
CV03  nominal value T.external
CV03  actual value  T.external
SV01  set value     T.shift
SV02  set value     T.shift
MV01 unused setpoint
MV01  not supported
MV02 unused setpoint
MV02  not supported
MV03 unused setpoint
MV03  not supported
MV04 unused setpoint
MV04  not supported
DO00  unused
DO01  Start
DO02  Humidity
DO03  Cond.protect
DO04  not supported
DO05  not supported
DO06  not supported
DO07  not supported
DO08  not supported
DO09  Custom 1
DO10  Custom 2
DO11  Custom 3
DO12  Custom 4
DO13  unused
DO14  unused
DO15  unused
DO16  unused
DO17  unused
DO18  unused
DO19  unused
DO20  unused
DO21  unused
DO22  unused
DO23  unused
DO24  unused
DO25  unused
DO26  unused
DO27  unused
DO28  unused
DO29  unused
DO30  unused
DO31  unused
--------------------------------------------------------------------------------
Configured Messages:
none
"""

    def setTargetsCommand(self, parts):
        """Interpretation of the E-command
        There are 9 decimal numbers, starting with [1]
        [0] $01E
        [1] CV01 chamber temp
        [2] CV02 external temp 1
        [3] CV03 external temp 2
        [4] SV01 fan speed
        [5] SV02
        [6] MV01
        [7] MV02
        [8] MV03
        [9] MV04
        [10] bits

        """
        # TODO: Understand which setpoint value is used to control temperature. There can only be one.
        self.command = parts[0]

        self.tempStart = self.nominalTemp
        self.nominalTemp = float(parts[1])
        self.actualTemperature = self.nominalTemp + self.chamberTempOffset
        self.actualCabinetTemp = self.nominalTemp + self.extCabinetTempOffset
        self.nominalHumidity = float(parts[2])
        self.actualHumidity = self.nominalHumidity + 5
        self.fanSpeed = float(parts[4])
        # five unused parts
        float(parts[5])
        float(parts[6])
        float(parts[7])
        float(parts[8])
        float(parts[9])
        self.bits = parts[10]

        self.startBit = (self.bits[1] == "1")
        self.humidityBit = (self.bits[2] == "1")

        return "0"