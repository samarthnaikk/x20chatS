"""
TUI Module

Terminal User Interface for the P2P texting application using Textual.
Provides a clean, interactive interface for peer-to-peer messaging.
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Input, Static, ListView, ListItem, Label
from textual.binding import Binding
from textual.reactive import reactive
from textual.message import Message
from typing import Optional
import threading
import time

from .peer import Peer


class MessageDisplay(Static):
    """Widget to display messages in the conversation area."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.messages = []
    
    def add_message(self, sender: str, text: str, is_sent: bool = False, msg_type: str = "text"):
        """Add a message to the display.
        
        Args:
            sender: Name of the sender
            text: Message text or file event description
            is_sent: True if sent by this peer
            msg_type: Type of message ('text', 'file_request', 'file_accepted', 
                     'file_rejected', 'file_complete', 'file_error', 'file_progress')
        """
        self.messages.append({
            "sender": sender,
            "text": text,
            "is_sent": is_sent,
            "msg_type": msg_type,
            "timestamp": time.strftime("%H:%M:%S")
        })
        self.update_display()
    
    def clear_messages(self):
        """Clear all messages."""
        self.messages = []
        self.update_display()
    
    def update_display(self):
        """Update the message display."""
        if not self.messages:
            self.update("[dim]No messages yet. Select a peer and start chatting![/dim]")
            return
        
        lines = []
        for msg in self.messages:
            timestamp = f"[{msg['timestamp']}]"
            
            if msg["msg_type"] == "text":
                if msg["is_sent"]:
                    # Sent messages in cyan
                    lines.append(f"[cyan]{timestamp} You: {msg['text']}[/cyan]")
                else:
                    # Received messages in yellow
                    lines.append(f"[yellow]{timestamp} {msg['sender']}: {msg['text']}[/yellow]")
            
            elif msg["msg_type"] == "file_request":
                # File requests in magenta
                lines.append(f"[magenta]{timestamp} 📁 {msg['text']}[/magenta]")
            
            elif msg["msg_type"] == "file_accepted":
                # File accepted in green
                lines.append(f"[green]{timestamp} ✓ {msg['text']}[/green]")
            
            elif msg["msg_type"] == "file_rejected":
                # File rejected in red
                lines.append(f"[red]{timestamp} ✗ {msg['text']}[/red]")
            
            elif msg["msg_type"] == "file_complete":
                # File complete in bright green
                lines.append(f"[bright_green]{timestamp} ✓ {msg['text']}[/bright_green]")
            
            elif msg["msg_type"] == "file_error":
                # File error in red
                lines.append(f"[red]{timestamp} ⚠ {msg['text']}[/red]")
            
            elif msg["msg_type"] == "file_progress":
                # File progress in blue
                lines.append(f"[blue]{timestamp} ⏳ {msg['text']}[/blue]")
        
        self.update("\n".join(lines))


class PeerListView(ListView):
    """Widget to display the list of discovered peers."""
    
    class PeerSelected(Message):
        """Message sent when a peer is selected."""
        
        def __init__(self, peer_id: Optional[str]) -> None:
            self.peer_id = peer_id
            super().__init__()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.peer_ids = []
    
    def update_peers(self, peers: dict):
        """Update the peer list."""
        self.clear()
        self.peer_ids = []
        
        if not peers:
            self.append(ListItem(Label("[dim]No peers discovered yet[/dim]")))
        else:
            for peer_id, info in sorted(peers.items()):
                self.peer_ids.append(peer_id)
                status = "[green]●[/green] " if info else "[red]●[/red] "
                self.append(ListItem(Label(f"{status}{peer_id}")))
    
    def get_selected_peer(self) -> Optional[str]:
        """Get the currently selected peer ID."""
        if self.index is not None and 0 <= self.index < len(self.peer_ids):
            return self.peer_ids[self.index]
        return None
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle peer selection."""
        peer_id = self.get_selected_peer()
        self.post_message(self.PeerSelected(peer_id))


class StatusBar(Static):
    """Status bar showing connection info."""
    
    def __init__(self, peer_id: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.peer_id = peer_id
        self.peer_count = 0
        self.port = 0
        self.update_status()
    
    def update_info(self, peer_count: int, port: int):
        """Update status information."""
        self.peer_count = peer_count
        self.port = port
        self.update_status()
    
    def update_status(self):
        """Update the status bar display."""
        status = "[green]● Online[/green]"
        peer_text = f"Peers: {self.peer_count}"
        port_text = f"Port: {self.port}" if self.port else "Port: -"
        self.update(f"[bold]P2P Chat[/bold] | ID: {self.peer_id} | {status} | {peer_text} | {port_text}")


class P2PTextingApp(App):
    """Main TUI application for P2P texting."""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #main-container {
        width: 100%;
        height: 100%;
    }
    
    #content-container {
        height: 1fr;
    }
    
    #left-panel {
        width: 30;
        border: solid $primary;
        padding: 1;
    }
    
    #right-panel {
        width: 1fr;
        border: solid $primary;
    }
    
    #conversation-area {
        height: 1fr;
        padding: 1;
        overflow-y: auto;
    }
    
    #input-container {
        height: 3;
        border-top: solid $primary;
        padding: 0 1;
    }
    
    #status-bar {
        height: 1;
        background: $boost;
        color: $text;
        padding: 0 1;
    }
    
    PeerListView {
        height: 1fr;
    }
    
    PeerListView > ListItem {
        padding: 0 1;
    }
    
    PeerListView > ListItem.--highlight {
        background: $accent;
    }
    
    Input {
        width: 100%;
    }
    
    #peer-title {
        text-style: bold;
        background: $boost;
        padding: 0 1;
        margin-bottom: 1;
    }
    
    #conversation-title {
        text-style: bold;
        background: $boost;
        padding: 0 1;
        margin-bottom: 1;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("escape", "clear_input", "Clear", show=True),
        Binding("ctrl+f", "send_file", "Send File", show=True),
        Binding("ctrl+y", "accept_file", "Accept", show=False),
        Binding("ctrl+n", "reject_file", "Reject", show=False),
    ]
    
    def __init__(self, peer_id: Optional[str] = None):
        super().__init__()
        self.peer_id = peer_id
        self.peer: Optional[Peer] = None
        self.selected_peer: Optional[str] = None
        self.peer_conversations = {}  # peer_id -> list of messages
        self.pending_file_requests = {}  # file_id -> request info
        self._file_send_mode = False  # Flag for file path input mode
        self.update_thread = None
        self.running = False
    
    def compose(self) -> ComposeResult:
        """Create the UI layout."""
        yield StatusBar(self.peer_id or "unknown", id="status-bar")
        
        with Container(id="main-container"):
            with Horizontal(id="content-container"):
                # Left panel - Peer list
                with Vertical(id="left-panel"):
                    yield Static("Peers", id="peer-title")
                    yield PeerListView(id="peer-list")
                
                # Right panel - Conversation and input
                with Vertical(id="right-panel"):
                    yield Static("Conversation", id="conversation-title")
                    yield MessageDisplay(id="conversation-area")
                    with Container(id="input-container"):
                        yield Input(placeholder="Type a message...", id="message-input")
    
    def on_mount(self) -> None:
        """Initialize the app when mounted."""
        # Start the P2P peer
        self.peer = Peer(peer_id=self.peer_id)
        self.peer.on_peer_discovered = self.handle_peer_discovered
        self.peer.on_message_received = self.handle_message_received
        self.peer.on_file_request = self.handle_file_request
        self.peer.on_file_response = self.handle_file_response
        self.peer.on_file_progress = self.handle_file_progress
        self.peer.on_file_complete = self.handle_file_complete
        self.peer.on_file_error = self.handle_file_error
        self.peer.start()
        
        # Update status bar
        status_bar = self.query_one("#status-bar", StatusBar)
        status_bar.peer_id = self.peer.peer_id
        status_bar.port = self.peer.port
        status_bar.update_status()
        
        # Start background update thread
        self.running = True
        self.update_thread = threading.Thread(target=self._update_peers_loop, daemon=True)
        self.update_thread.start()
        
        # Focus the input
        self.query_one("#message-input", Input).focus()
    
    def _update_peers_loop(self):
        """Background thread to update peer list periodically."""
        while self.running:
            try:
                self.call_from_thread(self.update_peer_list)
                time.sleep(2)  # Update every 2 seconds
            except Exception as e:
                # Log errors but continue running
                import logging
                logging.error(f"Error updating peer list: {e}")
                time.sleep(2)
    
    def update_peer_list(self):
        """Update the peer list display."""
        if not self.peer:
            return
        
        peers = self.peer.get_known_peers()
        peer_list = self.query_one("#peer-list", PeerListView)
        peer_list.update_peers(peers)
        
        # Update status bar
        status_bar = self.query_one("#status-bar", StatusBar)
        status_bar.update_info(len(peers), self.peer.port)
    
    def handle_peer_discovered(self, peer_id: str, ip: str, port: int):
        """Handle discovery of a new peer."""
        self.call_from_thread(self.update_peer_list)
    
    def handle_message_received(self, from_peer: str, message: str):
        """Handle received message."""
        # Store message in conversation history
        if from_peer not in self.peer_conversations:
            self.peer_conversations[from_peer] = []
        self.peer_conversations[from_peer].append({
            "sender": from_peer,
            "text": message,
            "is_sent": False,
            "msg_type": "text"
        })
        
        # Update display if this peer is selected
        if self.selected_peer == from_peer:
            self.call_from_thread(self.update_conversation_display)
    
    def handle_file_request(self, from_peer: str, file_id: str, filename: str, filesize: int):
        """Handle incoming file transfer request."""
        # Store pending request
        self.pending_file_requests[file_id] = {
            "from_peer": from_peer,
            "filename": filename,
            "filesize": filesize
        }
        
        # Add to conversation
        if from_peer not in self.peer_conversations:
            self.peer_conversations[from_peer] = []
        
        size_mb = filesize / (1024 * 1024)
        self.peer_conversations[from_peer].append({
            "sender": from_peer,
            "text": f"wants to send file '{filename}' ({size_mb:.2f} MB) - Press Ctrl+Y to accept, Ctrl+N to reject",
            "is_sent": False,
            "msg_type": "file_request"
        })
        
        # Update display if this peer is selected
        if self.selected_peer == from_peer:
            self.call_from_thread(self.update_conversation_display)
    
    def handle_file_response(self, from_peer: str, file_id: str, accepted: bool, save_path: str):
        """Handle file transfer response."""
        if from_peer not in self.peer_conversations:
            self.peer_conversations[from_peer] = []
        
        if accepted:
            self.peer_conversations[from_peer].append({
                "sender": from_peer,
                "text": f"{from_peer} accepted the file transfer",
                "is_sent": False,
                "msg_type": "file_accepted"
            })
        else:
            self.peer_conversations[from_peer].append({
                "sender": from_peer,
                "text": f"{from_peer} rejected the file transfer",
                "is_sent": False,
                "msg_type": "file_rejected"
            })
        
        # Update display if this peer is selected
        if self.selected_peer == from_peer:
            self.call_from_thread(self.update_conversation_display)
    
    def handle_file_progress(self, from_peer: str, file_id: str, bytes_received: int, total_bytes: int):
        """Handle file transfer progress."""
        # Update progress in conversation (optional, could spam the display)
        # For now, we'll skip detailed progress updates
        pass
    
    def handle_file_complete(self, from_peer: str, file_id: str, filename: str):
        """Handle file transfer completion."""
        if from_peer not in self.peer_conversations:
            self.peer_conversations[from_peer] = []
        
        self.peer_conversations[from_peer].append({
            "sender": from_peer,
            "text": f"File '{filename}' transfer complete",
            "is_sent": False,
            "msg_type": "file_complete"
        })
        
        # Update display if this peer is selected
        if self.selected_peer == from_peer:
            self.call_from_thread(self.update_conversation_display)
    
    def handle_file_error(self, from_peer: str, file_id: str, error: str):
        """Handle file transfer error."""
        if from_peer not in self.peer_conversations:
            self.peer_conversations[from_peer] = []
        
        self.peer_conversations[from_peer].append({
            "sender": from_peer,
            "text": f"File transfer error: {error}",
            "is_sent": False,
            "msg_type": "file_error"
        })
        
        # Update display if this peer is selected
        if self.selected_peer == from_peer:
            self.call_from_thread(self.update_conversation_display)
    
    def on_peer_list_view_peer_selected(self, message: PeerListView.PeerSelected) -> None:
        """Handle peer selection from the list."""
        self.selected_peer = message.peer_id
        self.update_conversation_title()
        self.update_conversation_display()
    
    def update_conversation_title(self):
        """Update the conversation title with selected peer."""
        title = self.query_one("#conversation-title", Static)
        if self.selected_peer:
            title.update(f"Conversation with {self.selected_peer}")
        else:
            title.update("Conversation")
    
    def update_conversation_display(self):
        """Update the conversation display."""
        conv_display = self.query_one("#conversation-area", MessageDisplay)
        conv_display.clear_messages()
        
        if self.selected_peer and self.selected_peer in self.peer_conversations:
            for msg in self.peer_conversations[self.selected_peer]:
                conv_display.add_message(
                    msg["sender"],
                    msg["text"],
                    msg["is_sent"],
                    msg.get("msg_type", "text")
                )
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle message input submission."""
        if event.input.id != "message-input":
            return
        
        message = event.value.strip()
        if not message:
            return
        
        if not self.selected_peer:
            event.input.value = ""
            return
        
        # Check if we're in file send mode
        if self._file_send_mode:
            self._file_send_mode = False
            file_path = message
            
            # Reset placeholder
            event.input.placeholder = "Type a message..."
            event.input.value = ""
            
            # Validate file exists
            import os
            if not os.path.exists(file_path):
                if self.selected_peer not in self.peer_conversations:
                    self.peer_conversations[self.selected_peer] = []
                self.peer_conversations[self.selected_peer].append({
                    "sender": "System",
                    "text": f"Error: File '{file_path}' not found",
                    "is_sent": True,
                    "msg_type": "file_error"
                })
                self.update_conversation_display()
                return
            
            # Send file
            file_id = self.peer.send_file(self.selected_peer, file_path)
            
            if file_id:
                # Add to conversation
                if self.selected_peer not in self.peer_conversations:
                    self.peer_conversations[self.selected_peer] = []
                filename = os.path.basename(file_path)
                self.peer_conversations[self.selected_peer].append({
                    "sender": "You",
                    "text": f"Sending file '{filename}'...",
                    "is_sent": True,
                    "msg_type": "file_request"
                })
                self.update_conversation_display()
            else:
                # Error sending
                if self.selected_peer not in self.peer_conversations:
                    self.peer_conversations[self.selected_peer] = []
                self.peer_conversations[self.selected_peer].append({
                    "sender": "System",
                    "text": "Error: Failed to send file request",
                    "is_sent": True,
                    "msg_type": "file_error"
                })
                self.update_conversation_display()
            return
        
        # Normal text message
        success = self.peer.send_message(self.selected_peer, message)
        
        if success:
            # Store in conversation history
            if self.selected_peer not in self.peer_conversations:
                self.peer_conversations[self.selected_peer] = []
            self.peer_conversations[self.selected_peer].append({
                "sender": "You",
                "text": message,
                "is_sent": True,
                "msg_type": "text"
            })
            
            # Update display
            self.update_conversation_display()
        
        # Clear input
        event.input.value = ""
    
    def action_send_file(self) -> None:
        """Action to send a file to selected peer."""
        if not self.selected_peer:
            return
        
        # Create a simple file selection prompt
        import os
        input_widget = self.query_one("#message-input", Input)
        input_widget.placeholder = "Enter file path to send (or press Esc to cancel)..."
        input_widget.value = ""
        
        # We'll handle the file path in a special mode
        self._file_send_mode = True
    
    def action_accept_file(self) -> None:
        """Action to accept the latest file request."""
        if not self.selected_peer:
            return
        
        # Find the most recent file request from this peer
        file_id = None
        for fid in reversed(list(self.pending_file_requests.keys())):
            if self.pending_file_requests[fid]["from_peer"] == self.selected_peer:
                file_id = fid
                break
        
        if not file_id:
            return
        
        # Create data directory if it doesn't exist
        import os
        # Use absolute path relative to project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        data_dir = os.path.join(project_root, "data", "received_files")
        os.makedirs(data_dir, exist_ok=True)
        
        # Sanitize filename to prevent directory traversal
        import os.path
        filename = self.pending_file_requests[file_id]["filename"]
        safe_filename = os.path.basename(filename)  # Remove any path components
        # Remove any remaining dangerous characters
        safe_filename = "".join(c for c in safe_filename if c.isalnum() or c in "._- ")
        if not safe_filename:
            safe_filename = "received_file"
        
        # Save to data directory
        save_path = os.path.join(data_dir, safe_filename)
        
        # Handle duplicate filenames
        if os.path.exists(save_path):
            base, ext = os.path.splitext(safe_filename)
            counter = 1
            while os.path.exists(os.path.join(data_dir, f"{base}_{counter}{ext}")):
                counter += 1
            save_path = os.path.join(data_dir, f"{base}_{counter}{ext}")
        
        # Accept the file
        self.peer.accept_file(file_id, save_path)
        
        # Remove from pending
        del self.pending_file_requests[file_id]
        
        # Add to conversation
        if self.selected_peer not in self.peer_conversations:
            self.peer_conversations[self.selected_peer] = []
        self.peer_conversations[self.selected_peer].append({
            "sender": "You",
            "text": f"Accepted file transfer - saving to {save_path}",
            "is_sent": True,
            "msg_type": "file_accepted"
        })
        self.update_conversation_display()
    
    def action_reject_file(self) -> None:
        """Action to reject the latest file request."""
        if not self.selected_peer:
            return
        
        # Find the most recent file request from this peer
        file_id = None
        for fid in reversed(list(self.pending_file_requests.keys())):
            if self.pending_file_requests[fid]["from_peer"] == self.selected_peer:
                file_id = fid
                break
        
        if not file_id:
            return
        
        # Reject the file
        self.peer.reject_file(file_id)
        
        # Remove from pending
        del self.pending_file_requests[file_id]
        
        # Add to conversation
        if self.selected_peer not in self.peer_conversations:
            self.peer_conversations[self.selected_peer] = []
        self.peer_conversations[self.selected_peer].append({
            "sender": "You",
            "text": "Rejected file transfer",
            "is_sent": True,
            "msg_type": "file_rejected"
        })
        self.update_conversation_display()
    
    def action_clear_input(self) -> None:
        """Clear the input field."""
        input_widget = self.query_one("#message-input", Input)
        input_widget.value = ""
        # Reset file send mode if active
        if self._file_send_mode:
            self._file_send_mode = False
            input_widget.placeholder = "Type a message..."
    
    def action_quit(self) -> None:
        """Quit the application."""
        self.running = False
        if self.peer:
            self.peer.stop()
        self.exit()


def run_tui(peer_id: Optional[str] = None):
    """Run the TUI application."""
    app = P2PTextingApp(peer_id=peer_id)
    app.run()
