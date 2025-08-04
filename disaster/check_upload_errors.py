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
from datetime import datetime

print("🔍 Analyzing Upload Results...")
print("=" * 50)

# Check recent uploads
recent_landslides = LandslideEvent.objects.order_by('-event_id')[:10]
print(f"Recent landslide records: {recent_landslides.count()}")

if recent_landslides.count() > 0:
    print("\nSample of recently uploaded records:")
    print("-" * 40)
    for i, ls in enumerate(recent_landslides):
        print(f"Record {i+1}:")
        print(f"  ID: {ls.event_id}")
        print(f"  Title: {ls.event_title}")
        print(f"  Country: {ls.country_name}")
        print(f"  Coordinates: {ls.latitude}, {ls.longitude}")
        print(f"  Date: {ls.event_date}")
        print()

# Check for common data quality issues
print("Data Quality Analysis:")
print("-" * 30)

# Check for null coordinates
null_coords = LandslideEvent.objects.filter(latitude__isnull=True).count()
print(f"Records with null latitude: {null_coords}")

null_coords = LandslideEvent.objects.filter(longitude__isnull=True).count()
print(f"Records with null longitude: {null_coords}")

# Check for invalid coordinates
invalid_lat = LandslideEvent.objects.filter(latitude__lt=-90).count() + LandslideEvent.objects.filter(latitude__gt=90).count()
invalid_lon = LandslideEvent.objects.filter(longitude__lt=-180).count() + LandslideEvent.objects.filter(longitude__gt=180).count()
print(f"Records with invalid latitude: {invalid_lat}")
print(f"Records with invalid longitude: {invalid_lon}")

# Check for missing dates
null_dates = LandslideEvent.objects.filter(event_date__isnull=True).count()
print(f"Records with null dates: {null_dates}")

# Check for empty required fields
empty_titles = LandslideEvent.objects.filter(event_title__isnull=True).count()
print(f"Records with empty titles: {empty_titles}")

print("\n💡 Tips to improve upload success:")
print("- Ensure all records have valid latitude/longitude coordinates")
print("- Make sure dates are in YYYY-MM-DD format")
print("- Check that required fields (event_title, coordinates) are not empty")
print("- Verify CSV column names match expected format") 