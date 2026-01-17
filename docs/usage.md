# Usage Guide

## Installation

1. Clone the repository:
```bash
git clone https://github.com/samarthnaikk/x20chatS.git
cd x20chatS
```

2. Ensure Python 3.8+ is installed:
```bash
python --version
```

3. No external dependencies required (uses Python standard library only)

## Running the Application

### Starting a Peer

To start a peer with an auto-generated ID:
```bash
python src/main.py
```

To start a peer with a specific ID:
```bash
python src/main.py my-peer-id
```

### Initial Output

When you start the application, you'll see:
```
============================================================
P2P Texting Application
============================================================
Starting peer with ID: abc12345
Listening on port: 54321
Broadcasting presence on the network...

Type 'help' for available commands.

[abc12345]>
```

## Commands

The CLI provides the following commands:

### `help`
Display available commands and their usage.

Example:
```
[abc12345]> help
```

### `list`
List all currently known peers on the network.

Example:
```
[abc12345]> list

Known peers (2):
  - peer-001 at 192.168.1.100:54322
  - peer-002 at 192.168.1.101:54323
```

### `send <peer_id>`
Send a text message to a specific peer.

Example:
```
[abc12345]> send peer-001
Enter message for peer-001 (press Enter to send):
> Hello, this is a test message!
Message sent to peer-001.
```

### `quit` or `exit`
Exit the application gracefully.

Example:
```
[abc12345]> quit
Stopping peer...
Goodbye!
```

## Testing with Multiple Peers

### Same Machine Test

To test the application on a single machine, open multiple terminal windows:

**Terminal 1:**
```bash
python src/main.py peer-1
```

**Terminal 2:**
```bash
python src/main.py peer-2
```

Wait a few seconds for discovery, then use `list` to see discovered peers.

### Multiple Machines Test

To test across different machines on the same network:

**Machine 1:**
```bash
python src/main.py machine-1
```

**Machine 2:**
```bash
python src/main.py machine-2
```

Both peers should discover each other within 5-10 seconds.

## Example Session

Here's a complete example of two peers communicating:

**Peer 1 (peer-alice):**
```
[peer-alice]> list

Known peers (1):
  - peer-bob at 192.168.1.100:54322

[peer-alice]> send peer-bob
Enter message for peer-bob (press Enter to send):
> Hi Bob! How are you?
Message sent to peer-bob.

[Message from peer-bob]: I'm doing great, thanks Alice!

[peer-alice]> quit
```

**Peer 2 (peer-bob):**
```
[+] Peer discovered: peer-alice at 192.168.1.101:54321

[Message from peer-alice]: Hi Bob! How are you?

[peer-bob]> send peer-alice
Enter message for peer-alice (press Enter to send):
> I'm doing great, thanks Alice!
Message sent to peer-alice.

[peer-bob]> quit
```

## Troubleshooting

### Peers Not Discovering Each Other

1. **Check network connection**: Ensure both peers are on the same local network
2. **Check firewall**: Disable firewall or allow UDP port 37020
3. **Wait longer**: Discovery can take up to 10 seconds
4. **Check subnet**: Peers must be in the same broadcast domain

### Messages Not Sending

1. **Verify peer is listed**: Use `list` command to confirm peer is discovered
2. **Check connection**: Ensure the target peer is still running
3. **Network issues**: Check for network connectivity problems
4. **Firewall**: Ensure TCP connections are allowed

### Port Already in Use

If you get a "port already in use" error:
- The application uses dynamic ports by default
- If manually specifying ports, ensure they're not already in use
- Check for other instances of the application running

## Network Requirements

- **Same LAN**: Peers must be on the same local network
- **UDP Port 37020**: Must be open for broadcast discovery
- **Dynamic TCP Ports**: Used for message exchange (assigned automatically)
- **No NAT**: Direct connectivity required (no internet-based communication)
