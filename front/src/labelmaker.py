import os
import io, shutil, pathlib, base64, math

import dash
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
import dash_uploader as du
from dash.dependencies import Input, Output, State, MATCH, ALL

from flask import Flask
import itertools
import PIL
import plotly.express as px

import templates
from helper_utils import get_color_from_label, create_label_component, draw_rows
from file_manager import filename_list, move_a_file, move_dir, \
                         add_filenames_from_dir, check_duplicate_filename


external_stylesheets = [dbc.themes.BOOTSTRAP]
server = Flask(__name__)
app = dash.Dash(__name__, external_stylesheets = external_stylesheets, suppress_callback_exceptions=True)

header = templates.header()


# Font and background colors associated with each theme
text_color = {"dark": "#95969A", "light": "#595959"}
card_color = {"dark": "#2D3038", "light": "#FFFFFF"}

LABEL_LIST = ['Arc', 'Peaks', 'Rings', 'Rods']
COLOR_CYCLE = px.colors.qualitative.Plotly
NUMBER_OF_ROWS = 4

HOME_DATA = pathlib.Path.home() / 'data'

UPLOAD_FOLDER_ROOT = HOME_DATA / 'upload'
du.configure_upload(app, UPLOAD_FOLDER_ROOT, use_upload_id=False)


# REACTIVE COMPONENTS FOR ADDITIONAL OPTIONS : SORT, HIDE, ETC
additional_options_html = html.Div(
        [
            dcc.Input(id='add-label-name', placeholder="Input new label name", style={'width': '95%', 'margin-bottom': '10px'}),
            dbc.Row(dbc.Col(dbc.Button('Add New Label', id='modify-list',
                               outline="True", color='primary', n_clicks=0, style={'width': '95%', 'margin-bottom': '20px'}))),
            dbc.Row(dbc.Col([
                    dbc.Label('Number of Thumbnail Columns'),
                    dcc.Slider(id='thumbnail-slider', min=1, max=5, value=4,
                               marks = {str(n):str(n) for n in range(5+1)})
            ])),
                dbc.Row(dbc.Col(dbc.Button('Sort', id='button-sort', outline="True",
                                           color='primary', style={'width': '95%', 'margin-top': '20px'}))),
                dbc.Row(html.P('')),
                dbc.Row(dbc.Col(dbc.Button('Hide', id='button-hide', outline='True',
                                           color='primary', style={'width': '95%'}))),
                dbc.Row(html.P('')),
                dbc.Row(dbc.Col(dbc.Button('Save Labels to Disk', id='button-save-disk',
                                           outline='True', color='primary', style={'width': '95%'}))),
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
                row_selectable='multi',
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
                          dbc.Label('Upload a new file or folder (zip) to work dir:', className='mr-2'),
                          html.Div([html.Div([ du.Upload(
                                                    id="dash-uploader",
                                                    max_file_size=1800,  # 1800 Mb
                                                    cancel_button=True,
                                                    pause_button=True)],
                                                style={  # wrapper div style
                                                    'textAlign': 'center',
                                                    'width': '300px',
                                                    'padding': '5px',
                                                    'display': 'inline-block',
                                                    'margin-bottom': '30px',
                                                    'margin-right': '20px'}),
                                    html.Div([
                                        dbc.Col([
                                            dbc.Label("Dataset is by default uploaded to '{}'. \
                                                       You can move the selected files or dirs (from File Table) \
                                                       into a new dir.".format(UPLOAD_FOLDER_ROOT), className='mr-5'),
                                            dbc.Label("Home data dir (HOME) is '{}'.".format(HOME_DATA), className='mr-5'),
                                            html.Div([
                                                dbc.Label('Move data into dir:'.format(HOME_DATA), className='mr-5'),
                                                dcc.Input(id='dest-dir-name', placeholder="Input relative path to HOME", 
                                                                style={'width': '40%', 'margin-bottom': '10px'}),
                                                dbc.Button("Move",
                                                     id="move-dir",
                                                     className="ms-auto",
                                                     color="secondary",
                                                     outline=True,
                                                     n_clicks=0,
                                                     disabled = True,
                                                     style={'width': '22%', 'margin': '5px'}),
                                            ],
                                            style = {'width': '100%', 'display': 'flex', 'align-items': 'center'},
                                            )
                                        ])
                                    ])
                                    ],
                            style = {'width': '100%', 'display': 'flex', 'align-items': 'center'}
                          ),
                          dbc.Label('Choose files/directories:', className='mr-2'),
                          html.Div(
                                  [dbc.Button("Browse",
                                             id="browse-dir",
                                             className="ms-auto",
                                             color="secondary",
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
                                style = {'width': '100%', 'display': 'flex', 'align-items': 'center'},
                                ),
                        file_paths_table,
                        ]),
    ],
    id="data-access",
    #is_open=True
    )
])


file_explorer = html.Div(
    [
        dbc.Button(
            "Open File Manager",
            id="collapse-button",
            size="lg",
            className="mb-3",
            color="secondary",
            outline=True,
            n_clicks=0,
        ),
        dbc.Collapse(
            data_access,
            id="collapse",
            is_open=False,
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


label_html = html.Div(
    id='label_buttons',
    children=create_label_component(LABEL_LIST)
)


browser_cache =html.Div(
        id="no-display",
        children=[
            dcc.Store(id='labels', data={}),
            dcc.Store(id='labels-name', data={}),
            dcc.Store(id='file-paths', data=[]),
            dcc.Store(id='save-results-buffer', data=[]),
            dcc.Store(id='label-list', data=LABEL_LIST),
            dcc.Store(id='current-page', data=0),
            dcc.Store(id='image-order', data=[]),
            dcc.Store(id='del-label', data=-1)
        ],
    )


#APP LAYOUT
layout = html.Div(
    [
        header,
        dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(display, width=8),
                        dbc.Col(
                            dbc.Card(
                                dbc.CardBody([
                                    label_html,
                                    html.Hr(),
                                    additional_options_html
                                ]
                                )), width='auto', align='top'),
                    ],
                    justify='center'
                ),
            ],
            fluid=True
        ),
        html.Div(browser_cache)
    ]
)


app.layout = layout

#================================== callback functions ===================================

@app.callback(
    Output("collapse", "is_open"),
    Input("collapse-button", "n_clicks"),
    State("collapse", "is_open")
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


@app.callback(
    Output("modal", "is_open"),
    Input("delete-files", "n_clicks"),
    Input("confirm-delete", "n_clicks"),  
    State("modal", "is_open")
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


@app.callback(
    Output('files-table', 'data'),
    Output('file-paths', 'data'),
    Input('browse-format', 'value'),
    Input('browse-dir', 'n_clicks'),
    Input('import-dir', 'n_clicks'),
    Input('confirm-delete','n_clicks'),
    Input('move-dir', 'n_clicks'),
    Input('files-table', 'selected_rows'),
    Input('file-paths', 'data'),
    State('dest-dir-name', 'value')
)
def file_manager(browse_format, browse_n_clicks, import_n_clicks, delete_n_clicks, \
                  move_dir_n_clicks, rows, selected_paths, dest):
    changed_id = dash.callback_context.triggered[0]['prop_id']
    files = []
    if browse_n_clicks or import_n_clicks:
        files = filename_list(HOME_DATA, browse_format)
        
    selected_files = []
    if bool(rows):
        for row in rows:
            selected_files.append(files[row])
    
    if browse_n_clicks and changed_id == 'confirm-delete.n_clicks':
        for filepath in selected_files:
            if os.path.isdir(filepath['file_path']):
               shutil.rmtree(filepath['file_path'])
            else:
                os.remove(filepath['file_path'])
        selected_files = []
        files = filename_list(HOME_DATA, browse_format)
    
    if browse_n_clicks and changed_id == 'move-dir.n_clicks':
        if dest is None:
            dest = ''
            
        destination = HOME_DATA / dest
        destination.mkdir(parents=True, exist_ok=True)
        if bool(rows):
            sources = selected_paths
        else:
            sources = [{'file_path': str(UPLOAD_FOLDER_ROOT)}]
    
        for source in sources:
            if os.path.isdir(source['file_path']):
                move_dir(source['file_path'], str(destination))
                shutil.rmtree(source['file_path'])
            else:
                move_a_file(source['file_path'], str(destination))
                
        selected_files = []
        files = filename_list(HOME_DATA, browse_format)

    return files, selected_files


@app.callback(
    Output('image-order','data'),
    Input('file-paths','data'),
    Input('import-dir', 'n_clicks'),
    Input('import-format', 'value'),
    Input('files-table', 'selected_rows'),
    Input('button-hide', 'n_clicks'),
    Input('button-sort', 'n_clicks'),
    Input('confirm-delete','n_clicks'),
    Input('move-dir', 'n_clicks'),
    State('labels-name', 'data'),
    State('label-list', 'data'),
    State('image-order','data'),
    prevent_initial_call=True)
def display_index(file_paths, import_n_clicks, import_format, rows, button_hide_n_clicks,
                  button_sort_n_clicks, delete_n_clicks, move_dir_n_clicks, labels_name_data, label_list, image_order):
    '''
    This callback arranges the image order according to the following actions:
        - New content is uploaded
        - Buttons sort or hidden are selected
    Args:
        file_paths :            Absolute file paths selected from path table
        import_n_clicks:        Button for importing selected paths
        import_format:          File format for import
        rows:                   Rows of the selected file paths from path table
        button_hide_n_clicks:   Hide button
        button_sort_n_clicks:   Sort button
        delete_n_clicks:        Button for deleting selected file paths
        labels_name_data:       Dictionary of labeled images, as follows: {label: list of image filenames}
        label_list:             List of label names (tag name)
        image_order:            Order of the images according to the selected action (sort, hide, new data, etc)

    Returns:
        image_order:            Order of the images according to the selected action (sort, hide, new data, etc)
        data_access_open:       Closes the reactive component to select the data access (upload vs. directory)
    '''
    supported_formats = []
    import_format = import_format.split(',')
    if import_format[0] == '*':
        supported_formats = ['tiff', 'tif', 'jpg', 'jpeg', 'png']
    else:
        for ext in import_format:
            supported_formats.append(ext.split('.')[1])

    changed_id = dash.callback_context.triggered[0]['prop_id']
    if import_n_clicks and bool(rows):
        list_filename = []
        for file_path in file_paths:
            if file_path['file_type'] == 'dir':
                list_filename = add_filenames_from_dir(file_path['file_path'], supported_formats, list_filename)
            else:
                list_filename.append(file_path['file_path'])
    
        num_imgs = len(list_filename)
        if  changed_id == 'import-dir.n_clicks' or \
            changed_id == 'confirm-delete.n_clicks' or \
            changed_id == 'files-table.selected_rows' or \
            changed_id == 'move_dir_n_clicks':
            image_order = list(range(num_imgs))

        if changed_id == 'button-hide.n_clicks':
            if button_hide_n_clicks % 2 == 1:
                labeled_names = list(itertools.chain(*labels_name_data.values()))
                unlabeled_indx = []
                for i in range(num_imgs):
                    if list_filename[i] not in labeled_names:
                        unlabeled_indx.append(i)
                image_order = unlabeled_indx
            else:
                image_order = list(range(num_imgs))

        if changed_id == 'button-sort.n_clicks':
            new_indx = [[] for i in range(len(label_list) + 1)]
            for i in range(num_imgs):
                unlabeled = True
                for key_label in labels_name_data:
                    if list_filename[i] in labels_name_data[key_label]:
                        new_indx[int(key_label)].append(i)
                        unlabeled = False
                if unlabeled:
                    new_indx[-1].append(i)

            image_order = list(itertools.chain(*new_indx))
    else:
        image_order = []

    return image_order


@app.callback([
    Output('output-image-upload', 'children'),
    Output('prev-page', 'disabled'),
    Output('next-page', 'disabled'),
    Output('current-page', 'data'),

    Input('image-order', 'data'),
    Input('thumbnail-slider', 'value'),
    Input('prev-page', 'n_clicks'),
    Input('next-page', 'n_clicks'),
    Input('files-table', 'selected_rows'),
    Input('import-format', 'value'),
    Input('file-paths','data'),

    State('current-page', 'data'),
    State('import-dir', 'n_clicks')],
    prevent_initial_call=True)
def update_output(image_order, thumbnail_slider_value, button_prev_page, button_next_page, rows, import_format,
                  file_paths, current_page, import_n_clicks):
    '''
    This callback displays images in the front-end
    Args:
        image_order:            Order of the images according to the selected action (sort, hide, new data, etc)
        thumbnail_slider_value: Number of images per row
        button_prev_page:       Go to previous page
        button_next_page:       Go to next page
        rows:                   Rows of the selected file paths from path table
        import_format:          File format for import
        file_paths:             Absolute file paths selected from path table
        current_page:           Index of the current page
        import_n_clicks:        Button for importing the selected paths
    Returns:
        children:               Images to be displayed in front-end according to the current page index and # of columns
        prev_page:              Enable/Disable previous page button if current_page==0
        next_page:              Enable/Disable next page button if current_page==max_page
        current_page:           Update current page index if previous or next page buttons were selected
    '''
    supported_formats = []
    import_format = import_format.split(',')
    if import_format[0] == '*':
        supported_formats = ['tiff', 'tif', 'jpg', 'jpeg', 'png']
    else:
        for ext in import_format:
            supported_formats.append(ext.split('.')[1])
    
    changed_id = dash.callback_context.triggered[0]['prop_id']
    # update current page if necessary
    if changed_id == 'image-order.data':
        current_page = 0
    if changed_id == 'prev-page.n_clicks':
        current_page = current_page - 1
    if changed_id == 'next-page.n_clicks':
        current_page = current_page + 1

    children = []
    num_imgs = 0
    if import_n_clicks and bool(rows):
        list_filename = []
        for file_path in file_paths:
            if file_path['file_type'] == 'dir':
                list_filename = add_filenames_from_dir(file_path['file_path'], supported_formats, list_filename)
            else:
                list_filename.append(file_path['file_path'])
    
        # plot images according to current page index and number of columns
        num_imgs = len(image_order)
        if num_imgs>0:
            start_indx = NUMBER_OF_ROWS * thumbnail_slider_value * current_page
            max_indx = min(start_indx + NUMBER_OF_ROWS * thumbnail_slider_value, num_imgs)
            new_contents = []
            new_filenames = []
            for i in range(start_indx, max_indx):
                filename = list_filename[image_order[i]]
                with open(filename, "rb") as file:
                    img = base64.b64encode(file.read())
                    file_ext = filename[filename.find('.')+1:]
                    new_contents.append('data:image/'+file_ext+';base64,'+img.decode("utf-8"))
                new_filenames.append(list_filename[image_order[i]])
            children = draw_rows(new_contents, new_filenames, thumbnail_slider_value, NUMBER_OF_ROWS)

    return children, current_page==0, math.ceil((num_imgs//thumbnail_slider_value)/NUMBER_OF_ROWS)<=current_page+1, \
           current_page


@app.callback(
    Output({'type': 'thumbnail-card', 'index': MATCH}, 'color'),
    Input({'type': 'thumbnail-image', 'index': MATCH}, 'n_clicks'),
    Input('labels', 'data'),
    State({'type': 'thumbnail-name', 'index': MATCH}, 'children'),
    State('labels-name', 'data'),
    prevent_initial_call=True
)
def select_thumbnail(value, labels_data, thumbnail_name_children, labels_name_data):
    '''
    This callback assigns a color to thumbnail cards in the following scenarios:
        - An image has been selected, but no label has been assigned (blue)
        - An image has been labeled (label color)
        - An image has been unselected or unlabeled (no color)
    Args:
        value:                      Thumbnail card that triggered the callback (n_clicks)
        labels_data:                Dictionary of labeled images, as follows: {label: list of image indexes}
        unlabel_n_clicks:           Un-label button (n_clicks)
        thumbnail_name_children:    Filename in selected thumbnail
        labels_name_data:           Dictionary of labeled images, as follows: {label: list of image filenames}
    Returns:
        thumbnail_color:            Color of thumbnail card
    '''
    name = thumbnail_name_children
    # find background color according to label class if thumb is labelled
    color = ''
    for label_key in labels_name_data:
        if name in labels_name_data[label_key]:
            color = get_color_from_label(label_key, COLOR_CYCLE)
            break
    if value is None or (dash.callback_context.triggered[0]['prop_id'] == 'un-label.n_clicks' and color==''):
        return ''
    if value % 2 == 1:
        return 'primary'
    elif value % 2 == 0:
        return color


@app.callback(
    Output({'type': 'thumbnail-image', 'index': ALL}, 'n_clicks'),
    Input({'type': 'label-button', 'index': ALL}, 'n_clicks_timestamp'),
    Input('un-label', 'n_clicks'),
    State({'type': 'thumbnail-image', 'index': ALL}, 'n_clicks'),
)
def deselect(label_button_trigger, unlabel_n_clicks, thumb_clicked):
    '''
    This callback deselects a thumbnail card
    Args:
        label_button_trigger:   Label button
        unlabel_n_clicks:       Un-label button
        thumb_clicked:          Selected thumbnail card
    Returns:
        Modify the number of clicks for a specific thumbnail card
    '''
    return [0 for thumb in thumb_clicked]


@app.callback(
    Output('labels', 'data'),
    Output('labels-name', 'data'),
    Input('del-label', 'data'),
    Input({'type': 'label-button', 'index': ALL}, 'n_clicks_timestamp'),
    Input('un-label', 'n_clicks'),
    State({'type': 'thumbnail-image', 'index': ALL}, 'id'),
    State({'type': 'thumbnail-image', 'index': ALL}, 'n_clicks'),
    State({'type': 'thumbnail-name', 'index': ALL}, 'children'),
    State('labels', 'data'),
    State('labels-name', 'data'),
    prevent_initial_call=True
)
def label_selected_thumbnails(del_label, label_button_n_clicks, unlabel_button, thumbnail_image_index,
                              thumbnail_image_select_value, thumbnail_name_children, current_labels,
                              current_labels_name):
    '''
    This callback updates the dictionary of labeled images when:
        - A new image is labeled
        - An existing image changes labels
        - An image is unlabeled
    Args:
        del_label:                      Delete label button
        label_button_n_clicks:          Label button
        unlabel_button:                 Un-label button
        thumbnail_image_index:          Index of the thumbnail image
        thumbnail_image_select_value:   Selected thumbnail image (n_clicks)
        thumbnail_name_children:        Filename of the selected thumbnail image
        current_labels:                 Dictionary of labeled images, as follows: {label: list of image indexes}
        current_labels_name:            Dictionary of labeled images, as follows: {label: list of image filenames}
    Returns:
        labels_data:                    Dictionary of labeled images, as follows: {label: list of image indexes}
        labels_name_data:               Dictionary of labeled images, as follows: {label: list of image filenames}
    '''
    changed_id = dash.callback_context.triggered[-1]['prop_id']
    # if the list of labels is modified
    if changed_id == 'del-label.data' and del_label>-1:
        labels = list(current_labels.keys())
        for label in labels:
            if int(label)>del_label:
                current_labels[str(int(label)-1)] = current_labels[label]
                del current_labels[label]
                current_labels_name[str(int(label) - 1)] = current_labels_name[label]
                del current_labels_name[label]
            if int(label)==del_label:
                del current_labels[label]
                del current_labels_name[label]
        return current_labels, current_labels_name

    label_class_value = max(enumerate(label_button_n_clicks), key=lambda t: 0 if t[1] is None else t[1] )[0]
    selected_thumbs = []
    selected_thumbs_filename = []
    # add empty list to browser cache to store indices of thumbs
    if str(label_class_value) not in current_labels:
        current_labels[str(label_class_value)] = []
        current_labels_name[str(label_class_value)] = []

    for thumb_id, select_value, filename in zip(thumbnail_image_index, thumbnail_image_select_value,
                                                thumbnail_name_children):
        index = thumb_id['index']
        if select_value is not None:
            # add selected thumbs to the label key corresponding to last pressed button
            if select_value % 2 == 1:
                selected_thumbs.append(index)
                selected_thumbs_filename.append(filename)

    # need to remove label from other label_class if exists
    other_labels = {key: value[:] for key, value in current_labels.items() if key != label_class_value}
    other_labels_name = {key: value[:] for key, value in current_labels_name.items() if key != label_class_value}
    # create dict of every other label to test
    for thumb_index, thumb_name in zip(selected_thumbs, selected_thumbs_filename):
        for label in other_labels:
            if thumb_index in other_labels[label]:
                current_labels[label].remove(thumb_index)
            if thumb_name in other_labels_name[label]:
                current_labels_name[label].remove(thumb_name)
    if dash.callback_context.triggered[0]['prop_id'] != 'un-label.n_clicks':
        current_labels[str(label_class_value)].extend(selected_thumbs)
        current_labels_name[str(label_class_value)].extend(selected_thumbs_filename)
    return current_labels, current_labels_name


@app.callback(
    [Output('label_buttons', 'children'),
     Output('modify-list', 'n_clicks'),
     Output('label-list', 'data'),
     Output('del-label', 'data')],

    Input('modify-list', 'n_clicks'),
    Input({'type': 'delete-label-button', 'index': ALL}, 'n_clicks'),

    State('add-label-name', 'value'),
    State('label-list', 'data'),
    State('labels-name', 'data'),
    State('labels', 'data'),
    prevent_initial_call=True
)
def update_list(n_clicks, n_clicks2, add_label_name, label_list, labels_name_data, labels):
    '''
    This callback updates the list of labels. In the case a label is deleted, the index of this label is saved in
    cache so that the list of assigned labels can be updated in the next callback
    Args:
        n_clicks:               Button to add a new label (tag name)
        n_clicks2:              Delete the associated label (tag name)
        add_label_name:         Label to add (tag name)
        label_list:             List of label names (tag name)
        labels_name_data:       Dictionary of labeled images, as follows: {label: list of image filenames}
        labels:                 Dictionary of labeled images, as follows: {label: list of image indexes}
    Returns:
        label_component:        Reactive component with the updated list of labels
        modify_lists.n_clicks:  Number of clicks for the modify list button
        label_list:             List of labels
        del_label:              Index of the deleted label
    '''
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    add_clicks = n_clicks
    if 'delete-label-button' in changed_id and any(n_clicks2):
        rem = changed_id[changed_id.find('index')+7:]
        indx = int(rem[:rem.find(',')])
        try:
            label_list.pop(indx)    # remove label from tagged images
        except Exception as e:
            print(e)
    if add_clicks > 0:
        label_list.append(add_label_name)
        indx = -1
    return [create_label_component(label_list), 0, label_list, indx]


@app.callback(
    Output('save-results-buffer', 'data'),
    Input('button-save-disk', 'n_clicks'),
    State('file-paths','data'),
    State('labels-name', 'data'),
    State('label-list', 'data'),
    State('import-dir', 'n_clicks'),
    State('files-table', 'selected_rows')
)
def save_labels_disk(button_save_disk_n_clicks, file_paths, labels_name_data,
                     label_list, import_n_clicks, rows):
    '''
    This callback saves the labels to disk
    Args:
        button_save_disk_n_clicks:  Button save to disk
        file_paths:                 Absolute file paths selected from path table
        labels_name_data:           Dictionary of labeled images, as follows: {label: list of image filenames}
        label_list:                 List of label names (tag name)
        import_n_clicks:            Button for importing selected paths
        rows:                       Rows of the selected file paths from path table
    Returns:
        The data is saved in the output directory
    '''
    if labels_name_data is not None and import_n_clicks and bool(rows):
        if len(labels_name_data)>0:
            print('Saving labels')
            for label_index in labels_name_data:
                filename_list = labels_name_data[label_index]
                if len(filename_list)>0:
                    # create root directory
                    root = pathlib.Path(HOME_DATA / 'labelmaker_outputs')
                    label_dir = root / pathlib.Path(label_list[int(label_index)])
                    label_dir.mkdir(parents=True, exist_ok=True)
                    # save all files under the current label into the directory
                    for filename in filename_list:
                        im_bytes = filename
                        im = PIL.Image.open(im_bytes)
                        filename = im_bytes.split("/")[-1]
                        f_name = filename.split('.')[-2]
                        f_ext  = filename.split('.')[-1]
                        i = 0
                        while check_duplicate_filename(label_dir,filename):
                            if i:
                                filename = f_name + '_%s'%i + '.' + f_ext
                            i += 1 
                        im_fname = label_dir / pathlib.Path(filename)
                        im.save(im_fname)
    return []


if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0')



