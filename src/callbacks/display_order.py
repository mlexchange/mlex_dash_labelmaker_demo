import math
import os

import dash
import h5py
import numpy as np
from dash import ALL, Input, Output, State, callback
from dash.exceptions import PreventUpdate

from src.app_layout import NUMBER_OF_ROWS
from src.query import Query


@callback(
    Output("image-order", "data"),
    Input({"base_id": "file-manager", "name": "total-num-data-points"}, "data"),
    Input("current-page", "value"),
    Input("similarity-on-off-indicator", "color"),
    Input("button-hide", "n_clicks"),
    Input("button-sort", "n_clicks"),
    State("probability-collapse", "is_open"),
    State("tab-group", "value"),
    State("previous-tab", "data"),
    State("thumbnail-slider", "value"),
    State("similarity-model-list", "value"),
    State({"type": "thumbnail-image", "index": ALL}, "n_clicks_timestamp"),
    State({"type": "thumbnail-image", "index": ALL}, "n_clicks"),
    State("labels-dict", "data"),
    State("image-order", "data"),
    prevent_initial_call=True,
)
def update_image_order(
    num_imgs,
    current_page,
    similarity_on_off_color,
    button_hide_n_clicks,
    button_sort_n_clicks,
    probability_is_open,
    tab_selection,
    previous_tab,
    thumbnail_slider_value,
    similarity_model,
    timestamp,
    thumb_n_clicks,
    labels_dict,
    current_image_order,
):
    """
    This callback arranges the image order according to the following actions:
        - New content is uploaded
        - Buttons sort or hidden are selected
        - Find similar images display has been activated or deactivated
    Args:
        num_imgs:                   Number of images in the dataset
        current_page:               Current page number
        similarity_on_off_color:    Color of the similarity-based search button
        button_hide_n_clicks:       Hide button
        button_sort_n_clicks:       Sort button
        probability_is_open:        Probability tab is open
        tab_selection:              Current tab [Manual, Similarity, Probability]
        previous_tab:               Previous tab
        thumbnail_slider_value:     Number of thumbnails per row
        similarity_model:           Selected similarity-based model
        timestamp:                  Timestamps of selected images in current page - to find similar
                                    images. Currently, one 1 image is selected for this operation
        thumb_n_clicks:             Number of clicks per card/filename in current page
        labels_dict:                Dictionary with labeling information, e.g.
                                    {filename1: [label1,label2], ...}
    Returns:
        image_order:                Order of the images according to the selected action
                                    (sort, hide, new data, etc)
    """
    start_indx = NUMBER_OF_ROWS * thumbnail_slider_value * current_page
    max_indx = min(start_indx + NUMBER_OF_ROWS * thumbnail_slider_value, num_imgs)
    indices = list(range(start_indx, max_indx))
    if os.path.exists(".current_image_order.hdf5"):
        with h5py.File(".current_image_order.hdf5", "r") as f:
            ordered_indx = f["indices"]
            if len(ordered_indx) < len(indices):
                indices = indices[: len(ordered_indx)]
            image_order = ordered_indx[indices]
    elif similarity_on_off_color == "green":
        query = Query(num_imgs=num_imgs, **labels_dict)
        for indx, n_click in enumerate(thumb_n_clicks):
            if n_click % 2 == 0 or timestamp[indx] is None:
                timestamp[indx] = 0
        clicked_ind = timestamp.index(max(timestamp))  # retrieve clicked index
        if clicked_ind is not None and similarity_model:
            if similarity_model:
                ordered_indx = query.similarity_search(
                    similarity_model,
                    current_image_order[int(clicked_ind)],
                )
                with h5py.File(".current_image_order.hdf5", "w") as f:
                    store_ordered_indx = np.array(ordered_indx)
                    f.create_dataset("indices", data=store_ordered_indx)
                if len(ordered_indx) < len(indices):
                    indices = indices[: len(ordered_indx)]
                image_order = ordered_indx[indices]
        else:
            raise PreventUpdate
    elif button_hide_n_clicks and button_hide_n_clicks % 2 == 1:
        query = Query(num_imgs=num_imgs, **labels_dict)
        image_order = query.hide_labeled()
        with h5py.File(".current_image_order.hdf5", "w") as f:
            store_ordered_indx = np.array(image_order)
            f.create_dataset("indices", data=store_ordered_indx)
        image_order = [image_order[i] for i in indices]
    elif button_sort_n_clicks and button_sort_n_clicks % 2 == 1:
        query = Query(num_imgs=num_imgs, **labels_dict)
        image_order = query.sort_labeled()
        with h5py.File(".current_image_order.hdf5", "w") as f:
            store_ordered_indx = np.array(image_order)
            f.create_dataset("indices", data=store_ordered_indx)
        image_order = [image_order[i] for i in indices]
    else:
        image_order = indices
    return image_order


@callback(
    Output("image-order", "data", allow_duplicate=True),
    Input("button-hide", "n_clicks"),
    Input("button-sort", "n_clicks"),
    prevent_initial_call=True,
)
def undo_sort_or_hide_labeled_images(
    button_hide_n_clicks,
    button_sort_n_clicks,
):
    if os.path.exists(".current_image_order.hdf5"):
        os.remove(".current_image_order.hdf5")
    return dash.no_update


@callback(
    Output("current-page", "value", allow_duplicate=True),
    Input({"base_id": "file-manager", "name": "total-num-data-points"}, "data"),
    Input("first-page", "n_clicks"),
    Input("find-similar-unsupervised", "n_clicks"),
    prevent_initial_call=True,
)
def go_to_first_page(
    num_imgs,
    button_first_page,
    button_find_similar_images,
):
    """
    Update the current page to the first page
    """
    return 0


@callback(
    Output("current-page", "value", allow_duplicate=True),
    Input("prev-page", "n_clicks"),
    State("current-page", "value"),
    prevent_initial_call=True,
)
def go_to_prev_page(
    button_prev_page,
    current_page,
):
    """
    Update the current page to the previous page
    """
    current_page = current_page - 1
    return current_page


@callback(
    Output("current-page", "value", allow_duplicate=True),
    Input("next-page", "n_clicks"),
    State("current-page", "value"),
    prevent_initial_call=True,
)
def go_to_next_page(
    button_next_page,
    current_page,
):
    """
    Update the current page to the next page
    """
    current_page = current_page + 1
    return current_page


@callback(
    Output("current-page", "value", allow_duplicate=True),
    Input("last-page", "n_clicks"),
    State({"base_id": "file-manager", "name": "total-num-data-points"}, "data"),
    State("thumbnail-slider", "value"),
    prevent_initial_call=True,
)
def go_to_last_page(
    button_last_page,
    num_imgs,
    thumbnail_slider_value,
):
    """
    Update the current page to the last page
    """
    current_page = math.ceil(num_imgs / (NUMBER_OF_ROWS * thumbnail_slider_value)) - 1
    return current_page


@callback(
    Output("current-page", "value", allow_duplicate=True),
    Input("current-page", "value"),
    State({"base_id": "file-manager", "name": "total-num-data-points"}, "data"),
    State("thumbnail-slider", "value"),
    prevent_initial_call=True,
)
def go_to_users_input(
    current_page,
    num_imgs,
    thumbnail_slider_value,
):
    """
    Update the current page to user's direct input
    """
    max_num_pages = math.ceil((num_imgs // thumbnail_slider_value) / NUMBER_OF_ROWS)
    if current_page > max_num_pages:
        current_page = max_num_pages - 1
    return current_page


@callback(
    [
        [Output("first-page", "disabled"), Output("prev-page", "disabled")],
        [Output("next-page", "disabled"), Output("last-page", "disabled")],
        Input("current-page", "value"),
        State({"base_id": "file-manager", "name": "total-num-data-points"}, "data"),
        State("thumbnail-slider", "value"),
    ],
    prevent_initial_call=True,
)
def disable_buttons(
    current_page,
    num_imgs,
    thumbnail_slider_value,
):
    """
    Disable first and last page buttons based on the current page
    """
    max_num_pages = math.ceil((num_imgs // thumbnail_slider_value) / NUMBER_OF_ROWS)
    return (
        2 * [current_page == 0],
        2 * [max_num_pages <= current_page + 1],
    )
