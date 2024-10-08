import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import dcc, html
from dash_extensions import EventListener

from src.utils.plot_utils import create_label_component

LABEL_LIST = {"Label_1": [], "Label_2": []}


def label_method():
    label_method = html.Div(
        [
            html.Div(
                [
                    dbc.RadioItems(
                        id="tab-group",
                        className="btn-group",
                        inputClassName="btn-check",
                        labelClassName="btn btn-outline-primary",
                        labelCheckedClassName="active",
                        labelStyle={
                            "font-size": "13px",
                            "margin": "1px",
                            "width": "100%",  # "width": "85px",
                        },
                        options=[
                            {"label": "Manual", "value": "manual"},
                            {"label": "Similarity", "value": "similarity"},
                            {"label": "Probability", "value": "probability"},
                        ],
                        style={"width": "100%"},
                        value="manual",
                    )
                ],
                className="radio-group",
                style={"font-size": "0.5px", "margin-bottom": "10px"},
            ),
            # Labeling with Probabilities
            dbc.Collapse(
                children=[
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Button(
                                    "Go to MLCoach",
                                    id="goto-webpage",
                                    outline="True",
                                    color="primary",
                                    size="sm",
                                    n_clicks=0,
                                    style={
                                        "width": "100%",
                                        "margin-bottom": "1rem",
                                        "margin-top": "0.5rem",
                                    },
                                ),
                                width=11,
                                style={"margin-right": "2%", "width": "90%"},
                            ),
                            dbc.Col(
                                dbc.Button(
                                    className="fa fa-question",
                                    id="tab-help-button",
                                    outline="True",
                                    color="primary",
                                    size="sm",
                                    style={
                                        "width": "100%",
                                        "margin-bottom": "1rem",
                                        "margin-top": "0.5rem",
                                    },
                                ),
                                width=1,
                                style={"width": "8%"},
                            ),
                        ],
                        className="g-0",
                    )
                ],
                id="goto-webpage-collapse",
                is_open=False,
            ),
            dbc.Collapse(
                children=[
                    dbc.Row(
                        [
                            dbc.Col(
                                dcc.Input(
                                    id="add-label-name",
                                    placeholder="Input new label here",
                                    style={
                                        "width": "100%",
                                        "margin-bottom": "10px",
                                        "margin-top": "5px",
                                    },
                                ),
                                width=8,
                            ),
                            dbc.Col(
                                dbc.Button(
                                    "Add Label",
                                    id="modify-list",
                                    outline="True",
                                    size="sm",
                                    color="primary",
                                    n_clicks=0,
                                    style={
                                        "width": "100%",
                                        "margin-bottom": "10px",
                                        "margin-top": "5px",
                                    },
                                ),
                                width=4,
                            ),
                        ],
                        justify="center",
                    )
                ],
                id="manual-collapse",
                is_open=False,
            ),
            # manual tab is default button group
            dbc.Collapse(
                children=html.Div(
                    id="label-buttons",
                    children=create_label_component(LABEL_LIST.keys()),
                    style={"margin-bottom": "0.5rem"},
                ),
                id="label-buttons-collapse",
                is_open=False,
            ),
            # Labeling with Probabilities
            dbc.Collapse(
                children=[
                    dbc.Label("Trained models:"),
                    dbc.Row(
                        [
                            dbc.Col(dcc.Dropdown(id="probability-model-list"), width=8),
                            dbc.Col(
                                dbc.Button(
                                    "Refresh",
                                    id="probability-model-refresh",
                                    outline="True",
                                    color="primary",
                                    size="sm",
                                    style={"width": "100%", "margin-top": "1px"},
                                )
                            ),
                        ]
                    ),
                    dbc.Label(
                        "Probability Threshold",
                        style={"width": "100%", "margin-top": "20px"},
                    ),
                    dcc.Dropdown(id="probability-label-name"),
                    dcc.Slider(
                        id="probability-threshold",
                        min=0,
                        max=100,
                        value=51,
                        tooltip={"placement": "top", "always_visible": True},
                        marks={0: "0", 25: "25", 50: "50", 75: "75", 100: "100"},
                    ),
                    dbc.Button(
                        "Label with Threshold",
                        id="probability-label",
                        outline="True",
                        color="primary",
                        size="sm",
                        style={"width": "100%", "margin-top": "20px"},
                    ),
                ],
                id="probability-collapse",
                is_open=False,
            ),
            # Labeling with similarity-based search
            dbc.Collapse(
                children=[
                    dbc.Label("Trained models:"),
                    dbc.Row(
                        [
                            dbc.Col(dcc.Dropdown(id="similarity-model-list"), width=8),
                            dbc.Col(
                                dbc.Button(
                                    "Refresh",
                                    id="similarity-model-refresh",
                                    outline="True",
                                    color="primary",
                                    size="sm",
                                    style={"width": "100%", "margin-top": "1px"},
                                )
                            ),
                        ]
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Button(
                                    "Find Similar Images",
                                    id="find-similar-unsupervised",
                                    outline="True",
                                    color="primary",
                                    size="sm",
                                    style={"width": "100%", "margin-top": "20px"},
                                )
                            ),
                            dbc.Col(
                                dbc.Button(
                                    "Stop Find Similar Images",
                                    id="exit-similar-unsupervised",
                                    outline="True",
                                    color="primary",
                                    size="sm",
                                    style={"width": "100%", "margin-top": "20px"},
                                )
                            ),
                        ],
                    ),
                    daq.Indicator(
                        id="similarity-on-off-indicator",
                        label="Find Similar Images: OFF",
                        color="#596D4E",
                        size=30,
                        style={"margin-top": "20px", "margin-bottom": "20px"},
                    ),
                ],
                id="similarity-collapse",
                is_open=False,
            ),
            dbc.Button(
                "Unlabel All",
                id="un-label-all",
                outline="True",
                color="danger",
                size="sm",
                style={"width": "100%", "margin-bottom": "4px", "margin-top": "4px"},
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Warning")),
                    dbc.ModalBody(
                        id="un-label-warning",
                        children="Unsaved labels cannot be recovered after clearing data. Do \
                          you still want to proceed?",
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "YES",
                                id="confirm-un-label-all",
                                color="danger",
                                outline=False,
                                className="ms-auto",
                                n_clicks=0,
                            ),
                        ]
                    ),
                ],
                id="modal-un-label",
                is_open=False,
                style={"color": "red"},
            ),
            dbc.Modal(
                id="modal-help",
                children=[
                    dbc.ModalHeader(dbc.ModalTitle("Help")),
                    dbc.ModalBody(id="help-body"),
                ],
            ),
            EventListener(
                events=[
                    {
                        "event": "keydown",
                        "props": ["key", "ctrlKey", "timeStamp"],
                        "repeat": True,
                    }
                ],
                id="keybind-event-listener",
                logging=True,
            ),
        ]
    )
    return label_method
