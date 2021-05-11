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

external_stylesheets = [dbc.themes.BOOTSTRAP]

server = Flask(__name__)
app = dash.Dash(__name__, external_stylesheets = external_stylesheets)

header = templates.header()
# Font and background colors associated with each theme
text_color = {"dark": "#95969A", "light": "#595959"}
card_color = {"dark": "#2D3038", "light": "#FFFFFF"}

#def label_uploaded_images(contents, filename, date):
#    return dbc.Card(
#            [
#                dbc.CardImg(src = contents, top = True),
#                dbc.CardBody(
#                    [
#                        html.H4(filename, className = 'card-title'),
#                        dbc.FormGroup(
#                            [
#                                dbc.Label("Class Labels", width = 3),
#                                dbc.Col([
#                                    dbc.RadioItems(
#                                        id="label_select",
#                                        options = [
#                                            {'label': 'Good', 'value' : 'good'},
#                                            {'label': 'Bad', 'value' : 'bad'},
#                                            ],
#                                        value = 'good',
#                                        persistence = True, persistence_type = 'session'
#                                        ),
#                                    ]),
#                                    ]),
#                                dbc.Col([
#                                    dbc.Button('Label!', className = 'mr-2', id = 'label-button')
#                                ])
#                            ])
#                    ])
#
#def parse_uploaded_images(contents, filename, date):
#
#    return html.Div([
#        html.H5(filename),
#        html.H6(datetime.datetime.fromtimestamp(date)),
#
#        html.Img(src = contents),
#        html.Hr(),
#        html.Div('Raw Content'),
#        html.Pre(contents[0:4] + '...', style = {
#            'whiteSpace': 'pre-wrap',
#            'wordBreak': 'break-all'
#            })
#        ])
#
#
#@app.callback(Output('output-image-upload', 'children'),
#        Input('upload-image', 'contents'),
#        State('upload-image', 'filename'),
#        State('upload-image', 'last_modified'))
#def update_images(list_of_contents, list_of_names, list_of_dates):
#    if list_of_contents is not None:
#        children = [
#                label_uploaded_images(c, n, d) for c, n, d in
#                zip(list_of_contents, list_of_names, list_of_dates)]
#        return children
#
#@server.route('/blimages', methods=['GET'])
#def update_images_endpoint():
#    print('called endpoint')
#    return html.Div(children = 'Hello there')
#    #update_images([1,2,3],['1','1','1'], [12321, 123543, 129403])
#


#def upload_image_container():
#    return dbc.Card(
#        html.Div([
#            dcc.Upload(
#                id = 'upload-image',
#                children = html.Div([
#                'Drag and Drop or ',
#                html.A('Select Files')
#                ]),
#                style = {
#                    'width': '50%',
#                    'height': '60px',
#                    'lineHeight': '60px',
#                    'borderWidth': '1px',
#                    'borderStyle': 'dashed',
#                    'borderRadius': '5px',
#                    'textAlign': 'center',
#                    'margin': '10px'
#                    },
#                multiple = True
#                ),
#            html.Div(id = 'output-image-upload'),
#            ])
#        )
#

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
        dbc.Button('Submit', color='primary'),
    ],
    inline=True
    )
    ]
    )
#ml_parameter_controls = dbc.Card(
#        [
#            dbc.FormGroup(
#                [
#                    dbc.Label
app.layout = html.Div(
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
