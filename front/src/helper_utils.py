import os
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


def create_label_component(labels, color_cycle=px.colors.qualitative.Plotly, del_button=False):
    '''
    This function updates the reactive component that contains the label buttons when
        - A new label is added
        - A label is deleted
    Args:
        labels:         List of label names
        color_cycle:    List of label colors
        del_button:     Bool that indicates if the labels can be deleted
    Returns:
        Reactive components with updated label buttons
    '''
    comp_list = []
    if del_button:
        for i, label in enumerate(labels):
            comp_row = dbc.Row(
                [
                    dbc.Col(
                        dbc.Button(label,
                                   id={'type': 'label-button', 'index': i},
                                   size="sm",
                                   style={'background-color': color_cycle[i], 'border-color': color_cycle[i],
                                          'color':'white', 'width': '100%', 'margin-bottom': '5px'}
                                   ),
                        width=8
                    ),
                    dbc.Col(
                        dbc.Button('\u2716',
                                   id={'type': 'delete-label-button', 'index': i},
                                   size="sm",
                                   style={'background-color': color_cycle[i], 'border-color': color_cycle[i],
                                          'color':'white', 'width': '100%', 'margin-bottom': '5px'}),
                        width=4
                    ),
                ],
            )
            comp_list.append(comp_row)
    else:
        for i, label in enumerate(labels):
            comp_row = dbc.Row(
                dbc.Col(
                    dbc.Button(label,
                               id={'type': 'label-button', 'index': i},
                               size="sm",
                               style={'background-color': color_cycle[i], 'border-color': color_cycle[i],
                                      'color': 'white', 'width': '100%', 'margin-bottom': '5px'}
                               )
                ),
            )
            comp_list.append(comp_row)
    comp_list.append(
        dbc.Row([
            dbc.Col(
                dbc.Button('Unlabel the Selected',
                           id='un-label',
                           size="sm",
                           style={'color':'white', 'width': '100%', 'margin-bottom': '10px', 'margin-top': '10px'})
            )
        ])
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


def draw_rows(list_of_contents, list_of_names, n_cols, n_rows, show_prob=False, file=None):
    '''
    This function display the images per page
    Args:
        list_of_contents:   List of contents
        list_of_names:      List of filenames
        n_cols:             Number of columns
        n_rows:             Number of rows
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
            name = list_of_names[index]
            if show_prob:
                # warning
                filename = name.split(os.sep)     # this section is needed bc the filenames in mlcoach do not match
                filename = '/'.join(filename[-2:])
                if filename in filenames:
                    probs = str(file.loc[file['filename']==filename].T.iloc[1:].to_string(header=None))
            row_child.append(dbc.Col(parse_contents(content,
                                                    name,
                                                    j * n_cols + i,
                                                    probs),
                                     width="{}".format(12 // n_cols),
                                     )
                             )
            visible.append(1)
        children.append(dbc.Row(row_child))
    return children

