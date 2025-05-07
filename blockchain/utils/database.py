import psycopg2
from psycopg2.extras import DictCursor
from psycopg2 import pool
import json
from typing import Dict, Any, List, Optional, Tuple, Union
import logging
from ..config import DATABASE_CONFIG
import time
import hashlib

logger = logging.getLogger(__name__)

class Database:
    """
    Database utility class for PostgreSQL operations.
    Handles connection pooling, queries, and data persistence.
    """
    
    _connection_pool = None
    _pool_initialized = False
    _max_retries = 3
    _retry_delay = 1  # seconds
    
    @classmethod
    def initialize(cls):
        """Initialize the database connection pool."""
        if cls._pool_initialized:
            logger.debug("Database connection pool already initialized")
            return
            
        try:
            # Validate database config
            required_fields = ['host', 'port', 'database', 'user', 'password']
            for field in required_fields:
                if field not in DATABASE_CONFIG:
                    raise ValueError(f"Missing required database configuration field: {field}")
            
            # Set secure connection parameters
            connection_params = {
                'minconn': 1,
                'maxconn': 10,
                'host': DATABASE_CONFIG['host'],
                'port': DATABASE_CONFIG['port'],
                'database': DATABASE_CONFIG['database'],
                'user': DATABASE_CONFIG['user'],
                'password': DATABASE_CONFIG['password'],
                # Add SSL if provided
                'sslmode': DATABASE_CONFIG.get('sslmode', 'prefer'),
                # Add timeout for connections
                'connect_timeout': DATABASE_CONFIG.get('timeout', 10)
            }
            
            # Add optional SSL parameters if provided
            if 'sslcert' in DATABASE_CONFIG:
                connection_params['sslcert'] = DATABASE_CONFIG['sslcert']
            if 'sslkey' in DATABASE_CONFIG:
                connection_params['sslkey'] = DATABASE_CONFIG['sslkey']
            if 'sslrootcert' in DATABASE_CONFIG:
                connection_params['sslrootcert'] = DATABASE_CONFIG['sslrootcert']
            
            cls._connection_pool = pool.ThreadedConnectionPool(**connection_params)
            cls._pool_initialized = True
            logger.info("Database connection pool initialized successfully")
            
            # Create tables
            cls.create_tables()
        except Exception as e:
            logger.error(f"Failed to initialize database connection pool: {e}")
            raise
    
    @classmethod
    def get_connection(cls):
        """Get a connection from the pool with retry logic."""
        if cls._connection_pool is None:
            cls.initialize()
            
        for attempt in range(cls._max_retries):
            try:
                conn = cls._connection_pool.getconn()
                # Test connection
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                return conn
            except Exception as e:
                logger.warning(f"Failed to get database connection (attempt {attempt+1}/{cls._max_retries}): {e}")
                if attempt < cls._max_retries - 1:
                    time.sleep(cls._retry_delay)
                else:
                    logger.error("Failed to get database connection after maximum retries")
                    raise
    
    @classmethod
    def return_connection(cls, conn):
        """Return a connection to the pool."""
        if cls._connection_pool is not None and conn is not None:
            try:
                cls._connection_pool.putconn(conn)
            except Exception as e:
                logger.warning(f"Error returning connection to pool: {e}")
    
    @classmethod
    def _execute_query(cls, query: str, params: Optional[Tuple] = None, fetch_one: bool = False, 
                      fetch_all: bool = False, commit: bool = True) -> Union[List, Dict, None]:
        """
        Execute a database query with proper error handling and connection management.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            fetch_one: Whether to fetch a single row
            fetch_all: Whether to fetch all rows
            commit: Whether to commit the transaction
            
        Returns:
            Query results if fetch_one or fetch_all is True, None otherwise
        """
        conn = None
        result = None
        
        try:
            conn = cls.get_connection()
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(query, params)
                
                if fetch_one:
                    result = dict(cur.fetchone()) if cur.rowcount > 0 else None
                elif fetch_all:
                    result = [dict(row) for row in cur.fetchall()]
                    
                if commit:
                    conn.commit()
                    
            return result
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database query error: {e}")
            logger.debug(f"Query: {query}, Params: {params}")
            raise
        finally:
            if conn:
                cls.return_connection(conn)
    
    @classmethod
    def create_tables(cls):
        """Create necessary database tables if they don't exist."""
        tables_queries = [
            # Create blocks table
            """
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
            """,
            
            # Create transactions table
            """
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
            """,
            
            # Create wallets table
            """
            CREATE TABLE IF NOT EXISTS wallets (
                id SERIAL PRIMARY KEY,
                address VARCHAR(255) NOT NULL UNIQUE,
                public_key TEXT NOT NULL,
                encrypted_private_key JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Create peers table
            """
            CREATE TABLE IF NOT EXISTS peers (
                id SERIAL PRIMARY KEY,
                node_id VARCHAR(255) NOT NULL UNIQUE,
                host VARCHAR(255) NOT NULL,
                port INTEGER NOT NULL,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_trusted BOOLEAN DEFAULT FALSE
            )
            """,
            
            # Add indexes for performance
            "CREATE INDEX IF NOT EXISTS idx_transactions_hash ON transactions(transaction_hash)",
            "CREATE INDEX IF NOT EXISTS idx_blocks_hash ON blocks(hash)",
            "CREATE INDEX IF NOT EXISTS idx_wallets_address ON wallets(address)",
            "CREATE INDEX IF NOT EXISTS idx_peers_node_id ON peers(node_id)"
        ]
        
        conn = None
        try:
            conn = cls.get_connection()
            with conn.cursor() as cur:
                for query in tables_queries:
                    cur.execute(query)
                conn.commit()
                logger.info("Database tables created successfully")
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to create database tables: {e}")
            raise
        finally:
            if conn:
                cls.return_connection(conn)
    
    @classmethod
    def save_block(cls, block_data: Dict[str, Any]) -> bool:
        """
        Save a block to the database.
        
        Args:
            block_data: Block data to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        conn = None
        try:
            # Generate a consistent JSON string for storage
            block_json = json.dumps(block_data, sort_keys=True)
            
            conn = cls.get_connection()
            with conn.cursor() as cur:
                # Insert block with parameterized query
                cur.execute("""
                    INSERT INTO blocks (index, timestamp, previous_hash, hash, nonce, data)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (hash) DO NOTHING
                    RETURNING id
                """, (
                    block_data['index'],
                    block_data['timestamp'],
                    block_data['previous_hash'],
                    block_data['hash'],
                    block_data['nonce'],
                    block_json
                ))
                
                # Check if block was inserted
                result = cur.fetchone()
                if not result:
                    # Block already exists
                    logger.info(f"Block {block_data['hash']} already exists in database")
                    conn.commit()
                    return True
                    
                block_id = result[0]
                
                # Save transactions
                for tx in block_data.get('transactions', []):
                    # Generate a transaction hash if not present
                    tx_hash = tx.get('hash', hashlib.sha256(json.dumps(tx, sort_keys=True).encode()).hexdigest())
                    
                    cur.execute("""
                        INSERT INTO transactions 
                        (block_id, transaction_hash, sender, recipient, amount, timestamp, signature, is_pending)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, FALSE)
                        ON CONFLICT (transaction_hash) DO UPDATE
                        SET is_pending = FALSE,
                            block_id = EXCLUDED.block_id
                    """, (
                        block_id,
                        tx_hash,
                        tx['sender'],
                        tx['recipient'],
                        tx['amount'],
                        tx['timestamp'],
                        tx.get('signature')
                    ))
                
                conn.commit()
                logger.info(f"Block {block_data['index']} (hash: {block_data['hash']}) saved successfully")
                return True
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to save block: {e}")
            return False
        finally:
            if conn:
                cls.return_connection(conn)
    
    @classmethod
    def get_blocks(cls) -> List[Dict[str, Any]]:
        """
        Get all blocks from the database.
        
        Returns:
            List[Dict[str, Any]]: List of blocks
        """
        return cls._execute_query(
            "SELECT data FROM blocks ORDER BY index",
            fetch_all=True
        ) or []
    
    @classmethod
    def save_transaction(cls, transaction: Dict[str, Any]) -> bool:
        """
        Save a pending transaction to the database.
        
        Args:
            transaction: Transaction data to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        conn = None
        try:
            # Generate a transaction hash
            tx_hash = transaction.get('hash', hashlib.sha256(
                json.dumps(transaction, sort_keys=True).encode()
            ).hexdigest())
            
            conn = cls.get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO transactions 
                    (transaction_hash, sender, recipient, amount, timestamp, signature, is_pending)
                    VALUES (%s, %s, %s, %s, %s, %s, TRUE)
                    ON CONFLICT (transaction_hash) DO NOTHING
                """, (
                    tx_hash,
                    transaction['sender'],
                    transaction['recipient'],
                    transaction['amount'],
                    transaction['timestamp'],
                    transaction.get('signature')
                ))
                conn.commit()
                logger.info(f"Transaction {tx_hash} saved successfully")
                return True
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to save transaction: {e}")
            return False
        finally:
            if conn:
                cls.return_connection(conn)
    
    @classmethod
    def get_pending_transactions(cls) -> List[Dict[str, Any]]:
        """
        Get all pending transactions from the database.
        
        Returns:
            List[Dict[str, Any]]: List of pending transactions
        """
        return cls._execute_query(
            """
            SELECT transaction_hash as hash, sender, recipient, amount, timestamp, signature
            FROM transactions
            WHERE is_pending = TRUE
            """,
            fetch_all=True
        ) or []
    
    @classmethod
    def save_wallet(cls, wallet_data: Dict[str, Any]) -> bool:
        """
        Save a wallet to the database.
        
        Args:
            wallet_data: Wallet data to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Check required fields
        if 'address' not in wallet_data or 'public_key' not in wallet_data:
            logger.error("Missing required wallet data fields")
            return False
            
        conn = None
        try:
            conn = cls.get_connection()
            with conn.cursor() as cur:
                encrypted_private_key = wallet_data.get('encrypted_private_key')
                encrypted_private_key_json = json.dumps(encrypted_private_key) if encrypted_private_key else None
                
                cur.execute("""
                    INSERT INTO wallets (address, public_key, encrypted_private_key)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (address) DO UPDATE
                    SET public_key = EXCLUDED.public_key,
                        encrypted_private_key = EXCLUDED.encrypted_private_key,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    wallet_data['address'],
                    wallet_data['public_key'],
                    encrypted_private_key_json
                ))
                conn.commit()
                logger.info(f"Wallet {wallet_data['address']} saved successfully")
                return True
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to save wallet: {e}")
            return False
        finally:
            if conn:
                cls.return_connection(conn)
    
    @classmethod
    def get_wallet(cls, address: str) -> Optional[Dict[str, Any]]:
        """
        Get a wallet from the database by address.
        
        Args:
            address: Wallet address to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Wallet data if found, None otherwise
        """
        # Validate address
        if not address or not isinstance(address, str) or len(address) > 255:
            logger.warning(f"Invalid wallet address format: {address}")
            return None
            
        return cls._execute_query(
            """
            SELECT address, public_key, encrypted_private_key
            FROM wallets
            WHERE address = %s
            """,
            (address,),
            fetch_one=True
        )
    
    @classmethod
    def save_peer(cls, peer_data: Dict[str, Any]) -> bool:
        """
        Save a peer to the database.
        
        Args:
            peer_data: Peer data to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Check required fields
        if 'node_id' not in peer_data or 'host' not in peer_data or 'port' not in peer_data:
            logger.error("Missing required peer data fields")
            return False
            
        # Validate peer data
        if not isinstance(peer_data['node_id'], str) or len(peer_data['node_id']) > 255:
            logger.warning(f"Invalid peer node_id format: {peer_data['node_id']}")
            return False
            
        if not isinstance(peer_data['host'], str) or len(peer_data['host']) > 255:
            logger.warning(f"Invalid peer host format: {peer_data['host']}")
            return False
            
        if not isinstance(peer_data['port'], int) or peer_data['port'] < 1 or peer_data['port'] > 65535:
            logger.warning(f"Invalid peer port format: {peer_data['port']}")
            return False
            
        conn = None
        try:
            conn = cls.get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO peers (node_id, host, port, is_trusted)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (node_id) DO UPDATE
                    SET host = EXCLUDED.host,
                        port = EXCLUDED.port,
                        is_trusted = EXCLUDED.is_trusted,
                        last_seen = CURRENT_TIMESTAMP
                """, (
                    peer_data['node_id'],
                    peer_data['host'],
                    peer_data['port'],
                    peer_data.get('is_trusted', False)
                ))
                conn.commit()
                logger.info(f"Peer {peer_data['node_id']} saved successfully")
                return True
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to save peer: {e}")
            return False
        finally:
            if conn:
                cls.return_connection(conn)
    
    @classmethod
    def get_peers(cls, trusted_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get all peers from the database.
        
        Args:
            trusted_only: Whether to get only trusted peers
            
        Returns:
            List[Dict[str, Any]]: List of peers
        """
        if trusted_only:
            return cls._execute_query(
                """
                SELECT node_id, host, port, is_trusted
                FROM peers
                WHERE is_trusted = TRUE AND
                      last_seen > CURRENT_TIMESTAMP - INTERVAL '1 hour'
                """,
                fetch_all=True
            ) or []
        else:
            return cls._execute_query(
                """
                SELECT node_id, host, port, is_trusted
                FROM peers
                WHERE last_seen > CURRENT_TIMESTAMP - INTERVAL '1 hour'
                """,
                fetch_all=True
            ) or []
    
    @classmethod
    def clear_data(cls) -> bool:
        """
        Clear all data from the database.
        
        Returns:
            bool: True if successful, False otherwise
        """
        conn = None
        try:
            conn = cls.get_connection()
            with conn.cursor() as cur:
                cur.execute("TRUNCATE blocks, transactions, wallets, peers CASCADE")
                conn.commit()
                logger.info("Database cleared successfully")
                return True
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to clear database: {e}")
            return False
        finally:
            if conn:
                cls.return_connection(conn) 