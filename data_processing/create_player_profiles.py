import pandas as pd
import sqlite3

def create_player_profiles(conn, by_team=False, by_year=False):
    sql_query = f"""
        select 
            player,
            {'team,' if by_team else ''}
            {'substr(date,7,4) as year,' if by_year else ''}
            avg(distance) as avg_distance,
            avg(shotX) as avg_shotX,
            avg(made) as accuracy,
            sum(case when made = 1 then 1 else 0 end) as total_makes,
            sum(case when (made = 1 and quarter = 1) then 1 else 0 end) as q1_makes,
            sum(case when (made = 1 and quarter = 2) then 1 else 0 end) as q2_makes,
            sum(case when (made = 1 and quarter = 3) then 1 else 0 end) as q3_makes,
            sum(case when (made = 1 and quarter = 4) then 1 else 0 end) as q4_makes
        from shots
        where trim(player) <> 'made' and trim(player) <> 'missed'
        group by
            {'team,' if by_team else ''}
            {'substr(date,7,4),' if by_year else ''}
            player
    """
    return pd.read_sql(sql_query, conn)

def create_player_profile_tables(cursor):
    cursor.execute(
        """
            CREATE TABLE IF NOT EXISTS player_profiles (
                player TEXT,
                avg_distance REAL,
                avg_shotX REAL,
                accuracy_REAL,
                top_quarter INTEGER,
            )

            CREATE TABLE IF NOT EXISTS player_profiles_by_team (
                player TEXT,
                team TEXT,
                avg_distance REAL,
                avg_shotX REAL,
                accuracy_REAL,
                top_quarter INTEGER,
            )

            CREATE TABLE IF NOT EXISTS player_profiles_by_year (
                player TEXT,
                year TEXT,
                avg_distance REAL,
                avg_shotX REAL,
                accuracy_REAL,
                top_quarter INTEGER,
            )    

            CREATE TABLE IF NOT EXISTS player_profiles_by_team_and_year (
                player TEXT,
                team TEXT,
                year TEXT,
                avg_distance REAL,
                avg_shotX REAL,
                accuracy_REAL,
                top_quarter INTEGER,
            )          
        """
    )

if __name__ == 'main':
    conn = sqlite3.connect('data/nba_shots.db')
    print('Connected to SQLite DB')

    print('Creating profiles at different levels of aggregation...')
    player_profiles = create_player_profiles(conn)
    player_profiles_by_team = create_player_profiles(conn, by_team=True)
    player_profiles_by_year = create_player_profiles(conn, by_year=True)
    player_profiles_by_team_and_year = create_player_profiles(conn, by_team=True, by_year=True)

    def get_mode_quarter_makes(row):
        quarter_makes = [row.q1_makes, row.q2_makes, row.q3_makes, row.q4_makes]
        max_quarter_makes = max(*quarter_makes)
        return quarter_makes.index(max_quarter_makes) + 1
    
    print('Finishing up aggregation...')
    player_profiles['top_quarter'] = player_profiles.apply(get_mode_quarter_makes, axis=1)
    player_profiles_by_team['top_quarter'] = player_profiles_by_team.apply(get_mode_quarter_makes, axis=1)
    player_profiles_by_year['top_quarter'] = player_profiles_by_year.apply(get_mode_quarter_makes, axis=1)
    player_profiles_by_team_and_year['top_quarter'] = player_profiles_by_team_and_year.apply(get_mode_quarter_makes, axis=1)

    print('Writing tables...')
    cursor = conn.cursor()
    create_player_profile_tables(cursor)

    player_profiles.to_sql('player_profiles', conn, if_exists='replace', index=False)
    player_profiles_by_team.to_sql('player_profiles_by_team', conn, if_exists='replace', index=False)
    player_profiles_by_year.to_sql('player_profiles_by_year', conn, if_exists='replace', index=False)
    player_profiles_by_team_and_year.to_sql('player_profiles_by_team_and_year', conn, if_exists='replace', index=False)

    print('Done.')