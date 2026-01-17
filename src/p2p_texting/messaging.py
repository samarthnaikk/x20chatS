"""
Messaging Module

This module handles TCP-based peer-to-peer messaging.
It provides functionality to send and receive text messages between peers.
"""

import socket
import json
import threading
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class MessagingService:
    """
    Handles sending and receiving messages using TCP sockets.
    """
    
    MESSAGE_TYPE = "TEXT_MESSAGE"
    MAX_MESSAGE_SIZE = 4096
    
    def __init__(self, peer_id: str, port: int = 0, on_message_received: Optional[Callable] = None):
        """
        Initialize messaging service.
        
        Args:
            peer_id: Unique identifier for this peer
            port: Port to listen on (0 for automatic assignment)
            on_message_received: Callback when a message is received
        """
        self.peer_id = peer_id
        self.port = port
        self.on_message_received = on_message_received
        self.running = False
        self.server_socket = None
        self.listen_thread = None
        
    def start(self) -> int:
        """
        Start the messaging service.
        
        Returns:
            The port number the service is listening on
        """
        if self.running:
            return self.port
            
        self.running = True
        
        # Create TCP socket for listening
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('', self.port))
        self.server_socket.listen(5)
        
        # Get the actual port (in case port was 0)
        self.port = self.server_socket.getsockname()[1]
        
        # Start listening thread
        self.listen_thread = threading.Thread(target=self._listen_for_messages, daemon=True)
        self.listen_thread.start()
        
        return self.port
    
    def stop(self):
        """Stop the messaging service."""
        self.running = False
        
        if self.server_socket:
            self.server_socket.close()
            
        if self.listen_thread:
            self.listen_thread.join(timeout=1)
    
    def send_message(self, peer_ip: str, peer_port: int, message: str) -> bool:
        """
        Send a text message to another peer.
        
        Args:
            peer_ip: IP address of the peer
            peer_port: Port number of the peer
            message: Text message to send
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        try:
            # Create a TCP connection to the peer
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5.0)  # 5 second timeout
            client_socket.connect((peer_ip, peer_port))
            
            # Prepare message
            message_data = {
                "type": self.MESSAGE_TYPE,
                "from": self.peer_id,
                "message": message
            }
            message_bytes = json.dumps(message_data).encode('utf-8')
            
            # Send message length followed by message
            message_length = len(message_bytes)
            client_socket.sendall(message_length.to_bytes(4, byteorder='big'))
            client_socket.sendall(message_bytes)
            
            client_socket.close()
            return True
            
        except socket.timeout:
            logger.warning("Connection timeout - peer at %s:%s not responding", peer_ip, peer_port)
            return False
        except ConnectionRefusedError:
            logger.warning("Connection refused - peer at %s:%s not available", peer_ip, peer_port)
            return False
        except Exception as e:
            logger.error("Error sending message: %s", e)
            return False
    
    def _listen_for_messages(self):
        """Listen for incoming TCP connections and messages."""
        self.server_socket.settimeout(1.0)  # Allow checking self.running periodically
        
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                # Handle each connection in a separate thread
                handler_thread = threading.Thread(
                    target=self._handle_connection,
                    args=(client_socket, addr),
                    daemon=True
                )
                handler_thread.start()
                
            except socket.timeout:
                continue  # Normal timeout, check if still running
            except Exception as e:
                if self.running:
                    logger.error("Error accepting connection: %s", e)
    
    def _handle_connection(self, client_socket: socket.socket, addr):
        """Handle an incoming connection from a peer."""
        try:
            # Receive message length
            length_bytes = client_socket.recv(4)
            if not length_bytes:
                return
                
            message_length = int.from_bytes(length_bytes, byteorder='big')
            
            # Validate message length
            if message_length > self.MAX_MESSAGE_SIZE:
                logger.warning("Message too large (%d bytes), ignoring", message_length)
                return
            
            # Receive message data
            message_bytes = b''
            while len(message_bytes) < message_length:
                chunk = client_socket.recv(min(message_length - len(message_bytes), 4096))
                if not chunk:
                    break
                message_bytes += chunk
            
            # Parse message
            message_data = json.loads(message_bytes.decode('utf-8'))
            
            if message_data.get("type") == self.MESSAGE_TYPE:
                from_peer = message_data.get("from")
                message_text = message_data.get("message")
                
                # Notify about received message
                if self.on_message_received:
                    self.on_message_received(from_peer, message_text)
                    
        except json.JSONDecodeError:
            logger.warning("Received malformed message from %s", addr)
        except Exception as e:
            logger.error("Error handling connection from %s: %s", addr, e)
        finally:
            client_socket.close()
