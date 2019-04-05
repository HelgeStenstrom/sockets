from behaviors.SubDevice import SubDevice


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