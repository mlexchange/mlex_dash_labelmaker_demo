import dash_bootstrap_components as dbc
from dash import dcc, html

from src.utils.mask_utils import get_mask_options


def data_transformations():
    display_settings = html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(dbc.Label("Log Transform"), width=4, align="start"),
                    dbc.Col(
                        dbc.Switch(
                            id="log-transform",
                            value=False,
                            label_style={"display": "none"},
                            style={"height": "20px"},
                        ),
                        align="start",
                    ),
                ],
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Label("Min-Max Percentile"),
                        width=4,
                    ),
                    dbc.Col(
                        dcc.RangeSlider(
                            id="min-max-percentile",
                            min=0,
                            max=100,
                            tooltip={
                                "placement": "bottom",
                                "always_visible": True,
                            },
                        ),
                    ),
                ],
                style={"margin-bottom": "10px"},
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Label("Mask Selection"),
                        width=4,
                    ),
                    dbc.Col(
                        dcc.Dropdown(
                            id="mask-dropdown",
                            options=get_mask_options(),
                        ),
                    ),
                ]
            ),
        ]
    )
    return display_settings
