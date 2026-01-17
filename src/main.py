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


def main():
    """Main entry point - launches TUI by default, CLI with --cli flag."""
    # Check for CLI flag
    use_cli = "--cli" in sys.argv
    if use_cli:
        sys.argv.remove("--cli")
    
    # Get peer ID if provided
    peer_id = None
    if len(sys.argv) > 1:
        peer_id = sys.argv[1]
    
    if use_cli:
        # Use old CLI interface
        from p2p_texting.cli import CLI
        cli = CLI(peer_id=peer_id)
        cli.run()
    else:
        # Use new TUI interface (default)
        from p2p_texting.tui import run_tui
        run_tui(peer_id=peer_id)


if __name__ == "__main__":
    main()
