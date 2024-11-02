import dash_bootstrap_components as dbc
from dash import html

navbar = dbc.Navbar(
    dbc.Container(
        [
            html.Div(
                dbc.Row(
                    [
                        dbc.Col(html.Img(src="https://basketradarstorage.blob.core.windows.net/misc/icon-dark.png", height="30px")),
                        dbc.Col(dbc.NavbarBrand("BasketRadar", className="ms-2")),
                    ],
                    align="center",
                    className="g-0",
                ),
            )
        ],
        fluid=True
    ),
    dark=True,
    color="dark"
)