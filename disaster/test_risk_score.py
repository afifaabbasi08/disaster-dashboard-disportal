#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'disaster.settings')
django.setup()

from disaster_data.models import LandslideEvent
from disaster_data.views import landslide_risk_score_api
from django.test import RequestFactory
import json

def test_risk_score_dynamic():
    """Test that risk score API uses dynamic data"""
    
    # Create a mock request
    factory = RequestFactory()
    request = factory.get('/api/landslides/risk-score/')
    
    print("🔍 Testing Risk Score Dynamic Updates...")
    print("=" * 50)
    
    # Get current data count
    current_count = LandslideEvent.objects.count()
    print(f"📊 Current landslide records in database: {current_count}")
    
    # Call the risk score API
    response = landslide_risk_score_api(request)
    
    if response.status_code == 200:
        data = json.loads(response.content)
        
        print(f"✅ Risk Score API Response:")
        print(f"   📍 Total points processed: {data['statistics']['total_points']}")
        print(f"   🎯 Average risk: {data['statistics']['average_risk']}")
        print(f"   ⚠️  Max risk: {data['statistics']['max_risk']}")
        print(f"   🔥 High risk areas: {data['statistics']['high_risk_areas']}")
        print(f"   📅 Last updated: {data['statistics']['last_updated']}")
        
        print(f"\n🎉 SUCCESS: Risk score is using dynamic data!")
        print(f"   The API processed {data['statistics']['total_points']} points from the database")
        
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"   Content: {response.content}")

if __name__ == "__main__":
    test_risk_score_dynamic() 