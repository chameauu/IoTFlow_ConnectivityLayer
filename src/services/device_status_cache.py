"""
Device Status Cache Service
Provides caching for device online/offline status and last seen timestamps using Redis
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# Key prefixes for Redis
DEVICE_STATUS_PREFIX = "device:status:"
DEVICE_LASTSEEN_PREFIX = "device:lastseen:"
DEVICE_CACHE_TTL = 60 * 60 * 24  # 24 hours

class DeviceStatusCache:
    """Service for caching device status information in Redis"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.available = redis_client is not None
    
    def set_device_status(self, device_id: int, status: str) -> bool:
        """
        Set the online/offline status of a device
        
        Args:
            device_id: The device ID
            status: 'online' or 'offline'
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.available:
            logger.debug("Redis not available, skipping device status cache")
            return False
            
        try:
            key = f"{DEVICE_STATUS_PREFIX}{device_id}"
            self.redis.set(key, status, ex=DEVICE_CACHE_TTL)
            logger.debug(f"Device {device_id} status cached: {status}")
            return True
        except Exception as e:
            logger.warning(f"Failed to cache device {device_id} status: {str(e)}")
            return False
    
    def get_device_status(self, device_id: int) -> Optional[str]:
        """
        Get the cached online/offline status of a device
        
        Args:
            device_id: The device ID
            
        Returns:
            str: 'online', 'offline', or None if not in cache
        """
        if not self.available:
            return None
            
        try:
            key = f"{DEVICE_STATUS_PREFIX}{device_id}"
            status = self.redis.get(key)
            return status
        except Exception as e:
            logger.warning(f"Failed to get cached status for device {device_id}: {str(e)}")
            return None
    
    def update_device_last_seen(self, device_id: int, timestamp: Optional[datetime] = None) -> bool:
        """
        Update the last seen timestamp for a device
        
        Args:
            device_id: The device ID
            timestamp: The timestamp (defaults to current time)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.available:
            logger.debug("Redis not available, skipping device last seen cache")
            return False
            
        try:
            if timestamp is None:
                timestamp = datetime.now(timezone.utc)
                
            key = f"{DEVICE_LASTSEEN_PREFIX}{device_id}"
            timestamp_str = timestamp.isoformat()
            self.redis.set(key, timestamp_str, ex=DEVICE_CACHE_TTL)
            
            # Also set status to online
            self.set_device_status(device_id, 'online')
            
            logger.debug(f"Device {device_id} last seen cached: {timestamp_str}")
            return True
        except Exception as e:
            logger.warning(f"Failed to cache device {device_id} last seen: {str(e)}")
            return False
    
    def get_device_last_seen(self, device_id: int) -> Optional[datetime]:
        """
        Get the last seen timestamp for a device
        
        Args:
            device_id: The device ID
            
        Returns:
            datetime: The last seen timestamp, or None if not in cache
        """
        if not self.available:
            return None
            
        try:
            key = f"{DEVICE_LASTSEEN_PREFIX}{device_id}"
            timestamp_str = self.redis.get(key)
            if timestamp_str:
                return datetime.fromisoformat(timestamp_str)
            return None
        except Exception as e:
            logger.warning(f"Failed to get cached last seen for device {device_id}: {str(e)}")
            return None
    
    def set_device_offline(self, device_id: int) -> bool:
        """
        Set a device as offline in the cache
        
        Args:
            device_id: The device ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.set_device_status(device_id, 'offline')
    
    def get_all_device_statuses(self, device_ids: List[int]) -> Dict[int, str]:
        """
        Get online/offline status for multiple devices efficiently
        
        Args:
            device_ids: List of device IDs
            
        Returns:
            Dict mapping device_id to status ('online'/'offline'/None)
        """
        if not self.available or not device_ids:
            return {}
            
        try:
            pipeline = self.redis.pipeline()
            
            # Queue all get operations
            for device_id in device_ids:
                key = f"{DEVICE_STATUS_PREFIX}{device_id}"
                pipeline.get(key)
            
            # Execute pipeline and map results
            results = pipeline.execute()
            
            # Map results back to device IDs
            statuses = {}
            for i, device_id in enumerate(device_ids):
                statuses[device_id] = results[i]
                
            return statuses
        except Exception as e:
            logger.warning(f"Failed to get cached statuses for devices: {str(e)}")
            return {}
    
    def get_all_device_last_seen(self, device_ids: List[int]) -> Dict[int, Optional[datetime]]:
        """
        Get last seen timestamps for multiple devices efficiently
        
        Args:
            device_ids: List of device IDs
            
        Returns:
            Dict mapping device_id to last seen timestamp
        """
        if not self.available or not device_ids:
            return {}
            
        try:
            pipeline = self.redis.pipeline()
            
            # Queue all get operations
            for device_id in device_ids:
                key = f"{DEVICE_LASTSEEN_PREFIX}{device_id}"
                pipeline.get(key)
            
            # Execute pipeline and map results
            results = pipeline.execute()
            
            # Map results back to device IDs
            last_seen = {}
            for i, device_id in enumerate(device_ids):
                timestamp_str = results[i]
                if timestamp_str:
                    try:
                        last_seen[device_id] = datetime.fromisoformat(timestamp_str)
                    except ValueError:
                        last_seen[device_id] = None
                else:
                    last_seen[device_id] = None
                    
            return last_seen
        except Exception as e:
            logger.warning(f"Failed to get cached last seen for devices: {str(e)}")
            return {}
    
    def get_device_status_summary(self, device_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """
        Get status summary for multiple devices
        
        Args:
            device_ids: List of device IDs
            
        Returns:
            Dict[int, Dict]: Dictionary with device_id as key and status info as value
        """
        if not self.available:
            return {}
            
        result = {}
        for device_id in device_ids:
            status = self.get_device_status(device_id)
            last_seen = self.get_device_last_seen(device_id)
            
            result[device_id] = {
                'status': status or 'unknown',
                'last_seen': last_seen.isoformat() if last_seen else None
            }
            
        return result
    
    def clear_device_cache(self, device_id: int) -> bool:
        """
        Clear all cached data for a specific device
        
        Args:
            device_id: The device ID to clear
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.available:
            logger.debug("Redis not available, cannot clear device cache")
            return False
            
        try:
            status_key = f"{DEVICE_STATUS_PREFIX}{device_id}"
            lastseen_key = f"{DEVICE_LASTSEEN_PREFIX}{device_id}"
            
            pipeline = self.redis.pipeline()
            pipeline.delete(status_key)
            pipeline.delete(lastseen_key)
            pipeline.execute()
            
            logger.info(f"Cleared cache for device {device_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to clear cache for device {device_id}: {str(e)}")
            return False
    
    def clear_all_device_caches(self) -> bool:
        """
        Clear all device status and last seen caches
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.available:
            logger.debug("Redis not available, cannot clear device caches")
            return False
            
        try:
            # Delete all keys with our prefixes
            status_pattern = f"{DEVICE_STATUS_PREFIX}*"
            lastseen_pattern = f"{DEVICE_LASTSEEN_PREFIX}*"
            
            # Get all matching keys
            status_keys = self.redis.keys(status_pattern)
            lastseen_keys = self.redis.keys(lastseen_pattern)
            
            if status_keys or lastseen_keys:
                pipeline = self.redis.pipeline()
                
                # Add delete commands to pipeline
                if status_keys:
                    pipeline.delete(*status_keys)
                
                if lastseen_keys:
                    pipeline.delete(*lastseen_keys)
                
                # Execute all deletes
                pipeline.execute()
                
                logger.info(f"Cleared all device caches ({len(status_keys)} status, {len(lastseen_keys)} last seen)")
                return True
            else:
                logger.info("No device caches to clear")
                return True
                
        except Exception as e:
            logger.warning(f"Failed to clear all device caches: {str(e)}")
            return False
