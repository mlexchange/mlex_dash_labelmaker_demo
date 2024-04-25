import os
import time

import dash
import pandas as pd
from dash import ALL, MATCH, Input, Output, State, callback
from dash.exceptions import PreventUpdate
from file_manager.data_project import DataProject

from src.app_layout import NUMBER_OF_ROWS
from src.query import Query
from src.utils.plot_utils import draw_rows, parse_full_screen_content


@callback(
    Output({"type": "thumbnail-card", "index": ALL}, "style"),
    Output({"type": "thumbnail-card", "index": ALL}, "color"),
    Output({"type": "thumbnail-name", "index": ALL}, "children"),
    Output({"type": "thumbnail-src", "index": ALL}, "src"),
    Output({"type": "thumbnail-image", "index": ALL}, "n_clicks"),
    Input("image-order", "data"),
    Input({"base_id": "file-manager", "name": "data-project-dict"}, "data"),
    State("labels-dict", "data"),
    State("similarity-on-off-indicator", "color"),
    State("thumbnail-slider", "value"),
    prevent_initial_call=True,
)
# @cache.memoize(timeout=0)
def update_output(
    image_order,
    data_project_dict,
    # log,
    labels_dict,
    similarity_on_off_color,
    thumbnail_slider_value,
):
    """
    This callback displays images in the front-end
    Args:
        image_order:            Order of the images according to the selected action (sort, hide,
                                new data, etc)
        current_page:           Index of the current page
        log:                    Log toggle
        labels_dict:            Dictionary with labeling information, e.g.
                                {filename1: [label1,label2], ...}
        data_project_dict:      Data project information
        find_similar_images:    Find similar images button, n_clicks
        tab_selection:          Current tab [Manual, Similarity, Probability]
        card_id:                Card ID to identify the card index
        thumbnail_slider_value: Number of images per row
    Returns:
        style:                  Image card style
        color:                  Image card color
        filename:               Filename label in image card
        content:                Content to be displayed in image card
        init_clicks:            Initial number of clicks in image card
    """
    num_imgs_per_page = NUMBER_OF_ROWS * thumbnail_slider_value
    color = "white"
    none_style = {"display": "none"}

    if data_project_dict == {}:
        return (
            [none_style] * num_imgs_per_page,
            [dash.no_update] * num_imgs_per_page,
            [dash.no_update] * num_imgs_per_page,
            [dash.no_update] * num_imgs_per_page,
            [dash.no_update] * num_imgs_per_page,
        )

    data_project = DataProject.from_dict(data_project_dict)
    if len(data_project.datasets) == 0:
        return (
            [none_style] * num_imgs_per_page,
            [dash.no_update] * num_imgs_per_page,
            [dash.no_update] * num_imgs_per_page,
            [dash.no_update] * num_imgs_per_page,
            [dash.no_update] * num_imgs_per_page,
        )

    start = time.time()
    # Load labels and data project
    contents, uris = data_project.read_datasets(image_order, resize=True)
    print(f"Data project done after {time.time()-start}", flush=True)

    colors = [color] * len(contents) + ["white"] * (num_imgs_per_page - len(contents))
    uris = uris + [""] * (NUMBER_OF_ROWS * thumbnail_slider_value - len(contents))
    contents = contents + [""] * (num_imgs_per_page - len(contents))
    styles = [{"margin-bottom": "0px", "margin-top": "10px"}] * len(image_order) + [
        none_style
    ] * (num_imgs_per_page - len(image_order))

    # Find similar images has been activated
    if similarity_on_off_color == "green":
        init_clicks = 1
        color = "primary"
        query = Query(
            num_imgs=data_project.datasets[-1].cumulative_data_count, **labels_dict
        )
        unlabeled_indices = query.hide_labeled()
        init_clicks = [1 if image in unlabeled_indices else 0 for image in image_order]
    else:
        init_clicks = [0] * len(uris)

    init_clicks += [0] * (num_imgs_per_page - len(init_clicks))
    print(f"Display done after {time.time()-start}", flush=True)
    return (
        styles,
        colors,
        uris,
        contents,
        init_clicks,
    )


@callback(
    Output({"type": "thumbnail-prob", "index": ALL}, "children"),
    Output({"type": "thumbnail-prob", "index": ALL}, "style"),
    Input("image-order", "data"),
    Input("probability-model-list", "value"),
    State("probability-collapse", "is_open"),
    State("tab-group", "value"),
    State("thumbnail-slider", "value"),
    prevent_initial_call=True,
)
def update_probabilities(
    image_order,
    probability_model,
    probability_is_open,
    tab_selection,
    thumbnail_slider_value,
):
    if probability_model and tab_selection == "probability":
        num_imgs_per_page = NUMBER_OF_ROWS * thumbnail_slider_value
        df_prob = pd.read_parquet(probability_model)
        probs = df_prob.iloc[image_order]
        probs = [
            " \n".join([f"{col}: {row[col]}" for col in probs.columns])
            for _, row in probs.iterrows()
        ]
        if len(probs) < num_imgs_per_page:
            probs += [""] * (num_imgs_per_page - len(probs))
        prob_style = [
            {
                "display": "block",
                "whiteSpace": "pre-wrap",
                "font-size": "12px",
                "margin-bottom": "0px",
                "margin-top": "1px",
            }
        ] * len(probs)
        return (
            probs,
            prob_style,
        )
    raise PreventUpdate


@callback(
    Output("output-image-upload", "children"),
    Input("thumbnail-slider", "value"),
)
def update_rows(thumbnail_slider_value):
    """
    This callback prepares the image cards according to the number of rows selected by the user
    Args:
        thumbnail_slider_value: Number of images per row
    Returns:
        children:               Images to be displayed in front-end according to the current page
                                index and # of columns
    """
    children = draw_rows(NUMBER_OF_ROWS, thumbnail_slider_value)
    return children


@callback(
    Output({"type": "full-screen-modal", "index": ALL}, "children"),
    Output({"type": "full-screen-modal", "index": ALL}, "is_open"),
    Output({"type": "double-click-entry", "index": ALL}, "n_events"),
    Input({"type": "double-click-entry", "index": ALL}, "n_events"),
    State({"base_id": "file-manager", "name": "data-project-dict"}, "data"),
    State({"base_id": "file-manager", "name": "log-toggle"}, "on"),
    State("image-order", "data"),
    prevent_initial_call=True,
)
def full_screen_thumbnail(double_click, data_project_dict, log, image_order):
    """
    This callback opens the modal pop-up window with the full size image that was double-clicked
    Args:
        double_click:               List of number of times that every card has been double-clicked
        data_project_dict:          Data project information
        log:                        Log toggle
    Returns:
        contents:                   Contents for pop-up window
        open_modal:                 Open/close modal
        double_click:               Resets the number of double-clicks to zero
    """
    if 1 not in double_click:
        raise PreventUpdate
    data_project = DataProject.from_dict(data_project_dict)
    img_contents, img_uri = data_project.read_datasets(
        [image_order[double_click.index(1)]], resize=False, log=log
    )
    contents = parse_full_screen_content(img_contents, img_uri)
    return [contents], [True], [0] * len(double_click)


@callback(
    Output({"type": "thumbnail-card", "index": MATCH}, "color", allow_duplicate=True),
    Input({"type": "thumbnail-image", "index": MATCH}, "n_clicks"),
    Input("labels-dict", "data"),
    State("color-cycle", "data"),
    State({"type": "thumbnail-card", "index": MATCH}, "color"),
    State({"type": "thumbnail-card", "index": MATCH}, "id"),
    State("image-order", "data"),
    prevent_initial_call=True,
)
def select_thumbnail(
    value, labels_dict, color_cycle, current_color, card_id, image_order
):
    """
    This callback assigns a color to thumbnail cards in the following scenarios:
        - An image has been selected, but no label has been assigned (blue)
        - An image has been labeled (label color)
        - An image has been unselected or unlabeled (no color)
    Args:
        value:                      Thumbnail card that triggered the callback (n_clicks)
        labels_dict:                Dictionary of labeled images, as follows: {'img1':[], 'img2':[]}
        color_cycle:                List that contains the color cycle associated with the labels
        current_color:              Current color in thumbnail card
        card_id:                    Card ID to identify the card index
        image_order:                Order of the images according to the selected action (sort,hide)
    Returns:
        thumbnail_color:            Color of thumbnail card
    """
    changed_id = dash.callback_context.triggered[0]["prop_id"]
    if value is None or changed_id == "un-label.n_clicks":
        color = current_color
    elif value % 2 == 1:
        color = "primary"
    else:
        card_index = card_id["index"]
        color = "white"
        if card_index < len(image_order):
            if str(image_order[card_index]) in labels_dict["labels_dict"].keys():
                label = labels_dict["labels_dict"][str(image_order[card_index])]
                if len(label) > 0:
                    label_indx = labels_dict["labels_list"].index(label[0])
                    color = color_cycle[label_indx]
    if color == current_color:
        return dash.no_update
    return color


@callback(
    Output({"type": "thumbnail-image", "index": ALL}, "n_clicks", allow_duplicate=True),
    Input({"type": "label-button", "index": ALL}, "n_clicks_timestamp"),
    Input("un-label", "n_clicks"),
    Input("confirm-un-label-all", "n_clicks"),
    Input("keybind-event-listener", "event"),
    State({"type": "thumbnail-image", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def deselect(
    label_button_trigger, unlabel_n_clicks, unlabel_all, keybind_label, thumb_clicked
):
    """
    This callback deselects a thumbnail card
    Args:
        label_button_trigger:   Label button
        unlabel_n_clicks:       Un-label button
        unlabel_all:            Un-label all the images
        keybind_label:          Keyword entry
        thumb_clicked:          Selected thumbnail card indice, e.g., [0,1,1,0,0,0]
    Returns:
        Modify the number of clicks for a specific thumbnail card
    """
    changed_id = dash.callback_context.triggered[0]["prop_id"]
    keybind_is_valid = True
    if changed_id == "keybind-event-listener.event":
        keybind_is_valid = keybind_label["key"].isdigit() and int(
            keybind_label["key"]
        ) - 1 in range(len(label_button_trigger))
        if not keybind_is_valid:
            raise PreventUpdate
    if (
        all(x is None for x in label_button_trigger)
        and unlabel_n_clicks is None
        and unlabel_all is None
        and not keybind_is_valid
    ):
        return [dash.no_update] * len(thumb_clicked)
    return [0 for thumb in thumb_clicked]


@callback(
    Output("button-hide", "children"),
    Input("button-hide", "n_clicks"),
    State("button-hide", "children"),
    prevent_initial_call=True,
)
def update_hide_button_text(n_clicks, current_text):
    if current_text == "Hide" and n_clicks != 0:
        return "Unhide"
    return "Hide"


@callback(
    Output("button-sort", "children"),
    Input("button-sort", "n_clicks"),
    State("button-sort", "children"),
    prevent_initial_call=True,
)
def update_sort_button_text(n_clicks, current_text):
    if current_text == "Sort" and n_clicks != 0:
        return "Undo Sort"
    return "Sort"


@callback(
    Output("similarity-on-off-indicator", "color", allow_duplicate=True),
    Output("similarity-on-off-indicator", "label", allow_duplicate=True),
    Input("find-similar-unsupervised", "n_clicks"),
    State("similarity-model-list", "value"),
    prevent_initial_call=True,
)
def display_indicator_on(n_clicks, similarity_model):
    """
    This callback controls the light indicator in the DataClinic tab, which indicates whether the
    similarity-based image display is ON or OFF
    Args:
        n_clicks:           The button "Find Similar Images" triggers this callback
        similarity_model:   Selected similarity-based model
    Returns:
        color:              Indicator color
        label:              Indicator label
    """
    if similarity_model is None:
        raise PreventUpdate
    file_path = ".current_image_order.hdf5"
    if os.path.exists(file_path):
        os.remove(file_path)
    return "green", "Find Similar Images: ON"


@callback(
    Output("similarity-on-off-indicator", "color"),
    Output("similarity-on-off-indicator", "label"),
    Input("exit-similar-unsupervised", "n_clicks"),
    Input({"base_id": "file-manager", "name": "total-num-data-points"}, "data"),
    Input("button-hide", "n_clicks"),
    Input("button-sort", "n_clicks"),
    State("similarity-on-off-indicator", "color"),
)
def display_indicator_off(n_clicks, num_data_points, hide, sort, current_color):
    """
    This callback controls the light indicator in the DataClinic tab, which indicates whether the
    similarity-based image display is ON or OFF
    Args:
        n_clicks:        The button "Exit Similar Images" triggers this callback
        num_data_points: Total number of data points
        hide:            Hide button
        sort:            Sort button
        current_color:   Current indicator color
    Returns:
        color:           Indicator color
        label:           Indicator label
    """
    if current_color == "#596D4E":
        raise PreventUpdate
    file_path = ".current_image_order.hdf5"
    if os.path.exists(file_path):
        os.remove(file_path)
    return "#596D4E", "Find Similar Images: OFF"


@callback(
    Output("manual-collapse", "is_open"),
    Output("probability-collapse", "is_open"),
    Output("similarity-collapse", "is_open"),
    Output("label-buttons-collapse", "is_open"),
    Output("goto-webpage-collapse", "is_open"),
    Output("goto-webpage", "children"),
    Output("previous-tab", "data"),
    Input("tab-group", "value"),
    State("previous-tab", "data"),
)
def toggle_tabs_collapse(tab_value, previous_tab):
    """
    This callback toggles the tabs according to the selected labeling method
    """
    keys = ["manual", "probability", "similarity"]
    tabs = {key: False for key in keys}
    tabs[tab_value] = True
    if tab_value == "similarity":
        tabs["manual"] = True
    show_label_buttons = True
    goto_webpage = {"manual": False, "probability": True, "similarity": True}
    button_name = "Go to MLCoach"
    if tab_value == "similarity":
        button_name = "Go to DataClinic"
    if not previous_tab:
        previous_tab = ["init", tab_value]
    else:
        previous_tab.append(tab_value)
    return (
        tabs["manual"],
        tabs["probability"],
        tabs["similarity"],
        show_label_buttons,
        goto_webpage[tab_value],
        button_name,
        previous_tab,
    )
