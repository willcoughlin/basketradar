import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import Output, Input, dcc, html
from utils import draw_plotly_court
import pandas as pd
import time

distance_scatter = dcc.Loading(dcc.Graph(id='distance-scatter'))
moving_average_2pt = dcc.Loading(dcc.Graph(id='moving-average-2pt'))
moving_average_3pt = dcc.Loading(dcc.Graph(id='moving-average-3pt'))

shot_map = dcc.Loading(dcc.Graph(id='shot-map'))
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

def create_plot_callbacks(dash_app, conn):
    #create & update plots
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
        sql_query = f"""
            select
                shot_type, 
                distance, 
                made, 
                shotX, 
                shotY,
                date
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

        start_time = time.time()
        dff = pd.read_sql(sql_query, conn, params=params) if len(params) > 0 else pd.read_sql(sql_query, conn)
        dff['shotX_'] = dff['shotX'] / 50 * 500 - 250
        dff['shotY_'] = dff['shotY'] / 47 * 470 - 52.5
        print(f'DF loaded in {time.time() - start_time} sec')

        start_time = time.time()
        agg_df = dff.groupby(['distance', 'shot_type']).agg(
            average_made=('made', 'mean'),
            count_shots=('made', 'count')
        ).reset_index()
        agg_df['shot_type_label'] = agg_df.shot_type.astype(str) + '-pointer'
        print(f'DF aggregated in {time.time() - start_time} sec')

        def update_scatter(dff, agg_df):
            if dff.empty:
                return px.scatter(title="No data available for the selected filters.")
            fig = px.scatter(agg_df,
                            x='distance',
                            y='average_made',
                            size='count_shots',
                            size_max=40, 
                            color='shot_type_label',
                            hover_name='distance',
                            labels={'average_made': 'Accuracy', 'shot_type_label': 'Shot Type',},
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
                z=dff['made'],
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
            # point_value_str = f'{point_value}-pointer'
            # dfff=dff[dff['shot_type']==point_value]

            # avg_df = dfff[['date', 'made']].groupby('date').mean()
            # moving_avg_df = avg_df.rolling(window=3).mean().reset_index()
            # average_rate = dfff['made'].mean()
            # moving_avg_df['marker_color'] = np.where(
                # moving_avg_df['made'] < average_rate, 'lightcoral',
                # np.where(moving_avg_df['made'] > average_rate, 'palegreen', 'lightgray')
            # )

            fig_moving_avg = go.Figure()
            # fig_moving_avg.add_trace(go.Scatter(
            #     x=moving_avg_df['date'],
            #     y=moving_avg_df['made'],
            #     mode='lines+markers',
            #     marker=dict(size=10, color=moving_avg_df['marker_color']),
            #     line=dict(color='black'),
            #     name=f'3-day moving average of {point_value_str} %',
            #     hovertemplate="3-day moving average: %{y:.2%}"
            #                     "<extra></extra>"
            # ))
            # fig_moving_avg.add_trace(go.Scatter(
            #     x=[moving_avg_df['date'].min(),moving_avg_df['date'].max()],
            #     y=[average_rate, average_rate],
            #     mode='lines',
            #     line=dict(color='LightGray', dash='dash'),
            #     name=f'average {point_value_str} %',
            # ))
            # fig_moving_avg.update_yaxes(
            #             title='Accuracy',
            #             tickformat='2%',
            #             showgrid=True, 
            #             gridcolor='LightGray',
            #             dtick=0.2
            #         )
            # fig_moving_avg.update_xaxes(
            #     tickformat="%m/%d/%Y", 
            # )
            # fig_moving_avg.update_layout(title=f'Moving Average {point_value}-Point Percentage',
            #                             xaxis_title='Date', 
            #                             yaxis_title='Percentage', 
            #                             yaxis=dict(range=[0, 1], autorange=False),
            #                             plot_bgcolor='white',
            #                             hovermode='x unified')

            return fig_moving_avg

        start_time = time.time()
        scatter_fig = update_scatter(dff, agg_df)
        print(f'scatter loaded in {time.time() - start_time} sec')
        start_time = time.time()
        shot_map_fig = update_shot_map(dff, metric)
        print(f'shot map loaded in {time.time() - start_time} sec')
        fig_moving_avg_2pt = update_trend_charts(dff, 2)
        fig_moving_avg_3pt = update_trend_charts(dff, 3)
        
        return scatter_fig, shot_map_fig, fig_moving_avg_2pt, fig_moving_avg_3pt
