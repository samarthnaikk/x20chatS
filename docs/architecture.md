# Architecture Documentation

## System Overview

The P2P Texting Application is built as a decentralized messaging system where peers communicate directly without a central server. The architecture consists of four main components:

1. **Peer Discovery** - Finding other peers on the network
2. **Messaging** - Sending and receiving text messages
3. **File Sharing** - Transferring files between peers
4. **TUI Interface** - User interaction layer

## Component Architecture

```
┌─────────────────────────────────────────────────┐
│                  TUI Interface                   │
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
│                   │      │  - Text Messages     │
│                   │      │  - File Transfers    │
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

**Purpose**: Send and receive text messages and files between peers

**Technology**: TCP sockets with JSON protocol

**Key Features**:
- TCP server listening for incoming connections
- Send messages to known peers via TCP
- Message length prefixing for reliable transmission
- Handles multiple concurrent connections
- Timeout and error handling
- Chunked file transfer support (8KB chunks)
- File metadata exchange (filename, size)

**Classes**:
- `MessagingService`: Main class handling message exchange and file transfers

**Protocol**:
1. Send 4-byte message length (big-endian)
2. Send JSON message payload
3. For file chunks: also send chunk length and binary data
4. Close connection

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
- `send_file(peer_id, file_path)`: Send file to peer
- `accept_file(file_id, save_path)`: Accept incoming file
- `reject_file(file_id)`: Reject incoming file
- `get_known_peers()`: Get list of known peers
- Callbacks: `on_peer_discovered`, `on_message_received`, `on_file_request`, 
  `on_file_response`, `on_file_progress`, `on_file_complete`, `on_file_error`

### 4. TUI Interface (`tui.py`)

**Purpose**: Provide terminal user interface

**Key Features**:
- Interactive visual interface using Textual
- Real-time peer list display
- Conversation view with message history
- Color-coded messages and file events
- Keyboard-driven navigation
- File transfer controls (send, accept, reject)
- Transfer status display

**Classes**:
- `P2PTextingApp`: Main TUI application class
- `MessageDisplay`: Widget for conversation display
- `PeerListView`: Widget for peer list
- `StatusBar`: Widget for status information

**Key Bindings**: 
- `Ctrl+C`: Quit
- `Escape`: Clear input
- `Ctrl+F`: Send file
- `Ctrl+Y`: Accept file
- `Ctrl+N`: Reject file

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

### File Transfer Flow

```
Peer A (Sender)                 Peer B (Receiver)
  |                               |
  | User: send file "test.pdf"    |
  |                               |
  | FILE_REQUEST                  |
  | (filename, size, file_id)     |
  |------------------------------>|
  |                               | Display: "Accept file?"
  |                               | User: Accept
  |                               |
  |            FILE_ACCEPT         |
  |<------------------------------|
  |                               |
  | FILE_CHUNK (0)                |
  | [length][JSON][chunk_len][data]|
  |------------------------------>|
  | FILE_CHUNK (1)                |
  | [length][JSON][chunk_len][data]|
  |------------------------------>|
  | ...                           |
  |                               |
  | FILE_COMPLETE                 |
  | (total_chunks)                |
  |------------------------------>|
  |                               | File saved successfully
```

## Threading Model

Each peer runs multiple threads:

1. **Main Thread**: TUI event loop (user input and display)
2. **Discovery Broadcast Thread**: Sends UDP broadcasts every 5s
3. **Discovery Listen Thread**: Receives UDP broadcasts
4. **Messaging Listen Thread**: Accepts incoming TCP connections
5. **Message Handler Threads**: One per incoming message (short-lived)
6. **File Transfer Threads**: One per outgoing file transfer (long-lived during transfer)
7. **Peer List Update Thread**: Updates TUI peer list every 2s

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

### File Transfer Protocol (TCP)

**Port**: Dynamic (same as messaging)

**Message Types**:

1. **FILE_REQUEST**: Initial request to send a file
```json
{
  "type": "FILE_REQUEST",
  "from": "peer-alice",
  "file_id": "abc12345",
  "filename": "document.pdf",
  "filesize": 1048576
}
```

2. **FILE_ACCEPT/FILE_REJECT**: Response to file request
```json
{
  "type": "FILE_ACCEPT",
  "from": "peer-bob",
  "file_id": "abc12345",
  "save_path": "/path/to/save"
}
```

3. **FILE_CHUNK**: Binary file data chunk
```
[4 bytes: JSON length][JSON metadata][4 bytes: chunk length][chunk data]
```
JSON metadata:
```json
{
  "type": "FILE_CHUNK",
  "from": "peer-alice",
  "file_id": "abc12345",
  "chunk_num": 0
}
```

4. **FILE_COMPLETE**: Transfer completion
```json
{
  "type": "FILE_COMPLETE",
  "from": "peer-alice",
  "file_id": "abc12345",
  "total_chunks": 128
}
```

5. **FILE_ERROR**: Transfer error
```json
{
  "type": "FILE_ERROR",
  "from": "peer-alice",
  "file_id": "abc12345",
  "error": "Connection lost"
}
```

**Transfer Parameters**:
- Chunk size: 8KB (8192 bytes)
- Timeout: 30 seconds for file transfers
- Files transferred sequentially (no parallelism within a single transfer)

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

### File Transfer Errors
- File not found: Reported to user
- Connection timeout (30s): Transfer aborted
- Write errors: Transfer aborted, partial file may remain
- Receiver rejection: Notified to sender
- Disk full: Error during chunk write
- Network interruption: Transfer fails with FILE_ERROR message

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
2. **No Persistence**: Messages and file transfers not stored/resumable
3. **No Reliability**: No message acknowledgment or retry
4. **No Security**: Plaintext communication (messages and files)
5. **No NAT Traversal**: Cannot work across NAT boundaries
6. **Simple Protocol**: No advanced features (typing indicators, read receipts, etc.)
7. **Sequential Transfers**: One file transfer per connection
8. **No Compression**: Files transferred as-is
9. **Memory Usage**: Files read/written in chunks but full path validation only

## Extension Points

The architecture is designed to be extensible:

1. **Discovery Mechanism**: Replace UDP broadcast with DHT, mDNS, or bootstrap servers
2. **Message Transport**: Add encryption layer (TLS)
3. **Persistence**: Add message history storage and resumable transfers
4. **Protocol**: Extend JSON messages with new types
5. **UI**: Replace TUI with GUI or web interface
6. **File Transfer**: Add compression, encryption, parallel transfers, resume capability
