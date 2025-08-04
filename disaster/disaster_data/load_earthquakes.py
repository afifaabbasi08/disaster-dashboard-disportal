import os
import pandas as pd
from disaster_data.models import Earthquake

folder_path = r"C:\Users\USER\Downloads\earthquake"

for filename in os.listdir(folder_path):
    if filename.endswith(".csv"):
        file_path = os.path.join(folder_path, filename)
        print(f"Processing: {filename}")
        
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            print(f"Failed to read {filename}: {e}")
            continue
        
        for _, row in df.iterrows():
            try:
                Earthquake.objects.create(
                    time=pd.to_datetime(row['time']),
                    latitude=float(row['latitude']),
                    longitude=float(row['longitude']),
                    depth=float(row['depth']),
                    magnitude=float(row['mag']),
                    place=row['place']
                )
            except Exception as e:
                print(f" Skipped row due to error: {e}")

print(" All earthquake CSV files processed successfully!")
