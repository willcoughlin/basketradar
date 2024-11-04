from dash import Dash, html
import dash_bootstrap_components as dbc
import pandas as pd
import components.plots as plots
import components.profile as profile
from components.page import navbar
import sqlite3
import os
import requests

dash_app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, './assets/custom.css'],  suppress_callback_exceptions=True)
app = dash_app.server

df = pd.read_csv('https://basketradarstorage.blob.core.windows.net/cleandata/nov2k_clean_with_zones.csv')
# df = pd.read_csv('https://basketradarstorage.blob.core.windows.net/cleandata/cleaned_final_dataset.csv')

player_images = pd.read_csv('https://basketradarstorage.blob.core.windows.net/cleandata/player_images.csv')
team_images = pd.read_csv('https://basketradarstorage.blob.core.windows.net/cleandata/team_images.csv')

sqlite_file_path = './data/nba_shots.db'
if not os.path.exists(sqlite_file_path):
    print('SQLite database does not exist.')
    os.makedirs('data', exist_ok=True)
    print('Downloading...')
    with requests.get('https://basketradarstorage.blob.core.windows.net/cleandata/nba_shots.db', stream=True) as r:
        r.raise_for_status()
        with open(sqlite_file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                f.write(chunk)
    print('Database downloaded.')

conn = sqlite3.connect(sqlite_file_path, check_same_thread=False)

profile_content = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(profile.player_selector(df), md=2),
                dbc.Col(
                    [
                        dbc.Row([dbc.Col(profile.team_selector(df), md=12)]),
                        dbc.Row([dbc.Col(profile.year_selector(df), md=12)])
                    ],
                    md=2
                ),
                dbc.Col(
                    [
                        dbc.Row([dbc.Col(profile.stat_slider(None, 0, 22, {0: 'Short', 11: 'Medium', 22: 'Long'}, 'Shooting Distance', 'dist-slider'), md=12)]),
                        dbc.Row([dbc.Col(profile.stat_slider(None, 15, 35, {12: 'Left', 25: 'Neutral', 38: 'Right'}, 'Side Preference', 'side-slider'), md=12)]),
                        dbc.Row([dbc.Col(profile.stat_slider(None, 0, 1, {0: '0%', 0.5: '50%', 1: '100%'}, 'Accuracy', 'acc-slider'), md=12)]),
                        dbc.Row([dbc.Col(profile.stat_slider(None, 1, 4, {1: '1st', 2: '2nd', 3: '3rd', 4: '4th'}, 'Top Quarter', 'quarter-slider'), md=12)])
                    ],
                    md=3,
                    id='profile-slider-col',
                    className='hidden'
                ),
                dbc.Col(html.H4('Select a player to view profile'), md=3, id='profile-slider-placeholder-col',
                        style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),
                dbc.Col(
                    [
                        dbc.Row([dbc.Col(html.H5('Similar Players'), md=12)]),
                        dbc.Row([dbc.Col(profile.similarity_filters())])
                    ],
                    md=2,
                    id='similarity-filter-col',
                    className='d-none'
                ),
                dbc.Col([], md=3, id='similarity-graph-col', className='d-none')
            ],
            style={'height': '300px '}
        ),
    ],
    fluid=True,
    class_name="mt-2"
)

dashboard_content = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    plots.distance_scatter, 
                    md=6,
                    className="mx-auto" 
                ),
                dbc.Col(
                    plots.moving_average_2pt, 
                    md=6,
                    className="mx-auto"
                ),
            ],
            align="center",
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Row(plots.shot_map, className="mx-auto"),
                        dbc.Row(plots.controls_metric, className="mx-auto"),
                    ],
                    md=6
                ),
                dbc.Col(
                    plots.moving_average_3pt, 
                    md=6,
                    className="mx-auto"
                ),
            ],
            align="center",
        ),
    ],
    fluid=True,
)

dash_app.layout = html.Div(
    [
        navbar,  
        profile_content, 
        dashboard_content
    ]
)

plots.create_plot_callbacks(dash_app, df)
profile.create_filter_callbacks(dash_app, player_images, team_images, df)
profile.create_slider_callbacks(dash_app, conn)

if __name__ == '__main__':
    dash_app.run(debug=True)
