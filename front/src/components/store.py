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
                dbc.Button('Save Labels to Splash-ML', 
                                id='button-save-splash',
                                outline='True', 
                                color='primary', 
                                size="sm", 
                                style={'width': '100%', 'margin-bottom': '4px'}),
                dbc.Button('Save Labels to Disk', 
                                id='button-save-disk',
                                outline='True', 
                                color='primary', 
                                size="sm", 
                                style={'width': '100%'}),
                dcc.Loading(id="loading-storage",
                                type="default",
                                children=dbc.Modal([
                                        dbc.ModalBody(id='storage-body-modal'),
                                        dbc.ModalFooter(dbc.Button('OK', id='close-storage-modal'))
                                        ],
                                        id="storage-modal",
                                        is_open=False,
                                        scrollable=True
                                        )
                                )
                ]
        )
        return store_options