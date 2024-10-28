from dash import Dash, html, dcc, Input, Output, callback
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils import draw_plotly_court

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets)

df = pd.read_csv('https://raw.githubusercontent.com/willcoughlin/basketradar/refs/heads/main/data_processing/nov2k_clean_with_zones.csv?token=GHSAT0AAAAAACZNNLAHCDQCH762RPTHGXY6ZY65TEA')

markdown_text = '''
# BasketRadar
'''

app.layout = html.Div([
    dcc.Markdown(children=markdown_text),

    # filters
    html.Div([
        html.Label('Player'),
        dcc.Dropdown(
            id='crossfilter-player',
            options=[{'label': 'All Players', 'value': 'all_values'}] +
                    [{'label': player, 'value': player} for player in df['player'].unique()],
            value='all_values'
        ),
        html.Label('Team'),
        dcc.Dropdown(
            id='crossfilter-team',
            options=[{'label': 'All Teams', 'value': 'all_values'}] +
                    [{'label': team, 'value': team} for team in df['team'].unique()],
            value='all_values'
        ),
        html.Label('Year'),
        dcc.Dropdown(
            id='crossfilter-year',
            options=[{'label': 'All Years', 'value': 'all_values'}] +
                    [{'label': year, 'value': year} for year in df['date'].str[:4].unique()],
            value='all_values'
        ),
    ], 
    style={'width': '49%'}
    ),

    # distance scatter plot
    html.Div([
        dcc.Graph(id='distance-scatter'),
    ], style={'width': '49%', 'padding': '20 20'}),

    # radio button filter and shot map
    html.Div([
        dcc.RadioItems(
            ['Field Goal Percentage', 'Shot Attempts'],
            'Field Goal Percentage',
            id='shotmap-metric',
            labelStyle={'display': 'inline-block', 'marginTop': '10px'}
        ),
        dcc.Graph(id='shot-map')
    ], 
    style={'width': '49%'}
    ),

     # moving averages trend charts  
    html.Div([
        dcc.Graph(id='moving-average-2pt'),
        dcc.Graph(id='moving-average-3pt')
    ], style={'width': '49%', 'display': 'inline-block', 'padding': '20px 0'}),


])

# update dropdown options based on the other dropdowns
@app.callback(
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

@app.callback(
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

@app.callback(
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

# create & update distance scatterplot
@app.callback(
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
            return go.Figure()

        metric_histfunc = "avg" if metric == 'Field Goal Percentage' else "count"
        other_metric = 'shot_count' if metric == 'Field Goal Percentage' else 'fg_rate'

        x_bin_size = 15
        y_bin_size = 15
        fig = go.Figure()
        draw_plotly_court(fig, fig_width=600, margins=0)
        fig.add_trace(go.Histogram2dContour(
            x=dff['shotX_'],
            y=dff['shotY_'],
            z=dff['made_numeric'],
            histfunc=metric_histfunc,
            colorscale=custom_colorscale,
            line=dict(width=0),
            hoverinfo='x+y+z',
            hovertemplate=f"<b>{metric}</b>: %{{z:.2%}}<br>{other_metric.capitalize()}: %{{other_value}}<br>X: %{{x}}<br>Y: %{{y}}",
            xbins=dict(start=-250, end=250, size=x_bin_size),
            ybins=dict(start=-52.5, end=417.5, size=y_bin_size),
            showscale=True,
            colorbar=dict(title=metric)
        ))

        return fig

    def calculate_moving_averages(dff):
        dff['two_point_pct'] = dff.apply(lambda row: row['made'] / row['attempts'] if row['shot_type'] == '2PT' else 0, axis=1)
        dff['three_point_pct'] = dff.apply(lambda row: row['made'] / row['attempts'] if row['shot_type'] == '3PT' else 0, axis=1)

        moving_avg_2pt = dff[['date', 'two_point_pct']].groupby('date').mean().rolling(window=5).mean().reset_index()
        moving_avg_3pt = dff[['date', 'three_point_pct']].groupby('date').mean().rolling(window=5).mean().reset_index()

        return moving_avg_2pt, moving_avg_3pt

    moving_avg_2pt, moving_avg_3pt = calculate_moving_averages(dff)

    fig_moving_avg_2pt = go.Figure()
    fig_moving_avg_2pt.add_trace(go.Scatter(
        x=moving_avg_2pt['date'],
        y=moving_avg_2pt['two_point_pct'],
        mode='lines+markers',
        name='2-Point %',
        line=dict(color='blue')
    ))
    fig_moving_avg_2pt.update_layout(title='Moving Average 2-Point Percentage', xaxis_title='Date', yaxis_title='Percentage', plot_bgcolor='white')

    fig_moving_avg_3pt = go.Figure()
    fig_moving_avg_3pt.add_trace(go.Scatter(
        x=moving_avg_3pt['date'],
        y=moving_avg_3pt['three_point_pct'],
        mode='lines+markers',
        name='3-Point %',
        line=dict(color='green')
    ))
    fig_moving_avg_3pt.update_layout(title='Moving Average 3-Point Percentage', xaxis_title='Date', yaxis_title='Percentage', plot_bgcolor='white')

    scatter_fig = update_scatter(dff, agg_df)
    shot_map_fig = update_shot_map(dff, metric)
    
    return scatter_fig, shot_map_fig, fig_moving_avg_2pt, fig_moving_avg_3pt

if __name__ == '__main__':
    app.run_server(debug=True)
