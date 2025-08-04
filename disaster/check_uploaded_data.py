#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'disaster.settings')
django.setup()

from disaster_data.models import LandslideEvent
from django.db import connection
from datetime import datetime

print("🔍 Checking Uploaded Data...")
print("=" * 50)

# Get total count
total_count = LandslideEvent.objects.count()
print(f"📊 Total records in disaster_landslide table: {total_count}")

# Get unique years
cursor = connection.cursor()
cursor.execute("""
    SELECT DISTINCT EXTRACT(YEAR FROM event_date) as year
    FROM disaster_landslide 
    WHERE event_date IS NOT NULL
    ORDER BY year
""")
years = [row[0] for row in cursor.fetchall()]

print(f"\n📅 Years in database: {sorted(years)}")

# Get recent uploads (last 10 records)
print(f"\n🆕 Recent uploads (last 10 records):")
print("-" * 40)
recent_records = LandslideEvent.objects.all().order_by('-event_id')[:10]

for i, record in enumerate(recent_records):
    print(f"Record {i+1}:")
    print(f"  ID: {record.event_id}")
    print(f"  Title: {record.event_title}")
    print(f"  Date: {record.event_date}")
    print(f"  Country: {record.country_name}")
    print(f"  Coordinates: {record.latitude}, {record.longitude}")
    print()

# Check for specific years (like 2017 if you mentioned that)
target_years = [2017, 2020, 2021, 2022, 2023]
print("🎯 Checking for specific years:")
print("-" * 30)

for year in target_years:
    year_count = LandslideEvent.objects.filter(event_date__year=year).count()
    print(f"Year {year}: {year_count} records")

# Get year distribution
print(f"\n📈 Year distribution:")
print("-" * 25)
cursor.execute("""
    SELECT EXTRACT(YEAR FROM event_date) as year, COUNT(*) as count
    FROM disaster_landslide 
    WHERE event_date IS NOT NULL
    GROUP BY year
    ORDER BY year DESC
    LIMIT 10
""")

year_distribution = cursor.fetchall()
for year, count in year_distribution:
    print(f"  {int(year)}: {count} records")

print(f"\n✅ Upload verification complete!")
print(f"💡 If you see new records with recent dates, your upload was successful!") 