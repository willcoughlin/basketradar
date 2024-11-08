import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import Output, Input, dcc, html
from utils import draw_plotly_court
import pandas as pd

distance_scatter = dcc.Graph(id='distance-scatter')
moving_average_2pt = dcc.Graph(id='moving-average-2pt')
moving_average_3pt = dcc.Graph(id='moving-average-3pt')

shot_map = dcc.Graph(id='shot-map')
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
        ## dff query with transformations directly in SQL
        sql_query_dff = """
        SELECT shot_type, 
            distance, 
            made, 
            shotX, 
            shotY,
            -- Coordinate transformations directly in SQL
            ((shotX - 0) / (50 - 0)) * (250 - (-250)) + (-250) AS shotX_,
            ((shotY - 0) / (47 - 0)) * (417.5 - (-52.5)) + (-52.5) AS shotY_
        FROM shots
        WHERE
            (? = 'all_values' OR player = ?)
            AND (? = 'all_values' OR team = ?)
            AND (? = 'all_values' OR substr(date, 7, 4) = ?)
        """
        
        sql_query_agg_df = """
        SELECT 
            shot_type, 
            distance, 
            AVG(made) AS average_made,  -- Average of 'made'
            COUNT(*) AS count_shots  
        FROM 
            shots
        WHERE
            (? = 'all_values' OR player = ?)
            AND (? = 'all_values' OR team = ?)
            AND (? = 'all_values' OR substr(date, 7, 4) = ?)
        GROUP BY 
            shot_type, distance
        """
        ### params list
        params = [player_name, player_name, team, team, year, year]

        ### store in pandas df
        dff = pd.read_sql(sql_query_dff, conn, params=params)
        agg_df = pd.read_sql(sql_query_agg_df,conn,params=params)
        print(agg_df.head(2))

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

        def update_shot_map(dff=dff, metric=metric):
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
            query = """
            WITH DailyAverages AS (
                SELECT 
                    date,
                    player,
                    team,
                    shot_type,
                    COUNT(*) AS total_shots,  -- Total number of shots made for the day
                    SUM(made) AS shots_made,  -- Total shots made for the day
                    -- Calculate the shooting average (made / total shots) for the day
                    CAST(SUM(made) AS FLOAT) / COUNT(*) AS daily_shooting_avg
                FROM shots
                WHERE 
                    shot_type = ?  -- Filter by shot type
                    AND (? = 'all_values' OR player = ?)  -- Filter by player
                    AND (? = 'all_values' OR team = ?)  -- Filter by team
                    AND (? = 'all_values' OR SUBSTR(date, 7, 4) = ?)  -- Filter by year (extracted from date)
                GROUP BY date, player, team, shot_type  -- Group by day, player, team, and shot type
            ),
            MovingAverage AS (
                SELECT 
                    date,
                    player,
                    team,
                    shot_type,
                    daily_shooting_avg,  -- Daily shooting average
                    AVG(daily_shooting_avg) OVER (PARTITION BY player ORDER BY date ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS moving_avg,  -- 3-day moving average for shooting average
                    AVG(daily_shooting_avg) OVER () AS overall_avg,  -- Overall average of shooting percentage
                    ROW_NUMBER() OVER (PARTITION BY player ORDER BY date) AS row_num  -- Ensure correct ordering for moving average
                FROM DailyAverages
            )
            SELECT 
                date, 
                player,
                team,
                shot_type,
                daily_shooting_avg,  -- Shooting average for the day
                moving_avg,  -- 3-day moving average for shooting average
                overall_avg,
                -- Apply color coding based on moving_avg vs overall_avg
                CASE
                    WHEN moving_avg < overall_avg THEN 'lightcoral'
                    ELSE 'palegreen'
                END AS marker_color
            FROM MovingAverage
            WHERE row_num >= 3  -- Only include rows where there are at least 3 shots for moving average calculation
            """

            ### query params
            params = [point_value, player_name, player_name, team, team, year, year]

            ## store results in a dataframe
            agg_df_filtered = pd.read_sql(query, conn, params)

            # # Filter the aggregated data for the given shot type
            # agg_df_filtered = agg_df[agg_df['shot_type'] == point_value_str]
            # # Calculate the overall average for the shot type
            # average_rate = agg_df_filtered['average_made'].mean()

            # # Determine marker color based on moving average vs average rate
            # agg_df_filtered['marker_color'] = np.where(
            #     agg_df_filtered['moving_avg'] < average_rate, 'lightcoral',
            #     np.where(agg_df_filtered['moving_avg'] > average_rate, 'palegreen', 'lightgray')
            # )

            # Plotting the moving average trend
            fig_moving_avg = go.Figure()

            # Add moving average trace
            fig_moving_avg.add_trace(go.Scatter(
                x=agg_df_filtered['date'],
                y=agg_df_filtered['moving_avg'],
                mode='lines+markers',
                marker=dict(size=10, color=agg_df_filtered['marker_color']),
                line=dict(color='black'),
                name=f'3-day moving average of {point_value_str} %',
                hovertemplate="3-day moving average: %{y:.2%}"
                            "<extra></extra>"
            ))

            # Add the overall average line
            fig_moving_avg.add_trace(go.Scatter(
                x=[agg_df_filtered['date'].min(), agg_df_filtered['date'].max()],
                y=[average_rate, average_rate],
                mode='lines',
                line=dict(color='LightGray', dash='dash'),
                name=f'average {point_value_str} %',
            ))

            # Update y-axis properties
            fig_moving_avg.update_yaxes(
                title='Accuracy',
                tickformat='2%',
                showgrid=True, 
                gridcolor='LightGray',
                dtick=0.2
            )

            # Update x-axis properties
            fig_moving_avg.update_xaxes(
                tickformat="%m/%d/%Y", 
            )

            # Layout settings
            fig_moving_avg.update_layout(
                title=f'Moving Average {point_value}-Point Percentage',
                xaxis_title='Date', 
                yaxis_title='Percentage', 
                yaxis=dict(range=[0, 1], autorange=False),
                plot_bgcolor='white',
                hovermode='x unified'
            )

            return fig_moving_avg

        scatter_fig = update_scatter(dff, agg_df)
        shot_map_fig = update_shot_map(dff, metric)
        fig_moving_avg_2pt = update_trend_charts(dff, 2)
        fig_moving_avg_3pt = update_trend_charts(dff, 3)
        
        return scatter_fig, shot_map_fig, fig_moving_avg_2pt, fig_moving_avg_3pt
