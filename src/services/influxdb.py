from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from influxdb_client import Point
from influxdb_client.client.exceptions import InfluxDBError
from src.config.influxdb_config import influx_config
import json

class InfluxDBService:
    def __init__(self):
        self.client = influx_config.client
        self.write_api = influx_config.write_api
        self.query_api = influx_config.query_api
        self.delete_api = influx_config.delete_api
        self.bucket = influx_config.bucket
        self.org = influx_config.org

    def is_available(self) -> bool:
        """Check if InfluxDB service is available"""
        return influx_config.is_connected()

    def write_telemetry_data(self, device_id: str, data: Dict[str, Any], 
                           device_type: str = "sensor", metadata: Dict[str, Any] = None,
                           timestamp: Optional[datetime] = None) -> bool:
        """
        Write telemetry data to InfluxDB
        """
        if not self.is_available():
            print("InfluxDB is not available")
            return False
            
        try:
            if timestamp is None:
                timestamp = datetime.now(timezone.utc)
            
            # Create a point for each telemetry field
            points = []
            
            for field_name, field_value in data.items():
                if isinstance(field_value, (int, float)):
                    # Numeric values go as fields
                    point = Point("telemetry") \
                        .tag("device_id", device_id) \
                        .tag("device_type", device_type) \
                        .field(field_name, field_value) \
                        .time(timestamp)
                    
                    # Add metadata as tags if provided
                    if metadata:
                        for meta_key, meta_value in metadata.items():
                            if isinstance(meta_value, (str, int, float, bool)):
                                point = point.tag(f"meta_{meta_key}", str(meta_value))
                    
                    points.append(point)
                    
                elif isinstance(field_value, str):
                    # String values as tags with a dummy field
                    point = Point("telemetry") \
                        .tag("device_id", device_id) \
                        .tag("device_type", device_type) \
                        .tag(field_name, field_value) \
                        .field(f"{field_name}_indicator", 1) \
                        .time(timestamp)
                    
                    # Add metadata as tags if provided
                    if metadata:
                        for meta_key, meta_value in metadata.items():
                            if isinstance(meta_value, (str, int, float, bool)):
                                point = point.tag(f"meta_{meta_key}", str(meta_value))
                    
                    points.append(point)
                    
                elif isinstance(field_value, bool):
                    # Boolean values as fields (converted to int)
                    point = Point("telemetry") \
                        .tag("device_id", device_id) \
                        .tag("device_type", device_type) \
                        .field(field_name, int(field_value)) \
                        .time(timestamp)
                    
                    # Add metadata as tags if provided
                    if metadata:
                        for meta_key, meta_value in metadata.items():
                            if isinstance(meta_value, (str, int, float, bool)):
                                point = point.tag(f"meta_{meta_key}", str(meta_value))
                    
                    points.append(point)
            
            # Write all points
            if points:
                self.write_api.write(bucket=self.bucket, org=self.org, record=points)
                return True
            else:
                print("No valid data points to write")
                return False
            
        except InfluxDBError as e:
            print(f"InfluxDB write error: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error writing to InfluxDB: {e}")
            return False

    def get_device_telemetry(self, device_id: str, start_time: str = "-1h", 
                           limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Get telemetry data for a specific device
        """
        if not self.is_available():
            return []
            
        try:
            query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: {start_time})
                |> filter(fn: (r) => r["_measurement"] == "telemetry")
                |> filter(fn: (r) => r["device_id"] == "{device_id}")
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                |> limit(n: {limit})
                |> sort(columns: ["_time"], desc: true)
            '''
            
            result = self.query_api.query(org=self.org, query=query)
            
            telemetry_data = []
            for table in result:
                for record in table.records:
                    data_point = {
                        "timestamp": record.get_time().isoformat(),
                        "device_id": record.values.get("device_id"),
                        "device_type": record.values.get("device_type"),
                    }
                    
                    # Add all field values
                    for key, value in record.values.items():
                        if (not key.startswith("_") and 
                            key not in ["device_id", "device_type", "result", "table"] and
                            not key.startswith("meta_") and
                            not key.endswith("_indicator")):
                            data_point[key] = value
                    
                    # Add metadata
                    metadata = {}
                    for key, value in record.values.items():
                        if key.startswith("meta_"):
                            metadata[key[5:]] = value  # Remove 'meta_' prefix
                    
                    if metadata:
                        data_point["metadata"] = metadata
                    
                    telemetry_data.append(data_point)
            
            return telemetry_data
            
        except InfluxDBError as e:
            print(f"InfluxDB query error: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error querying InfluxDB: {e}")
            return []

    def get_device_latest_telemetry(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest telemetry data for a device
        """
        if not self.is_available():
            return None
            
        try:
            query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: -30d)
                |> filter(fn: (r) => r["_measurement"] == "telemetry")
                |> filter(fn: (r) => r["device_id"] == "{device_id}")
                |> last()
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            '''
            
            result = self.query_api.query(org=self.org, query=query)
            
            for table in result:
                for record in table.records:
                    data_point = {
                        "timestamp": record.get_time().isoformat(),
                        "device_id": record.values.get("device_id"),
                        "device_type": record.values.get("device_type"),
                    }
                    
                    # Add all field values
                    for key, value in record.values.items():
                        if (not key.startswith("_") and 
                            key not in ["device_id", "device_type", "result", "table"] and
                            not key.startswith("meta_") and
                            not key.endswith("_indicator")):
                            data_point[key] = value
                    
                    # Add metadata
                    metadata = {}
                    for key, value in record.values.items():
                        if key.startswith("meta_"):
                            metadata[key[5:]] = value  # Remove 'meta_' prefix
                    
                    if metadata:
                        data_point["metadata"] = metadata
                    
                    return data_point
            
            return None
            
        except Exception as e:
            print(f"Error getting latest telemetry: {e}")
            return None

    def get_device_aggregated_data(self, device_id: str, field: str, 
                                 aggregation: str = "mean", window: str = "1h", 
                                 start_time: str = "-24h") -> List[Dict[str, Any]]:
        """
        Get aggregated telemetry data for a device
        """
        if not self.is_available():
            return []
            
        try:
            query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: {start_time})
                |> filter(fn: (r) => r["_measurement"] == "telemetry")
                |> filter(fn: (r) => r["device_id"] == "{device_id}")
                |> filter(fn: (r) => r["_field"] == "{field}")
                |> aggregateWindow(every: {window}, fn: {aggregation}, createEmpty: false)
                |> sort(columns: ["_time"], desc: true)
            '''
            
            result = self.query_api.query(org=self.org, query=query)
            
            aggregated_data = []
            for table in result:
                for record in table.records:
                    data_point = {
                        "timestamp": record.get_time().isoformat(),
                        "device_id": record.values.get("device_id"),
                        "device_type": record.values.get("device_type"),
                        "field": field,
                        "value": record.get_value(),
                        "aggregation": aggregation,
                        "window": window
                    }
                    aggregated_data.append(data_point)
            
            return aggregated_data
            
        except Exception as e:
            print(f"Error getting aggregated data: {e}")
            return []

    def delete_device_data(self, device_id: str, start_time: str, stop_time: str) -> bool:
        """
        Delete telemetry data for a device within a time range
        """
        if not self.is_available():
            return False
            
        try:
            predicate = f'_measurement="telemetry" AND device_id="{device_id}"'
            
            self.delete_api.delete(
                start=start_time,
                stop=stop_time,
                predicate=predicate,
                bucket=self.bucket,
                org=self.org
            )
            return True
            
        except Exception as e:
            print(f"Error deleting device data: {e}")
            return False

    def get_device_count(self) -> int:
        """Get total number of unique devices in InfluxDB"""
        if not self.is_available():
            return 0
            
        try:
            query = f'''
            import "influxdata/influxdb/schema"
            
            schema.tagValues(
                bucket: "{self.bucket}",
                tag: "device_id",
                predicate: (r) => r["_measurement"] == "telemetry",
                start: -30d
            ) |> count()
            '''
            
            result = self.query_api.query(org=self.org, query=query)
            
            for table in result:
                for record in table.records:
                    return record.get_value()
            
            return 0
            
        except Exception as e:
            print(f"Error getting device count: {e}")
            return 0

# Global service instance
influx_service = InfluxDBService()
