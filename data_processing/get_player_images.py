import pandas as pd

## loading data
df = pd.read_csv('data/cleaned_final_dataset.csv')

# unique players
unique_players = df['player'].unique()
unique_df = pd.DataFrame(unique_players, columns=['player'])

# create scrape_name
def create_scrape_name(player):
    parts = player.replace('.', '').lower().split()
    if len(parts) == 2:
        first, last = parts
        scrape_name = last[:5] + first[:2] + "01" 
    else:
        scrape_name = parts[0][:5] + "01" 
    return scrape_name

unique_df['scrape_name'] = unique_df['player'].apply(create_scrape_name)

# generate link
def get_image_link(scrape_name):
    link = f"https://www.basketball-reference.com/req/202106291/images/headshots/{scrape_name}.jpg"
    return link
unique_df['player_image_link'] = unique_df['scrape_name'].apply(get_image_link)

unique_df.to_csv('data/player_images.csv')