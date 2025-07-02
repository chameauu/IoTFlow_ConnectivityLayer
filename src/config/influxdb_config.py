import os
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

class InfluxDBConfig:
    def __init__(self):
        self.url = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
        self.token = os.getenv('INFLUXDB_TOKEN', 'your-super-secret-token')
        self.org = os.getenv('INFLUXDB_ORG', 'iotflow')
        self.bucket = os.getenv('INFLUXDB_BUCKET', 'telemetry')
        
        # Create client
        self.client = None
        self.write_api = None
        self.query_api = None
        self.delete_api = None
        
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize InfluxDB client and APIs"""
        try:
            self.client = InfluxDBClient(
                url=self.url,
                token=self.token,
                org=self.org
            )
            
            # Create APIs
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.query_api = self.client.query_api()
            self.delete_api = self.client.delete_api()
            
        except Exception as e:
            print(f"Warning: Failed to initialize InfluxDB client: {e}")
            print("InfluxDB features will be disabled")
    
    def is_connected(self):
        """Check if InfluxDB is connected"""
        try:
            if self.client:
                health = self.client.health()
                return health.status == "pass"
            return False
        except Exception:
            return False
    
    def close(self):
        """Close the InfluxDB client"""
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass

# Global instance
influx_config = InfluxDBConfig()
