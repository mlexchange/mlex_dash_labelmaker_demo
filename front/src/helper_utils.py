from dash import html
import dash_bootstrap_components as dbc
import plotly.express as px


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


def create_label_component(labels, color_cycle=px.colors.qualitative.Plotly):
    '''
    This function updates the reactive component that contains the label buttons when
        - A new label is added
        - A label is deleted
    Args:
        labels:         List of label names
        color_cycle:    List of label colors
    Returns:
        Reactive components with updated label buttons
    '''
    comp_list = []
    for i, label in enumerate(labels):
        comp_row = dbc.Row(
            [
                dbc.Col(
                    dbc.Button(label,
                               id={'type': 'label-button', 'index': i},
                               style={'background-color': color_cycle[i], 'border-color': color_cycle[i],
                                      'color':'white', 'width': '100%', 'margin-bottom': '5px'}
                               ),
                    width=8
                ),
                dbc.Col(
                    dbc.Button('\u2716',
                               id={'type': 'delete-label-button', 'index': i},
                               style={'background-color': color_cycle[i], 'border-color': color_cycle[i],
                                      'color':'white', 'width': '100%', 'margin-bottom': '5px'}),
                    width=4
                ),
            ],
        )
        comp_list.append(comp_row)
    comp_list.append(
        dbc.Row(
            dbc.Col(
                dbc.Button('Un-label',
                           id='un-label',
                           style={'color':'white', 'width': '100%', 'margin-bottom': '10px', 'margin-top': '10px'})
            )
        )
    )
    return comp_list


def parse_contents(contents, filename, index):
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
                       children=dbc.CardImg(id={'type': 'thumbnail-src', 'index': index},
                                            src=contents,
                                            bottom=False)),
                dbc.CardBody([
                    html.P(id={'type':'thumbnail-name', 'index': index}, children=filename)
                ])
            ],
            outline=False,
            color='white'
        ),
        id={'type': 'thumbnail-wrapper', 'index': index},
        style={'display': 'block'}
    )
    return img_card


def draw_rows(list_of_contents, list_of_names, n_cols, n_rows):
    '''
    This function display the images per page
    Args:
        list_of_contents:   List of contents
        list_of_names:      List of filenames
        n_cols:             Number of columns
        n_rows:             Number of rows
    Returns:
        reactivate component with all the images
    '''
    n_images = len(list_of_contents)
    n_cols = n_cols
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
            row_child.append(dbc.Col(parse_contents(content,
                                                    name,
                                                    j * n_cols + i),
                                     width="{}".format(12 // n_cols),
                                     )
                             )
            visible.append(1)
        children.append(dbc.Row(row_child))
    return children

