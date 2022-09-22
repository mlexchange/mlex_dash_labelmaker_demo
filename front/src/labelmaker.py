import io, os, json, itertools, time
import shutil, pathlib, base64, math, zipfile
import requests
import uuid

import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State, MATCH, ALL
from dash.exceptions import PreventUpdate
from flask_caching import Cache
import numpy as np
import pandas as pd
import PIL
from PIL import Image
import plotly.express as px
from tiled.client import from_uri
from tiled.client.array import ArrayClient
from tiled.client.cache import Cache as TiledCache

from helper_utils import get_color_from_label, create_label_component, draw_rows, get_trained_models_list, adapt_tiled_filename, \
                         parse_full_screen_content   
from app_layout import app, DOCKER_DATA, UPLOAD_FOLDER_ROOT
from file_manager import filename_list, move_a_file, move_dir, add_paths_from_dir, \
                         check_duplicate_filename, docker_to_local_path, local_to_docker_path


# Font and background colors associated with each theme
text_color = {"dark": "#95969A", "light": "#595959"}
card_color = {"dark": "#2D3038", "light": "#FFFFFF"}

NUMBER_OF_ROWS = 4
USER = 'admin'
LOCAL_DATA = str(os.environ['DATA_DIR'])
DOCKER_HOME = str(DOCKER_DATA) + '/'
LOCAL_HOME = str(LOCAL_DATA)
TILED_KEY = str(os.environ['TILED_KEY'])
TILED_CLIENT = from_uri(f'http://tiled-server:8000/api?api_key={TILED_KEY}', cache=TiledCache.on_disk('data/cache'))

#====================================== memoization ======================================
cache = Cache(app.server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory'
})

TIMEOUT = 60

@cache.memoize(timeout=TIMEOUT)
def query_data(file_paths, tiled_on):
    list_filename = []
    if tiled_on and len(file_paths)>0:    # load through tiled
        file_path = file_paths[0]['file_path'].replace(DOCKER_HOME, '')
        subdir = file_path.split('/')
        tiled_client = TILED_CLIENT
        for local_dir in subdir:
            tiled_client = tiled_client[local_dir]
        tmp_list = list(tiled_client)
        if isinstance(tiled_client[tmp_list[0]], ArrayClient):
            list_filename = tmp_list
            list_filename = list(map(adapt_tiled_filename, list_filename, [file_paths[0]['file_path']]*len(list_filename)))
    else:           # load through file reading
        for file_path in file_paths:
            if file_path['file_type'] == 'dir':
                list_filename = add_paths_from_dir(file_path['file_path'], ['tiff', 'tif', 'jpg', 'jpeg', 'png'], list_filename)
            else:
                list_filename.append(file_path['file_path'])
    return json.dumps(list_filename)


def load_filenames(file_paths, tiled_on):
    return json.loads(query_data(file_paths, tiled_on))


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
        body_txt = [dbc.Label('1. Please use the File Manager on the left to import/load the dataset of interest.'),
                    dbc.Label('2. Click the DataClinic tab. Use the "Go to" button to open DataClinic and train unsupervised learning algorithms to estimate image similarity. \
                               Then, come back to the DataClinic tab in Label Maker to load the results and label batches of similar images.'),
                    dbc.Label('3. Click the Manual tab to manually label images or make corrections to the previous step. \
                               Save the current labels by clicking the button Save Labels to Disk.'),
                    dbc.Label('4. Click the MLCoach tab. Use the "Go to" button to open MLCoach and do supervised learning for image classification using the previously saved labels. \
                               Then, come back to the MLCoach tab in Label Maker to load the results and label the full dataset using their estimated probabilities. \
                               Click the Manual tab to manually label images or make corrections to the previous step.'),
                    dbc.Label('5. Finally, save all the labels by clicking the button Save Labels to Disk.')]
    # Tab instructions
    else:
        if tab_value == 'data_clinic':
            body_txt = [dbc.Label('1. Select a trained model to start.', className='mr-2'),
                        dbc.Label('2. Click on the image of interest. Then click Find Similar Images button below.', className='mr-2'),
                        dbc.Label('3. The image display updates according to the trained model results. Label as usual.', className='mr-2'),
                        dbc.Label('4. To exit this similarity based display, click Stop Find Similar Images.', className='mr-2')]
        
        else:           # mlcoach
            body_txt = [dbc.Label('1. Select a trained model to start.', className='mr-2'),
                        dbc.Label('2. Select the label name to be assigned accross the dataset in the dropdown beneath Probability Threshold.', className='mr-2'),
                        dbc.Label('3. Use the slider to setup the probability threshold.', className='mr-2'),
                        dbc.Label('4. Click Label with Threshold.', className='mr-2')]

    return not is_open, body_txt


@app.callback(
    Output("collapse", "is_open"),
    Input("collapse-button", "n_clicks"),
    Input('import-dir', 'n_clicks'),
    State("collapse", "is_open")
)
def toggle_collapse(n, import_n_clicks, is_open):
    if n or import_n_clicks:
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
    function(n_clicks, tab_value) {
        if (tab_value == 'mlcoach') {
            window.open('https://mlcoach.mlexchange.als.lbl.gov');
        } else if (tab_value == 'clinic') {
            window.open('https://dataclinic.mlexchange.als.lbl.gov');
        } 
        return '';
    }
    """,
    Output('dummy1', 'data'),
    Input('goto-webpage', 'n_clicks'),
    State('tab-group', 'value')
)


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
    Output("modal-un-label", "is_open"),
    Input("un-label-all", "n_clicks"),
    Input("confirm-un-label-all", "n_clicks"),
    State("modal-un-label", "is_open")
)
def toggle_modal_unlabel(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


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
    Output('dummy-data', 'data'),
    Input('dash-uploader', 'isCompleted'),
    State('dash-uploader', 'fileNames'),
)
def upload_zip(iscompleted, upload_filename):
    if not iscompleted:
        return 0

    if upload_filename is not None:
        path_to_zip_file = pathlib.Path(UPLOAD_FOLDER_ROOT) / upload_filename[0]
        if upload_filename[0].split('.')[-1] == 'zip':
            zip_ref = zipfile.ZipFile(path_to_zip_file)                 # create zipfile object
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

    Input('clear-data', 'n_clicks'),
    Input('browse-format', 'value'),
    Input('import-dir', 'n_clicks'),
    Input('confirm-delete','n_clicks'),
    Input('move-dir', 'n_clicks'),
    Input('docker-file-paths', 'data'),
    Input('my-toggle-switch', 'value'),
    Input('dummy-data', 'data'),

    State('dest-dir-name', 'value'),
    State('files-table', 'selected_rows'),
)
def load_dataset(clear_data, browse_format, import_n_clicks, delete_n_clicks, 
                move_dir_n_clicks, selected_paths, docker_path, uploaded_data, dest, rows):
    '''
    This callback displays manages the actions of file manager
    Args:
        clear_data:         Clear loaded images
        browse_format:      File extension to browse
        import_n_clicks:    Import button
        delete_n_clicks:    Delete button
        move_dir_n_clicks:  Move button
        selected_paths:     Selected paths in cache
        docker_path:        [bool] docker vs local path
        dest:               Destination path
        rows:               Selected rows
    Returns
        files:              Filenames to be displayed in File Manager according to browse_format from docker/local path
        selected_files:     List of selected filename FROM DOCKER PATH (no subdirectories)
    '''
    changed_id = dash.callback_context.triggered[0]['prop_id']
    files = filename_list(DOCKER_DATA, browse_format)
        
    selected_files = []
    if bool(rows):
        for row in rows:
            selected_files.append(files[row])
    
    if changed_id == 'confirm-delete.n_clicks':
        for filepath in selected_files:
            if os.path.isdir(filepath['file_path']):
               shutil.rmtree(filepath['file_path'])
            else:
                os.remove(filepath['file_path'])
        selected_files = []
        files = filename_list(DOCKER_DATA, browse_format)
    
    if changed_id == 'move-dir.n_clicks':
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
    
    if changed_id == 'clear-data.n_clicks':
        selected_files = []

    if docker_path:
        return files, selected_files
    else:
        return docker_to_local_path(files, DOCKER_HOME, LOCAL_HOME), selected_files


@app.callback(
    Output('on-off-display', 'color'),
    Output('on-off-display', 'label'),
    Input('find-similar-unsupervised', 'n_clicks'),
)
def display_indicator(n_clicks):
    '''
    This callback controls the light indicator in the DataClinic tab, which indicates whether the similarity-based
    image display is ON or OFF
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
    Input('my-toggle-switch', 'value'),
    Input('docker-file-paths','data'),
    Input('import-dir', 'n_clicks'),
    Input('import-format', 'value'),
    Input('files-table', 'selected_rows'),
    Input('button-hide', 'n_clicks'),
    Input('button-sort', 'n_clicks'),
    Input('confirm-delete','n_clicks'),
    Input('move-dir', 'n_clicks'),
    Input('tab-group', 'value'),
    Input('tiled-switch', 'on'),

    State({'type': 'thumbnail-name', 'index': ALL}, 'children'),
    State({'type': 'thumbnail-image', 'index': ALL}, 'n_clicks_timestamp'),
    State('data-clinic-model-list', 'value'),
    State('docker-labels-name', 'data'),
    State('label-dict', 'data'),
    State('image-order','data'),
    prevent_initial_call=True)
def display_index(exit_similar_images, find_similar_images, docker_path, file_paths, import_n_clicks, import_format,
                  rows, button_hide_n_clicks, button_sort_n_clicks, delete_n_clicks, move_dir_n_clicks, tab_selection,
                  tiled_on, thumbnail_name_children, timestamp, data_clinic_model, labels_name_data, label_dict,
                  image_order):
    '''
    This callback arranges the image order according to the following actions:
        - New content is uploaded
        - Buttons sort or hidden are selected
        - Find similar images display has been activated or deactivated
    Args:
        exit_similar_images:        Button "Exit Find Similar Images" has been clicked
        find_similar_images:        Button "Find Similar Images" has been clicked
        docker_path:                [Bool] show docker path T/F
        file_paths :                Absolute (docker) file paths selected from path table
        import_n_clicks:            Button for importing selected paths
        import_format:              File format for import
        rows:                       Rows of the selected file paths from path table
        button_hide_n_clicks:       Hide button
        button_sort_n_clicks:       Sort button
        delete_n_clicks:            Button for deleting selected file paths
        move_dir_n_clicks:          Button for moving dir
        tab_selection:              Current tab [Manual, Data Clinic, MLCoach]
        tiled_on:                   Tiled has been selected to load the dataset
        thumbnail_name_children:    Filenames of images in current page
        timestamp:                  Timestamps of selected images in current page - to find similar images. Currently,
                                    one 1 image is selected for this operation
        data_clinic_model:          Selected data clinic model
        labels_name_data:           Dictionary of labeled images (docker path), as follows: {label: list of image filenames}
        label_dict:                 Dict of label names (tag name), e.g., {0: 'label',...}
        image_order:                Order of the images according to the selected action (sort, hide, new data, etc)

    Returns:
        image_order:                Order of the images according to the selected action (sort, hide, new data, etc)
        data_access_open:           Closes the reactive component to select the data access (upload vs. directory)
    '''
    if import_n_clicks==0:
        raise PreventUpdate
    start = time.time()
    supported_formats = []
    import_format = import_format.split(',')
    if import_format[0] == '*':
        supported_formats = ['tiff', 'tif', 'jpg', 'jpeg', 'png']
    else:
        for ext in import_format:
            supported_formats.append(ext.split('.')[1])

    changed_id = dash.callback_context.triggered[0]['prop_id']
    print(f'The image order is triggered by: {changed_id}')
    if changed_id == 'tab-group.value' and tab_selection != 'mlcoach':
        return [dash.no_update]*4

    similar_img_clicks = dash.no_update
    button_hide = dash.no_update

    if 'find-similar-unsupervised.n_clicks' in changed_id:
        clicked_ind = [i for i, e in enumerate(timestamp) if e != None]
        if len(clicked_ind) > 0:                # if more than one image is selected
            clicked_ind = clicked_ind[-1]       # we take the last one
        filenames = []
        list_filename = []
        for file_path in file_paths:
            if file_path['file_type'] == 'dir':
                list_filename = add_paths_from_dir(file_path['file_path'], supported_formats, list_filename)
            else:
                list_filename.append(file_path['file_path'])

        labeled_filenames = list(itertools.chain.from_iterable(list(labels_name_data.values())))
        match_ind = [i for i, item in enumerate(list_filename) if item in set(labeled_filenames)]

        if bool(clicked_ind) and data_clinic_model:
            ind = int(clicked_ind)
            if docker_path:
                filenames.append(thumbnail_name_children[ind])
            else:
                filenames.append(local_to_docker_path(thumbnail_name_children[ind], DOCKER_HOME, LOCAL_HOME, type='str'))
            filename = filenames[0]
            if data_clinic_model:
                df_clinic = pd.read_csv(data_clinic_model)
                row_dataframe = df_clinic.iloc[df_clinic.set_index('filename').index.get_loc(filename)]
                image_order = [int(order) for order in row_dataframe.values[1:].tolist()]
                image_order = [x for x in image_order if x not in set(match_ind)]       # filter labeled images
        else:
            # if no image is selected, no update is triggered
            return dash.no_update, 0, dash.no_update

    elif import_n_clicks and bool(rows):
        list_filename = load_filenames(file_paths, tiled_on)
        if changed_id == "import-dir.n_clicks":
            params = {'key': 'datapath'}
            resp = requests.post("http://labelmaker-api:8005/api/v0/import/datapath", params=params, json=file_paths)
            params = {'key': 'filenames'}
            resp = requests.post("http://labelmaker-api:8005/api/v0/import/datapath", params=params, json=list_filename)
        
        num_imgs = len(list_filename)
        if  changed_id == 'import-dir.n_clicks' or \
            changed_id == 'confirm-delete.n_clicks' or \
            changed_id == 'files-table.selected_rows' or \
            changed_id == 'move_dir_n_clicks':
            image_order = list(range(num_imgs))

        if changed_id == 'button-hide.n_clicks':
            similar_img_clicks = 0
            if button_hide_n_clicks % 2 == 1:
                labeled_names = list(itertools.chain(*labels_name_data.values()))
                unlabeled_filenames = set(list_filename)-set(labeled_names)
                image_order = [i for i, el in enumerate(list_filename) if el in unlabeled_filenames]
            else:
                image_order = list(range(num_imgs))
        
        elif changed_id == 'exit-similar-unsupervised.n_clicks' or tab_selection=='mlcoach':
            button_hide = 0
            similar_img_clicks = 0
            image_order = list(range(num_imgs))

        if changed_id == 'button-sort.n_clicks':
            button_hide = 0
            similar_img_clicks = 0
            new_indx = [[] for i in range(len(label_dict.keys()) + 1)]
            for key_label in labels_name_data:
                key_filenames = list(set(list_filename) & set(labels_name_data[key_label]))
                new_indx[int(key_label)] = [i for i, el in enumerate(list_filename) if el in key_filenames]
            image_order = list(itertools.chain(*new_indx))
            unlabeled = [i for i in list(range(num_imgs)) if i not in image_order]
            image_order = image_order + unlabeled
    else:
        image_order = []
    print(f'Image order is done after {time.time()-start}. Number of images is {len(image_order)}.')
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
    Input('files-table', 'selected_rows'),
    Input('import-format', 'value'),
    Input('docker-file-paths','data'),
    Input('my-toggle-switch', 'value'),
    Input('tiled-switch', 'on'),
    Input('mlcoach-collapse', 'is_open'),
    Input('mlcoach-model-list', 'value'),
    
    State('find-similar-unsupervised', 'n_clicks'),
    State('current-page', 'data'),
    State('import-dir', 'n_clicks'),
    State('docker-labels-name', 'data'),
    State('tab-group', 'value'),
    State('previous-tab', 'data')],
    prevent_initial_call=True)
def update_output(image_order, thumbnail_slider_value, button_prev_page, button_next_page, rows, import_format,
                  file_paths, docker_path, tiled_on, ml_coach_is_open, mlcoach_model, find_similar_images, current_page,
                  import_n_clicks, labels_name_data, tab_selection, previous_tab):
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
        tiled_on:               Tiled has been selected to load the dataset
        ml_coach_is_open:       MLCoach is the labeling method
        mlcoach_model:          Selected MLCoach model
        find_similar_images:    Find similar images button, n_clicks
        current_page:           Index of the current page
        import_n_clicks:        Button for importing the selected paths
        labels_name_data:       Dictionary of labeled images (docker path), as follows: {label: list of image filenames}
        tab_selection:          Current tab [Manual, Data Clinic, MLCoach]
        previous_tab:           List of previous tab selection [Manual, Data Clinic, MLCoach]
    Returns:
        children:               Images to be displayed in front-end according to the current page index and # of columns
        prev_page:              Enable/Disable previous page button if current_page==0
        next_page:              Enable/Disable next page button if current_page==max_page
        current_page:           Update current page index if previous or next page buttons were selected
    '''
    start = time.time()
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

    if changed_id == 'mlcoach-collapse.is_open':
        if tab_selection=='mlcoach':        # if the previous tab is mlcoach, the display should be updated
            current_page = 0                # to remove the probability list per image
        elif previous_tab[-2] != 'mlcoach':
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    children = []
    num_imgs = 0
    if (import_n_clicks and bool(file_paths)) or changed_id == 'tiled-switch.on':
        num_imgs = len(image_order)
        start_indx = NUMBER_OF_ROWS * thumbnail_slider_value * current_page
        max_indx = min(start_indx + NUMBER_OF_ROWS * thumbnail_slider_value, num_imgs)
        new_contents = []
        new_filenames = []
        if num_imgs>0:
            list_filename = load_filenames(file_paths, tiled_on)
            if tiled_on:    # load through tiled
                file_path = file_paths[0]['file_path'].replace(DOCKER_HOME, '')
                subdir = file_path.split('/')
                tiled_client = TILED_CLIENT
                for local_dir in subdir:
                    tiled_client = tiled_client[local_dir]
                for i in range(start_indx, max_indx):
                    rawBytes = io.BytesIO()
                    img = tiled_client.values_indexer[image_order[i]].export(rawBytes, format='jpeg')
                    rawBytes.seek(0)        # return to the start of the file
                    img = base64.b64encode(rawBytes.read())
                    new_contents.append(f'data:image/jpeg;base64,{img.decode("utf-8")}')
                    if docker_path:
                        new_filenames.append(list_filename[image_order[i]])
                    else:
                        new_filenames.append(docker_to_local_path(list_filename[image_order[i]], DOCKER_HOME, LOCAL_HOME, 'str'))
            else:           # load through file reading
                # plot images according to current page index and number of columns
                for i in range(start_indx, max_indx):
                    filename = list_filename[image_order[i]]
                    img = Image.open(filename)
                    img = img.resize((300, 300))
                    rawBytes = io.BytesIO()
                    img.save(rawBytes, "JPEG")
                    rawBytes.seek(0)        # return to the start of the file
                    img = base64.b64encode(rawBytes.read())
                    file_ext = filename[filename.find('.')+1:]
                    new_contents.append('data:image/'+file_ext+';base64,'+img.decode("utf-8"))
                    if docker_path:
                        new_filenames.append(list_filename[image_order[i]])
                    else:
                        new_filenames.append(docker_to_local_path(list_filename[image_order[i]], DOCKER_HOME,
                                                                LOCAL_HOME, 'str'))
        if mlcoach_model and tab_selection=='mlcoach':
            df_prob = pd.read_csv(mlcoach_model)
            children = draw_rows(new_contents, new_filenames, NUMBER_OF_ROWS, thumbnail_slider_value,
                                    ml_coach_is_open, df_prob)
        elif find_similar_images:
            pre_highlight = True
            filenames = local_to_docker_path(new_filenames, DOCKER_HOME, LOCAL_HOME, 'list')
            for name in filenames:                  # if there is one label in page, do not pre-highlight
                for label_key in labels_name_data:
                    if name in labels_name_data[label_key]:
                        pre_highlight = False
                        break
            if find_similar_images>0 and pre_highlight:
                children = draw_rows(new_contents, new_filenames, NUMBER_OF_ROWS, thumbnail_slider_value, 
                        data_clinic=True)
            else:
                children = draw_rows(new_contents, new_filenames, NUMBER_OF_ROWS, thumbnail_slider_value)
        else:
            children = draw_rows(new_contents, new_filenames, NUMBER_OF_ROWS, thumbnail_slider_value)

    print(f'Total time to display images: {time.time() - start}')
    return children, current_page==0, math.ceil((num_imgs//thumbnail_slider_value)/NUMBER_OF_ROWS)<=current_page+1, \
           current_page


@app.callback(
    Output({'type': 'thumbnail-card', 'index': MATCH}, 'color'),

    Input({'type': 'thumbnail-image', 'index': MATCH}, 'n_clicks'),
    Input('docker-labels-name', 'data'),
    Input('my-toggle-switch', 'value'),

    State({'type': 'thumbnail-name', 'index': MATCH}, 'children'),
    State('color-cycle', 'data')
)
def select_thumbnail(value, labels_name_data, docker_path, thumbnail_name_children, color_cycle):
    '''
    This callback assigns a color to thumbnail cards in the following scenarios:
        - An image has been selected, but no label has been assigned (blue)
        - An image has been labeled (label color)
        - An image has been unselected or unlabeled (no color)
    Args:
        value:                      Thumbnail card that triggered the callback (n_clicks)
        labels_name_data:           Dictionary of labeled images, as follows: {0: [image filenames]}
        docker_path:                [Bool] show docker path T/F
        thumbnail_name_children:    Filename in selected thumbnail
    Returns:
        thumbnail_color:            Color of thumbnail card
    '''
    start = time.time()
    name = thumbnail_name_children
    if not docker_path:
        name =  local_to_docker_path(name, DOCKER_HOME, LOCAL_HOME, 'str')
    color = ''
    for label_key in labels_name_data:
        if name in labels_name_data[label_key]:
            color = get_color_from_label(label_key, color_cycle)
            break
    print(f'Total time to select image: {time.time() - start}')
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
    if all(x is None for x in label_button_trigger) and unlabel_n_clicks is None and unlabel_all is None:
        return [dash.no_update]*len(thumb_clicked)
    return [0 for thumb in thumb_clicked]


@app.callback(
    Output({'type': 'full-screen-modal', 'index': ALL}, 'children'),
    Output({'type': 'full-screen-modal', 'index': ALL}, 'is_open'),
    Output({'type': 'double-click-entry', 'index': ALL}, 'n_events'),

    Input({'type': 'double-click-entry', 'index': ALL}, 'n_events'),

    State({'type': 'thumbnail-name', 'index': ALL}, 'children'),
    State('tiled-switch', 'on'),
    State('my-toggle-switch', 'value'),
    prevent_initial_call=True
)
def full_screen_thumbnail(double_click, thumbnail_name_children, tiled_on, docker_path):
    '''
    This callback opens the modal pop-up window with the full size image that was double-clicked
    Args:
        double_click:               List of number of times that every card has been double-clicked
        thumbnail_name_children:    List of the thumbnails filenames
        tiled_on:                   [Bool] indicates if tiled reading is ON/OFF
        docker_path:                [Bool] show docker path T/F
    Returns:
        contents:                   Contents for pop-up window
        open_modal:                 Open/close modal
        double_click:               Resets the number of double-clicks to zero
    '''
    if 1 not in double_click:
        raise PreventUpdate
    filename = thumbnail_name_children[double_click.index(1)]
    if not docker_path:
        docker_name = local_to_docker_path(filename, DOCKER_HOME, LOCAL_HOME, 'str')
    else:
        docker_name = filename
    if tiled_on:    # load through tiled
        file_path = docker_name.replace(str(DOCKER_DATA), '')
        file_path = file_path.split('/')
        subdir = file_path[:-1]
        tiled_client = TILED_CLIENT
        for local_dir in subdir:
            tiled_client = tiled_client[local_dir]
        test = file_path[-1].split('.')[0]
        np_img = tiled_client[file_path[-1].split('.')[0]][:]
        img = Image.fromarray(np_img)
    else:           # load from file reading
        img = Image.open(docker_name)
    rawBytes = io.BytesIO()
    img.save(rawBytes, "JPEG")
    rawBytes.seek(0)        # return to the start of the file
    img = base64.b64encode(rawBytes.read())
    file_ext = filename[filename.find('.')+1:]
    img_contents = 'data:image/'+file_ext+';base64,'+img.decode("utf-8")
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
    Output('docker-labels-name', 'data'),
    Output({'type': 'label-percentage', 'index': ALL}, 'value'),
    Output({'type': 'label-percentage', 'index': ALL}, 'label'),
    Output('total_labeled', 'children'),

    Input('del-label', 'data'),
    Input({'type': 'label-button', 'index': ALL}, 'n_clicks_timestamp'),
    Input('un-label', 'n_clicks'),
    Input('confirm-un-label-all', 'n_clicks'),
    Input('mlcoach-label', 'n_clicks'),
    Input('clinic-label', 'n_clicks'),
    Input('mlcoach-model-list', 'value'),

    State('image-order', 'data'),
    State({'type': 'thumbnail-image', 'index': ALL}, 'id'),
    State({'type': 'thumbnail-image', 'index': ALL}, 'n_clicks'),
    State({'type': 'thumbnail-name', 'index': ALL}, 'children'),
    State('docker-labels-name', 'data'),
    State('probability-threshold', 'value'),
    State('label-dict', 'data'),
    State('clinic-filenames', 'data'),
    State('docker-file-paths', 'data'),
    State({'type': 'label-percentage', 'index': ALL}, 'label'),
    State({'type': 'label-percentage', 'index': ALL}, 'id'),
    State('mlcoach-label-name', 'value'),
    State('tiled-switch', 'on'),
    prevent_initial_call=True
)
def label_selected_thumbnails(del_label, label_button_n_clicks, unlabel_button, unlabel_all_button,
                              mlcoach_label_button, clinic_label_button, mlcoach_model, image_order,
                              thumbnail_image_index, thumbnail_image_select_value, thumbnail_name_children,
                              current_labels_name, threshold, label_dict, clinic_filenames, docker_file_paths,
                              labeled_amount, labeled_amount_indx, mlcoach_label, tiled_on):
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
        mlcoach_model:                  Selected MLCoach model
        thumbnail_image_index:          Index of the thumbnail image
        thumbnail_image_select_value:   Selected thumbnail image (n_clicks)
        thumbnail_name_children:        Filename of the selected thumbnail image
        current_labels_name:            Dictionary of labeled images, e.g., {0: [image filenames],...}
        threshold:                      Threshold value
        label_dict:                     Dict of label names (tag name), e.g., {0: 'label',...}
        clinic_filenames:               Dictionary of labeled images from DataClinic pop window, e.g., {0: [image filenames],...}
        docker_file_paths:              Absolute (docker) file paths selected from path table
        labeled_amount:                 Current amount of labeled images per label
    Returns:
        labels_data:                    Dictionary of labeled images, e.g., {label: list of image filenames}
        label_perc_value
        label_perc_label
        total_labeled
    '''
    start = time.time()
    list_labels_indx = [elem['index'] for elem in labeled_amount_indx]
    label_dict = {int(key): value for key,value in label_dict.items()}
    changed_id = dash.callback_context.triggered[-1]['prop_id']
    progress_values = [dash.no_update] * len(labeled_amount)
    labelmaker_filenames = load_filenames(docker_file_paths, tiled_on)

    # Check if a label has been deleted
    if changed_id == 'del-label.data' or changed_id == 'image-order.data':
        progress_labels = [dash.no_update] * len(labeled_amount)
        if del_label > -1:
            if str(del_label) in current_labels_name.keys():
                current_labels_name.pop(str(del_label))
        num_labeled_imgs = len(list(itertools.chain.from_iterable(list(current_labels_name.values()))))
        if num_labeled_imgs != 0:
            labeled_amount = [0] * len(labeled_amount)
            for name in current_labels_name.keys():
                labeled_amount[list_labels_indx.index(int(name))] = len(current_labels_name[name])
            progress_values = [100 * a / num_labeled_imgs for a in labeled_amount]
            progress_labels = list(map(str, labeled_amount))
        labeled_img = f'Labeled {num_labeled_imgs} out of {len(labelmaker_filenames)} images.'
        return current_labels_name, progress_values, progress_labels, labeled_img

    # initialize the values of the # of labeled images if the list of labels is updated
    if None not in labeled_amount:
        labeled_amount = list(map(int, labeled_amount))
    else:
        labeled_amount = [0] * len(labeled_amount)
        for name in current_labels_name.keys():
            labeled_amount[list_labels_indx.index(int(name))] = len(current_labels_name[name])

    # check if unlabel all is selected
    if dash.callback_context.triggered[0]['prop_id'] == 'confirm-un-label-all.n_clicks':
        current_labels_name = {}
        return current_labels_name, [0] * len(labeled_amount), ['0'] * len(labeled_amount), \
               f'Labeled 0 images out of {len(labelmaker_filenames)}'
    
    label_class_value = -1
    # figures out the latest-clicked label button index
    if bool(label_button_n_clicks):
        label_class_value = sorted(label_dict.keys())[max(enumerate(label_button_n_clicks),\
                                                      key=lambda t: 0 if t[1] is None else t[1])[0]]
    selected_thumbs = []
    selected_thumbs_filename = []
    # add empty list to browser cache to store indices of thumbs
    if label_class_value != -1 and str(label_class_value) not in current_labels_name.keys():
        current_labels_name[str(label_class_value)] = []

    # labeling with mlcoach
    if changed_id == 'mlcoach-label.n_clicks':
        if mlcoach_model:
            label_class_value = mlcoach_label
            if str(label_class_value) not in current_labels_name.keys():
                current_labels_name[str(label_class_value)] = []
            df_prob = pd.read_csv(mlcoach_model)
            tmp_filenames = []
            for ind, filename in enumerate(list(df_prob['filename'])):
                 tmp_filenames.append(filename.split(os.sep)[-1])
            df_prob['filename'] = tmp_filenames
            labeled_filenames = list(itertools.chain.from_iterable(list(current_labels_name.values())))
            tmp_labeled_filenames = []
            for ind, filename in enumerate(labeled_filenames):
                tmp_labeled_filenames.append(filename.split(os.sep)[-1])
            try:
                filenames = df_prob['filename'][df_prob[label_dict[label_class_value]]>threshold/100].tolist()
                for indx, filename in enumerate(filenames):
                    if filename not in tmp_labeled_filenames and tmp_example+'/'+filename in labelmaker_filenames\
                            and tmp_example+'/'+filename not in selected_thumbs_filename:
                        selected_thumbs.append(indx)
                        # the next line is needed bc the filenames in mlcoach do not match (only good for selecting single
                        # folder/subfolder )
                        selected_thumbs_filename.append(tmp_example+'/'+filename)
            except Exception as e:
                print(f'Exception {e}')

    # labeling with data clinic
    elif changed_id == 'clinic-label.n_clicks':
        for key, name_list in clinic_filenames.items():
            ## remove the previously assigned label before assigning new one
            for current_key in current_labels_name.keys():
                for file in name_list:
                    if file in current_labels_name[current_key]:
                        current_labels_name[current_key].remove(file)
                        labeled_amount[list_labels_indx.index(int(current_key))] -= 1
            ##
            if key in current_labels_name.keys():
                current_labels_name[key].extend(name_list)
            else:
                current_labels_name[key] = name_list
            ind = current_labels_name.index(key)
            labeled_amount[ind] =+ 1

    # manual labeling
    else:
        for thumb_id, select_value, filename in zip(thumbnail_image_index, thumbnail_image_select_value,
                                                    thumbnail_name_children):
            index = thumb_id['index']
            if select_value is not None:
                # add selected thumbs to the label key corresponding to last pressed button
                if select_value % 2 == 1:
                    ## remove the previously assigned label before assigning new one
                    for current_key in current_labels_name.keys():
                        docker_filename = local_to_docker_path(filename, DOCKER_HOME, LOCAL_HOME, 'str')
                        if docker_filename in current_labels_name[current_key]:
                            current_labels_name[current_key].remove(docker_filename)
                            labeled_amount[list_labels_indx.index(int(current_key))] -= 1
                    ##
                    selected_thumbs.append(index)
                    selected_thumbs_filename.append(filename)

    # get docker path to selected images
    selected_thumbs_filename = local_to_docker_path(selected_thumbs_filename, DOCKER_HOME, LOCAL_HOME, 'list')

    # if unlabel, remove the selected filenames from the labeled data
    if dash.callback_context.triggered[0]['prop_id'] == 'un-label.n_clicks':
        for thumb_name in selected_thumbs_filename:
            for key, names in zip(current_labels_name.keys(), current_labels_name.values()):
                if thumb_name in names:
                    names.remove(thumb_name)
                    labeled_amount[list_labels_indx.index(int(key))] -= 1
    else:   # otherwise, add them to it's respective label
        if str(label_class_value) in current_labels_name.keys():
            current_labels_name[str(label_class_value)].extend(selected_thumbs_filename)
            labeled_amount[list_labels_indx.index(label_class_value)] += len(selected_thumbs_filename)

    num_labeled_imgs = len(list(itertools.chain.from_iterable(list(current_labels_name.values()))))
    if num_labeled_imgs!=0:
        progress_values = list(100*np.array(labeled_amount)/num_labeled_imgs)

    print(f'Labeling callback takes {time.time()-start}')
    return current_labels_name, progress_values, list(map(str, labeled_amount)), \
           f'Labeled {num_labeled_imgs} out of {len(labelmaker_filenames)} images.'


@app.callback(
    [Output('label-buttons', 'children'),
     Output('modify-list', 'n_clicks'),
     Output('label-dict', 'data'),
     Output('del-label', 'data'),
     Output('mlcoach-model-list', 'options'),
     Output('data-clinic-model-list', 'options'),
     Output('mlcoach-label-name', 'options')],

    Input("tab-group", "value"),
    Input('modify-list', 'n_clicks'),
    Input('mlcoach-refresh', 'n_clicks'),
    Input('data-clinic-refresh', 'n_clicks'),
    Input({'type': 'delete-label-button', 'index': ALL}, 'n_clicks'),
    Input('mlcoach-model-list', 'value'),
    Input('docker-file-paths', 'data'),
    Input('color-cycle', 'data'),

    State('add-label-name', 'value'),
    State('label-dict', 'data'),
    State('docker-labels-name', 'data'),
    State({'type': 'clinic-label-input', 'index': ALL}, 'value'),
    prevent_initial_call=True
)
def update_list(tab_value, n_clicks, mlcoach_refresh, data_clinic_refresh, n_clicks2, mlcoach_model, datapath,
                color_cycle, add_label_name, label_dict, labels_name_data, input_labels):
    '''
    This callback updates the list of labels. In the case a label is deleted, the index of this label is saved in
    cache so that the list of assigned labels can be updated in the next callback
    Args:
        tab_value:                  Tab option
        n_clicks:                   Button to add a new label (tag name)
        n_clicks2:                  Delete the associated label (tag name)
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
    mlcoach_models = dash.no_update
    data_clinic_models = dash.no_update
    if 'tab-group.value' == changed_id or 'docker-file-paths.data' in changed_id or \
            'mlcoach-refresh.n_clicks' in changed_id or 'data-clinic-refresh.n_clicks' in changed_id:
        if tab_value == 'mlcoach':
            mlcoach_models = get_trained_models_list(USER, datapath, tab_value)
        if tab_value == 'clinic':
            data_clinic_models = get_trained_models_list(USER, datapath, tab_value)
    
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if 'mlcoach-model-list.value' in changed_id:
        if mlcoach_model:
            df_prob = pd.read_csv(mlcoach_model)
            mlcoach_labels = list(set(list(df_prob.columns[1:])) - set(list(label_dict.values())))
            current_num_keys = len(list(label_dict.keys()))
            num_keys = range(current_num_keys + len(mlcoach_labels))
            num_keys = list(set(num_keys) - set(list(label_dict.keys())))
            label_dict.update(({key: value for key, value in zip(num_keys, list(mlcoach_labels))}))

    if changed_id == 'clinic-add-label-button.n_clicks':
        for new_label in input_labels:
            if new_label is not None:
                if new_label.replace(' ', '_') not in label_dict.values():
                    label_dict[len(label_dict.keys())] = new_label.replace(' ', '_')

    add_clicks = n_clicks
    if 'delete-label-button' in changed_id and any(n_clicks2):
        rem = changed_id[changed_id.find('index')+7:]
        indx = int(rem[:rem.find(',')])
        try:
            label_dict.pop(indx)    # remove label from tagged images
        except Exception as e:
            print(e)
            
    if add_clicks > 0:
        add_label_name = add_label_name.replace(' ', '_')
        if len(label_dict.keys())>0:
            if add_label_name not in label_dict.values():
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
        else:
            label_dict = {0: add_label_name}

    options = []
    for elem in label_dict:
        options.append({'value': elem, 'label': label_dict[elem]})

    return [create_label_component(label_dict, color_cycle), 0, label_dict, indx, mlcoach_models, data_clinic_models,
            options]


@app.callback(
    Output('save-results-buffer', 'data'),
    Input('button-save-disk', 'n_clicks'),
    State('docker-file-paths','data'),
    State('docker-labels-name', 'data'),
    State('label-dict', 'data'),
    State('import-dir', 'n_clicks'),
    State('files-table', 'selected_rows')
)
def save_labels_disk(button_save_disk_n_clicks, file_paths, labels_name_data, label_dict, import_n_clicks, rows):
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
            # create root directory
            root = pathlib.Path(DOCKER_DATA / 'labelmaker_outputs' /str(uuid.uuid4()))
            params1 = {'key': 'datapath'}
            payload = [{'file_path': str(root), 'file_type': 'dir'}]
            resp = requests.post("http://labelmaker-api:8005/api/v0/export/datapath", params=params1, json=payload)
            total_filename_list = []
            for label_index in labels_name_data:
                filename_list = labels_name_data[label_index]
                if len(filename_list)>0:
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
                        im_fname = os.path.join(label_dir, pathlib.Path(filename))
                        im.save(im_fname)
                        total_filename_list.append(str(im_fname))
            params2 = {'key': 'filenames'}
            resp = requests.post("http://labelmaker-api:8005/api/v0/export/datapath", params=params2, json=total_filename_list)
    return []


if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8067)

