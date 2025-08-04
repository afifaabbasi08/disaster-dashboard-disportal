#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'disaster.settings')
django.setup()

from django.db import connection
from datetime import datetime

def check_years_in_database():
    """Check what years are actually in the database"""
    
    print("🔍 Checking Years in Database...")
    print("=" * 50)
    
    with connection.cursor() as cursor:
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM disaster_landslide")
        total_count = cursor.fetchone()[0]
        print(f"📊 Total records: {total_count}")
        
        # Get years with counts
        cursor.execute("""
            SELECT EXTRACT(YEAR FROM event_date) as year, COUNT(*) as count
            FROM disaster_landslide 
            WHERE event_date IS NOT NULL
            GROUP BY EXTRACT(YEAR FROM event_date)
            ORDER BY year
        """)
        year_counts = cursor.fetchall()
        
        print(f"📅 Years found: {len(year_counts)}")
        for year, count in year_counts:
            print(f"   {int(year)}: {count} records")
        
        # Check for records with NULL dates
        cursor.execute("SELECT COUNT(*) FROM disaster_landslide WHERE event_date IS NULL")
        null_dates = cursor.fetchone()[0]
        print(f"⚠️  Records with NULL dates: {null_dates}")
        
        # Check recent uploads (last 100 records)
        cursor.execute("""
            SELECT event_id, event_title, event_date, latitude, longitude
            FROM disaster_landslide 
            ORDER BY event_id DESC 
            LIMIT 10
        """)
        recent_records = cursor.fetchall()
        
        print(f"\n🆕 Recent records:")
        for record in recent_records:
            event_id, title, date, lat, lng = record
            year = date.year if date else "NULL"
            print(f"   ID {event_id}: {title} ({year}) at ({lat}, {lng})")

if __name__ == "__main__":
    check_years_in_database() 