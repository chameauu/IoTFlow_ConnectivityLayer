#!/usr/bin/env python3
"""
Quick IoTDB Data Checker
Check if data is being stored in IoTDB for a specific device
"""

import subprocess
import sys
import json
import time
from datetime import datetime, timedelta

def run_iotdb_query(query):
    """Run IoTDB query using docker"""
    try:
        # Use docker exec to run IoTDB CLI command
        cmd = [
            'docker', 'compose', 'exec', '-T', 'iotdb',
            '/iotdb/sbin/start-cli.sh', '-h', 'localhost', '-p', '6667', 
            '-u', 'root', '-pw', 'root', '-e', query
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.stdout, result.stderr, result.returncode
        
    except subprocess.TimeoutExpired:
        return "", "Query timeout", 1
    except Exception as e:
        return "", str(e), 1

def check_device_data(device_id):
    """Check for device data in IoTDB"""
    print(f"🔍 Checking IoTDB for device {device_id} data...")
    print("=" * 50)
    
    # Check if timeseries exists
    query1 = f"SHOW TIMESERIES root.iotflow.devices.device_{device_id}.**"
    print(f"📊 Checking timeseries existence...")
    stdout, stderr, rc = run_iotdb_query(query1)
    
    if rc == 0:
        lines = stdout.strip().split('\n')
        timeseries_count = len([line for line in lines if 'root.iotflow.devices' in line])
        if timeseries_count > 0:
            print(f"✅ Found {timeseries_count} timeseries for device {device_id}")
            for line in lines:
                if 'root.iotflow.devices' in line:
                    print(f"   📈 {line.strip()}")
        else:
            print(f"❌ No timeseries found for device {device_id}")
    else:
        print(f"❌ Error checking timeseries: {stderr}")
    
    print()
    
    # Check recent data (last hour)
    query2 = f"SELECT * FROM root.iotflow.devices.device_{device_id}.** WHERE time > now() - 1h"
    print(f"📊 Checking recent data (last hour)...")
    stdout, stderr, rc = run_iotdb_query(query2)
    
    if rc == 0:
        lines = stdout.strip().split('\n')
        data_lines = [line for line in lines if line.strip() and not line.startswith('Time') and not line.startswith('+')]
        
        if data_lines:
            print(f"✅ Found {len(data_lines)} recent data points:")
            for line in data_lines[:10]:  # Show first 10
                print(f"   📊 {line.strip()}")
            if len(data_lines) > 10:
                print(f"   ... and {len(data_lines) - 10} more")
        else:
            print(f"❌ No recent data found for device {device_id}")
    else:
        print(f"❌ Error checking recent data: {stderr}")
    
    print()
    
    # Count total records
    query3 = f"SELECT COUNT(*) FROM root.iotflow.devices.device_{device_id}.**"
    print(f"📊 Counting total records...")
    stdout, stderr, rc = run_iotdb_query(query3)
    
    if rc == 0:
        lines = stdout.strip().split('\n')
        for line in lines:
            if line.strip() and not line.startswith('Time') and not line.startswith('+'):
                print(f"✅ Total records: {line.strip()}")
                break
    else:
        print(f"❌ Error counting records: {stderr}")

def check_iotdb_connection():
    """Check if IoTDB is running and accessible"""
    print("🔍 Checking IoTDB connection...")
    
    # Simple version check
    stdout, stderr, rc = run_iotdb_query("SHOW VERSION")
    
    if rc == 0:
        print("✅ IoTDB is accessible")
        return True
    else:
        print(f"❌ Cannot connect to IoTDB: {stderr}")
        print("💡 Try running: ./docker-manage.sh start")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python check_iotdb_data.py <device_id>")
        print("Example: python check_iotdb_data.py 1")
        sys.exit(1)
    
    try:
        device_id = int(sys.argv[1])
    except ValueError:
        print("❌ Device ID must be a number")
        sys.exit(1)
    
    print(f"🚀 IoTDB Data Checker for Device {device_id}")
    print(f"🕒 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Check connection first
    if not check_iotdb_connection():
        sys.exit(1)
    
    print()
    check_device_data(device_id)

if __name__ == "__main__":
    main()
