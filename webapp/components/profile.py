from dash import html, dcc, Output, Input
import dash_bootstrap_components as dbc
import dash_cytoscape as cyto
import pandas as pd

# Basic filters

def player_selector(df):
    return dbc.Card(
        [
            dbc.CardBody(
                style={
                    'display': 'flex',
                    'justify-content': 'center',
                    'align-items': 'center',
                    'padding': '0'
                },
                id="player-img-container"
            ),
            dbc.CardFooter(
                [
                    dcc.Dropdown(
                        id='crossfilter-player',
                        options=[{'label': 'All Players', 'value': 'all_values'}] +
                                [{'label': player, 'value': player} for player in df['player'].unique()],
                        value='all_values'
                    ),  
                ]
            )
        ],
        style={
            'width': '100%',
            'height': '275px',
        }
    )

def team_selector(df):
    return dbc.Card(
        [
            dbc.CardBody(
                style={
                    'display': 'flex',
                    'justify-content': 'center',
                    'align-items': 'center',
                },
                id="team-img-container"
            ),
            dbc.CardFooter(
                [
                    dcc.Dropdown(
                        id='crossfilter-team',
                        options=[{'label': 'All Teams', 'value': 'all_values'}] +
                                [{'label': team, 'value': team} for team in df['team'].unique()],
                        value='all_values'
                    ), 
                ]
            )
        ],
        style={
            'width': '100%',
            'height': '181px',
            'margin-bottom': '24px'
        }
    )

def year_selector(df):
    return dbc.Card(
        [
            dbc.CardBody(
                dcc.Dropdown(
                    id='crossfilter-year',
                    options=[{'label': 'All Years', 'value': 'all_values'}] +
                            [{'label': year, 'value': year} for year in df['date'].unique()],
                    value='all_values'
                ),
            )
        ],
        style={
            'width': '100%',
            'height': '70px',
            'background-color': 'rgba(33, 37, 41, 0.03)'
        }
    )

def create_filter_callbacks(dash_app, player_images, team_images, df):
    @dash_app.callback(
        Output('player-img-container', 'children'),
        Input('crossfilter-player', 'value')
    )
    def update_player_image(selected_player):
        if selected_player == 'all_values':
            return  html.H3("All Players", id="player-card-default-text")

        img_loc = player_images.loc[player_images.player == selected_player, :].player_image_link.values[0]
        return html.Img(src=img_loc, alt=selected_player, height="220")
    
    @dash_app.callback(
        Output('team-img-container', 'children'),
        Input('crossfilter-team', 'value')
    )
    def update_team_image(selected_team):
        if selected_team == 'all_values':
            return  html.H3("All Teams", id="player-card-default-text")

        img_loc = team_images.loc[team_images.team == selected_team, :].logo_link.values[0]
        return html.Img(src=img_loc, alt=selected_team, style={'max-height': '80px'})
    
    # update dropdown options based on the other dropdowns
    @dash_app.callback(
        Output('crossfilter-player', 'options'),
        Input('crossfilter-team', 'value'),
        Input('crossfilter-year', 'value')
    )
    def update_player_options(selected_team, selected_year):
        dff = df.copy()
        if selected_team != 'all_values':
            dff = dff[dff['team'] == selected_team]
        if selected_year != 'all_values':
            dff = dff[dff['date'].str[:4] == selected_year]
        players = [{'label': 'All Players', 'value': 'all_values'}] + \
                [{'label': player, 'value': player} for player in dff['player'].unique()]
        return players

    @dash_app.callback(
        Output('crossfilter-team', 'options'),
        Input('crossfilter-player', 'value'),
        Input('crossfilter-year', 'value')
    )
    def update_team_options(selected_player, selected_year):
        dff = df.copy()
        if selected_player != 'all_values':
            dff = dff[dff['player'] == selected_player]
        if selected_year != 'all_values':
            dff = dff[dff['date'].str[:4] == selected_year]
        teams = [{'label': 'All Teams', 'value': 'all_values'}] + \
                [{'label': team, 'value': team} for team in dff['team'].unique()]
        return teams

    @dash_app.callback(
        Output('crossfilter-year', 'options'),
        Input('crossfilter-player', 'value'),
        Input('crossfilter-team', 'value')
    )
    def update_year_options(selected_player, selected_team):
        dff = df.copy()
        if selected_player != 'all_values':
            dff = dff[dff['player'] == selected_player]
        if selected_team != 'all_values':
            dff = dff[dff['team'] == selected_team]
        years = [{'label': 'All Years', 'value': 'all_values'}] + \
                [{'label': year, 'value': year} for year in dff['date'].str[:4].unique()]
        return years

# Profile stats and clustering
 
def stat_slider(val, min, max, marks, label, id):
    return html.Div(
        [
            dbc.Label(label),
            dcc.Slider(min, max, value=val, marks=marks, disabled=True, included=False, className='statSlider', id=id),
        ],
    )

def similarity_filters():
    return html.Div(
        [
            dbc.Label('Search By:', html_for='similarity-filters'),
            dbc.Checklist(
                options=[
                    {'label': 'Shooting Distance', 'value': 'dist'},
                    {'label': 'Side Preference', 'value': 'side'},
                    {'label': 'Accuracy', 'value': 'acc'},
                    {'label': 'Top Quarter', 'value': 'quart'},
                ],
                id='similarity-filters',
                className='mb-2'
            ),
            dbc.Label('Top Results:'),
            html.Ol([
                html.Li('Placeholder'),
                html.Li('Placeholder'),
                html.Li('Placeholder'),
            ])
        ]
    )

def similiarity_graph():
    return html.Div([
        cyto.Cytoscape(
            id='similarity-graph',
            layout={'name': 'random'},
            style={'width': '100%', 'height': '300px'},
            elements=[
                {'data': {'id': 'one', 'label': 'Selected'}},
                {'data': {'id': 'two', 'label': 'Similar 1'}},
                {'data': {'id': 'three', 'label': 'Similar 2'}},
                {'data': {'id': 'four', 'label': 'Similar 3'}},
                {'data': {'id': 'five', 'label': 'Similar 4'}},
                {'data': {'id': 'six', 'label': 'Similar 5'}},
                {'data': {'source': 'one', 'target': 'two'}},
                {'data': {'source': 'one', 'target': 'three'}},
                {'data': {'source': 'one', 'target': 'four'}},
                {'data': {'source': 'one', 'target': 'five'}},
                {'data': {'source': 'one', 'target': 'six'}},
            ]
        )
    ])

def create_slider_callbacks(dash_app, conn):
    @dash_app.callback(
        [
            Output('profile-slider-placeholder-col', 'className'),
            Output('profile-slider-col', 'className'),
            Output('similarity-filter-col', 'className'),
            Output('similarity-graph-col', 'className'),
            Output('similarity-graph-col', 'children'),
        ],
        [Input('crossfilter-player', 'value')]
    )
    def update_profile_col_visibility(selected_player):
        if selected_player == 'all_values':
            return '', 'd-none', 'd-none', 'd-none', None
        return 'd-none', '', '', '', similiarity_graph()


    @dash_app.callback(
        [
            Output('dist-slider', 'value'), 
            Output('side-slider', 'value'), 
            Output('acc-slider', 'value'), 
            Output('quarter-slider', 'value')
        ],
        [Input('crossfilter-year', 'value'), Input('crossfilter-player', 'value'), Input('crossfilter-team', 'value')]
    )
    def update_profile_sliders(selected_year, selected_player, selected_team):
        if selected_player == 'all_values':
            return None, None, None, None
        
        if selected_team == 'all_values' and selected_year == 'all_values':
            player_profile = pd.read_sql('select * from player_profiles where player = (?)', 
                                         conn, params=(selected_player,))
        elif selected_year == 'all_values':
            player_profile = pd.read_sql('select * from player_profiles_by_team where player = (?) and team = (?)', 
                                         conn, params=(selected_player, selected_team,))
        elif selected_team == 'all_values':
            player_profile = pd.read_sql('select * from player_profiles_by_year where player = (?) and year = (?)', 
                                         conn, params=(selected_player, selected_year,))
        else:
            player_profile = pd.read_sql('select * from player_profiles_by_year where player = (?) and team = (?) and year = (?)', 
                                         conn, params=(selected_player, selected_team, selected_year,))
            
        avg_dist = min(player_profile.avg_distance.item(), 21)
        avg_side = max(min((50 - player_profile.avg_shotX.item()), 35), 15)
        acc = player_profile.accuracy.item()
        top_qtr = player_profile.top_quarter.item()

        return avg_dist, avg_side, acc, top_qtr