# Terminal User Interface (TUI) Guide

## Overview

The P2P Texting Application features a modern Terminal User Interface (TUI) built with [Textual](https://textual.textualize.io/), providing an intuitive and visually appealing way to interact with the peer-to-peer messaging system directly from your terminal.

## Features

- **Real-time peer discovery**: Automatically displays newly discovered peers
- **Interactive message display**: Color-coded messages for easy distinction
- **Keyboard-driven navigation**: No mouse required
- **Status bar**: Shows connection state, peer ID, and network information
- **Persistent conversations**: Message history maintained per peer during the session

## Layout

The TUI uses a clean 3-panel layout:

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  P2P Chat | ID: peer-1 | ● Online | Peers: 2 | Port: 12345             ┃
┣━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ Peers              ┃ Conversation with peer-2                          ┃
┃━━━━━━━━━━━━━━━━━━━━┃━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┃
┃ ● peer-2           ┃ [14:23:45] peer-2: Hello!                         ┃
┃ ● peer-3           ┃ [14:23:47] You: Hi there! 👋                      ┃
┃                    ┃ [14:23:50] peer-2: How are you?                   ┃
┃                    ┃ [14:23:55] You: Great, thanks!                    ┃
┃                    ┃                                                   ┃
┣━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ Type a message...                                                       ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### Panels

1. **Status Bar (Top)**
   - Application name
   - Your peer ID
   - Online/Offline status (color-coded)
   - Number of discovered peers
   - Listening port number

2. **Left Panel: Peer List**
   - Shows all discovered peers
   - Green indicator (●) for online peers
   - Select peers using arrow keys or Tab
   - Highlighted peer is the active conversation

3. **Right Panel: Conversation Area**
   - Displays messages for the selected peer
   - Shows timestamps for each message
   - Color-coded messages:
     - **Cyan**: Your sent messages
     - **Yellow**: Received messages from peer
   - Auto-scrolls to show latest messages

4. **Bottom: Input Box**
   - Type your message here
   - Press Enter to send
   - Press Esc to clear

## Keyboard Controls

| Key           | Action                          |
|---------------|---------------------------------|
| `↑` / `↓`     | Navigate peer list              |
| `Tab`         | Navigate between UI elements    |
| `Enter`       | Send message                    |
| `Esc`         | Clear input field               |
| `Ctrl+C`      | Exit application                |

## Color Scheme

The TUI uses a dark theme optimized for terminal readability:

- **Background**: Dark (terminal default)
- **Primary text**: Light/White
- **Sent messages**: Cyan
- **Received messages**: Yellow
- **Online status**: Green (●)
- **UI borders**: Primary theme color
- **Highlights**: Accent color for selected items

Colors degrade gracefully on terminals with limited color support.

## Usage

### Starting the TUI

Launch the application with the TUI interface (default):

```bash
python src/main.py
```

Or specify a custom peer ID:

```bash
python src/main.py my-peer-name
```

### Using the Old CLI Interface

If you prefer the old command-line interface, use the `--cli` flag:

```bash
python src/main.py --cli
```

### Sending Messages

1. **Select a peer**: Use arrow keys to highlight a peer in the left panel
2. **Type your message**: Click in the input box or start typing
3. **Send**: Press Enter to send the message
4. **View conversation**: Messages appear in the conversation panel on the right

### Peer Discovery

- Peers are automatically discovered on your local network
- New peers appear in the peer list within seconds
- The status bar shows the total number of discovered peers
- Stale peers (not seen in 30+ seconds) are automatically removed

### Exiting

Press `Ctrl+C` to cleanly exit the application. This will:
1. Stop the peer discovery service
2. Close the messaging service
3. Clean up network resources
4. Exit the TUI

## Requirements

- Python 3.8 or higher
- Textual library (installed via `requirements.txt`)
- Terminal with ANSI color support (most modern terminals)

## Terminal Compatibility

The TUI has been tested and works well on:

- **Linux**: GNOME Terminal, Konsole, xterm, kitty, alacritty
- **macOS**: Terminal.app, iTerm2
- **Windows**: Windows Terminal, PowerShell (with color support)

For best results, use a terminal with:
- At least 120x30 characters size
- 256-color support or true color
- Unicode support (for proper borders and symbols)

## Troubleshooting

### Layout Issues

If the TUI doesn't display correctly:
- Ensure your terminal window is large enough (minimum 80x24)
- Check that your terminal supports ANSI escape codes
- Try resizing the terminal window

### Colors Not Showing

If colors don't appear:
- Verify your terminal supports 256 colors: `echo $TERM`
- Try setting: `export TERM=xterm-256color`
- The TUI will work without colors but may look less appealing

### Keyboard Not Working

If keyboard controls don't respond:
- Make sure the input field is focused (click it or press Tab)
- Check that no other application is capturing keyboard input
- Try restarting the application

### Peer Discovery Issues

If peers aren't discovered:
- Ensure both peers are on the same local network
- Check firewall settings (UDP port 37020, TCP dynamic ports)
- Review logs with the CLI version: `python src/main.py --cli`

## Technical Details

The TUI is implemented using:

- **Framework**: Textual 0.47.0+
- **Architecture**: Event-driven with reactive updates
- **Threading**: Background thread for peer list updates
- **Integration**: Clean separation from P2P networking layer

The TUI does not modify any P2P networking logic and sits as a pure presentation layer on top of the existing `Peer`, `PeerDiscovery`, and `MessagingService` classes.

## Future Enhancements

Potential improvements for future versions:

- Message history persistence
- Notification sounds
- Custom color themes
- Mouse support for clicking peers
- Message search functionality
- Multi-peer group chat view
- File transfer progress indicators
- Emoji picker
- Customizable keybindings

## Related Documentation

- [Usage Guide](usage.md) - General application usage
- [Peer Discovery](peer_discovery.md) - How peer discovery works
- [Architecture](architecture.md) - System design and technical details
