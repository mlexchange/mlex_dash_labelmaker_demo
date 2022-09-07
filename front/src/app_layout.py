import dash
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
import dash_daq as daq
import dash_uploader as du

from flask import Flask
import pathlib
import templates
from helper_utils import create_label_component


external_stylesheets = [dbc.themes.BOOTSTRAP]
server = Flask(__name__)
app = dash.Dash(__name__, external_stylesheets = external_stylesheets, suppress_callback_exceptions=True)

header = templates.header()

LABEL_LIST = {0:'Label_1', 1:'Label_2'}
DOCKER_DATA = pathlib.Path.home() / 'data'

UPLOAD_FOLDER_ROOT = DOCKER_DATA / 'upload'
du.configure_upload(app, UPLOAD_FOLDER_ROOT, use_upload_id=False)


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
                labelStyle={'font-size': '13px', 'width': '85px', 'margin':'1px'},
                options=[
                    {"label": "Instructions", "value": "instruction"},
                    {"label": "Manual", "value": "manual"},
                    {"label": "DataClinic", "value": "clinic"},
                    {"label": "MLCoach", "value": "mlcoach"}
                ],
                value="instruction")
        ],
        className="radio-group",
        style ={'font-size': '0.5px','margin-bottom': '10px'},
    ),
    # Labeling with MLCoach
    dbc.Collapse(
        children = [
                    dbc.Button('Go to MLCoach', id='goto-webpage', outline="True",
                               color='primary', size="sm", style={'width': '100%', 'margin-bottom': '1rem', 'margin-top': '0.5rem'})
                    ],
        id="goto-webpage-collapse",
        is_open=False
    ),
    # Labeling manually
    dbc.Collapse(
        children = [dbc.Label('1. Please use the File Manager on the left to import/load the dataset of interest.'),
                    dbc.Label('2. Click the DataClinic tab. Use the "Go to" button to open DataClinic and train unsupervised learning algorithms to estimate image similarity. \
                               Then, come back to the DataClinic tab in Label Maker to load the results and label batches of similar images.'),
                    dbc.Label('3. Click the Manual tab to manually label images or make corrections to the previous step. \
                               Save the current labels by clicking the button Save Labels to Disk.'),
                    dbc.Label('4. Click the MLCoach tab. Use the "Go to" button to open MLCoach and do supervised learning for image classification using the previously saved labels. \
                               Then, come back to the MLCoach tab in Label Maker to load the results and label the full dataset using their estimated probabilities. \
                               Click the Manual tab to manually label images or make corrections to the previous step.'),
                    dbc.Label('5. Finally, save all the labels by clicking the button Save Labels to Disk.')
        ],
        id="instruction-collapse",
        is_open=True
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
                            children=create_label_component(LABEL_LIST),
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
        children = [dbc.CardHeader("Instructions Data Clinic"),
                    dbc.CardBody([
                        dbc.Label('1. Select a trained model to start.', className='mr-2'),
                        dbc.Label('2. Click on the image of interest. Then click Find Similar Images button below.', className='mr-2'),
                        dbc.Label('3. The image display updates according to the trained model results. Label as usual.', className='mr-2'),
                        dbc.Label('4. To exit this similarity based display, click Stop Find Similar Images.', className='mr-2'),
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
                        daq.Indicator(id='on-off-display', label='Find Similar Images: OFF', color='#596D4E', size=30, style={'margin-top': '20px'}),
                        dbc.Button('Label', id='clinic-label', outline="True",
                               color='primary', size="sm", style={'width': '100%', 'margin-top': '20px', "display": "none"})
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
                dbc.ModalBody("Labels cannot be recovered after deletion. Do you still want to proceed?"),
                dbc.ModalFooter([
                    dbc.Button(
                        "Unlabel", id="confirm-un-label-all", color='danger', outline=False,
                        className="ms-auto", n_clicks=0),
                ]),
            ], id="modal-un-label",
                is_open=False,
                style = {'color': 'red'}
            ),
            dbc.Row(html.P('')),
            dbc.Row(dbc.Col(dbc.Button('Save Labels to Disk', id='button-save-disk',
                                       outline='True', color='primary', size="sm", style={'width': '100%'}))),
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


# UPLOAD DATASET OR USE PRE-DEFINED DIRECTORY
data_access = html.Div([
    dbc.Card([
        dbc.CardBody(id='data-body',
                      children=[
                          dbc.Label('1. Upload a new file or a zipped folder:', className='mr-2'),
                          html.Div([ du.Upload(
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
                          html.Div(
                                  [dbc.Button("Browse",
                                             id="browse-dir",
                                             className="ms-auto",
                                             color="secondary",
                                             size='sm',
                                             outline=True,
                                             n_clicks=0,
                                             style={'width': '15%', 'margin': '5px'}),
                                   html.Div([
                                        dcc.Dropdown(
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
                                                value='*')
                                            ],
                                            style={"width": "15%", 'margin-right': '60px'}
                                    ),
                                  dbc.Button("Delete the Selected",
                                             id="delete-files",
                                             className="ms-auto",
                                             color="danger",
                                             size='sm',
                                             outline=True,
                                             n_clicks=0,
                                             style={'width': '22%', 'margin-right': '10px'}
                                    ),
                                   dbc.Modal(
                                        [
                                            dbc.ModalHeader(dbc.ModalTitle("Warning")),
                                            dbc.ModalBody("Files cannot be recovered after deletion. Do you still want to proceed?"),
                                            dbc.ModalFooter([
                                                dbc.Button(
                                                    "Delete", id="confirm-delete", color='danger', outline=False, 
                                                    className="ms-auto", n_clicks=0
                                                ),
                                            ]),
                                        ],
                                        id="modal",
                                        is_open=False,
                                        style = {'color': 'red'}
                                    ), 
                                   dbc.Button("Import",
                                             id="import-dir",
                                             className="ms-auto",
                                             color="secondary",
                                             size='sm',
                                             outline=True,
                                             n_clicks=0,
                                             style={'width': '22%', 'margin': '5px'}
                                   ),
                                   html.Div([
                                        dcc.Dropdown(
                                                id='import-format',
                                                options=[
                                                    {'label': 'all files (*)', 'value': '*'},
                                                    {'label': '.png', 'value': '*.png'},
                                                    {'label': '.jpg/jpeg', 'value': '*.jpg,*.jpeg'},
                                                    {'label': '.tif/tiff', 'value': '*.tif,*.tiff'},
                                                    {'label': '.txt', 'value': '*.txt'},
                                                    {'label': '.csv', 'value': '*.csv'},
                                                ],
                                                value='*')
                                            ],
                                            style={"width": "15%"}
                                    ),
                                 ],
                                style = {'width': '100%', 'display': 'flex', 'align-items': 'center', 'margin-bottom': '10px'},
                                ),
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
                        html.Div([ html.Div([dbc.Label('4. Show Local/Docker Path')], style = {'margin-right': '10px'}),
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
            className="mtb-2",
            color="secondary",
            outline=True,
            n_clicks=0,
        ),
        dbc.Button(
            "Tiled",
            id="tiled-button",
            size="lg",
            className="mtb-2",
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
        html.Div(id='output-image-upload'),
        dbc.Row([
            dbc.Col(dbc.Row(dbc.Button('<', id='prev-page', style={'width': '10%'}, disabled=True), justify='end')),
            dbc.Col(dbc.Row(dbc.Button('>', id='next-page', style={'width': '10%'}, disabled=True), justify='start'))
        ],justify='center'
        )
    ]
)


browser_cache =html.Div(
        id="no-display",
        children=[
            dcc.Store(id='docker-labels-name', data={}),
            dcc.Store(id='docker-file-paths', data=[]),
            dcc.Store(id='save-results-buffer', data=[]),
            dcc.Store(id='label-dict', data=LABEL_LIST),
            dcc.Store(id='current-page', data=0),
            dcc.Store(id='image-order', data=[]),
            dcc.Store(id='del-label', data=-1),
            dcc.Store(id='dummy-data', data=0),
            dcc.Store(id='dummy1', data=0),
            dcc.Store(id='clinic-file-list', data=[]),
            dcc.Store(id='clinic-filenames', data=[]),
            dcc.Store(id='previous-tab', data=['init'])
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
                        dbc.Col(display, width=8),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader('Labeling Method'),
                                dbc.CardBody([label_method])
                            ]),
                            dbc.Card([
                                dbc.CardHeader('Display Settings'),
                                dbc.CardBody([additional_options_html])
                            ])
                        ], width=4),
                    ],
                    justify='center'
                ),
            ],
            fluid=True
        ),
        html.Div(browser_cache)
    ]
)

