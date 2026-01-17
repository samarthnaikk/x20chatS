# Peer Discovery Documentation

## Overview

The P2P texting application uses **UDP broadcast** for peer discovery. This allows peers to find each other on a local network without requiring a central server.

## How It Works

### Discovery Process

1. **Broadcasting Presence**
   - Each peer periodically broadcasts its presence on the network
   - Broadcasts are sent via UDP to port **37020**
   - Broadcast interval: **5 seconds**
   - Broadcast message contains:
     - Peer ID (unique identifier)
     - TCP port number for messaging

2. **Listening for Peers**
   - Each peer listens for UDP broadcasts on port 37020
   - When a broadcast is received, the peer extracts:
     - Peer ID of the sender
     - IP address (from UDP packet source)
     - TCP port for messaging
   - New peers are added to the known peers list

3. **Maintaining Peer List**
   - Peers track the last time they received a broadcast from each known peer
   - Peers not seen for **30 seconds** are removed from the list
   - This ensures the peer list stays current

### Technical Details

**Protocol**: UDP (User Datagram Protocol)
- Connectionless, suitable for broadcast
- Low overhead for discovery messages
- No reliability needed (periodic broadcasts ensure eventual discovery)

**Broadcast Address**: `<broadcast>` (255.255.255.255)
- Sends to all devices on the local network
- Works within the same subnet/LAN

**Message Format** (JSON):
```json
{
  "type": "PEER_DISCOVERY",
  "peer_id": "abc123",
  "port": 54321
}
```

### Network Requirements

- Peers must be on the same local network (LAN)
- UDP port 37020 must be open for broadcast/listening
- No firewall blocking UDP broadcasts
- Router/switch must allow broadcast traffic

### Limitations

1. **LAN Only**: Broadcast discovery only works within a local network
2. **No NAT Traversal**: Cannot discover peers across the internet
3. **Subnet Boundaries**: Limited to broadcast domain
4. **No Security**: Discovery messages are unencrypted and unauthenticated

### Future Enhancements

Possible improvements for peer discovery:
- DHT (Distributed Hash Table) for internet-wide discovery
- STUN/TURN servers for NAT traversal
- Multicast DNS (mDNS) for more efficient local discovery
- Bootstrap nodes for initial peer discovery
