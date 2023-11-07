from datetime import datetime, timezone

import dash
from dash import Input, Output, State, callback, ALL, dcc
from dash.exceptions import PreventUpdate
import numpy as np
import pandas as pd
import requests

from labels import Labels
from file_manager.data_project import DataProject
from utils.plot_utils import create_label_component
from app_layout import DOCKER_DATA, SPLASH_URL


@callback(
    Output('color-picker-modal', 'is_open'),

    Input({'type': 'color-label-button', 'index': ALL}, 'n_clicks'),
    Input('submit-color-button', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_color_picker_modal(color_label_n_clicks, submit_n_clicks):
    '''
    This callback toggles the color picker modal for label color definition
    Args:
        color_label_n_clicks:       Number of clicks in all the label color buttons
        submit_n_clicks:            Number of clicks in submit color button
    Returns:
        Opens or closes the color picker modal
    '''
    if any(color_label_n_clicks):
        return True
    elif submit_n_clicks:
        return False
    else:
        return dash.no_update


@callback(
    Output('label-buttons', 'children'),
    Output('mlcoach-label-name', 'options'),
    Output('labels-dict', 'data'),
    Output({'type': 'label-percentage', 'index': ALL}, 'value'),
    Output({'type': 'label-percentage', 'index': ALL}, 'label'),
    Output('total_labeled', 'children'),
    Output('color-cycle', 'data'),

    Input({'type': 'label-button', 'index': ALL}, 'n_clicks_timestamp'),
    Input('keybind-event-listener', 'event'),
    Input('un-label', 'n_clicks'),
    Input('mlcoach-label', 'n_clicks'),
    Input('mlcoach-model-list', 'value'),
    Input('confirm-load-splash', 'n_clicks'),
    Input('modify-list', 'n_clicks'),
    Input({'type': 'delete-label-button', 'index': ALL}, 'n_clicks_timestamp'),
    Input({'base_id': 'file-manager', 'name': 'docker-file-paths'}, 'data'),
    Input('submit-color-button', 'n_clicks'),

    State('add-label-name', 'value'),
    State({'type': 'thumbnail-image', 'index': ALL}, 'n_clicks'),
    State({'type': 'thumbnail-name', 'index': ALL}, 'children'),
    State('labels-dict', 'data'),
    State('probability-threshold', 'value'),
    State('mlcoach-label-name', 'value'),
    State({'type': 'label-button', 'index': ALL}, 'children'),
    State({'base_id': 'file-manager', 'name': 'project-id'}, 'data'),
    State('event-id', 'value'),
    State({'type': 'color-label-button', 'index': ALL}, 'n_clicks_timestamp'),
    State('label-color-picker', 'value'),
    State('color-cycle', 'data'),
    prevent_initial_call=True
)
def label_selected_thumbnails(label_button_n_clicks, keybind_label, unlabel_button,
                              mlcoach_label_button, mlcoach_model, load_splash_n_clicks,
                              modify_list_n_clicks, del_label_n_clicks, file_paths,
                              submit_color_n_clicks, add_label_name, thumbnail_image_select_value,
                              thumbnail_name_children, labels_dict, threshold, mlcoach_label,
                              label_button_children, project_id, event_id, color_label_t_clicks,
                              new_color, color_cycle):
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
        keybind_label:                  Keyword entry
        unlabel_button:                 Un-label button
        mlcoach_label_button:           Triggers labeling with mlcoach results
        mlcoach_model:                  Selected mlcoach model
        load_splash_n_clicks:           Triggers loading labeled datasets with splash-ml
        modify_list_n_clicks:           Button to add a new label (tag name)
        del_label_n_clicks:             List of n_clicks to delete a label button  
        file_paths:                     Data project information
        submit_color_n_clicks:          Button "submit label color" was clicked
        add_label_name:                 Label to add (tag name)
        thumbnail_image_select_value:   Selected thumbnail image (n_clicks)
        thumbnail_name_children:        Filename of the selected thumbnail image
        labels_dict:                    Dictionary of labeled images, e.g., 
                                        {filename1: [label1, label2], ...}
        threshold:                      Threshold value for labeling with mlcoach
        mlcoach_label:                  Selected label to be assigned with mlcoach model
        label_button_children:          List of label text in label buttons
        project_id:                     Data project id
        event_id:                       Tagging event id for version control of tags
        color_label_t_clicks:           Timestamps of label color buttons
        new_color:                      User defined label color from palette
        color_cycle:                    Color cycle per label
    Returns:
        label_buttons:                  Dash components with the updated list of labels
        mlcoach_label_options:          Label options from trained model in mlcoach
        labels_dict:                    Dictionary with labeling information, e.g. 
                                        {filename1: [label1, label2], ...}
        label_perc_value:               Numerical values that indicate the percentage of images 
                                        labeled per class/label
        label_perc_label:               Same as above, but string
        total_labeled:                  Message to indicate how many images have been labeled
        color_cycle:                    Color cycle per label
    '''
    changed_id = dash.callback_context.triggered[-1]['prop_id']
    labels = Labels(**labels_dict)
    mlcoach_options = dash.no_update
    label_comp = dash.no_update
    # Labeling with keyword shortcuts
    if changed_id == 'keybind-event-listener.event':
        if keybind_label['key'].isdigit() and int(keybind_label['key'])-1 in range(len(label_button_children)):
            label_class_value = label_button_children[int(keybind_label['key'])-1]
            labels.manual_labeling(label_class_value, 
                                   thumbnail_image_select_value,
                                   thumbnail_name_children)
        else:
            raise PreventUpdate
    # A new data set has been selected
    elif 'docker-file-paths' in changed_id:
        data_project = DataProject()
        data_project.init_from_dict(file_paths)
        filenames = [data_set.uri for data_set in data_project.data]
        labels.init_labels(filenames, label_button_children)
    # The label dash components (buttons) need to be updated
    elif changed_id in ['modify-list.n_clicks', 'color-cycle.data', 'submit-color-button.n_clicks', 
                        'mlcoach-model-list.value', 'confirm-load-splash.n_clicks'] or \
         'delete-label-button' in changed_id:
        label_perc_value = [dash.no_update]*len(labels.labels_list)
        label_perc_label = [dash.no_update]*len(labels.labels_list)
        total_labeled = dash.no_update
        if changed_id == 'submit-color-button.n_clicks':
            mod_indx = color_label_t_clicks.index(max(color_label_t_clicks))
            color_cycle[mod_indx] = new_color['hex']
        # A label has been deleted
        elif 'delete-label-button' in changed_id:
            indx_label_to_delete = np.argmax(del_label_n_clicks)
            label_to_delete = labels.labels_list[indx_label_to_delete]
            labels.update_labels_list(remove_label=label_to_delete)
            color_cycle.pop(indx_label_to_delete)
        # New label has been added
        elif changed_id == 'modify-list.n_clicks':
            labels.update_labels_list(add_label=add_label_name)
        # Loading labels from splash-ml
        elif changed_id == 'confirm-load-splash.n_clicks':
            labels.load_splash_labels(project_id, event_id)
        # Update labels according to mlcoach model selection
        elif changed_id == 'mlcoach-model-list.value':
            mlcoach_options = {}
            if mlcoach_model:
                df_prob = pd.read_parquet(mlcoach_model)
                mlcoach_labels = list(df_prob.columns[0:])
                additional_labels = list(set(mlcoach_labels) - set(labels.labels_list))
                for additional_label in additional_labels:
                    labels.update_labels_list(add_label=additional_label)
                mlcoach_options = [{'label':name, 'value':name} for name in mlcoach_labels]
        progress_values, progress_labels, total_num_labeled = labels.get_labeling_progress()
        label_comp = create_label_component(labels.labels_list,
                                            color_cycle,
                                            progress_values=progress_values,
                                            progress_labels=progress_labels,
                                            total_num_labeled=total_num_labeled)
        return label_comp, mlcoach_options, vars(labels), label_perc_value, label_perc_label, \
            total_labeled, color_cycle
    # Labeling with mlcoach
    elif changed_id == 'mlcoach-label.n_clicks':
        if mlcoach_model:
            labels.mlcoach_labeling(mlcoach_model, mlcoach_label, threshold)
    # Labeling manually
    else:
        # Unlabel an image
        if changed_id == 'un-label.n_clicks':
            labels.manual_labeling(None,
                                   thumbnail_image_select_value,
                                   thumbnail_name_children)
        # Label an image
        else:
            indx = np.argmax(label_button_n_clicks)
            label_class_value = label_button_children[indx]
            labels.manual_labeling(label_class_value,
                                   thumbnail_image_select_value,
                                   thumbnail_name_children) 
    label_perc_value, label_perc_label, total_labeled = labels.get_labeling_progress()   
    return label_comp, mlcoach_options, vars(labels), label_perc_value, label_perc_label, \
           total_labeled, color_cycle


@callback(
    Output('event-id', 'options'),
    Output('modal-load-splash', 'is_open'),

    Input('button-load-splash', 'n_clicks'),
    Input('confirm-load-splash', 'n_clicks'),

    State({'base_id': 'file-manager', 'name': 'docker-file-paths'}, 'data'),
    State({'base_id': 'file-manager', 'name': 'project-id'}, 'data'),
    prevent_initial_call=True
)
def load_from_splash_modal(load_n_click, confirm_load, file_paths, project_id):
    '''
    Load labels from splash-ml associated with the project_id
    Args:
        load_n_click:       Number of clicks in load from splash-ml button
        confirm_load:       Number of clicks in confim button within loading from splash-ml modal
        file_paths:         Data project information
        project_id:         Project id associated with the current data project
    Returns:
        event_id:           Available tagging event IDs associated with the current data project
        modal_load_splash:  True/False to open/close loading from splash-ml modal
    '''
    changed_id = dash.callback_context.triggered[-1]['prop_id']
    if changed_id == 'confirm-load-splash.n_clicks':    # if confirmed, load chosen tagging event
        return dash.no_update, False
    # If unconfirmed, retrieve the tagging event IDs associated with the current data project
    data_project = DataProject()
    data_project.init_from_dict(file_paths)
    num_imgs = len(data_project.data)
    response = requests.post(f'{SPLASH_URL}/datasets/search', 
                             params={'page[limit]': num_imgs}, 
                             json={'project': project_id})
    event_ids = []
    for dataset in response.json():
        for tag in dataset['tags']:
            if tag['event_id'] not in event_ids:
                event_ids.append(tag['event_id'])
    # Present the tagging event options with their corresponding tagger id and runtime
    options = []
    for event_id in event_ids:
        tagging_event = requests.get(f'{SPLASH_URL}/events/{event_id}').json()
        tagging_event_time = datetime.strptime(tagging_event['run_time'], "%Y-%m-%dT%H:%M:%S.%f")
        tagging_event_time = tagging_event_time.replace(tzinfo=timezone.utc).astimezone(tz=None)\
            .strftime("%d-%m-%Y %H:%M:%S")
        options.append({'label': f"Tagger ID: {tagging_event['tagger_id']}, \
                                 modified: {tagging_event_time}",
                        'value' : event_id})
    return options, True