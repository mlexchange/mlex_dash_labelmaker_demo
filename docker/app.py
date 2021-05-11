# -*- coding: utf-8 -*-

import dash
import dash_core_components as dcc
import dash_html_componets as html
import plotly.express as px
import pandas as pd

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWlwgP.css']

app = dash.Dash(__name__, external_stylesheets = external_stylesheets)

app.layout = html.Div(children = [
    html.H1(children = "LabelMaker v0.1"),

    html.Div(children = '''
    An ML workflow for labelling your data
    '''
    ),

)
])

if __name__ = '__main__':
    app.run_server(debug = True)
