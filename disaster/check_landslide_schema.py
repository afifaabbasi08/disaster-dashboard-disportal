#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'disaster.settings')
django.setup()

from django.db import connection

print("🔍 Checking Landslide Table Schema...")
print("=" * 50)

cursor = connection.cursor()

# Get table schema
cursor.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns 
    WHERE table_name = 'disaster_landslide'
    ORDER BY ordinal_position
""")

columns = cursor.fetchall()

print("📋 Landslide Table Schema:")
print("-" * 40)
for col in columns:
    print(f"  {col[0]} ({col[1]}) - Nullable: {col[2]}")

print("\n🔍 Checking Primary Key...")
cursor.execute("""
    SELECT column_name 
    FROM information_schema.key_column_usage 
    WHERE table_name = 'disaster_landslide' 
    AND constraint_name LIKE '%_pkey'
""")

pk_columns = cursor.fetchall()
if pk_columns:
    print(f"Primary Key: {pk_columns[0][0]}")
else:
    print("No primary key found")

print("\n📊 Sample Data:")
print("-" * 20)
cursor.execute("SELECT * FROM disaster_landslide LIMIT 3")
sample_data = cursor.fetchall()

if sample_data:
    # Get column names
    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'disaster_landslide' ORDER BY ordinal_position")
    column_names = [col[0] for col in cursor.fetchall()]
    
    for i, row in enumerate(sample_data):
        print(f"Record {i+1}:")
        for j, value in enumerate(row):
            print(f"  {column_names[j]}: {value}")
        print()
else:
    print("No data found in table") 