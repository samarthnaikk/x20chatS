# Architecture Documentation

## System Overview

The P2P Texting Application is built as a decentralized messaging system where peers communicate directly without a central server. The architecture consists of three main components:

1. **Peer Discovery** - Finding other peers on the network
2. **Messaging** - Sending and receiving text messages
3. **CLI Interface** - User interaction layer

## Component Architecture

```
┌─────────────────────────────────────────────────┐
│                  CLI Interface                   │
│           (User Commands & Display)              │
└───────────────┬─────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────┐
│                 Peer Coordinator                 │
│          (peer.py - Main Peer Class)             │
└────────┬──────────────────────────┬─────────────┘
         │                          │
         ▼                          ▼
┌───────────────────┐      ┌──────────────────────┐
│ Peer Discovery    │      │  Messaging Service   │
│  (UDP Broadcast)  │      │   (TCP Sockets)      │
└───────────────────┘      └──────────────────────┘
```

## Module Descriptions

### 1. Peer Discovery (`peer_discovery.py`)

**Purpose**: Discover other peers on the local network

**Technology**: UDP broadcast on port 37020

**Key Features**:
- Broadcasts peer presence every 5 seconds
- Listens for broadcasts from other peers
- Maintains list of known peers with timeout
- Callback notification for new peer discoveries

**Classes**:
- `PeerDiscovery`: Main class handling discovery logic

**Thread Safety**: Uses separate threads for broadcasting and listening

### 2. Messaging Service (`messaging.py`)

**Purpose**: Send and receive text messages between peers

**Technology**: TCP sockets with JSON protocol

**Key Features**:
- TCP server listening for incoming connections
- Send messages to known peers via TCP
- Message length prefixing for reliable transmission
- Handles multiple concurrent connections
- Timeout and error handling

**Classes**:
- `MessagingService`: Main class handling message exchange

**Protocol**:
1. Send 4-byte message length (big-endian)
2. Send JSON message payload
3. Close connection

**Thread Safety**: Each incoming connection handled in separate thread

### 3. Peer Coordinator (`peer.py`)

**Purpose**: Coordinate discovery and messaging services

**Key Features**:
- Manages lifecycle of discovery and messaging services
- Provides simplified API for applications
- Routes callbacks from services to application
- Maintains peer ID and state

**Classes**:
- `Peer`: Main coordinator class

**Public API**:
- `start()`: Start peer services
- `stop()`: Stop peer services
- `send_message(peer_id, message)`: Send message to peer
- `get_known_peers()`: Get list of known peers
- Callbacks: `on_peer_discovered`, `on_message_received`

### 4. CLI Interface (`cli.py`)

**Purpose**: Provide command-line user interface

**Key Features**:
- Interactive command prompt
- Command parsing and execution
- Real-time display of peer discoveries
- Real-time display of incoming messages
- User-friendly error messages

**Classes**:
- `CLI`: Main CLI application class

**Commands**: `help`, `list`, `send <peer_id>`, `quit`

## Data Flow

### Peer Discovery Flow

```
Peer A                          Peer B
  |                               |
  | UDP Broadcast                 |
  | "I'm peer-A on port 54321"    |
  |------------------------------>|
  |                               | (Stores peer-A info)
  |                               |
  | UDP Broadcast                 |
  |     "I'm peer-B on port 54322"|
  |<------------------------------|
  | (Stores peer-B info)          |
```

### Message Exchange Flow

```
Peer A                          Peer B
  |                               |
  | User: send peer-B             |
  | "Hello World"                 |
  |                               |
  | TCP Connect to peer-B:54322   |
  |------------------------------>|
  | Send: [length][JSON payload]  |
  |------------------------------>|
  |                               | Parse & Display Message
  | TCP Close                     |
  |<------------------------------|
```

## Threading Model

Each peer runs multiple threads:

1. **Main Thread**: CLI event loop (user input)
2. **Discovery Broadcast Thread**: Sends UDP broadcasts every 5s
3. **Discovery Listen Thread**: Receives UDP broadcasts
4. **Messaging Listen Thread**: Accepts incoming TCP connections
5. **Message Handler Threads**: One per incoming message (short-lived)

All threads except main thread are daemon threads (auto-terminate on exit).

## Network Protocols

### Discovery Protocol (UDP)

**Port**: 37020 (UDP)

**Message Format**:
```json
{
  "type": "PEER_DISCOVERY",
  "peer_id": "abc12345",
  "port": 54321
}
```

### Messaging Protocol (TCP)

**Port**: Dynamic (assigned by OS)

**Message Format**:
1. 4 bytes: Message length (big-endian integer)
2. N bytes: JSON payload

**JSON Payload**:
```json
{
  "type": "TEXT_MESSAGE",
  "from": "peer-alice",
  "message": "Hello World"
}
```

## Error Handling

### Discovery Errors
- Malformed JSON: Ignored
- Socket errors: Logged if service is running
- Broadcast failures: Logged, continues trying

### Messaging Errors
- Connection timeout (5s): Reported to user
- Connection refused: Reported to user
- Message too large (>4KB): Rejected
- Parse errors: Logged

### Peer Management
- Stale peers (>30s): Automatically removed
- Unknown peer IDs: Error message to user

## Security Considerations

**Current Implementation**:
- No encryption
- No authentication
- No message validation
- Vulnerable to spoofing and eavesdropping

**Future Enhancements**:
- TLS for message encryption
- Public key authentication
- Message signing
- Peer verification

## Performance Characteristics

**Peer Discovery**:
- Time to discover: 0-5 seconds (depends on broadcast timing)
- Discovery overhead: Minimal (small UDP packets every 5s)
- Scalability: Good for small networks (dozens of peers)

**Messaging**:
- Latency: Low (direct TCP connection)
- Throughput: Limited to network bandwidth
- Concurrent messages: Unlimited (thread per connection)

## Limitations

1. **Network Scope**: LAN only (no internet support)
2. **No Persistence**: Messages not stored
3. **No Reliability**: No message acknowledgment or retry
4. **No Security**: Plaintext communication
5. **No NAT Traversal**: Cannot work across NAT boundaries
6. **Simple Protocol**: No advanced features (typing indicators, read receipts, etc.)

## Extension Points

The architecture is designed to be extensible:

1. **Discovery Mechanism**: Replace UDP broadcast with DHT, mDNS, or bootstrap servers
2. **Message Transport**: Add encryption layer (TLS)
3. **Persistence**: Add message history storage
4. **Protocol**: Extend JSON messages with new types
5. **UI**: Replace CLI with GUI or web interface
