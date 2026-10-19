#!/usr/bin/env python3
"""Replay complete NX09 rank/execution/design acceptance evidence."""
import sys
from nx_decision_recovery import main
if __name__=='__main__':
    sys.argv.extend(('--track','NX09'));main()
