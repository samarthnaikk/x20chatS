# Source Code

This directory contains the main source code for the P2P texting application.

## Structure

```
src/
├── main.py              # Entry point script
└── p2p_texting/         # Main package
    ├── __init__.py      # Package initialization
    ├── peer.py          # Peer coordinator class
    ├── peer_discovery.py # UDP broadcast discovery
    ├── messaging.py     # TCP message exchange
    └── cli.py           # Command-line interface
```

## Modules

### `main.py`
Entry point for the application. Run with:
```bash
python src/main.py [peer-id]
```

### `p2p_texting` Package

#### `peer.py`
Main `Peer` class that coordinates discovery and messaging services.
- Manages peer lifecycle
- Provides simple API for applications
- Handles callbacks and events

#### `peer_discovery.py`
`PeerDiscovery` class implementing UDP broadcast-based peer discovery.
- Broadcasts peer presence every 5 seconds
- Listens for broadcasts from other peers
- Maintains list of known peers with timeout

#### `messaging.py`
`MessagingService` class implementing TCP socket messaging.
- Listens for incoming connections
- Sends messages to other peers
- JSON-based message protocol
- Concurrent connection handling

#### `cli.py`
`CLI` class providing command-line interface.
- Interactive command prompt
- Commands: list, send, help, quit
- Real-time peer discovery notifications
- Real-time message display

## Running the Application

```bash
# Start a peer
python src/main.py my-peer-id

# Or let it auto-generate an ID
python src/main.py
```

## Dependencies

The application uses only Python standard library:
- `socket` - Network communication
- `json` - Message serialization
- `threading` - Concurrent operations
- `logging` - Error and event logging
- `uuid` - Peer ID generation
