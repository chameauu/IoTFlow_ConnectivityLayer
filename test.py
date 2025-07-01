
import requests
import os

# Test InfluxDB with the configured token
url = 'http://localhost:8086'
token = 'iotflow-super-secret-admin-token'
org = 'iotflow'

# Test ping
try:
    response = requests.get(f'{url}/ping')
    print(f'✅ InfluxDB ping: {response.status_code}')
except Exception as e:
    print(f'❌ InfluxDB ping failed: {e}')

# Test with token
try:
    headers = {'Authorization': f'Token {token}'}
    response = requests.get(f'{url}/api/v2/ready', headers=headers)
    print(f'✅ InfluxDB ready check: {response.status_code}')
    if response.status_code == 200:
        print(f'   Response: {response.json()}')
except Exception as e:
    print(f'❌ InfluxDB ready check failed: {e}')

# Test buckets
try:
    headers = {'Authorization': f'Token {token}'}
    response = requests.get(f'{url}/api/v2/buckets', headers=headers, params={'org': org})
    print(f'✅ Buckets check: {response.status_code}')
    if response.status_code == 200:
        buckets = response.json()
        print(f'   Found {len(buckets.get(\"buckets\", []))} buckets')
        for bucket in buckets.get('buckets', []):
            print(f'   - {bucket.get(\"name\", \"unknown\")}')
except Exception as e:
    print(f'❌ Buckets check failed: {e}')
