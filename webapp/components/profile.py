from dash import html, dcc, Output, Input
import dash_bootstrap_components as dbc

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

def stat_slider(val, min, max, marks, label):
    return html.Div(
        [
            html.Label(label),
            dcc.Slider(min, max, value=val, marks=marks, disabled=True, included=False, className='statSlider'),
        ],
        className='mb-3'
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