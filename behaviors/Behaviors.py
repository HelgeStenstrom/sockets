import math
import time


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


