from dash import Dash, html, dcc, Input, Output, callback
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils import draw_plotly_court

dash_app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],  suppress_callback_exceptions=True)
app = dash_app.server

df = pd.read_csv('https://basketradarstorage.blob.core.windows.net/cleandata/nov2k_clean_with_zones.csv')
# df = pd.read_csv('https://basketradarstorage.blob.core.windows.net/cleandata/cleaned_final_dataset.csv')

controls_filters = dbc.Card(
    [
        html.Div(
            [
                dbc.Label('Player'),
                dcc.Dropdown(
                    id='crossfilter-player',
                    options=[{'label': 'All Players', 'value': 'all_values'}] +
                            [{'label': player, 'value': player} for player in df['player'].unique()],
                    value='all_values'
                ),
            ], 
        ),
        html.Div(
            [
                dbc.Label('Team'),
                dcc.Dropdown(
                    id='crossfilter-team',
                    options=[{'label': 'All Teams', 'value': 'all_values'}] +
                            [{'label': team, 'value': team} for team in df['team'].unique()],
                    value='all_values'
                ),
            ],
        ),
        html.Div(
            [
                dbc.Label('Year'),
                dcc.Dropdown(
                    id='crossfilter-year',
                    options=[{'label': 'All Years', 'value': 'all_values'}] +
                            [{'label': year, 'value': year} for year in df['date'].unique()],
                    value='all_values'
                ),
            ], 
        )
    ],
)

controls_metric = dbc.Card(
    [
        html.Div(
            [
                dbc.Label('Metric'),
                dcc.RadioItems(
                    options=[
                        {'label': 'Field Goal Percentage', 'value': 'Field Goal Percentage'},
                        {'label': 'Shot Attempts', 'value': 'Shot Attempts'}
                    ],
                    value='Field Goal Percentage',
                    id='shotmap-metric',
                    labelStyle={'display': 'block'}
                ),
            ], className="mx-auto"
        ),
    ],
)

dash_app.layout = dbc.Container(
    [
        html.H1("BasketRadar"),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(controls_filters, md=6, className="text-center"),
                dbc.Col(
                    [
                        dbc.Row(
                            [
                                dbc.Col(dcc.Markdown(children='### Player Image', className="text-center")),
                                dbc.Col(dcc.Markdown(children='### Team Image', className="text-center"))
                            ],
                            align="center"
                        ),
                    ],
                ),
            ],
            align="center",justify="center"
        ),
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(id='distance-scatter'), 
                    md=6,
                    className="mx-auto" 
                ),
                dbc.Col(
                    dcc.Graph(id='moving-average-2pt'), 
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
                        dbc.Row(dcc.Graph(id='shot-map'), className="mx-auto"),
                        dbc.Row(controls_metric, className="mx-auto"),
                    ],
                    md=6
                ),
                dbc.Col(
                    dcc.Graph(id='moving-average-3pt'), 
                    md=6,
                    className="mx-auto"
                ),
            ],
            align="center",
        ),
    ],
    fluid=True,
)

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

# player image - just need to figure out how to pull player ID first 
# @dash_app.callback(
#     Output(component_id='player-image', component_property='src'),
#     Input(component_id='player-select', component_property='value')
# )
# def update_image(pid):
#     return 'https://cdn.nba.com/headshots/nba/latest/1040x760/%d.png' % pid

# create & update plots
@dash_app.callback(
    Output('distance-scatter', 'figure'),
    Output('shot-map', 'figure'),
    Output('moving-average-2pt', 'figure'),
    Output('moving-average-3pt', 'figure'),
    Input('crossfilter-player', 'value'),
    Input('crossfilter-team', 'value'),
    Input('crossfilter-year', 'value'),
    Input('shotmap-metric', 'value')
)
def update_graphs(player_name, team, year, metric):
    dff = df.copy()
    dff['made_numeric'] = dff['made'].astype(int)

    # Define the old and new x- and y-ranges & transform coords
    old_x_range = (0, 50)
    new_x_range = (-250, 250)
    old_y_range = (0, 47)
    new_y_range = (-52.5, 417.5)
    dff['shotX_'] = ((dff['shotX'] - old_x_range[0]) / (old_x_range[1] - old_x_range[0])) * (new_x_range[1] - new_x_range[0]) + new_x_range[0]
    dff['shotY_'] = ((dff['shotY'] - old_y_range[0]) / (old_y_range[1] - old_y_range[0])) * (new_y_range[1] - new_y_range[0]) + new_y_range[0]

    if player_name and player_name != 'all_values':
        dff = dff[dff['player'] == player_name]
    if team and team != 'all_values':
        dff = dff[dff['team'] == team]
    if year and year != 'all_values':
        dff = dff[dff['date'].str[:4] == year]

    agg_df = dff.groupby(['distance', 'shot_type']).agg(
        average_made=('made', 'mean'),
        count_shots=('made', 'count')
    ).reset_index()

    def update_scatter(dff, agg_df):
        if dff.empty:
            return px.scatter(title="No data available for the selected filters.")
        fig = px.scatter(agg_df,
                         x='distance',
                         y='average_made',
                         size='count_shots',
                         size_max=40, 
                         color='shot_type',
                         hover_name='distance',
                         labels={'average_made': 'Accuracy', 'shot_type': 'Shot Type',},
                         title='Average Field Goal % by Distance'
                         )
        
        fig.update_xaxes(
            title='Distance',
            showgrid=True,
            gridcolor='LightGray',
            dtick=10
        )
        fig.update_yaxes(
            title='Accuracy',
            tickformat='2%',
            showgrid=True, 
            gridcolor='LightGray',
            dtick=0.2
        )
        fig.update_layout(
            plot_bgcolor="white",
            # margin={'l': 40, 'b': 40, 't': 40, 'r': 0},
            hovermode='closest'
        )
        return fig

    def update_shot_map(dff, metric):
        # colorblind-safe colorscale from https://colorbrewer2.org/#type=sequential&scheme=OrRd&n=9
        custom_colorscale = [
            [0.0, '#fff7ec'],
            [0.11, '#fee8c8'],
            [0.22, '#fdd49e'],
            [0.33, '#fdbb84'],
            [0.44, '#fc8d59'],
            [0.56, '#ef6548'],
            [0.67, '#d7301f'],
            [0.78, '#b30000'],
            [1.0, '#7f0000']
        ]

        if dff.empty:
            return go.Figure(data=[go.Scatter(x=[], y=[], mode='text', text=["No data available for the selected filters."])])

        metric_histfunc = "avg" if metric == 'Field Goal Percentage' else "count"

        x_bin_size = 15
        y_bin_size = 15
        shotmap_fig = go.Figure()
        draw_plotly_court(shotmap_fig, fig_width=700, margins=0)
        shotmap_fig.add_trace(go.Histogram2dContour(
            x=dff['shotX_'],
            y=dff['shotY_'],
            z=dff['made_numeric'],
            histfunc=metric_histfunc,
            colorscale=custom_colorscale,
            line=dict(width=0),
            hoverinfo='x+y+z',
            hovertemplate=(
                f"<b>{metric}</b>: %{{z:.2}}<br>"
                f"X: %{{x}}<br>"
                f"Y: %{{y}}"
                "<extra></extra>"
            ),
            xbins=dict(start=-250, end=250, size=x_bin_size),
            ybins=dict(start=-52.5, end=417.5, size=y_bin_size),
            showscale=True,
            colorbar=dict(title=metric)
        ))
        return shotmap_fig
    
    def update_trend_charts(dff, point_value):
        shot_type = f'{point_value}-pointer'
        dfff=dff[dff['shot_type']==shot_type]

        avg_df = dfff[['date', 'made_numeric']].groupby('date').mean()
        moving_avg_df = avg_df.rolling(window=3).mean().reset_index()
        average_rate = dfff['made_numeric'].mean()
        moving_avg_df['marker_color'] = np.where(
            moving_avg_df['made_numeric'] < average_rate, 'lightcoral',
            np.where(moving_avg_df['made_numeric'] > average_rate, 'palegreen', 'lightgray')
        )

        fig_moving_avg = go.Figure()
        fig_moving_avg.add_trace(go.Scatter(
            x=moving_avg_df['date'],
            y=moving_avg_df['made_numeric'],
            mode='lines+markers',
            marker=dict(size=10, color=moving_avg_df['marker_color']),
            line=dict(color='black'),
            name=f'3-day moving average of {shot_type} %',
            hovertemplate="3-day moving average: %{y:.2%}"
                            "<extra></extra>"
        ))
        fig_moving_avg.add_trace(go.Scatter(
            x=[moving_avg_df['date'].min(),moving_avg_df['date'].max()],
            y=[average_rate, average_rate],
            mode='lines',
            line=dict(color='LightGray', dash='dash'),
            name=f'average {shot_type} %',
        ))
        fig_moving_avg.update_yaxes(
                    title='Accuracy',
                    tickformat='2%',
                    showgrid=True, 
                    gridcolor='LightGray',
                    dtick=0.2
                )
        fig_moving_avg.update_xaxes(
            tickformat="%m/%d/%Y", 
        )
        fig_moving_avg.update_layout(title=f'Moving Average {point_value}-Point Percentage',
                                    xaxis_title='Date', 
                                    yaxis_title='Percentage', 
                                    yaxis=dict(range=[0, 1], autorange=False),
                                    plot_bgcolor='white',
                                    hovermode='x unified')

        return fig_moving_avg

    scatter_fig = update_scatter(dff, agg_df)
    shot_map_fig = update_shot_map(dff, metric)
    fig_moving_avg_2pt = update_trend_charts(dff, 2)
    fig_moving_avg_3pt = update_trend_charts(dff, 3)
    
    return scatter_fig, shot_map_fig, fig_moving_avg_2pt, fig_moving_avg_3pt

if __name__ == '__main__':
    dash_app.run(debug=True)
