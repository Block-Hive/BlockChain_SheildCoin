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
        self.difficulty = difficulty
        self.mining_reward = MINING_REWARD
        self.block_time = 10  # Target time between blocks in seconds
        self.difficulty_adjustment_interval = 10  # Adjust difficulty every N blocks
        self.transaction_pool = TransactionPool()
        self.chain = []  # Initialize empty chain
        self._create_genesis_block()  # Create genesis block after setting difficulty
    
    def _create_genesis_block(self, seed=None) -> Block:
        """Create the genesis block."""
        # Check if genesis block already exists
        if len(self.chain) > 0:
            print("Genesis block already exists, skipping creation")
            return self.chain[0]
            
        # Use fixed seed for consistent genesis block across all nodes
        if seed:
            import random
            random.seed(seed)
        
        genesis_block = Block(
            index=0,
            timestamp=1234567890,  # Fixed timestamp for genesis block
            transactions=[],
            previous_hash="0" * 64
        )
        genesis_block.mine_block(self.difficulty)
        self.chain.append(genesis_block)
        print(f"Genesis block created with hash: {genesis_block.hash}")
        return genesis_block
    
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
        # Skip if no transactions and not a system miner
        if not self.transaction_pool.transactions and miner_address != "system":
            print("No transactions to mine and miner is not system")
            return None
            
        # Create mining reward transaction
        if miner_address != "system":  # Skip reward for system mining (genesis)
            reward_tx = Transaction(
                sender="system",
                recipient=miner_address,
                amount=self.mining_reward
            )
            
        # Get pending transactions
        transactions = self.transaction_pool.get_transactions()
        
        # Add reward transaction at the beginning
        if miner_address != "system":
            transactions.insert(0, reward_tx)
        
        # Create new block
        new_block = Block(
            index=len(self.chain),
            transactions=transactions,
            previous_hash=self.get_latest_block().hash
        )
        
        # Mine the block
        print(f"Mining new block at index {new_block.index}...")
        start_time = time.time()
        new_block.mine_block(self.difficulty)
        end_time = time.time()
        mining_time = end_time - start_time
        print(f"Block mined in {mining_time:.2f} seconds with hash: {new_block.hash}")
        
        # Add block to chain
        result = self.add_block(new_block)
        
        if result:
            # Clear transaction pool on successful mining
            self.transaction_pool.clear_transactions()
            return new_block
        else:
            print("Failed to add mined block to chain")
            return None
    
    def add_block(self, block: Block) -> bool:
        """
        Add a new block to the chain.
        
        Args:
            block: Block to add
            
        Returns:
            True if block was added, False otherwise
        """
        # Check if block already exists
        if any(existing_block.hash == block.hash for existing_block in self.chain):
            print(f"Block with hash {block.hash} already exists in chain")
            return False
        
        # Verify block
        if not self._is_valid_block(block):
            print(f"Block with hash {block.hash} failed validation")
            return False
        
        # Add block to chain
        self.chain.append(block)
        print(f"Added new block with hash {block.hash} at index {block.index}")
        
        # Remove transactions from pool
        self.transaction_pool.remove_transactions(block.transactions)
        
        # Adjust difficulty if needed
        self.adjust_difficulty()
        
        return True
    
    def replace_chain(self, new_chain: List[Dict[str, Any]]) -> bool:
        """
        Replace the current chain with a new one if it's valid and longer.
        
        Args:
            new_chain: List of block dictionaries
            
        Returns:
            True if chain was replaced, False otherwise
        """
        # Verify input
        if not isinstance(new_chain, list) or len(new_chain) == 0:
            print("Error: new_chain must be a non-empty list")
            return False
            
        # Convert dictionary chain to Block objects
        try:
            new_blocks = [Block.from_dict(block_data) for block_data in new_chain]
        except Exception as e:
            print(f"Error converting dictionary chain to blocks: {e}")
            return False
        
        # Check for duplicate blocks
        block_hashes = set()
        for block in new_blocks:
            if block.hash in block_hashes:
                print(f"Error: duplicate block with hash {block.hash} found in new chain")
                return False
            block_hashes.add(block.hash)
        
        # Verify new chain
        if not self._is_valid_chain(new_blocks):
            print("Error: new chain is invalid")
            return False
        
        # Only replace if new chain is longer
        if len(new_blocks) <= len(self.chain):
            print(f"Error: new chain is not longer than current chain ({len(new_blocks)} <= {len(self.chain)})")
            return False
        
        # Replace chain
        self.chain = new_blocks
        print(f"Chain replaced with new chain of length {len(new_blocks)}")
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
            print(f"Invalid block index: {block.index}, expected {len(self.chain)}")
            return False
        
        # Check previous hash
        if block.previous_hash != self.get_latest_block().hash:
            print(f"Invalid previous hash: {block.previous_hash}, expected {self.get_latest_block().hash}")
            return False
        
        # Use block's built-in validation
        if not block.is_valid(self.difficulty):
            print("Block failed hash validation")
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
            print("Invalid genesis block")
            return False
        
        # Check each block
        for i in range(1, len(chain)):
            current = chain[i]
            previous = chain[i-1]
            
            # Check block index
            if current.index != i:
                print(f"Invalid block index at position {i}: {current.index}")
                return False
            
            # Check block references previous block
            if current.previous_hash != previous.hash:
                print(f"Invalid previous hash at position {i}")
                return False
            
            # Verify block hash
            if not current.is_valid(self.difficulty):
                print(f"Invalid block hash at position {i}")
                return False
                
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert blockchain to dictionary."""
        return {
            'chain': [block.to_dict() for block in self.chain],
            'difficulty': self.difficulty,
            'mining_reward': self.mining_reward,
            'transaction_pool': self.transaction_pool.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Blockchain':
        """Create a blockchain from dictionary data."""
        blockchain = cls(difficulty=data.get('difficulty', INITIAL_DIFFICULTY))
        
        # Clear default genesis block
        blockchain.chain = []
        
        # Add blocks
        for block_data in data.get('chain', []):
            blockchain.chain.append(Block.from_dict(block_data))
        
        # Set mining reward
        if 'mining_reward' in data:
            blockchain.mining_reward = data['mining_reward']
        
        # Set transaction pool
        if 'transaction_pool' in data:
            blockchain.transaction_pool = TransactionPool.from_dict(data['transaction_pool'])
        
        return blockchain
    
    def adjust_difficulty(self) -> None:
        """Adjust mining difficulty based on block time."""
        if len(self.chain) % self.difficulty_adjustment_interval != 0:
            return
            
        if len(self.chain) <= self.difficulty_adjustment_interval:
            return
            
        # Calculate the time it took to mine the last N blocks
        prev_adjustment_block = self.chain[-self.difficulty_adjustment_interval]
        time_expected = self.block_time * self.difficulty_adjustment_interval
        time_taken = self.get_latest_block().timestamp - prev_adjustment_block.timestamp
        
        # Adjust difficulty if mining was too fast or too slow
        if time_taken < time_expected / 2:
            self.difficulty += 1
            print(f"Increased difficulty to {self.difficulty}")
        elif time_taken > time_expected * 2:
            if self.difficulty > 1:
                self.difficulty -= 1
                print(f"Decreased difficulty to {self.difficulty}")
    
    def add_block_from_dict(self, block_data: Dict[str, Any]) -> bool:
        """Add a block from dictionary data."""
        try:
            block = Block.from_dict(block_data)
            return self.add_block(block)
        except Exception as e:
            print(f"Failed to add block from dict: {e}")
            return False
    
    def get_balance(self, address: str) -> float:
        """
        Calculate the balance of an address by looking at all transactions.
        
        Args:
            address: Wallet address to check
            
        Returns:
            float: Current balance
        """
        balance = 0.0
        
        # Calculate balance from all blocks in the chain
        for block in self.chain:
            for tx in block.transactions:
                if tx.sender == address:
                    balance -= tx.amount
                if tx.recipient == address:
                    balance += tx.amount
        
        return balance 