#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'disaster.settings')
django.setup()

from disaster_data.models import UploadedDataset, LocationPoint

print("=== Testing Save Table Functionality ===")
print()

# Check if models exist
print("📊 UploadedDataset count:", UploadedDataset.objects.count())
print("📍 LocationPoint count:", LocationPoint.objects.count())

if UploadedDataset.objects.count() > 0:
    print("\n📋 Existing datasets:")
    for dataset in UploadedDataset.objects.all():
        print(f"  - {dataset.name} ({dataset.category}) - {dataset.upload_date}")
else:
    print("\n❌ No datasets found")

print("\n=== End of Test ===") 