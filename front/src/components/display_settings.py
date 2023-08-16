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
        ]
    )
    return display_settings