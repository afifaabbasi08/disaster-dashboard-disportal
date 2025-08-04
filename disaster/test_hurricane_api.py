#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'disaster.settings')
django.setup()

from disaster_data.models import HurricaneData
from disaster_data.views import hurricane_data_api
from django.test import RequestFactory
import json

print("🔍 Testing Hurricane API...")
print("=" * 50)

# Test the API function directly
factory = RequestFactory()
request = factory.get('/api/hurricanes/')

try:
    response = hurricane_data_api(request)
    print(f"Response status: {response.status_code}")
    print(f"Response content: {response.content[:500]}...")  # First 500 chars
    
    # Try to parse as JSON
    try:
        data = json.loads(response.content)
        print(f"Data type: {type(data)}")
        print(f"Data length: {len(data) if isinstance(data, list) else 'Not a list'}")
        
        if isinstance(data, list) and len(data) > 0:
            print(f"First record: {data[0]}")
        else:
            print("No data or empty response")
            
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Raw response: {response.content}")
        
except Exception as e:
    print(f"API error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("Database check:")
print(f"Total hurricane records: {HurricaneData.objects.count()}")

if HurricaneData.objects.count() > 0:
    sample = HurricaneData.objects.first()
    print(f"Sample record fields: {[f.name for f in HurricaneData._meta.fields]}")
    print(f"Sample record: {sample.__dict__}") 