# Tests Directory

This directory contains test files for the P2P texting application.

## Available Tests

### `test_p2p.py`
Automated integration test for P2P messaging functionality.

**Run the test:**
```bash
python tests/test_p2p.py
```

**What it tests:**
- Peer discovery using UDP broadcast
- Message exchange using TCP sockets
- Callback handling for events
- Multi-peer communication

**Expected output:**
```
✅ ALL TESTS PASSED!
```

## Test Coverage

Current test coverage includes:
- ✅ Peer discovery mechanism
- ✅ TCP message sending and receiving
- ✅ Peer-to-peer communication
- ✅ Basic error handling

## Future Tests

Additional tests to be added:
- Unit tests for individual components
- Edge case handling
- Network failure scenarios
- Performance tests
- Stress tests with many peers

## Testing Conventions

- Tests use Python's standard library (no external testing frameworks)
- Each test should be self-contained and independent
- Tests should clean up resources (stop peers, close sockets)
- Tests should report clear success/failure messages

