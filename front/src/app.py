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
app = dash.Dash(__name__, external_stylesheets = external_stylesheets, suppress_callback_exceptions=True)

