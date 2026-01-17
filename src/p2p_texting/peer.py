"""
Peer Module

This module provides the main Peer class that coordinates peer discovery
and messaging functionality.
"""

import uuid
from typing import Optional, Callable
from .peer_discovery import PeerDiscovery
from .messaging import MessagingService


class Peer:
    """
    Main peer class that manages discovery and messaging.
    
    A Peer can discover other peers on the network and exchange
    text messages with them.
    """
    
    def __init__(self, peer_id: Optional[str] = None, port: int = 0):
        """
        Initialize a peer.
        
        Args:
            peer_id: Unique identifier for this peer (auto-generated if not provided)
            port: Port to listen on for messages (0 for automatic assignment)
        """
        self.peer_id = peer_id or str(uuid.uuid4())[:8]
        self.port = port
        self.running = False
        
        # Callbacks
        self.on_peer_discovered: Optional[Callable] = None
        self.on_message_received: Optional[Callable] = None
        
        # Services
        self.messaging_service = None
        self.discovery_service = None
    
    def start(self):
        """Start the peer (discovery and messaging services)."""
        if self.running:
            return
        
        # Start messaging service first to get the port
        self.messaging_service = MessagingService(
            peer_id=self.peer_id,
            port=self.port,
            on_message_received=self._handle_message_received
        )
        self.port = self.messaging_service.start()
        
        # Start discovery service with the messaging port
        self.discovery_service = PeerDiscovery(
            peer_id=self.peer_id,
            listening_port=self.port,
            on_peer_discovered=self._handle_peer_discovered
        )
        self.discovery_service.start()
        
        self.running = True
    
    def stop(self):
        """Stop the peer."""
        if not self.running:
            return
        
        self.running = False
        
        if self.discovery_service:
            self.discovery_service.stop()
        if self.messaging_service:
            self.messaging_service.stop()
    
    def send_message(self, peer_id: str, message: str) -> bool:
        """
        Send a message to another peer.
        
        Args:
            peer_id: ID of the peer to send to
            message: Text message to send
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        if not self.running:
            print("Error: Peer is not running")
            return False
        
        # Get peer info from discovery service
        peers = self.discovery_service.get_peers()
        if peer_id not in peers:
            print(f"Error: Peer {peer_id} not found")
            return False
        
        peer_info = peers[peer_id]
        return self.messaging_service.send_message(
            peer_info["ip"],
            peer_info["port"],
            message
        )
    
    def get_known_peers(self):
        """
        Get list of known peers.
        
        Returns:
            Dictionary of peer_id -> peer info
        """
        if not self.running:
            return {}
        return self.discovery_service.get_peers()
    
    def _handle_peer_discovered(self, peer_id: str, ip: str, port: int):
        """Internal handler for peer discovery."""
        if self.on_peer_discovered:
            self.on_peer_discovered(peer_id, ip, port)
    
    def _handle_message_received(self, from_peer: str, message: str):
        """Internal handler for received messages."""
        if self.on_message_received:
            self.on_message_received(from_peer, message)
