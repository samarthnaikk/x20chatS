# P2P Texting Application

A peer-to-peer (P2P) texting application built with Python that enables direct, decentralized communication between users without the need for a central server. This project aims to provide secure, private, and reliable text messaging through a distributed network architecture.

## High-Level Goals

- Create a decentralized messaging system where users can communicate directly
- Ensure privacy and security in peer-to-peer communications
- Build a scalable and maintainable codebase
- Provide an intuitive user experience
- Support cross-platform functionality

## Features

### Current Features (v0.1.0)

- **Peer Discovery**: Automatic discovery of peers on the local network using UDP broadcast
- **Direct Messaging**: Send and receive text messages directly between peers
- **File Sharing**: Send and receive files directly between peers with chunked transfer
- **No Central Server**: Fully decentralized architecture
- **Modern TUI**: Interactive terminal user interface with real-time updates
- **CLI Interface**: Simple command-line interface also available
- **Real-time Updates**: Immediate notification of new peers and messages
- **Multi-peer Support**: Communicate with multiple peers simultaneously
- **Color-coded Messages**: Visual distinction between sent and received messages
- **File Transfer Progress**: Visual feedback for file transfers with accept/reject prompts

### Future Features

- Message encryption and security
- User authentication
- Message persistence and history
- GUI interface
- Cross-network communication (NAT traversal)
- Group chats
- File transfer pause/resume
- File encryption
- Transfer history persistence

## Architecture

The application uses a decentralized architecture with three main components:

1. **Peer Discovery**: UDP broadcast-based discovery (port 37020) for finding peers on LAN
2. **Messaging**: TCP socket-based messaging for reliable message delivery
3. **File Sharing**: Chunked file transfer over TCP with metadata exchange

For detailed architecture documentation, see [docs/architecture.md](docs/architecture.md).

## Setup

### Requirements

- Python 3.8 or higher
- Textual library for TUI (install via requirements.txt)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/samarthnaikk/x20chatS.git
cd x20chatS
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python src/main.py
```

Or with a custom peer ID:
```bash
python src/main.py my-peer-name
```

To use the old CLI interface:
```bash
python src/main.py --cli
```

### Quick Start

1. **Start first peer** (Terminal 1):
```bash
python src/main.py peer-1
```

2. **Start second peer** (Terminal 2):
```bash
python src/main.py peer-2
```

3. **Use the TUI**:
   - Select a peer using arrow keys
   - Type your message in the input box
   - Press Enter to send
   - Press Ctrl+F to send a file
   - Press Ctrl+Y to accept incoming file / Ctrl+N to reject

For the old CLI interface:
```bash
python src/main.py peer-1 --cli
```

Then list peers and send messages:
```
[peer-1]> list
[peer-1]> send peer-2
Enter message for peer-2 (press Enter to send):
> Hello from peer-1!
```

For complete usage instructions, see [docs/usage.md](docs/usage.md) and [docs/tui.md](docs/tui.md).

## Documentation

- [TUI Guide](docs/tui.md) - Terminal User Interface guide and features
- [Usage Guide](docs/usage.md) - How to use the application
- [Peer Discovery](docs/peer_discovery.md) - How peer discovery works
- [Architecture](docs/architecture.md) - System design and technical details

## Project Structure

```
p2p-texting/
│
├── src/            # Main source code
├── docs/           # Documentation
├── tests/          # Test files
├── scripts/        # Utility scripts
├── data/           # Data files and storage
├── .gitignore      # Git ignore rules
├── README.md       # This file
├── requirements.txt # Python dependencies
├── pyproject.toml  # Python project configuration
└── LICENSE         # License file
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.