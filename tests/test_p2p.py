#!/usr/bin/env python3
"""
Test script to verify P2P messaging functionality.
This script creates two peers and tests message exchange.
"""

import sys
import os
import time

# Add src directory to path
src_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, src_dir)

from p2p_texting.peer import Peer

def test_peer_discovery_and_messaging():
    """Test peer discovery and message exchange."""
    print("=" * 60)
    print("P2P Messaging Test")
    print("=" * 60)
    
    # Track received messages
    peer1_messages = []
    peer2_messages = []
    
    # Create callbacks
    def peer1_on_peer_discovered(peer_id, ip, port):
        print(f"[Peer1] Discovered: {peer_id} at {ip}:{port}")
    
    def peer1_on_message_received(from_peer, message):
        print(f"[Peer1] Message from {from_peer}: {message}")
        peer1_messages.append((from_peer, message))
    
    def peer2_on_peer_discovered(peer_id, ip, port):
        print(f"[Peer2] Discovered: {peer_id} at {ip}:{port}")
    
    def peer2_on_message_received(from_peer, message):
        print(f"[Peer2] Message from {from_peer}: {message}")
        peer2_messages.append((from_peer, message))
    
    # Create two peers
    print("\nCreating peers...")
    peer1 = Peer(peer_id="peer-1")
    peer1.on_peer_discovered = peer1_on_peer_discovered
    peer1.on_message_received = peer1_on_message_received
    
    peer2 = Peer(peer_id="peer-2")
    peer2.on_peer_discovered = peer2_on_peer_discovered
    peer2.on_message_received = peer2_on_message_received
    
    # Start peers
    print("Starting peer-1...")
    peer1.start()
    print(f"Peer-1 listening on port {peer1.port}")
    
    print("Starting peer-2...")
    peer2.start()
    print(f"Peer-2 listening on port {peer2.port}")
    
    # Wait for discovery
    print("\nWaiting for peer discovery (10 seconds)...")
    time.sleep(10)
    
    # Check discovered peers
    print("\n" + "=" * 60)
    print("Discovery Results:")
    print("=" * 60)
    peer1_peers = peer1.get_known_peers()
    peer2_peers = peer2.get_known_peers()
    
    print(f"Peer-1 knows about: {list(peer1_peers.keys())}")
    print(f"Peer-2 knows about: {list(peer2_peers.keys())}")
    
    if "peer-2" not in peer1_peers:
        print("\n❌ FAILED: Peer-1 did not discover Peer-2")
        peer1.stop()
        peer2.stop()
        return False
    
    if "peer-1" not in peer2_peers:
        print("\n❌ FAILED: Peer-2 did not discover Peer-1")
        peer1.stop()
        peer2.stop()
        return False
    
    print("✅ Both peers discovered each other!")
    
    # Test messaging
    print("\n" + "=" * 60)
    print("Testing Messaging:")
    print("=" * 60)
    
    # Peer 1 sends to Peer 2
    print("\nPeer-1 sending message to Peer-2...")
    success1 = peer1.send_message("peer-2", "Hello from Peer-1!")
    if success1:
        print("✅ Message sent successfully")
    else:
        print("❌ Failed to send message")
    
    time.sleep(2)
    
    # Peer 2 sends to Peer 1
    print("\nPeer-2 sending message to Peer-1...")
    success2 = peer2.send_message("peer-1", "Hello from Peer-2!")
    if success2:
        print("✅ Message sent successfully")
    else:
        print("❌ Failed to send message")
    
    time.sleep(2)
    
    # Check received messages
    print("\n" + "=" * 60)
    print("Message Reception Results:")
    print("=" * 60)
    
    print(f"Peer-1 received {len(peer1_messages)} message(s)")
    for from_peer, msg in peer1_messages:
        print(f"  - From {from_peer}: {msg}")
    
    print(f"Peer-2 received {len(peer2_messages)} message(s)")
    for from_peer, msg in peer2_messages:
        print(f"  - From {from_peer}: {msg}")
    
    # Verify results
    success = True
    if len(peer1_messages) == 0:
        print("\n❌ FAILED: Peer-1 did not receive any messages")
        success = False
    if len(peer2_messages) == 0:
        print("\n❌ FAILED: Peer-2 did not receive any messages")
        success = False
    
    # Stop peers
    print("\n" + "=" * 60)
    print("Stopping peers...")
    peer1.stop()
    peer2.stop()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
    
    return success

if __name__ == "__main__":
    try:
        success = test_peer_discovery_and_messaging()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
