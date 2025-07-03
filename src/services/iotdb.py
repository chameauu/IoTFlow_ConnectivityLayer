from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from src.config.iotdb_config import iotdb_config
from iotdb.utils.IoTDBConstants import TSDataType, TSEncoding, Compressor
from iotdb.utils.Tablet import Tablet
import json
import logging

logger = logging.getLogger(__name__)

class IoTDBService:
    def __init__(self):
        self.session = iotdb_config.session
        self.database = iotdb_config.database
        
    def is_available(self) -> bool:
        """Check if IoTDB service is available"""
        return iotdb_config.is_connected()

    def _get_data_type(self, value: Any) -> TSDataType:
        """Map Python types to IoTDB data types"""
        if isinstance(value, bool):
            return TSDataType.BOOLEAN
        elif isinstance(value, int):
            return TSDataType.INT64
        elif isinstance(value, float):
            return TSDataType.DOUBLE
        elif isinstance(value, str):
            return TSDataType.TEXT
        else:
            # Default to TEXT for complex types (will be JSON serialized)
            return TSDataType.TEXT

    def _prepare_time_series(self, device_path: str, data: Dict[str, Any], metadata: Dict[str, Any] = None):
        """Prepare time series paths and data types for IoTDB"""
        measurements = []
        data_types = []
        values = []
        
        # Process telemetry data
        for field_name, field_value in data.items():
            measurement = f"{device_path}.{field_name}"
            measurements.append(measurement)
            data_types.append(self._get_data_type(field_value))
            
            # Convert complex types to JSON strings
            if isinstance(field_value, (dict, list)):
                values.append(json.dumps(field_value))
            else:
                values.append(field_value)
        
        # Process metadata if provided
        if metadata:
            for meta_key, meta_value in metadata.items():
                measurement = f"{device_path}.meta_{meta_key}"
                measurements.append(measurement)
                data_types.append(self._get_data_type(meta_value))
                
                if isinstance(meta_value, (dict, list)):
                    values.append(json.dumps(meta_value))
                else:
                    values.append(meta_value)
        
        return measurements, data_types, values

    def write_telemetry_data(self, device_id: str, data: Dict[str, Any], 
                           device_type: str = "sensor", metadata: Dict[str, Any] = None,
                           timestamp: Optional[datetime] = None) -> bool:
        """
        Write telemetry data to IoTDB
        """
        logger.debug(f"Writing telemetry data - device_id={device_id}, data={data}, metadata={metadata}")
        
        if not self.is_available():
            logger.warning("IoTDB is not available")
            return False
            
        try:
            if timestamp is None:
                timestamp = datetime.now(timezone.utc)
            
            # Convert to milliseconds (IoTDB default time unit)
            timestamp_ms = int(timestamp.timestamp() * 1000)
            logger.debug(f"Using timestamp: {timestamp} ({timestamp_ms}ms)")
            
            # Get device path
            device_path = iotdb_config.get_device_path(device_id)
            
            # Add device_type to metadata
            if metadata is None:
                metadata = {}
            metadata['device_type'] = device_type
            
            # Prepare time series
            measurements, data_types, values = self._prepare_time_series(device_path, data, metadata)
            
            logger.debug(f"Prepared {len(measurements)} measurements for device {device_id}")
            
            # Create time series if they don't exist
            for i, measurement in enumerate(measurements):
                try:
                    self.session.create_time_series(
                        measurement, 
                        data_types[i], 
                        TSEncoding.PLAIN, 
                        Compressor.SNAPPY
                    )
                    logger.debug(f"Created time series: {measurement}")
                except Exception as e:
                    # Time series might already exist
                    logger.debug(f"Time series creation (may already exist): {measurement} - {e}")
            
            # Insert data
            self.session.insert_str_record(
                device_path,
                timestamp_ms,
                [m.split('.')[-1] for m in measurements],  # Extract measurement names
                [str(v) for v in values]  # Convert all values to strings
            )
            
            logger.info(f"Successfully wrote telemetry data for device {device_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing telemetry data to IoTDB: {str(e)}")
            return False

    def get_device_telemetry(self, device_id: str, start_time: str = None, 
                           end_time: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Query telemetry data from IoTDB
        """
        logger.debug(f"Querying telemetry data - device_id={device_id}, limit={limit}")
        
        if not self.is_available():
            logger.warning("IoTDB is not available")
            return []
        
        try:
            device_path = iotdb_config.get_device_path(device_id)
            
            # Build query
            query = f"SELECT * FROM {device_path}"
            
            # Add time constraints if provided
            where_conditions = []
            if start_time:
                if start_time.startswith('-'):
                    # Relative time (e.g., "-1h", "-30d")
                    # Convert to absolute timestamp
                    now = datetime.now(timezone.utc)
                    if 'h' in start_time:
                        hours = int(start_time.replace('-', '').replace('h', ''))
                        start_timestamp = int((now.timestamp() - hours * 3600) * 1000)
                    elif 'd' in start_time:
                        days = int(start_time.replace('-', '').replace('d', ''))
                        start_timestamp = int((now.timestamp() - days * 24 * 3600) * 1000)
                    else:
                        start_timestamp = int((now.timestamp() - 3600) * 1000)  # Default 1 hour
                    where_conditions.append(f"time >= {start_timestamp}")
                else:
                    # Absolute time
                    start_timestamp = int(datetime.fromisoformat(start_time.replace('Z', '+00:00')).timestamp() * 1000)
                    where_conditions.append(f"time >= {start_timestamp}")
            
            if end_time:
                end_timestamp = int(datetime.fromisoformat(end_time.replace('Z', '+00:00')).timestamp() * 1000)
                where_conditions.append(f"time <= {end_timestamp}")
            
            if where_conditions:
                query += " WHERE " + " AND ".join(where_conditions)
            
            # Add limit
            query += f" ORDER BY time DESC LIMIT {limit}"
            
            logger.debug(f"Executing query: {query}")
            
            # Execute query
            session_data_set = self.session.execute_query_statement(query)
            
            # Process results
            results = []
            column_names = session_data_set.get_column_names()
            
            while session_data_set.has_next():
                record = session_data_set.next()
                
                # Create result record
                result_record = {
                    "timestamp": datetime.fromtimestamp(record.get_timestamp() / 1000, tz=timezone.utc).isoformat(),
                    "device_id": device_id,
                }
                
                # Add field values
                fields = record.get_fields()
                for i, column_name in enumerate(column_names):
                    if column_name != "Time":  # Skip time column as we handle it separately
                        field_name = column_name.split('.')[-1]  # Extract field name from full path
                        field_index = i - 1  # -1 because Time is first column
                        
                        if field_index < len(fields):
                            field_obj = fields[field_index]
                            
                            # Extract the actual value from the Field object
                            if hasattr(field_obj, 'get_value'):
                                field_value = field_obj.get_value()
                            elif hasattr(field_obj, 'value'):
                                field_value = field_obj.value
                            else:
                                field_value = str(field_obj)
                            
                            # Handle bytes values
                            if isinstance(field_value, bytes):
                                try:
                                    field_value = field_value.decode('utf-8')
                                except:
                                    field_value = str(field_value)
                            
                            # Handle NaN and special types
                            if str(type(field_value).__name__) == 'NAType' or field_value is None:
                                field_value = None
                            elif hasattr(field_value, 'is_nan') and field_value.is_nan():
                                field_value = None
                            elif str(field_value) == 'nan':
                                field_value = None
                            
                            # Try to parse JSON for complex types
                            if isinstance(field_value, str):
                                try:
                                    field_value = json.loads(field_value)
                                except:
                                    pass  # Keep as string if not valid JSON
                            
                            result_record[field_name] = field_value
                
                results.append(result_record)
            
            session_data_set.close_operation_handle()
            
            logger.info(f"Retrieved {len(results)} telemetry records for device {device_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error querying telemetry data from IoTDB: {str(e)}")
            return []

    def get_telemetry_count(self, device_id: str, start_time: str = None) -> int:
        """
        Get count of telemetry records for a device
        """
        logger.debug(f"Getting telemetry count - device_id={device_id}")
        
        if not self.is_available():
            logger.warning("IoTDB is not available")
            return 0
        
        try:
            device_path = iotdb_config.get_device_path(device_id)
            
            # Build count query
            query = f"SELECT count(*) FROM {device_path}"
            
            if start_time:
                if start_time.startswith('-'):
                    # Relative time
                    now = datetime.now(timezone.utc)
                    if 'h' in start_time:
                        hours = int(start_time.replace('-', '').replace('h', ''))
                        start_timestamp = int((now.timestamp() - hours * 3600) * 1000)
                    elif 'd' in start_time:
                        days = int(start_time.replace('-', '').replace('d', ''))
                        start_timestamp = int((now.timestamp() - days * 24 * 3600) * 1000)
                    else:
                        start_timestamp = int((now.timestamp() - 3600) * 1000)
                    query += f" WHERE time >= {start_timestamp}"
            
            logger.debug(f"Executing count query: {query}")
            
            # Execute query
            session_data_set = self.session.execute_query_statement(query)
            
            count = 0
            if session_data_set.has_next():
                record = session_data_set.next()
                fields = record.get_fields()
                if fields:
                    field_obj = fields[0]
                    if hasattr(field_obj, 'get_value'):
                        count = field_obj.get_value()
                    elif hasattr(field_obj, 'value'):
                        count = field_obj.value
                    else:
                        count = int(str(field_obj))
            
            session_data_set.close_operation_handle()
            
            logger.debug(f"Telemetry count for device {device_id}: {count}")
            return int(count) if count else 0
            
        except Exception as e:
            logger.error(f"Error getting telemetry count from IoTDB: {str(e)}")
            return 0

    def delete_device_data(self, device_id: str, start_time: str = None, end_time: str = None) -> bool:
        """
        Delete telemetry data for a device
        """
        logger.debug(f"Deleting telemetry data - device_id={device_id}")
        
        if not self.is_available():
            logger.warning("IoTDB is not available")
            return False
        
        try:
            device_path = iotdb_config.get_device_path(device_id)
            
            # Build delete query
            time_conditions = []
            if start_time:
                start_timestamp = int(datetime.fromisoformat(start_time.replace('Z', '+00:00')).timestamp() * 1000)
                time_conditions.append(str(start_timestamp))
            else:
                time_conditions.append("0")  # From beginning
            
            if end_time:
                end_timestamp = int(datetime.fromisoformat(end_time.replace('Z', '+00:00')).timestamp() * 1000)
                time_conditions.append(str(end_timestamp))
            else:
                time_conditions.append(str(int(datetime.now(timezone.utc).timestamp() * 1000)))  # Until now
            
            # Delete data
            self.session.delete_data([f"{device_path}.*"], time_conditions[0], time_conditions[1])
            
            logger.info(f"Successfully deleted telemetry data for device {device_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting telemetry data from IoTDB: {str(e)}")
            return False

    def close(self):
        """Close IoTDB connection"""
        iotdb_config.close()

    def get_device_latest_telemetry(self, device_id: str) -> Dict[str, Any]:
        """
        Get the latest telemetry data for a device
        """
        logger.debug(f"Getting latest telemetry data - device_id={device_id}")
        
        if not self.is_available():
            logger.warning("IoTDB is not available")
            return {}
        
        try:
            device_path = iotdb_config.get_device_path(device_id)
            
            # Query for latest data (limit 1, order by time desc)
            query = f"SELECT * FROM {device_path} ORDER BY time DESC LIMIT 1"
            
            logger.debug(f"Executing latest query: {query}")
            
            # Execute query
            session_data_set = self.session.execute_query_statement(query)
            
            result = {}
            column_names = session_data_set.get_column_names()
            
            if session_data_set.has_next():
                record = session_data_set.next()
                
                # Create result record
                result = {
                    "timestamp": datetime.fromtimestamp(record.get_timestamp() / 1000, tz=timezone.utc).isoformat(),
                    "device_id": device_id,
                }
                
                # Add field values
                fields = record.get_fields()
                for i, column_name in enumerate(column_names):
                    if column_name != "Time":  # Skip time column as we handle it separately
                        field_name = column_name.split('.')[-1]  # Extract field name from full path
                        field_index = i - 1  # -1 because Time is first column
                        
                        if field_index < len(fields):
                            field_obj = fields[field_index]
                            
                            # Extract the actual value from the Field object
                            if hasattr(field_obj, 'get_value'):
                                field_value = field_obj.get_value()
                            elif hasattr(field_obj, 'value'):
                                field_value = field_obj.value
                            else:
                                field_value = str(field_obj)
                            
                            # Handle bytes values
                            if isinstance(field_value, bytes):
                                try:
                                    field_value = field_value.decode('utf-8')
                                except:
                                    field_value = str(field_value)
                            
                            # Handle NaN and special types
                            if str(type(field_value).__name__) == 'NAType' or field_value is None:
                                field_value = None
                            elif hasattr(field_value, 'is_nan') and field_value.is_nan():
                                field_value = None
                            elif str(field_value) == 'nan':
                                field_value = None
                            
                            # Try to parse JSON for complex types
                            if isinstance(field_value, str):
                                try:
                                    field_value = json.loads(field_value)
                                except:
                                    pass  # Keep as string if not valid JSON
                            
                            result[field_name] = field_value
            
            session_data_set.close_operation_handle()
            
            logger.info(f"Retrieved latest telemetry for device {device_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting latest telemetry from IoTDB: {str(e)}")
            return {}
