# Architecture Overview

This document provides a comprehensive overview of the BlockChain architecture, detailing the system design, core components, data flow, and component interactions.

## System Architecture

BlockChain follows a layered architecture pattern, combining a traditional blockchain with modern web technologies and database persistence. The system is designed to be modular, allowing components to be extended or replaced as needed.

### High-Level Architecture

```
                  ┌─────────────────┐
                  │     Client      │
                  │  Applications   │
                  └────────┬────────┘
                           │
                           ▼
┌───────────────────────────────────────────────┐
│                RESTful API Layer               │
└───────────────────────┬───────────────────────┘
                        │
┌───────────────────────┴───────────────────────┐
│               Blockchain Core                  │
├─────────────┬─────────────┬──────────┬────────┤
│    Blocks   │Transactions │  Wallet  │  DHT   │
└─────────────┴──────┬──────┴──────────┴────────┘
                     │
┌────────────────────┴───────────────────────┐
│                Database Layer               │
└────────────────────────────────────────────┘
```

### Component Layers

1. **Client Applications**: External applications that interact with the blockchain via HTTP requests.

2. **RESTful API Layer**: Flask-based API exposing blockchain functionality to clients.

3. **Blockchain Core**: The central component containing all blockchain logic.
   - Block management
   - Transaction processing
   - Mining operations
   - Chain validation
   - Wallet cryptography

4. **P2P Network Layer**: Distributed Hash Table (DHT) for peer discovery and communication.

5. **Database Layer**: PostgreSQL storage for blockchain data persistence.

## Core Components

### 1. Block (`blockchain/core/block.py`)

The Block component represents a single block in the blockchain. Each block contains:

- Index
- Timestamp
- List of transactions
- Previous block's hash
- Nonce (for proof-of-work)
- Block hash

**Key Responsibilities**:
- Calculate and verify block hash
- Implement proof-of-work mining
- Validate block structure and contents
- Serialize and deserialize block data

**Example Block Structure**:
```python
{
    'index': 1,
    'timestamp': 1625097660,
    'previous_hash': '000a1b2c3d4e5f...',
    'hash': '000bcd123456...',
    'nonce': 67890,
    'transactions': [
        {
            'sender': 'system',
            'recipient': 'miner-address-123',
            'amount': 50,
            'timestamp': 1625097650
        }
    ]
}
```

### 2. Transaction (`blockchain/core/transaction.py`)

The Transaction component represents a transfer of value between wallets. Each transaction contains:

- Sender address
- Recipient address
- Amount
- Timestamp
- Digital signature

**Key Responsibilities**:
- Create and validate transactions
- Sign transactions with sender's private key
- Verify transaction signatures
- Serialize and deserialize transaction data

**Example Transaction Structure**:
```python
{
    'sender': 'PUBLIC_KEY_STRING',
    'recipient': 'RECIPIENT_ADDRESS',
    'amount': 10.5,
    'timestamp': 1625097750,
    'signature': 'TRANSACTION_SIGNATURE'
}
```

### 3. Blockchain (`blockchain/core/blockchain.py`)

The Blockchain component manages the chain of blocks and implements consensus rules. It contains:

- Chain of blocks
- Current mining difficulty
- Mining reward amount
- Transaction pool

**Key Responsibilities**:
- Initialize the blockchain with a genesis block
- Add new blocks to the chain
- Validate the entire blockchain
- Mine pending transactions into new blocks
- Adjust mining difficulty dynamically
- Calculate wallet balances
- Implement chain consensus

### 4. Transaction Pool (`blockchain/core/transaction_pool.py`)

The Transaction Pool component manages pending transactions that have not yet been included in a block.

**Key Responsibilities**:
- Add new transactions to the pool
- Validate transactions before adding them
- Remove transactions that have been mined
- Prevent duplicate transactions
- Provide pending transactions for mining

### 5. Wallet (`blockchain/crypto/wallet.py`)

The Wallet component handles cryptographic operations for creating and using blockchain wallets.

**Key Responsibilities**:
- Generate RSA-3072 key pairs
- Create wallet addresses from public keys
- Sign transactions with private keys
- Verify transaction signatures
- Encrypt and decrypt private keys
- Serialize and deserialize wallet data

**Example Wallet Structure**:
```python
{
    'address': '1a2b3c4d5e6f7g8h9i0j...',
    'public_key': '-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BA...\n-----END PUBLIC KEY-----',
    'encrypted_private_key': {
        'salt': 'base64_encoded_salt',
        'iv': 'base64_encoded_iv',
        'encrypted': 'base64_encoded_encrypted_key'
    }
}
```

### 6. Database Layer (`blockchain/utils/database.py`)

The Database component provides persistence for blockchain data using PostgreSQL.

**Key Responsibilities**:
- Initialize database connection pool
- Create and manage database schema
- Save and retrieve blocks
- Save and retrieve transactions
- Save and retrieve wallet data
- Save and retrieve peer information
- Implement transaction isolation

### 7. Storage Manager (`blockchain/utils/storage.py`)

The Storage component provides a simplified interface for blockchain persistence operations.

**Key Responsibilities**:
- Initialize storage
- Save and load blockchain state
- Manage serialization and deserialization

### 8. DHT Node (`blockchain/network/dht_node.py`)

The DHT Node component implements peer-to-peer networking using a Distributed Hash Table.

**Key Responsibilities**:
- Initialize and maintain DHT network
- Discover and connect to peers
- Handle node joining and leaving
- Broadcast new blocks and transactions
- Synchronize blockchain data between nodes
- Implement consensus across the network

### 9. API Server (`blockchain/api/app.py`)

The API Server component provides a RESTful interface for interacting with the blockchain.

**Key Responsibilities**:
- Expose blockchain functionality via HTTP endpoints
- Handle API requests and responses
- Implement rate limiting and security measures
- Provide node status and information
- Connect to the DHT network

## Data Flow

### Transaction Creation and Mining

```
┌────────┐     ┌─────────────┐     ┌───────────┐     ┌──────────┐
│ Client │────▶│  API Layer  │────▶│ TX Pool   │────▶│Blockchain│
└────────┘     └─────────────┘     └───────────┘     └──────────┘
                                                          │
                                                          ▼
┌────────┐     ┌─────────────┐     ┌───────────┐     ┌──────────┐
│ Client │◀────│  API Layer  │◀────│  Block    │◀────│  Mining  │
└────────┘     └─────────────┘     └───────────┘     └──────────┘
                                        │
                                        ▼
                                   ┌──────────┐
                                   │ Database │
                                   └──────────┘
```

1. A client creates a transaction and submits it to the API
2. The API validates the transaction and adds it to the transaction pool
3. A mining request triggers the blockchain to mine pending transactions
4. Once mined, a new block is created and added to the blockchain
5. The block is persisted to the database
6. The new block is broadcast to all peers in the network

### Node Synchronization

```
┌────────┐     ┌─────────────┐     ┌────────────┐
│New Node│────▶│ Bootstrap   │────▶│ DHT Network│
└────────┘     └─────────────┘     └────────────┘
                                         │
                                         ▼
┌────────┐     ┌─────────────┐     ┌────────────┐
│New Node│◀────│ Chain Data  │◀────│Other Nodes │
└────────┘     └─────────────┘     └────────────┘
    │
    ▼
┌────────┐
│Database│
└────────┘
```

1. A new node starts and connects to a bootstrap node
2. The bootstrap node adds the new node to its DHT routing table
3. The new node requests the current blockchain from other nodes
4. Once received, the blockchain is validated and stored locally
5. The node is now synchronized and can participate in the network

### API Request Processing

```
┌────────┐     ┌─────────────┐     ┌────────────┐     ┌────────────┐
│ Client │────▶│  API Route  │────▶│ Blockchain │────▶│   Result   │
└────────┘     └─────────────┘     └────────────┘     └────────────┘
                                                           │
                                                           ▼
                                                      ┌────────────┐
                                                      │   Client   │
                                                      └────────────┘
```

1. A client sends an HTTP request to an API endpoint
2. The API route handler processes the request
3. The request is delegated to the appropriate blockchain method
4. The result is formatted and returned to the client

## Database Schema

The blockchain uses a PostgreSQL database with the following schema:

### Blocks Table

```sql
CREATE TABLE IF NOT EXISTS blocks (
    id SERIAL PRIMARY KEY,
    index INTEGER NOT NULL,
    timestamp DOUBLE PRECISION NOT NULL,
    previous_hash VARCHAR(64) NOT NULL,
    hash VARCHAR(64) NOT NULL UNIQUE,
    nonce INTEGER NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Transactions Table

```sql
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    block_id INTEGER REFERENCES blocks(id),
    transaction_hash VARCHAR(64) NOT NULL UNIQUE,
    sender VARCHAR(255) NOT NULL,
    recipient VARCHAR(255) NOT NULL,
    amount DOUBLE PRECISION NOT NULL,
    timestamp DOUBLE PRECISION NOT NULL,
    signature TEXT,
    is_pending BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Wallets Table

```sql
CREATE TABLE IF NOT EXISTS wallets (
    id SERIAL PRIMARY KEY,
    address VARCHAR(255) NOT NULL UNIQUE,
    public_key TEXT NOT NULL,
    encrypted_private_key JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Peers Table

```sql
CREATE TABLE IF NOT EXISTS peers (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(255) NOT NULL UNIQUE,
    host VARCHAR(255) NOT NULL,
    port INTEGER NOT NULL,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_trusted BOOLEAN DEFAULT FALSE
)
```

## Project Structure

```
blockchain/
├── api/
│   ├── __init__.py
│   └── app.py              # Flask API implementation
├── core/
│   ├── __init__.py
│   ├── block.py            # Block implementation
│   ├── blockchain.py       # Blockchain implementation
│   ├── transaction.py      # Transaction implementation
│   └── transaction_pool.py # Transaction pool management
├── crypto/
│   ├── __init__.py
│   └── wallet.py           # Wallet and cryptographic operations
├── network/
│   ├── __init__.py
│   └── dht_node.py         # DHT node implementation
├── utils/
│   ├── __init__.py
│   ├── database.py         # PostgreSQL database operations
│   ├── initializer.py      # System initialization
│   └── storage.py          # Data persistence
├── config.py               # Configuration settings
└── __init__.py

docs/
├── API.md                  # API documentation
├── ARCHITECTURE.md         # Architecture documentation (this file)
├── SECURITY.md             # Security documentation
├── CONFIGURATION.md        # Configuration documentation
└── DEVELOPMENT.md          # Development guide

tests/
├── __init__.py
├── test_api.py             # API tests
├── test_block.py           # Block tests
├── test_blockchain.py      # Blockchain tests
├── test_transaction.py     # Transaction tests
└── test_wallet.py          # Wallet tests
```

## Consensus Mechanism

The blockchain implements a proof-of-work consensus mechanism similar to Bitcoin:

1. **Block Mining**:
   - Miners compete to solve a cryptographic puzzle by finding a nonce that produces a block hash with a specified number of leading zeros
   - The difficulty (number of leading zeros) adjusts dynamically based on the network's mining rate

2. **Chain Selection**:
   - When a node encounters multiple valid chains, it selects the longest chain as the valid one
   - If chains have equal length, the chain with more total proof-of-work is selected

3. **Block Validation**:
   - Each block is validated for:
     - Correct index and previous hash
     - Valid proof-of-work solution
     - Valid transaction signatures
     - Correct block structure

4. **Transaction Validation**:
   - Each transaction is validated for:
     - Valid sender and recipient addresses
     - Valid transaction amount (positive and within limits)
     - Valid signature from the sender
     - Sender has sufficient balance

## Performance Considerations

The blockchain is designed with several performance optimizations:

1. **Connection Pooling**:
   - Database connections are pooled to reduce connection overhead
   - Connection pooling parameters can be tuned based on load

2. **Database Indexing**:
   - Key fields like transaction hashes, block hashes, and wallet addresses are indexed
   - Improves query performance for common operations

3. **Caching**:
   - Current blockchain state is kept in memory during operation
   - Reduces need for database queries for common operations

4. **Parallel Processing**:
   - DHT network operations run in separate threads from the API
   - Mining operations can be offloaded to avoid blocking API responses

5. **Difficulty Adjustment**:
   - Mining difficulty automatically adjusts based on network hash power
   - Ensures consistent block times regardless of network size

## Extending the System

The modular design allows for several extension points:

1. **Consensus Mechanisms**:
   - The proof-of-work consensus can be replaced with alternatives like proof-of-stake
   - Implement a new consensus class that adheres to the same interface

2. **Storage Backends**:
   - The PostgreSQL database can be replaced with other databases
   - Implement a new storage adapter that conforms to the same interface

3. **Network Protocols**:
   - The DHT can be replaced with other P2P network implementations
   - Implement a new network class that provides the same node discovery and message broadcasting capabilities

4. **API Extensions**:
   - New API endpoints can be added to expose additional functionality
   - Existing endpoints can be modified to support additional parameters

## Future Enhancements

Potential future enhancements to the architecture include:

1. **Smart Contracts**:
   - Add support for executing code on the blockchain
   - Implement a virtual machine for contract execution

2. **Sharding**:
   - Partition the blockchain to improve scalability
   - Implement cross-shard transaction validation

3. **Layer 2 Solutions**:
   - Add support for off-chain scaling solutions
   - Implement payment channels or state channels

4. **Privacy Features**:
   - Add support for private transactions
   - Implement zero-knowledge proofs or ring signatures

5. **Governance Mechanisms**:
   - Add support for on-chain governance
   - Implement voting mechanisms for protocol changes

## Conclusion

The BlockChain architecture provides a solid foundation for a blockchain system with a focus on security, scalability, and extensibility. The modular design allows for components to be replaced or extended as needed, while the layered architecture provides clear separation of concerns.

By understanding this architecture, developers can effectively extend and customize the system to meet specific requirements, whether for private blockchains, cryptocurrencies, or decentralized applications. 