"""
Configuration settings for the blockchain system.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Blockchain settings
INITIAL_DIFFICULTY = int(os.getenv('INITIAL_DIFFICULTY', 4))
TARGET_BLOCK_TIME = int(os.getenv('TARGET_BLOCK_TIME', 10))
DIFFICULTY_ADJUSTMENT_INTERVAL = 10
MINING_REWARD = float(os.getenv('MINING_REWARD', 10.0))

# Network settings
DEFAULT_HOST = os.getenv('DEFAULT_HOST', 'localhost')
DEFAULT_PORT = int(os.getenv('DEFAULT_PORT', 5000))
MAX_PEERS = int(os.getenv('MAX_PEERS', 50))
PEER_DISCOVERY_INTERVAL = 60
CHAIN_SYNC_INTERVAL = 300

# DHT settings
DHT_BOOTSTRAP_NODES = os.getenv('DHT_BOOTSTRAP_NODES', '').split(',')
DHT_REPLICATION_FACTOR = int(os.getenv('DHT_REPLICATION_FACTOR', 3))
DHT_SYNC_INTERVAL = int(os.getenv('DHT_SYNC_INTERVAL', 30))
DHT_STORAGE_PATH = os.getenv('DHT_STORAGE_PATH', 'dht_storage')

# Transaction settings
MAX_TRANSACTION_POOL_SIZE = 1000
MIN_TRANSACTION_FEE = 0.0001
MAX_TRANSACTION_SIZE = 1024

# Security settings
KEY_SIZE = int(os.getenv('KEY_SIZE', 2048))
HASH_ALGORITHM = os.getenv('HASH_ALGORITHM', 'SHA-256')
SIGNATURE_ALGORITHM = os.getenv('SIGNATURE_ALGORITHM', 'RSA-PSS')
ENCRYPTION_ALGORITHM = "AES-256-CBC"
PBKDF2_ITERATIONS = 100000

# Storage settings
DATA_DIR = 'data'
WALLET_FILE = 'wallet.json'
BLOCKCHAIN_FILE = 'blockchain.json'
PEERS_FILE = 'peers.json'

# Database settings
DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'blockchain'),
    'user': os.getenv('DB_USER', 'blockchain_user'),
    'password': os.getenv('DB_PASSWORD', 'your_password')
}

# API settings
API_HOST = os.getenv('API_HOST', 'localhost')
API_PORT = int(os.getenv('API_PORT', 5000))
API_DEBUG = os.getenv('API_DEBUG', 'True').lower() == 'true'
API_THREADED = True
API_RATE_LIMIT = 100

# API configuration dictionary
API_CONFIG = {
    'host': API_HOST,
    'port': API_PORT,
    'debug': API_DEBUG,
    'threaded': API_THREADED,
    'rate_limit': API_RATE_LIMIT,
    'bootstrap_nodes': DHT_BOOTSTRAP_NODES
}

# Logging settings
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'blockchain.log')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Message types for network communication
class MessageType:
    NEW_BLOCK = "new_block"
    NEW_TRANSACTION = "new_transaction"
    REQUEST_CHAIN = "request_chain"
    CHAIN_RESPONSE = "chain_response"
    PEER_DISCOVERY = "peer_discovery"
    PEER_RESPONSE = "peer_response"
    # DHT message types
    STORE_BLOCK = "store_block"
    STORE_TRANSACTION = "store_transaction"
    GET_BLOCK = "get_block"
    GET_TRANSACTION = "get_transaction"
    REQUEST_DATA = "request_data"
    DATA_RESPONSE = "data_response"

# Error messages
class ErrorMessages:
    INVALID_TRANSACTION = "Invalid transaction"
    INVALID_BLOCK = "Invalid block"
    INVALID_SIGNATURE = "Invalid signature"
    INSUFFICIENT_FUNDS = "Insufficient funds"
    NETWORK_ERROR = "Network error"
    INVALID_PEER = "Invalid peer"
    CHAIN_SYNC_ERROR = "Chain synchronization error"
    WALLET_ERROR = "Wallet error"
    API_ERROR = "API error"
    BLOCKCHAIN_NOT_FOUND = "Blockchain not found"
    WALLET_NOT_FOUND = "Wallet not found"
    PEER_NOT_FOUND = "Peer not found"
    DHT_ERROR = "DHT error"
    DHT_STORAGE_ERROR = "DHT storage error"
    DHT_SYNC_ERROR = "DHT synchronization error" 