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

def check_database_content():
    """Check what's actually in the database"""
    
    print("🔍 Checking Database Content...")
    print("=" * 50)
    
    # Get total count
    total_count = LandslideEvent.objects.count()
    print(f"📊 Total landslide records: {total_count}")
    
    # Check years in database
    print("\n📅 Years in database:")
    years = LandslideEvent.objects.exclude(event_date__isnull=True).dates('event_date', 'year')
    year_list = [y.year for y in years]
    print(f"   Years found: {sorted(year_list)}")
    
    # Check recent uploads (last 10 records)
    print("\n📋 Recent records:")
    recent_records = LandslideEvent.objects.order_by('-event_id')[:10]
    for record in recent_records:
        year = record.event_date.year if record.event_date else "N/A"
        print(f"   ID: {record.event_id}, Title: {record.event_title[:50]}..., Year: {year}")
    
    # Check for any records with 2010-2017 dates
    print("\n🔍 Checking for 2010-2017 records:")
    for year in range(2010, 2018):
        count = LandslideEvent.objects.filter(event_date__year=year).count()
        if count > 0:
            print(f"   {year}: {count} records")
        else:
            print(f"   {year}: 0 records")
    
    # Check database table directly
    print("\n🗄️ Direct database query:")
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT EXTRACT(YEAR FROM event_date) AS year, COUNT(*) as count
            FROM disaster_landslide 
            WHERE event_date IS NOT NULL
            GROUP BY year
            ORDER BY year
        """)
        results = cursor.fetchall()
        for year, count in results:
            print(f"   Year {int(year)}: {count} records")

if __name__ == "__main__":
    check_database_content() 