#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'disaster.settings')
django.setup()

from disaster_data.models import EarthquakeData, HurricaneData
from datetime import datetime

print("🔍 Checking Hurricane Data...")
print("=" * 50)

# Check Hurricane data
hurricane_count = HurricaneData.objects.count()
print(f"📊 Hurricane records: {hurricane_count}")

if hurricane_count > 0:
    sample_hurricanes = HurricaneData.objects.all()[:5]
    print("\nSample hurricane records:")
    print("-" * 30)
    
    for i, hur in enumerate(sample_hurricanes):
        print(f"Record {i+1}:")
        print(f"  SID: {hur.sid}")
        print(f"  Basin: {hur.basin}")
        print(f"  Subbasin: {hur.subbasin}")
        print(f"  ISO Time: {hur.iso_time}")
        print(f"  Nature: {hur.nature}")
        print(f"  Lat: {hur.lat}")
        print(f"  Lon: {hur.lon}")
        print()

    # Check for unique basins
    basins = HurricaneData.objects.values_list('basin', flat=True).distinct()
    print(f"Unique basins: {list(basins)}")
    
    # Check for years
    years = set()
    for hur in HurricaneData.objects.all():
        if hur.iso_time:
            years.add(hur.iso_time.year)
    print(f"Years in data: {sorted(years)}")
    
else:
    print("❌ No hurricane data found!")
    print("💡 You may need to upload hurricane CSV data") 