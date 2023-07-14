import io, os, time
import pathlib, base64, math

import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State, MATCH, ALL
from dash.exceptions import PreventUpdate
from flask_caching import Cache
import numpy as np
import pandas as pd
from PIL import Image
import requests
import uuid

from helper_utils import create_label_component, draw_rows, get_trained_models_list, \
                         parse_full_screen_content
from labels import Labels
from query import Query
from app_layout import app, DOCKER_DATA
from file_manager.data_project import DataProject

# Font and background colors associated with each theme
text_color = {"dark": "#95969A", "light": "#595959"}
card_color = {"dark": "#2D3038", "light": "#FFFFFF"}

NUMBER_OF_ROWS = 4
USER = 'admin'
LOCAL_DATA = str(os.environ['DATA_DIR'])
DOCKER_HOME = str(DOCKER_DATA) + '/'
LOCAL_HOME = str(LOCAL_DATA)


#================================== callback functions ===================================
@app.callback(
    Output("modal-help", "is_open"),
    Output("help-body", "children"),

    Input("button-help", "n_clicks"),
    Input("tab-help-button", "n_clicks"),

    State("modal-help", "is_open"),
    State("tab-group", "value"),
    prevent_initial_call=True
)
def toggle_help_modal(main_n_clicks, tab_n_clicks, is_open, tab_value):
    changed_id = dash.callback_context.triggered[0]['prop_id']
    # Main instructions
    if 'button-help.n_clicks' in changed_id:
        body_txt = [dbc.Label('1. Please use the File Manager on the left to import/load the dataset \
                               of interest.'),
                    dbc.Label('2. Click the DataClinic tab. Use the "Go to" button to open DataClinic \
                              and train unsupervised learning algorithms to estimate image similarity. \
                              Then, come back to the DataClinic tab in Label Maker to load the results \
                              and label batches of similar images.'),
                    dbc.Label('3. Click the Manual tab to manually label images or make corrections \
                              to the previous step. Save the current labels by clicking the button \
                              Save Labels to Disk.'),
                    dbc.Label('4. Click the MLCoach tab. Use the "Go to" button to open MLCoach and \
                              do supervised learning for image classification using the previously \
                              saved labels. Then, come back to the MLCoach tab in Label Maker to load \
                              the results and label the full dataset using their estimated probabilities. \
                              Click the Manual tab to manually label images or make corrections to \
                              the previous step.'),
                    dbc.Label('5. Finally, save all the labels by clicking the button Save Labels to \
                              Disk.')]
    # Tab instructions
    else:
        if tab_value == 'data_clinic':
            body_txt = [dbc.Label('1. Select a trained model to start.', 
                                  className='mr-2'),
                        dbc.Label('2. Click on the image of interest. Then click Find Similar Images \
                                  button below.', 
                                  className='mr-2'),
                        dbc.Label('3. The image display updates according to the trained model results. \
                                  Label as usual.', 
                                  className='mr-2'),
                        dbc.Label('4. To exit this similarity based display, click Stop Find Similar \
                                  Images.', 
                                  className='mr-2')]
        
        else:           # mlcoach
            body_txt = [dbc.Label('1. Select a trained model to start.', 
                                  className='mr-2'),
                        dbc.Label('2. Select the label name to be assigned accross the dataset in \
                                  the dropdown beneath Probability Threshold.', 
                                  className='mr-2'),
                        dbc.Label('3. Use the slider to setup the probability threshold.', 
                                  className='mr-2'),
                        dbc.Label('4. Click Label with Threshold.', 
                                  className='mr-2')]

    return not is_open, body_txt


@app.callback(
    Output("manual-collapse", "is_open"),
    Output("mlcoach-collapse", "is_open"),
    Output("data-clinic-collapse", "is_open"),
    Output("label-buttons-collapse", "is_open"),
    Output("goto-webpage-collapse", "is_open"),
    Output("goto-webpage", "children"),
    Output('previous-tab', 'data'),

    Input("tab-group", "value"),

    State("previous-tab", "data")
)
def toggle_tabs_collapse(tab_value, previous_tab):
    keys = ['manual', 'mlcoach', 'clinic']
    tabs = {key: False for key in keys}
    tabs[tab_value] = True
    if tab_value == 'clinic':
        tabs['manual'] = True
    show_label_buttons = True
    goto_webpage = {'manual': False, 'mlcoach': True, 'clinic': True}
    button_name = 'Go to MLCoach'
    if tab_value == 'clinic':
        button_name = 'Go to DataClinic'
    if not previous_tab:
        previous_tab = ['init', tab_value]
    else:
        previous_tab.append(tab_value)
    return tabs['manual'], tabs['mlcoach'], tabs['clinic'], \
           show_label_buttons, goto_webpage[tab_value], button_name, previous_tab


app.clientside_callback(
    """
    function(n_clicks, tab_value, mlcoach_url, data_clinic_url) {
        if (tab_value == 'mlcoach') {
            window.open(mlcoach_url);
        } else if (tab_value == 'clinic') {
            window.open(data_clinic_url);
        } 
        return '';
    }
    """,
    Output('dummy1', 'data'),
    Input('goto-webpage', 'n_clicks'),
    State('tab-group', 'value'),
    State('mlcoach-url', 'data'),
    State('data-clinic-url', 'data'),
    prevent_initial_call=True
)


@app.callback(
    Output("modal-un-label", "is_open"),
    Output({'base_id': 'file-manager', 'name': "confirm-update-data"}, "data"),

    Input("un-label-all", "n_clicks"),
    Input("confirm-un-label-all", "n_clicks"),
    Input({'base_id': 'file-manager', 'name': "import-dir"}, "n_clicks"),
    Input({'base_id': 'file-manager', 'name': "clear-data"}, "n_clicks"),

    State("labels-dict", "data"),
)
def toggle_modal_unlabel_warning(unlabel_all_clicks, confirm_unlabel_all_clicks, n_clear, n_import, \
                                 labels_dict):
    '''
    This callback toggles a modal with unlabeling warnings
    Args:
        unlabel_all_clicks:         Number of clicks of unlabel all button
        confirm_unlabel_all_clicks: Number of clicks of confirm unlabel all button
        n_clear:                    Number of clicks of clear data button
        n_import:                   Number of clicks of import button
        labels_dict:                Dictionary with labeling information, e.g. 
                                    {filename1: [label1,label2], ...}
    Returns:
        modal_is_open:              [Bool] modal unlabel warning is open
        reset_labels:               Flag indicating that the labels should be reset
        update_data:                Flag indicating that new data can be imported from file manager
        clear_data:                 Flag indicating that the data can be cleared
    '''
    changed_id = dash.callback_context.triggered[0]['prop_id']
    modal_is_open = False
    update_data = True
    labels = Labels(**labels_dict)
    if changed_id != 'confirm-un-label-all.n_clicks' and np.sum(np.array(list(labels.num_imgs_per_label.values())))>0:      # if there are labels
        if changed_id == 'un-label-all.n_clicks':
            update_data = dash.no_update
        else:
            update_data = False
        modal_is_open = True
    return modal_is_open, update_data


@app.callback(
    Output("button-hide", "children"),
    Input("button-hide", "n_clicks"),
    State("button-hide", "children"),
    prevent_initial_call=True
)
def toggle_modal_unlabel(n1, current_text):
    if current_text == 'Hide' and n1 != 0:
        return 'Unhide'
    return 'Hide'


@app.callback(
    Output('on-off-display', 'color'),
    Output('on-off-display', 'label'),

    Input('find-similar-unsupervised', 'n_clicks'),
)
def display_indicator(n_clicks):
    '''
    This callback controls the light indicator in the DataClinic tab, which indicates whether the 
    similarity-based image display is ON or OFF
    Args:
        n_clicks:   The button "Find Similar Images" triggers this callback
    Returns:
        color:      Indicator color
        label:      Indicator label
    '''
    if n_clicks == 0 or n_clicks == None:
        return '#596D4E', 'Find Similar Images: OFF'
    else:
        return 'green', 'Find Similar Images: ON'


@app.callback(
    Output('image-order','data'),
    Output('find-similar-unsupervised', 'n_clicks'),
    Output('button-hide', 'n_clicks'),
    Output('loading-display', 'style'),

    Input('exit-similar-unsupervised', 'n_clicks'),
    Input('find-similar-unsupervised', 'n_clicks'),
    Input('labels-dict', 'data'),
    Input('button-hide', 'n_clicks'),
    Input('button-sort', 'n_clicks'),
    Input('tab-group', 'value'),

    State({'type': 'thumbnail-name', 'index': ALL}, 'children'),
    State({'type': 'thumbnail-image', 'index': ALL}, 'n_clicks_timestamp'),
    State({'type': 'thumbnail-image', 'index': ALL}, 'n_clicks'),
    State('data-clinic-model-list', 'value'),
    State('image-order','data'),
    prevent_initial_call=True)
def display_index(exit_similar_images, find_similar_images, labels_dict, button_hide_n_clicks, \
                  button_sort_n_clicks, tab_selection, thumbnail_name_children, timestamp, \
                  thumb_n_clicks, data_clinic_model, image_order):
    '''
    This callback arranges the image order according to the following actions:
        - New content is uploaded
        - Buttons sort or hidden are selected
        - Find similar images display has been activated or deactivated
    Args:
        exit_similar_images:        Button "Exit Find Similar Images" has been clicked
        find_similar_images:        Button "Find Similar Images" has been clicked
        labels_dict:                Dictionary with labeling information, e.g. 
                                    {filename1: [label1,label2], ...}
        button_hide_n_clicks:       Hide button
        button_sort_n_clicks:       Sort button
        tab_selection:              Current tab [Manual, Data Clinic, MLCoach]
        thumbnail_name_children:    Filenames of images in current page
        timestamp:                  Timestamps of selected images in current page - to find similar 
                                    images. Currently, one 1 image is selected for this operation
        thumb_n_clicks:             Number of clicks per card/filename in current page
        data_clinic_model:          Selected data clinic model
        image_order:                Order of the images according to the selected action 
                                    (sort, hide, new data, etc)
    Returns:
        image_order:                Order of the images according to the selected action 
                                    (sort, hide, new data, etc)
        data_access_open:           Closes the reactive component to select the data access 
                                    (upload vs. directory)
    '''
    changed_id = dash.callback_context.triggered[0]['prop_id']
    query = Query(**labels_dict)
    similar_img_clicks = dash.no_update
    button_hide = dash.no_update
    num_imgs = len(query.labels_dict)
    image_order = list(range(num_imgs))
    if 'find-similar-unsupervised.n_clicks' in changed_id:
        for indx, n_click in enumerate(thumb_n_clicks):
            if n_click%2 == 0 or timestamp[indx] is None:
                timestamp[indx] = 0
        clicked_ind = timestamp.index(max(timestamp))       # retrieve clicked index
        if clicked_ind is not None and data_clinic_model:
            if data_clinic_model:
                image_order = query.similarity_search(thumbnail_name_children[int(clicked_ind)])
        else:                                      # if no image is selected, no update is triggered
            return dash.no_update, 0, dash.no_update, dash.no_update
    elif changed_id == 'button-hide.n_clicks':
        similar_img_clicks = 0
        if button_hide_n_clicks % 2 == 1:
            image_order = query.hide_labeled()
        else:
            image_order = list(range(num_imgs))
    elif changed_id == 'exit-similar-unsupervised.n_clicks' or tab_selection=='mlcoach':
        button_hide = 0
        similar_img_clicks = 0
        image_order = list(range(num_imgs))
    elif changed_id == 'button-sort.n_clicks':
        button_hide = 0
        similar_img_clicks = 0
        image_order = query.sort_labels()
    return image_order, similar_img_clicks, button_hide, {'visibility': 'visible'}


@app.callback([
    Output('output-image-upload', 'children'),
    Output('prev-page', 'disabled'),
    Output('next-page', 'disabled'),
    Output('current-page', 'data'),

    Input('image-order', 'data'),
    Input('thumbnail-slider', 'value'),
    Input('prev-page', 'n_clicks'),
    Input('next-page', 'n_clicks'),
    # Input({'base_id': 'file-manager', 'name': 'tiled-switch'}, 'on'),
    Input('mlcoach-collapse', 'is_open'),
    Input('mlcoach-model-list', 'value'),
    Input('labels-dict', 'data'),

    State({'base_id': 'file-manager', 'name': 'docker-file-paths'},'data'),
    State('find-similar-unsupervised', 'n_clicks'),
    State('current-page', 'data'),
    # State('import-dir', 'n_clicks'),
    State('tab-group', 'value'),
    State('previous-tab', 'data')],
    prevent_initial_call=True)
def update_output(image_order, thumbnail_slider_value, button_prev_page, button_next_page, 
                  ml_coach_is_open, mlcoach_model, labels_dict, file_paths, \
                  find_similar_images, current_page, #import_n_clicks, \
                  tab_selection, previous_tab):
    '''
    This callback displays images in the front-end
    Args:
        image_order:            Order of the images according to the selected action (sort, hide, 
                                new data, etc)
        thumbnail_slider_value: Number of images per row
        button_prev_page:       Go to previous page
        button_next_page:       Go to next page
        file_paths:             Absolute file paths selected from path table
        tiled_on:               Tiled has been selected to load the dataset
        ml_coach_is_open:       MLCoach is the labeling method
        mlcoach_model:          Selected MLCoach model
        find_similar_images:    Find similar images button, n_clicks
        current_page:           Index of the current page
        import_n_clicks:        Button for importing the selected paths
        labels_name_data:       Dictionary of labeled images (docker path), as follows: 
                                {label: list of image filenames}
        tab_selection:          Current tab [Manual, Data Clinic, MLCoach]
        previous_tab:           List of previous tab selection [Manual, Data Clinic, MLCoach]
    Returns:
        children:               Images to be displayed in front-end according to the current page 
                                index and # of columns
        prev_page:              Enable/Disable previous page button if current_page==0
        next_page:              Enable/Disable next page button if current_page==max_page
        current_page:           Update current page index if previous or next page buttons were selected
    '''
    start = time.time()
    changed_id = dash.callback_context.triggered[0]['prop_id']
    # update current page if necessary
    if changed_id == 'image-order.data':
        current_page = 0
    if changed_id == 'prev-page.n_clicks':
        current_page = current_page - 1
    if changed_id == 'next-page.n_clicks':
        current_page = current_page + 1
    if changed_id == 'mlcoach-collapse.is_open':
        if tab_selection=='mlcoach':        # if the previous tab is mlcoach, the display should be 
            current_page = 0                # updated to remove the probability list per image
        elif previous_tab[-2] != 'mlcoach':
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    children = []
    labels = Labels(**labels_dict)
    data_project = DataProject()
    data_project.init_from_dict(file_paths)
    num_imgs = len(image_order)
    start_indx = NUMBER_OF_ROWS * thumbnail_slider_value * current_page
    max_indx = min(start_indx + NUMBER_OF_ROWS * thumbnail_slider_value, num_imgs)
    new_contents = []
    new_filenames = []
    if num_imgs>0:
        data_set = data_project.data
        new_contents = []
        new_filenames = []
        for indx in range(start_indx, max_indx):
            content, filename = data_set[image_order[indx]].read_data()
            new_contents.append(content)
            new_filenames.append(filename)
    if mlcoach_model and tab_selection=='mlcoach':
        if mlcoach_model.split('.')[-1] == 'csv':
            df_prob = pd.read_csv(mlcoach_model)
        else:
            df_prob = pd.read_parquet(mlcoach_model)
        children = draw_rows(new_contents, new_filenames, NUMBER_OF_ROWS, thumbnail_slider_value,
                                ml_coach_is_open, df_prob)
    elif find_similar_images:
        pre_highlight = True
        filenames = new_filenames
        for name in filenames:                 # if there is one label in page, do not pre-highlight
            if labels.labels_dict[name] != []:
                pre_highlight = False
        if find_similar_images>0 and pre_highlight:
            children = draw_rows(new_contents, new_filenames, NUMBER_OF_ROWS, \
                                 thumbnail_slider_value, data_clinic=True)
        else:
            children = draw_rows(new_contents, new_filenames, NUMBER_OF_ROWS, \
                                 thumbnail_slider_value)
    else:
        children = draw_rows(new_contents, new_filenames, NUMBER_OF_ROWS, thumbnail_slider_value)
    print(f'Total time to display images: {time.time() - start}, with changed if: {changed_id}')
    return children, current_page==0, \
           math.ceil((num_imgs//thumbnail_slider_value)/NUMBER_OF_ROWS)<=current_page+1, \
           current_page


@app.callback(
    Output({'type': 'thumbnail-card', 'index': MATCH}, 'color'),

    Input({'type': 'thumbnail-image', 'index': MATCH}, 'n_clicks'),
    Input('labels-dict', 'data'),

    State({'type': 'thumbnail-name', 'index': MATCH}, 'children'),
    State('color-cycle', 'data'),
)
def select_thumbnail(value, labels_dict, thumbnail_name_children, color_cycle):
    '''
    This callback assigns a color to thumbnail cards in the following scenarios:
        - An image has been selected, but no label has been assigned (blue)
        - An image has been labeled (label color)
        - An image has been unselected or unlabeled (no color)
    Args:
        value:                      Thumbnail card that triggered the callback (n_clicks)
        labels_dict:                Dictionary of labeled images, as follows: {'img1':[], 'img2':[]}
        thumbnail_name_children:    Filename in selected thumbnail
    Returns:
        thumbnail_color:            Color of thumbnail card
    '''
    changed_id = dash.callback_context.triggered[0]['prop_id']
    labels = Labels(**labels_dict)
    color = ''
    if len(labels.labels_dict)==0 or value is None or changed_id == 'un-label.n_clicks':
        return color
    elif value % 2 == 1:
        return 'primary'
    else:
        filename = thumbnail_name_children
        try:
            label = labels.labels_dict[filename]
        except:
            label = []
        if len(label)>0:
            label_indx = labels.labels_list.index(label[0])
            color = color_cycle[label_indx]
        return color


@app.callback(
    Output({'type': 'thumbnail-image', 'index': ALL}, 'n_clicks'),

    Input({'type': 'label-button', 'index': ALL}, 'n_clicks_timestamp'),
    Input('un-label', 'n_clicks'),
    Input('confirm-un-label-all', 'n_clicks'),

    State({'type': 'thumbnail-image', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def deselect(label_button_trigger, unlabel_n_clicks, unlabel_all, thumb_clicked):
    '''
    This callback deselects a thumbnail card
    Args:
        label_button_trigger:   Label button
        unlabel_n_clicks:       Un-label button
        unlabel_all:            Un-label all the images
        thumb_clicked:          Selected thumbnail card indice, e.g., [0,1,1,0,0,0]
    Returns:
        Modify the number of clicks for a specific thumbnail card
    '''
    if all(x is None for x in label_button_trigger) and unlabel_n_clicks is None and \
        unlabel_all is None:
        return [dash.no_update]*len(thumb_clicked)
    return [0 for thumb in thumb_clicked]


@app.callback(
    Output({'type': 'full-screen-modal', 'index': ALL}, 'children'),
    Output({'type': 'full-screen-modal', 'index': ALL}, 'is_open'),
    Output({'type': 'double-click-entry', 'index': ALL}, 'n_events'),

    Input({'type': 'double-click-entry', 'index': ALL}, 'n_events'),

    State({'type': 'thumbnail-name', 'index': ALL}, 'children'),
    State({'base_id': 'file-manager', 'name': 'docker-file-paths'},'data'),
    prevent_initial_call=True
)
def full_screen_thumbnail(double_click, thumbnail_name_children, file_paths):
    '''
    This callback opens the modal pop-up window with the full size image that was double-clicked
    Args:
        double_click:               List of number of times that every card has been double-clicked
        thumbnail_name_children:    List of the thumbnails filenames
        tiled_on:                   [Bool] indicates if tiled reading is ON/OFF
    Returns:
        contents:                   Contents for pop-up window
        open_modal:                 Open/close modal
        double_click:               Resets the number of double-clicks to zero
    '''
    if 1 not in double_click:
        raise PreventUpdate
    filename = thumbnail_name_children[double_click.index(1)]
    data_project = DataProject()
    data_project.init_from_dict(file_paths)
    data = data_project.data
    data_set = next(item for item in data if item.uri == filename)
    img_contents, _ = data_set.read_data()
    contents = parse_full_screen_content(img_contents, filename)
    return [contents], [True], [0]*len(double_click)


@app.callback(
    Output('color-picker-modal', 'is_open'),

    Input({'type': 'color-label-button', 'index': ALL}, 'n_clicks'),
    Input('submit-color-button', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_color_picker_modal(color_label_n_clicks, submit_n_clicks):
    '''
    This callback toggles the color picker modal for label color definition
    Args:
        color_label_n_clicks:       Number of clicks on all the label color buttons
    Returns:
        Opens or closes the color picker modal
    '''
    if any(color_label_n_clicks):
        return True
    elif submit_n_clicks:
        return False
    else:
        return dash.no_update


@app.callback(
    Output('color-cycle', 'data'),

    Input('submit-color-button', 'n_clicks'),

    State({'type': 'color-label-button', 'index': ALL}, 'n_clicks_timestamp'),
    State('label-color-picker', 'value'),
    State('color-cycle', 'data'),
    prevent_initial_call=True
)
def change_label_color(submit_n_clicks, color_label_t_clicks, new_color, color_cycle):
    '''
    This callback updates color labels according to user's selection
    Args:
        submit_n_clicks:            Button "submit label color" was clicked
        color_label_t_clicks:       Timestamps of clicks on all the label color buttons
        new_color:                  User defined label color from palette
        color_cycle:                Current color cycle definition
    Returns:
        New color cycle definition
    '''
    mod_indx = color_label_t_clicks.index(max(color_label_t_clicks))
    color_cycle[mod_indx] = new_color['hex']
    return color_cycle


@app.callback(
    Output('mlcoach-model-list', 'options'),
    Output('data-clinic-model-list', 'options'),

    Input("tab-group", "value"),
    Input('mlcoach-refresh', 'n_clicks'),
    Input('data-clinic-refresh', 'n_clicks'),
    prevent_initial_call=True
)
def update_trained_model_list(tab_value, mlcoach_refresh_n_clicks, data_clinic_refresh_n_clicks):
    '''
    This callback updates the list of trained models
    Args:
        tab_value:                      Tab option
        mlcoach_refresh_n_clicks:       Button to refresh the list of mlcoach trained models
        data_clinic_refresh_n_clicks:   Button to refresh the list of data clinic trained models
    Returns:
        mlcoach_model_list:             List of trained models in mlcoach
        data_clinic_model_list:         List of trained models in data clinic
    '''
    if tab_value == 'mlcoach':
        mlcoach_models = get_trained_models_list(USER, tab_value)
        data_clinic_models = dash.no_update
    elif tab_value == 'clinic':
        mlcoach_models = dash.no_update
        data_clinic_models = get_trained_models_list(USER, tab_value)
    else:
        return dash.no_update, dash.no_update
    return mlcoach_models, data_clinic_models


@app.callback(
    Output('label-buttons', 'children'),
    Output('mlcoach-label-name', 'options'),
    Output('labels-dict', 'data'),
    Output({'type': 'label-percentage', 'index': ALL}, 'value'),
    Output({'type': 'label-percentage', 'index': ALL}, 'label'),
    Output('total_labeled', 'children'),

    Input({'type': 'label-button', 'index': ALL}, 'n_clicks_timestamp'),
    Input('un-label', 'n_clicks'),
    Input('confirm-un-label-all', 'n_clicks'),
    Input('mlcoach-label', 'n_clicks'),
    Input('mlcoach-model-list', 'value'),
    Input('button-load-splash', 'n_clicks'),
    Input('modify-list', 'n_clicks'),
    Input({'type': 'delete-label-button', 'index': ALL}, 'n_clicks_timestamp'),
    Input('color-cycle', 'data'),
    Input({'base_id': 'file-manager', 'name': 'docker-file-paths'}, 'data'),

    State('add-label-name', 'value'),
    State({'type': 'thumbnail-image', 'index': ALL}, 'n_clicks'),
    State({'type': 'thumbnail-name', 'index': ALL}, 'children'),
    State('labels-dict', 'data'),
    State('probability-threshold', 'value'),
    State('mlcoach-label-name', 'value'),
    State({'type': 'label-button', 'index': ALL}, 'children'),
    prevent_initial_call=True
)
def label_selected_thumbnails(label_button_n_clicks, unlabel_button, unlabel_all_button, \
                              mlcoach_label_button, mlcoach_model, load_splash_n_clicks, \
                              modify_list_n_clicks, del_label_n_clicks, color_cycle, docker_file_paths, add_label_name, \
                              thumbnail_image_select_value, thumbnail_name_children, labels_dict, \
                              threshold, mlcoach_label, label_button_children):
    '''
    This callback updates the dictionary of labeled images when:
        - A new image is labeled
        - An existing image changes labels
        - An image is unlabeled
        - Information is loaded from splash-ml
    This callback also updates the label list on the right column according to:
        - New trained supervised models have been selected
        - New labels have been added
        - Labels have been deleted
        - A new color cycle has been selected
    Args:
        label_button_n_clicks:          List of timestamps of the clicked label-buttons
        unlabel_button:                 Un-label button
        unlabel_all_button:             Unlabel all button
        mlcoach_label_button:           Triggers labeling with mlcoach results
        mlcoach_model:                  Selected MLCoach model
        load_splash_n_clicks:           Triggers loading labeled datasets with splash-ml
        modify_list_n_clicks:           Button to add a new label (tag name)
        mlcoach_refresh_n_clicks:       Button to refresh the list of mlcoach trained models
        data_clinic_refresh_n_clicks:   Button to refresh the list of data clinic trained models
        del_label_n_clicks:             List of n_clicks to delete a label button  
        color_cycle:                    Color cycle per label
        docker_file_paths:              Dictionary [{'file_path': 'path/to/dataset', 'file_type': dir/tiled}]
        add_label_name:                 Label to add (tag name)
        thumbnail_image_select_value:   Selected thumbnail image (n_clicks)
        thumbnail_name_children:        Filename of the selected thumbnail image
        labels_dict:                    Dictionary of labeled images, e.g., 
                                        {filename1: [label1, label2], ...}
        threshold:                      Threshold value                                                  
        mlcoach_label:                  Selected label from trained model in mlcoach
        label_button_children:          List of label text in label buttons
    Returns:
        label_buttons:                  Reactive component with the updated list of labels
        mlcoach_label:                  Selected label from trained model in mlcoach
        labels_dict:                    Dictionary with labeling information, e.g. 
                                        {filename1: [label1, label2], ...}
        label_perc_value:               Numerical values that indicate the percentage of images 
                                        labeled per class/label
        label_perc_label:               Same as above, but string
        total_labeled:                  Message to indicate how many images have been labeled
    '''
    changed_id = dash.callback_context.triggered[-1]['prop_id']
    labels = Labels(**labels_dict)
    if 'docker-file-paths' in changed_id:
        data_project = DataProject()
        data_project.init_from_dict(docker_file_paths)
        filenames = [data_set.uri for data_set in data_project.data]
        labels.init_labels(filenames, label_button_children)
    mlcoach_options = dash.no_update
    if changed_id in ['delete-label-button', 'modify-list', 'color-cycle']:
        label_perc_value = [dash.no_update]*len(labels.labels_list)
        label_perc_label = [dash.no_update]*len(labels.labels_list)
        total_labeled = dash.no_update
        if changed_id == 'delete-label-button.n_clicks':        # A label has been deleted
            label_to_delete = labels.labels_list[np.argmax(del_label_n_clicks)]
            labels.update_labels_list(remove_label=label_to_delete)
        elif changed_id == 'modify-list.n_clicks':              # New label has been added
            labels.update_labels_list(add_label=add_label_name)
        elif changed_id == 'mlcoach-model-list.value':          # Update labels according to mlcoach
            mlcoach_options = {}                                # model selection
            if mlcoach_model:
                df_prob = pd.read_parquet(mlcoach_model)
                mlcoach_labels = list(df_prob.columns[0:])
                additional_labels = list(set(mlcoach_labels) - set(labels.labels_list))
                for additional_label in additional_labels:
                    labels.update_labels_list(add_label=additional_label)
                mlcoach_options = [{'label':name, 'value':name} for name in mlcoach_labels]
        progress_values, progress_labels, total_num_labeled = labels.get_labeling_progress()
        label_comp = create_label_component(labels.labels_list, \
                                            color_cycle, \
                                            progress_values=progress_values, \
                                            progress_labels=progress_labels, \
                                            total_num_labeled=total_num_labeled)
    else:
        label_comp = dash.no_update
        if changed_id == 'confirm-un-label-all.n_clicks':       # Unlabel all is selected 
            labels.init_labels()
        elif changed_id == 'mlcoach-label.n_clicks':            # Labeling with mlcoach
            if mlcoach_model:
                labels.mlcoach_labeling(mlcoach_model, mlcoach_label, threshold)
        elif changed_id == 'button-load-splash.n_clicks':       # Labeling from splash-ml
            labels.load_splash_labels()
        else:                                                   # Labeling manually
            if changed_id == 'un-label.n_clicks':               # Unlabel an image
                labels.manual_labeling(None, thumbnail_image_select_value, thumbnail_name_children)
            else:                                               # Label an image
                if bool(label_button_n_clicks):                 # Figures out the latest-clicked 
                    indx = np.argmax(label_button_n_clicks)     # label button index
                    label_class_value = label_button_children[indx]
                labels.manual_labeling(label_class_value, thumbnail_image_select_value, \
                                       thumbnail_name_children) 
        label_perc_value, label_perc_label, total_labeled = labels.get_labeling_progress()   
    return label_comp, mlcoach_options, vars(labels), label_perc_value, label_perc_label, \
           total_labeled


@app.callback(
    Output('storage-modal', 'is_open'),
    Output('storage-body-modal', 'children'),

    Input('button-save-disk', 'n_clicks'),
    Input('button-save-splash', 'n_clicks'),
    Input('close-storage-modal', 'n_clicks'),

    State({'base_id': 'file-manager', 'name': 'docker-file-paths'},'data'),
    State('labels-dict', 'data'),
    State('import-dir', 'n_clicks'),
    prevent_initial_call=True
)
def save_labels(button_save_disk_n_clicks, button_save_splash_n_clicks, close_modal_n_clicks, \
                file_paths, labels_dict, import_n_clicks):
    '''
    This callback saves the labels to disk or to splash-ml
    Args:
        button_save_disk_n_clicks:      Button to save to disk
        button_save_splash_n_clicks:    Button to save to splash-ml
        close_modal_n_clicks:           Button to close the confirmation message
        file_paths:                     Absolute file paths selected from path table
        labels_dict:                    Dictionary of labeled images (docker path), as follows: 
                                        {filename1: [label1, label2], ...}
        import_n_clicks:                Button for importing selected paths
    Returns:
        storage_modal_open:             Open/closes the confirmation message
        storag_body_modal:              Confirmation message
    '''
    changed_id = dash.callback_context.triggered[-1]['prop_id']
    if changed_id == 'close-storage-modal.n_clicks':
        return False, ''
    if labels_dict is not None and import_n_clicks:
        labels = Labels(**labels_dict)
        if 'button-save-splash.n_clicks' in changed_id:
            status = labels.save_to_splash()
            if len(status)==0:
                response = 'Labels stored in splash-ml'
            else:
                response = f'Error. {status}'
            file_path = file_paths[0]['file_path']
            payload = {'file_path': [file_path], 'file_type': 'uri', 'where': 'splash'}
        else:
            docker_save_dir = pathlib.Path(DOCKER_DATA / 'labelmaker_outputs' /str(uuid.uuid4()))
            response = labels.save_to_directory(docker_save_dir)
            payload = {'file_path': [str(docker_save_dir)], 'file_type': 'dir', 'where': 'local'}
            # local_save_dir = docker_to_local_path(str(docker_save_dir), \
            #                                       DOCKER_HOME, \
            #                                       LOCAL_HOME, \
            #                                       'str')
            local_save_dir = ''
            response = f'Labeled files are stored to disk at: {local_save_dir}'
        params = {'datapath': payload, 'operation_type': 'export_dataset'}
        status_code = requests.post("http://labelmaker-api:8005/api/v0/datapath", 
                                    json=params).status_code
        return True, response


if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8057)
