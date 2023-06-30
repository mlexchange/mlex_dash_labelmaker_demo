import os, itertools, math, time
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash_extensions import EventListener
import pathlib
import plotly.express as px
import requests
from file_manager.helper_utils import local_to_docker_path

LOCAL_DATA = str(os.environ['DATA_DIR'])
DOCKER_DATA = pathlib.Path.home() / 'data'
DOCKER_HOME = str(DOCKER_DATA) + '/'
LOCAL_HOME = str(LOCAL_DATA)
SPLASH_CLIENT = 'http://splash:80/api/v0'


#============================= labelmaker related functions ==============================
def get_color_from_label(label_indx, color_cycle):
    '''
    This function assigns a color label
    Args:
        label_indx:     Label index
        color_cycle:    List of label colors
    Returns:
        color:          Color that corresponds to the input label
    '''
    return color_cycle[label_indx]


def create_label_component(label_list, color_cycle=px.colors.qualitative.Light24, mlcoach=False, \
                           progress_values=None, progress_labels=None, total_num_labeled=None):
    '''
    This function updates the reactive component that contains the label buttons when
        - A new label is added
        - A label is deleted
    Args:
        label_list:     Dictionary of label names, e.g., ['label1', 'label2', ...]
        color_cycle:    List of label colors
        mlcoach:        Bool that indicates if the labels should be arranged as a dropdown
    Returns:
        Reactive components with updated label buttons (sorted by label key number)
    '''
    comp_list = []
    progress = []
    label_list = list(label_list)
    if not progress_values:
        progress_values = [0]*len(label_list)
        progress_labels = ['0']*len(label_list)
        total_num_labeled = 'Labeled 0 out of 0 images.'
    if not mlcoach:
        for i in range(len(label_list)):
            comp_row = dbc.Row(
                [
                    dbc.Col(
                        dbc.Button(label_list[i],
                                   id={'type': 'label-button', 'index': i},
                                   n_clicks_timestamp=0,
                                   size="sm",
                                   style={'background-color': color_cycle[i], 
                                          'border-color': color_cycle[i],
                                          'color':'black', 'width': '100%'}
                                   ),
                        width=10,
                        style={'margin-right': '2%', 'width': '80%'}
                    ),
                    dbc.Col(
                        dbc.Button(className="fa fa-paint-brush",
                                   id={'type': 'color-label-button', 'index': i},
                                   size="sm",
                                   n_clicks_timestamp=0,
                                   style={'background-color': color_cycle[i], 
                                          'border-color': color_cycle[i],
                                          'color':'black', 'width': '100%'}),
                        width=1,
                        style={ 'margin-right': '2%', 'width': '8%'}
                    ),
                    dbc.Col(
                        dbc.Button(className="fa fa-times",
                                   id={'type': 'delete-label-button', 'index': i},
                                   n_clicks_timestamp=0,
                                   size="sm",
                                   style={'background-color': color_cycle[i], 
                                          'border-color': color_cycle[i],
                                          'color':'black', 'width': '100%'}),
                        width=1,
                        style={'width': '8%'}
                    ),
                ],
                className="g-0",
            )
            comp_list.append(comp_row)
            progress.append(dbc.Progress(id={'type': 'label-percentage', 'index': i},
                                         value=progress_values[i],
                                         label=progress_labels[i],
                                         style={'background-color': color_cycle[i], 
                                                'color':'black'}, bar=True))
    else:
        options = []
        for label in label_list:
            options.append({'value': elem, 'label': label})
        comp_list = [dcc.Dropdown(id={'type': 'mlcoach-label-name', 'index': 0}, options=options)]
        for i in range(len(label_list)):
            progress.append(dbc.Progress(id={'type': 'label-percentage', 'index': i},
                                         style={'background-color': color_cycle[i], 
                                                'color':'black'}, bar=True))
    comp_list = comp_list + \
                [dbc.Button('Unlabel the Selected',
                            id='un-label',
                            className="ms-auto",
                            color = 'primary',
                            size="sm",
                            outline=True,
                            style={'width': '100%', 'margin-bottom': '10px', 'margin-top': '10px'}),
                 dbc.Label('Labeled images:'),
                 dbc.Progress(progress),
                 dbc.Label(total_num_labeled, id='total_labeled', style={'margin-top': '5px'})
                 ]
    
    return comp_list


def parse_contents(contents, filename, index, probs=None, data_clinic=False):
    '''
    This function creates the reactive components to display thumbnail images
    Args:
        contents:       Image contents
        filename:       Filename
        index:          Index of the reactive component
        probs:          String of probabilities
        data_clinic:    Bool indicating if the images should be pre-selected for data clinic mode
    Returns:
        reactive_component
    '''
    text=''
    if probs:
        text = 'Label \t Probability\n' + '--------\n' + probs
    if data_clinic:
        init_clicks = 1
    else:
        init_clicks = 0
    # ====== label results =======
    img_card = html.Div(
        EventListener(
            children=[dbc.Card(
                                id={'type': 'thumbnail-card', 'index': index},
                                children=[
                                        html.A(id={'type': 'thumbnail-image', 'index': index},
                                            n_clicks=init_clicks,   
                                            children=dbc.CardImg(id={'type': 'thumbnail-src', 'index': index},
                                                                 src=contents,
                                                                 bottom=False)),
                                        dbc.CardBody([
                                            html.P(id={'type':'thumbnail-name', 'index': index}, 
                                                   children=filename, 
                                                   style={'font-size': '12px'}),
                                            html.P(children=text, style={'whiteSpace': 'pre-wrap', 'font-size': '12px'})
                                        ])],
                                outline=False,
                                color='white')],
            id={'type': 'double-click-entry', 'index': index}, 
            events=[{"event": "dblclick", "props": ["srcElement.className", "srcElement.innerText"]}], 
            logging=True),
        id={'type': 'thumbnail-wrapper', 'index': index},
        style={'display': 'block'}
    )
    return img_card


def draw_rows(list_of_contents, list_of_names, n_rows, n_cols, show_prob=False, file=None, data_clinic=False):
    '''
    This function display the images per page
    Args:
        list_of_contents:   List of contents
        list_of_names:      List of filenames
        n_rows:             Number of rows
        n_cols:             Number of columns
        show_prob:          Bool, show probabilities
        file:               table of filenames and probabilities
    Returns:
        reactivate component with all the images
    '''
    n_images = len(list_of_contents)
    n_cols = n_cols
    children = []
    visible = []
    probs = None
    if show_prob:
        try:
            filenames = list(file['filename'])
        except Exception as e:
            filenames = list(file.index)
    for j in range(n_rows):
        row_child = []
        for i in range(n_cols):
            index = j * n_cols + i
            if index >= n_images:
                # no more images, on hanging row
                break
            content = list_of_contents[index]
            filename = list_of_names[index]
            docker_filename = local_to_docker_path(filename, DOCKER_HOME, LOCAL_HOME, 'str')
            if show_prob:
                if docker_filename in filenames:
                # if docker_filename.replace('.tiff', '.tif') in filenames:
                    try:
                        # probs = str(file.loc[file['filename']==docker_filename.replace('.tiff', '.tif')].T.iloc[1:].to_string(header=None))
                        probs = str(file.loc[file['filename']==docker_filename].T.iloc[1:].to_string(header=None))
                    except Exception as e:
                        # probs = str(file.loc[docker_filename.replace('.tiff', '.tif')].T.iloc[0:].to_string(header=None))
                        probs = str(file.loc[docker_filename].T.iloc[0:].to_string(header=None))
                else:
                    probs = ''
            row_child.append(dbc.Col(parse_contents(content,
                                                    filename, #.replace('.tiff', '.tif'),
                                                    j * n_cols + i,
                                                    probs,
                                                    data_clinic),
                                     width="{}".format(12 // n_cols),
                                    )
                             )
            visible.append(1)
        children.append(dbc.Row(row_child))
    return children


def get_trained_models_list(user, tab):
    '''
    This function queries the MLCoach or DataClinic results
    Args:
        user:               Username
        tab:                Tab option (MLCoach vs Data Clinic)
    Returns:
        trained_models:     List of options
    '''
    if tab == 'mlcoach':
        filename = '/results.parquet'
        alt_filename = '/results.csv'
    else:
        tab = 'data_clinic'
        filename = '/dist_matrix.parquet'
        alt_filename = '/dist_matrix.csv'
    model_list = requests.get(f'http://job-service:8080/api/v0/jobs?&user={user}&mlex_app={tab}').json()
    trained_models = []
    for model in model_list:
        if model['job_kwargs']['kwargs']['job_type'].split(' ')[0]=='prediction_model':
            if os.path.exists(model['job_kwargs']['cmd'].split(' ')[4]+filename):  # check if the file exists
                if model['description']:
                    trained_models.append({'label': model['description'],
                                           'value': model['job_kwargs']['cmd'].split(' ')[4]+filename})
                else:
                    trained_models.append({'label': model['job_kwargs']['kwargs']['job_type'],
                                           'value': model['job_kwargs']['cmd'].split(' ')[4]+filename})
            elif os.path.exists(model['job_kwargs']['cmd'].split(' ')[4]+alt_filename):  # check if the file exists
                if model['description']:
                    trained_models.append({'label': model['description'],
                                           'value': model['job_kwargs']['cmd'].split(' ')[4]+alt_filename})
                else:
                    trained_models.append({'label': model['job_kwargs']['kwargs']['job_type'],
                                           'value': model['job_kwargs']['cmd'].split(' ')[4]+alt_filename})
    trained_models.reverse()
    return trained_models


def adapt_tiled_filename(filename, dir):
    '''
    This function takes the filename retrieved from tiled and add the full directory path and file extension
    '''
    new_filename = f'{dir}/{filename}.tif'
    if Path(new_filename).is_file():
        return new_filename
    else:
        return f'{dir}/{filename}.tiff'


def parse_full_screen_content(contents, filename):
    '''
    This function creates the reactive components to display an image full screen
    Args:
        contents:   Image contents
        filename:   Filename
    Returns:
        reactive_component
    '''
    img_card = [html.A(id='full-screen-image',
                       n_clicks=0,
                       children=dbc.CardImg(id='full-screen-src',
                                            src=contents,
                                            bottom=False)),
                dbc.CardBody([html.P(id='full-screen-name', 
                                     children=filename, 
                                     style={'font-size': '12px'})
                                     ])
                ]
    return img_card
