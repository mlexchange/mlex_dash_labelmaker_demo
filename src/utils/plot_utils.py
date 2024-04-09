import dash_bootstrap_components as dbc
import plotly.express as px
from dash import dcc, html
from dash_extensions import EventListener


def create_label_button(label_text, label_color, indx):
    """
    Creates the label button with it's corresponding options
    Args:
        label_text:     Label name to be used as text in the button
        label_color:    Color associated with the label
        indx:           Index to identify the label buttons
    Returns:
        label_comp:     Dash component with label button
    """
    label_comp = dbc.Row(
        [
            dbc.Col(
                dbc.Button(
                    label_text,
                    id={"type": "label-button", "index": indx},
                    n_clicks_timestamp=0,
                    size="sm",
                    style={
                        "background-color": label_color,
                        "border-color": label_color,
                        "color": "black",
                        "width": "100%",
                    },
                ),
                width=10,
                style={"margin-right": "2%", "width": "80%"},
            ),
            dbc.Col(
                dbc.Button(
                    className="fa fa-edit",
                    id={"type": "color-label-button", "index": indx},
                    size="sm",
                    n_clicks_timestamp=0,
                    style={
                        "background-color": label_color,
                        "border-color": label_color,
                        "color": "black",
                        "width": "100%",
                    },
                ),
                width=1,
                style={"margin-right": "2%", "width": "8%"},
            ),
            dbc.Col(
                dbc.Button(
                    className="fa fa-trash",
                    id={"type": "delete-label-button", "index": indx},
                    n_clicks_timestamp=0,
                    size="sm",
                    style={
                        "background-color": label_color,
                        "border-color": label_color,
                        "color": "black",
                        "width": "100%",
                    },
                ),
                width=1,
                style={"width": "8%"},
            ),
            dbc.Tooltip(
                f"Keyboard shortcut: {indx+1}",
                target={"type": "label-button", "index": indx},
                placement="top",
            ),
        ],
        className="g-0",
        style={"background-color": label_color},
    )
    return label_comp


def create_label_component(
    label_list,
    color_cycle=px.colors.qualitative.Light24,
    mlcoach=False,
    progress_values=None,
    progress_labels=None,
    total_num_labeled=None,
):
    """
    This function updates the dash component that contains the label buttons when
        - A new label is added
        - A label is deleted
    Args:
        label_list:         Dictionary of label names, e.g., ['label1', 'label2', ...]
        color_cycle:        List of label colors
        mlcoach:            Bool that indicates if the labels should be arranged as a dropdown
        progress_values:    Current progress values
        progress_labels:    Current progress labels
        total_num_labeled:  Current number of labeled images
    Returns:
        dash components with updated label buttons (sorted by label key number)
    """
    comp_list = []
    progress = []
    label_list = list(label_list)
    if not progress_values:
        progress_values = [0] * len(label_list)
        progress_labels = ["0"] * len(label_list)
        total_num_labeled = "Labeled 0 out of 0 images."
    if not mlcoach:
        for i in range(len(label_list)):
            comp_row = create_label_button(label_list[i], color_cycle[i], i)
            comp_list.append(comp_row)
            progress.append(
                dbc.Progress(
                    id={"type": "label-percentage", "index": i},
                    value=progress_values[i],
                    label=progress_labels[i],
                    style={"background-color": color_cycle[i], "color": "black"},
                    bar=True,
                )
            )
    else:
        options = []
        for label in label_list:
            options.append({"value": label, "label": label})
        comp_list = [
            dcc.Dropdown(id={"type": "mlcoach-label-name", "index": 0}, options=options)
        ]
        for i in range(len(label_list)):
            progress.append(
                dbc.Progress(
                    id={"type": "label-percentage", "index": i},
                    style={"background-color": color_cycle[i], "color": "black"},
                    bar=True,
                )
            )
    comp_list = comp_list + [
        dbc.Button(
            "Unlabel the Selected",
            id="un-label",
            className="ms-auto",
            color="primary",
            size="sm",
            outline=True,
            style={"width": "100%", "margin-bottom": "10px", "margin-top": "10px"},
        ),
        dbc.Label("Labeled images:"),
        dbc.Progress(progress),
        dbc.Label(total_num_labeled, id="total_labeled", style={"margin-top": "5px"}),
    ]
    return comp_list


def parse_contents(index):
    """
    This function creates the dash components to display thumbnail images
    Args:
        index:          Index of the dash component
    Returns:
        dash component
    """
    img_card = html.Div(
        EventListener(
            children=[
                dbc.Card(
                    id={"type": "thumbnail-card", "index": index},
                    children=[
                        html.A(
                            id={"type": "thumbnail-image", "index": index},
                            children=[
                                dbc.CardImg(
                                    id={"type": "thumbnail-src", "index": index},
                                    style={
                                        "width": "100%",
                                        "margin": "auto",
                                        "display": "block",
                                    },
                                    bottom=False,
                                )
                            ],
                        ),
                        dbc.CardBody(
                            [
                                html.P(
                                    id={"type": "thumbnail-name", "index": index},
                                    style={"display": "none"},
                                ),
                                html.P(
                                    id={"type": "thumbnail-prob", "index": index},
                                ),
                            ],
                        ),
                    ],
                    outline=False,
                    style={"display": "none"},
                )
            ],
            id={"type": "double-click-entry", "index": index},
            events=[
                {
                    "event": "dblclick",
                    "props": ["srcElement.className", "srcElement.innerText"],
                }
            ],
            logging=True,
        ),
        id={"type": "thumbnail-wrapper", "index": index},
        style={"display": "block"},
    )
    return img_card


def draw_rows(n_rows, n_cols):
    """
    This function display the images per page
    Args:
        n_rows:             Number of rows
        n_cols:             Number of columns
    Returns:
        dash component with all the images
    """
    n_cols = n_cols
    children = []
    for j in range(n_rows):
        row_child = []
        for i in range(n_cols):
            row_child.append(
                dbc.Col(
                    parse_contents(j * n_cols + i),
                    width="{}".format(12 // n_cols),
                )
            )
        children.append(dbc.Row(row_child, className="g-1"))
    for indx in range(n_rows * n_cols * 3):
        children.append(dcc.Store(id={"type": "cached-images", "index": indx}, data=""))
    return children


def parse_full_screen_content(contents, filename):
    """
    This function creates the dash components to display an image full screen
    Args:
        contents:   Image contents
        filename:   Filename
    Returns:
        dash_component
    """
    img_card = dbc.Card(
        id="full-screen-image",
        children=[
            dbc.CardImg(
                id="full-screen-src",
                src=contents,
                top=True,
                className="align-self-center",
                style={"width": "80vmin", "aspect-ratio": "1/1"},
            ),
            dbc.CardBody([html.P(filename, className="card-text")]),
        ],
    )
    return img_card
