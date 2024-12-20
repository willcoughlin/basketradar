import pandas as pd
from data_cleaning_library import clean_data
import kagglehub
import os
import shutil
import sqlite3

def download_data():
    # Define the directory name for the dataset
    dataset_dir = 'data'
    
    ### checking if dataset exists. if it does, it won't be downloaded again
    if not os.path.isdir(dataset_dir):
        try:
            ## downloading dataset via kaggle api
            path = kagglehub.dataset_download("techbaron13/nba-shots-dataset-2001-present")
            print("Path to dataset files:", path)
            
            ## the dataset will download to a cashe directory. This moves it to the cwd
            current_dir = os.getcwd()
            target_path = os.path.join(current_dir, dataset_dir)
            
            if os.path.isdir(path) and path != target_path:
                shutil.move(path, target_path)
                print(f"Moved dataset folder to: {target_path}")
            else:
                print("Dataset is already in the current working directory.")

        except Exception as e:
            print("Error downloading dataset:", e)
    else:
        print("Dataset already exists in the 'nba' directory.")


def stack_csvs(output_file):
    # Define the input folder as the "nba" directory in the current working directory
    input_folder = os.path.join(os.getcwd(), 'data/nba')
    dataframes = []
    
    # Loop through all files in the input folder
    for file_name in os.listdir(input_folder):
        # Check if the file is a CSV
        year_from_file = int(file_name[:4])
        if file_name.endswith('.csv') and year_from_file > 2013:
            file_path = os.path.join(input_folder, file_name)
            # Read the CSV file and append the DataFrame to the list
            df = pd.read_csv(file_path)
            dataframes.append(df)
            # print(f"Loaded: {file_name}")

    # Concatenate all DataFrames in the list into a single DataFrame
    stacked_df = pd.concat(dataframes, ignore_index=True)

    # Write the concatenated DataFrame to a new CSV file
    stacked_df.to_csv(output_file, index=False)
    print(f"Stacked CSV saved to: {output_file}")

def data_cleaning(path_to_csv):
    instance1 = clean_data(path_to_csv)
    clean_df = instance1.full_clense()

    return clean_df

def retrieve_and_clean_data():
    download_data()  ### downloading
    
    ## Ensure final dataset does not already exist. If it doesn't exist, stack CSVs.
    final_dataset_path = os.path.join(os.getcwd(), 'data/combined_dataset.csv')
    if not os.path.isfile(final_dataset_path):
        stack_csvs('data/combined_dataset.csv')
        
    # data cleaning script - doing the same thing to make sure it doesn't already exist
    cleaned_dataset_path = os.path.join(os.getcwd(), 'data/cleaned_final_dataset.csv')
    if not os.path.isfile(cleaned_dataset_path):
        data_cleaning(final_dataset_path).to_csv('data/cleaned_final_dataset.csv')

    # Load and round data for insertion
    df = pd.read_csv(cleaned_dataset_path)  
    df['shotX'] = df['shotX'].round(1)
    df['shotY'] = df['shotY'].round(1)

    # Check if SQLite database file exists
    db_path = os.path.join(os.getcwd(), 'data/nba_shots.db')
    if not os.path.isfile(db_path):
        ### Only create the database if it doesn't already exist
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create table if it does not exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shots (
                date TEXT,
                year INTEGER,
                game_location TEXT,
                shotX REAL,
                shotY REAL,
                quarter INTEGER,
                player TEXT,
                team TEXT,
                made BOOLEAN,
                distance INTEGER,
                shot_type INTEGER,
                zone INTEGER
            )
        ''')

        # Insert data into the database
        df.to_sql('shots', conn, if_exists='replace', index=False)

        # Create indexes for UI filtering
        cursor.executescript('''
            CREATE INDEX idx_shots_team ON shots(team);
            CREATE INDEX idx_shots_year ON shots(year);
            CREATE INDEX idx_shots_player_year ON shots(player, year);
            CREATE INDEX idx_shots_team_year ON shots(team, year);
            CREATE INDEX idx_shots_player_team_year ON shots(player, team, year);
        ''')

        # Commit changes and close connection
        conn.commit()
        conn.close()

    return df

if __name__ == "__main__":
    df = retrieve_and_clean_data()
    print(df.head())