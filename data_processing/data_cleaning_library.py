import pandas as pd

class clean_data:
    def __init__(self,path_to_csv:str):
        self.df = pd.read_csv(path_to_csv)

    def assert_columns(self, df):
      """
      asserts dataframe has correct columns
      """
      required_columns = ['match_id','shotX','shotY','quarter','player','team','made','distance','shot_type']

      assert set(required_columns).issubset(df.columns), f"You have missing columns {set(required_columns)-set(df.columns)} is missing!"

    def extract_date(self,match_id):
        """
        extracts MM/DD/YYYY from match_id column
        """
        year = match_id[:4]  # first 4 are year
        month = match_id[4:6]  # next 2 are month
        day = match_id[6:8]  # last 2 are day
        return f"{month}/{day}/{year}"  # formatting


    def get_date_column(self,df):
       """
       create a date column based on match id
       """
       df['date'] = df['match_id'].apply(self.extract_date)

       return df

    def get_year_column(self, df):
       """
       create a year column based on match id
       """
       df['year'] = df['match_id'].apply(lambda id: int(id[:4]))

       return df

    def remove_columns(self,df):
      """
      removes columns that are not needed
      """
      return df[['date','year','match_id','shotX','shotY','quarter','player','team','made','distance','shot_type']]

    def get_location(self,df):
      """
      returns location of game - based on alphabetic characters in match_id
      """
      df = df.copy()
      df.loc[:, 'game_location'] = df['match_id'].str.replace('[^a-zA-Z]', '', regex=True)
      return df[['date','year','game_location','shotX','shotY','quarter','player','team','made','distance','shot_type']]

    def get_quarter(self,df):
      """
      Instead of "1st quarter" - converts quarter column to numeric (i.e. 1)
      """
      df = df.copy()
      df.loc[:, 'quarter'] = df['quarter'].str.replace('[^0-9]', '', regex=True)


      return df

    def shot_type(self,df):
      """
      Instead of "2-pointer" or "3-pointer" - convert shot_type column to 2 or 3 (I double checked that the dataset does not include free throws)
      """
      df = df.copy()
      df.loc[:, 'shot_type'] = df['shot_type'].str.replace('[^0-9]', '', regex=True)

      return df
    
    def get_zone(self,x,y):
      """
      defines the zones - we can change this if need be
      """
      # Three-point zones (beyond a certain range)
      if x <= 10 and y <= 10:
          return 1  # Left Corner 3
      elif x >= 40 and y <= 10:
          return 2  # Right Corner 3
      elif 20 <= x <= 30 and y >= 30:
          return 3  # Top of Arc 3
      elif x < 10 or x > 40:
          return 4  # Deep 3 from the sides
      elif y >= 35:
          return 5  # Deep straight-on 3



      # Two-point zones outside the paint
      if 10 < x < 20 and 10 < y < 25:
          return 6  # Left wing mid-range
      elif 30 < x < 40 and 10 < y < 25:
          return 7  # Right wing mid-range
      elif 20 <= x <= 30 and 20 <= y < 30:
          return 8  # Top of the key mid-range
      elif x < 10 and 10 <= y < 30:
          return 9  # Baseline left mid-range
      elif x > 40 and 10 <= y < 30:
          return 10  # Baseline right mid-range



      # Paint zones
      if 15 <= x <= 35 and 0 <= y <= 10:
          if 20 <= x <= 30:
              return 15  # At the rim (layups)
          return 14  # Restricted area within the paint
      elif 15 <= x <= 35 and 10 < y <= 20:
          return 11  # Paint (lower region)
      elif 15 <= x <= 35 and 20 < y <= 30:
          return 12  # Paint (upper region)
      elif 10 < x < 20 or 30 < x < 40:
          return 13  # Paint edges

      # Dunk zone (within 2 units of center rim)
      if abs(x - 25) <= 2 and abs(y - 5) <= 2:
          return 16  # Dunk zone

      return 0


    def assign_zone(self,df):
      """
      assigns the zones created in "get_zone"
      """
      df['zone'] = df.apply(lambda row: self.get_zone(row['shotX'], row['shotY']), axis=1)
      return df

    def full_clense(self):
      self.assert_columns(self.df)
      df = self.get_date_column(self.df)
      df = self.get_year_column(self.df)
      df = self.remove_columns(df)
      df = self.get_location(df)
      df = self.get_quarter(df)
      df = self.shot_type(df)
      df = self.assign_zone(df)

      return df
    

if __name__ == "__main__":
   ## here's how you would use the library
   import matplotlib.pyplot as plt
   from data_cleaning_library import clean_data ## i know this step is completely pointless in this file, but this section is really meant to be copied into another group member's code
   instance1 = clean_data('nov2k_clean.csv')
   clean_df = instance1.full_clense()
   print(clean_df.head())

   ## sample visual for zones
   plt.figure(figsize=(8, 6))
   scatter = plt.scatter(clean_df['shotX'], clean_df['shotY'], c=clean_df['zone'])
   plt.colorbar(scatter, label='Zone')
   plt.title('NBA Shots with Zone Coloring')
   plt.xlabel('Shot X')
   plt.ylabel('Shot Y')
   plt.show()