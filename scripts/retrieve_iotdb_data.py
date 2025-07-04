#!/usr/bin/env python3
"""
IoTDB Data Retrieval Tool
Comprehensive tool for querying and retrieving data from IoTDB
"""

import os
import sys
import json
import argparse
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import logging

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.config.iotdb_config import iotdb_config
from src.services.iotdb import IoTDBService


class IoTDBDataRetriever:
    """IoTDB data retrieval and query service"""
    
    def __init__(self):
        self.iotdb_service = IoTDBService()
        self.session = iotdb_config.session
        self.database = iotdb_config.database
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        if not self.iotdb_service.is_available():
            self.logger.error("❌ IoTDB is not available!")
            sys.exit(1)
        
        self.logger.info(f"✅ Connected to IoTDB at {iotdb_config.host}:{iotdb_config.port}")
    
    def list_databases(self) -> List[str]:
        """List all databases (storage groups)"""
        try:
            query = "SHOW DATABASES"
            session_data_set = self.session.execute_query_statement(query)
            
            databases = []
            while session_data_set.has_next():
                record = session_data_set.next()
                # The database name is typically in the first field
                databases.append(record.get_fields()[0].get_string_value())
            
            session_data_set.close_operation_handle()
            return databases
        except Exception as e:
            self.logger.error(f"Error listing databases: {e}")
            return []
    
    def list_devices(self) -> List[str]:
        """List all devices in the IoTFlow database"""
        try:
            query = f"SHOW DEVICES {self.database}.**"
            session_data_set = self.session.execute_query_statement(query)
            
            devices = []
            while session_data_set.has_next():
                record = session_data_set.next()
                device_path = record.get_fields()[0].get_string_value()
                # Extract device ID from path like "root.iotflow.devices.device_123"
                if "devices.device_" in device_path:
                    device_id = device_path.split("devices.device_")[-1]
                    devices.append(device_id)
            
            session_data_set.close_operation_handle()
            return list(set(devices))  # Remove duplicates
        except Exception as e:
            self.logger.error(f"Error listing devices: {e}")
            return []
    
    def list_timeseries(self, device_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all time series, optionally filtered by device"""
        try:
            if device_id:
                pattern = f"{self.database}.devices.device_{device_id}.**"
            else:
                pattern = f"{self.database}.devices.**"
            
            query = f"SHOW TIMESERIES {pattern}"
            session_data_set = self.session.execute_query_statement(query)
            
            timeseries = []
            while session_data_set.has_next():
                record = session_data_set.next()
                fields = record.get_fields()
                
                # Parse timeseries info
                ts_info = {
                    'timeseries': fields[0].get_string_value() if len(fields) > 0 else '',
                    'alias': fields[1].get_string_value() if len(fields) > 1 else '',
                    'database': fields[2].get_string_value() if len(fields) > 2 else '',
                    'datatype': fields[3].get_string_value() if len(fields) > 3 else '',
                    'encoding': fields[4].get_string_value() if len(fields) > 4 else '',
                    'compression': fields[5].get_string_value() if len(fields) > 5 else '',
                    'tags': fields[6].get_string_value() if len(fields) > 6 else '',
                    'attributes': fields[7].get_string_value() if len(fields) > 7 else ''
                }
                timeseries.append(ts_info)
            
            session_data_set.close_operation_handle()
            return timeseries
        except Exception as e:
            self.logger.error(f"Error listing timeseries: {e}")
            return []
    
    def get_latest_data(self, device_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get the latest data points for a device"""
        try:
            device_path = f"{self.database}.devices.device_{device_id}"
            query = f"SELECT * FROM {device_path}.** ORDER BY time DESC LIMIT {limit}"
            
            return self._execute_data_query(query)
        except Exception as e:
            self.logger.error(f"Error getting latest data for device {device_id}: {e}")
            return []
    
    def get_data_by_time_range(
        self, 
        device_id: str, 
        start_time: datetime, 
        end_time: datetime,
        measurements: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get data for a device within a time range"""
        try:
            device_path = f"{self.database}.devices.device_{device_id}"
            
            # Format timestamps for IoTDB (milliseconds since epoch)
            start_ms = int(start_time.timestamp() * 1000)
            end_ms = int(end_time.timestamp() * 1000)
            
            if measurements:
                measurement_paths = [f"{device_path}.{m}" for m in measurements]
                select_clause = ", ".join(measurement_paths)
            else:
                select_clause = f"{device_path}.**"
            
            query = f"SELECT {select_clause} FROM {device_path} WHERE time >= {start_ms} AND time <= {end_ms} ORDER BY time DESC"
            
            return self._execute_data_query(query)
        except Exception as e:
            self.logger.error(f"Error getting data by time range for device {device_id}: {e}")
            return []
    
    def get_aggregated_data(
        self, 
        device_id: str, 
        measurement: str,
        aggregation: str = "avg",
        interval: str = "1h",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get aggregated data (avg, sum, count, etc.) for a measurement"""
        try:
            device_path = f"{self.database}.devices.device_{device_id}"
            measurement_path = f"{device_path}.{measurement}"
            
            # Default to last 24 hours if no time range specified
            if not start_time:
                start_time = datetime.now(timezone.utc) - timedelta(hours=24)
            if not end_time:
                end_time = datetime.now(timezone.utc)
            
            start_ms = int(start_time.timestamp() * 1000)
            end_ms = int(end_time.timestamp() * 1000)
            
            # Convert interval to milliseconds
            interval_ms = self._parse_interval(interval)
            
            query = f"""
            SELECT {aggregation.upper()}({measurement_path})
            FROM {device_path}
            WHERE time >= {start_ms} AND time <= {end_ms}
            GROUP BY ([{start_ms}, {end_ms}), {interval_ms}ms)
            ORDER BY time DESC
            """
            
            return self._execute_data_query(query)
        except Exception as e:
            self.logger.error(f"Error getting aggregated data: {e}")
            return []
    
    def get_device_statistics(self, device_id: str) -> Dict[str, Any]:
        """Get comprehensive statistics for a device"""
        try:
            device_path = f"{self.database}.devices.device_{device_id}"
            
            # Get count of data points
            count_query = f"SELECT COUNT(*) FROM {device_path}.** WHERE time > 0"
            count_result = self._execute_data_query(count_query)
            
            # Get first and last timestamps
            first_query = f"SELECT * FROM {device_path}.** ORDER BY time ASC LIMIT 1"
            last_query = f"SELECT * FROM {device_path}.** ORDER BY time DESC LIMIT 1"
            
            first_result = self._execute_data_query(first_query)
            last_result = self._execute_data_query(last_query)
            
            # Get timeseries for this device
            timeseries = self.list_timeseries(device_id)
            
            stats = {
                'device_id': device_id,
                'timeseries_count': len(timeseries),
                'timeseries': [ts['timeseries'].split('.')[-1] for ts in timeseries],
                'data_point_count': count_result[0].get('count', 0) if count_result else 0,
                'first_timestamp': first_result[0].get('timestamp') if first_result else None,
                'last_timestamp': last_result[0].get('timestamp') if last_result else None,
                'duration_hours': 0
            }
            
            # Calculate duration
            if stats['first_timestamp'] and stats['last_timestamp']:
                first_dt = datetime.fromisoformat(stats['first_timestamp'].replace('Z', '+00:00'))
                last_dt = datetime.fromisoformat(stats['last_timestamp'].replace('Z', '+00:00'))
                duration = last_dt - first_dt
                stats['duration_hours'] = round(duration.total_seconds() / 3600, 2)
            
            return stats
        except Exception as e:
            self.logger.error(f"Error getting device statistics: {e}")
            return {}
    
    def _execute_data_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a data query and return results as list of dictionaries"""
        try:
            self.logger.debug(f"Executing query: {query}")
            session_data_set = self.session.execute_query_statement(query)
            
            results = []
            column_names = session_data_set.get_column_names()
            
            while session_data_set.has_next():
                record = session_data_set.next()
                fields = record.get_fields()
                
                # Create a dictionary for this record
                record_dict = {}
                
                for i, field in enumerate(fields):
                    column_name = column_names[i] if i < len(column_names) else f"col_{i}"
                    
                    # Handle timestamp column
                    if column_name.lower() == 'time':
                        # Convert timestamp from ms to ISO format
                        timestamp_ms = field.get_long_value()
                        timestamp_dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
                        record_dict['timestamp'] = timestamp_dt.isoformat()
                        record_dict['timestamp_ms'] = timestamp_ms
                    else:
                        # Extract measurement name from full path
                        if '.' in column_name:
                            measurement = column_name.split('.')[-1]
                        else:
                            measurement = column_name
                        
                        # Get field value based on type
                        if field.get_data_type().name == 'BOOLEAN':
                            record_dict[measurement] = field.get_bool_value()
                        elif field.get_data_type().name == 'INT32':
                            record_dict[measurement] = field.get_int_value()
                        elif field.get_data_type().name == 'INT64':
                            record_dict[measurement] = field.get_long_value()
                        elif field.get_data_type().name == 'FLOAT':
                            record_dict[measurement] = field.get_float_value()
                        elif field.get_data_type().name == 'DOUBLE':
                            record_dict[measurement] = field.get_double_value()
                        elif field.get_data_type().name == 'TEXT':
                            text_value = field.get_string_value()
                            # Try to parse JSON if it looks like JSON
                            if text_value.startswith(('{', '[')):
                                try:
                                    record_dict[measurement] = json.loads(text_value)
                                except:
                                    record_dict[measurement] = text_value
                            else:
                                record_dict[measurement] = text_value
                        else:
                            record_dict[measurement] = str(field.get_object_value())
                
                results.append(record_dict)
            
            session_data_set.close_operation_handle()
            return results
            
        except Exception as e:
            self.logger.error(f"Error executing query: {e}")
            return []
    
    def _parse_interval(self, interval: str) -> int:
        """Parse interval string to milliseconds"""
        if interval.endswith('s'):
            return int(interval[:-1]) * 1000
        elif interval.endswith('m'):
            return int(interval[:-1]) * 60 * 1000
        elif interval.endswith('h'):
            return int(interval[:-1]) * 60 * 60 * 1000
        elif interval.endswith('d'):
            return int(interval[:-1]) * 24 * 60 * 60 * 1000
        else:
            # Default to seconds
            return int(interval) * 1000
    
    def export_data_to_csv(self, data: List[Dict[str, Any]], filename: str):
        """Export data to CSV file"""
        if not data:
            self.logger.warning("No data to export")
            return
        
        try:
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False)
            self.logger.info(f"✅ Data exported to {filename}")
        except Exception as e:
            self.logger.error(f"Error exporting to CSV: {e}")
    
    def export_data_to_json(self, data: List[Dict[str, Any]], filename: str):
        """Export data to JSON file"""
        if not data:
            self.logger.warning("No data to export")
            return
        
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            self.logger.info(f"✅ Data exported to {filename}")
        except Exception as e:
            self.logger.error(f"Error exporting to JSON: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='IoTDB Data Retrieval Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all devices
  python retrieve_iotdb_data.py --list-devices

  # Get latest data for a device
  python retrieve_iotdb_data.py --device 5 --latest --limit 50

  # Get data from last 2 hours
  python retrieve_iotdb_data.py --device 5 --hours 2

  # Get temperature data from last day
  python retrieve_iotdb_data.py --device 5 --hours 24 --measurements temperature

  # Export data to CSV
  python retrieve_iotdb_data.py --device 5 --hours 6 --export-csv device_5_data.csv

  # Get device statistics
  python retrieve_iotdb_data.py --device 5 --stats
        """
    )
    
    # General options
    parser.add_argument('--list-databases', action='store_true',
                       help='List all databases')
    parser.add_argument('--list-devices', action='store_true',
                       help='List all devices')
    parser.add_argument('--list-timeseries', action='store_true',
                       help='List all timeseries')
    
    # Device-specific options
    parser.add_argument('--device', type=str,
                       help='Device ID to query')
    parser.add_argument('--stats', action='store_true',
                       help='Show device statistics')
    
    # Data retrieval options
    parser.add_argument('--latest', action='store_true',
                       help='Get latest data points')
    parser.add_argument('--limit', type=int, default=100,
                       help='Limit number of results (default: 100)')
    parser.add_argument('--hours', type=int,
                       help='Get data from last N hours')
    parser.add_argument('--days', type=int,
                       help='Get data from last N days')
    parser.add_argument('--measurements', nargs='+',
                       help='Specific measurements to retrieve')
    
    # Aggregation options
    parser.add_argument('--aggregate', choices=['avg', 'sum', 'count', 'min', 'max'],
                       help='Aggregate function')
    parser.add_argument('--interval', default='1h',
                       help='Aggregation interval (e.g., 1h, 30m, 1d)')
    
    # Export options
    parser.add_argument('--export-csv', type=str,
                       help='Export results to CSV file')
    parser.add_argument('--export-json', type=str,
                       help='Export results to JSON file')
    
    # Output options
    parser.add_argument('--format', choices=['table', 'json', 'csv'], default='table',
                       help='Output format (default: table)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create retriever
    retriever = IoTDBDataRetriever()
    
    # Handle list commands
    if args.list_databases:
        databases = retriever.list_databases()
        print("📊 Databases:")
        for db in databases:
            print(f"  - {db}")
        return
    
    if args.list_devices:
        devices = retriever.list_devices()
        print("🔌 Devices:")
        for device in devices:
            print(f"  - Device {device}")
        return
    
    if args.list_timeseries:
        timeseries = retriever.list_timeseries(args.device)
        print("📈 Time Series:")
        for ts in timeseries:
            print(f"  - {ts['timeseries']} ({ts['datatype']})")
        return
    
    # Device-specific commands
    if not args.device:
        print("❌ Device ID required for data operations. Use --device <id>")
        return
    
    data = []
    
    if args.stats:
        stats = retriever.get_device_statistics(args.device)
        print(f"📊 Device {args.device} Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        return
    
    # Data retrieval
    if args.latest:
        print(f"📡 Getting latest {args.limit} data points for device {args.device}...")
        data = retriever.get_latest_data(args.device, args.limit)
    
    elif args.hours or args.days:
        hours = args.hours or (args.days * 24)
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)
        
        print(f"📡 Getting data for device {args.device} from last {hours} hours...")
        data = retriever.get_data_by_time_range(
            args.device, start_time, end_time, args.measurements
        )
    
    else:
        print("❌ Specify --latest, --hours, or --days for data retrieval")
        return
    
    # Output results
    if not data:
        print("📭 No data found")
        return
    
    print(f"✅ Retrieved {len(data)} data points")
    
    # Export if requested
    if args.export_csv:
        retriever.export_data_to_csv(data, args.export_csv)
    
    if args.export_json:
        retriever.export_data_to_json(data, args.export_json)
    
    # Display results
    if args.format == 'json':
        print(json.dumps(data, indent=2, default=str))
    elif args.format == 'csv':
        df = pd.DataFrame(data)
        print(df.to_csv(index=False))
    else:  # table format
        if data:
            df = pd.DataFrame(data)
            print("\n📊 Data Preview:")
            print(df.head(20).to_string(index=False))
            if len(data) > 20:
                print(f"\n... and {len(data) - 20} more rows")


if __name__ == "__main__":
    main()
