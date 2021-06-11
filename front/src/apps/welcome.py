# -*- coding: utf-8 -*-

import dash
import datetime
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
from flask_caching import Cache
from flask import Flask
import templates
from app import app

external_stylesheets = [dbc.themes.BOOTSTRAP]

#server = Flask(__name__)
#app = dash.Dash(__name__, external_stylesheets = external_stylesheets)

header = templates.header()
# Font and background colors associated with each theme
text_color = {"dark": "#95969A", "light": "#595959"}
card_color = {"dark": "#2D3038", "light": "#FFFFFF"}


metadata_form_layout= html.Div([
    dbc.Form(
        [dbc.FormGroup(
            [
                dbc.Label('Session Keyword', className='mr-2'),
                dbc.Input(id='session-keyword', placeholder='unobtainium', type='text'),
            ],
            className='mr-3'
            ),
        dbc.FormGroup(
            [
                dbc.Label('Technique', className='mr-2'),
                dcc.Dropdown(id='session-dropdown', 
                    options=[
                        {'label': "scattering", 'value': 'scattering'},
                        {'label': "segmenting", 'value': 'segmenting'}
                    ],
                    style={'min-width':'250px'},
                value = 'scattering',
                )
            ],
            className='mr-5'
        ),
        dbc.Button('Submit', color='primary', href='/data'),
    ],
    inline=True
    )
    ]
    )




layout = html.Div(
        [
            header,
            dbc.Container(
                [
                    metadata_form_layout,
                    #html.Div([upload_image_container()])

                ]
            )
        ]
    )

if __name__ == '__main__':
    #host option so docker container listens on all container ports for browser (lets you view the page from outside)
    app.run_server(debug = True, host = '0.0.0.0') 
