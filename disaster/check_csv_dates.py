#!/usr/bin/env python
import csv
import os
import sys

def check_csv_dates(csv_file_path):
    """Check what date formats are in the CSV file"""
    
    print(f"🔍 Checking CSV file: {csv_file_path}")
    print("=" * 50)
    
    if not os.path.exists(csv_file_path):
        print(f"❌ File not found: {csv_file_path}")
        return
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # Get column names
            fieldnames = reader.fieldnames
            print(f"📋 CSV columns: {fieldnames}")
            
            # Find date column
            date_columns = [col for col in fieldnames if 'date' in col.lower() or 'time' in col.lower()]
            print(f"📅 Date columns found: {date_columns}")
            
            # Check first 10 rows for date formats
            date_samples = []
            for i, row in enumerate(reader):
                if i >= 10:  # Only check first 10 rows
                    break
                    
                for date_col in date_columns:
                    if date_col in row and row[date_col]:
                        date_samples.append((i+2, date_col, row[date_col]))
            
            print(f"\n📅 Date samples from first 10 rows:")
            for row_num, col_name, date_value in date_samples:
                print(f"   Row {row_num}, Column '{col_name}': '{date_value}'")
                
            # Try to parse some dates
            print(f"\n🧪 Testing date parsing:")
            from datetime import datetime
            
            for row_num, col_name, date_value in date_samples[:5]:  # Test first 5
                print(f"\n   Testing: '{date_value}'")
                
                # Try different formats
                formats_to_try = [
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%d',
                    '%m/%d/%Y',
                    '%d/%m/%Y',
                    '%Y/%m/%d',
                    '%m-%d-%Y',
                    '%d-%m-%Y',
                    '%Y/%m/%d %H:%M:%S',
                    '%m/%d/%Y %H:%M:%S',
                    '%d/%m/%Y %H:%M:%S'
                ]
                
                parsed = False
                for fmt in formats_to_try:
                    try:
                        parsed_date = datetime.strptime(date_value, fmt)
                        print(f"     ✅ SUCCESS with format '{fmt}': {parsed_date}")
                        parsed = True
                        break
                    except ValueError:
                        continue
                
                if not parsed:
                    print(f"     ❌ FAILED: Could not parse '{date_value}' with any format")
                    
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")

if __name__ == "__main__":
    # You'll need to provide the path to your CSV file
    csv_path = input("Enter the path to your CSV file: ").strip()
    if csv_path:
        check_csv_dates(csv_path)
    else:
        print("No file path provided") 