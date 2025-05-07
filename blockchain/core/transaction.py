import time
from typing import Dict, Any, Optional
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
import json
import logging
import decimal

# Configure logging
logger = logging.getLogger(__name__)

class Transaction:
    """
    Represents a single transaction in the blockchain.
    Handles transaction creation, validation, and signing.
    """
    
    # Constants for validation
    MAX_AMOUNT = 1000000000  # 1 billion units
    MIN_AMOUNT = decimal.Decimal('0.00000001')  # Minimum transaction amount
    
    def __init__(self, sender: str, recipient: str, amount: float, timestamp: Optional[float] = None, signature: Optional[str] = None):
        """
        Initialize a new transaction.
        
        Args:
            sender: Sender's public address
            recipient: Recipient's public address
            amount: Amount to transfer
            timestamp: Optional timestamp (defaults to current time)
            signature: Optional signature
        """
        # Validate inputs
        if not sender or not isinstance(sender, str):
            raise ValueError("Sender must be a valid string")
        if not recipient or not isinstance(recipient, str):
            raise ValueError("Recipient must be a valid string")
        
        # Convert amount to Decimal for precision
        try:
            amount_decimal = decimal.Decimal(str(amount))
            if amount_decimal <= 0:
                raise ValueError("Amount must be positive")
            if amount_decimal < self.MIN_AMOUNT:
                raise ValueError(f"Amount is too small (minimum: {self.MIN_AMOUNT})")
            if amount_decimal > self.MAX_AMOUNT:
                raise ValueError(f"Amount is too large (maximum: {self.MAX_AMOUNT})")
            
            # Store as float but validate as Decimal
            self.amount = float(amount_decimal)
        except (ValueError, decimal.InvalidOperation):
            raise ValueError("Invalid amount format")
            
        self.sender = sender
        self.recipient = recipient
        self.timestamp = timestamp or time.time()
        self.signature = signature
    
    def sign(self, private_key: RSA.RsaKey) -> None:
        """
        Sign the transaction with a private key.
        
        Args:
            private_key: Private key to sign with
        """
        # Check if already signed
        if self.signature:
            logger.warning("Transaction already signed, overwriting existing signature")
            
        # System transactions don't need signing
        if self.sender == "system":
            return
            
        try:
            # Create a hash of the transaction data without the signature
            tx_dict = self.to_dict()
            tx_dict.pop('signature', None)
            transaction_hash = SHA256.new(
                json.dumps(tx_dict, sort_keys=True).encode()
            )
            
            # Sign the hash with the private key
            self.signature = pkcs1_15.new(private_key).sign(transaction_hash).hex()
        except Exception as e:
            logger.error(f"Failed to sign transaction: {e}")
            raise ValueError(f"Failed to sign transaction: {e}")
    
    def verify(self) -> bool:
        """
        Verify the transaction signature.
        
        Returns:
            True if signature is valid, False otherwise
        """
        # System transactions (mining rewards) are always valid
        if self.sender == "system":
            return True
        
        # If no signature, transaction is invalid
        if not self.signature:
            logger.warning(f"Transaction from {self.sender} has no signature")
            return False
            
        # Basic amount validation
        try:
            amount_decimal = decimal.Decimal(str(self.amount))
            if amount_decimal <= 0 or amount_decimal < self.MIN_AMOUNT or amount_decimal > self.MAX_AMOUNT:
                logger.warning(f"Invalid amount in transaction: {self.amount}")
                return False
        except (ValueError, decimal.InvalidOperation):
            logger.warning(f"Invalid amount format in transaction: {self.amount}")
            return False
        
        try:
            # Create a hash of the transaction data without the signature
            tx_dict = self.to_dict()
            tx_dict.pop('signature', None)
            transaction_hash = SHA256.new(
                json.dumps(tx_dict, sort_keys=True).encode()
            )
            
            # Import the public key from the sender's address
            try:
                public_key = RSA.import_key(self.sender)
            except ValueError:
                logger.warning(f"Invalid public key format from sender: {self.sender}")
                return False
            
            # Verify the signature
            pkcs1_15.new(public_key).verify(
                transaction_hash,
                bytes.fromhex(self.signature)
            )
            return True
        except Exception as e:
            logger.warning(f"Signature verification failed for transaction from {self.sender} to {self.recipient}: {e}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the transaction to a dictionary for serialization.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the transaction
        """
        result = {
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': self.amount,
            'timestamp': self.timestamp
        }
        
        if self.signature:
            result['signature'] = self.signature
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Transaction':
        """
        Create a Transaction instance from a dictionary.
        
        Args:
            data: Dictionary containing transaction data
            
        Returns:
            Transaction: New Transaction instance
        """
        # Handle both field naming conventions
        sender = data.get('sender') or data.get('from')
        recipient = data.get('recipient') or data.get('to')
        
        if not sender or not recipient:
            raise ValueError("Transaction must have sender and recipient")
            
        amount = data.get('amount')
        if amount is None:
            raise ValueError("Transaction must have an amount")
            
        timestamp = data.get('timestamp')
        signature = data.get('signature')
        
        # Additional input validation
        try:
            # Validate amount format
            amount_decimal = decimal.Decimal(str(amount))
            if amount_decimal <= 0:
                raise ValueError("Amount must be positive")
                
            # Create and return the transaction
            return cls(
                sender=sender,
                recipient=recipient,
                amount=float(amount),
                timestamp=timestamp,
                signature=signature
            )
        except (ValueError, decimal.InvalidOperation) as e:
            logger.error(f"Error creating transaction from dictionary: {e}")
            raise ValueError(f"Invalid transaction data: {e}")
    
    def __str__(self) -> str:
        """Return a string representation of the transaction."""
        return (
            f"Transaction(sender={self.sender}, recipient={self.recipient}, "
            f"amount={self.amount}, timestamp={self.timestamp})"
        )
        
    def __eq__(self, other) -> bool:
        """Check if two transactions are equal based on their data."""
        if not isinstance(other, Transaction):
            return False
            
        return (self.sender == other.sender and
                self.recipient == other.recipient and
                self.amount == other.amount and
                self.timestamp == other.timestamp and
                self.signature == other.signature)
                
    def get_hash(self) -> str:
        """Get a unique hash for this transaction."""
        tx_dict = self.to_dict()
        tx_str = json.dumps(tx_dict, sort_keys=True)
        return SHA256.new(tx_str.encode()).hexdigest() 