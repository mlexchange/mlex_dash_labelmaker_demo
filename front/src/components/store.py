from dash import dcc, html
import dash_bootstrap_components as dbc


def store_options():
    store_options = html.Div(
        [
            dbc.Button('Load Labels from Splash-ML', 
                       id='button-load-splash',
                       outline='True', 
                       color='success', 
                       size="sm", 
                       style={'width': '100%', 'margin-bottom': '4px'}),
            dbc.Modal(
                [
                    dbc.ModalHeader(
                        dbc.ModalTitle("Labeling versions")
                        ),
                    dbc.ModalBody(
                        dcc.Dropdown(id='event-id')
                        ),
                    dbc.ModalFooter(
                        [
                            dbc.Button("LOAD", 
                                       id="confirm-load-splash", 
                                       color='primary', 
                                       outline=False,
                                       className="ms-auto", 
                                       n_clicks=0)
                        ]
                    ),
                ], 
                id="modal-load-splash",
                is_open=False),
            dbc.Button('Save Labels to Splash-ML', 
                       id='button-save-splash',
                       outline='True', 
                       color='primary', 
                       size="sm", 
                       style={'width': '100%', 'margin-bottom': '4px'}),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Tagger ID")),
                    dbc.ModalBody(
                        [
                            dbc.Label("Entry tagger ID:"),
                            dbc.Input(id="tagger-id", 
                                      type="text")
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button("SAVE", 
                                       id="confirm-save-splash", 
                                       color='primary', 
                                       outline=False,
                                       className="ms-auto", 
                                       n_clicks=0)
                        ]
                    ), 
                ],
                id="modal-save-splash",
                is_open=False),
            dbc.Button('Download Labels to Disk', 
                       id='button-save-disk',
                       outline='True', 
                       color='primary', 
                       size="sm", 
                       style={'width': '100%'}),
            dcc.Download(id='download-out'),
            dcc.Loading(id="loading-storage",
                        type="default",
                        children=[
                            dbc.Modal(
                                [
                                    dbc.ModalBody(id='storage-body-modal'),
                                    dbc.ModalFooter(dbc.Button('OK', id='close-storage-modal'))
                                ],
                            id="storage-modal",
                            is_open=False,
                            scrollable=True
                            )
                        ]
                        )
        ]
    )
    return store_options