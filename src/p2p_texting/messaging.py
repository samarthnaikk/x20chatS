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
    FILE_REQUEST_TYPE = "FILE_REQUEST"
    FILE_ACCEPT_TYPE = "FILE_ACCEPT"
    FILE_REJECT_TYPE = "FILE_REJECT"
    FILE_CHUNK_TYPE = "FILE_CHUNK"
    FILE_COMPLETE_TYPE = "FILE_COMPLETE"
    FILE_ERROR_TYPE = "FILE_ERROR"
    
    MAX_MESSAGE_SIZE = 4096
    CHUNK_SIZE = 8192  # 8KB chunks for file transfer
    
    def __init__(self, peer_id: str, port: int = 0, on_message_received: Optional[Callable] = None,
                 on_file_request: Optional[Callable] = None,
                 on_file_response: Optional[Callable] = None,
                 on_file_chunk: Optional[Callable] = None,
                 on_file_complete: Optional[Callable] = None,
                 on_file_error: Optional[Callable] = None):
        """
        Initialize messaging service.
        
        Args:
            peer_id: Unique identifier for this peer
            port: Port to listen on (0 for automatic assignment)
            on_message_received: Callback when a message is received
            on_file_request: Callback when a file transfer is requested
            on_file_response: Callback when file request is accepted/rejected
            on_file_chunk: Callback when a file chunk is received
            on_file_complete: Callback when file transfer is complete
            on_file_error: Callback when a file transfer error occurs
        """
        self.peer_id = peer_id
        self.port = port
        self.on_message_received = on_message_received
        self.on_file_request = on_file_request
        self.on_file_response = on_file_response
        self.on_file_chunk = on_file_chunk
        self.on_file_complete = on_file_complete
        self.on_file_error = on_file_error
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
        # Note: Binding to all interfaces ('') is intentional for P2P connectivity
        # This allows peers on any network interface to connect
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
    
    def send_file_request(self, peer_ip: str, peer_port: int, file_id: str, 
                         filename: str, filesize: int) -> bool:
        """
        Send a file transfer request to another peer.
        
        Args:
            peer_ip: IP address of the peer
            peer_port: Port number of the peer
            file_id: Unique identifier for this file transfer
            filename: Name of the file
            filesize: Size of the file in bytes
            
        Returns:
            True if request was sent successfully, False otherwise
        """
        return self._send_json_message(peer_ip, peer_port, {
            "type": self.FILE_REQUEST_TYPE,
            "from": self.peer_id,
            "file_id": file_id,
            "filename": filename,
            "filesize": filesize
        })
    
    def send_file_response(self, peer_ip: str, peer_port: int, file_id: str, 
                          accepted: bool, save_path: str = None) -> bool:
        """
        Send acceptance or rejection of a file transfer.
        
        Args:
            peer_ip: IP address of the peer
            peer_port: Port number of the peer
            file_id: Unique identifier for this file transfer
            accepted: True to accept, False to reject
            save_path: Path where file will be saved (if accepted)
            
        Returns:
            True if response was sent successfully, False otherwise
        """
        response_type = self.FILE_ACCEPT_TYPE if accepted else self.FILE_REJECT_TYPE
        message_data = {
            "type": response_type,
            "from": self.peer_id,
            "file_id": file_id
        }
        if save_path:
            message_data["save_path"] = save_path
        return self._send_json_message(peer_ip, peer_port, message_data)
    
    def send_file_chunks(self, peer_ip: str, peer_port: int, file_id: str, 
                        file_path: str) -> bool:
        """
        Send file in chunks to another peer.
        
        Args:
            peer_ip: IP address of the peer
            peer_port: Port number of the peer
            file_id: Unique identifier for this file transfer
            file_path: Path to the file to send
            
        Returns:
            True if file was sent successfully, False otherwise
        """
        try:
            # Create a TCP connection to the peer
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(30.0)  # Longer timeout for file transfers
            client_socket.connect((peer_ip, peer_port))
            
            with open(file_path, 'rb') as f:
                chunk_num = 0
                while True:
                    chunk_data = f.read(self.CHUNK_SIZE)
                    if not chunk_data:
                        break
                    
                    # Send chunk
                    message_data = {
                        "type": self.FILE_CHUNK_TYPE,
                        "from": self.peer_id,
                        "file_id": file_id,
                        "chunk_num": chunk_num
                    }
                    message_bytes = json.dumps(message_data).encode('utf-8')
                    
                    # Send: [message_length][message_json][chunk_length][chunk_data]
                    client_socket.sendall(len(message_bytes).to_bytes(4, byteorder='big'))
                    client_socket.sendall(message_bytes)
                    client_socket.sendall(len(chunk_data).to_bytes(4, byteorder='big'))
                    client_socket.sendall(chunk_data)
                    
                    chunk_num += 1
            
            # Send completion message
            complete_data = {
                "type": self.FILE_COMPLETE_TYPE,
                "from": self.peer_id,
                "file_id": file_id,
                "total_chunks": chunk_num
            }
            complete_bytes = json.dumps(complete_data).encode('utf-8')
            client_socket.sendall(len(complete_bytes).to_bytes(4, byteorder='big'))
            client_socket.sendall(complete_bytes)
            
            client_socket.close()
            return True
            
        except Exception as e:
            logger.error("Error sending file: %s", e)
            # Send error message if possible
            try:
                self._send_json_message(peer_ip, peer_port, {
                    "type": self.FILE_ERROR_TYPE,
                    "from": self.peer_id,
                    "file_id": file_id,
                    "error": str(e)
                })
            except:
                pass
            return False
    
    def _send_json_message(self, peer_ip: str, peer_port: int, message_data: dict) -> bool:
        """
        Helper to send a JSON message.
        
        Args:
            peer_ip: IP address of the peer
            peer_port: Port number of the peer
            message_data: Dictionary to send as JSON
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5.0)
            client_socket.connect((peer_ip, peer_port))
            
            message_bytes = json.dumps(message_data).encode('utf-8')
            message_length = len(message_bytes)
            client_socket.sendall(message_length.to_bytes(4, byteorder='big'))
            client_socket.sendall(message_bytes)
            
            client_socket.close()
            return True
            
        except Exception as e:
            logger.error("Error sending JSON message: %s", e)
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
        max_messages_per_connection = 1000  # Limit to prevent resource exhaustion
        message_count = 0
        
        try:
            # Keep connection open for multiple messages (file chunks)
            while message_count < max_messages_per_connection:
                message_count += 1
                
                # Receive message length
                length_bytes = client_socket.recv(4)
                if not length_bytes:
                    break  # Connection closed
                    
                message_length = int.from_bytes(length_bytes, byteorder='big')
                
                # Validate message length
                if message_length > self.MAX_MESSAGE_SIZE:
                    logger.warning("Message too large (%d bytes), ignoring", message_length)
                    break
                
                # Receive message data
                message_bytes = b''
                while len(message_bytes) < message_length:
                    chunk = client_socket.recv(min(message_length - len(message_bytes), 4096))
                    if not chunk:
                        break
                    message_bytes += chunk
                
                if len(message_bytes) < message_length:
                    break  # Incomplete message
                
                # Parse message
                message_data = json.loads(message_bytes.decode('utf-8'))
                message_type = message_data.get("type")
                
                if message_type == self.MESSAGE_TYPE:
                    from_peer = message_data.get("from")
                    message_text = message_data.get("message")
                    
                    # Notify about received message
                    if self.on_message_received:
                        self.on_message_received(from_peer, message_text)
                    break  # Close connection after text message
                
                elif message_type == self.FILE_REQUEST_TYPE:
                    from_peer = message_data.get("from")
                    file_id = message_data.get("file_id")
                    filename = message_data.get("filename")
                    filesize = message_data.get("filesize")
                    
                    if self.on_file_request:
                        self.on_file_request(from_peer, file_id, filename, filesize)
                    break  # Close connection after file request
                
                elif message_type in (self.FILE_ACCEPT_TYPE, self.FILE_REJECT_TYPE):
                    from_peer = message_data.get("from")
                    file_id = message_data.get("file_id")
                    accepted = message_type == self.FILE_ACCEPT_TYPE
                    save_path = message_data.get("save_path")
                    
                    if self.on_file_response:
                        self.on_file_response(from_peer, file_id, accepted, save_path)
                    break  # Close connection after response
                
                elif message_type == self.FILE_CHUNK_TYPE:
                    from_peer = message_data.get("from")
                    file_id = message_data.get("file_id")
                    chunk_num = message_data.get("chunk_num")
                    
                    # Read chunk length and data
                    chunk_length_bytes = client_socket.recv(4)
                    if not chunk_length_bytes:
                        break
                    
                    chunk_length = int.from_bytes(chunk_length_bytes, byteorder='big')
                    chunk_data = b''
                    while len(chunk_data) < chunk_length:
                        data = client_socket.recv(min(chunk_length - len(chunk_data), 8192))
                        if not data:
                            break
                        chunk_data += data
                    
                    if len(chunk_data) < chunk_length:
                        break  # Incomplete chunk
                    
                    if self.on_file_chunk:
                        self.on_file_chunk(from_peer, file_id, chunk_num, chunk_data)
                    # Continue to next message (more chunks or completion)
                
                elif message_type == self.FILE_COMPLETE_TYPE:
                    from_peer = message_data.get("from")
                    file_id = message_data.get("file_id")
                    total_chunks = message_data.get("total_chunks")
                    
                    if self.on_file_complete:
                        self.on_file_complete(from_peer, file_id, total_chunks)
                    break  # Close connection after completion
                
                elif message_type == self.FILE_ERROR_TYPE:
                    from_peer = message_data.get("from")
                    file_id = message_data.get("file_id")
                    error = message_data.get("error")
                    
                    if self.on_file_error:
                        self.on_file_error(from_peer, file_id, error)
                    break  # Close connection after error
                
                else:
                    # Unknown message type, close connection
                    break
                    
        except json.JSONDecodeError:
            logger.warning("Received malformed message from %s", addr)
        except Exception as e:
            logger.error("Error handling connection from %s: %s", addr, e)
        finally:
            client_socket.close()
