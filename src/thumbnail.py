import dash
# from dash.dependencies import Input, Output, State
from dash.dependencies import Input, Output, State, MATCH, ALL
from dash.exceptions import PreventUpdate
import datetime
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import plotly.express as px
from flask import Flask
import templates

external_stylesheets = [dbc.themes.BOOTSTRAP]

server = Flask(__name__)
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

header = templates.header()
# Font and background colors associated with each theme
text_color = {"dark": "#95969A", "light": "#595959"}
card_color = {"dark": "#2D3038", "light": "#FFFFFF"}
LABEL_LIST = ['Arc', 'Peaks', 'Rings', 'Rods']
COLOR_CYCLE = px.colors.qualitative.Plotly
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


# LABEL COMPONENT
def create_label_component(labels, color_cycle=px.colors.qualitative.Plotly, example_img=None):
    comp_list = []
    for i, label in enumerate(labels):
        comp_row = dbc.Row(
            [
                dbc.Col(
                    html.Button(label, id={'type': 'label-button', 'index': i},
                                style={'background-color': color_cycle[i], 'color':'white'}
                                ),
                ),
                dbc.Col(
                    html.Div('<Img>', style={'background-color': color_cycle[i]})
                ),
            ],
        )
        comp_list.append(comp_row)

    return comp_list


label_html = html.Div(
    create_label_component(LABEL_LIST)
)


def parse_contents(contents, filename, date, index):
    img_card = dbc.Card(id={
                        'type': 'thumbnail-card',
                        'index': index
                        },
                        children=[
                            html.A(id={
                                'type': 'thumbnail-image',
                                'index': index
                                },
                               children=dbc.CardImg(src=contents, bottom=False)),
                            dbc.CardBody(
                                [
                                    html.P(filename),
                                ]
                            ),
                        ],
                        outline=False,
                        color='white',
                        )
    return img_card


@app.callback(Output('output-image-upload', 'children'),
              Input('upload-image', 'contents'),
              State('upload-image', 'filename'),
              State('upload-image', 'last_modified'))
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        n_images = len(list_of_contents)
        n_cols = 4
        n_rows = (n_images // n_cols) + 1
        children = []
        for j in range(n_rows):
            row_child = []
            for i in range(n_cols):
                index = j*n_cols + i
                if index >= n_images:
                    # no more images, on hanging row
                    break
                content = list_of_contents[index]
                name = list_of_names[index]
                date = list_of_dates[index]
                row_child.append(dbc.Col(parse_contents(
                    content,
                    name,
                    date,
                    j*n_cols+i),
                                         width="{}".format(12//n_cols),
                                         )
                                 )
            children.append(dbc.Row(row_child))
        return children

@app.callback(
    Output({'type': 'thumbnail-card', 'index': MATCH}, 'color'),
    Input({'type': 'thumbnail-image', 'index': MATCH}, 'n_clicks'),
    State({'type': 'thumbnail-image', 'index': MATCH}, 'id'),
    State('labels', 'data'),
    prevent_initial_call=True
)
def select_thumbnail( value, id_name, labels_data):
    index = id_name['index']
    #choose the right background for not selected
    trigger = dash.callback_context
#    print(trigger.triggered[0])
    # find background color according to label class if thumb is labelled
    color = ''
    for label_key in labels_data:
        print('for: {} {}'.format(label_key, labels_data[label_key]))
        if int(index) in labels_data[label_key]:
            color = COLOR_CYCLE[int(label_key)]
            print('if: {} in {} then color: {}'.format(index, labels_data[label_key],color ))

    if value is None:
        print('index: {}, Not selected'.format(index))
        return ''
    if value % 2 == 1:
        print('index: {}, Selected'.format(index))
        return 'primary'
    elif value % 2 == 0:
        print('index: {}, Not selected/labeled color: {}'.format(index, color))
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
    Input({'type': 'label-button', 'index': ALL}, 'n_clicks_timestamp'),
    State({'type': 'thumbnail-image', 'index': ALL}, 'id'),
    State({'type': 'thumbnail-image', 'index': ALL}, 'n_clicks'),
    State('labels', 'data'), prevent_initial_call=True
)
def label_selected_thumbnails(label_button_n_clicks, thumbnail_image_index, thumbnail_image_select_value, current_labels):
    # find most recent pressed label button

    label_class_value = max(enumerate(label_button_n_clicks), key=lambda t: 0 if t[1] is None else t[1] )[0]
    selected_thumbs = []
    if str(label_class_value) not in current_labels:
        current_labels[str(label_class_value)] = []

    for thumb_id, select_value in zip(thumbnail_image_index, thumbnail_image_select_value):
        index = thumb_id['index']
        if select_value is not None:
            if select_value % 2 == 1:
                selected_thumbs.append(index)

    # need to remove label from other label_class if exists
    other_labels = {key: value[:] for key, value in current_labels.items() if key != label_class_value}
    # create dict of every other label to test
    other_labels.pop(str(label_class_value))
    for thumb_index in selected_thumbs:
        for label in other_labels:
            if thumb_index in other_labels[label]:
                current_labels[label].remove(thumb_index)

    current_labels[str(label_class_value)].extend(selected_thumbs)
    return current_labels
# REACTIVE COMPONENTS FOR UPLOADING FIGURE ###

browser_cache =html.Div(
        id="no-display",
        children=[
            dcc.Store(id='selected', data=''),
            dcc.Store(id='labels', data={}),
        ],
    )
"""
@app.callback(
        [Output('image-store', 'data'),
            Output('image-slider', 'max'),
            ],

        Input('upload-image', 'contents'),
        Input('upload-image', 'filename'),
        State('image-store', 'data'),
        )
def image_upload(
    upload_image_contents,
    upload_image_filename,
    image_store_data):
    if upload_image_contents is None:
        raise PreventUpdate
    print('uploading data...')
    print(upload_image_contents)
    if upload_image_contents is not None:
        for c, n in zip(upload_image_contents, upload_image_filename):
            content_type, content_string = c.split(',')
            image_store_data[n] = (content_type, content_string)
            print('storing: {} \n {}'.format(n,c))
        image_slider_max = len(upload_image_filename)-1
    return [image_store_data, image_slider_max]
    """
app.layout = html.Div(
        [
            header,
            dbc.Container(
                [
                    dbc.Row(
                        [
                            dbc.Col(upload_html, width=8), 
                            dbc.Col(dbc.Card(dbc.CardBody(label_html)), width='auto', align='top'),
                        ],
                        justify='center'
                    ),
                ],
                fluid=True
            ),
            html.Div(
                [
                browser_cache
                ]
            )
        ]
    )

if __name__ == '__main__':
    # host option so docker container listens on all container ports for
    # browser (lets you view the page from outside)
    app.run_server(debug=True, host='0.0.0.0')
