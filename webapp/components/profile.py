from dash import html, dcc, Output, Input, ctx, State
import plotly.express as px
from plotly.figure_factory import create_dendrogram
import dash_bootstrap_components as dbc
import pandas as pd
import urllib.parse
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import euclidean_distances
import scipy.cluster.hierarchy as sch

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

    @dash_app.callback(
        [
            Output('crossfilter-player', 'value'),
            Output('crossfilter-team', 'value'),
            Output('crossfilter-year', 'value'),
            Output('url', 'href')
        ],
        [
            Input('crossfilter-player', 'value'),
            Input('crossfilter-team', 'value'),
            Input('crossfilter-year', 'value'),
            Input('url', 'search')
        ],
        prevent_initial_call=True
    )
    def update_selections_from_url(selected_player, selected_team, selected_year, query_str):
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if trigger_id == 'url':
            args = urllib.parse.parse_qs(query_str[1:])
            return (
                args.get('player', ['all_values'])[0],
                args.get('team', ['all_values'])[0],
                args.get('year', ['all_values'])[0],
                f'/{query_str}'
            )
        
        new_args = {}
        if selected_player != 'all_values': new_args['player'] = selected_player
        if selected_team != 'all_values': new_args['team'] = selected_team
        if selected_year != 'all_values': new_args['year'] = selected_year
        new_query_str = f'/?{urllib.parse.urlencode(new_args)}'

        return selected_player, selected_team, selected_year, new_query_str

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

def dissimilarity_list():
    return dcc.Loading(html.Ol([], id='dissimilarity-list-results'))

def player_list_btn(i, text, urlparams, dissimilar=False):
    return html.Li(
        dbc.Button(
            text,
            color='link', 
            n_clicks=0,
            id=f'{"similar" if not dissimilar else "dissimilar"}-player-btn-{i}',
            href=f'/?{urllib.parse.urlencode(urlparams)}'
        ),
        className='similar-player-link'
    ) 

def launch_modal_btn():
    return dbc.Button(['Visualize ', html.I(className="bi bi-stars")], id='open-similarity-modal', n_clicks=0, style={'width': '100%'})

def similarity_modal():
    modal = dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Similarity Visualizer")),
            dbc.ModalBody(
                [
                    html.Div(
                        [ 
                            html.Div(
                                [
                                    html.Strong('Similarity Attributes'),
                                    html.Div([], id='modal-attributes-container')
                                ],
                                style={'width': '40%'}
                            ),
                            html.Div(
                                [
                                    html.Strong('Filters'),
                                    html.Div([], id='modal-filters-container')
                                ],
                                style={'width': '40%'},
                                id='modal-filters-container-parent'
                            )  
                        ],
                        style={'display': 'flex', 'justify-content': 'space-around'}
                    ),
                    html.Div(id='similarity-modal-body'),
                ]
            ),
            dbc.ModalFooter(
                dbc.Button(
                    "Close", id="close", className="ms-auto", n_clicks=0
                )
            ),
        ],
        id="similarity-modal",
        is_open=False,
        size="lg"
    )
    return modal

def create_similarity_dendrogram(df, similarity_attributes, selected_player, similar_players):
    X = df[similarity_attributes].values
    y = df.player.values
    similar_player_names = similar_players.index

    X_scaled = StandardScaler().fit_transform(X)

    # Compute threshold of furthest "similar player"
    # furthest_similar = similar_players.index[similar_players.argmax()]
    # idx_tgt = np.argwhere(y == selected_player).astype(np.float64)[0][0]
    # idx_sim = np.argwhere(y == furthest_similar).astype(np.float64)[0][0]
    # n = X.shape[0]
    # Z = sch.linkage(X_scaled, 'centroid')  
    # cluster_tgt = idx_tgt
    # cluster_sim = idx_sim
    # while cluster_sim != cluster_tgt:
    #     print(cluster_tgt, cluster_sim)
    #     cluster_tgt = n+[(i, row) for i, row in enumerate(Z) if cluster_tgt in row[:2]][0][0]
    #     cluster_sim = n+[(i, row) for i, row in enumerate(Z) if cluster_sim in row[:2]][0][0]
    # linkage_idx = cluster_tgt-n
    # print(Z[linkage_idx][2])
    # color_thres = Z[linkage_idx][2] + 0.1
    # print(color_thres)
    color_thres = 100

    fig = create_dendrogram(X_scaled, 
                            labels=y, 
                            color_threshold=color_thres, 
                            orientation='left',
                            linkagefun=lambda x: sch.linkage(x, 'centroid'))
    
    tick_idx = np.argwhere(fig.layout.yaxis.ticktext == selected_player)[0][0]

    zoomed_y_axis = [fig.layout.yaxis.tickvals[tick_idx - 9], fig.layout.yaxis.tickvals[tick_idx + 10]]
    zoomed_x_axis = [0, 2]

    fig.update_xaxes(range=zoomed_x_axis, minallowed=0)#, rangeslider=dict(visible=True))
    fig.update_yaxes(range=zoomed_y_axis)
    # fig.show(config={
    #     'modeBarButtonsToRemove': ['autoScale', 'resetScale']
    # })
    # fig.layout.update({
        # 'width': 900,
    # })

    def tick_text(player):
        if player == selected_player: 
            return f'<span style="color: #0d6efd; font-weight: bold;">{player}</span>' 
        elif player in similar_player_names:
            return f'<span style="color: #0d6efd">{player}</span>' 
        else: 
            return player
    fig.layout.yaxis.ticktext = [tick_text(t) for t in fig.layout.yaxis.ticktext]
    fig.update_layout(autosize=True, margin=dict(t=50, b=50))

    return dcc.Graph(figure=fig, id='dendrogram', style={'width': '100%'})

def create_similarity_scatter(df, selected_player, similar_players):    
    target = df.player.apply(lambda x: f'{selected_player} and most similar' if x in [selected_player, *similar_players] else 'Others') 
    size = df.player.apply(lambda x: 3 if x == selected_player else 1)

    X = df.drop(columns='player').values
    y = df.player.values
    
    X_scaled = StandardScaler().fit_transform(X)

    fig_scatter2 = px.scatter(x=X_scaled[:,0], y=X_scaled[:,2], hover_name=y, hover_data=[target], color=target, size=size)

    bigger_series = 0 if len(fig_scatter2.data[0].x) > len(fig_scatter2.data[1].x) else 1
    smaller_series = 1 - bigger_series

    min_x = min(fig_scatter2.data[bigger_series].x)
    max_x = max(fig_scatter2.data[bigger_series].x)
    range_x = max_x - min_x

    min_y = min(fig_scatter2.data[bigger_series].y)
    max_y = max(fig_scatter2.data[bigger_series].y)
    range_y = max_y + min_y

    tick_idx = np.argwhere(fig_scatter2.data[smaller_series].hovertext == selected_player)[0][0]
    target_x = fig_scatter2.data[smaller_series].x[tick_idx]
    target_y = fig_scatter2.data[smaller_series].y[tick_idx]

    zoomed_x_axis = [target_x - (0.05 * range_x), target_x + (0.05 * range_x)]
    zoomed_y_axis = [target_y - (0.05 * range_y), target_y + (0.05 * range_y)]
    fig_scatter2.update_xaxes(range=zoomed_x_axis)
    fig_scatter2.update_yaxes(range=zoomed_y_axis)

    return dcc.Graph(figure=fig_scatter2)

def create_similarity_list_callbacks(dash_app, similarity_calculators, conn):
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
            Input('similarity-filters', 'value'),
        ]
    )
    def update_similarity_filters(selected_year, selected_player, selected_team, cur_filter_vals):
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        options = []
        if selected_player == 'all_values': 
            return [], [], 'd-none', 'd-none'
        
        if selected_team != 'all_values':
            options += [{'label': 'Same Team', 'value': 'same-team'}]
        if selected_year != 'all_values':
            options += [{'label': 'Same Year', 'value': 'same-year'}]

        filter_vals = cur_filter_vals or []

        return options, [v for v in filter_vals if v in [d['value'] for d in options]], '', 'd-none' if len(options) == 0 else ''

    @dash_app.callback(
        Output('modal-attributes-container', 'children'),
        Output('modal-filters-container', 'children'),
        Output('modal-filters-container-parent', 'className'),
        Input('similarity-attributes', 'value'),
        Input('similarity-filters', 'value'),
        Input('similarity-filters', 'className')
    )
    def update_modal_pills(selected_attrs, selected_filters, filter_className):
        attr_map = {
            'avg_distance': 'Average Distance', 
            'avg_shotX': 'Side Preference', 
            'accuracy': 'Accuracy',
            'top_quarter': 'Top Quarter'
        }

        filter_map = {
            'same-team': 'Same Team', 
            'same-year': 'Same Year', 
        }

        if 'd-none' in filter_className:
            filter_pills = []
            filter_className = 'd-none'
        else:
            filter_pills = [dbc.Badge(filter_map[f], pill=True, color="primary", className="me-1") for f in selected_filters]
            filter_className = '' if len(filter_pills) > 0 else 'd-none'

        attr_pills = [dbc.Badge(attr_map[a], pill=True, color="primary", className="me-1") for a in selected_attrs]

        return attr_pills, filter_pills, filter_className

    @dash_app.callback(
        Output('similarity-list-results', 'children'),
        Output('dissimilarity-list-results', 'children'),
        Output('similarity-modal-body', 'children'),
        Input('crossfilter-year', 'value'),
        Input('crossfilter-player', 'value'),
        Input('crossfilter-team', 'value'),
        Input('similarity-attributes', 'value'),
        Input('similarity-filters', 'value')
    )
    def update_similarity_list(selected_year, selected_player, selected_team, similarity_attributes, filters):
        if selected_player == 'all_values': 
            return [], [], None
        
        if len(similarity_attributes) == 0:
            return (
                [html.Li('No Filters Selected!', style={'list-style-type': 'none'})], 
                [html.Li('No Filters Selected!', style={'list-style-type': 'none'})],
                None
            )

        df = pd.read_sql('select player, avg_distance, avg_shotX, accuracy, top_quarter from player_profiles', conn)

        # Grouped by player
        if selected_team == 'all_values' and selected_year and selected_year == 'all_values':
            player_similarities = get_player_similarities(similarity_attributes)
            sorted_sims = player_similarities[selected_player].sort_values(ascending=True)
            top = sorted_sims[1:4]
            bottom = player_similarities[-3:]
            return (
                [player_list_btn(i, result, {"player": result}) for i, result in enumerate(top.index)], 
                [player_list_btn(i, result, {"player": result}, dissimilar=True) for i, result in enumerate(bottom.index)],
                create_similarity_dendrogram(df, similarity_attributes, selected_player, top)
            )
        
        # Grouped by player and team
        elif selected_team != 'all_values' and selected_year == 'all_values':
            player_similarities_team = get_player_similarities_by_team(similarity_attributes)
            similar = player_similarities_team[(selected_player, selected_team)]
            
            # Optional filter
            if 'same-team' in filters:
                similar = similar[similar.index.get_level_values('team') == selected_team]
            sorted_sims = similar.sort_values(ascending=True)
            top = sorted_sims[1:4]
            bottom = sorted_sims[-3:]
            return (
                [player_list_btn(i, f'{player} ({team})',{"player": player, "team": team}) for i, (player, team) in enumerate(top.index)], 
                [player_list_btn(i, f'{player} ({team})',{"player": player, "team": team}, dissimilar=True) for i, (player, team) in enumerate(bottom.index)], 
                create_similarity_dendrogram(df, similarity_attributes, selected_player, top)
            )
        
        # Grouped by player and year
        elif selected_team == 'all_values' and selected_year != 'all_values':
            player_similarities_year = get_player_similarities_by_year(similarity_attributes)
            similar = player_similarities_year[(selected_player, selected_year)]
            
            # Optional filter
            if 'same-year' in filters:
                similar = similar[similar.index.get_level_values('year') == selected_year]
            
            sorted_sims = similar.sort_values(ascending=True)
            top = sorted_sims[1:4]
            bottom = sorted_sims[-3:]
            return (
                [player_list_btn(i, f'{player} ({year})',{"player": player, "year": year}) for i, (player, year) in enumerate(top.index)], 
                [player_list_btn(i, f'{player} ({year})',{"player": player, "year": year}, dissimilar=False) for i, (player, year) in enumerate(bottom.index)], 
                create_similarity_dendrogram(df, similarity_attributes, selected_player, top)
            )
        
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

            sorted_sims = similar.sort_values(ascending=True)
            top = sorted_sims[1:4]
            bottom = sorted_sims[-3:]
            return (
                [player_list_btn(i, f'{player} ({team} {year})', {"player": player, "team": team, "year": year}) for i, (player, team, year) in enumerate(top.index)], 
                [player_list_btn(i, f'{player} ({team} {year})', {"player": player, "team": team, "year": year}, dissimilar=False) for i, (player, team, year) in enumerate(bottom.index)], 
                create_similarity_dendrogram(df, similarity_attributes, selected_player, top)
            )
                
    @dash_app.callback(
        Output("similarity-modal", "is_open"),
        [Input("open-similarity-modal", "n_clicks"), Input("close", "n_clicks")],
        [State("similarity-modal", "is_open")],
    )
    def toggle_modal(n1, n2, is_open):
        if n1 or n2:
            return not is_open
        return is_open

def create_similarity_calc_funcs(cache, conn):
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
        idx = pd.MultiIndex.from_frame(player_profiles_by_year[['player', 'year']])
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

