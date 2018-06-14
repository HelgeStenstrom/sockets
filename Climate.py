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

    def helpText(self):
        return """ASCII description of the protocol
Contains multiple lines
        """


class Vc37060(VotschBase):

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

    def setTargetsCommand(self, parts):
        self.command = parts[0]

        self.tempStart = self.nominalTemp
        self.nominalTemp = float(parts[1])
        self.actualTemperature = self.nominalTemp + 3
        self.nominalHumidity = float(parts[2])
        self.actualHumidity = self.nominalHumidity + 5
        self.fanSpeed = float(parts[3])
        # four unused parts
        float(parts[4])
        float(parts[5])
        float(parts[6])
        float(parts[7])
        self.bits = parts[8]

        return "0"
