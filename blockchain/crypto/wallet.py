from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import json
import hashlib
import os
import base64
from typing import Dict, Any, Optional

class Wallet:
    """Handles cryptographic operations including key generation, signing, and verification."""
    
    def __init__(self, password: str = None):
        """Initialize a new wallet with optional password encryption."""
        # Use 3072 bits for stronger security (NIST recommendation)
        self.private_key = RSA.generate(3072)
        self.public_key = self.private_key.publickey()
        self.address = self.generate_address()
        self.encrypted_private_key = None
        
        # Encrypt the private key if password is provided
        if password:
            self.encrypt_private_key(password)
    
    def get_address(self) -> str:
        """Get the wallet's public address."""
        return self.address
    
    def generate_address(self) -> str:
        """Generate a unique address for the wallet."""
        public_key_bytes = self.public_key.export_key()
        # Use SHA3-256 for enhanced security
        return hashlib.sha3_256(public_key_bytes).hexdigest()
    
    def encrypt_private_key(self, password: str) -> None:
        """Encrypt the private key with a password."""
        # Generate a salt
        salt = get_random_bytes(32)
        # Generate a key from the password
        key = PBKDF2(password.encode(), salt, dkLen=32, count=1000000)
        # Generate a random IV
        iv = get_random_bytes(16)
        # Encrypt the private key
        cipher = AES.new(key, AES.MODE_CBC, iv)
        private_key_bytes = self.private_key.export_key()
        encrypted_data = cipher.encrypt(pad(private_key_bytes, AES.block_size))
        
        # Store the encrypted data with salt and IV
        self.encrypted_private_key = {
            'salt': base64.b64encode(salt).decode('utf-8'),
            'iv': base64.b64encode(iv).decode('utf-8'),
            'encrypted': base64.b64encode(encrypted_data).decode('utf-8')
        }
    
    def decrypt_private_key(self, password: str) -> bool:
        """Decrypt the private key with a password."""
        if not self.encrypted_private_key:
            return False
            
        try:
            # Get the salt and IV
            salt = base64.b64decode(self.encrypted_private_key['salt'])
            iv = base64.b64decode(self.encrypted_private_key['iv'])
            encrypted_data = base64.b64decode(self.encrypted_private_key['encrypted'])
            
            # Generate the key from the password
            key = PBKDF2(password.encode(), salt, dkLen=32, count=1000000)
            
            # Decrypt the private key
            cipher = AES.new(key, AES.MODE_CBC, iv)
            private_key_bytes = unpad(cipher.decrypt(encrypted_data), AES.block_size)
            
            # Import the private key
            self.private_key = RSA.import_key(private_key_bytes)
            return True
        except Exception as e:
            print(f"Error decrypting private key: {e}")
            return False
    
    def sign_transaction(self, transaction: Dict[str, Any], password: Optional[str] = None) -> str:
        """
        Sign a transaction with the private key.
        
        Args:
            transaction: Transaction data to sign
            password: Password to decrypt the private key if it's encrypted
            
        Returns:
            Hex-encoded signature
        """
        # Check if private key is encrypted and password is provided
        if self.encrypted_private_key and password:
            if not self.decrypt_private_key(password):
                raise ValueError("Failed to decrypt private key with provided password")
                
        # Create a string representation of the transaction
        transaction_str = json.dumps(transaction, sort_keys=True)
        
        # Create a hash of the transaction
        transaction_hash = SHA256.new(transaction_str.encode())
        
        # Sign the hash
        signature = pkcs1_15.new(self.private_key).sign(transaction_hash)
        return signature.hex()
    
    def to_dict(self, include_private_key: bool = False) -> Dict[str, Any]:
        """
        Convert wallet to dictionary.
        
        Args:
            include_private_key: Whether to include the private key (dangerous!)
            
        Returns:
            Dictionary representation of the wallet
        """
        result = {
            'address': self.address,
            'public_key': self.public_key.export_key().decode()
        }
        
        # Include encrypted private key if available
        if self.encrypted_private_key:
            result['encrypted_private_key'] = self.encrypted_private_key
        
        # Only include raw private key if explicitly requested (dangerous!)
        if include_private_key and not self.encrypted_private_key:
            result['private_key'] = self.private_key.export_key().decode()
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], password: Optional[str] = None) -> 'Wallet':
        """
        Create a wallet from dictionary data.
        
        Args:
            data: Dictionary containing wallet data
            password: Password to decrypt the private key if it's encrypted
            
        Returns:
            New Wallet instance
        """
        wallet = cls.__new__(cls)
        wallet.address = data['address']
        wallet.public_key = RSA.import_key(data['public_key'])
        
        # Handle encrypted private key
        if 'encrypted_private_key' in data:
            wallet.encrypted_private_key = data['encrypted_private_key']
            if password:
                wallet.decrypt_private_key(password)
            else:
                wallet.private_key = None  # Can't use for signing without password
        # Handle raw private key (legacy support)
        elif 'private_key' in data:
            wallet.private_key = RSA.import_key(data['private_key'])
            # Automatically encrypt if password provided
            if password:
                wallet.encrypt_private_key(password)
        else:
            # Public key only wallet (can't sign)
            wallet.private_key = None
            
        return wallet
    
    @staticmethod
    def verify_signature(public_key_str: str, signature_hex: str, data: Dict[str, Any]) -> bool:
        """
        Verify a signature using a public key.
        
        Args:
            public_key_str: Public key as a string
            signature_hex: Signature as a hex string
            data: Data that was signed
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Create a hash of the data
            data_str = json.dumps(data, sort_keys=True)
            data_hash = SHA256.new(data_str.encode())
            
            # Import the public key
            public_key = RSA.import_key(public_key_str)
            
            # Verify the signature
            pkcs1_15.new(public_key).verify(
                data_hash,
                bytes.fromhex(signature_hex)
            )
            return True
        except Exception as e:
            print(f"Signature verification failed: {e}")
            return False 