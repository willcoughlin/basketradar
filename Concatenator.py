import pandas as pd
import glob

# List all CSV files in the directory
csv_files = glob.glob('200011*.csv')
for file in csv_files:
    print(file)

# Initialize an empty list to hold dataframes
dfs = []

# Loop through each CSV file and append to list
for file in csv_files:
    df = pd.read_csv(file)
    dfs.append(df)

# Concatenate all dataframes
stacked_df = pd.concat(dfs, ignore_index=True)

# Save the stacked dataframe to a new CSV file
stacked_df.to_csv('nov2k.csv', index=False)
