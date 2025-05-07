import time
import hashlib
import json
from typing import List, Dict, Any, Optional
from .transaction import Transaction
import logging

logger = logging.getLogger(__name__)

class Block:
    """
    Represents a block in the blockchain.
    Contains transactions, hash, previous hash, and proof-of-work.
    """
    
    def __init__(self, index: int, transactions: List[Transaction], previous_hash: str, 
                timestamp: Optional[float] = None, nonce: int = 0, hash: Optional[str] = None):
        """
        Initialize a new block.
        
        Args:
            index: Block index in the chain
            transactions: List of transactions
            previous_hash: Hash of the previous block
            timestamp: Optional timestamp (defaults to current time)
            nonce: Nonce for proof-of-work (defaults to 0)
            hash: Block hash (calculated if not provided)
        """
        self.index = index
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.timestamp = timestamp or time.time()
        self.nonce = nonce
        self.hash = hash or self.calculate_hash()
        
        # Validate inputs
        if not isinstance(index, int) or index < 0:
            raise ValueError("Block index must be a non-negative integer")
            
        if not isinstance(transactions, list):
            raise ValueError("Transactions must be a list")
            
        if not isinstance(previous_hash, str) or len(previous_hash) != 64:
            raise ValueError("Previous hash must be a 64-character string")
    
    def calculate_hash(self) -> str:
        """
        Calculate the hash of the block.
        
        Returns:
            Hex-encoded SHA-256 hash of the block data
        """
        # Create a sorted and deterministic data structure for hash calculation
        block_data = {
            'index': self.index,
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'transactions': [tx.to_dict() for tx in self.transactions]
        }
        
        # Convert to JSON with deterministic ordering
        block_string = json.dumps(block_data, sort_keys=True)
        
        # Calculate hash using SHA-256
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self, difficulty: int) -> None:
        """
        Mine the block by finding a hash with a specified number of leading zeros.
        
        Args:
            difficulty: Number of leading zeros required in the hash
        """
        if difficulty < 1:
            logger.warning(f"Mining with low difficulty: {difficulty}")
        elif difficulty > 8:
            logger.warning(f"Mining with very high difficulty: {difficulty}")
            
        target = '0' * difficulty
        max_nonce = 2**32  # Prevent infinite loops
        
        start_time = time.time()
        for i in range(max_nonce):
            self.nonce = i
            self.hash = self.calculate_hash()
            
            if self.hash.startswith(target):
                mining_time = time.time() - start_time
                logger.info(f"Block mined in {mining_time:.2f} seconds with nonce {self.nonce}")
                return
                
        # If we reach here, we couldn't find a valid hash
        raise RuntimeError(f"Failed to mine block after {max_nonce} attempts")
    
    def is_valid(self, difficulty: int) -> bool:
        """
        Verify that the block is valid:
        1. The hash matches the block data
        2. The hash has the required number of leading zeros
        
        Args:
            difficulty: Number of leading zeros required in the hash
            
        Returns:
            True if the block is valid, False otherwise
        """
        # Check that hash is correctly calculated
        calculated_hash = self.calculate_hash()
        if calculated_hash != self.hash:
            logger.warning(f"Block hash mismatch: {self.hash} vs {calculated_hash}")
            return False
            
        # Check proof-of-work
        target = '0' * difficulty
        if not self.hash.startswith(target):
            logger.warning(f"Block hash does not meet difficulty requirement: {self.hash}")
            return False
            
        # Validate transactions
        for tx in self.transactions:
            if not isinstance(tx, Transaction):
                logger.warning("Block contains an invalid transaction type")
                return False
                
            if not tx.verify():
                logger.warning(f"Block contains an invalid transaction: {tx}")
                return False
                
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the block to a dictionary for serialization.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the block
        """
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'hash': self.hash,
            'nonce': self.nonce,
            'transactions': [tx.to_dict() for tx in self.transactions]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Block':
        """
        Create a Block instance from a dictionary.
        
        Args:
            data: Dictionary containing block data
            
        Returns:
            Block: New Block instance
        """
        # Validate required fields
        required_fields = ['index', 'timestamp', 'previous_hash', 'hash', 'nonce', 'transactions']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Convert transaction dictionaries to Transaction objects
        transactions = []
        for tx_data in data['transactions']:
            try:
                tx = Transaction.from_dict(tx_data)
                transactions.append(tx)
            except ValueError as e:
                logger.warning(f"Skipping invalid transaction: {e}")
        
        # Create and return the block
        return cls(
            index=data['index'],
            timestamp=data['timestamp'],
            previous_hash=data['previous_hash'],
            nonce=data['nonce'],
            hash=data['hash'],
            transactions=transactions
        )
    
    def __str__(self) -> str:
        """Return a string representation of the block."""
        return (
            f"Block(index={self.index}, hash={self.hash[:10]}..., "
            f"previous_hash={self.previous_hash[:10]}..., "
            f"transactions={len(self.transactions)}, nonce={self.nonce})"
        ) 