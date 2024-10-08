import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import html


def display():
    display = html.Div(
        [
            dbc.Row(
                [
                    dbc.Button(
                        className="fa fa-step-backward",
                        id="first-page",
                        style={"width": "5%"},
                        disabled=True,
                    ),
                    dbc.Button(
                        className="fa fa-chevron-left",
                        id="prev-page",
                        style={"width": "5%"},
                        disabled=True,
                    ),
                    dbc.Input(
                        id="current-page",
                        value=0,
                        type="number",
                        style={"width": "8%"},
                        debounce=True,
                    ),
                    dbc.Button(
                        className="fa fa-chevron-right",
                        id="next-page",
                        style={"width": "5%"},
                        disabled=True,
                    ),
                    dbc.Button(
                        className="fa fa-step-forward",
                        id="last-page",
                        style={"width": "5%"},
                        disabled=True,
                    ),
                ],
                justify="center",
                style={"margin-top": "1%"},
            ),
            dbc.Modal(
                id={"type": "full-screen-modal", "index": 0},
                size="xl",
                centered=True,
                is_open=False,
            ),
            dbc.Modal(
                id="color-picker-modal",
                children=[
                    dbc.Input(
                        id="modify-label-name",
                        value="",
                        placeholder="Type new label name",
                        style={"width": "100%", "margin-top": "1rem"},
                    ),
                    daq.ColorPicker(
                        id="label-color-picker",
                        label="Choose label color",
                        value=dict(hex="#119DFF"),
                    ),
                    dbc.Button(
                        "Submit", id="modify-label-button", style={"width": "100%"}
                    ),
                ],
                is_open=False,
            ),
        ]
    )
    return display
