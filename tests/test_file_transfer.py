#!/usr/bin/env python3
"""
Test script to verify P2P file transfer functionality.
This script creates two peers and tests file transfer.
"""

import sys
import os
import time
import tempfile

# Add src directory to path
src_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, src_dir)

from p2p_texting.peer import Peer


def test_file_transfer():
    """Test file transfer between two peers."""
    print("=" * 60)
    print("P2P File Transfer Test")
    print("=" * 60)
    
    # Track events
    peer1_events = []
    peer2_events = []
    file_id_holder = [None]  # Use list to allow modification in nested function
    
    # Create callbacks for peer1
    def peer1_on_peer_discovered(peer_id, ip, port):
        print(f"[Peer1] Discovered: {peer_id} at {ip}:{port}")
        peer1_events.append(("peer_discovered", peer_id))
    
    def peer1_on_message_received(from_peer, message):
        print(f"[Peer1] Message from {from_peer}: {message}")
        peer1_events.append(("message", from_peer, message))
    
    def peer1_on_file_response(from_peer, file_id, accepted, save_path):
        print(f"[Peer1] File response from {from_peer}: {'Accepted' if accepted else 'Rejected'}")
        peer1_events.append(("file_response", from_peer, file_id, accepted))
    
    def peer1_on_file_complete(from_peer, file_id, filename):
        print(f"[Peer1] File transfer complete: {filename}")
        peer1_events.append(("file_complete", from_peer, file_id, filename))
    
    def peer1_on_file_error(from_peer, file_id, error):
        print(f"[Peer1] File transfer error: {error}")
        peer1_events.append(("file_error", from_peer, file_id, error))
    
    # Create callbacks for peer2
    def peer2_on_peer_discovered(peer_id, ip, port):
        print(f"[Peer2] Discovered: {peer_id} at {ip}:{port}")
        peer2_events.append(("peer_discovered", peer_id))
    
    def peer2_on_message_received(from_peer, message):
        print(f"[Peer2] Message from {from_peer}: {message}")
        peer2_events.append(("message", from_peer, message))
    
    def peer2_on_file_request(from_peer, file_id, filename, filesize):
        print(f"[Peer2] File request from {from_peer}: {filename} ({filesize} bytes)")
        peer2_events.append(("file_request", from_peer, file_id, filename, filesize))
        file_id_holder[0] = file_id
    
    def peer2_on_file_complete(from_peer, file_id, filename):
        print(f"[Peer2] File transfer complete: {filename}")
        peer2_events.append(("file_complete", from_peer, file_id, filename))
    
    def peer2_on_file_error(from_peer, file_id, error):
        print(f"[Peer2] File transfer error: {error}")
        peer2_events.append(("file_error", from_peer, file_id, error))
    
    # Create two peers
    print("\nCreating peers...")
    peer1 = Peer(peer_id="peer-1")
    peer1.on_peer_discovered = peer1_on_peer_discovered
    peer1.on_message_received = peer1_on_message_received
    peer1.on_file_response = peer1_on_file_response
    peer1.on_file_complete = peer1_on_file_complete
    peer1.on_file_error = peer1_on_file_error
    
    peer2 = Peer(peer_id="peer-2")
    peer2.on_peer_discovered = peer2_on_peer_discovered
    peer2.on_message_received = peer2_on_message_received
    peer2.on_file_request = peer2_on_file_request
    peer2.on_file_complete = peer2_on_file_complete
    peer2.on_file_error = peer2_on_file_error
    
    # Start peers
    print("Starting peers...")
    peer1.start()
    peer2.start()
    
    print(f"Peer1 listening on port {peer1.port}")
    print(f"Peer2 listening on port {peer2.port}")
    
    # Wait for peer discovery
    print("\nWaiting for peer discovery...")
    time.sleep(7)  # Wait for discovery broadcasts
    
    # Check if peers discovered each other
    peer1_peers = peer1.get_known_peers()
    peer2_peers = peer2.get_known_peers()
    
    print(f"\nPeer1 knows about: {list(peer1_peers.keys())}")
    print(f"Peer2 knows about: {list(peer2_peers.keys())}")
    
    if "peer-2" not in peer1_peers or "peer-1" not in peer2_peers:
        print("\n❌ FAIL: Peers did not discover each other")
        peer1.stop()
        peer2.stop()
        return False
    
    print("✓ Peers discovered each other")
    
    # Test text messaging first
    print("\n--- Testing text messaging ---")
    success = peer1.send_message("peer-2", "Hello from peer-1!")
    if success:
        print("✓ Message sent successfully")
    else:
        print("❌ Failed to send message")
        peer1.stop()
        peer2.stop()
        return False
    
    time.sleep(2)
    
    # Create a temporary test file
    print("\n--- Testing file transfer ---")
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        test_file_path = f.name
        f.write("This is a test file for P2P file transfer.\n")
        f.write("Line 2\n")
        f.write("Line 3\n")
    
    print(f"Created test file: {test_file_path}")
    
    # Send file request
    print("Sending file request from peer-1 to peer-2...")
    file_id = peer1.send_file("peer-2", test_file_path)
    
    if not file_id:
        print("❌ FAIL: Failed to send file request")
        os.unlink(test_file_path)
        peer1.stop()
        peer2.stop()
        return False
    
    print(f"✓ File request sent with ID: {file_id}")
    
    # Wait for file request to be received
    time.sleep(2)
    
    # Check if peer2 received the request
    if file_id_holder[0] is None:
        print("❌ FAIL: Peer2 did not receive file request")
        os.unlink(test_file_path)
        peer1.stop()
        peer2.stop()
        return False
    
    print("✓ Peer2 received file request")
    
    # Accept the file
    print("Peer2 accepting file...")
    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = os.path.join(tmpdir, "received_test.txt")
        success = peer2.accept_file(file_id_holder[0], save_path)
        
        if not success:
            print("❌ FAIL: Failed to accept file")
            os.unlink(test_file_path)
            peer1.stop()
            peer2.stop()
            return False
        
        print("✓ File accepted")
        
        # Wait for transfer to complete
        print("Waiting for file transfer to complete...")
        time.sleep(5)
        
        # Check if file was received
        if not os.path.exists(save_path):
            print("❌ FAIL: File was not received")
            os.unlink(test_file_path)
            peer1.stop()
            peer2.stop()
            return False
        
        print("✓ File received")
        
        # Verify file contents
        with open(test_file_path, 'r') as original:
            original_content = original.read()
        
        with open(save_path, 'r') as received:
            received_content = received.read()
        
        if original_content == received_content:
            print("✓ File content matches original")
        else:
            print("❌ FAIL: File content does not match")
            print(f"Original: {repr(original_content)}")
            print(f"Received: {repr(received_content)}")
            os.unlink(test_file_path)
            peer1.stop()
            peer2.stop()
            return False
    
    # Clean up
    os.unlink(test_file_path)
    
    # Stop peers
    print("\nStopping peers...")
    peer1.stop()
    peer2.stop()
    
    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    try:
        success = test_file_transfer()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
