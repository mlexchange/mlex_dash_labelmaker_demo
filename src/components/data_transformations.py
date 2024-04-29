import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import html


def data_transformations():
    display_settings = html.Div(
        [
            dbc.Label("Log Transform"),
            daq.BooleanSwitch(
                id="log-transform",
                on=False,
            ),
        ]
    )
    return display_settings
