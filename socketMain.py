"""
Mimic an instrument, and let it respond to commands.
Usually instruments are attached by VISA over GPIB or TRP/IP.
Here we use VISA over Socket, to be able to simulate instrument responses to commands.

Implemented instruments:
- Vötsch climate chamber models Vt 3 7060 and Vc 3 7060.
- innco GmbH IN3000 RotaryDisc.
"""
import argparse

from Amplifier import PaRsBBA150, PaEmpower
from Climate import VotschBase, Vc37060, Vt37060ExtCab, Vt37060ExtCabOttawa
from behaviors.InncoBehavior import InncoBehavior
from behaviors.OptimusBehavior import OptimusBehavior
from behaviors.MaturoNcdBehavior import MaturoNcdBehavior


def main():
    attachedInstrument = instrumentTypeArgument()
    attachedInstrument.communicator.start()


def instrumentTypeArgument():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    parser.add_argument('InstrumentType', help='Type of instrument or Vötsch model',
                        choices=['Vc', 'Vt', 'Vc37060', 'Vt37060ExtCab', 'Vt37060ExtCabOttawa', 'RotaryDisc', 'NCD', 'BBA150', 'Empower', 'Optimus'])
    parser.add_argument('--offset', help="How far the used target pos is from the requested one.", type=float)
    args = parser.parse_args()
    if args.InstrumentType in ['Vc', 'Vt']:
        attachedInstrument = VotschBase()
        attachedInstrument.CcType = args.InstrumentType

    elif args.InstrumentType == 'Vc37060':
        attachedInstrument = Vc37060()

    elif args.InstrumentType == 'Vt37060ExtCab':
        attachedInstrument = Vt37060ExtCab()

    elif args.InstrumentType == 'Vt37060ExtCabOttawa':
        attachedInstrument = Vt37060ExtCabOttawa()

    elif args.InstrumentType in ['RotaryDisc']:
        attachedInstrument = InncoBehavior()
        if args.offset:
            attachedInstrument.offset = args.offset

    elif args.InstrumentType == 'NCD':
        attachedInstrument = MaturoNcdBehavior()

    elif args.InstrumentType in ['BBA150']:
        attachedInstrument = PaRsBBA150()

    elif args.InstrumentType in ['Empower']:
        attachedInstrument = PaEmpower()

    elif args.InstrumentType == "Optimus":
        attachedInstrument = OptimusBehavior()

    else:
        raise NotImplementedError
    return attachedInstrument


if __name__ == '__main__':
    main()
