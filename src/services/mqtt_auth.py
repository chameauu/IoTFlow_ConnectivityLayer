"""
MQTT Authentication Service
Handles server-side device authentication for MQTT connections and message authorization
Note: MQTT broker allows anonymous connections, all authentication happens server-side
"""

import logging
import hashlib
import json
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from ..models import Device, DeviceAuth, db
from ..services.influxdb import InfluxDBService

logger = logging.getLogger(__name__)


class MQTTAuthService:
    """Service for handling server-side MQTT device authentication and authorization"""
    
    def __init__(self, influxdb_service: Optional[InfluxDBService] = None, app=None):
        self.influxdb_service = influxdb_service or InfluxDBService()
        self.authenticated_devices = {}  # Cache for authenticated devices
        self.app = app  # Flask app instance for context
        
    def authenticate_device_by_api_key(self, api_key: str) -> Optional[Device]:
        """
        Authenticate device using API key for server-side validation
        This is called when processing MQTT messages server-side
        """
        if not self.app:
            logger.error("No Flask app instance available for database operations")
            return None
            
        try:
            with self.app.app_context():
                # Find device by API key
                device = Device.query.filter_by(api_key=api_key, status='active').first()
                
                if not device:
                    logger.warning("Device not found or inactive for API key: %s...", api_key[:8])
                    return None
                    
                # Update last seen
                device.update_last_seen()
                
                # Cache authenticated device
                self.authenticated_devices[device.id] = device
                
                logger.info("Device authenticated successfully: %s (ID: %d)", device.name, device.id)
                return device
                
        except Exception as e:
            logger.error("Error authenticating device by API key: %s", e)
            return None
    
    def validate_device_message(self, device_id: int, api_key: str, topic: str) -> Optional[Device]:
        """
        Validate that a device is authorized to publish to a specific topic
        Returns the device if validation passes, None otherwise
        """
        try:
            # First authenticate the device by API key
            device = self.authenticate_device_by_api_key(api_key)
            if not device or device.id != device_id:
                logger.warning("API key validation failed for device_id %d", device_id)
                return None
            
            # Check topic authorization
            if not self.is_device_authorized(device_id, topic):
                logger.warning("Device %d not authorized for topic: %s", device_id, topic)
                return None
                
            return device
            
        except Exception as e:
            logger.error("Error validating device message: %s", e)
            return None
    
    def is_device_authorized(self, device_id: int, topic: str) -> bool:
        """
        Check if device is authorized to publish/subscribe to a topic
        """
        try:
            # Check if device is authenticated and active
            device = self.authenticated_devices.get(device_id)
            if not device:
                device = Device.query.filter_by(id=device_id, status='active').first()
                if not device:
                    return False
                self.authenticated_devices[device_id] = device
            
            # Basic topic authorization rules
            # Devices can publish to their own telemetry topics
            allowed_publish_topics = [
                f"iotflow/devices/{device_id}/telemetry",
                f"iotflow/devices/{device_id}/status",
                f"iotflow/devices/{device_id}/heartbeat"
            ]
            
            # Devices can subscribe to their own command topics
            allowed_subscribe_topics = [
                f"iotflow/devices/{device_id}/commands",
                f"iotflow/devices/{device_id}/config"
            ]
            
            return topic in allowed_publish_topics or topic in allowed_subscribe_topics
            
        except Exception as e:
            logger.error(f"Error checking device authorization: {e}")
            return False
    
    def handle_telemetry_message(self, device_id: int, api_key: str, topic: str, payload: str) -> bool:
        """
        Handle incoming telemetry message from device with server-side authentication
        Store data only in InfluxDB
        """
        if not self.app:
            logger.error("No Flask app instance available for telemetry processing")
            return False
            
        try:
            with self.app.app_context():
                # Validate device and authorization
                device = self.validate_device_message(device_id, api_key, topic)
                if not device:
                    logger.warning("Unauthorized telemetry attempt from device_id %d", device_id)
                    return False
                
                # Parse JSON payload
                try:
                    data = json.loads(payload)
                except json.JSONDecodeError:
                    logger.error("Invalid JSON payload from device %d: %s", device_id, payload)
                    return False
                
                # Extract telemetry data and metadata
                telemetry_data = data.get('data', {})
                metadata = data.get('metadata', {})
                timestamp_str = data.get('timestamp')
                
                if not telemetry_data:
                    logger.warning("Empty telemetry data from device %d", device_id)
                    return False
                
                # Parse timestamp if provided
                timestamp = None
                if timestamp_str:
                    try:
                        if timestamp_str.endswith('Z'):
                            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        else:
                            timestamp = datetime.fromisoformat(timestamp_str)
                    except ValueError:
                        logger.warning("Invalid timestamp format from device %d: %s", device_id, timestamp_str)
                
                # Store in InfluxDB only
                success = self.influxdb_service.write_telemetry_data(
                    device_id=str(device_id),
                    data=telemetry_data,
                    device_type=device.device_type,
                    metadata=metadata,
                    timestamp=timestamp
                )
                
                if success:
                    # Update device last seen
                    device.update_last_seen()
                    logger.info("Telemetry stored in InfluxDB for device %s (ID: %d)", device.name, device_id)
                    return True
                else:
                    logger.error("Failed to store telemetry in InfluxDB for device %d", device_id)
                    return False
                    
        except Exception as e:
            logger.error("Error handling telemetry message: %s", e)
            return False
                
        except Exception as e:
            logger.error(f"Error handling telemetry message: {e}")
            return False
    
    def get_device_credentials(self, device_id: int) -> Optional[Dict[str, str]]:
        """
        Get MQTT credentials for a device
        Returns dict with username (device_id) and password (api_key)
        """
        try:
            device = Device.query.filter_by(id=device_id, status='active').first()
            if device:
                return {
                    'username': str(device.id),
                    'password': device.api_key,
                    'client_id': f"device_{device.id}_{device.name.replace(' ', '_')}"
                }
            return None
        except Exception as e:
            logger.error(f"Error getting device credentials: {e}")
            return None
    
    def revoke_device_access(self, device_id: int):
        """
        Revoke access for a device (remove from authenticated devices cache)
        """
        if device_id in self.authenticated_devices:
            del self.authenticated_devices[device_id]
            logger.info(f"Revoked access for device {device_id}")
    
    def cleanup_inactive_devices(self):
        """
        Clean up authenticated devices cache for inactive devices
        """
        try:
            active_device_ids = set()
            for device_id in list(self.authenticated_devices.keys()):
                device = Device.query.filter_by(id=device_id, status='active').first()
                if device:
                    active_device_ids.add(device_id)
                else:
                    del self.authenticated_devices[device_id]
            
            logger.info(f"Cleaned up inactive devices. Active: {len(active_device_ids)}")
            
        except Exception as e:
            logger.error(f"Error cleaning up inactive devices: {e}")
