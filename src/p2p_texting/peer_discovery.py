"""
Peer Discovery Module

This module handles peer discovery using UDP broadcast messages.
Peers periodically broadcast their presence on the network and listen
for broadcasts from other peers.
"""

import socket
import json
import threading
import time
import logging
from typing import Dict, Callable, Optional

logger = logging.getLogger(__name__)


class PeerDiscovery:
    """
    Handles peer discovery using UDP broadcast.
    
    Peers broadcast their presence (IP address and listening port) on the network
    and listen for similar broadcasts from other peers.
    """
    
    BROADCAST_PORT = 37020
    BROADCAST_INTERVAL = 5  # seconds
    DISCOVERY_MESSAGE_TYPE = "PEER_DISCOVERY"
    
    def __init__(self, peer_id: str, listening_port: int, on_peer_discovered: Optional[Callable] = None):
        """
        Initialize peer discovery.
        
        Args:
            peer_id: Unique identifier for this peer
            listening_port: TCP port this peer is listening on for messages
            on_peer_discovered: Callback function when a new peer is discovered
        """
        self.peer_id = peer_id
        self.listening_port = listening_port
        self.on_peer_discovered = on_peer_discovered
        self.known_peers: Dict[str, Dict] = {}  # peer_id -> {ip, port, last_seen}
        self.running = False
        self.broadcast_thread = None
        self.listen_thread = None
        self.sock = None
        self.broadcast_error_logged = False  # Track if we've logged broadcast errors
        
    def start(self):
        """Start the peer discovery service."""
        if self.running:
            return
            
        self.running = True
        
        # Setup UDP socket for broadcasting and listening
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', self.BROADCAST_PORT))
        
        # Start broadcast and listen threads
        self.broadcast_thread = threading.Thread(target=self._broadcast_presence, daemon=True)
        self.listen_thread = threading.Thread(target=self._listen_for_peers, daemon=True)
        
        self.broadcast_thread.start()
        self.listen_thread.start()
        
    def stop(self):
        """Stop the peer discovery service."""
        self.running = False
        
        if self.sock:
            self.sock.close()
            
        if self.broadcast_thread:
            self.broadcast_thread.join(timeout=1)
        if self.listen_thread:
            self.listen_thread.join(timeout=1)
    
    def _broadcast_presence(self):
        """Periodically broadcast this peer's presence on the network."""
        while self.running:
            try:
                message = {
                    "type": self.DISCOVERY_MESSAGE_TYPE,
                    "peer_id": self.peer_id,
                    "port": self.listening_port
                }
                message_bytes = json.dumps(message).encode('utf-8')
                
                # Broadcast to all devices on the network
                self.sock.sendto(message_bytes, ('<broadcast>', self.BROADCAST_PORT))
                
            except Exception as e:
                # Only log broadcast errors once to avoid spam
                if self.running and not self.broadcast_error_logged:
                    logger.warning("Broadcast not available (%s). Discovery will still work via listening.", e)
                    self.broadcast_error_logged = True
            
            time.sleep(self.BROADCAST_INTERVAL)
    
    def _listen_for_peers(self):
        """Listen for broadcast messages from other peers."""
        self.sock.settimeout(1.0)  # Allow checking self.running periodically
        
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                message = json.loads(data.decode('utf-8'))
                
                if message.get("type") == self.DISCOVERY_MESSAGE_TYPE:
                    peer_id = message.get("peer_id")
                    port = message.get("port")
                    ip = addr[0]
                    
                    # Don't add ourselves
                    if peer_id == self.peer_id:
                        continue
                    
                    # Check if this is a new peer
                    is_new_peer = peer_id not in self.known_peers
                    
                    # Update known peers
                    self.known_peers[peer_id] = {
                        "ip": ip,
                        "port": port,
                        "last_seen": time.time()
                    }
                    
                    # Notify about new peer
                    if is_new_peer and self.on_peer_discovered:
                        self.on_peer_discovered(peer_id, ip, port)
                        
            except socket.timeout:
                continue  # Normal timeout, just check if still running
            except json.JSONDecodeError:
                continue  # Ignore malformed messages
            except Exception as e:
                if self.running:
                    logger.error("Error listening for peers: %s", e)
    
    def get_peers(self) -> Dict[str, Dict]:
        """
        Get all known peers.
        
        Returns:
            Dictionary mapping peer_id to peer info (ip, port, last_seen)
        """
        # Clean up stale peers (not seen in 30 seconds)
        current_time = time.time()
        stale_peers = [
            peer_id for peer_id, info in self.known_peers.items()
            if current_time - info["last_seen"] > 30
        ]
        for peer_id in stale_peers:
            del self.known_peers[peer_id]
        
        return self.known_peers.copy()
