import math, time
import dash
from dash import Input, Output, State, callback, ALL, MATCH
from dash.exceptions import PreventUpdate
import pandas as pd

from labels import Labels
from file_manager.data_project import DataProject
from utils.plot_utils import draw_rows, parse_full_screen_content
from app_layout import NUMBER_OF_ROWS


@callback([
    Output('output-image-upload', 'children'),
    [Output('first-page', 'disabled'), Output('prev-page', 'disabled')],
    [Output('next-page', 'disabled'), Output('last-page', 'disabled')],
    Output('current-page', 'data'),

    Input('image-order', 'data'),
    Input('thumbnail-slider', 'value'),
    Input('first-page', 'n_clicks'),
    Input('prev-page', 'n_clicks'),
    Input('next-page', 'n_clicks'),
    Input('last-page', 'n_clicks'),
    Input('mlcoach-collapse', 'is_open'),
    Input('mlcoach-model-list', 'value'),
    
    State('labels-dict', 'data'),
    State({'base_id': 'file-manager', 'name': 'docker-file-paths'},'data'),
    State('find-similar-unsupervised', 'n_clicks'),
    State('current-page', 'data'),
    State('tab-group', 'value'),
    State('previous-tab', 'data')],
    prevent_initial_call=True)
def update_output(image_order, thumbnail_slider_value, button_first_page, button_prev_page, 
                  button_next_page, button_last_page, ml_coach_is_open, mlcoach_model, labels_dict, 
                  file_paths, find_similar_images, current_page, tab_selection, previous_tab):
    '''
    This callback displays images in the front-end and enables/disables the page navigation buttons
    Args:
        image_order:            Order of the images according to the selected action (sort, hide, 
                                new data, etc)
        thumbnail_slider_value: Number of images per row
        button_first_page:      Go to first page
        button_prev_page:       Go to previous page
        button_next_page:       Go to next page
        button_last_page:       Go to last page
        ml_coach_is_open:       MLCoach is the labeling method
        mlcoach_model:          Selected MLCoach model
        labels_dict:            Dictionary with labeling information, e.g. 
                                {filename1: [label1,label2], ...}
        file_paths:             Data project information
        find_similar_images:    Find similar images button, n_clicks
        current_page:           Index of the current page
        tab_selection:          Current tab [Manual, Data Clinic, MLCoach]
        previous_tab:           List of previous tab selection [Manual, Data Clinic, MLCoach]
    Returns:
        children:               Images to be displayed in front-end according to the current page 
                                index and # of columns
        [first_page, prev_page]:Enable/Disable previous page button if current_page==0
        [next_page, last_page]: Enable/Disable next page button if current_page==max_page
        current_page:           Update current page index
    '''
    start = time.time()
    changed_id = dash.callback_context.triggered[0]['prop_id']
    labels = Labels(**labels_dict)
    data_project = DataProject()
    data_project.init_from_dict(file_paths)
    num_imgs = len(image_order)
    # update current page if necessary
    if changed_id == 'image-order.data' or changed_id == 'first-page.n_clicks':
        current_page = 0
    elif changed_id == 'prev-page.n_clicks':
        current_page = current_page - 1
    elif changed_id == 'next-page.n_clicks':
        current_page = current_page + 1
    elif changed_id == 'last-page.n_clicks':
        current_page = math.ceil(num_imgs/(NUMBER_OF_ROWS*thumbnail_slider_value)) - 1
    elif changed_id == 'mlcoach-collapse.is_open':
        if tab_selection=='mlcoach':        # if the previous tab is mlcoach, the display should be 
            current_page = 0                # updated to remove the probability list per image
        elif previous_tab[-2] != 'mlcoach':
            raise PreventUpdate
    children = []
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
    elif find_similar_images:               # Find similar images has been activated
        pre_highlight = True
        for name in new_filenames:          # if there is one label in page, do not pre-highlight
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
    return children, 2*[current_page==0], \
           2*[math.ceil((num_imgs//thumbnail_slider_value)/NUMBER_OF_ROWS)<=current_page+1], \
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
        file_paths:                 Data project information
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
        color_cycle:                List that contains the color cycle associated with the labels
    Returns:
        thumbnail_color:            Color of thumbnail card
    '''
    changed_id = dash.callback_context.triggered[0]['prop_id']
    labels = Labels(**labels_dict)
    if len(labels.labels_dict)==0 or value is None or changed_id == 'un-label.n_clicks':
        color = dash.no_update
    elif value % 2 == 1:
        color = 'primary'
    else:
        label = labels.labels_dict[thumbnail_name_children]
        if len(label)>0:
            label_indx = labels.labels_list.index(label[0])
            color = color_cycle[label_indx]
        else:
            color = 'white'
    return color


@callback(
    Output({'type': 'thumbnail-image', 'index': ALL}, 'n_clicks'),

    Input({'type': 'label-button', 'index': ALL}, 'n_clicks_timestamp'),
    Input('un-label', 'n_clicks'),
    Input('confirm-un-label-all', 'n_clicks'),
    Input('keybind-event-listener', 'event'),

    State({'type': 'thumbnail-image', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def deselect(label_button_trigger, unlabel_n_clicks, unlabel_all, keybind_label, thumb_clicked):
    '''
    This callback deselects a thumbnail card
    Args:
        label_button_trigger:   Label button
        unlabel_n_clicks:       Un-label button
        unlabel_all:            Un-label all the images
        keybind_label:          Keyword entry
        thumb_clicked:          Selected thumbnail card indice, e.g., [0,1,1,0,0,0]
    Returns:
        Modify the number of clicks for a specific thumbnail card
    '''
    changed_id = dash.callback_context.triggered[0]['prop_id']
    keybind_is_valid = True
    if changed_id == 'keybind-event-listener.event':
        keybind_is_valid = keybind_label['key'].isdigit() and \
                           int(keybind_label['key']) in range(len(label_button_trigger))
        if not keybind_is_valid:
            raise PreventUpdate
    if all(x is None for x in label_button_trigger) and unlabel_n_clicks is None and \
        unlabel_all is None and not keybind_is_valid:
        return [dash.no_update]*len(thumb_clicked)
    return [0 for thumb in thumb_clicked]


@callback(
    Output('button-hide', 'children'),
    Input('button-hide', 'n_clicks'),
    State('button-hide', 'children'),
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
    Output('manual-collapse', 'is_open'),
    Output('mlcoach-collapse', 'is_open'),
    Output('data-clinic-collapse', 'is_open'),
    Output('label-buttons-collapse', 'is_open'),
    Output('goto-webpage-collapse', 'is_open'),
    Output('goto-webpage', 'children'),
    Output('previous-tab', 'data'),

    Input('tab-group', 'value'),

    State('previous-tab', 'data')
)
def toggle_tabs_collapse(tab_value, previous_tab):
    '''
    This callback toggles the tabs according to the selected labeling method
    '''
    keys = ['manual', 'mlcoach', 'data_clinic']
    tabs = {key: False for key in keys}
    tabs[tab_value] = True
    if tab_value == 'data_clinic':
        tabs['manual'] = True
    show_label_buttons = True
    goto_webpage = {'manual': False, 'mlcoach': True, 'data_clinic': True}
    button_name = 'Go to MLCoach'
    if tab_value == 'data_clinic':
        button_name = 'Go to DataClinic'
    if not previous_tab:
        previous_tab = ['init', tab_value]
    else:
        previous_tab.append(tab_value)
    return tabs['manual'], tabs['mlcoach'], tabs['data_clinic'], \
           show_label_buttons, goto_webpage[tab_value], button_name, previous_tab