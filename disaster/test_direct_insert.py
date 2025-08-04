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

from django.db import connection

def test_direct_insert():
    """Test direct database insertion"""
    
    print("🧪 Testing Direct Database Insert...")
    print("=" * 50)
    
    # Check current count
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM disaster_landslide")
        initial_count = cursor.fetchone()[0]
        print(f"📊 Initial count: {initial_count}")
        
        # Get max event_id to avoid conflicts
        cursor.execute("SELECT MAX(event_id) FROM disaster_landslide")
        max_id = cursor.fetchone()[0] or 0
        print(f"📊 Max event_id: {max_id}")
        
        # Try to insert a test record
        test_id = max_id + 1000  # Use a high ID to avoid conflicts
        test_date = datetime(2015, 6, 15, 12, 0, 0)
        
        try:
            sql = """
            INSERT INTO disaster_landslide (
                event_id, event_title, event_description, location_description,
                location_accuracy, landslide_category, landslide_trigger, landslide_size,
                fatality_count, injury_count, event_import_id, country_name,
                country_code, latitude, longitude, event_date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(sql, (
                test_id, "TEST DIRECT INSERT - 2015", "Test description", "Test location",
                "", "Test", "Test", "Test", None, None, test_id, "Test Country",
                "TC", 45.0, -122.0, test_date
            ))
            
            # Check if it was inserted
            cursor.execute("SELECT COUNT(*) FROM disaster_landslide")
            new_count = cursor.fetchone()[0]
            print(f"📊 New count: {new_count}")
            
            if new_count > initial_count:
                print("✅ SUCCESS: Test record was inserted!")
                
                # Check if we can find it
                cursor.execute("SELECT event_id, event_title, event_date FROM disaster_landslide WHERE event_id = %s", [test_id])
                result = cursor.fetchone()
                if result:
                    print(f"✅ Found inserted record: ID={result[0]}, Title={result[1]}, Date={result[2]}")
                else:
                    print("❌ Inserted record not found in query")
                    
            else:
                print("❌ FAILED: Count didn't increase")
                
        except Exception as e:
            print(f"❌ ERROR inserting test record: {e}")
            print(f"   Error type: {type(e).__name__}")
            
            # Check for specific database errors
            if "duplicate key" in str(e).lower():
                print("   → This is a primary key conflict")
            elif "constraint" in str(e).lower():
                print("   → This is a constraint violation")
            elif "permission" in str(e).lower():
                print("   → This is a permission issue")
        
        # Check table structure
        print("\n🗄️ Table structure:")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'disaster_landslide' 
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        for col in columns:
            print(f"   {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")

if __name__ == "__main__":
    test_direct_insert() 