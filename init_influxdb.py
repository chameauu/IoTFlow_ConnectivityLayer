#!/usr/bin/env python3
"""
InfluxDB initialization script for IoTFlow Connectivity Layer.
Sets up the InfluxDB database, bucket, and initial configuration.
"""

import os
import sys
import requests
import json
from datetime import datetime, timezone
from influxdb_client import InfluxDBClient
from influxdb_client.client.exceptions import InfluxDBError

# Configuration from environment variables
INFLUXDB_URL = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
INFLUXDB_TOKEN = os.getenv('INFLUXDB_TOKEN', 'your-token-here')
INFLUXDB_ORG = os.getenv('INFLUXDB_ORG', 'iotflow')
INFLUXDB_BUCKET = os.getenv('INFLUXDB_BUCKET', 'telemetry')
INFLUXDB_ADMIN_TOKEN = os.getenv('INFLUXDB_ADMIN_TOKEN', 'admin-token')

def wait_for_influxdb(max_retries=30, delay=2):
    """Wait for InfluxDB to be ready"""
    print("⏳ Waiting for InfluxDB to be ready...")
    
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{INFLUXDB_URL}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                if health_data.get("status") == "pass":
                    print("✅ InfluxDB is ready!")
                    return True
            
            print(f"⏳ Attempt {attempt + 1}/{max_retries}: InfluxDB not ready yet...")
            time.sleep(delay)
            
        except Exception as e:
            print(f"⏳ Attempt {attempt + 1}/{max_retries}: {e}")
            time.sleep(delay)
    
    print("❌ InfluxDB failed to become ready")
    return False

def initialize_influxdb():
    """Initialize InfluxDB with organization and bucket"""
    print("🚀 Initializing InfluxDB...")
    
    try:
        # Connect with admin token
        client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_ADMIN_TOKEN,
            org=INFLUXDB_ORG
        )
        
        # Test connection
        health = client.health()
        if health.status != "pass":
            print(f"❌ InfluxDB health check failed: {health.status}")
            return False
        
        print("✅ Connected to InfluxDB successfully")
        
        # Check if organization exists
        orgs_api = client.organizations_api()
        orgs = orgs_api.find_organizations()
        
        org_exists = False
        org_id = None
        for org in orgs.orgs:
            if org.name == INFLUXDB_ORG:
                org_exists = True
                org_id = org.id
                break
        
        if not org_exists:
            print(f"📁 Creating organization: {INFLUXDB_ORG}")
            try:
                new_org = orgs_api.create_organization(name=INFLUXDB_ORG)
                org_id = new_org.id
                print(f"✅ Organization created: {INFLUXDB_ORG}")
            except Exception as e:
                print(f"❌ Failed to create organization: {e}")
                return False
        else:
            print(f"✅ Organization exists: {INFLUXDB_ORG}")
        
        # Check if bucket exists
        buckets_api = client.buckets_api()
        buckets = buckets_api.find_buckets()
        
        bucket_exists = False
        for bucket in buckets.buckets:
            if bucket.name == INFLUXDB_BUCKET and bucket.org_id == org_id:
                bucket_exists = True
                break
        
        if not bucket_exists:
            print(f"🪣 Creating bucket: {INFLUXDB_BUCKET}")
            try:
                from influxdb_client.domain.bucket import Bucket
                from influxdb_client.domain.bucket_retention_rules import BucketRetentionRules
                
                # Create bucket with 30-day retention
                retention_rules = BucketRetentionRules(
                    type="expire",
                    every_seconds=30 * 24 * 3600  # 30 days
                )
                
                bucket = Bucket(
                    name=INFLUXDB_BUCKET,
                    org_id=org_id,
                    retention_rules=[retention_rules]
                )
                
                new_bucket = buckets_api.create_bucket(bucket=bucket)
                print(f"✅ Bucket created: {INFLUXDB_BUCKET}")
            except Exception as e:
                print(f"❌ Failed to create bucket: {e}")
                return False
        else:
            print(f"✅ Bucket exists: {INFLUXDB_BUCKET}")
        
        # Create API token for the application
        print("🔑 Creating API token for IoTFlow application...")
        try:
            tokens_api = client.authorizations_api()
            
            # Check if token already exists
            existing_tokens = tokens_api.find_authorizations()
            token_exists = False
            
            for token in existing_tokens.authorizations:
                if token.description == "IoTFlow Application Token":
                    token_exists = True
                    print("✅ Application token already exists")
                    break
            
            if not token_exists:
                from influxdb_client.domain.authorization import Authorization
                from influxdb_client.domain.permission import Permission
                from influxdb_client.domain.resource import Resource
                
                # Create permissions for the bucket
                bucket_resource = Resource(
                    type="buckets",
                    id=None,
                    name=INFLUXDB_BUCKET,
                    org_id=org_id
                )
                
                read_permission = Permission(action="read", resource=bucket_resource)
                write_permission = Permission(action="write", resource=bucket_resource)
                
                authorization = Authorization(
                    org_id=org_id,
                    permissions=[read_permission, write_permission],
                    description="IoTFlow Application Token"
                )
                
                new_token = tokens_api.create_authorization(authorization)
                print(f"✅ API token created for IoTFlow application")
                print(f"🔑 Token: {new_token.token}")
                print("⚠️ Save this token securely! Update your .env file with INFLUXDB_TOKEN")
        
        except Exception as e:
            print(f"⚠️ Failed to create API token: {e}")
            print("You may need to create the token manually in the InfluxDB UI")
        
        # Test write operation
        print("📊 Testing write operation...")
        try:
            write_api = client.write_api()
            
            from influxdb_client import Point
            test_point = Point("test_measurement") \
                .tag("device_id", "init_test") \
                .field("value", 1.0) \
                .time(datetime.now(timezone.utc))
            
            write_api.write(bucket=INFLUXDB_BUCKET, record=test_point)
            write_api.close()
            
            print("✅ Test write successful")
        except Exception as e:
            print(f"⚠️ Test write failed: {e}")
        
        client.close()
        print("🎉 InfluxDB initialization completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ InfluxDB initialization failed: {e}")
        return False

def create_sample_data():
    """Create sample telemetry data for testing"""
    print("📊 Creating sample telemetry data...")
    
    try:
        client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG
        )
        
        write_api = client.write_api()
        
        from influxdb_client import Point
        import random
        from datetime import timedelta
        
        # Create sample data points
        base_time = datetime.now(timezone.utc)
        points = []
        
        # Sample devices
        devices = ["esp32_001", "esp32_002", "esp32_003"]
        measurements = ["temperature", "humidity", "pressure"]
        
        for i in range(50):  # Create 50 data points
            for device in devices:
                for measurement in measurements:
                    timestamp = base_time - timedelta(minutes=i * 2)
                    
                    if measurement == "temperature":
                        value = random.uniform(18, 30)
                    elif measurement == "humidity":
                        value = random.uniform(30, 80)
                    else:  # pressure
                        value = random.uniform(1000, 1025)
                    
                    point = Point(measurement) \
                        .tag("device_id", device) \
                        .tag("location", f"room_{device[-1]}") \
                        .field("value", value) \
                        .time(timestamp)
                    
                    points.append(point)
        
        # Write points in batches
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            write_api.write(bucket=INFLUXDB_BUCKET, record=batch)
        
        write_api.close()
        client.close()
        
        print(f"✅ Created {len(points)} sample data points")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create sample data: {e}")
        return False

def main():
    """Main initialization function"""
    print("🚀 InfluxDB Initialization Script")
    print("=" * 50)
    
    # Wait for InfluxDB to be ready
    if not wait_for_influxdb():
        return 1
    
    # Initialize InfluxDB
    if not initialize_influxdb():
        return 1
    
    # Create sample data (optional)
    create_sample = input("\n📊 Create sample telemetry data? (y/n): ").lower() == 'y'
    if create_sample:
        create_sample_data()
    
    print("\n" + "=" * 50)
    print("🎉 InfluxDB initialization completed!")
    print("\nNext steps:")
    print("1. Update your .env file with the generated INFLUXDB_TOKEN")
    print("2. Start your IoTFlow application")
    print("3. Begin sending telemetry data")
    print("\nInfluxDB UI: http://localhost:8086")
    
    return 0

if __name__ == "__main__":
    import time
    sys.exit(main())
