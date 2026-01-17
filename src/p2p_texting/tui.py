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
    
    def add_message(self, sender: str, text: str, is_sent: bool = False):
        """Add a message to the display."""
        self.messages.append({
            "sender": sender,
            "text": text,
            "is_sent": is_sent,
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
            if msg["is_sent"]:
                # Sent messages in cyan
                lines.append(f"[cyan][{msg['timestamp']}] You: {msg['text']}[/cyan]")
            else:
                # Received messages in yellow
                lines.append(f"[yellow][{msg['timestamp']}] {msg['sender']}: {msg['text']}[/yellow]")
        
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
    ]
    
    def __init__(self, peer_id: Optional[str] = None):
        super().__init__()
        self.peer_id = peer_id
        self.peer: Optional[Peer] = None
        self.selected_peer: Optional[str] = None
        self.peer_conversations = {}  # peer_id -> list of messages
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
            "is_sent": False
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
                    msg["is_sent"]
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
        
        # Send message
        success = self.peer.send_message(self.selected_peer, message)
        
        if success:
            # Store in conversation history
            if self.selected_peer not in self.peer_conversations:
                self.peer_conversations[self.selected_peer] = []
            self.peer_conversations[self.selected_peer].append({
                "sender": "You",
                "text": message,
                "is_sent": True
            })
            
            # Update display
            self.update_conversation_display()
        
        # Clear input
        event.input.value = ""
    
    def action_clear_input(self) -> None:
        """Clear the input field."""
        input_widget = self.query_one("#message-input", Input)
        input_widget.value = ""
    
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
