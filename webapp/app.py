from dash import Dash, html
import dash_bootstrap_components as dbc
import pandas as pd
import components.plots as plots
import components.profile as profile
from components.page import navbar

dash_app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, './assets/custom.css'],  suppress_callback_exceptions=True)
app = dash_app.server

df = pd.read_csv('https://basketradarstorage.blob.core.windows.net/cleandata/nov2k_clean_with_zones.csv')
# df = pd.read_csv('https://basketradarstorage.blob.core.windows.net/cleandata/cleaned_final_dataset.csv')

player_images = pd.read_csv('https://basketradarstorage.blob.core.windows.net/cleandata/player_images.csv')
team_images = pd.read_csv('https://basketradarstorage.blob.core.windows.net/cleandata/team_images.csv')

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
                        dbc.Row([dbc.Col(profile.stat_slider(.5, 0, 1, {0: 'Short', 0.5: 'Medium', 1: 'Long'}, 'Shooting Distance'), md=12)]),
                        dbc.Row([dbc.Col(profile.stat_slider(25, 0, 50, {0: 'Left', 25: 'Neutral', 50: 'Right'}, 'Side Preference'), md=12)]),
                        dbc.Row([dbc.Col(profile.stat_slider(.0, 0, 1, {0: '0%', 0.5: '50%', 1: '100%'}, 'Accuracy'), md=12)]),
                        dbc.Row([dbc.Col(profile.stat_slider(1, 1, 4, {1: '1st', 2: '2nd', 3: '3rd', 4: '4th'}, 'Effective Quarter'), md=12)])
                    ],
                    md=2
                )
            ]
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

if __name__ == '__main__':
    dash_app.run(debug=True)
