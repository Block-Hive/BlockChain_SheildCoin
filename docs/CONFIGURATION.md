# Configuration Guide

This document provides comprehensive information on configuring the BlockChain system, including configuration files, environment variables, and command-line arguments.

## Configuration File

The primary configuration is stored in `blockchain/config.py`. This file contains settings for the blockchain, database, networking, and security components.

### Database Configuration

Database connection settings are defined in the `DATABASE_CONFIG` dictionary:

```python
DATABASE_CONFIG = {
    'host': 'localhost',       # Database server hostname
    'port': 5432,              # PostgreSQL port
    'database': 'blockchain',  # Database name
    'user': 'blockchain_user', # Database username
    'password': 'your_password', # Database password
    'sslmode': 'prefer',       # SSL mode (prefer, require, disable)
    'timeout': 10,             # Connection timeout in seconds
    
    # Optional SSL parameters
    'sslcert': '/path/to/cert.pem',     # Client certificate file
    'sslkey': '/path/to/key.pem',       # Client key file
    'sslrootcert': '/path/to/ca.pem',   # CA certificate file
}
```

### Blockchain Settings

Blockchain behavior is controlled by the `BLOCKCHAIN_CONFIG` dictionary:

```python
BLOCKCHAIN_CONFIG = {
    'difficulty': 4,                  # Initial mining difficulty (number of leading zeros)
    'mining_reward': 50,              # Reward for mining a block
    'target_block_time': 600,         # Target time between blocks in seconds (10 minutes)
    'difficulty_adjustment_interval': 10, # Number of blocks between difficulty adjustments
    'max_transactions_per_block': 100,  # Maximum transactions in a block
    
    # Transaction limits
    'min_transaction_amount': 0.00000001, # Minimum transaction amount
    'max_transaction_amount': 1000000000, # Maximum transaction amount
    
    # Fee structure
    'transaction_fee': 0.001,         # Fee per transaction
    'min_transaction_fee': 0.0001,    # Minimum fee
}
```

### Network Settings

P2P network configuration is defined in the `NETWORK_CONFIG` dictionary:

```python
NETWORK_CONFIG = {
    'bootstrap_nodes': [             # List of bootstrap nodes
        '192.168.1.100:6000',
        '192.168.1.101:6000'
    ],
    'dht_bucket_size': 20,           # K-bucket size for DHT
    'max_peers': 50,                 # Maximum number of peers to connect to
    'peer_timeout': 30,              # Peer connection timeout in seconds
    
    # Message broadcasting
    'broadcast_retries': 3,          # Number of retries for failed broadcasts
    'broadcast_timeout': 5,          # Timeout for broadcast operations in seconds
}
```

### Security Settings

Security-related settings are defined in the `SECURITY_CONFIG` dictionary:

```python
SECURITY_CONFIG = {
    # API rate limiting
    'rate_limit_per_minute': 60,     # Default requests per minute
    'rate_limit_burst': 20,          # Burst allowance
    
    # CORS settings
    'allowed_origins': [             # Allowed CORS origins
        'http://localhost:3000',
        'https://yourapp.com'
    ],
    
    # Crypto settings
    'key_derivation_iterations': 1000000,  # PBKDF2 iterations for key derivation
    'aes_key_size': 32,              # AES key size in bytes (256 bits)
}
```

## Environment Variables

The BlockChain system can be configured using environment variables, which take precedence over values in the configuration file. The following environment variables are supported:

### Database Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BLOCKCHAIN_DB_HOST` | Database server hostname | `localhost` |
| `BLOCKCHAIN_DB_PORT` | PostgreSQL port | `5432` |
| `BLOCKCHAIN_DB_NAME` | Database name | `blockchain` |
| `BLOCKCHAIN_DB_USER` | Database username | `blockchain_user` |
| `BLOCKCHAIN_DB_PASSWORD` | Database password | None |
| `BLOCKCHAIN_DB_SSL_MODE` | SSL mode for database connection | `prefer` |
| `BLOCKCHAIN_DB_SSL_CERT` | Path to client certificate file | None |
| `BLOCKCHAIN_DB_SSL_KEY` | Path to client key file | None |
| `BLOCKCHAIN_DB_SSL_ROOT_CERT` | Path to CA certificate file | None |

### Blockchain Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BLOCKCHAIN_DIFFICULTY` | Initial mining difficulty | `4` |
| `BLOCKCHAIN_MINING_REWARD` | Reward for mining a block | `50` |
| `BLOCKCHAIN_TARGET_BLOCK_TIME` | Target time between blocks (seconds) | `600` |
| `BLOCKCHAIN_MAX_TXS_PER_BLOCK` | Maximum transactions per block | `100` |
| `BLOCKCHAIN_MIN_TX_AMOUNT` | Minimum transaction amount | `0.00000001` |
| `BLOCKCHAIN_MAX_TX_AMOUNT` | Maximum transaction amount | `1000000000` |
| `BLOCKCHAIN_TX_FEE` | Fee per transaction | `0.001` |

### Network Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BLOCKCHAIN_BOOTSTRAP_NODES` | Comma-separated list of bootstrap nodes | Empty |
| `BLOCKCHAIN_MAX_PEERS` | Maximum number of peers to connect to | `50` |
| `BLOCKCHAIN_PEER_TIMEOUT` | Peer connection timeout (seconds) | `30` |
| `BLOCKCHAIN_DHT_BUCKET_SIZE` | K-bucket size for DHT | `20` |

### Security Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BLOCKCHAIN_RATE_LIMIT` | Default requests per minute | `60` |
| `BLOCKCHAIN_ALLOWED_ORIGINS` | Comma-separated list of allowed CORS origins | Empty |
| `BLOCKCHAIN_KEY_ITERATIONS` | PBKDF2 iterations for key derivation | `1000000` |
| `BLOCKCHAIN_AES_KEY_SIZE` | AES key size in bytes | `32` |

## Command-Line Arguments

The blockchain node can be started with various command-line arguments to control its behavior. These arguments take precedence over both environment variables and configuration file settings.

### Basic Node Arguments

```bash
python -m blockchain.api.app [options]
```

| Argument | Description | Default |
|----------|-------------|---------|
| `--host` | Host to bind the API server to | `0.0.0.0` |
| `--port` | Port for the API server | `5000` |
| `--dht-port` | Port for the DHT node | `port + 1000` |
| `--bootstrap` | Bootstrap node address (host:port) | None |
| `--local-ip` | Explicitly set the local IP address | Auto-detected |

### Security Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--ssl-cert` | Path to SSL certificate for HTTPS | None |
| `--ssl-key` | Path to SSL key for HTTPS | None |
| `--allowed-hosts` | Comma-separated list of allowed hosts | `localhost,127.0.0.1` |

### Advanced Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--difficulty` | Initial mining difficulty | From config |
| `--mining-reward` | Reward for mining a block | From config |
| `--max-tx-per-block` | Maximum transactions per block | From config |
| `--max-peers` | Maximum number of peers | From config |
| `--disable-mining` | Disable mining on this node | Mining enabled |
| `--no-sync` | Don't synchronize with other nodes | Sync enabled |

## Configuration Loading Hierarchy

The configuration is loaded in the following order, with later sources taking precedence:

1. Default values defined in the code
2. Configuration file (`blockchain/config.py`)
3. Environment variables
4. Command-line arguments

## Example Configurations

### Development Configuration

```python
# blockchain/config.py for development
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'blockchain_dev',
    'user': 'dev_user',
    'password': 'dev_password'
}

BLOCKCHAIN_CONFIG = {
    'difficulty': 3,          # Lower difficulty for faster mining
    'mining_reward': 50,
    'target_block_time': 60,  # Faster blocks for development
    'max_transactions_per_block': 10
}

NETWORK_CONFIG = {
    'bootstrap_nodes': ['localhost:6000'],
    'max_peers': 5
}

SECURITY_CONFIG = {
    'rate_limit_per_minute': 1000,  # Higher rate limit for testing
    'allowed_origins': ['*'],       # Allow all origins in development
    'key_derivation_iterations': 1000  # Fewer iterations for faster testing
}
```

### Production Configuration

```python
# blockchain/config.py for production
DATABASE_CONFIG = {
    'host': os.environ.get('BLOCKCHAIN_DB_HOST', 'db.example.com'),
    'port': int(os.environ.get('BLOCKCHAIN_DB_PORT', 5432)),
    'database': os.environ.get('BLOCKCHAIN_DB_NAME', 'blockchain_prod'),
    'user': os.environ.get('BLOCKCHAIN_DB_USER', 'blockchain_user'),
    'password': os.environ.get('BLOCKCHAIN_DB_PASSWORD'),
    'sslmode': 'require',
    'timeout': 30
}

BLOCKCHAIN_CONFIG = {
    'difficulty': 5,          # Higher difficulty for security
    'mining_reward': 50,
    'target_block_time': 600,
    'max_transactions_per_block': 1000,
    'transaction_fee': 0.005  # Higher fee for production
}

NETWORK_CONFIG = {
    'bootstrap_nodes': [
        'node1.example.com:6000',
        'node2.example.com:6000',
        'node3.example.com:6000'
    ],
    'max_peers': 100,
    'peer_timeout': 60
}

SECURITY_CONFIG = {
    'rate_limit_per_minute': 60,
    'allowed_origins': [
        'https://app.example.com',
        'https://api.example.com'
    ],
    'key_derivation_iterations': 1000000
}
```

## Docker Environment

When running the blockchain in Docker, the recommended approach is to use environment variables for configuration:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY . /app/
RUN pip install -r requirements.txt

ENV BLOCKCHAIN_DB_HOST=db
ENV BLOCKCHAIN_DB_PORT=5432
ENV BLOCKCHAIN_DB_NAME=blockchain
ENV BLOCKCHAIN_DB_USER=blockchain_user
ENV BLOCKCHAIN_DB_PASSWORD=your_password
ENV BLOCKCHAIN_DIFFICULTY=4
ENV BLOCKCHAIN_MAX_PEERS=50
ENV BLOCKCHAIN_BOOTSTRAP_NODES=node1.example.com:6000,node2.example.com:6000

EXPOSE 5000 6000

CMD ["python", "-m", "blockchain.api.app", "--host", "0.0.0.0", "--port", "5000", "--dht-port", "6000"]
```

## Configuration Validation

The system validates configuration settings on startup. If any configuration values are invalid, the system will log an error and use default values or exit if the configuration error is critical.

Critical configuration errors include:
- Invalid database connection settings
- Invalid bootstrap node formats
- Invalid SSL certificate or key paths

## Configuration Best Practices

1. **Use Environment Variables for Secrets**: Never store sensitive information like database passwords in the configuration file. Use environment variables instead.

2. **Configure Database SSL**: In production, always use SSL for database connections to protect data in transit.

3. **Set Appropriate Rate Limits**: Configure rate limits based on your expected API usage to prevent abuse.

4. **Adjust Mining Difficulty**: Set the initial mining difficulty based on your network's hash power to ensure reasonable block times.

5. **Secure API Access**: In production, always use HTTPS for API access and configure allowed hosts appropriately.

6. **Use Multiple Bootstrap Nodes**: Configure multiple bootstrap nodes for redundancy and better network resilience.

7. **Monitor and Adjust**: Regularly monitor the system and adjust configuration settings as needed based on performance and security requirements.

## Configuration File Location

By default, the system looks for the configuration file at `blockchain/config.py`. To use a different configuration file, you can set the `BLOCKCHAIN_CONFIG_FILE` environment variable:

```bash
export BLOCKCHAIN_CONFIG_FILE=/path/to/custom_config.py
python -m blockchain.api.app
```

## Dynamic Configuration

Some configuration settings can be changed dynamically while the system is running:

1. **Rate Limits**: API rate limits can be adjusted dynamically by sending a request to the admin endpoint (requires admin authentication).

2. **Peer Connections**: Maximum peer connections can be adjusted dynamically through the admin interface.

3. **Mining Difficulty**: The blockchain automatically adjusts mining difficulty based on the actual block times.

Static settings that require a restart to change include:
- Database connection settings
- API binding host and port
- DHT port
- SSL certificate and key paths

## Configuration Troubleshooting

### Database Connection Issues

If you're experiencing database connection issues, check the following:
- Database server is running and accessible from the blockchain node
- Database user has appropriate permissions
- Database name exists
- SSL settings are correct if SSL is enabled

### Network Configuration Issues

If nodes are not connecting properly, check:
- Firewall settings allow connections on the DHT port
- Bootstrap nodes are reachable
- Local IP is correctly detected or specified
- NAT traversal is configured properly if behind a NAT

### Performance Tuning

To improve performance:
- Adjust database connection pool size based on expected load
- Tune the blockchain difficulty for target block time
- Configure appropriate rate limits for your API usage patterns
- Adjust DHT settings based on network size and topology

## Complete Configuration Reference

For a complete reference of all configuration options and their impacts, see the inline documentation in the configuration file at `blockchain/config.py`. 