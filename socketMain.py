
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
from Climate import VotschBase, Vc37060
from socketInstrument import *

def main():
    attachedInstrument = instrumentTypeArgument()

    attachedInstrument.theSocket()


def instrumentTypeArgument():
    ignored = __doc__
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    parser.add_argument('InstrumentType', help='Type of instrument or Vötsch model',
                        choices=['Vc', 'Vt', 'Vc37060', 'RotaryDisc', 'NCD', 'BBA150', 'Empower', 'Optimus'])
    parser.add_argument('--offset', help="How far the used target pos is from the requested one.", type=float)
    args = parser.parse_args()
    if args.InstrumentType in ['Vc', 'Vt']:
        attachedInstrument = VotschBase()
        attachedInstrument.CcType = args.InstrumentType

    elif args.InstrumentType == 'Vc37060':
        attachedInstrument = Vc37060()

    elif args.InstrumentType in ['RotaryDisc']:
        attachedInstrument = RotaryDiscBySocket()
        if args.offset:
            attachedInstrument.offset = args.offset

    elif args.InstrumentType == 'NCD':
        attachedInstrument = MaturoNCD()

    elif args.InstrumentType in ['BBA150']:
        attachedInstrument = PaRsBBA150()

    elif args.InstrumentType in ['Empower']:
        attachedInstrument = PaEmpower()

    elif args.InstrumentType == "Optimus":
        attachedInstrument = Optimus()

    else:
        raise NotImplementedError
    return attachedInstrument


if __name__ == '__main__':
    main()
