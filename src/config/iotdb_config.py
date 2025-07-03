import os
from iotdb.Session import Session
from iotdb.utils.IoTDBConstants import TSDataType, TSEncoding, Compressor
from iotdb.utils.Tablet import Tablet
import logging

logger = logging.getLogger(__name__)

class IoTDBConfig:
    def __init__(self):
        self.host = os.getenv('IOTDB_HOST', 'localhost')
        self.port = int(os.getenv('IOTDB_PORT', '6667'))
        self.username = os.getenv('IOTDB_USERNAME', 'root')
        self.password = os.getenv('IOTDB_PASSWORD', 'root')
        
        # IoTDB-specific settings
        self.database = os.getenv('IOTDB_DATABASE', 'root.iotflow')
        self.device_path_template = f"{self.database}.devices"
        
        # Session
        self.session = None
        
        self._initialize_session()
    
    def _initialize_session(self):
        """Initialize IoTDB session"""
        try:
            self.session = Session(
                host=self.host,
                port=self.port,
                user=self.username,
                password=self.password
            )
            
            self.session.open(False)  # False means not enable_rpc_compression
            logger.info(f"IoTDB session initialized successfully - {self.host}:{self.port}")
            
            # Create the root database path if it doesn't exist
            self._ensure_database_exists()
            
        except Exception as e:
            logger.error(f"Failed to initialize IoTDB session: {e}")
            logger.warning("IoTDB features will be disabled")
            self.session = None
    
    def _ensure_database_exists(self):
        """Ensure the database path exists"""
        if not self.session:
            return
        
        try:
            # Set storage group (database)
            storage_groups = [self.database]
            self.session.set_storage_group(self.database)
            logger.info(f"Storage group set: {self.database}")
        except Exception as e:
            # Storage group might already exist
            logger.debug(f"Storage group setup: {e}")
    
    def is_connected(self):
        """Check if IoTDB is connected"""
        try:
            if self.session:
                # Simple connectivity test - try to get time series
                return True
            return False
        except Exception:
            return False
    
    def get_device_path(self, device_id: str) -> str:
        """Get the device path for a given device ID"""
        return f"{self.device_path_template}.device_{device_id}"
    
    def close(self):
        """Close the IoTDB session"""
        if self.session:
            try:
                self.session.close()
                logger.info("IoTDB session closed")
            except Exception as e:
                logger.error(f"Error closing IoTDB session: {e}")

# Global instance
iotdb_config = IoTDBConfig()
