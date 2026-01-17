"""
Peer Module

This module provides the main Peer class that coordinates peer discovery
and messaging functionality.
"""

import uuid
import os
from typing import Optional, Callable, Dict
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
        self.on_file_request: Optional[Callable] = None
        self.on_file_response: Optional[Callable] = None
        self.on_file_progress: Optional[Callable] = None
        self.on_file_complete: Optional[Callable] = None
        self.on_file_error: Optional[Callable] = None
        
        # Services
        self.messaging_service = None
        self.discovery_service = None
        
        # File transfer state
        self.active_file_transfers: Dict[str, Dict] = {}  # file_id -> transfer info
        self.pending_file_requests: Dict[str, Dict] = {}  # file_id -> request info
    
    def start(self):
        """Start the peer (discovery and messaging services)."""
        if self.running:
            return
        
        # Start messaging service first to get the port
        self.messaging_service = MessagingService(
            peer_id=self.peer_id,
            port=self.port,
            on_message_received=self._handle_message_received,
            on_file_request=self._handle_file_request,
            on_file_response=self._handle_file_response,
            on_file_chunk=self._handle_file_chunk,
            on_file_complete=self._handle_file_complete,
            on_file_error=self._handle_file_error
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
    
    def send_file(self, peer_id: str, file_path: str) -> Optional[str]:
        """
        Send a file to another peer.
        
        Args:
            peer_id: ID of the peer to send to
            file_path: Path to the file to send
            
        Returns:
            File transfer ID if request was sent successfully, None otherwise
        """
        if not self.running:
            print("Error: Peer is not running")
            return None
        
        # Validate file exists
        if not os.path.exists(file_path):
            print(f"Error: File {file_path} not found")
            return None
        
        # Get peer info from discovery service
        peers = self.discovery_service.get_peers()
        if peer_id not in peers:
            print(f"Error: Peer {peer_id} not found")
            return None
        
        peer_info = peers[peer_id]
        
        # Generate file transfer ID
        file_id = str(uuid.uuid4())[:8]
        filename = os.path.basename(file_path)
        filesize = os.path.getsize(file_path)
        
        # Store transfer info
        self.pending_file_requests[file_id] = {
            "peer_id": peer_id,
            "peer_ip": peer_info["ip"],
            "peer_port": peer_info["port"],
            "file_path": file_path,
            "filename": filename,
            "filesize": filesize,
            "status": "pending"
        }
        
        # Send file request
        success = self.messaging_service.send_file_request(
            peer_info["ip"],
            peer_info["port"],
            file_id,
            filename,
            filesize
        )
        
        if success:
            return file_id
        else:
            del self.pending_file_requests[file_id]
            return None
    
    def accept_file(self, file_id: str, save_path: str) -> bool:
        """
        Accept an incoming file transfer.
        
        Args:
            file_id: ID of the file transfer to accept
            save_path: Path where the file should be saved
            
        Returns:
            True if acceptance was sent successfully, False otherwise
        """
        if file_id not in self.active_file_transfers:
            print(f"Error: File transfer {file_id} not found")
            return False
        
        transfer_info = self.active_file_transfers[file_id]
        transfer_info["save_path"] = save_path
        transfer_info["status"] = "accepted"
        transfer_info["received_chunks"] = []
        transfer_info["bytes_received"] = 0
        
        try:
            transfer_info["file_handle"] = open(save_path, 'wb')
        except PermissionError:
            print(f"Error: Permission denied writing to {save_path}")
            del self.active_file_transfers[file_id]
            return False
        except OSError as e:
            # Covers disk full, invalid path, etc.
            print(f"Error: Cannot write to file - {e}")
            del self.active_file_transfers[file_id]
            return False
        except Exception as e:
            print(f"Error: Cannot open file for writing: {e}")
            del self.active_file_transfers[file_id]
            return False
        
        # Send acceptance
        return self.messaging_service.send_file_response(
            transfer_info["peer_ip"],
            transfer_info["peer_port"],
            file_id,
            accepted=True,
            save_path=save_path
        )
    
    def reject_file(self, file_id: str) -> bool:
        """
        Reject an incoming file transfer.
        
        Args:
            file_id: ID of the file transfer to reject
            
        Returns:
            True if rejection was sent successfully, False otherwise
        """
        if file_id not in self.active_file_transfers:
            print(f"Error: File transfer {file_id} not found")
            return False
        
        transfer_info = self.active_file_transfers[file_id]
        
        # Send rejection
        success = self.messaging_service.send_file_response(
            transfer_info["peer_ip"],
            transfer_info["peer_port"],
            file_id,
            accepted=False
        )
        
        # Remove from active transfers
        if success:
            del self.active_file_transfers[file_id]
        
        return success
    
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
    
    def _handle_file_request(self, from_peer: str, file_id: str, filename: str, filesize: int):
        """Internal handler for file transfer requests."""
        # Get peer info
        peers = self.discovery_service.get_peers()
        peer_info = peers.get(from_peer, {})
        
        # Store transfer info
        self.active_file_transfers[file_id] = {
            "peer_id": from_peer,
            "peer_ip": peer_info.get("ip"),
            "peer_port": peer_info.get("port"),
            "filename": filename,
            "filesize": filesize,
            "status": "requested"
        }
        
        # Notify application
        if self.on_file_request:
            self.on_file_request(from_peer, file_id, filename, filesize)
    
    def _handle_file_response(self, from_peer: str, file_id: str, accepted: bool, save_path: str):
        """Internal handler for file transfer response."""
        if file_id not in self.pending_file_requests:
            return
        
        transfer_info = self.pending_file_requests[file_id]
        
        if accepted:
            # Start sending file in a separate thread
            import threading
            transfer_info["status"] = "accepted"
            self.active_file_transfers[file_id] = transfer_info
            
            def send_file():
                success = self.messaging_service.send_file_chunks(
                    transfer_info["peer_ip"],
                    transfer_info["peer_port"],
                    file_id,
                    transfer_info["file_path"]
                )
                if not success and self.on_file_error:
                    self.on_file_error(from_peer, file_id, "Failed to send file")
            
            send_thread = threading.Thread(target=send_file, daemon=True)
            send_thread.start()
        else:
            transfer_info["status"] = "rejected"
            if self.on_file_error:
                self.on_file_error(from_peer, file_id, "File transfer rejected by peer")
        
        # Remove from pending
        del self.pending_file_requests[file_id]
        
        # Notify application
        if self.on_file_response:
            self.on_file_response(from_peer, file_id, accepted, save_path)
    
    def _handle_file_chunk(self, from_peer: str, file_id: str, chunk_num: int, chunk_data: bytes):
        """Internal handler for file chunks."""
        if file_id not in self.active_file_transfers:
            return
        
        transfer_info = self.active_file_transfers[file_id]
        
        # Write chunk to file
        if "file_handle" in transfer_info:
            try:
                transfer_info["file_handle"].write(chunk_data)
                if "received_chunks" not in transfer_info:
                    transfer_info["received_chunks"] = []
                transfer_info["received_chunks"].append(chunk_num)
                if "bytes_received" not in transfer_info:
                    transfer_info["bytes_received"] = 0
                transfer_info["bytes_received"] += len(chunk_data)
                
                # Notify about progress
                if self.on_file_progress:
                    self.on_file_progress(from_peer, file_id, 
                                        transfer_info["bytes_received"], 
                                        transfer_info["filesize"])
            except IOError as e:
                # Handle disk full, permission errors, etc.
                import logging
                logging.error("Error writing file chunk: %s", e)
                
                # Close file handle
                try:
                    transfer_info["file_handle"].close()
                except:
                    pass
                
                # Notify about error
                if self.on_file_error:
                    self.on_file_error(from_peer, file_id, f"Write error: {e}")
                
                # Clean up
                del self.active_file_transfers[file_id]
    
    def _handle_file_complete(self, from_peer: str, file_id: str, total_chunks: int):
        """Internal handler for file transfer completion."""
        if file_id not in self.active_file_transfers:
            return
        
        transfer_info = self.active_file_transfers[file_id]
        
        # Close file handle
        if "file_handle" in transfer_info:
            try:
                transfer_info["file_handle"].close()
            except Exception as e:
                import logging
                logging.warning("Error closing file handle: %s", e)
        
        transfer_info["status"] = "complete"
        
        # Notify application
        if self.on_file_complete:
            self.on_file_complete(from_peer, file_id, transfer_info.get("filename", "unknown"))
        
        # Clean up
        del self.active_file_transfers[file_id]
    
    def _handle_file_error(self, from_peer: str, file_id: str, error: str):
        """Internal handler for file transfer errors."""
        if file_id in self.active_file_transfers:
            transfer_info = self.active_file_transfers[file_id]
            
            # Close file handle if open
            if "file_handle" in transfer_info:
                try:
                    transfer_info["file_handle"].close()
                except Exception as e:
                    import logging
                    logging.warning("Error closing file handle: %s", e)
            
            # Notify application
            if self.on_file_error:
                self.on_file_error(from_peer, file_id, error)
            
            # Clean up
            del self.active_file_transfers[file_id]
