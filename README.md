# BlockChain - Secure Distributed Ledger System

A complete, secure, and production-ready blockchain implementation featuring transaction processing, proof-of-work consensus, wallet management, and a distributed peer-to-peer network.

## Features

- **Complete Blockchain Implementation**
  - Proof-of-Work consensus algorithm
  - Dynamic difficulty adjustment
  - Secure transaction validation
  - Mining rewards and fee structures

- **Cryptographic Security**
  - Strong RSA-3072 based wallet encryption
  - SHA-256 and SHA3-256 hashing for blockchain integrity
  - Digital signatures for transaction verification
  - Password-protected wallet storage

- **Distributed Network**
  - Peer-to-peer architecture via DHT (Distributed Hash Table)
  - Automatic node discovery and synchronization
  - Chain validation and conflict resolution
  - Automatic bootstrap node detection

- **RESTful API**
  - Full blockchain management API
  - Wallet creation and management
  - Transaction creation and verification
  - Block mining capabilities
  - Node status monitoring

- **Database Persistence**
  - PostgreSQL database integration
  - Transaction pool persistence
  - Chain and wallet storage
  - Connection pooling and failure recovery

## System Requirements

- Python 3.8+
- PostgreSQL 12+
- Network connectivity for distributed operations
- 2GB+ RAM recommended for mining operations

## Installation

### Setting up the environment

```bash
# Clone the repository
git clone https://github.com/yourusername/BlockChain.git
cd BlockChain

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Database Setup

1. Create a PostgreSQL database:

```sql
CREATE DATABASE blockchain;
CREATE USER blockchain_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE blockchain TO blockchain_user;
```

2. Configure the database connection in `blockchain/config.py`:

```python
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'blockchain',
    'user': 'blockchain_user',
    'password': 'your_password'
}
```

## Running the Blockchain

### Starting a Bootstrap Node

```bash
python -m blockchain.api.app --host 0.0.0.0 --port 5000 --dht-port 6000
```

This will start a bootstrap node that creates the initial blockchain with a genesis block.

### Joining an Existing Network

```bash
python -m blockchain.api.app --host 0.0.0.0 --port 5001 --dht-port 6001 --bootstrap 192.168.1.100:6000
```

Replace `192.168.1.100:6000` with the IP and DHT port of a running bootstrap node.

## Basic Usage

Once your node is running, you can interact with the blockchain using the API:

### Creating a Wallet

```bash
curl http://localhost:5000/wallet/new
```

This will return a new wallet containing:
- Public address
- Public key
- Private key (store securely!)

### Creating a Transaction

```bash
curl -X POST http://localhost:5000/transactions/new \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "PUBLIC_KEY_HERE", 
    "recipient": "RECIPIENT_ADDRESS_HERE", 
    "amount": 10,
    "signature": "SIGNATURE_HERE"
  }'
```

### Mining a Block

```bash
curl http://localhost:5000/mine?address=YOUR_WALLET_ADDRESS
```

This will mine a new block with pending transactions and credit mining rewards to the specified address.

### Viewing the Blockchain

```bash
curl http://localhost:5000/chain
```

## Security Considerations

- Always encrypt and securely store wallet private keys
- Run nodes on secure, firewalled servers
- Consider implementing additional authentication for production use
- Monitor for suspicious transaction patterns
- Regularly backup blockchain database

## Documentation

For more detailed documentation, see:

- [API Documentation](docs/API.md) - Complete API reference
- [Security Guide](docs/SECURITY.md) - Security features and best practices
- [Architecture Overview](docs/ARCHITECTURE.md) - System architecture and design
- [Advanced Configuration](docs/CONFIGURATION.md) - Advanced configuration options
- [Development Guide](docs/DEVELOPMENT.md) - Guide for developers extending the system

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For questions or support, please contact [your-email@example.com](mailto:your-email@example.com)
