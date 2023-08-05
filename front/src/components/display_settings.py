from dash import dcc, html
import dash_bootstrap_components as dbc


def display_settings():
    display_settings = html.Div(
        [
            dbc.Label('Number of Thumbnail Columns'),
            dcc.Slider(1,5,1,
                       value=4,
                       id='thumbnail-slider'),
            dbc.Button('Sort', 
                       id='button-sort', 
                       outline="True",
                       color='primary', 
                       size="sm", 
                       style={'width': '100%', 'margin-top': '20px', 'margin-bottom': '4px'}),
            dbc.Button('Hide', 
                       id='button-hide', 
                       outline='True',
                       color='primary', 
                       size="sm", 
                       style={'width': '100%', 'margin-bottom': '4px'}),
            dbc.Button('Unlabel All', 
                       id='un-label-all', 
                       outline='True',
                       color='danger', 
                       size="sm", 
                       style={'width': '100%', 'margin-bottom': '4px'}),
            dbc.Modal([
                dbc.ModalHeader(dbc.ModalTitle("Warning")),
                dbc.ModalBody(id="un-label-warning",
                              children="Unsaved labels cannot be recovered after clearing data. Do \
                                        you still want to proceed?"),
                dbc.ModalFooter([
                    dbc.Button(
                        "YES", id="confirm-un-label-all", 
                        color='danger', 
                        outline=False,
                        className="ms-auto", 
                        n_clicks=0),
                ]),
            ], id="modal-un-label",
               is_open=False,
               style = {'color': 'red'}
            )
        ]
    )
    return display_settings