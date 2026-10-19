#!/usr/bin/env python3
"""Replay complete NX12 constrained protocol population evidence."""
import sys
from nx_decision_recovery import main
if __name__=='__main__':
    sys.argv.extend(('--track','NX12'));main()
