# BlockChain Project

A secure, scalable, and efficient blockchain implementation built in Python. This project provides a complete blockchain solution with mining, wallet management, peer-to-peer networking, and a RESTful API.

## Features

- **Blockchain Core**: Implements a full blockchain with blocks, transactions, mining, and chain validation
- **Cryptographic Security**: Secure wallets with public/private key cryptography and transaction signing
- **Peer-to-Peer Network**: DHT-based peer discovery and synchronization
- **RESTful API**: Complete API for interacting with the blockchain
- **Database Integration**: PostgreSQL storage backend for durability
- **Transaction Pool**: Efficient management of pending transactions
- **Mining Protocol**: Proof-of-work consensus mechanism

## Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL
- Docker (optional, for containerized deployment)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/blockchain.git
cd blockchain
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure the environment:

```bash
cp .env.example .env
# Edit .env with your configuration settings
```

4. Initialize the database:

```bash
python -m blockchain.utils.initializer
```

5. Start the blockchain node:

```bash
python -m blockchain.api.app
```

### Docker Deployment

```bash
docker-compose up -d
```

## Documentation

- [Architecture](./ARCHITECTURE.md): System design, components, and data flow
- [API Reference](./API.md): Complete REST API documentation
- [Configuration Guide](./CONFIGURATION.md): Configuration options and environment variables
- [Development Guide](./DEVELOPMENT.md): Guide for developers contributing to the project

## Core Components

### Blockchain

The blockchain is the core data structure that maintains a continuously growing list of records (blocks) that are linked using cryptography. Each block contains a timestamp, transaction data, and a cryptographic hash of the previous block.

### Transactions

Transactions represent transfers of value between wallet addresses. Each transaction includes a sender, recipient, amount, timestamp, and a cryptographic signature to verify authenticity.

### Wallet

Wallets manage cryptographic keys for transaction signing and verification. Each wallet has a unique address derived from its public key.

### Mining

Mining is the process of adding transaction records to the blockchain. Miners use computing power to solve a cryptographic puzzle (Proof of Work) to add new blocks to the chain.

### Networking

The P2P network enables nodes to discover each other, synchronize the blockchain, and propagate new transactions and blocks.

## Usage Examples

### Creating a Wallet

```python
from blockchain.crypto.wallet import Wallet

# Create a new wallet
wallet = Wallet()
print(f"Address: {wallet.get_address()}")
print(f"Public Key: {wallet.public_key.hex()}")
```

### Creating a Transaction

```python
from blockchain.core.transaction import Transaction
from blockchain.crypto.wallet import Wallet

# Create sender and recipient wallets
sender_wallet = Wallet()
recipient_wallet = Wallet()

# Create and sign a transaction
transaction = Transaction(
    sender=sender_wallet.get_address(),
    recipient=recipient_wallet.get_address(),
    amount=10.0
)
sender_wallet.sign_transaction(transaction)

# Verify the transaction
is_valid = transaction.verify()
print(f"Transaction valid: {is_valid}")
```

### Mining a Block

```python
from blockchain.core.blockchain import Blockchain
from blockchain.crypto.wallet import Wallet

# Initialize blockchain
blockchain = Blockchain()

# Create a miner wallet
miner_wallet = Wallet()

# Mine pending transactions
blockchain.mine_pending_transactions(miner_wallet.get_address())
```

## API Usage

The blockchain exposes a RESTful API for interacting with the system. See the [API Documentation](./API.md) for details.

Example API request:

```bash
# Get blockchain status
curl -X GET http://localhost:5000/api/v1/status

# Create a transaction
curl -X POST http://localhost:5000/api/v1/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "0x3f4d9...",
    "recipient": "0x8a72c...",
    "amount": 5.0,
    "private_key": "5a4e2..."
  }'
```

## Contributing

Contributions are welcome! Please check the [Development Guide](./DEVELOPMENT.md) for details on how to contribute to the project.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Satoshi Nakamoto for the original blockchain concept
- The wider blockchain community for research and standards 