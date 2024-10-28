import pandas as pd 
## loading data
df = pd.read_csv('cleaned_final_dataset.csv')

# unique players
unique_players = df['team'].unique()
unique_df = pd.DataFrame(unique_players, columns=['team'])

def get_link(team):
    link = f"https://cdn.ssref.net/req/202410231/tlogo/bbr/{team}.png"
    return link

unique_df['logo_link'] = unique_df['team'].apply(get_link)

unique_df.to_csv('team_images.csv')