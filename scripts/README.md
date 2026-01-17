# Scripts Directory

This directory contains utility scripts for the P2P texting application.

## Available Scripts

### Run Application
To run the P2P application:

**Single peer:**
```bash
python src/main.py [peer-id]
```

**Multiple peers (different terminals):**
```bash
# Terminal 1
python src/main.py alice

# Terminal 2
python src/main.py bob
```

### Running Tests
To run the automated test suite:
```bash
python tests/test_p2p.py
```

This will:
- Create two test peers
- Verify peer discovery
- Test message exchange
- Report results

## Development Utilities

Additional development scripts will be added here as needed for:
- Build and deployment
- Testing automation
- Setup and configuration

