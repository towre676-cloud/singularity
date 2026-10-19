#!/usr/bin/env python3
"""Replay complete NX11 source-bound remote response evidence."""
import sys
from nx_decision_recovery import main
if __name__=='__main__':
    sys.argv.extend(('--track','NX11'));main()
