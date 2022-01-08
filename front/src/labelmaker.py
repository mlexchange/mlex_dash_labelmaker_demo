import io
import pathlib
import base64

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State, MATCH, ALL
from flask import Flask
import itertools
import PIL
import plotly.express as px

import templates


external_stylesheets = [dbc.themes.BOOTSTRAP]

server = Flask(__name__)
app = dash.Dash(__name__, external_stylesheets = external_stylesheets, suppress_callback_exceptions=True)


header = templates.header()
# Font and background colors associated with each theme
text_color = {"dark": "#95969A", "light": "#595959"}
card_color = {"dark": "#2D3038", "light": "#FFFFFF"}
LABEL_LIST = ['Arc', 'Peaks', 'Rings', 'Rods']
COLOR_CYCLE = px.colors.qualitative.Plotly


def get_color_from_label(label, color_cycle):
    return color_cycle[int(label)]


# LABEL COMPONENT
def create_label_component(labels, color_cycle=px.colors.qualitative.Plotly):
    comp_list = []
    for i, label in enumerate(labels):
        comp_row = dbc.Row(
            [
                dbc.Col(
                    dbc.Button(label, id={'type': 'label-button', 'index': i},
                                style={'background-color': color_cycle[i], 'color':'white', 'width': '100%'}
                                ),
                    width=8
                ),
                dbc.Col(
                    dbc.Button('\u2716', id={'type': 'delete-label-button', 'index': i},
                               style={'background-color': color_cycle[i], 'color':'white', 'width': '100%'}),
                    width=4
                ),
            ],
        )
        comp_list.append(comp_row)

    return comp_list


def draw_rows(list_of_contents, list_of_names, list_of_dates, n_cols):
    n_images = len(list_of_contents)
    n_cols = n_cols
    n_rows = (n_images // n_cols) + 1
    children = []
    visible = []
    for j in range(n_rows):
        row_child = []
        for i in range(n_cols):
            index = j * n_cols + i
            if index >= n_images:
                # no more images, on hanging row
                break
            content = list_of_contents[index]
            name = list_of_names[index]
            date = list_of_dates[index]
            row_child.append(dbc.Col(parse_contents(content,
                                                    name,
                                                    date,
                                                    j * n_cols + i),
                                     width="{}".format(12 // n_cols),
                                     )
                             )
            visible.append(1)
        children.append(dbc.Row(row_child))
    return children


def parse_contents(contents, filename, date, index):
    img_card = html.Div(dbc.Card(id={
                        'type': 'thumbnail-card',
                        'index': index
                        },
                        children=[
                            html.A(id={
                                'type': 'thumbnail-image',
                                'index': index
                            }, children=dbc.CardImg(id={'type': 'thumbnail-src', 'index': index}, 
                                                        src=contents, bottom=False)),
                            dbc.CardBody(
                                [
                                    html.P(id={'type':'thumbnail-name', 'index': index}, children=filename),
                                ]
                            ),
                        ],
                        outline=False,
                        color='white',
                        ),
                        id={'type': 'thumbnail-wrapper', 'index': index},
                        style={'display': 'block'}
                        )

    return img_card


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
    This function takes images from the drag and drop and uploads them to local
    browser cache

    Args:
        list_of_contents, list: list of byte strings corresponding to images
        list_of_names: list: list of strings, filenames of images
        list_of_dates, list: list of dates with file creation
    """
    if list_of_names is not None:
        return list_of_names, list_of_contents, list_of_dates
    else:
        return [dash.no_update, dash.no_update, dash.no_update]


@app.callback(
    [Output('output-image-upload', 'children')],
    Input('image-cache-content', 'data'),
    Input('button-hide', 'n_clicks'),
    Input('button-sort', 'n_clicks'),
    Input('thumbnail-slider', 'value'),
    State('image-cache-filename', 'data'),
    State('image-cache-date', 'data'),
    State({'type': 'thumbnail-src', 'index': ALL}, 'src'),
    State('labels', 'data'),
    State('labels-name', 'data'),
    State('label-list', 'data')
              )
def update_output(list_of_contents, button_hide_n_clicks, button_sort_n_clicks,
                  thumbnail_slider_value, list_of_names, list_of_dates,
                  thumbnail_src_index, labels_data, labels_name_data, label_list):
    """
    1. Initial upload (parsing from upload)
    2. redraw of thumbnails (when sort or hide button is pressed)
    """
    if len(list_of_contents) == 0:
        return [dash.no_update]
    trigger = dash.callback_context

    if (trigger.triggered[0]['prop_id'] == 'image-cache-content.data' or \
        trigger.triggered[0]['prop_id'] == 'thumbnail-slider.value' or \
        trigger.triggered[0]['prop_id'] == '.') and list_of_contents is not None:
        children = draw_rows(list_of_contents, list_of_names, list_of_dates,
                             n_cols=thumbnail_slider_value)
        print('upload-contents: length of images: {}'.format(len(children)))
        return [children]

    elif trigger.triggered[0]['prop_id'] == 'button-hide.n_clicks':
        if button_hide_n_clicks % 2 == 1:
            labeled_names = list(itertools.chain(*labels_name_data.values()))
            unlabled_name_lists = []
            unlabled_src_lists = []
            unlabled_date_lists = []
            for thumb_name, content, date in zip(list_of_names,
                                                 list_of_contents, list_of_dates):
                if thumb_name not in labeled_names:
                    unlabled_name_lists.append(thumb_name)
                    unlabled_src_lists.append(content)
                    unlabled_date_lists.append(date)
            children = draw_rows(unlabled_src_lists, unlabled_name_lists, unlabled_date_lists,
                                 n_cols=thumbnail_slider_value)
        else:
            children = draw_rows(list_of_contents, list_of_names, list_of_dates,
                                 n_cols=thumbnail_slider_value)
        return [children]
    
    elif trigger.triggered[0]['prop_id'] == 'button-sort.n_clicks':
        # do not show those thumbnails which already have a label.
        n_images = len(list_of_contents)
        print('Number of images ', n_images)
        new_name_lists = [[] for i in range(len(label_list)+1)]
        new_src_lists = [[] for i in range(len(label_list)+1)]
        new_date_lists = [[] for i in range(len(label_list)+1)]
        for name, content, date in zip(list_of_names, 
                                       list_of_contents, list_of_dates):
            unlabled=True
            for key_label in labels_name_data:
            
                if name in labels_name_data[key_label]:
                    new_name_lists[int(key_label)].append(name)
                    new_src_lists[int(key_label)].append(content)
                    new_date_lists[int(key_label)].append(date)
                    unlabled=False
            if unlabled == True:
                new_name_lists[-1].append(name)
                new_src_lists[-1].append(content)
                new_date_lists[-1].append(date)
        new_name = list(itertools.chain(*new_name_lists))
        new_src = list(itertools.chain(*new_src_lists))
        new_date = list(itertools.chain(*new_date_lists))


        print('name lists old: {}'.format(new_name_lists))
        print('name lists: {}'.format(new_name))
        children = draw_rows(new_src, new_name, new_date,
                             n_cols=thumbnail_slider_value)
        print('button-sort: length of images: {}'.format(len(children)))

        return [children]


@app.callback(
    Output({'type': 'thumbnail-card', 'index': MATCH}, 'color'),
    Input({'type': 'thumbnail-image', 'index': MATCH}, 'n_clicks'),
    State({'type': 'thumbnail-image', 'index': MATCH}, 'id'),
    State({'type': 'thumbnail-name', 'index': MATCH}, 'children'),
    State('labels', 'data'),
    State('labels-name', 'data'),
    prevent_initial_call=True
)
def select_thumbnail( value, id_name, thumbnail_name_children, labels_data, labels_name_data):
    index = id_name['index']
    name = thumbnail_name_children
    # find background color according to label class if thumb is labelled
    color = ''
    for label_key in labels_name_data:
        print('for: {} {}'.format(label_key, labels_name_data[label_key]))
        if name in labels_name_data[label_key]:
            color = get_color_from_label(label_key, COLOR_CYCLE)
            print('if: {} in {} then color: {}'.format(name, labels_name_data[label_key],color ))

    if value is None:
        print('index: {}, Not selected'.format(index))
        return ''
    if value % 2 == 1:
        print('index: {}, Selected'.format(index))
        return 'primary'
    elif value % 2 == 0:
        print('index: {}, Not selected/labeled color: {}'.format(name, color))
        return color


@app.callback(
    Output({'type': 'thumbnail-image', 'index': ALL}, 'n_clicks'),
    Input({'type': 'label-button', 'index': ALL}, 'n_clicks_timestamp'),
    State({'type': 'thumbnail-image', 'index': ALL}, 'n_clicks'),
)
def deselect(label_button_trigger, thumb_clicked):
    return [0 for thumb in thumb_clicked]


@app.callback(
    Output('labels', 'data'),
    Output('labels-name', 'data'),
    Input({'type': 'label-button', 'index': ALL}, 'n_clicks_timestamp'),
    State({'type': 'thumbnail-image', 'index': ALL}, 'id'),
    State({'type': 'thumbnail-image', 'index': ALL}, 'n_clicks'),
    State({'type': 'thumbnail-name', 'index': ALL}, 'children'),
    State('labels', 'data'),
    State('labels-name', 'data'), prevent_initial_call=True
)
def label_selected_thumbnails(label_button_n_clicks,
                              thumbnail_image_index,
                              thumbnail_image_select_value,
                              thumbnail_name_children,
                              current_labels,
                              current_labels_name):
    # find most recent pressed label button
    if not any(label_button_n_clicks):
        return [dash.no_update, dash.no_update]
    label_class_value = max(enumerate(label_button_n_clicks), key=lambda t: 0 if t[1] is None else t[1] )[0]
    selected_thumbs = []
    selected_thumbs_filename = []
    # add empty list to browser cache to store indices of thumbs
    if str(label_class_value) not in current_labels:
        current_labels[str(label_class_value)] = []
        current_labels_name[str(label_class_value)] = []

    for thumb_id, select_value, filename in zip(thumbnail_image_index, thumbnail_image_select_value, thumbnail_name_children):
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
    for thumb_index in selected_thumbs:
        for label in other_labels:
            if thumb_index in other_labels[label]:
                current_labels[label].remove(thumb_index)
    for thumb_name in selected_thumbs_filename:
        for label in other_labels:
            if thumb_name in other_labels_name[label]:
                current_labels_name[label].remove(thumb_name)

    current_labels[str(label_class_value)].extend(selected_thumbs)
    current_labels_name[str(label_class_value)].extend(selected_thumbs_filename)
    return current_labels, current_labels_name


# REACTIVE COMPONENTS FOR ADDITIONAL OPTIONS
# HTML FOR ADDITIONAL OPTIONS
additional_options_html = html.Div(
        [
            dbc.Label('Add a New Label Below'),
            dcc.Input(id='label_name', style={'width': '95%'}),
            dbc.Row(dbc.Col(dbc.Button('ADD', id='modify-list',
                               outline="True", color='primary', n_clicks=0, style={'width': '95%'}))),
            dbc.FormGroup(
                [
                    dbc.Label('Number of Thumbnail Columns'),
                    dcc.Slider(id='thumbnail-slider', min=1, max=5, value=4,
                               marks = {str(n):str(n) for n in range(5+1)})
                ]
            ),
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


@app.callback(
    [Output('label_buttons', 'children'),
     Output('modify-list', 'n_clicks'),
     Output('label-list', 'data')],
    Input('modify-list', 'n_clicks'),
    Input({'type': 'delete-label-button', 'index': ALL}, 'n_clicks'),
    State('label_name', 'value'),
    State('label-list', 'data'),
    prevent_initial_call=True
)
def update_list(n_clicks, n_clicks2, label_name, label_list):
    """
    Update the labels list
    """
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    print(changed_id)
    add_clicks = n_clicks
    if 'delete-label-button' in changed_id and any(n_clicks2):
        rem = changed_id[changed_id.find('index')+7:]
        indx = int(rem[:rem.find(',')])
        try:
            label_list.pop(indx)
        except Error as e:
            print(e)
    if add_clicks > 0:
        label_list.append(label_name)
    return [create_label_component(label_list), 0, label_list]


@app.callback(
    Output('save-results-buffer', 'data'),
    Input('button-save-disk', 'n_clicks'),
    State('labels-name', 'data'),
    State('image-cache-content', 'data'),
    State('image-cache-filename', 'data'),
    State('label-list', 'data')
)
def save_labels_disk(button_save_disk_n_clicks, labels_name_data, image_cache_content, image_cache_filename, label_list):
    """
    Creates a directory tree corresponding to the labels, and saves
    the images in the appropriate directory. This prepares the program to launch an
    ml training task, which is expecting the files to be in the classic
    ml classification orgainziation (folder name as semantic label for images)

    Args:
        button_save_disk_n_clicks: int, number of times button has been clicked
        labels_name_data: dict, keys are class index (int), values are list of filenames
            corresponding that have been labelled as part of that class
        image_cache_content: list, binary64 encoded images
        image_cache_filename: list, filename strings

    Returns:
        a true or false value to a hidden buffer indicting successful labelling 
        set completion
    """
    if labels_name_data is not None:
        if len(labels_name_data)>0:
            print('Saving labels')
            print('\n\n')
            print(labels_name_data)
            for label_index in labels_name_data:
                filename_list = labels_name_data[label_index]
                if len(filename_list)>0:
                    # create root directory
                    root = pathlib.Path('data/labelmaker_temp')
                    label_dir = root / pathlib.Path(label_list[int(label_index)])
                    label_dir.mkdir(parents=True, exist_ok=True)

                    # save all files under the current label into the directory
                    for filename in filename_list:
                        filename_index = image_cache_filename.index(filename)
                        file_contents = image_cache_content[filename_index]
                        file_contents_data = file_contents.split(',')[1]
                        im_decode = base64.b64decode(file_contents_data)
                        im_bytes = io.BytesIO(im_decode)
                        im = PIL.Image.open(im_bytes)
                        im_fname = label_dir / pathlib.Path(filename)
                        im.save(im_fname)
    return []


# UPLOAD COMPONENT
upload_html = html.Div(
        [
            dcc.Upload(
                id='upload-image',
                children=html.Div(
                    [
                        'Drag and Drop or ',
                        html.A('Select Files'),
                    ]
                ),
                style={
                    'width': '100%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '10px',
                    },
                multiple=True,
            ),
            html.Div(id='output-image-upload'),
            ]
)


label_html = html.Div(
    id='label_buttons',
    children=create_label_component(LABEL_LIST)
)


browser_cache =html.Div(
        id="no-display",
        children=[
            dcc.Store(id='selected', data=''),
            dcc.Store(id='labels', data={}),
            dcc.Store(id='labels-name', data={}),
            dcc.Store(id='image-cache-filename', data=[]),
            dcc.Store(id='image-cache-content', data=[]),
            dcc.Store(id='image-cache-date', data=[]),
            dcc.Store(id='test-value1', data=[]),
            dcc.Store(id='test-value2', data=[]),
            dcc.Store(id='test-value3', data=[]),
            dcc.Store(id='save-results-buffer', data=[]),
            dcc.Store(id='label-list', data=LABEL_LIST)
        ],
    )


def visible_thumbnails():
    layout = html.Div(
            [header,
                dbc.Container(
                    [
                        dbc.Row(
                            [
                                dbc.Col(upload_html, width=8), 
                                dbc.Col(dbc.Card(dbc.CardBody([
                                    label_html,
                                    html.Hr(),
                                    additional_options_html,
                                ]
                                )), width='auto', align='top'),
                            ],
                            justify='center'
                        ),
                    ],
                    fluid=True
                ),
            html.Div(browser_cache)
            ],
        )
    return layout


app.layout = visible_thumbnails()


if __name__ == '__main__':
    # host option so docker container listens on all container ports for
    # browser (lets you view the page from outside)
    app.run_server(debug=True, host='0.0.0.0')
