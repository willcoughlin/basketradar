import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
# import dash_bootstrap_components as dbc
from dash import Output, Input, dcc, html
from utils import draw_plotly_court
import pandas as pd
import time
# from datetime import timedelta
from dateutil.relativedelta import relativedelta


distance_scatter = dcc.Loading(dcc.Graph(id='distance-scatter'))
moving_average = dcc.Loading(dcc.Graph(id='moving-average'))
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
        return dff
    
    def agg_ma_data(dff):
        start_time = time.time()
        dff['date'] = pd.to_datetime(dff['date'])
        dff = dff.sort_values(by='date')
        moving_avg_df = dff[['date', 'shot_type', 'made']].groupby(['date', 'shot_type']).mean().reset_index().pivot_table(
            index='date', 
            columns='shot_type', 
            values='made', 
            fill_value=np.nan
        )
        moving_avg_df.columns.name = None
        moving_avg_df=moving_avg_df.rolling(window=3).mean()
        print(f'    ma agg took {time.time() - start_time} sec')

        return moving_avg_df

    # Preload and cache unfiltered dataframe
    @cache.cached(key_prefix='unfiltered_data', timeout=0)
    def preload_unfiltered_data():
        return filter_db_data(*['all_values'] * 3)
    preload_unfiltered_data()

    # Preload and cache moving avg agg on unfiltered dataframe
    @cache.memoize(timeout=0)
    def preload_unfiltered_ma():
        return agg_ma_data(preload_unfiltered_data())
    preload_unfiltered_ma()

    #create & update plots
    @dash_app.callback(
        Output('distance-scatter', 'figure'),
        Output('shot-map', 'figure'),
        Output('moving-average', 'figure'),
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

                custom_color_map = {
                    '2-pointer': 'dodgerblue',
                    '3-pointer': '#fc8d59',
                }

                fig = px.scatter(agg_dist_df,
                                x='distance',
                                y='average_made',
                                size='count_shots',
                                size_max=40, 
                                color='shot_type_label',
                                color_discrete_map=custom_color_map,  # Use the custom color map
                                # hover_name='distance',
                                labels={'distance': 'Distance (feet)', 'average_made': 'FG%', 'shot_type_label': 'Shot Type',},
                                title='Shooting Accuracy by Distance from Basket',
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
                        y=1,
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
                draw_plotly_court(shotmap_fig, fig_width=1000, margins=0)
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
                    title='Shooting Accuracy Shot Map',
                    autosize=True, 
                    margin=dict(l=0, r=0, t=30, b=0),  
                )
                return shotmap_fig
        
        def update_trend_charts(dff):

            if player_name == 'all_values' and team == 'all_values' and year == 'all_values':
                moving_avg_df = preload_unfiltered_ma()
            else:
                moving_avg_df = agg_ma_data(dff)            
            moving_avg_df=moving_avg_df.rename(columns={col: str(col) for col in moving_avg_df.columns})

            last_date = moving_avg_df.index.max()
            six_mo_ago = last_date - relativedelta(months=6)
            first_date = max(moving_avg_df.index.min(), six_mo_ago)
            print(f'first_date: {first_date}')
            date_range_index = pd.Index(pd.date_range(start=moving_avg_df.index[0], end=moving_avg_df.index[-1]).date)
            dt_breaks = date_range_index.difference(moving_avg_df.index).tolist()

            fig_moving_avg = make_subplots(
                rows=2,
                cols=1,
                shared_xaxes=True, 
                # vertical_spacing=0.1
            )

            for i, col in enumerate(['2','3'], start=1):
                average_rate = moving_avg_df[col].mean()
                above_avg = np.where(moving_avg_df[col] > average_rate, moving_avg_df[col], average_rate)
                below_avg = np.where(moving_avg_df[col] < average_rate, moving_avg_df[col], average_rate)

                fig_moving_avg.add_trace(go.Scatter(
                    x=[moving_avg_df.index.min(),moving_avg_df.index.max()],
                    y=[average_rate, average_rate],
                    mode='lines',
                    line_color="rgba(0,0,0,0)",
                    showlegend=False
                ), row=i, col=1)

                fig_moving_avg.add_trace(go.Scatter(
                    x=moving_avg_df.index,
                    y=below_avg,
                    fill='tonexty',
                    mode='none',
                    fillcolor='lightcoral',
                    showlegend=False,
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        f"{col}-pointer" + " moving average: %{y:.2%} (below average)"
                        "<extra></extra>"),
                ), row=i, col=1)

                fig_moving_avg.add_trace(go.Scatter(
                    x=[moving_avg_df.index.min(),moving_avg_df.index.max()],
                    y=[average_rate, average_rate],
                    mode='lines',
                    line_color="rgba(0,0,0,0)",
                    showlegend=False
                ), row=i, col=1)

                fig_moving_avg.add_trace(go.Scatter(
                    x=moving_avg_df.index,
                    y=above_avg,
                    fill='tonexty',
                    mode='none',
                    fillcolor='rgba(0, 109, 44, 0.4)',
                    showlegend=False,
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        f"{col}-pointer" + " moving average: %{y:.2%} (above average)"
                        "<extra></extra>"),
                ), row=i, col=1)

                fig_moving_avg.add_trace(go.Scatter(
                    x=moving_avg_df.index,
                    y=[average_rate] * len(moving_avg_df.index),
                    mode='lines',
                    line=dict(color='Black', dash='dash'),
                    showlegend=False,
                    name=f'average {col}-pointer %',
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        f"{col}-pointer" + " overall average: %{y:.2%}<extra></extra>"
                        "<extra></extra>"),
                ), row=i, col=1)

                fig_moving_avg.update_xaxes(
                    title='Date' if i == 2 else '',
                    type="date",
                    range=[six_mo_ago, last_date],
                    rangebreaks=[dict(values=dt_breaks)],
                    row=i,
                    col=1
                )
                if i == 1:
                    fig_moving_avg.update_xaxes(
                        rangeselector=dict(
                            buttons=list([
                                dict(count=7, label="1w", step="day", stepmode="backward"),
                                dict(count=1, label="1m", step="month", stepmode="backward"),
                                dict(count=6, label="6m", step="month", stepmode="backward"),
                                dict(count=1, label="YTD", step="year", stepmode="todate"),
                                dict(count=1, label="1y", step="year", stepmode="backward"),
                                dict(step="all")
                            ])
                        ),
                        row=i,
                        col=1
                    )

                fig_moving_avg.update_yaxes(
                    title=f'Moving Average',
                    tickformat='2%',
                    showgrid=True,
                    gridcolor='LightGray',
                    nticks=4,
                    row=i,
                    col=1        
                )

            fig_moving_avg.update_layout(
                title='Shooting Accuracy 3-day Moving Average',
                plot_bgcolor='white',
                height=600,
                annotations=[
                    dict(
                        yanchor="bottom",
                        y=0.95,
                        xanchor="right",
                        x=0.99,
                        xref='paper', 
                        yref='paper',
                        text='2-Pointer',
                        showarrow=False,
                        font=dict(size=12)
                    ),
                    dict(
                        yanchor="bottom",
                        y=0.45,
                        xanchor="right",
                        x=0.99,
                        xref='paper', 
                        yref='paper',
                        text='3-Pointer',
                        showarrow=False,
                        font=dict(size=12)
                    )
                ]
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
        fig_moving_avg = update_trend_charts(dff)
        print(f'ma loaded in {time.time() - start_time} sec')
        
        return scatter_fig, shot_map_fig, fig_moving_avg
