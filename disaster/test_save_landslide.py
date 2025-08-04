#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'disaster.settings')
django.setup()

from disaster_data.models import LandslideEvent
from django.db import connection

def test_save_landslide():
    """Test if we can save landslide data to the database"""
    
    print("🧪 Testing Landslide Save...")
    print("=" * 50)
    
    # Check current count
    initial_count = LandslideEvent.objects.count()
    print(f"📊 Initial count: {initial_count}")
    
    # Try to save a test record
    try:
        test_landslide = LandslideEvent(
            event_id=999999,  # Use a high ID to avoid conflicts
            event_title="TEST UPLOAD - 2015",
            event_description="Test record for upload verification",
            location_description="Test Location",
            location_accuracy="",
            landslide_category="Test",
            landslide_trigger="Test",
            landslide_size="Test",
            fatality_count=None,
            injury_count=None,
            event_import_id=999999,
            country_name="Test Country",
            country_code="TC",
            latitude=45.0,
            longitude=-122.0,
            event_date=datetime(2015, 6, 15, 12, 0, 0)  # 2015 date
        )
        
        print(f"🔧 Attempting to save test record...")
        test_landslide.save()
        
        # Check if it was saved
        new_count = LandslideEvent.objects.count()
        print(f"📊 New count: {new_count}")
        
        if new_count > initial_count:
            print("✅ SUCCESS: Test record was saved!")
            
            # Check if we can find it
            saved_record = LandslideEvent.objects.filter(event_id=999999).first()
            if saved_record:
                print(f"✅ Found saved record: {saved_record.event_title} ({saved_record.event_date.year})")
            else:
                print("❌ Saved record not found in query")
                
        else:
            print("❌ FAILED: Count didn't increase")
            
    except Exception as e:
        print(f"❌ ERROR saving test record: {e}")
        print(f"   Error type: {type(e).__name__}")
        
    # Check database directly
    print("\n🗄️ Direct database check:")
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM disaster_landslide")
        db_count = cursor.fetchone()[0]
        print(f"   Direct DB count: {db_count}")
        
        cursor.execute("SELECT MAX(event_id) FROM disaster_landslide")
        max_id = cursor.fetchone()[0]
        print(f"   Max event_id: {max_id}")

if __name__ == "__main__":
    test_save_landslide() 