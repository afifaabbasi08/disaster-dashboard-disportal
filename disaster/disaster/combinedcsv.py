import os
import pandas as pd

# Folder where your 11 CSVs are
folder_path = r"C:\Users\USER\Downloads\earthquake"

# Columns to keep
columns_to_keep = ['latitude', 'longitude', 'mag', 'place']

# List to collect cleaned DataFrames
df_list = []

# Loop through CSVs
for file in os.listdir(folder_path):
    if file.endswith(".csv"):
        path = os.path.join(folder_path, file)
        try:
            df = pd.read_csv(path, usecols=columns_to_keep)
            df_list.append(df)
            print(f"Processed: {file}")
        except Exception as e:
            print(f"Skipped {file} due to: {e}")

# Merge all into one DataFrame
merged_df = pd.concat(df_list, ignore_index=True)

# Save the combined CSV
output_path = os.path.join(folder_path, "earthquakes_combined_clean.csv")
merged_df.to_csv(output_path, index=False)

print(f"\nMerged file saved to: {output_path}")

