from typing import List, Dict, Any, Union
from .transaction import Transaction
from ..config import MAX_TRANSACTION_POOL_SIZE

class TransactionPool:
    """Manages a pool of pending transactions."""
    
    def __init__(self, max_size: int = MAX_TRANSACTION_POOL_SIZE):
        """Initialize an empty transaction pool."""
        self.transactions: List[Transaction] = []
        self.max_size = max_size
    
    def add_transaction(self, transaction: Union[Dict[str, Any], Transaction]) -> bool:
        """
        Add a transaction to the pool.
        
        Args:
            transaction: Transaction to add (can be dict or Transaction object)
            
        Returns:
            True if transaction was added, False otherwise
        """
        # Check pool capacity
        if len(self.transactions) >= self.max_size:
            print(f"Transaction pool full ({self.max_size} transactions)")
            return False
        
        # Convert dict to Transaction if needed
        if isinstance(transaction, dict):
            try:
                transaction = Transaction.from_dict(transaction)
            except Exception as e:
                print(f"Invalid transaction data: {e}")
                return False
        
        # Verify the transaction
        if not transaction.verify():
            print(f"Transaction verification failed")
            return False
            
        # Check for duplicate transactions
        for tx in self.transactions:
            if (tx.sender == transaction.sender and 
                tx.recipient == transaction.recipient and 
                tx.amount == transaction.amount and 
                tx.timestamp == transaction.timestamp):
                print(f"Duplicate transaction rejected")
                return False
                
        self.transactions.append(transaction)
        print(f"Added transaction: {transaction.sender} -> {transaction.recipient} ({transaction.amount})")
        return True
    
    def get_transactions(self) -> List[Transaction]:
        """Get all transactions in the pool."""
        return self.transactions.copy()  # Return a copy to prevent external modification
    
    def remove_transactions(self, transactions: List[Transaction]) -> None:
        """Remove transactions from the pool."""
        # Create a set of transaction signatures for faster lookup
        tx_signatures = {tx.signature for tx in transactions if tx.signature}
        
        # Keep transactions that aren't in the removal list
        self.transactions = [tx for tx in self.transactions 
                            if tx.signature not in tx_signatures]
    
    def clear_transactions(self) -> None:
        """Clear all transactions from the pool."""
        self.transactions = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction pool to dictionary."""
        return {
            'transactions': [tx.to_dict() for tx in self.transactions]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TransactionPool':
        """Create a transaction pool from dictionary data."""
        pool = cls()
        
        # Add transactions from data if present
        if 'transactions' in data:
            for tx_data in data['transactions']:
                try:
                    pool.add_transaction(Transaction.from_dict(tx_data))
                except Exception:
                    # Skip invalid transactions
                    pass
                    
        return pool 