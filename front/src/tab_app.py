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
import thumbnail_tab

external_stylesheets = [dbc.themes.BOOTSTRAP]

server = Flask(__name__)
app = dash.Dash(__name__, external_stylesheets = external_stylesheets)

header = templates.header()
thumbnail_layout = thumbnail_tab.thumbnails()
# Font and background colors associated with each theme
text_color = {"dark": "#95969A", "light": "#595959"}
card_color = {"dark": "#2D3038", "light": "#FFFFFF"}




app.layout = html.Div(
        [
            header,
            dbc.Container(
                [dcc.Tabs(id='workflow-tabs', value='thumbnails', children=[
                    dcc.Tab(label='Data', value='thumbnails'),
                    dcc.Tab(label='Training', value='training'),
                ]),
                 html.Div(id='tab-layout'),
                 #   metadata_form_layout,
                    #html.Div([upload_image_container()])

                ]
            )
        ]
    )

@app.callback(Output('tab-layout', 'children'),
              Input('workflow-tabs', 'value'))
def render_content(workflow_tabs_value):
    if workflow_tabs_value == 'thumbnails':
        return thumbnail_layout
    elif workflow_tabs_value == 'training':
        return html.H2("Training")
    

if __name__ == '__main__':
    #host option so docker container listens on all container ports for browser (lets you view the page from outside)
    app.run_server(debug = True, host = '0.0.0.0') 
