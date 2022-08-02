import os
from dash import html
import dash_bootstrap_components as dbc
import pathlib
import plotly.express as px
import requests
from file_manager import local_to_docker_path

LOCAL_DATA = str(os.environ['DATA_DIR'])
DOCKER_DATA = pathlib.Path.home() / 'data'
DOCKER_HOME = str(DOCKER_DATA) + '/'
LOCAL_HOME = str(LOCAL_DATA)


def get_color_from_label(label, color_cycle):
    '''
    This function assigns a color label
    Args:
        label:          Label index
        color_cycle:    List of label colors
    Returns:
        color:          Color that corresponds to the input label
    '''
    return color_cycle[int(label)]


def create_label_component(label_dict, color_cycle=px.colors.qualitative.Dark24, del_button=False):
    '''
    This function updates the reactive component that contains the label buttons when
        - A new label is added
        - A label is deleted
    Args:
        label_dict:     Dictionary of label names, e.g., [0: 'label',...]
        color_cycle:    List of label colors
        del_button:     Bool that indicates if the labels can be deleted
    Returns:
        Reactive components with updated label buttons (sorted by label key number)
    '''
    comp_list = []
    if del_button:
        for i in sorted(label_dict.keys()):
            comp_row = dbc.Row(
                [
                    dbc.Col(
                        dbc.Button(label_dict[i],
                                   id={'type': 'label-button', 'index': i},
                                   size="sm",
                                   style={'background-color': color_cycle[i], 'border-color': color_cycle[i],
                                          'color':'black', 'width': '100%', 'margin-bottom': '5px'}
                                   ),
                        width=8
                    ),
                    dbc.Col(
                        dbc.Button('\u2716',
                                   id={'type': 'delete-label-button', 'index': i},
                                   size="sm",
                                   style={'background-color': color_cycle[i], 'border-color': color_cycle[i],
                                          'color':'black', 'width': '100%', 'margin-bottom': '5px'}),
                        width=4
                    ),
                ],
            )
            comp_list.append(comp_row)
    else:
        for i in sorted(label_dict.keys()):
            comp_row = dbc.Row(
                dbc.Col(
                    dbc.Button(label_dict[i],
                               id={'type': 'label-button', 'index': i},
                               size="sm",
                               style={'background-color': color_cycle[i], 'border-color': color_cycle[i],
                                      'color': 'black', 'width': '100%', 'margin-bottom': '5px'}
                               )
                ),
            )
            comp_list.append(comp_row)
    
    comp_list.append(
        dbc.Button('Unlabel the Selected',
                   id='un-label',
                   className="ms-auto",
                   color = 'primary',
                   size="sm",
                   outline=True,
                   style={'width': '100%', 'margin-bottom': '0px', 'margin-top': '10px'})
    )
    comp_list.append(
        dbc.Button('Unlabel All',
                   id='un-label-all',
                   className="ms-auto",
                   color = 'primary',
                   size="sm",
                   outline=True,
                   style={'width': '100%', 'margin-bottom': '10px', 'margin-top': '5px'})
    )
    
    return comp_list


def parse_contents(contents, filename, index, probs=None):
    '''
    This function creates the reactive components to display 1 image with it's thumbnail card
    Args:
        contents:   Image contents
        filename:   Filename
        index:      Index of the reactive component
        probs:      String of probabilities
    Returns:
        reactive_component
    '''
    text=''
    if probs:
        text = 'Label \t Probability\n' + '--------\n' + probs
    # ====== label results =======
    img_card = html.Div(
        dbc.Card(
            id={'type': 'thumbnail-card', 'index': index},
            children=[
                html.A(id={'type': 'thumbnail-image', 'index': index},
                       n_clicks=0,   
                       children=dbc.CardImg(id={'type': 'thumbnail-src', 'index': index},
                                            src=contents,
                                            bottom=False)),
                dbc.CardBody([
                    html.P(id={'type':'thumbnail-name', 'index': index}, children=filename, style={'font-size': '12px'}),
                    html.P(children=text, style={'whiteSpace': 'pre-wrap', 'font-size': '12px'})
                ])
            ],
            outline=False,
            color='white'
        ),
        id={'type': 'thumbnail-wrapper', 'index': index},
        style={'display': 'block'}
    )
    return img_card


def parse_contents_data_clinic(contents, filename, index):
    '''
    This function creates the reactive components to display 1 image with it's thumbnail card
    Args:
        contents:   Image contents
        filename:   Filename
        index:      Index of the reactive component
    Returns:
        reactive_component
    '''
    img_card = html.Div(
        dbc.Card(
            id={'type': 'thumbnail-card', 'index': index},
            children=[
                html.A(id={'type': 'thumbnail-image', 'index': index},
                       n_clicks=1,
                       children=dbc.CardImg(id={'type': 'thumbnail-src', 'index': index},
                                            src=contents,
                                            bottom=False)),
                dbc.CardBody([
                    html.P(id={'type':'thumbnail-name', 'index': index}, children=filename, style={'font-size': '12px'}),
                ])
            ],
            outline=False,
            color='primary'
        ),
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
        filenames = list(file['filename'])
        for ind, filename in enumerate(filenames):
            filenames[ind] = filename.split(os.sep)[-1]
        file['filename'] = filenames
    for j in range(n_rows):
        row_child = []
        for i in range(n_cols):
            index = j * n_cols + i
            if index >= n_images:
                # no more images, on hanging row
                break
            content = list_of_contents[index]
            filename = list_of_names[index]
            docker_filename = local_to_docker_path(filename, DOCKER_HOME, LOCAL_HOME, type='str')
            if show_prob:
                # warning
                # this section is needed bc the filenames in mlcoach do not match
                docker_filename = docker_filename.split(os.sep)[-1]  # match by filename - not full path
                
                if docker_filename in filenames:
                    probs = str(file.loc[file['filename']==docker_filename].T.iloc[1:].to_string(header=None))
                else:
                    probs = ''
            if data_clinic:
                row_child.append(dbc.Col(parse_contents_data_clinic(content,
                                                                    filename,
                                                                    j * n_cols + i),
                                                     width="{}".format(12 // n_cols),
                                         )
                                 )
            else:
                row_child.append(dbc.Col(parse_contents(content,
                                                        filename,
                                                        j * n_cols + i,
                                                        probs),
                                         width="{}".format(12 // n_cols),
                                         )
                                 )
            visible.append(1)
            
        children.append(dbc.Row(row_child))
    return children


def get_trained_models_list(user, datapath, tab):
    '''
    This function queries the MLCoach or DataClinic results
    Args:
        user:               Username
        datapath:           Path to data
        tab:                Tab option (MLCoach vs Data Clinic)
    Returns:
        trained_models:     List of options
    '''
    if tab == 'mlcoach':
        filename = '/results.csv'
    else:
        tab = 'data_clinic'
        filename = '/dist_matrix.csv'
    model_list = requests.get(f'http://job-service:8080/api/v0/jobs?&user={user}&mlex_app={tab}').json()
    trained_models = [{'label': 'Default', 'value': 'data'+filename}]
    for model in model_list:
        # if datapath:
            #if model['job_kwargs']['kwargs']['dataset']==datapath[0]['file_path'] and \
            #        model['job_kwargs']['kwargs']['job_type'].split(' ')[0]=='prediction_model':
        if model['job_kwargs']['kwargs']['job_type'].split(' ')[0]=='prediction_model':
            if os.path.exists(model['job_kwargs']['cmd'].split(' ')[4]+filename):  # check if the file exists
                trained_models.append({'label': model['job_kwargs']['kwargs']['job_type'],
                                           'value': model['job_kwargs']['cmd'].split(' ')[4]+filename})
    trained_models.reverse()
    return trained_models
