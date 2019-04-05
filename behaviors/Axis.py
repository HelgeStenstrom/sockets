import math
import time

from behaviors.SubDevice import SubDevice


class Axis(SubDevice):
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