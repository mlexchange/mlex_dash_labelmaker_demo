import math, time
import dash
from dash import Input, Output, State, callback, ALL, MATCH
import pandas as pd

from labels import Labels
from file_manager.data_project import DataProject
from helper_utils import draw_rows, parse_full_screen_content
from app_layout import NUMBER_OF_ROWS


@callback([
    Output('output-image-upload', 'children'),
    Output('prev-page', 'disabled'),
    Output('next-page', 'disabled'),
    Output('current-page', 'data'),

    Input('image-order', 'data'),
    Input('thumbnail-slider', 'value'),
    Input('prev-page', 'n_clicks'),
    Input('next-page', 'n_clicks'),
    Input('mlcoach-collapse', 'is_open'),
    Input('mlcoach-model-list', 'value'),
    Input('labels-dict', 'data'),

    State({'base_id': 'file-manager', 'name': 'docker-file-paths'},'data'),
    State('find-similar-unsupervised', 'n_clicks'),
    State('current-page', 'data'),
    State('tab-group', 'value'),
    State('previous-tab', 'data')],
    prevent_initial_call=True)
def update_output(image_order, thumbnail_slider_value, button_prev_page, button_next_page, 
                  ml_coach_is_open, mlcoach_model, labels_dict, file_paths, \
                  find_similar_images, current_page, tab_selection, previous_tab):
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


@callback(
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
        raise dash.exceptions.PreventUpdate
    filename = thumbnail_name_children[double_click.index(1)]
    data_project = DataProject()
    data_project.init_from_dict(file_paths)
    data = data_project.data
    data_set = next(item for item in data if item.uri == filename)
    img_contents, _ = data_set.read_data()
    contents = parse_full_screen_content(img_contents, filename)
    return [contents], [True], [0]*len(double_click)


@callback(
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


@callback(
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


@callback(
    Output("button-hide", "children"),
    Input("button-hide", "n_clicks"),
    State("button-hide", "children"),
    prevent_initial_call=True
)
def update_hide_button_text(n1, current_text):
    if current_text == 'Hide' and n1 != 0:
        return 'Unhide'
    return 'Hide'


@callback(
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
    

@callback(
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