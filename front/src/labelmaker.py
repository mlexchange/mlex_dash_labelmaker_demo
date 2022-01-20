import io
import pathlib
import base64
import math
import os

import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc

from dash.dependencies import Input, Output, State, MATCH, ALL
from flask import Flask
import itertools
import PIL
import plotly.express as px

import templates
from helper_utils import get_color_from_label, create_label_component, draw_rows


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
DATA_DIR = 'fixed_dir'


@app.callback([
    Output('image-cache-filename', 'data'),
    Output('image-cache-content', 'data'),
    Output('image-cache-date', 'data'),
    Input('upload-image', 'contents'),
    State('upload-image', 'filename'),
    State('upload-image', 'last_modified'),
], prevent_initial_call=True)
def upload_image_to_cache(list_of_contents, list_of_names, list_of_dates):
    """
    This callback takes images from the drag and drop and uploads them to local browser cache
    Args:
        list_of_contents, list: list of byte strings corresponding to images
        list_of_names: list:    list of strings, filenames of images
        list_of_dates, list:    list of dates with file creation
    Returns:
        same information stored in cache
    """
    if list_of_names is not None:
        return list_of_names, list_of_contents, list_of_dates
    else:
        return [dash.no_update, dash.no_update, dash.no_update]


@app.callback(
    [
        Output('image-order','data'),
        Output('data-access', 'is_open')
    ],
    Input('image-cache-filename', 'data'),
    Input('image-dir', 'n_clicks'),
    Input('button-hide', 'n_clicks'),
    Input('button-sort', 'n_clicks'),
    State('labels-name', 'data'),
    State('label-list', 'data'),
    State('image-order','data'),
    prevent_initial_call=True)
def display_index(list_filename_cache, dir_n_clicks, button_hide_n_clicks, button_sort_n_clicks,
                  labels_name_data, label_list, image_order):
    '''
    This callback arranges the image order according to the following actions:
        - New content is uploaded
        - Buttons sort or hidden are selected
    Args:
        list_filename_cache:    Filenames of the images saved in cache (data access: upload option)
        dir_n_clicks:           User selected the directory option (data access)
        button_hide_n_clicks:   Hide button
        button_sort_n_clicks:   Sort button
        labels_name_data:       Dictionary of labeled images, as follows: {label: list of image filenames}
        label_list:             List of label names (tag name)
        image_order:            Order of the images according to the selected action (sort, hide, new data, etc)

    Returns:
        image_order:            Order of the images according to the selected action (sort, hide, new data, etc)
        data_access_open:       Closes the reactive component to select the data access (upload vs. directory)
    '''
    changed_id = dash.callback_context.triggered[0]['prop_id']
    if dir_n_clicks>0:
        list_path, list_dirs, filenames = next(os.walk(DATA_DIR))
        list_filename = []
        for filename in filenames:
            if filename.split('.')[-1] in ['tiff', 'tif', 'jpg', 'jpeg', 'png']:
                list_filename.append(filename)
    else:
        list_filename = list_filename_cache
    num_imgs = len(list_filename)
    if changed_id == 'image-cache-filename.data' or changed_id == 'image-dir.n_clicks':
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
    return [image_order, False]


@app.callback([
    Output('output-image-upload', 'children'),
    Output('prev-page', 'disabled'),
    Output('next-page', 'disabled'),
    Output('current-page', 'data'),

    Input('image-order', 'data'),
    Input('thumbnail-slider', 'value'),
    Input('prev-page', 'n_clicks'),
    Input('next-page', 'n_clicks'),

    State('image-cache-content', 'data'),
    State('image-cache-filename', 'data'),
    State('image-cache-date', 'data'),
    State('current-page', 'data'),
    State('image-dir', 'n_clicks')],
    prevent_initial_call=True)
def update_output(image_order, thumbnail_slider_value, button_prev_page, button_next_page, list_contents_cache,
                  list_filenames_cache, list_dates_cache, current_page, dir_n_clicks):
    '''
    This callback displays images in the front-end
    Args:
        image_order:            Order of the images according to the selected action (sort, hide, new data, etc)
        thumbnail_slider_value: Number of images per row
        button_prev_page:       Go to previous page
        button_next_page:       Go to next page
        list_contents_cache:    Contents of the images saved in cache (data access: upload option)
        list_filenames_cache:   Filenames of the images saved in cache (data access: upload option)
        list_dates_cache:       Dates of the images saved in cache (data access: upload option)
        current_page:           Index of the current page
        dir_n_clicks:           User selected the directory option (data access)
    Returns:
        children:               Images to be displayed in front-end according to the current page index and # of columns
        prev_page:              Enable/Disable previous page button if current_page==0
        next_page:              Enable/Disable next page button if current_page==max_page
        current_page:           Update current page index if previous or next page buttons were selected
    '''
    changed_id = dash.callback_context.triggered[0]['prop_id']
    # update current page if necessary
    if changed_id == 'image-order.data':
        current_page = 0
    if changed_id == 'prev-page.n_clicks':
        current_page = current_page - 1
    if changed_id == 'next-page.n_clicks':
        current_page = current_page + 1
    # check data access (upload vs directory)
    if dir_n_clicks > 0:
        list_path, list_dirs, filenames = next(os.walk(DATA_DIR))
        list_filename = []
        for filename in filenames:
            if filename.split('.')[-1] in ['tiff', 'tif', 'jpg', 'jpeg', 'png']:
                list_filename.append(filename)
    else:
        list_filename = list_filenames_cache
    # plot images according to current page index and number of columns
    num_imgs = len(image_order)
    if num_imgs>0:
        start_indx = NUMBER_OF_ROWS * thumbnail_slider_value * current_page
        max_indx = start_indx + NUMBER_OF_ROWS * thumbnail_slider_value
        if max_indx > num_imgs:
            max_indx = num_imgs
        new_contents = []
        new_filenames = []
        new_dates = []
        if dir_n_clicks>0:
            for i in range(start_indx, max_indx):
                filename = DATA_DIR+'/'+list_filename[image_order[i]]
                with open(filename, "rb") as file:
                    img = base64.b64encode(file.read())
                    file_ext = filename[filename.find('.')+1:]
                    new_contents.append('data:image/'+file_ext+';base64,'+img.decode("utf-8"))
                new_filenames.append(list_filename[image_order[i]])
                new_dates.append(os.path.getmtime(filename))
        else:
            for i in range(start_indx, max_indx):
                new_contents.append(list_contents_cache[image_order[i]])
                new_filenames.append(list_filenames_cache[image_order[i]])
                new_dates.append(list_dates_cache[image_order[i]])
        children = draw_rows(new_contents, new_filenames, new_dates, thumbnail_slider_value, NUMBER_OF_ROWS)
    else:
        children = []
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
    State('labels-name', 'data'),
    State('image-cache-content', 'data'),
    State('image-cache-filename', 'data'),
    State('label-list', 'data'),
    State('image-dir', 'n_clicks')
)
def save_labels_disk(button_save_disk_n_clicks, labels_name_data, list_contents_cache, list_filenames_cache,
                     label_list, dir_n_clicks):
    '''
    This callback saves the labels to disk
    Args:
        button_save_disk_n_clicks:  Button save to disk
        labels_name_data:           Dictionary of labeled images, as follows: {label: list of image filenames}
        list_contents_cache:        Contents of the images saved in cache (data access: upload option)
        list_filenames_cache:       Filenames of the images saved in cache (data access: upload option)
        label_list:                 List of label names (tag name)
        dir_n_clicks:               User selected the directory option (data access)
    Returns:
        The data is saved in the output directory
    '''
    if labels_name_data is not None:
        if len(labels_name_data)>0:
            print('Saving labels')
            if dir_n_clicks > 0:
                list_path, list_dirs, list_filename = next(os.walk(DATA_DIR))
            else:
                list_filename = list_filenames_cache
            for label_index in labels_name_data:
                filename_list = labels_name_data[label_index]
                if len(filename_list)>0:
                    # create root directory
                    root = pathlib.Path('data/labelmaker_temp')
                    label_dir = root / pathlib.Path(label_list[int(label_index)])
                    label_dir.mkdir(parents=True, exist_ok=True)
                    # save all files under the current label into the directory
                    for filename in filename_list:
                        filename_index = list_filename.index(filename)
                        if dir_n_clicks > 0:
                            im_bytes = DATA_DIR + '/' + list_filename[filename_index]
                        else:
                            file_contents = list_contents_cache[filename_index]
                            file_contents_data = file_contents.split(',')[1]
                            im_decode = base64.b64decode(file_contents_data)
                            im_bytes = io.BytesIO(im_decode)
                        im = PIL.Image.open(im_bytes)
                        im_fname = label_dir / pathlib.Path(filename)
                        im.save(im_fname)
    return []


# REACTIVE COMPONENTS FOR ADDITIONAL OPTIONS : SORT, HIDE, ETC
additional_options_html = html.Div(
        [
            dbc.Label('Add a New Label Below'),
            dcc.Input(id='add-label-name', style={'width': '95%'}),
            dbc.Row(dbc.Col(dbc.Button('ADD', id='modify-list',
                               outline="True", color='primary', n_clicks=0, style={'width': '95%'}))),
            dbc.Row(dbc.Col([
                    dbc.Label('Number of Thumbnail Columns'),
                    dcc.Slider(id='thumbnail-slider', min=1, max=5, value=4,
                               marks = {str(n):str(n) for n in range(5+1)})
            ])),
                dbc.Row(dbc.Col(dbc.Button('Sort', id='button-sort', outline="True",
                                           color='primary', style={'width': '95%'}))),
                dbc.Row(html.P('')),
                dbc.Row(dbc.Col(dbc.Button('Hide', id='button-hide', outline='True',
                                           color='primary', style={'width': '95%'}))),
                dbc.Row(html.P('')),
                dbc.Row(dbc.Col(dbc.Button('Save Labels to Disk', id='button-save-disk',
                                           outline='True', color='primary', style={'width': '95%'}))),
        ]
)

# UPLOAD DATASET OR USE PRE-DEFINED DIRECTORY
data_access = html.Div([
    dbc.Modal([
        dbc.ModalBody(id='data-body',
                      children=[
                          dbc.Label('Upload a new dataset:', className='mr-2'),
                          dcc.Upload(id='upload-image',
                                     children=html.Div(['Drag and Drop or ',
                                                        html.A('Select Files')]),
                                     style={'width': '97%',
                                            'height': '60px',
                                            'lineHeight': '60px',
                                            'borderWidth': '1px',
                                            'borderStyle': 'dashed',
                                            'borderRadius': '5px',
                                            'textAlign': 'center',
                                            'margin': '10px'},
                                     multiple=True),
                          dbc.Label('Or use directory:', className='mr-2'),
                          dbc.Button("Use Pre-defined Directory",
                                     id="image-dir",
                                     className="ms-auto",
                                     n_clicks=0,
                                     style={'width': '100%', 'margin': '10px'})
                      ])
    ],
    id="data-access",
    centered=True,
    is_open=True)
])


# DISPLAY DATASET
display = html.Div(
    [
        data_access,
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
            dcc.Store(id='image-cache-filename', data=[]),
            dcc.Store(id='image-cache-content', data=[]),
            dcc.Store(id='image-cache-date', data=[]),
            dcc.Store(id='save-results-buffer', data=[]),
            dcc.Store(id='label-list', data=LABEL_LIST),
            dcc.Store(id='current-page', data=0),
            dcc.Store(id='image-order', data=[]),
            dcc.Store(id='del-label', data=-1)
        ],
    )


#APP LAYOUT
app.layout = html.Div(
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


if __name__ == '__main__':
    # host option so docker container listens on all container ports for
    # browser (lets you view the page from outside)
    app.run_server(debug=True, host='0.0.0.0')
