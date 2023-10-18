import os
import dash
from dash import dcc, html
from dash.long_callback import DiskcacheLongCallbackManager
import dash_bootstrap_components as dbc
import dash_uploader as du
import diskcache
from flask import Flask
import pathlib

from file_manager.main import FileManager
from components.label_method import label_method
from components.store import store_options
from components.display_settings import display_settings
from components.display import display
from components.browser_cache import browser_cache
from components.header import header

cache = diskcache.Cache("./cache")
long_callback_manager = DiskcacheLongCallbackManager(cache)

external_stylesheets = [
    dbc.themes.BOOTSTRAP, 
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css',
    '../assets/labelmaker-style.css'
    ]
server = Flask(__name__)
app = dash.Dash(__name__, 
                external_stylesheets = external_stylesheets,
                suppress_callback_exceptions=True, 
                long_callback_manager=long_callback_manager)

MLCOACH_URL = str(os.environ['MLCOACH_URL'])
DATA_CLINIC_URL = str(os.environ['DATA_CLINIC_URL'])
SPLASH_URL = str(os.environ['SPLASH_URL'])
MLEX_COMPUTE_URL = str(os.environ['MLEX_COMPUTE_URL'])
TILED_KEY = str(os.environ['TILED_KEY'])
DOCKER_DATA = pathlib.Path.home() / 'data'
UPLOAD_FOLDER_ROOT = DOCKER_DATA / 'upload'
USER = 'admin'
NUMBER_OF_ROWS = 4

dash_file_explorer = FileManager(DOCKER_DATA, 
                                 UPLOAD_FOLDER_ROOT, 
                                 api_key=TILED_KEY, 
                                 splash_uri=SPLASH_URL)
dash_file_explorer.init_callbacks(app)
du.configure_upload(app, UPLOAD_FOLDER_ROOT, use_upload_id=False)

#APP LAYOUT
app.title = 'Label Maker'
app._favicon = 'mlex.ico'

app.layout = html.Div(
    [
        header("MLExchange | Label Maker", 
               "https://github.com/mlexchange/mlex_dash_labelmaker_demo"),
        dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col([
                            dbc.Accordion([
                                dbc.AccordionItem(
                                    label_method(), 
                                    title='Labeling Method'),
                                dbc.AccordionItem(
                                    store_options(), 
                                    title='Store Options'),
                                dbc.AccordionItem(
                                    display_settings(), 
                                    title='Display Settings'),
                            ], style = {'position': 'sticky', 'top': '10%'})
                        ], width=4),
                        dbc.Col(
                            [
                                dash_file_explorer.file_explorer,
                                dcc.Loading(id="loading-display",
                                            parent_className='transparent-loader-wrapper',
                                            children=[html.Div(id='output-image-upload')],
                                            style={'visibility': 'hidden'},
                                            type="circle"),
                                display()
                            ], width=8),
                    ],
                    justify='center'
                ),
            ],
            fluid=True,
            style={'margin-top': '1%'}
        ),
        browser_cache(MLCOACH_URL, DATA_CLINIC_URL)
    ]
)