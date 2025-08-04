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

def check_2017_data():
    """Check how much 2017 data exists"""
    print("=== Checking 2017 Landslide Data ===")
    
    # Count 2017 records
    count_2017 = LandslideEvent.objects.filter(event_date__year=2017).count()
    print(f"Total 2017 records: {count_2017}")
    
    if count_2017 > 0:
        print("\n=== Sample 2017 Records ===")
        for i, landslide in enumerate(LandslideEvent.objects.filter(event_date__year=2017)[:3]):
            print(f"Record {i+1}:")
            print(f"  Event ID: {landslide.event_id}")
            print(f"  Title: {landslide.event_title}")
            print(f"  Date: {landslide.event_date}")
            print(f"  Location: {landslide.country_name}")
            print(f"  Trigger: {landslide.landslide_trigger}")
            print()
    
    return count_2017

def delete_2017_data():
    """Delete all 2017 landslide data"""
    print("=== Deleting 2017 Landslide Data ===")
    
    count_before = LandslideEvent.objects.count()
    count_2017 = LandslideEvent.objects.filter(event_date__year=2017).count()
    
    if count_2017 == 0:
        print("No 2017 data found to delete.")
        return
    
    # Delete 2017 data
    deleted_count = LandslideEvent.objects.filter(event_date__year=2017).delete()[0]
    count_after = LandslideEvent.objects.count()
    
    print(f"Deleted {deleted_count} 2017 records")
    print(f"Total records before: {count_before}")
    print(f"Total records after: {count_after}")
    print(f"Records removed: {count_before - count_after}")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python manage_2017_data.py check    - Check 2017 data")
        print("  python manage_2017_data.py delete   - Delete 2017 data")
        return
    
    command = sys.argv[1]
    
    if command == "check":
        check_2017_data()
    elif command == "delete":
        confirm = input("Are you sure you want to delete all 2017 data? (yes/no): ")
        if confirm.lower() == "yes":
            delete_2017_data()
        else:
            print("Operation cancelled.")
    else:
        print("Unknown command. Use 'check' or 'delete'.")

if __name__ == "__main__":
    main() 