"""
InfluxDB client service for IoTFlow Connectivity Layer.
Provides real-time telemetry data storage and retrieval.
"""

import logging
import time
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union
from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.client.write_api import ASYNCHRONOUS
from influxdb_client.client.exceptions import InfluxDBError
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TelemetryPoint:
    """Represents a telemetry data point"""
    measurement: str
    device_id: str
    timestamp: Optional[datetime] = None
    fields: Optional[Dict[str, Union[float, int, str, bool]]] = None
    tags: Optional[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
        if self.fields is None:
            self.fields = {}
        if self.tags is None:
            self.tags = {}


class InfluxDBService:
    """InfluxDB service for handling telemetry data storage and retrieval"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize InfluxDB service
        
        Args:
            config: InfluxDB configuration dictionary
        """
        self.config = config
        self.url = config['url']
        self.token = config['token']
        self.org = config['org']
        self.bucket = config['bucket']
        self.timeout = config.get('timeout', 10000)
        
        self.client = None
        self.write_api = None
        self.query_api = None
        self._connected = False
        
        logger.info(f"Initializing InfluxDB service for {self.url}")
    
    def connect(self) -> bool:
        """
        Connect to InfluxDB
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.client = InfluxDBClient(
                url=self.url,
                token=self.token,
                org=self.org,
                timeout=self.timeout
            )
            
            # Test connection
            health = self.client.health()
            if health.status == "pass":
                # Configure write API with batching
                write_options = WriteOptions(
                    batch_size=self.config.get('batch_size', 5000),
                    flush_interval=self.config.get('flush_interval', 10000),
                    jitter_interval=2000,
                    retry_interval=5000,
                    max_retries=5,
                    max_retry_delay=30000,
                    exponential_base=2
                )
                
                self.write_api = self.client.write_api(write_options=write_options)
                self.query_api = self.client.query_api()
                self._connected = True
                
                logger.info("Successfully connected to InfluxDB")
                return True
            else:
                logger.error(f"InfluxDB health check failed: {health.status}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to InfluxDB: {e}")
            self._connected = False
            return False
    
    def disconnect(self):
        """Disconnect from InfluxDB"""
        try:
            if self.write_api:
                self.write_api.close()
            if self.client:
                self.client.close()
            self._connected = False
            logger.info("Disconnected from InfluxDB")
        except Exception as e:
            logger.error(f"Error disconnecting from InfluxDB: {e}")
    
    def is_connected(self) -> bool:
        """Check if connected to InfluxDB"""
        return self._connected and self.client is not None
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on InfluxDB
        
        Returns:
            dict: Health status information
        """
        try:
            if not self.client:
                return {"status": "disconnected", "message": "No client connection"}
            
            health = self.client.health()
            return {
                "status": health.status,
                "message": health.message if hasattr(health, 'message') else "OK",
                "version": health.version if hasattr(health, 'version') else "Unknown"
            }
        except Exception as e:
            logger.error(f"InfluxDB health check failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def write_telemetry_point(self, telemetry_point: TelemetryPoint) -> bool:
        """
        Write a single telemetry point to InfluxDB
        
        Args:
            telemetry_point: TelemetryPoint object containing the data
            
        Returns:
            bool: True if write successful, False otherwise
        """
        if not self.is_connected():
            logger.error("Not connected to InfluxDB")
            return False
        
        try:
            # Create InfluxDB Point
            point = Point(telemetry_point.measurement)
            
            # Add device_id as tag
            point = point.tag("device_id", telemetry_point.device_id)
            
            # Add additional tags
            for tag_key, tag_value in telemetry_point.tags.items():
                point = point.tag(tag_key, str(tag_value))
            
            # Add fields
            for field_key, field_value in telemetry_point.fields.items():
                point = point.field(field_key, field_value)
            
            # Set timestamp
            point = point.time(telemetry_point.timestamp)
            
            # Write point
            self.write_api.write(bucket=self.bucket, record=point)
            
            logger.debug(f"Written telemetry point for device {telemetry_point.device_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write telemetry point: {e}")
            return False
    
    def write_telemetry_batch(self, telemetry_points: List[TelemetryPoint]) -> bool:
        """
        Write multiple telemetry points to InfluxDB
        
        Args:
            telemetry_points: List of TelemetryPoint objects
            
        Returns:
            bool: True if write successful, False otherwise
        """
        if not self.is_connected():
            logger.error("Not connected to InfluxDB")
            return False
        
        if not telemetry_points:
            return True
        
        try:
            points = []
            for telemetry_point in telemetry_points:
                # Create InfluxDB Point
                point = Point(telemetry_point.measurement)
                
                # Add device_id as tag
                point = point.tag("device_id", telemetry_point.device_id)
                
                # Add additional tags
                for tag_key, tag_value in telemetry_point.tags.items():
                    point = point.tag(tag_key, str(tag_value))
                
                # Add fields
                for field_key, field_value in telemetry_point.fields.items():
                    point = point.field(field_key, field_value)
                
                # Set timestamp
                point = point.time(telemetry_point.timestamp)
                
                points.append(point)
            
            # Write all points
            self.write_api.write(bucket=self.bucket, record=points)
            
            logger.info(f"Written {len(points)} telemetry points to InfluxDB")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write telemetry batch: {e}")
            return False
    
    def write_mqtt_telemetry(self, device_id: str, topic: str, payload: Dict[str, Any]) -> bool:
        """
        Write MQTT telemetry data to InfluxDB
        
        Args:
            device_id: Device identifier
            topic: MQTT topic
            payload: Telemetry payload
            
        Returns:
            bool: True if write successful, False otherwise
        """
        try:
            # Extract measurement from topic (e.g., "telemetry/temperature" -> "temperature")
            topic_parts = topic.split('/')
            measurement = topic_parts[-1] if len(topic_parts) > 1 else "telemetry"
            
            # Parse timestamp if provided, otherwise use current time
            timestamp = None
            if 'timestamp' in payload:
                try:
                    timestamp = datetime.fromisoformat(payload['timestamp'].replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    timestamp = datetime.now(timezone.utc)
            else:
                timestamp = datetime.now(timezone.utc)
            
            # Separate fields and tags
            fields = {}
            tags = {'topic': topic}
            
            for key, value in payload.items():
                if key == 'timestamp':
                    continue
                elif key in ['location', 'type', 'status', 'unit']:
                    # These are typically tags
                    tags[key] = str(value)
                else:
                    # Numeric or boolean values are typically fields
                    if isinstance(value, (int, float, bool)):
                        fields[key] = value
                    elif isinstance(value, str):
                        try:
                            # Try to convert string numbers to numeric
                            if '.' in value:
                                fields[key] = float(value)
                            else:
                                fields[key] = int(value)
                        except ValueError:
                            # Keep as string field
                            fields[key] = value
                    else:
                        # Convert complex types to string
                        fields[key] = str(value)
            
            # Create telemetry point
            telemetry_point = TelemetryPoint(
                measurement=measurement,
                device_id=device_id,
                timestamp=timestamp,
                fields=fields,
                tags=tags
            )
            
            return self.write_telemetry_point(telemetry_point)
            
        except Exception as e:
            logger.error(f"Failed to write MQTT telemetry for device {device_id}: {e}")
            return False
    
    def query_device_data(self, device_id: str, measurement: str = None, 
                         start_time: str = "-1h", stop_time: str = "now()") -> List[Dict[str, Any]]:
        """
        Query telemetry data for a specific device
        
        Args:
            device_id: Device identifier
            measurement: Specific measurement to query (optional)
            start_time: Start time for query (InfluxDB time format)
            stop_time: Stop time for query (InfluxDB time format)
            
        Returns:
            List of telemetry data points
        """
        if not self.is_connected():
            logger.error("Not connected to InfluxDB")
            return []
        
        try:
            # Build query
            query = f'''
            from(bucket: "{self.bucket}")
              |> range(start: {start_time}, stop: {stop_time})
              |> filter(fn: (r) => r["device_id"] == "{device_id}")
            '''
            
            if measurement:
                query += f'  |> filter(fn: (r) => r["_measurement"] == "{measurement}")\n'
            
            query += '  |> sort(columns: ["_time"], desc: false)'
            
            # Execute query
            result = self.query_api.query(query)
            
            # Process results
            data_points = []
            for table in result:
                for record in table.records:
                    data_point = {
                        'time': record.get_time().isoformat(),
                        'measurement': record.get_measurement(),
                        'device_id': record.values.get('device_id'),
                        'field': record.get_field(),
                        'value': record.get_value()
                    }
                    
                    # Add tags
                    for key, value in record.values.items():
                        if key.startswith('_') or key in ['device_id', 'result', 'table']:
                            continue
                        data_point[key] = value
                    
                    data_points.append(data_point)
            
            logger.debug(f"Retrieved {len(data_points)} data points for device {device_id}")
            return data_points
            
        except Exception as e:
            logger.error(f"Failed to query device data: {e}")
            return []
    
    def get_device_latest_data(self, device_id: str, measurement: str = None) -> Dict[str, Any]:
        """
        Get the latest telemetry data for a device
        
        Args:
            device_id: Device identifier
            measurement: Specific measurement to query (optional)
            
        Returns:
            Latest telemetry data point
        """
        if not self.is_connected():
            logger.error("Not connected to InfluxDB")
            return {}
        
        try:
            # Build query for latest data
            query = f'''
            from(bucket: "{self.bucket}")
              |> range(start: -30d)
              |> filter(fn: (r) => r["device_id"] == "{device_id}")
            '''
            
            if measurement:
                query += f'  |> filter(fn: (r) => r["_measurement"] == "{measurement}")\n'
            
            query += '''
              |> sort(columns: ["_time"], desc: true)
              |> limit(n: 1)
            '''
            
            # Execute query
            result = self.query_api.query(query)
            
            # Process result
            for table in result:
                for record in table.records:
                    data_point = {
                        'time': record.get_time().isoformat(),
                        'measurement': record.get_measurement(),
                        'device_id': record.values.get('device_id'),
                        'field': record.get_field(),
                        'value': record.get_value()
                    }
                    
                    # Add tags
                    for key, value in record.values.items():
                        if key.startswith('_') or key in ['device_id', 'result', 'table']:
                            continue
                        data_point[key] = value
                    
                    return data_point
            
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get latest device data: {e}")
            return {}
    
    def delete_device_data(self, device_id: str, start_time: str = "1970-01-01T00:00:00Z", 
                          stop_time: str = "now()") -> bool:
        """
        Delete telemetry data for a specific device
        
        Args:
            device_id: Device identifier
            start_time: Start time for deletion (RFC3339 format)
            stop_time: Stop time for deletion (RFC3339 format)
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        if not self.is_connected():
            logger.error("Not connected to InfluxDB")
            return False
        
        try:
            delete_api = self.client.delete_api()
            
            # Delete data with predicate
            predicate = f'device_id="{device_id}"'
            delete_api.delete(
                start=start_time,
                stop=stop_time,
                predicate=predicate,
                bucket=self.bucket,
                org=self.org
            )
            
            logger.info(f"Deleted telemetry data for device {device_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete device data: {e}")
            return False


# Global InfluxDB service instance
influxdb_service = None


def get_influxdb_service() -> Optional[InfluxDBService]:
    """Get the global InfluxDB service instance"""
    return influxdb_service


def init_influxdb_service(config: Dict[str, Any]) -> InfluxDBService:
    """
    Initialize the global InfluxDB service
    
    Args:
        config: InfluxDB configuration dictionary
        
    Returns:
        InfluxDBService instance
    """
    global influxdb_service
    influxdb_service = InfluxDBService(config)
    return influxdb_service
