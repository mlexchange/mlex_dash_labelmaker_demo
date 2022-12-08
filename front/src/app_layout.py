import os
import dash
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
import dash_daq as daq
from dash_extensions import EventListener
import dash_uploader as du

from flask import Flask
import pathlib
import plotly.express as px
import templates
from helper_utils import create_label_component


external_stylesheets = [dbc.themes.BOOTSTRAP, 
                        'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css'
                        ]
server = Flask(__name__)
app = dash.Dash(__name__, external_stylesheets = external_stylesheets, suppress_callback_exceptions=True)

header = templates.header()

LABEL_LIST = {'Label_1': [], 'Label_2': []}
MLCOACH_URL = str(os.environ['MLCOACH_URL'])
DATA_CLINIC_URL = str(os.environ['DATA_CLINIC_URL'])
DOCKER_DATA = pathlib.Path.home() / 'data'

UPLOAD_FOLDER_ROOT = DOCKER_DATA / 'upload'
du.configure_upload(app, UPLOAD_FOLDER_ROOT, use_upload_id=False)

# Connecting to tiled server
TILED_KEY = str(os.environ['TILED_KEY'])
try:
    TILED_CLIENT = from_uri(f'http://tiled-server:8000/api?api_key={TILED_KEY}', cache=TiledCache.on_disk('data/cache'))
    disable_tiled = False
except Exception as e:
    TILED_CLIENT = ''
    print(f'Could not connect to tiled server due to: {e}')
    disable_tiled = True


# REACTIVE COMPONENTS FOR LABELING METHOD
label_method = html.Div([
    html.Div(
        [
            dbc.RadioItems(
                id="tab-group",
                className="btn-group",
                inputClassName="btn-check",
                labelClassName="btn btn-outline-primary",
                labelCheckedClassName="active",
                labelStyle={'font-size': '13px', 'width': '85px', 'margin':'1px', 'width': '100%'},
                options=[
                    {"label": "Manual", "value": "manual"},
                    {"label": "DataClinic", "value": "clinic"},
                    {"label": "MLCoach", "value": "mlcoach"}
                ],
                style={'width': '100%'},
                value="manual")
        ],
        className="radio-group",
        style ={'font-size': '0.5px','margin-bottom': '10px'},
    ),
    # Labeling with MLCoach
    dbc.Collapse(
        children = [
                    dbc.Row(
                        [
                            dbc.Col(dbc.Button('Go to MLCoach', 
                                                id='goto-webpage', 
                                                outline="True",
                                                color='primary', 
                                                size="sm", 
                                                style={'width': '100%', 'margin-bottom': '1rem', 'margin-top': '0.5rem'}),
                                    width=11,
                                    style={ 'margin-right': '2%', 'width': '90%'}),
                            dbc.Col(dbc.Button(className="fa fa-question",
                                               id='tab-help-button',
                                               outline="True",
                                               color='primary', 
                                               size="sm", 
                                               style={'width': '100%', 'margin-bottom': '1rem', 'margin-top': '0.5rem'}),
                                    width=1,
                                    style={'width': '8%'})
                        ],
                        className="g-0"
                    )
                    ],
        id="goto-webpage-collapse",
        is_open=False
    ),
    dbc.Collapse(
        children = [
                    dbc.Row([
                        dbc.Col(dcc.Input(
                            id='add-label-name',
                            placeholder="Input new label here",
                            style={'width': '100%', 'margin-bottom': '10px', 'margin-top': '5px'}), width=8),
                        dbc.Col(dbc.Button(
                            'Add Label',
                            id='modify-list',
                            outline="True",
                            size = 'sm',
                            color='primary',
                            n_clicks=0,
                            style={'width': '100%', 'margin-bottom': '10px', 'margin-top': '5px'}), width=4) ],
                        justify = 'center'
                        )
        ],
        id="manual-collapse",
        is_open=False
    ),
    # manual tab is default button group
    dbc.Collapse(
        children = html.Div(id='label-buttons',
                            children=create_label_component(LABEL_LIST.keys()),
                            style={'margin-bottom': '0.5rem'}),
        id="label-buttons-collapse",
        is_open=False
    ),
    # Labeling with MLCoach
    dbc.Collapse(
        children = [dbc.Label('Trained models:'),
                    dbc.Row([dbc.Col(dcc.Dropdown(id='mlcoach-model-list')),
                             dbc.Col(dbc.Button('Refresh', id='mlcoach-refresh', outline="True",
                                 color='primary', size="sm", style={'width': '100%', 'margin-top': '1px'}))]),
                    dbc.Label('Probability Threshold', style={'width': '100%', 'margin-top': '20px'}),
                    dcc.Dropdown(id='mlcoach-label-name'),
                    dcc.Slider(id='probability-threshold',
                               min=0,
                               max=100,
                               value=51,
                               tooltip={"placement": "top", "always_visible": True},
                               marks={0: '0', 25: '25', 50: '50', 75: '75', 100: '100'}),
                    dbc.Button('Label with Threshold', id='mlcoach-label', outline="True",
                               color='primary', size="sm", style={'width': '100%', 'margin-top': '20px'})
                    ],
        id="mlcoach-collapse",
        is_open=False
    ),
    # Labeling with Data Clinic
    dbc.Collapse(
        children = [dbc.CardBody([
                        dbc.Label('Trained models:'),
                        dbc.Row([dbc.Col(dcc.Dropdown(id='data-clinic-model-list')),
                             dbc.Col(dbc.Button('Refresh', id='data-clinic-refresh', outline="True",
                                 color='primary', size="sm", style={'width': '100%', 'margin-top': '1px'}))]),
                        dbc.Input(id='n-similar-images', placeholder='Input num of similar images to find',
                                  style={'width': '100%', 'margin-top': '20px', "display": "none"}),
                        dbc.Row([dbc.Col(dbc.Button('Find Similar Images', 
                                                    id='find-similar-unsupervised', outline="True",
                                                    color='primary', size="sm", style={'width': '100%', 'margin-top': '20px'})),
                                 dbc.Col(dbc.Button('Stop Find Similar Images', id='exit-similar-unsupervised', outline="True",
                                                    color='primary', size="sm", style={'width': '100%', 'margin-top': '20px'}))]),
                        daq.Indicator(id='on-off-display', label='Find Similar Images: OFF', color='#596D4E', size=30, style={'margin-top': '20px'})
                    ]),
        ],
        id="data-clinic-collapse",
        is_open=False
    )
])


# REACTIVE COMPONENTS FOR ADDITIONAL OPTIONS : SORT, HIDE, ETC
additional_options_html = html.Div(
        [
            dbc.Row(dbc.Col([
                    dbc.Label('Number of Thumbnail Columns'),
                    dcc.Slider(id='thumbnail-slider', min=1, max=5, value=4,
                               marks = {str(n):str(n) for n in range(5+1)})
            ])),
            dbc.Row(dbc.Col(dbc.Button('Sort', id='button-sort', outline="True",
                                       color='primary', size="sm", style={'width': '100%', 'margin-top': '20px'}))),
            dbc.Row(html.P('')),
            dbc.Row(dbc.Col(dbc.Button('Hide', id='button-hide', outline='True',
                                       color='primary', size="sm", style={'width': '100%'}))),
            dbc.Row(html.P('')),
            dbc.Row(dbc.Col(dbc.Button('Unlabel All', id='un-label-all', outline='True',
                            color='primary', size="sm", style={'width': '100%'}))),
            dbc.Modal([
                dbc.ModalHeader(dbc.ModalTitle("Warning")),
                dbc.ModalBody(id="un-label-warning"),
                dbc.ModalFooter([
                    dbc.Button(
                        "YES", id="confirm-un-label-all", color='danger', outline=False,
                        className="ms-auto", n_clicks=0),
                ]),
            ], id="modal-un-label",
                is_open=False,
                style = {'color': 'red'}
            )
        ]
)

# files display
file_paths_table = html.Div(
        children=[
            dash_table.DataTable(
                id='files-table',
                columns=[
                    {'name': 'type', 'id': 'file_type'},
                    {'name': 'File Table', 'id': 'file_path'},
                ],
                data = [],
                hidden_columns = ['file_type'],
                row_selectable='single',
                style_cell={'padding': '0.5rem', 'textAlign': 'left'},
                fixed_rows={'headers': False},
                css=[{"selector": ".show-hide", "rule": "display: none"}],
                style_data_conditional=[
                    {'if': {'filter_query': '{file_type} = dir'},
                     'color': 'blue'},
                 ],
                style_table={'height':'18rem', 'overflowY': 'auto'}
            )
        ]
    )


# UPLOAD DATASET
data_access = html.Div([
    dbc.Card([
        dbc.CardBody(id='data-body',
                      children=[
                          dbc.Label('1. Upload a new file or a zipped folder:', className='mr-2'),
                          html.Div([du.Upload(
                                            id="dash-uploader",
                                            max_file_size=60000,  # 1800 Mb
                                            cancel_button=True,
                                            pause_button=True
                                    )],
                                    style={  # wrapper div style
                                        'textAlign': 'center',
                                        'width': '770px',
                                        'padding': '5px',
                                        'display': 'inline-block',
                                        'margin-bottom': '10px',
                                        'margin-right': '20px'},
                          ),
                          dbc.Label('2. Choose files/directories:', className='mr-2'),
                          dbc.Row([
                            dbc.Col(
                                dbc.Row([
                                    dbc.Col(dbc.InputGroupText("Browse Format: ",
                                                               style={'height': '2.5rem', 'width': '100%'}),
                                            width=5),
                                    dbc.Col(dcc.Dropdown(
                                                id='browse-format',
                                                options=[
                                                    {'label': 'dir', 'value': 'dir'},
                                                    {'label': 'all (*)', 'value': '*'},
                                                    {'label': '.png', 'value': '*.png'},
                                                    {'label': '.jpg/jpeg', 'value': '*.jpg,*.jpeg'},
                                                    {'label': '.tif/tiff', 'value': '*.tif,*.tiff'},
                                                    {'label': '.txt', 'value': '*.txt'},
                                                    {'label': '.csv', 'value': '*.csv'},
                                                ],
                                                value='dir',
                                                style={'height': '2.5rem', 'width': '100%'}),
                                            width=7)
                                ], className="g-0"),
                                width=4,
                            ),
                            dbc.Col([
                                dbc.Button("Delete the Selected",
                                             id="delete-files",
                                             className="ms-auto",
                                             color="danger",
                                             size='sm',
                                             outline=True,
                                             n_clicks=0,
                                             style={'width': '100%', 'height': '2.5rem'}
                                    ),
                                dbc.Modal([
                                    dbc.ModalHeader(dbc.ModalTitle("Warning")),
                                    dbc.ModalBody("Files cannot be recovered after deletion. Do you still want to proceed?"),
                                    dbc.ModalFooter([
                                        dbc.Button(
                                            "Delete", id="confirm-delete", color='danger', outline=False, 
                                            className="ms-auto", n_clicks=0
                                        )])
                                    ],
                                    id="modal",
                                    is_open=False,
                                    style = {'color': 'red'}
                                )
                            ], width=2),
                            dbc.Col(
                                dbc.Row([
                                    dbc.Col(dbc.InputGroupText("Import Format: ",
                                                       style={'height': '2.5rem', 'width': '100%'}),
                                            width=5),
                                    dbc.Col(dcc.Dropdown(
                                            id='import-format',
                                            options=[
                                                {'label': 'all files (*)', 'value': '*'},
                                                {'label': '.png', 'value': '*.png'},
                                                {'label': '.jpg/jpeg', 'value': '*.jpg,*.jpeg'},
                                                {'label': '.tif/tiff', 'value': '*.tif,*.tiff'},
                                                {'label': '.txt', 'value': '*.txt'},
                                                {'label': '.csv', 'value': '*.csv'},
                                            ],
                                            value='*',
                                            style={'height': '2.5rem', 'width': '100%'}),
                                            width=7)
                                ], className="g-0"),
                                width=4
                            ),
                            dbc.Col(
                                dbc.Button("Import",
                                             id="import-dir",
                                             className="ms-auto",
                                             color="secondary",
                                             size='sm',
                                             outline=True,
                                             n_clicks=0,
                                             style={'width': '100%', 'height': '2.5rem'}
                                ),
                                width=2,
                            ),
                          ]),        
                        dbc.Label('3. (Optional) Move a file or folder into a new directory:', className='mr-2'),
                        dbc.Button(
                            "Open File Mover",
                            id="file-mover-button",
                            size="sm",
                            className="mb-3",
                            color="secondary",
                            outline=True,
                            n_clicks=0,
                        ),
                        dbc.Collapse(
                            html.Div([
                                dbc.Col([
                                      dbc.Label("Home data directory (Docker HOME) is '{}'.\
                                                 Dataset is by default uploaded to '{}'. \
                                                 You can move the selected files or directories (from File Table) \
                                                 into a new directory.".format(DOCKER_DATA, UPLOAD_FOLDER_ROOT), className='mr-5'),
                                      html.Div([
                                          dbc.Label('Move data into directory:', className='mr-5'),
                                          dcc.Input(id='dest-dir-name', placeholder="Input relative path to Docker HOME", 
                                                        style={'width': '40%', 'margin-bottom': '10px'}),
                                          dbc.Button("Move",
                                               id="move-dir",
                                               className="ms-auto",
                                               color="secondary",
                                               size='sm',
                                               outline=True,
                                               n_clicks=0,
                                               #disabled = True,
                                               style={'width': '22%', 'margin': '5px'}),
                                      ],
                                      style = {'width': '100%', 'display': 'flex', 'align-items': 'center'},
                                      )
                                  ])
                             ]),
                            id="file-mover-collapse",
                            is_open=False,
                        ),
                        html.Div([ html.Div([dbc.Label('4. (Optional) Load data through Tiled')], style = {'margin-right': '10px'}),
                                    daq.BooleanSwitch(
                                        id='tiled-switch',
                                        on=False,
                                        color="#9B51E0",
                                        disabled=disable_tiled,
                                    )],
                            style = {'width': '100%', 'display': 'flex', 'align-items': 'center', 'margin': '10px', 'margin-left': '0px'},
                        ),
                        html.Div([ html.Div([dbc.Label('5. (Optional) Show Local/Docker Path')], style = {'margin-right': '10px'}),
                                    daq.ToggleSwitch(
                                        id='my-toggle-switch',
                                        value=False
                                    )],
                            style = {'width': '100%', 'display': 'flex', 'align-items': 'center', 'margin': '10px', 'margin-left': '0px'},
                        ),
                        file_paths_table,
                        ]),
    ],
    id="data-access",
    )
])


file_explorer = html.Div(
    [
        dbc.Button(
            "Toggle File Manager",
            id="collapse-button",
            size="lg",
            className="m-2",
            color="secondary",
            outline=True,
            n_clicks=0,
        ),
        dbc.Button(
            "Clear Images",
            id="clear-data",
            size="lg",
            className="m-2",
            color="secondary",
            outline=True,
            n_clicks=0,
            #style={'width': '100%', 'justify-content': 'center'}
        ),
        dbc.Collapse(
            data_access,
            id="collapse",
            is_open=True,
        ),
    ]
)


# DISPLAY DATASET
display = html.Div(
    [
        file_explorer,
        dcc.Loading(id="loading-display",
                    parent_className='transparent-loader-wrapper',
                    children=[html.Div(id='output-image-upload')],
                    # fullscreen=True,
                    style={'visibility': 'hidden'},
                    type="circle"),
        dbc.Row([
            dbc.Col(dbc.Row(dbc.Button('<', id='prev-page', style={'width': '10%'}, disabled=True), justify='end')),
            dbc.Col(dbc.Row(dbc.Button('>', id='next-page', style={'width': '10%'}, disabled=True), justify='start'))
        ],justify='center'
        ),
        dbc.Modal(id={'type': 'full-screen-modal', 'index': 0},
                  size="xl", 
                  is_open=False),
        dbc.Modal(id='color-picker-modal',
                  children=[daq.ColorPicker(id='label-color-picker',
                                        label='Choose label color',
                                        value=dict(hex='#119DFF')),
                            dbc.Button('Submit', id='submit-color-button', style={'width': '100%'})
                            ],
                  is_open=False
                  )
    ]
)


# REACTIVE COMPONENTS FOR STORING PURPOSES
store_options = html.Div(
        [
            dbc.Row(dbc.Col(dbc.Button('Load Labels from Splash-ML', id='button-load-splash',
                                       outline='True', color='success', size="sm", style={'width': '100%'}))),
            dbc.Row(html.P('')),
            dbc.Row(dbc.Col(dbc.Button('Save Labels to Splash-ML', id='button-save-splash',
                                       outline='True', color='primary', size="sm", style={'width': '100%'}))),
            dbc.Row(html.P('')),
            dbc.Row(dbc.Col(dbc.Button('Save Labels to Disk', id='button-save-disk',
                                       outline='True', color='primary', size="sm", style={'width': '100%'}))),
            dcc.Loading(id="loading-storage",
                                  type="default",
                                  children=
                dbc.Modal([dbc.ModalBody(id='storage-body-modal'),
                                                dbc.ModalFooter(dbc.Button('OK', id='close-storage-modal'))],
                        id="storage-modal",
                        is_open=False,
                        scrollable=True
                        )
            )
        ]
)


browser_cache =html.Div(
        id="no-display",
        children=[
            dcc.Store(id='docker-labels-name', data=LABEL_LIST),
            dcc.Store(id='docker-file-paths', data=[]),
            dcc.Store(id='current-page', data=0),
            dcc.Store(id='image-order', data=[]),
            dcc.Store(id='del-label', data=-1),
            dcc.Store(id='dummy-data', data=0),
            dcc.Store(id='dummy1', data=0),
            dcc.Store(id='previous-tab', data=['init']),
            dcc.Store(id='color-cycle', data=px.colors.qualitative.Light24),
            dcc.Store(id='mlcoach-url', data=MLCOACH_URL),
            dcc.Store(id='data-clinic-url', data=DATA_CLINIC_URL),
            dcc.Store(id='clear-data-flag', data=0),
            dcc.Store(id='clear-then-import', data=0)
        ],
    )


#APP LAYOUT
app.title = 'Label Maker'
app._favicon = 'mlex.ico'

app.layout = html.Div(
    [
        header,
        dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader('Labeling Method'),
                                dbc.CardBody([label_method])
                            ]),
                            dbc.Card([
                                dbc.CardHeader('Labels I/O'),
                                dbc.CardBody([store_options])
                            ]),
                            dbc.Card([
                                dbc.CardHeader('Display Settings'),
                                dbc.CardBody([additional_options_html])
                            ]),
                        ], width=4),
                        dbc.Col(display, width=8),
                    ],
                    justify='center'
                ),
            ],
            fluid=True
        ),
        html.Div(browser_cache)
    ]
)
