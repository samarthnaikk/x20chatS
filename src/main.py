#!/usr/bin/env python3
"""
Entry point script for the P2P texting application.
"""

import sys
import os

# Add src directory to path to allow imports
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from p2p_texting.cli import main

if __name__ == "__main__":
    main()
