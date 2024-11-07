from dash import html, dcc, Output, Input
import dash_bootstrap_components as dbc
import pandas as pd

# Basic filters

def player_selector(conn):
    all_players = [{'label': player, 'value': player} for player in pd.read_sql('select distinct player from player_profiles', conn).player]
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
                        options=[{'label': 'All Players', 'value': 'all_values'}] + all_players,
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

def team_selector(conn):
    all_teams = [{'label': team, 'value': team} for team in pd.read_sql('select distinct team from player_profiles_by_team order by team', conn).team]
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
                        options=[{'label': 'All Teams', 'value': 'all_values'}] + all_teams,
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

def year_selector(conn):
    all_years = [{'label': year, 'value': year} for year in pd.read_sql('select distinct year from player_profiles_by_year order by year desc', conn).year]
    return dbc.Card(
        [
            dbc.CardBody(
                dcc.Dropdown(
                    id='crossfilter-year',
                    options=[{'label': 'All Years', 'value': 'all_values'}] + all_years,
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

def create_filter_callbacks(dash_app, player_images, team_images, conn):
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
        sql_query = f"""
            select distinct player
            from player_profiles_by_team_and_year
            where
                1 = 1
                {'and team = (?)' if selected_team != 'all_values' else ''}
                {'and year = (?)' if selected_year != 'all_values' else ''}
            order by player
        """
        params = []
        if selected_team != 'all_values':
            params = params + [selected_team]
        if selected_year != 'all_values':
            params = params + [selected_year]

        all_players = [{'label': player, 'value': player} for player in pd.read_sql(sql_query, conn, params=params).player]
        players = [{'label': 'All Players', 'value': 'all_values'}] + all_players
        return players

    @dash_app.callback(
        Output('crossfilter-team', 'options'),
        Input('crossfilter-player', 'value'),
        Input('crossfilter-year', 'value')
    )
    def update_team_options(selected_player, selected_year):
        sql_query = f"""
            select distinct team
            from player_profiles_by_team_and_year
            where
                1 = 1
                {'and player = (?)' if selected_player != 'all_values' else ''}
                {'and year = (?)' if selected_year != 'all_values' else ''}
            order by team
        """
        params = []

        if selected_player != 'all_values':
            params = params + [selected_player]
        if selected_year != 'all_values':
            params = params + [selected_year]
        
        all_teams = [{'label': team, 'value': team} for team in pd.read_sql(sql_query, conn, params=params).team]
        teams = [{'label': 'All Teams', 'value': 'all_values'}] + all_teams
        return teams

    @dash_app.callback(
        Output('crossfilter-year', 'options'),
        Input('crossfilter-player', 'value'),
        Input('crossfilter-team', 'value')
    )
    def update_year_options(selected_player, selected_team):
        sql_query = f"""
            select distinct year
            from player_profiles_by_team_and_year
            where
                1 = 1
                {'and player = (?)' if selected_player != 'all_values' else ''}
                {'and team = (?)' if selected_team != 'all_values' else ''}
            order by year desc
        """
        params = []

        if selected_player != 'all_values':
            params = params + [selected_player]
        if selected_team != 'all_values':
            params = params + [selected_team]

        all_years = [{'label': year, 'value': year} for year in pd.read_sql(sql_query, conn, params=params).year]
        years = [{'label': 'All Years', 'value': 'all_values'}] + all_years
        return years

# Profile sliders
 
def stat_slider(val, min, max, marks, label, id):
    return html.Div(
        [
            dbc.Label(label),
            dcc.Slider(min, max, value=val, marks=marks, disabled=True, included=False, className='statSlider', id=id),
        ],
    )

def create_slider_callbacks(dash_app, conn):
    @dash_app.callback(
        [
            Output('profile-slider-placeholder-col', 'className'),
            Output('profile-slider-col', 'className'),
            Output('similarity-filter-col', 'className'),
        ],
        [Input('crossfilter-player', 'value')]
    )
    def update_profile_col_visibility(selected_player):
        if selected_player == 'all_values':
            return 'text-muted', 'd-none', 'd-none'
        return 'd-none', '', ''


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
            player_profile = pd.read_sql('select * from player_profiles_by_team_and_year where player = (?) and team = (?) and year = (?)', 
                                         conn, params=(selected_player, selected_team, selected_year,))
            
        avg_dist = min(player_profile.avg_distance.item(), 21)
        avg_side = max(min((50 - player_profile.avg_shotX.item()), 35), 15)
        acc = player_profile.accuracy.item()
        top_qtr = player_profile.top_quarter.item()

        return avg_dist, avg_side, acc, top_qtr
    
# Similarity search

def similarity_filters():
    return html.Div(
        [
            dbc.Label('Filters:', html_for='similarity-filters', id='similarity-filter-lbl', className='d-none'),
            dbc.Checklist(
                options=[],
                id='similarity-filters',
                className='d-none'
            ),
            dbc.Label('Compare Attributes:', html_for='similarity-attributes',),
            dbc.Checklist(
                options=[
                    {'label': 'Shooting Distance', 'value': 'avg_distance'},
                    {'label': 'Side Preference', 'value': 'avg_shotX'},
                    {'label': 'Accuracy', 'value': 'accuracy'},
                    {'label': 'Top Quarter', 'value': 'top_quarter'},
                ],
                value=['avg_distance', 'avg_shotX', 'accuracy', 'top_quarter'],
                id='similarity-attributes',
                className='mb-2'
            ),
        ]
    )

def similarity_list():
    return dcc.Loading(html.Ol([], id="similarity-list-results"))

def create_similarity_list_callbacks(dash_app, similarity_calculators):
    get_player_similarities = similarity_calculators[0]
    get_player_similarities_by_team = similarity_calculators[1]
    get_player_similarities_by_year = similarity_calculators[2]
    get_player_similarities_by_team_year = similarity_calculators[3]

    @dash_app.callback(
        [
            Output('similarity-filters', 'options'),
            Output('similarity-filters', 'value'),
            Output('similarity-filters', 'className'),
            Output('similarity-filter-lbl', 'className')
        ],
        [
            Input('crossfilter-year', 'value'),
            Input('crossfilter-player', 'value'),
            Input('crossfilter-team', 'value'),
        ]
    )
    def update_similarity_filters(selected_year, selected_player, selected_team):
        options = []
        if selected_player == 'all_values': 
            return [], [], 'd-none', 'd-none'
        
        if selected_team != 'all_values':
            options += [{'label': 'Same Team', 'value': 'same-team'}]
        if selected_year != 'all_values':
            options += [{'label': 'Same Year', 'value': 'same-year'}]

        return options, [], '', 'd-none' if len(options) == 0 else ''

    @dash_app.callback(
        Output('similarity-list-results', 'children'),
        Input('crossfilter-year', 'value'),
        Input('crossfilter-player', 'value'),
        Input('crossfilter-team', 'value'),
        Input('similarity-attributes', 'value'),
        Input('similarity-filters', 'value'),
    )
    def update_similarity_list(selected_year, selected_player, selected_team, similarity_attributes, filters):
        if selected_player == 'all_values': 
            return []
        
        if len(similarity_attributes) == 0:
            return [html.Li('No Filters Selected!', style={'list-style-type': 'none'})]

        # Grouped by player
        if selected_team == 'all_values' and selected_year and selected_year == 'all_values':
            player_similarities = get_player_similarities(similarity_attributes)
            top = player_similarities[selected_player].sort_values(ascending=True)[1:6]
            return [html.Li([result]) for result in top.index]
        
        # Grouped by player and team
        elif selected_team != 'all_values' and selected_year == 'all_values':
            player_similarities_team = get_player_similarities_by_team(similarity_attributes)
            similar = player_similarities_team[(selected_player, selected_team)]
            
            # Optional filter
            if 'same-team' in filters:
                similar = similar[similar.index.get_level_values('team') == selected_team]
            
            top = similar.sort_values(ascending=True)[1:6]
            return [html.Li(f'{player} ({team})') for player, team in top.index]
        
        # Grouped by player and year
        elif selected_team == 'all_values' and selected_year != 'all_values':
            player_similarities_year = get_player_similarities_by_year(similarity_attributes)
            similar = player_similarities_year[(selected_player, selected_year)]
            
            # Optional filter
            if 'same-year' in filters:
                similar = similar[similar.index.get_level_values('year') == selected_year]
            
            top = similar.sort_values(ascending=True)[1:6]
            return [html.Li(f'{player} ({year})') for player, year in top.index]
        
        # Grouped by player, team, and year
        else:
            player_similarities_team_year = get_player_similarities_by_team_year(similarity_attributes)
            similar = player_similarities_team_year[(selected_player, selected_team, selected_year)]
            
            # Optional filters
            if 'same-team' in filters and 'same-year' in filters:
                similar = similar[(similar.index.get_level_values('team') == selected_team) & (similar.index.get_level_values('year') == selected_year)]
            elif 'same-team' in filters:
                similar = similar[similar.index.get_level_values('team') == selected_team]
            elif 'same-year' in filters:
                similar = similar[similar.index.get_level_values('year') == selected_year]

            top = similar.sort_values(ascending=True)[1:6]
            return [html.Li(f'{player} ({team} {year})') for player, team, year in top.index]

def create_similarity_calc_funcs(cache, conn):
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics.pairwise import euclidean_distances
    import pandas as pd

    @cache.memoize()
    def similarities_by_player(features):
        player_profiles = pd.read_sql('select * from player_profiles', conn)
        X_player_scaled = StandardScaler().fit_transform(player_profiles[features])
        similarities_player = pd.DataFrame(euclidean_distances(X_player_scaled), columns=player_profiles.player, index=player_profiles.player)
        return similarities_player
    
    @cache.memoize()
    def similarities_by_player_team(features):
        player_profiles_by_team = pd.read_sql('select * from player_profiles_by_team', conn)
        X_player_team_scaled = StandardScaler().fit_transform(player_profiles_by_team[features])
        idx = pd.MultiIndex.from_frame(player_profiles_by_team[['player', 'team']])
        similarities_player_team = pd.DataFrame(euclidean_distances(X_player_team_scaled), columns=idx, index=idx)
        return similarities_player_team
    
    @cache.memoize()
    def similarities_by_player_year(features):
        player_profiles_by_year = pd.read_sql('select * from player_profiles_by_year', conn)
        X_player_year_scaled = StandardScaler().fit_transform(player_profiles_by_year[features])
        idx = pd.MultiIndex.from_frame(player_profiles_by_year[['player', 'team']])
        similarities_player_year = pd.DataFrame(euclidean_distances(X_player_year_scaled), columns=idx, index=idx)
        return similarities_player_year
    
    @cache.memoize()
    def similarities_by_player_team_year(features):
        player_profiles_by_team_year = pd.read_sql('select * from player_profiles_by_team_and_year', conn)
        X_player_team_year_scaled = StandardScaler().fit_transform(player_profiles_by_team_year[features])
        idx = pd.MultiIndex.from_frame(player_profiles_by_team_year[['player', 'team', 'year']])
        similarities_player_team_year = pd.DataFrame(euclidean_distances(X_player_team_year_scaled), columns=idx, index=idx)
        return similarities_player_team_year

    return similarities_by_player, similarities_by_player_team, similarities_by_player_year, similarities_by_player_team_year 

