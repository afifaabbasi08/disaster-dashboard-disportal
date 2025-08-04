#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'disaster.settings')
django.setup()

from disaster_data.models import LandslideEvent, UploadedDataset, LocationPoint

print("=== Quick Database Check ===")
print()

# Check LandslideEvent (main landslide data)
landslide_count = LandslideEvent.objects.count()
print(f"📊 LandslideEvent records: {landslide_count}")

if landslide_count > 0:
    # Check for 2017 data
    data_2017 = LandslideEvent.objects.filter(event_date__year=2017).count()
    print(f"   2017 records: {data_2017}")
    
    if data_2017 > 0:
        print("   ✅ 2017 data found!")
        latest_2017 = LandslideEvent.objects.filter(event_date__year=2017).order_by('-event_date').first()
        print(f"   Latest 2017 record: {latest_2017.event_date} - {latest_2017.event_title}")
    else:
        print("   ❌ No 2017 data found")
    
    # Show latest record
    latest = LandslideEvent.objects.order_by('-event_date').first()
    print(f"   Latest record: {latest.event_date} - {latest.event_title}")
else:
    print("   ❌ No landslide data found")

print()

# Check UploadedDataset (My Uploads)
dataset_count = UploadedDataset.objects.count()
print(f"💾 UploadedDataset records: {dataset_count}")

if dataset_count > 0:
    print("   Saved tables:")
    for dataset in UploadedDataset.objects.all():
        print(f"     - {dataset.name} ({dataset.category}) - {dataset.upload_date}")
else:
    print("   ❌ No uploaded datasets found")

print()

# Check LocationPoint
location_count = LocationPoint.objects.count()
print(f"📍 LocationPoint records: {location_count}")

print("=== End of Check ===") 