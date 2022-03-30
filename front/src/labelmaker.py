import os, io
import shutil, pathlib, base64, math, copy, zipfile
import numpy as np

import dash
from dash.dependencies import Input, Output, State, MATCH, ALL

import itertools
import pandas as pd
import PIL
import plotly.express as px

from helper_utils import get_color_from_label, create_label_component, draw_rows
from app_layout import app, LABEL_LIST, DOCKER_DATA, UPLOAD_FOLDER_ROOT
from file_manager import filename_list, move_a_file, move_dir, add_paths_from_dir, \
                         check_duplicate_filename, docker_to_local_path, local_to_docker_path


# Font and background colors associated with each theme
text_color = {"dark": "#95969A", "light": "#595959"}
card_color = {"dark": "#2D3038", "light": "#FFFFFF"}

COLOR_CYCLE = px.colors.qualitative.Plotly
NUMBER_OF_ROWS = 4

LOCAL_DATA = str(os.environ['DATA_DIR'])
DOCKER_HOME = str(DOCKER_DATA) + '/'
LOCAL_HOME = str(LOCAL_DATA)
TOP_N = 6 # number of images per row in data clinic pop window

df_prob = pd.read_csv('data/results.csv')
df_clinic = pd.read_csv('data/dist_matrix.csv')

#================================== callback functions ===================================
@app.callback(
    Output("collapse", "is_open"),
    Input("collapse-button", "n_clicks"),
    State("collapse", "is_open")
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    Output("file-mover-collapse", "is_open"),
    Input("file-mover-button", "n_clicks"),
    State("file-mover-collapse", "is_open")
)
def file_mover_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    Output("manual-collapse", "is_open"),
    Output("mlcoach-collapse", "is_open"),
    Output("data-clinic-collapse", "is_open"),
    Input("tab-group", "value")
)
def toggle_tabs_collapse(tab_value):
    keys = ['manual', 'mlcoach', 'clinic']
    tabs = {key: False for key in keys}
    tabs[tab_value] = True
     
    return tabs['manual'], tabs['mlcoach'], tabs['clinic']

@app.callback(
    Output("modal", "is_open"),
    Input("delete-files", "n_clicks"),
    Input("confirm-delete", "n_clicks"),  
    State("modal", "is_open")
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app.callback(
    Output("modal-window", "is_open"),
    Input("find-similar-unsupervised", "n_clicks"),
    Input("clinic-add-label-button", "n_clicks"), 
    Input('docker-file-paths','data'), 
    State("modal-window", "is_open")
)
def data_clinic_window(n1, n2, docker_file_paths, is_open):
    if n1 or n2:
        return not is_open
    return is_open


@app.callback(
    Output('dummy-data', 'data'),
    [Input('dash-uploader', 'isCompleted')],
    [State('dash-uploader', 'fileNames'),
     State('dash-uploader', 'upload_id')],
)
def upload_zip(iscompleted, upload_filename, upload_id):
    if not iscompleted:
        return 0

    if upload_filename is not None:
        path_to_zip_file = pathlib.Path(UPLOAD_FOLDER_ROOT) / upload_filename[0]
        if upload_filename[0].split('.')[-1] == 'zip':
            zip_ref = zipfile.ZipFile(path_to_zip_file)  # create zipfile object
            path_to_folder = pathlib.Path(UPLOAD_FOLDER_ROOT) / upload_filename[0].split('.')[-2]
            if (upload_filename[0].split('.')[-2] + '/') in zip_ref.namelist():
                zip_ref.extractall(pathlib.Path(UPLOAD_FOLDER_ROOT))    # extract file to dir
            else:
                zip_ref.extractall(path_to_folder)
                
            zip_ref.close()  # close file
            os.remove(path_to_zip_file)

    return 0 


@app.callback(
    Output('files-table', 'data'),
    Output('docker-file-paths', 'data'),
    Input('browse-format', 'value'),
    Input('browse-dir', 'n_clicks'),
    Input('import-dir', 'n_clicks'),
    Input('confirm-delete','n_clicks'),
    Input('move-dir', 'n_clicks'),
    Input('files-table', 'selected_rows'),
    Input('docker-file-paths', 'data'),
    Input('my-toggle-switch', 'value'),
    State('dest-dir-name', 'value')
)
def file_manager(browse_format, browse_n_clicks, import_n_clicks, delete_n_clicks, 
                  move_dir_n_clicks, rows, selected_paths, docker_path, dest):
    changed_id = dash.callback_context.triggered[0]['prop_id']
    files = []
    if browse_n_clicks or import_n_clicks:
        files = filename_list(DOCKER_DATA, browse_format)
        
    selected_files = []
    if bool(rows):
        for row in rows:
            selected_files.append(files[row])
    
    if browse_n_clicks and changed_id == 'confirm-delete.n_clicks':
        for filepath in selected_files:
            if os.path.isdir(filepath['file_path']):
               shutil.rmtree(filepath['file_path'])
            else:
                os.remove(filepath['file_path'])
        selected_files = []
        files = filename_list(DOCKER_DATA, browse_format)
    
    if browse_n_clicks and changed_id == 'move-dir.n_clicks':
        if dest is None:
            dest = ''
        destination = DOCKER_DATA / dest
        destination.mkdir(parents=True, exist_ok=True)
        if bool(rows):
            sources = selected_paths
            for source in sources:
                if os.path.isdir(source['file_path']):
                    move_dir(source['file_path'], str(destination))
                    shutil.rmtree(source['file_path'])
                else:
                    move_a_file(source['file_path'], str(destination))
                
            selected_files = []
            files = filename_list(DOCKER_DATA, browse_format)

    if docker_path:
        return files, selected_files
    else:
        return docker_to_local_path(files, DOCKER_HOME, LOCAL_HOME), selected_files


@app.callback(
    Output('image-order','data'),
    Input('docker-file-paths','data'),
    Input('import-dir', 'n_clicks'),
    Input('import-format', 'value'),
    Input('files-table', 'selected_rows'),
    Input('button-hide', 'n_clicks'),
    Input('button-sort', 'n_clicks'),
    Input('confirm-delete','n_clicks'),
    Input('move-dir', 'n_clicks'),
    State('docker-labels-name', 'data'),
    State('label-dict', 'data'),
    State('image-order','data'),
    prevent_initial_call=True)
def display_index(file_paths, import_n_clicks, import_format, rows, button_hide_n_clicks,
                  button_sort_n_clicks, delete_n_clicks, move_dir_n_clicks, 
                  labels_name_data, label_dict, image_order):
    '''
    This callback arranges the image order according to the following actions:
        - New content is uploaded
        - Buttons sort or hidden are selected
    Args:
        file_paths :            Absolute (docker) file paths selected from path table
        import_n_clicks:        Button for importing selected paths
        import_format:          File format for import
        rows:                   Rows of the selected file paths from path table
        button_hide_n_clicks:   Hide button
        button_sort_n_clicks:   Sort button
        delete_n_clicks:        Button for deleting selected file paths
        move_dir_n_clicks       Button for moving dir
        labels_name_data:       Dictionary of labeled images (docker path), as follows: {label: list of image filenames}
        label_dict:             Dict of label names (tag name), e.g., {0: 'label',...}
        image_order:            Order of the images according to the selected action (sort, hide, new data, etc)

    Returns:
        image_order:            Order of the images according to the selected action (sort, hide, new data, etc)
        data_access_open:       Closes the reactive component to select the data access (upload vs. directory)
    '''
    supported_formats = []
    import_format = import_format.split(',')
    if import_format[0] == '*':
        supported_formats = ['tiff', 'tif', 'jpg', 'jpeg', 'png']
    else:
        for ext in import_format:
            supported_formats.append(ext.split('.')[1])

    changed_id = dash.callback_context.triggered[0]['prop_id']
    if import_n_clicks and bool(rows):
        list_filename = []
        for file_path in file_paths:
            if file_path['file_type'] == 'dir':
                list_filename = add_paths_from_dir(file_path['file_path'], supported_formats, list_filename)
            else:
                list_filename.append(file_path['file_path'])
    
        num_imgs = len(list_filename)
        if  changed_id == 'import-dir.n_clicks' or \
            changed_id == 'confirm-delete.n_clicks' or \
            changed_id == 'files-table.selected_rows' or \
            changed_id == 'move_dir_n_clicks':
            image_order = list(range(num_imgs))

        if changed_id == 'button-hide.n_clicks':
            if button_hide_n_clicks % 2 == 1:
                labeled_names = list(itertools.chain(*labels_name_data.values()))
                unlabeled_indx = []
                for i in range(num_imgs):
                    if list_filename[i] not in labeled_names:
                        unlabeled_indx.append(i)
                image_order = unlabeled_indx
            else:
                image_order = list(range(num_imgs))

        if changed_id == 'button-sort.n_clicks':
            new_indx = [[] for i in range(len(label_dict.keys()) + 1)]
            for i in range(num_imgs):
                unlabeled = True
                for key_label in labels_name_data:
                    if list_filename[i] in labels_name_data[key_label]:
                        new_indx[int(key_label)].append(i)
                        unlabeled = False
                if unlabeled:
                    new_indx[-1].append(i)

            image_order = list(itertools.chain(*new_indx))
    else:
        image_order = []

    return image_order


@app.callback(
    Output('output-image-find', 'children'),
    Output('clinic-file-list', 'data'),
    Input('find-similar-unsupervised', 'n_clicks'),
    Input('my-toggle-switch', 'value'),
    State({'type': 'thumbnail-image', 'index': ALL}, 'n_clicks'),
    State({'type': 'thumbnail-name', 'index': ALL}, 'children'),
    State({'type': 'clinic-label-input', 'index': ALL}, 'value'),
    prevent_initial_call=True
)
def update_pop_window(find_similar_images, docker_path, thumb_clicked, thumbnail_name_children, input_value):
    print(f'input_value {input_value}')
    clicked_indice = [i for i, e in enumerate(thumb_clicked) if e != 0]
    filenames = []
    clinic_file_list = []
    display_filenames = []
    contents = []
    children = []
    if bool(clicked_indice):
        for index in clicked_indice:
            index = int(index)
            if docker_path:
                filenames.append(thumbnail_name_children[index])
            else:
                filenames.append(local_to_docker_path(thumbnail_name_children[index], DOCKER_HOME, LOCAL_HOME, type='str'))

        CLINIC_PATH = '/'.join(local_to_docker_path(thumbnail_name_children[0], DOCKER_HOME, LOCAL_HOME, type='str').split('/')[:-2])
        for name in filenames:
            filename = '/'.join(name.split(os.sep)[-2:])
            row_dataframe = df_clinic.iloc[df_clinic.set_index('filename').index.get_loc(filename)]
            row_filenames = df_clinic.iloc[np.argsort(row_dataframe.values[1:])[:TOP_N]]['filename'].tolist()
            for row_filename in row_filenames:
                row_filename = CLINIC_PATH + '/' + row_filename
                clinic_file_list.append(row_filename)
                with open(row_filename, "rb") as file:
                    img = base64.b64encode(file.read())
                    file_ext = row_filename.split('.')[-1]
                    contents.append('data:image/'+file_ext+';base64,'+img.decode("utf-8"))
                    
                if docker_path:
                    display_filenames.append(row_filename)
                else:
                    display_filenames.append(docker_to_local_path(row_filename, DOCKER_HOME, LOCAL_HOME, type='str'))
    
        children = draw_rows(contents, display_filenames, len(filenames), TOP_N, data_clinic=True)
    
    return children, clinic_file_list


@app.callback(
    Output('clinic-filenames', 'data'),
    Input('clinic-add-label-button', 'n_clicks'),
    Input('label-dict', 'data'),
    State('clinic-file-list', 'data'),
    State({'type': 'clinic-label-input', 'index': ALL}, 'value'),
    prevent_initial_call=True
)
def update_data_clinic_filenames(clinic_label, label_dict, clinic_file_list, input_values):
    clinic_filenames = {}
    label_dict_r = {value: int(key) for key, value in label_dict.items()}
    j = -1
    for i,filename in enumerate(clinic_file_list):
        if i % TOP_N == 0:
            j += 1
            if input_values[j] in label_dict_r:
                if label_dict_r[input_values[j]] not in clinic_filenames:
                    clinic_filenames[label_dict_r[input_values[j]]] = []
        clinic_filenames[label_dict_r[input_values[j]]].append(filename)
    
    return clinic_filenames


@app.callback([
    Output('output-image-upload', 'children'),
    Output('prev-page', 'disabled'),
    Output('next-page', 'disabled'),
    Output('current-page', 'data'),

    Input('image-order', 'data'),
    Input('thumbnail-slider', 'value'),
    Input('prev-page', 'n_clicks'),
    Input('next-page', 'n_clicks'),
    Input('files-table', 'selected_rows'),
    Input('import-format', 'value'),
    Input('docker-file-paths','data'),
    Input('my-toggle-switch', 'value'),
    Input('mlcoach-collapse', 'is_open'),
    Input('find-similar-unsupervised', 'n_clicks'),

    State('current-page', 'data'),
    State('import-dir', 'n_clicks')],
    prevent_initial_call=True)
def update_output(image_order, thumbnail_slider_value, button_prev_page, button_next_page, rows, import_format,
                  file_paths, docker_path, ml_coach_is_open, find_similar_images, current_page, import_n_clicks):
    '''
    This callback displays images in the front-end
    Args:
        image_order:            Order of the images according to the selected action (sort, hide, new data, etc)
        thumbnail_slider_value: Number of images per row
        button_prev_page:       Go to previous page
        button_next_page:       Go to next page
        rows:                   Rows of the selected file paths from path table
        import_format:          File format for import
        file_paths:             Absolute file paths selected from path table
        docker_path:            Showing file path in Docker environment
        ml_coach_is_open:       MLCoach is the labeling method
        find_similar_images:    Find similar images button, n_clicks
        current_page:           Index of the current page
        import_n_clicks:        Button for importing the selected paths
    Returns:
        children:               Images to be displayed in front-end according to the current page index and # of columns
        prev_page:              Enable/Disable previous page button if current_page==0
        next_page:              Enable/Disable next page button if current_page==max_page
        current_page:           Update current page index if previous or next page buttons were selected
    '''
    supported_formats = []
    import_format = import_format.split(',')
    if import_format[0] == '*':
        supported_formats = ['tiff', 'tif', 'jpg', 'jpeg', 'png']
    else:
        for ext in import_format:
            supported_formats.append(ext.split('.')[1])
    
    changed_id = dash.callback_context.triggered[0]['prop_id']
    # update current page if necessary
    if changed_id == 'image-order.data':
        current_page = 0
    if changed_id == 'prev-page.n_clicks':
        current_page = current_page - 1
    if changed_id == 'next-page.n_clicks':
        current_page = current_page + 1

    children = []
    num_imgs = 0
    if import_n_clicks and bool(rows):
        list_filename = []
        for file_path in file_paths:
            if file_path['file_type'] == 'dir':
                list_filename = add_paths_from_dir(file_path['file_path'], supported_formats, list_filename)
            else:
                list_filename.append(file_path['file_path'])
    
        # plot images according to current page index and number of columns
        num_imgs = len(image_order)
        if num_imgs>0:
            start_indx = NUMBER_OF_ROWS * thumbnail_slider_value * current_page
            max_indx = min(start_indx + NUMBER_OF_ROWS * thumbnail_slider_value, num_imgs)
            new_contents = []
            new_filenames = []
            for i in range(start_indx, max_indx):
                filename = list_filename[image_order[i]]
                with open(filename, "rb") as file:
                    img = base64.b64encode(file.read())
                    file_ext = filename[filename.find('.')+1:]
                    new_contents.append('data:image/'+file_ext+';base64,'+img.decode("utf-8"))
                if docker_path:
                    new_filenames.append(list_filename[image_order[i]])
                else:
                    new_filenames.append(docker_to_local_path(list_filename[image_order[i]], DOCKER_HOME,
                                                              LOCAL_HOME, 'str'))
                
            children = draw_rows(new_contents, new_filenames, thumbnail_slider_value, NUMBER_OF_ROWS,
                                                 ml_coach_is_open, df_prob)

    return children, current_page==0, math.ceil((num_imgs//thumbnail_slider_value)/NUMBER_OF_ROWS)<=current_page+1, \
           current_page


@app.callback(
    Output({'type': 'thumbnail-card', 'index': MATCH}, 'color'),
    Input({'type': 'thumbnail-image', 'index': MATCH}, 'n_clicks'),
    Input('docker-labels-name', 'data'),
    Input('my-toggle-switch', 'value'),
    State({'type': 'thumbnail-name', 'index': MATCH}, 'children'),
    prevent_initial_call=True
)
def select_thumbnail(value, labels_name_data, docker_path, thumbnail_name_children):
    '''
    This callback assigns a color to thumbnail cards in the following scenarios:
        - An image has been selected, but no label has been assigned (blue)
        - An image has been labeled (label color)
        - An image has been unselected or unlabeled (no color)
    Args:
        value:                      Thumbnail card that triggered the callback (n_clicks)
        unlabel_n_clicks:           Un-label button (n_clicks)
        thumbnail_name_children:    Filename in selected thumbnail
        labels_name_data:           Dictionary of labeled images, as follows: {0: [image filenames]}
    Returns:
        thumbnail_color:            Color of thumbnail card
    '''
    name = thumbnail_name_children
    if not docker_path:
        name =  local_to_docker_path(name, DOCKER_HOME, LOCAL_HOME, 'str')

    color = ''
    for label_key in labels_name_data:
        if name in labels_name_data[label_key]:
            color = get_color_from_label(label_key, COLOR_CYCLE)
            break
    if value is None or (dash.callback_context.triggered[0]['prop_id'] == 'un-label.n_clicks' and color==''):
        return ''
    if value % 2 == 1:
        return 'primary'
    else:
        return color


@app.callback(
    Output({'type': 'thumbnail-image', 'index': ALL}, 'n_clicks'),
    Input({'type': 'label-button', 'index': ALL}, 'n_clicks_timestamp'),
    Input('un-label', 'n_clicks'),
    Input('un-label-all', 'n_clicks'),
    State({'type': 'thumbnail-image', 'index': ALL}, 'n_clicks'),
)
def deselect(label_button_trigger, unlabel_n_clicks, unlabel_all, thumb_clicked):
    '''
    This callback deselects a thumbnail card
    Args:
        label_button_trigger:   Label button
        unlabel_n_clicks:       Un-label button
        thumb_clicked:          Selected thumbnail card indice, e.g., [0,1,1,0,0,0]
    Returns:
        Modify the number of clicks for a specific thumbnail card
    '''
    print(f'thumbnail trigger {label_button_trigger}')
    return [0 for thumb in thumb_clicked]


@app.callback(
    Output('docker-labels-name', 'data'),
    Output('chosen-label', 'children'),
    Input('del-label', 'data'),
    Input({'type': 'label-button', 'index': ALL}, 'n_clicks_timestamp'),
    Input('un-label', 'n_clicks'),
    Input('un-label-all', 'n_clicks'),
    Input('mlcoach-label', 'n_clicks'),
    Input('clinic-label', 'n_clicks'),
    State({'type': 'thumbnail-image', 'index': ALL}, 'id'),
    State({'type': 'thumbnail-image', 'index': ALL}, 'n_clicks'),
    State({'type': 'thumbnail-name', 'index': ALL}, 'children'),
    State('docker-labels-name', 'data'),
    State('probability-threshold', 'value'),
    State('label-dict', 'data'),
    State({'type': 'clinic-label-input', 'index': ALL}, 'value'),
    State('clinic-filenames', 'data'),
    prevent_initial_call=True
)
def label_selected_thumbnails(del_label, label_button_n_clicks, unlabel_button, unlabel_all_button,
                              mlcoach_label_button, clinic_label_button, thumbnail_image_index, 
                              thumbnail_image_select_value, thumbnail_name_children, 
                              current_labels_name, threshold, label_dict, input_labels, clinic_filenames):
    '''
    This callback updates the dictionary of labeled images when:
        - A new image is labeled
        - An existing image changes labels
        - An image is unlabeled
    Args:
        del_label:                      Delete label button
        label_button_n_clicks:          Label button
        unlabel_button:                 Un-label button
        unlabel_all_button:             Unlabel all button
        mlcoach_label_button:           Button to label with mlcoach results
        clinic_label_button:            Label button under DataClinic tab
        thumbnail_image_index:          Index of the thumbnail image
        thumbnail_image_select_value:   Selected thumbnail image (n_clicks)
        thumbnail_name_children:        Filename of the selected thumbnail image
        current_labels_name:            Dictionary of labeled images, e.g., {0: [image filenames],...}
        threshold:                      Threshold value
        label_dict:                     Dict of label names (tag name), e.g., {0: 'label',...}
        input_labels:                   A list of ordered labels from Add Label button in DataClinic pop window
        clinic_filenames:               Dictionary of labeled images from DataClinic pop window, e.g., {0: [image filenames],...} 
    Returns:
        labels_data:                    Dictionary of labeled images, e.g., {label: list of image indexes}
        labels_name_data:               Dictionary of labeled images, e.g., {label: list of image filenames}
    '''
    label_dict = {int(key): value for key,value in label_dict.items()}
    changed_id = dash.callback_context.triggered[-1]['prop_id']
    # if the list of labels is modified
    if changed_id == 'del-label.data' and del_label>-1:
        if str(del_label) in current_labels_name.keys():
            current_labels_name.pop(str(del_label))
        return current_labels_name, None
    
    label_class_value = -1
    # figures out the latest-clicked label button index
    if bool(label_button_n_clicks):
        label_class_value = sorted(label_dict.keys())[max(enumerate(label_button_n_clicks),\
                                                      key=lambda t: 0 if t[1] is None else t[1])[0]]
    selected_thumbs = []
    selected_thumbs_filename = []
    # add empty list to browser cache to store indices of thumbs
    if str(label_class_value) not in current_labels_name.keys():
        current_labels_name[str(label_class_value)] = []
    
    changed_id = dash.callback_context.triggered[-1]['prop_id']
    if changed_id == 'mlcoach-label.n_clicks':
        filenames = df_prob['filename'][df_prob.iloc[:,label_class_value+1]>threshold/100].tolist()
        MLCOACH_PATH = '/'.join(docker_to_local_path(thumbnail_name_children[0], DOCKER_HOME, LOCAL_HOME, type='str').split('/')[:-2])
        for indx, filename in enumerate(filenames):
            selected_thumbs.append(indx)
            # the next line is needed bc the filenames in mlcoach do not match (only good for selecting single folder/subfolder )
            selected_thumbs_filename.append(MLCOACH_PATH+'/'+filename)
    
    elif changed_id == 'clinic-label.n_clicks':
        for key, name_list in clinic_filenames.items():
            if key in current_labels_name.keys():
                current_labels_name[key].extend(name_list)
            else:
                current_labels_name[key] = name_list
    
    else:
        for thumb_id, select_value, filename in zip(thumbnail_image_index, thumbnail_image_select_value,
                                                    thumbnail_name_children):
            index = thumb_id['index']
            if select_value is not None:
                # add selected thumbs to the label key corresponding to last pressed button
                if select_value % 2 == 1:
                    selected_thumbs.append(index)
                    selected_thumbs_filename.append(filename)

    selected_thumbs_filename = local_to_docker_path(selected_thumbs_filename, DOCKER_HOME, LOCAL_HOME, 'list')

    if dash.callback_context.triggered[0]['prop_id'] == 'un-label.n_clicks':
        for thumb_name in selected_thumbs_filename:
            for names in current_labels_name.values():
                if thumb_name in names:
                    names.remove(thumb_name)
    else:
        if str(label_class_value) in current_labels_name.keys():
            current_labels_name[str(label_class_value)].extend(selected_thumbs_filename)
        
    if dash.callback_context.triggered[0]['prop_id'] == 'un-label-all.n_clicks':
        current_labels_name = {}
        return current_labels_name, None

    if label_class_value == -1:
        return current_labels_name, None
    
    return current_labels_name, label_dict[label_class_value]


@app.callback(
    [Output('label_buttons', 'children'),
     Output('modify-list', 'n_clicks'),
     Output('label-dict', 'data'),
     Output('del-label', 'data')],

    Input("tab-group", "value"),
    Input('modify-list', 'n_clicks'),
    Input({'type': 'delete-label-button', 'index': ALL}, 'n_clicks'),
    Input('clinic-add-label-button', 'n_clicks'),

    State('add-label-name', 'value'),
    State('label-dict', 'data'),
    State('docker-labels-name', 'data'),
    State({'type': 'clinic-label-input', 'index': ALL}, 'value'),
    prevent_initial_call=True
)
def update_list(tab_value, n_clicks, n_clicks2, clinic_add_label_button,
                add_label_name, label_dict, labels_name_data, input_labels):
    '''
    This callback updates the list of labels. In the case a label is deleted, the index of this label is saved in
    cache so that the list of assigned labels can be updated in the next callback
    Args:
        tab_value:                  Tab option
        n_clicks:                   Button to add a new label (tag name)
        n_clicks2:                  Delete the associated label (tag name)
        clinic_add_label_button:    Add Label button in DataClinic pop window 
        add_label_name:             Label to add (tag name)
        label_dict:                 Dict of label names (tag name), e.g., {0:'label',...}
        labels_name_data:           Dictionary of labeled images (docker path), as follows: {label: list of image filenames}
        input_labels:               A list of ordered labels from Add Label button in DataClinic pop window
    Returns:
        label_component:        Reactive component with the updated list of labels
        modify_lists.n_clicks:  Number of clicks for the modify list button
        label_dict:             List of labels
        del_label:              Index of the deleted label
    '''
    label_dict = {int(key): value for key,value in label_dict.items()}
    indx = -1
    changed_id = dash.callback_context.triggered[-1]['prop_id']
    if changed_id == 'tab-group.value':
        if tab_value == 'manual':
            label_dict = LABEL_LIST
        elif tab_value == 'mlcoach':
            label_dict = {key: value for key,value in zip(range(len(list(df_prob.columns[1:]))), list(df_prob.columns[1:]))}
        elif tab_value == 'clinic':
            label_dict = {}
    
    del_button = False 
    if tab_value == 'manual':
        del_button = True
    
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if changed_id == 'clinic-add-label-button.n_clicks':
        for new_label in input_labels:
            if new_label is not None:
                if new_label not in label_dict.values():
                    label_dict[len(label_dict.keys())] = new_label

    add_clicks = n_clicks
    if 'delete-label-button' in changed_id and any(n_clicks2):
        rem = changed_id[changed_id.find('index')+7:]
        indx = int(rem[:rem.find(',')])
        try:
            label_dict.pop(indx)    # remove label from tagged images
        except Exception as e:
            print(e)
            
    if add_clicks > 0:
        if len(label_dict.keys()) < max(label_dict.keys())+1:
            key_to_add = 0
            last_key = -1
            for key in sorted(label_dict.keys()):
                if key > last_key + 1:
                    key_to_add = last_key +1
                    break
                else:
                    last_key += 1
            if key_to_add == max(label_dict.keys()):
                key_to_add = max(label_dict.keys())+1
            label_dict[key_to_add] = add_label_name
        else:
            label_dict[max(label_dict.keys())+1] = add_label_name
    
    return [create_label_component(label_dict, del_button=del_button), 0, label_dict, indx]


@app.callback(
    Output('save-results-buffer', 'data'),
    Input('button-save-disk', 'n_clicks'),
    State('docker-file-paths','data'),
    State('docker-labels-name', 'data'),
    State('label-dict', 'data'),
    State('import-dir', 'n_clicks'),
    State('files-table', 'selected_rows')
)
def save_labels_disk(button_save_disk_n_clicks, file_paths, labels_name_data,
                     label_dict, import_n_clicks, rows):
    '''
    This callback saves the labels to disk
    Args:
        button_save_disk_n_clicks:  Button save to disk
        file_paths:                 Absolute file paths selected from path table
        labels_name_data:           Dictionary of labeled images (docker path), as follows: {0: [image filenames],...}
        label_dict:                 Dictionary of label names (tag name), e.g., {0: 'label',...}
        import_n_clicks:            Button for importing selected paths
        rows:                       Rows of the selected file paths from path table
    Returns:
        The data is saved in the output directory
    '''
    label_dict = {int(key):value for key,value in label_dict.items()}
    if labels_name_data is not None and import_n_clicks and bool(rows):
        if len(labels_name_data)>0:
            print('Saving labels')
            for label_index in labels_name_data:
                filename_list = labels_name_data[label_index]
                if len(filename_list)>0:
                    # create root directory
                    root = pathlib.Path(DOCKER_DATA / 'labelmaker_outputs')
                    label_dir = root / pathlib.Path(label_dict[int(label_index)])
                    label_dir.mkdir(parents=True, exist_ok=True)
                    # save all files under the current label into the directory
                    for filename in filename_list:
                        im_bytes = filename
                        im = PIL.Image.open(im_bytes)
                        filename = im_bytes.split("/")[-1]
                        f_name = filename.split('.')[-2]
                        f_ext  = filename.split('.')[-1]
                        i = 0
                        while check_duplicate_filename(label_dir,filename): # check duplicate filenames and save as different names 
                            if i:
                                filename = f_name + '_%s'%i + '.' + f_ext
                            i += 1 
                        im_fname = label_dir / pathlib.Path(filename)
                        im.save(im_fname)
    return []


if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0')



