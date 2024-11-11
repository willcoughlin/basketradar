import numpy as np
import plotly.express as px
import plotly.graph_objects as go
# import dash_bootstrap_components as dbc
from dash import Output, Input, dcc, html
from utils import draw_plotly_court
import pandas as pd
import time
from datetime import timedelta

distance_scatter = dcc.Loading(dcc.Graph(id='distance-scatter'))
moving_average_2pt = dcc.Loading(dcc.Graph(id='moving-average-2pt'))
moving_average_3pt = dcc.Loading(dcc.Graph(id='moving-average-3pt'))
shot_map = dcc.Loading(dcc.Graph(id='shot-map',style={'marginLeft': 'auto', 'marginRight': 'auto'}))
# controls_metric = dbc.Card(
#     [
#         html.Div(
#             [
#                 dbc.Label('Metric'),
#                 dcc.RadioItems(
#                     options=[
#                         {'label': 'Field Goal Percentage', 'value': 'Field Goal Percentage'},
#                         {'label': 'Shot Attempts', 'value': 'Shot Attempts'}
#                     ],
#                     value='Field Goal Percentage',
#                     id='shotmap-metric',
#                     labelStyle={'display': 'block'}
#                 ),
#             ], className="mx-auto"
#         ),
#     ],
# )

def create_plot_callbacks(dash_app, conn, cache):
    def filter_db_data(player_name, team, year):
        sql_query = f"""
            select 
                shot_type, 
                distance, 
                made, 
                shotX, 
                shotY,
                date,
                year
            from shots
            where
                1 = 1
                {'and player = (?)' if player_name != 'all_values' else ''}
                {'and team = (?)' if team != 'all_values' else ''}
                {'and year = (?)' if year != 'all_values' else ''}
        """
        # print(f'sql_query: \n{sql_query}')

        params = []
        if player_name and player_name != 'all_values':
            params = params + [player_name]
        if team and team != 'all_values':
            params = params + [team]
        if year and year != 'all_values':
            params = params + [int(year)]
        print(f'params: \n{params}')

        start_time = time.time()
        dff = pd.read_sql(sql_query, conn, params=params) if len(params) > 0 else pd.read_sql(sql_query, conn)
        dff['shotX_'] = dff['shotX'] / 50 * 500 - 250
        dff['shotY_'] = dff['shotY'] / 47 * 470 - 52.5
        print(f'DF loaded in {time.time() - start_time} sec')
        # print(f'dff.head(): \n{dff.head()}')
        return dff
    
    def agg_ma_data(dff, point_value):
        start_time = time.time()
        agg_date_df = dff[dff['shot_type'] == point_value]
        agg_date_df.loc[:, 'date'] = pd.to_datetime(agg_date_df['date'])
        agg_date_df = agg_date_df.sort_values(by='date')
        print(f'    ma filtering took {time.time() - start_time} sec')

        start_time = time.time()
        average_rate = agg_date_df['made'].mean()
        moving_avg_df = agg_date_df[['date', 'made']].groupby('date').mean().rolling(window=3).mean().reset_index()
        moving_avg_df['average'] = average_rate
        moving_avg_df['above_avg'] = np.where(moving_avg_df['made'] > moving_avg_df['average'], moving_avg_df['made'], moving_avg_df['average'])
        moving_avg_df['below_avg'] = np.where(moving_avg_df['made'] < moving_avg_df['average'], moving_avg_df['made'], moving_avg_df['average'])
        # moving_avg_df['date_str'] = moving_avg_df['date'].dt.strftime('%-m/%-d/%Y')
        print(f'    ma agg took {time.time() - start_time} sec')
        
        return agg_date_df, moving_avg_df

    # Preload and cache unfiltered dataframe
    @cache.cached(key_prefix='unfiltered_data')
    def preload_unfiltered_data():
        return filter_db_data(*['all_values'] * 3)
    preload_unfiltered_data()

    # Preload and cache moving avg agg on unfiltered dataframe
    @cache.memoize()
    def preload_unfiltered_ma(point_value):
        return agg_ma_data(preload_unfiltered_data(), point_value)
    preload_unfiltered_ma(2)
    preload_unfiltered_ma(3)

    #create & update plots
    @dash_app.callback(
        [Output('distance-scatter', 'figure'),
        Output('shot-map', 'figure'),
        Output('moving-average-2pt', 'figure'),
        Output('moving-average-3pt', 'figure')],
        Input('crossfilter-player', 'value'),
        Input('crossfilter-team', 'value'),
        Input('crossfilter-year', 'value'),
        # Input('shotmap-metric', 'value')
    )
    def update_graphs(player_name, team, year, metric='Field Goal Percentage'):
        def update_scatter(dff):
            if dff.empty:
                return px.scatter(title="No data available for the selected filters.")
            else:
                start_time = time.time()
                agg_dist_df = dff.groupby(['distance', 'shot_type']).agg(
                    average_made=('made', 'mean'),
                    count_shots=('made', 'count')
                ).reset_index()
                agg_dist_df['shot_type_label'] = agg_dist_df.shot_type.astype(str) + '-pointer'
                print(f'DF aggregated in {time.time() - start_time} sec')
                # print(f'agg_dist_df.head(): \n{agg_dist_df.head()}')

                fig = px.scatter(agg_dist_df,
                                x='distance',
                                y='average_made',
                                size='count_shots',
                                size_max=40, 
                                color='shot_type_label',
                                # hover_name='distance',
                                labels={'distance': 'Distance (feet)', 'average_made': 'FG%', 'shot_type_label': 'Shot Type',},
                                title='Average Field Goal Percentage (FG%) by Distance',
                                )
                fig.update_traces(hovertemplate=(
                    "<b>%{x} feet</b><br>"
                    "FG%: %{y:.2%}<br>"
                    "%{marker.size:,} shot attempts<br>"
                    "<extra></extra>"
                ))
                fig.update_layout(
                    plot_bgcolor="white",
                    # margin={'l': 40, 'b': 40, 't': 40, 'r': 0},
                    yaxis=dict(
                        title='FG%',
                        tickformat='2%',
                        showgrid=True, 
                        gridcolor='LightGray',
                        dtick=0.2
                    ),
                    legend=dict(
                        orientation="h",
                        yanchor="top",
                        y=0.99,
                        xanchor="right",
                        x=0.99
                    )
                )
                return fig

        def update_shot_map(dff, metric):
            if dff.empty:
                return go.Figure(data=[go.Scatter(x=[], y=[], mode='text', text=["No data available for the selected filters."])])
            else:
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
                metric_histfunc = "avg" if metric == 'Field Goal Percentage' else "count"
                x_bin_size = 15
                y_bin_size = 15
                shotmap_fig = go.Figure()
                draw_plotly_court(shotmap_fig, fig_width=400, margins=0)
                shotmap_fig.add_trace(go.Histogram2dContour(
                    x=dff['shotX_'],
                    y=dff['shotY_'],
                    z=dff['made'], 
                    histfunc=metric_histfunc,
                    colorscale=custom_colorscale,
                    line=dict(width=0),
                    hoverinfo='x+y+z',
                    hovertemplate=(
                        f"<b>{metric}</b>: %{{z:.2%}}<br>"
                        # f"X: %{{x}}<br>"
                        # f"Y: %{{y}}"
                        "<extra></extra>"
                    ),
                    xbins=dict(start=-250, end=250, size=x_bin_size),
                    ybins=dict(start=-52.5, end=417.5, size=y_bin_size),
                    showscale=False,
                    # colorbar=dict(title=metric),
                    # colorbar_xpad=False,
                    # colorbar_ypad=False,
                    # colorbar_tickformat = '.0%'
                ))
                shotmap_fig.update_layout(
                    autosize=True, 
                    margin=dict(l=0, r=0, t=0, b=0),  
                )
                return shotmap_fig
        
        def update_trend_charts(dff, point_value):
            point_value_str = f'{point_value}-pointer'

            if player_name == 'all_values' and team == 'all_values' and year == 'all_values':
                agg_date_df, moving_avg_df = preload_unfiltered_ma(point_value)
            else:
                agg_date_df, moving_avg_df = agg_ma_data(dff, point_value)            
            
            last_date = moving_avg_df['date'].max()
            one_year_ago = last_date - timedelta(days=365)
            # data_dates =           
            date_observations = pd.Index(pd.to_datetime(moving_avg_df['date'].dt.date.unique()))
            date_range_index = pd.Index(pd.date_range(start=agg_date_df['date'].iloc[0], end=agg_date_df['date'].iloc[-1]).date)
            dt_breaks = date_range_index.difference(date_observations).tolist()

            # print(f'moving_avg_df.head(): \n{moving_avg_df.head()}')

            fig_moving_avg = go.Figure()
            fig_moving_avg.add_trace(go.Scatter(
                x=moving_avg_df['date'],
                y=moving_avg_df['average'],
                mode='lines',
                line_color="rgba(0,0,0,0)",
                showlegend=False,
            ))
            fig_moving_avg.add_trace(go.Scatter(
                x=moving_avg_df['date'],
                y=moving_avg_df['below_avg'],
                fill='tonexty',
                mode='none',
                fillcolor='lightcoral',
                showlegend=False,
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    f"{point_value_str}" + " moving average: %{y:.2%} (below average)"
                    "<extra></extra>"),
            ))
            fig_moving_avg.add_trace(go.Scatter(
                x=moving_avg_df['date'],
                y=moving_avg_df['average'],
                mode='lines',
                line_color="rgba(0,0,0,0)",
                showlegend=False,
            ))
            fig_moving_avg.add_trace(go.Scatter(
                x=moving_avg_df['date'],
                y=moving_avg_df['above_avg'],
                fill='tonexty',
                mode='none',
                fillcolor='rgba(0, 109, 44, 0.4)',
                showlegend=False,
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    f"{point_value_str}" + " moving average: %{y:.2%} (above average)"
                    "<extra></extra>"),
            ))
            fig_moving_avg.add_trace(go.Scatter(
                x=moving_avg_df['date'],
                y=moving_avg_df['average'],
                mode='lines',
                line=dict(color='Black', dash='dash'),
                showlegend=True,
                name=f'average {point_value_str} %',
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    f"{point_value_str}" + " overall average: %{y:.2%}<extra></extra>"
                    "<extra></extra>"),
            ))

            fig_moving_avg.update_layout(
                title=f'{point_value}-Pt FG% Moving Average',
                plot_bgcolor='white',
                xaxis=dict(
                    type="date",
                    nticks=3,
                    title='Date',
                    range=[one_year_ago, last_date],
                    tickformat='%-m/%-d/%Y',
                    rangebreaks=[dict(values=dt_breaks)],
                    # rangeslider_visible=True,
                    rangeselector=dict(
                        buttons=list([
                            dict(count=7, label="1w", step="day", stepmode="backward"),
                            dict(count=1, label="1m", step="month", stepmode="backward"),
                            dict(count=6, label="6m", step="month", stepmode="backward"),
                            dict(count=1, label="YTD", step="year", stepmode="todate"),
                            dict(count=1, label="1y", step="year", stepmode="backward"),
                            dict(count=5, label="5y", step="year", stepmode="backward"),
                            dict(count=10, label="10y", step="year", stepmode="backward"),
                            dict(step="all")
                        ])
                    )
                ),
                yaxis=dict(
                    title='3-day Moving Average',
                    tickformat='2%',
                    showgrid=True,
                    gridcolor='LightGray',
                    nticks=4
                ),
                legend=dict(
                    yanchor="bottom",
                    y=0.99,
                    xanchor="right",
                    x=0.99
                )
            )
            return fig_moving_avg

        if player_name == 'all_values' and team == 'all_values' and year == 'all_values':
            dff = preload_unfiltered_data()
        else:
            dff = filter_db_data(player_name, team, year)

        # update_graphs
        start_time = time.time()
        scatter_fig = update_scatter(dff)
        print(f'scatter loaded in {time.time() - start_time} sec')
        start_time = time.time()
        shot_map_fig = update_shot_map(dff, metric)
        print(f'shot map loaded in {time.time() - start_time} sec')
        start_time = time.time()
        fig_moving_avg_2pt = update_trend_charts(dff, 2)
        print(f'2 pt ma loaded in {time.time() - start_time} sec')
        start_time = time.time()
        fig_moving_avg_3pt = update_trend_charts(dff, 3)
        print(f'3pt ma loaded in {time.time() - start_time} sec')
        
        return scatter_fig, shot_map_fig, fig_moving_avg_2pt, fig_moving_avg_3pt
