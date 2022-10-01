import os, itertools, math, time
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash_extensions import EventListener
import pandas as pd
import pathlib
import plotly.express as px
import requests
from file_manager import local_to_docker_path

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


def create_label_component(label_list, color_cycle=px.colors.qualitative.Light24, mlcoach=False, progress_values=None, progress_labels=None):
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
    if not mlcoach:
        for i in range(len(label_list)):
            comp_row = dbc.Row(
                [
                    dbc.Col(
                        dbc.Button(label_list[i],
                                   id={'type': 'label-button', 'index': i},
                                   n_clicks_timestamp=0,
                                   size="sm",
                                   style={'background-color': color_cycle[i], 'border-color': color_cycle[i],
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
                                   style={'background-color': color_cycle[i], 'border-color': color_cycle[i],
                                          'color':'black', 'width': '100%'}),
                        width=1,
                        style={ 'margin-right': '2%', 'width': '8%'}
                    ),
                    dbc.Col(
                        dbc.Button(className="fa fa-times",
                                   id={'type': 'delete-label-button', 'index': i},
                                   n_clicks_timestamp=0,
                                   size="sm",
                                   style={'background-color': color_cycle[i], 'border-color': color_cycle[i],
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
                                         style={'background-color': color_cycle[i], 'color':'black'}, bar=True))
    else:
        options = []
        for label in label_list:
            options.append({'value': elem, 'label': label})
        comp_list = [dcc.Dropdown(id={'type': 'mlcoach-label-name', 'index': 0}, options=options)]
        for i in range(len(label_list)):
            progress.append(dbc.Progress(id={'type': 'label-percentage', 'index': i},
                                         style={'background-color': color_cycle[i], 'color':'black'}, bar=True))
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
                 dbc.Label(id='total_labeled', style={'margin-top': '5px'})
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
        filenames = list(file['filename'])
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
                if docker_filename in filenames:
                    probs = str(file.loc[file['filename']==docker_filename].T.iloc[1:].to_string(header=None))
                else:
                    probs = ''
            row_child.append(dbc.Col(parse_contents(content,
                                                    filename,
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
        filename = '/results.csv'
    else:
        tab = 'data_clinic'
        filename = '/dist_matrix.csv'
    model_list = requests.get(f'http://job-service:8080/api/v0/jobs?&user={user}&mlex_app={tab}').json()
    trained_models = [{'label': 'Default', 'value': 'data'+filename}]
    for model in model_list:
        if model['job_kwargs']['kwargs']['job_type'].split(' ')[0]=='prediction_model':
            if os.path.exists(model['job_kwargs']['cmd'].split(' ')[4]+filename):  # check if the file exists
                trained_models.append({'label': model['description'],
                                           'value': model['job_kwargs']['cmd'].split(' ')[4]+filename})
    trained_models.reverse()
    return trained_models


def adapt_tiled_filename(filename, dir):
    '''
    This function takes the filename retrieved from tiled and add the full directory path and file extension
    '''
    return dir + '/' + filename + '.tiff'


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


def get_labeling_progress(current_labels_name, num_files):
    '''
    This function calculates the labeling progress
    '''
    # need to calculate non-duplicate labeled images in the future
    num_labeled_imgs = len(list(itertools.chain.from_iterable(list(current_labels_name.values()))))
    labeled_amount = [0] * len(current_labels_name)
    if num_labeled_imgs != 0:
        for indx, label_name in enumerate(current_labels_name.keys()):
            labeled_amount[indx] = len(current_labels_name[label_name])
        progress_values = [100 * a / num_labeled_imgs for a in labeled_amount]
    else:
        progress_values = labeled_amount
    progress_labels = list(map(str, labeled_amount))
    total_num_labeled = f'Labeled {num_labeled_imgs} out of {num_files} images.'
    return progress_values, progress_labels, total_num_labeled


def mlcoach_labeling(current_labels_name, mlcoach_model, mlcoach_label, labelmaker_filenames, threshold):
    # Load mlcoach probabilities
    df_prob = pd.read_csv(mlcoach_model)
    # list the files that are already labeled to avoid overwriting labels
    labeled_filenames = list(itertools.chain.from_iterable(list(current_labels_name.values())))
    selected_thumbs_filename = []
    try:
        filenames = df_prob['filename'][df_prob[mlcoach_label]>threshold/100].tolist()
        for indx, filename in enumerate(filenames):
            if filename not in labeled_filenames and filename in labelmaker_filenames and filename not in selected_thumbs_filename:
                selected_thumbs_filename.append(filename)
    except Exception as e:
        print(f'Exception {e}')
    current_labels_name[mlcoach_label].extend(selected_thumbs_filename)
    return current_labels_name


def manual_labeling(current_labels_name, thumbnail_image_index, thumbnail_image_select_value, thumbnail_name_children):
    selected_thumbs_filename = []
    for thumb_id, select_value, filename in zip(thumbnail_image_index, thumbnail_image_select_value, \
                                                thumbnail_name_children):
        index = thumb_id['index']
        if select_value is not None:
            # add selected thumbs to the label key corresponding to last pressed button
            if select_value % 2 == 1:
                ## remove the previously assigned label before assigning new one
                for current_key in current_labels_name.keys():
                    docker_filename = local_to_docker_path(filename, DOCKER_HOME, LOCAL_HOME, 'str')
                    if docker_filename in current_labels_name[current_key]:
                        current_labels_name[current_key].remove(docker_filename)
                ##
                selected_thumbs_filename.append(filename)
    return selected_thumbs_filename


#============================= splash-ml related functions ===============================
def load_from_splash(uri_list):
    '''
    This function queries labels from splash-ml.
    Args:
        uri_list:           URI of dataset (e.g. file path)
    Returns:
        labels_name_data:   Dictionary of labeled images (docker path), as follows: {'label1': [image filenames],...}
    '''
    url = f'{SPLASH_CLIENT}/datasets?'
    try:
        params = {'uris': uri_list}
        datasets = requests.get(url, params=params).json()
    except Exception as e:
        print(f'Loading from splash exception: {e}')
        datasets = []
        for i in range(math.ceil(len(uri_list)/100)):
            params = {'uris': uri_list[i*100:min(100*(i+1),len(uri_list))]}
            datasets = datasets + requests.get(url, params=params).json()
            time.sleep(0.01)
    labels_name_data = {}
    for dataset in datasets:
        for tag in dataset['tags']:
            if tag['name'] == 'labelmaker':
                label = tag['locator']['path']
                if label not in labels_name_data:
                    labels_name_data[label] = [dataset['uri']]
                else:
                    labels_name_data[label].append(dataset['uri'])
    return labels_name_data


def save_to_splash(labels_name_data):
    '''
    This function saves labels to splash-ml.
    Args:
        labels_name_data:   Dictionary of labeled images (docker path), as follows: {'label1': [image filenames],...}
    Returns:
        Request status, a list of dataset
    '''
    uri_list = []
    status = []
    splash_dataset = requests.get(f'{SPLASH_CLIENT}/datasets?', params={'tags': 'labelmaker'}).json()
    splash_uri_list = list(map(lambda d: d['uri'], splash_dataset))
    for key in labels_name_data:
        for dataset in labels_name_data[key]:
            uri_list.append(dataset)
            status_code = 200
            # check if the dataset already exists in splash-ml
            if dataset in splash_uri_list:
                indx = splash_uri_list.index(dataset)
                dataset_uid = splash_dataset[indx]['uid']
                tag2check = splash_dataset[indx]['tags'][0]['locator']['path']
                if splash_dataset[indx]['tags'][0]['locator']['path'] != key:       # if the tag has changed, patch the dataset
                    tag = {'name': 'labelmaker', 
                           'locator': {'spec': 'label', 
                                       'path': str(key)}}
                    data = {'add_tags': [tag], 
                            'remove_tags': [splash_dataset[indx]['tags'][0]['uid']]}
                    status_code = requests.patch(f'{SPLASH_CLIENT}/datasets/{dataset_uid}/tags', json=data).status_code
            # if it doesn't exist in splash-ml, post it
            else:
                dataset = {'type': 'file',
                            'uri': dataset,
                            'tags': [{'name': 'labelmaker',
                                    'locator': {'spec': 'label',
                                                'path': key
                                                }
                                    }]
                            }
                status_code = requests.post(f'{SPLASH_CLIENT}/datasets/', json=dataset).status_code
            if status_code != 200:
                status = status.append(f'Filename: {dataset} with label {key} failed with status {status_code}. ')
    if len(status)==0:
        return 'Labels stored in splash-ml', uri_list
    else:
        return f'Error. {status}', uri_list
