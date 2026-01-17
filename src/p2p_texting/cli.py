"""
CLI Module

Command-line interface for the P2P texting application.
"""

import sys
import threading
from .peer import Peer


class CLI:
    """Command-line interface for P2P texting."""
    
    def __init__(self, peer_id: str = None):
        """
        Initialize CLI.
        
        Args:
            peer_id: Optional peer ID (will be auto-generated if not provided)
        """
        self.peer = Peer(peer_id=peer_id)
        self.peer.on_peer_discovered = self.handle_peer_discovered
        self.peer.on_message_received = self.handle_message_received
        self.running = False
        
    def handle_peer_discovered(self, peer_id: str, ip: str, port: int):
        """Handle discovery of a new peer."""
        print(f"\n[+] Peer discovered: {peer_id} at {ip}:{port}")
        self.print_prompt()
    
    def handle_message_received(self, from_peer: str, message: str):
        """Handle received message."""
        print(f"\n[Message from {from_peer}]: {message}")
        self.print_prompt()
    
    def print_prompt(self):
        """Print the command prompt."""
        print(f"[{self.peer.peer_id}]> ", end='', flush=True)
    
    def print_help(self):
        """Print available commands."""
        print("\nAvailable commands:")
        print("  list              - List all known peers")
        print("  send <peer_id>    - Send a message to a peer")
        print("  help              - Show this help message")
        print("  quit              - Exit the application")
        print()
    
    def list_peers(self):
        """List all known peers."""
        peers = self.peer.get_known_peers()
        if not peers:
            print("No peers discovered yet.")
        else:
            print(f"\nKnown peers ({len(peers)}):")
            for peer_id, info in peers.items():
                print(f"  - {peer_id} at {info['ip']}:{info['port']}")
        print()
    
    def send_message_interactive(self, peer_id: str):
        """Send a message to a peer interactively."""
        # Check if peer exists
        peers = self.peer.get_known_peers()
        if peer_id not in peers:
            print(f"Error: Peer '{peer_id}' not found. Use 'list' to see available peers.")
            return
        
        # Get message
        print(f"Enter message for {peer_id} (press Enter to send):")
        message = input("> ").strip()
        
        if not message:
            print("Message cancelled (empty message).")
            return
        
        # Send message
        success = self.peer.send_message(peer_id, message)
        if success:
            print(f"Message sent to {peer_id}.")
        else:
            print(f"Failed to send message to {peer_id}.")
    
    def run(self):
        """Run the CLI application."""
        print("=" * 60)
        print("P2P Texting Application")
        print("=" * 60)
        print(f"Starting peer with ID: {self.peer.peer_id}")
        
        # Start peer
        self.peer.start()
        print(f"Listening on port: {self.peer.port}")
        print(f"Broadcasting presence on the network...")
        print("\nType 'help' for available commands.")
        print()
        
        self.running = True
        
        # Main command loop
        try:
            while self.running:
                self.print_prompt()
                try:
                    command = input().strip().lower()
                except EOFError:
                    break
                
                if not command:
                    continue
                
                parts = command.split(maxsplit=1)
                cmd = parts[0]
                
                if cmd == "quit" or cmd == "exit":
                    break
                elif cmd == "help":
                    self.print_help()
                elif cmd == "list":
                    self.list_peers()
                elif cmd == "send":
                    if len(parts) < 2:
                        print("Usage: send <peer_id>")
                    else:
                        peer_id = parts[1]
                        self.send_message_interactive(peer_id)
                else:
                    print(f"Unknown command: {cmd}. Type 'help' for available commands.")
        
        except KeyboardInterrupt:
            print("\nInterrupted by user.")
        
        finally:
            print("\nStopping peer...")
            self.peer.stop()
            print("Goodbye!")


def main():
    """Main entry point for the CLI application."""
    peer_id = None
    
    # Parse command-line arguments
    if len(sys.argv) > 1:
        peer_id = sys.argv[1]
    
    # Run CLI
    cli = CLI(peer_id=peer_id)
    cli.run()


if __name__ == "__main__":
    main()
