import dash_bootstrap_components as dbc
from dash import dcc, html


def display_settings():
    display_settings = html.Div(
        [
            dbc.Label("Number of Thumbnail Columns"),
            dcc.Slider(1, 6, 1, value=6, id="thumbnail-num-cols"),
            dbc.Label("Number of Thumbnail Rows"),
            dcc.Slider(1, 6, 1, value=3, id="thumbnail-num-rows"),
            dbc.Button(
                "Sort",
                id="button-sort",
                outline="True",
                color="primary",
                size="sm",
                n_clicks=0,
                style={"width": "100%", "margin-top": "20px", "margin-bottom": "4px"},
            ),
            dbc.Tooltip(
                "Sort images according to assigned label",
                target="button-sort",
                placement="top",
            ),
            dbc.Button(
                "Hide",
                id="button-hide",
                outline="True",
                color="primary",
                size="sm",
                n_clicks=0,
                style={"width": "100%", "margin-bottom": "4px"},
            ),
            dbc.Tooltip(
                "Hide/unhide labeled images", target="button-hide", placement="top"
            ),
        ]
    )
    return display_settings
