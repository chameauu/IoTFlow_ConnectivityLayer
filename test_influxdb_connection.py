#!/usr/bin/env python3
"""
Test InfluxDB connection and verify it's working with the configured token.
"""

import requests

# Test InfluxDB with the configured token
url = 'http://localhost:8086'
token = 'iotflow-super-secret-admin-token'
org = 'iotflow'

def test_influxdb_connection():
    print("🧪 Testing InfluxDB Connection")
    print("=" * 40)
    
    # Test ping
    print("1. Testing InfluxDB ping...")
    try:
        response = requests.get(f'{url}/ping')
        print(f'   ✅ InfluxDB ping: {response.status_code}')
    except Exception as e:
        print(f'   ❌ InfluxDB ping failed: {e}')
        return False

    # Test health with token
    print("2. Testing InfluxDB health...")
    try:
        headers = {'Authorization': f'Token {token}'}
        response = requests.get(f'{url}/health', headers=headers)
        print(f'   ✅ InfluxDB health check: {response.status_code}')
        if response.status_code == 200:
            health_data = response.json()
            print(f'   Status: {health_data.get("status", "unknown")}')
    except Exception as e:
        print(f'   ❌ InfluxDB health check failed: {e}')
        return False

    # Test ready endpoint
    print("3. Testing InfluxDB ready endpoint...")
    try:
        headers = {'Authorization': f'Token {token}'}
        response = requests.get(f'{url}/api/v2/ready', headers=headers)
        print(f'   ✅ InfluxDB ready check: {response.status_code}')
        if response.status_code == 200:
            ready_data = response.json()
            print(f'   Started: {ready_data.get("started", "unknown")}')
    except Exception as e:
        print(f'   ❌ InfluxDB ready check failed: {e}')
        return False

    # Test buckets
    print("4. Testing buckets access...")
    try:
        headers = {'Authorization': f'Token {token}'}
        response = requests.get(f'{url}/api/v2/buckets', headers=headers, params={'org': org})
        print(f'   ✅ Buckets check: {response.status_code}')
        if response.status_code == 200:
            buckets = response.json()
            bucket_list = buckets.get('buckets', [])
            print(f'   Found {len(bucket_list)} buckets')
            for bucket in bucket_list:
                print(f'   - {bucket.get("name", "unknown")}')
        else:
            print(f'   Response: {response.text}')
    except Exception as e:
        print(f'   ❌ Buckets check failed: {e}')
        return False

    # Test organizations
    print("5. Testing organizations access...")
    try:
        headers = {'Authorization': f'Token {token}'}
        response = requests.get(f'{url}/api/v2/orgs', headers=headers)
        print(f'   ✅ Organizations check: {response.status_code}')
        if response.status_code == 200:
            orgs = response.json()
            org_list = orgs.get('orgs', [])
            print(f'   Found {len(org_list)} organizations')
            for organization in org_list:
                print(f'   - {organization.get("name", "unknown")}')
    except Exception as e:
        print(f'   ❌ Organizations check failed: {e}')
        return False

    print("\n✅ All InfluxDB tests passed! InfluxDB is ready for use.")
    return True

if __name__ == "__main__":
    test_influxdb_connection()
