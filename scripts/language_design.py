#!/usr/bin/env python3
"""Replay complete NX07 catalogue/thermal acceptance evidence."""
import sys
from nx_decision_recovery import main
if __name__=='__main__':
    sys.argv.extend(('--track','NX07'));main()
