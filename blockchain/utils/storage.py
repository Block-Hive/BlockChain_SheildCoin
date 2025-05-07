import os
import json
import logging
from typing import Dict, Any, List, Optional
from .database import Database
from ..config import DATA_DIR

logger = logging.getLogger(__name__)

class Storage:
    """
    Storage utility for managing blockchain data persistence.
    Uses PostgreSQL database for storage.
    """
    
    @staticmethod
    def initialize():
        """Initialize storage and create necessary database tables."""
        try:
            # Create data directory if it doesn't exist
            os.makedirs(DATA_DIR, exist_ok=True)
            
            # Initialize database and create tables
            Database.initialize()
            Database.create_tables()
            
            logger.info("Storage initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize storage: {e}")
            raise
    
    @staticmethod
    def save_blockchain(blockchain_data: Dict[str, Any]) -> bool:
        """
        Save blockchain data to the database.
        
        Args:
            blockchain_data: Blockchain data to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Save each block to the database
            for block in blockchain_data.get('chain', []):
                if not Database.save_block(block):
                    return False
            
            logger.info("Blockchain saved successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to save blockchain: {e}")
            return False
    
    @staticmethod
    def load_blockchain() -> Optional[Dict[str, Any]]:
        """
        Load blockchain data from the database.
        
        Returns:
            Optional[Dict[str, Any]]: Blockchain data if found, None otherwise
        """
        try:
            blocks = Database.get_blocks()
            if not blocks:
                return None
            
            return {'chain': blocks}
        except Exception as e:
            logger.error(f"Failed to load blockchain: {e}")
            return None
    
    # Direct database operations are now handled by Database class directly
    # This eliminates redundant pass-through methods 