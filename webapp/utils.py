# from https://gist.github.com/jpolarizing/17a8ceb6d49d45140ebbcea6f59c73ac

def draw_plotly_court_orig_coords(fig, fig_width=800, margins=1):
    # uses original x and y coordinate ranges, but currently getting incorrect basketball court 
    import numpy as np

    # Function to generate an arc path for ellipses
    def ellipse_arc(x_center=0.0, y_center=0.0, a=10.5, b=10.5, start_angle=0.0, end_angle=2 * np.pi, N=200, closed=False):
        t = np.linspace(start_angle, end_angle, N)
        x = x_center + a * np.cos(t)
        y = y_center + b * np.sin(t)
        path = f'M {x[0]}, {y[0]}'
        for k in range(1, len(t)):
            path += f'L{x[k]}, {y[k]}'
        if closed:
            path += ' Z'
        return path

    fig_height = fig_width * (48 + 2 * margins) / (50 + 2 * margins)
    fig.update_layout(width=fig_width, height=fig_height)

    # Set axes ranges to 0-50 (x) and 0-48 (y)
    fig.update_xaxes(range=[0 - margins, 50 + margins])
    fig.update_yaxes(range=[0 - margins, 48 + margins])

    threept_break_y = 19.5
    three_line_col = "#777777"
    main_line_col = "#777777"

    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor="white",
        plot_bgcolor="white",
        yaxis=dict(
            scaleanchor="x",
            scaleratio=1,
            showgrid=False,
            zeroline=False,
            showline=False,
            ticks='',
            showticklabels=False,
            fixedrange=True,
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=False,
            ticks='',
            showticklabels=False,
            fixedrange=True,
        ),
        # Add court shapes
        shapes=[
            # Outer court border
            dict(type="rect", x0=0, y0=0, x1=50, y1=47, line=dict(color=main_line_col, width=1)),
            # Paint area
            dict(type="rect", x0=19, y0=0, x1=31, y1=19, line=dict(color=main_line_col, width=1)),
            dict(type="rect", x0=21, y0=0, x1=29, y1=19, line=dict(color=main_line_col, width=1)),
            # Hoop
            dict(type="circle", x0=23.5, y0=4.5, x1=26.5, y1=7.5, xref="x", yref="y", line=dict(color="#ec7607", width=1)),
            # Backboard
            dict(type="rect", x0=24.5, y0=4, x1=25.5, y1=3.5, line=dict(color="#ec7607", width=1), fillcolor="#ec7607"),
            # Free throw arc
            dict(type="circle", x0=19, y0=19, x1=31, y1=29, line=dict(color=main_line_col, width=1)),
            # Free throw line
            dict(type="line", x0=19, y0=19, x1=31, y1=19, line=dict(color=main_line_col, width=1)),
            # Three-point arc
            dict(type="path", path=ellipse_arc(x_center=25, y_center=5, a=23.75, b=23.75, start_angle=0.3863, end_angle=2.755), line=dict(color=three_line_col, width=1)),
            # Three-point lines (left and right)
            dict(type="line", x0=3.3, y0=0, x1=3.3, y1=threept_break_y, line=dict(color=three_line_col, width=1)),
            dict(type="line", x0=46.7, y0=0, x1=46.7, y1=threept_break_y, line=dict(color=three_line_col, width=1)),
            # Restricted area
            dict(type="path", path=ellipse_arc(x_center=25, y_center=5, a=4, b=4, start_angle=0, end_angle=np.pi), line=dict(color=main_line_col, width=1)),
            # Top key arc
            dict(type="path", path=ellipse_arc(x_center=25, y_center=47, a=6, b=6, start_angle=-np.pi, end_angle=0), line=dict(color=main_line_col, width=1)),
        ]
    )
    return True

def draw_plotly_court(fig, fig_width=600, margins=10):
    import numpy as np
        
    # Define an ellipse arc function
    def ellipse_arc(x_center=0.0, y_center=0.0, a=10.5, b=10.5, start_angle=0.0, 
                    end_angle=2 * np.pi, N=200, closed=False):
        t = np.linspace(start_angle, end_angle, N)  # Generate angles
        x = x_center + a * np.cos(t)                # X coordinates
        y = y_center + b * np.sin(t)                # Y coordinates
        path = f'M {x[0]}, {y[0]}'                   # Move to start point
        for k in range(1, len(t)):
            path += f'L{x[k]}, {y[k]}'               # Create line to each point
        if closed:
            path += ' Z'                             # Close the path if needed
        return path

    # Set figure dimensions
    fig_height = fig_width * (470 + 2 * margins) / (500 + 2 * margins) 
    fig.update_layout(width=fig_width, height=fig_height)

    # Set axes ranges
    fig.update_xaxes(range=[-250 - margins, 250 + margins])
    fig.update_yaxes(range=[-52.5 - margins, 417.5 + margins])

    # Define colors and y-coordinate for the three-point line break
    threept_break_y = 89.47765084
    three_line_col = "#777777"
    main_line_col = "#777777"

    # Update layout settings
    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        yaxis=dict(scaleanchor="x", scaleratio=1, showgrid=False, zeroline=False,
                   showline=False, ticks='', showticklabels=False, fixedrange=True),
        xaxis=dict(showgrid=False, zeroline=False, showline=False, ticks='',
                   showticklabels=False, fixedrange=True),
        shapes=[
            # Outer court rectangle
            dict(type="rect", x0=-250, y0=-52.5, x1=250, y1=417.5,
                 line=dict(color=main_line_col, width=1), layer='above'),
            # Key area rectangles
            dict(type="rect", x0=-80, y0=-52.5, x1=80, y1=137.5,
                 line=dict(color=main_line_col, width=1), layer='above'),
            dict(type="rect", x0=-60, y0=-52.5, x1=60, y1=137.5,
                 line=dict(color=main_line_col, width=1), layer='above'),
            # Free-throw circle
            dict(type="circle", x0=-60, y0=77.5, x1=60, y1=197.5, 
                 xref="x", yref="y", line=dict(color=main_line_col, width=1), 
                 layer='above'),
            # Free-throw line
            dict(type="line", x0=-60, y0=137.5, x1=60, y1=137.5,
                 line=dict(color=main_line_col, width=1), layer='above'),
            # Additional shapes for three-point line and more
            dict(type="rect", x0=-2, y0=-7.25, x1=2, y1=-12.5,
                 line=dict(color="#ec7607", width=1)),
            dict(type="circle", x0=-7.5, y0=-7.5, x1=7.5, y1=7.5, 
                 xref="x", yref="y", line=dict(color="#ec7607", width=1)),
            dict(type="line", x0=-30, y0=-12.5, x1=30, y1=-12.5,
                 line=dict(color="#ec7607", width=1)),
            # Ellipse arcs for three-point line
            dict(type="path", path=ellipse_arc(a=40, b=40, start_angle=0, end_angle=np.pi),
                 line=dict(color=main_line_col, width=1), layer='above'),
            dict(type="path", path=ellipse_arc(a=237.5, b=237.5, 
                 start_angle=0.386283101, end_angle=np.pi - 0.386283101),
                 line=dict(color=main_line_col, width=1), layer='above'),
            # Three-point lines
            dict(type="line", x0=-220, y0=-52.5, x1=-220, y1=threept_break_y,
                 line=dict(color=three_line_col, width=1), layer='above'),
            dict(type="line", x0=220, y0=-52.5, x1=220, y1=threept_break_y,
                 line=dict(color=three_line_col, width=1), layer='above'),
            # Other court lines
            dict(type="line", x0=-250, y0=227.5, x1=-220, y1=227.5,
                 line=dict(color=main_line_col, width=1), layer='above'),
            dict(type="line", x0=250, y0=227.5, x1=220, y1=227.5,
                 line=dict(color=main_line_col, width=1), layer='above'),
            # dict(type="line", x0=-90, y0=17.5, x1=-80, y1=17.5,
            #      line=dict(color=main_line_col, width=1), layer='above'),
            # dict(type="line", x0=90, y0=17.5, x1=80, y1=17.5,
            #      line=dict(color=main_line_col, width=1), layer='above'),
            # Arc at the top of the court
            dict(type="path", path=ellipse_arc(y_center=417.5, a=60, b=60,
                 start_angle=-0, end_angle=-np.pi),
                 line=dict(color=main_line_col, width=1), layer='above'),
        ]
    )
    return True
