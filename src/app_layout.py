import os

import dash
import dash_bootstrap_components as dbc
import diskcache
from dash import dcc, html
from dash.long_callback import DiskcacheLongCallbackManager
from dotenv import load_dotenv
from file_manager.main import FileManager
from flask import Flask
from flask_caching import Cache

from src.components.browser_cache import browser_cache
from src.components.display import display
from src.components.display_settings import display_settings
from src.components.header import header
from src.components.label_method import label_method
from src.components.store import store_options

cache = diskcache.Cache("./cache")
long_callback_manager = DiskcacheLongCallbackManager(cache)

external_stylesheets = [
    dbc.themes.BOOTSTRAP,
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css",
    "../assets/labelmaker-style.css",
]
server = Flask(__name__)
app = dash.Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    suppress_callback_exceptions=True,
    long_callback_manager=long_callback_manager,
)

cache = Cache(app.server, config={"CACHE_TYPE": "filesystem", "CACHE_DIR": ".cache"})

load_dotenv(".env")

MLCOACH_URL = os.getenv("MLCOACH_URL")
DATA_CLINIC_URL = os.getenv("DATA_CLINIC_URL")
SPLASH_URL = os.getenv("SPLASH_URL")
MLEX_COMPUTE_URL = os.getenv("MLEX_COMPUTE_URL")
DEFAULT_TILED_URI = os.getenv("DEFAULT_TILED_URI")
DEFAULT_TILED_QUERY = os.getenv("DEFAULT_TILED_QUERY")
TILED_KEY = os.getenv("TILED_KEY")
if TILED_KEY == "":
    TILED_KEY = None
DATA_DIR = os.getenv("DATA_DIR")
USER = "admin"
NUMBER_OF_ROWS = 3

dash_file_explorer = FileManager(
    DATA_DIR,
    api_key=TILED_KEY,
)
dash_file_explorer.init_callbacks(app)

# APP LAYOUT
app.title = "Label Maker"
app._favicon = "mlex.ico"

app.layout = html.Div(
    [
        header(
            "MLExchange | Label Maker",
            "https://github.com/mlexchange/mlex_dash_labelmaker_demo",
        ),
        dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Accordion(
                                    [
                                        dbc.AccordionItem(
                                            label_method(), title="Labeling Method"
                                        ),
                                        dbc.AccordionItem(
                                            store_options(), title="Store Options"
                                        ),
                                        dbc.AccordionItem(
                                            display_settings(), title="Display Settings"
                                        ),
                                    ],
                                    style={
                                        "position": "sticky",
                                        "top": "10%",
                                        "width": "100%",
                                    },
                                )
                            ],
                            width=4,
                            style={"display": "flex"},
                        ),
                        dbc.Col(
                            [
                                dash_file_explorer.file_explorer,
                                # html.Div(id='output-image-upload'),
                                dcc.Loading(
                                    id="loading-display",
                                    parent_className="transparent-loader-wrapper",
                                    children=[html.Div(id="output-image-upload")],
                                    type="circle",
                                ),
                                display(),
                            ],
                            width=8,
                        ),
                    ],
                    justify="center",
                ),
            ],
            fluid=True,
            style={"margin-top": "1%"},
        ),
        browser_cache(MLCOACH_URL, DATA_CLINIC_URL),
    ]
)
