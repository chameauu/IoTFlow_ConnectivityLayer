#!/usr/bin/env python3
"""
Verify InfluxDB data after telemetry submission
"""

from influxdb_client import InfluxDBClient
from datetime import datetime, timezone, timedelta

# InfluxDB configuration
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "iotflow-super-secret-admin-token"
INFLUXDB_ORG = "iotflow"
INFLUXDB_BUCKET = "telemetry"

def query_influxdb_data():
    """Query recent telemetry data from InfluxDB"""
    print("🔍 Querying InfluxDB for telemetry data...")
    print("=" * 50)
    
    try:
        # Connect to InfluxDB
        client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
        query_api = client.query_api()
        
        # Query recent data
        query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
          |> range(start: -1h)
          |> filter(fn: (r) => r._measurement == "sensor_reading")
          |> sort(columns: ["_time"], desc: true)
          |> limit(n: 10)
        '''
        
        print(f"📊 Executing query: {query.strip()}")
        print()
        
        # Execute query
        result = query_api.query(org=INFLUXDB_ORG, query=query)
        
        data_points = []
        for table in result:
            for record in table.records:
                data_points.append({
                    'time': record.get_time(),
                    'measurement': record.get_measurement(),
                    'field': record.get_field(),
                    'value': record.get_value(),
                    'device_id': record.values.get('device_id'),
                    'device_name': record.values.get('device_name'),
                    'location': record.values.get('location')
                })
        
        if data_points:
            print(f"✅ Found {len(data_points)} data points in InfluxDB:")
            print()
            
            # Group by time for better display
            grouped_by_time = {}
            for point in data_points:
                time_str = point['time'].strftime('%H:%M:%S')
                if time_str not in grouped_by_time:
                    grouped_by_time[time_str] = []
                grouped_by_time[time_str].append(point)
            
            for time_str, points in list(grouped_by_time.items())[:3]:  # Show last 3 timestamps
                print(f"🕐 {time_str}:")
                for point in points:
                    print(f"   {point['field']}: {point['value']} (device: {point['device_name']})")
                print()
        else:
            print("⚠️ No data found in InfluxDB")
            print("   This might mean:")
            print("   1. Telemetry data wasn't written to InfluxDB")
            print("   2. The query time range is too narrow")
            print("   3. The measurement name doesn't match")
        
        # Query all measurements to see what's available
        print("📋 Available measurements in the last hour:")
        measurements_query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
          |> range(start: -1h)
          |> group(columns: ["_measurement"])
          |> distinct(column: "_measurement")
        '''
        
        measurements_result = query_api.query(org=INFLUXDB_ORG, query=measurements_query)
        measurements = []
        for table in measurements_result:
            for record in table.records:
                measurements.append(record.get_value())
        
        if measurements:
            for measurement in measurements:
                print(f"   - {measurement}")
        else:
            print("   No measurements found")
        
        client.close()
        return len(data_points) > 0
        
    except Exception as e:
        print(f"❌ Error querying InfluxDB: {e}")
        return False

if __name__ == "__main__":
    query_influxdb_data()
