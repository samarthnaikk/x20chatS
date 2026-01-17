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
- **No Central Server**: Fully decentralized architecture
- **CLI Interface**: Simple command-line interface for interaction
- **Real-time Updates**: Immediate notification of new peers and messages
- **Multi-peer Support**: Communicate with multiple peers simultaneously

### Future Features

- Message encryption and security
- User authentication
- Message persistence and history
- GUI interface
- Cross-network communication (NAT traversal)
- Group chats
- File sharing

## Architecture

The application uses a decentralized architecture with two main components:

1. **Peer Discovery**: UDP broadcast-based discovery (port 37020) for finding peers on LAN
2. **Messaging**: TCP socket-based messaging for reliable message delivery

For detailed architecture documentation, see [docs/architecture.md](docs/architecture.md).

## Setup

### Requirements

- Python 3.8 or higher
- No external dependencies (uses Python standard library only)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/samarthnaikk/x20chatS.git
cd x20chatS
```

2. Run the application:
```bash
python src/main.py
```

Or with a custom peer ID:
```bash
python src/main.py my-peer-name
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

3. **List discovered peers**:
```
[peer-1]> list
```

4. **Send a message**:
```
[peer-1]> send peer-2
Enter message for peer-2 (press Enter to send):
> Hello from peer-1!
```

For complete usage instructions, see [docs/usage.md](docs/usage.md).

## Documentation

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