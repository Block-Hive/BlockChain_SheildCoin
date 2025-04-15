import json
import time
from typing import List, Dict, Any, Optional
from .block import Block
from .transaction import Transaction
from .transaction_pool import TransactionPool
from ..config import INITIAL_DIFFICULTY, MINING_REWARD

class Blockchain:
    """
    Represents the blockchain network. Maintains a list of blocks and provides
    methods for adding new blocks, validating the chain, and managing consensus.
    """
    
    def __init__(self, difficulty: int = INITIAL_DIFFICULTY):
        """
        Initialize a new blockchain.
        
        Args:
            difficulty: Mining difficulty (number of leading zeros required)
        """
        self.chain: List[Block] = [self._create_genesis_block()]
        self.difficulty = difficulty
        self.transaction_pool = TransactionPool()
        self.mining_reward = MINING_REWARD
        self.block_time = 10  # Target time between blocks in seconds
        self.difficulty_adjustment_interval = 10  # Adjust difficulty every N blocks
    
    def _create_genesis_block(self) -> Block:
        """Create the first block in the chain."""
        return Block(
            index=0,
            transactions=[],
            previous_hash="0" * 64
        )
    
    def get_latest_block(self) -> Block:
        """Get the most recent block in the chain."""
        return self.chain[-1]
    
    def add_transaction(self, transaction: Dict[str, Any] | Transaction) -> bool:
        """
        Add a new transaction to the pool.
        
        Args:
            transaction: Transaction to add (can be dict or Transaction object)
            
        Returns:
            True if transaction was added, False otherwise
        """
        return self.transaction_pool.add_transaction(transaction)
    
    def mine_pending_transactions(self, miner_address: str) -> Optional[Block]:
        """
        Mine a new block with pending transactions.
        
        Args:
            miner_address: Address of the miner
            
        Returns:
            New block if mining successful, None otherwise
        """
        # Create mining reward transaction
        reward_tx = Transaction(
            sender="system",
            recipient=miner_address,
            amount=MINING_REWARD
        )
        
        # Get pending transactions
        transactions = self.transaction_pool.get_transactions()
        transactions.insert(0, reward_tx)
        
        # Create new block
        new_block = Block(
            index=len(self.chain),
            transactions=transactions,
            previous_hash=self.get_latest_block().hash
        )
        
        # Mine the block
        new_block.mine_block(self.difficulty)
        
        # Add block to chain
        self.chain.append(new_block)

        #Todo : Lock Transaction pool at that time.
        
        # Clear transaction pool
        self.transaction_pool.clear_transactions()
        
        return new_block
    
    def add_block(self, block: Block) -> bool:
        """
        Add a new block to the chain.
        
        Args:
            block: Block to add
            
        Returns:
            True if block was added, False otherwise
        """
        # Verify block
        if not self._is_valid_block(block):
            return False
        
        # Add block to chain
        self.chain.append(block)
        
        # Remove transactions from pool
        self.transaction_pool.remove_transactions(block.transactions)
        
        return True
    
    def replace_chain(self, new_chain: List[Dict[str, Any]]) -> bool:
        """
        Replace the current chain with a new one if it's valid and longer.
        
        Args:
            new_chain: List of block dictionaries
            
        Returns:
            True if chain was replaced, False otherwise
        """
        # Convert dictionary chain to Block objects
        new_blocks = [Block.from_dict(block_data) for block_data in new_chain]
        
        # Verify new chain
        if not self._is_valid_chain(new_blocks):
            return False
        
        # Only replace if new chain is longer
        if len(new_blocks) <= len(self.chain):
            return False
        
        # Replace chain
        self.chain = new_blocks
        return True
    
    def _is_valid_block(self, block: Block) -> bool:
        """
        Check if a block is valid.
        
        Args:
            block: Block to validate
            
        Returns:
            True if block is valid, False otherwise
        """
        # Check block index
        if block.index != len(self.chain):
            return False
        
        # Check previous hash
        if block.previous_hash != self.get_latest_block().hash:
            return False
        
        # Check block hash
        if block.hash != block.calculate_hash():
            return False
        
        # Check proof of work
        if block.hash[:self.difficulty] != "0" * self.difficulty:
            return False
        
        return True
    
    def _is_valid_chain(self, chain: List[Block]) -> bool:
        """
        Check if a chain is valid.
        
        Args:
            chain: Chain to validate
            
        Returns:
            True if chain is valid, False otherwise
        """
        # Check genesis block
        if chain[0].index != 0 or chain[0].previous_hash != "0" * 64:
            return False
        
        # Check each block
        for i in range(1, len(chain)):
            current = chain[i]
            previous = chain[i-1]
            
            # Check block index
            if current.index != i:
                return False
            
            # Check previous hash
            if current.previous_hash != previous.hash:
                return False
            
            # Check block hash
            if current.hash != current.calculate_hash():
                return False
            
            # Check proof of work
            if current.hash[:self.difficulty] != "0" * self.difficulty:
                return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert blockchain to dictionary."""
        return {
            'chain': [block.to_dict() for block in self.chain],
            'difficulty': self.difficulty,
            'mining_reward': self.mining_reward,
            'block_time': self.block_time,
            'difficulty_adjustment_interval': self.difficulty_adjustment_interval
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Blockchain':
        """Create a blockchain from dictionary data."""
        blockchain = cls(difficulty=data['difficulty'])
        blockchain.chain = [Block.from_dict(block_data) for block_data in data['chain']]
        blockchain.mining_reward = data['mining_reward']
        blockchain.block_time = data['block_time']
        blockchain.difficulty_adjustment_interval = data['difficulty_adjustment_interval']
        return blockchain
    
    def adjust_difficulty(self) -> None:
        """
        Adjust the mining difficulty based on the average block time.
        This helps maintain a consistent block creation rate.
        """
        if len(self.chain) % self.difficulty_adjustment_interval != 0:
            return
        
        # Calculate average block time for the last N blocks
        recent_blocks = self.chain[-self.difficulty_adjustment_interval:]
        time_diffs = [
            recent_blocks[i].timestamp - recent_blocks[i-1].timestamp
            for i in range(1, len(recent_blocks))
        ]
        avg_block_time = sum(time_diffs) / len(time_diffs)
        
        # Adjust difficulty based on average block time
        if avg_block_time < self.block_time / 2:
            self.difficulty += 1
        elif avg_block_time > self.block_time * 2:
            self.difficulty = max(1, self.difficulty - 1) 