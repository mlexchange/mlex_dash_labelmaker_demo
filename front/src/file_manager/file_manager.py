import os
import pathlib, zipfile

import dash
from dash import html, Input, Output, State
import dash_bootstrap_components as dbc


from file_manager.dash_file_explorer import create_file_explorer
from file_manager.data_project import DataProject


class FileManager():
    def __init__(self, docker_home, local_home, data_folder_root, upload_folder_root,
                 max_file_size=60000):
        self.docker_home = docker_home
        self.local_home = local_home
        self.data_folder_root = data_folder_root
        self.upload_folder_root = upload_folder_root
        self.max_file_size = max_file_size

        self.file_explorer = html.Div(
            [
                dbc.Button(
                    'Toggle File Manager',
                    id='collapse-button',
                    size='lg',
                    className='m-2',
                    color='secondary',
                    outline=True,
                    n_clicks=0,
                ),
                dbc.Button(
                    'Clear Images',
                    id='clear-data',
                    size='lg',
                    className='m-2',
                    color='secondary',
                    outline=True,
                    n_clicks=0,
                ),
                dbc.Collapse(
                    create_file_explorer(max_file_size),
                    id='collapse',
                    is_open=True,
                ),
            ]
        )
        pass
    
    def init_callbacks(self, app):
        app.callback(
            Output('collapse', 'is_open'),
            [Input('collapse-button', 'n_clicks'),
             Input('import-dir', 'n_clicks'),
             State('collapse', 'is_open')]
        )(self._toggle_collapse)

        app.callback(
            Output('upload-data', 'data'),
            [Input('dash-uploader', 'isCompleted'),
             State('dash-uploader', 'fileNames')]
        )(self._upload_zip)

        app.callback(
            [Output('files-table', 'data'),
             Output('docker-file-paths', 'data'),
             Output('files-table', 'selected_rows')],
            [Input('browse-format', 'value'),
             Input('import-dir', 'n_clicks'),
             Input('upload-data', 'data'),
             Input('confirm-update-data', 'data'),
             Input('clear-data', 'n_clicks'),
             Input('tiled-switch', 'on'),
             State('files-table', 'selected_rows'),
             State('docker-file-paths', 'data'),
             State('tiled-uri', 'value'),
             State('files-table', 'data'),
             State('import-format', 'value')]
        )(self._load_dataset)

    @staticmethod
    def _toggle_collapse(n, import_n_clicks, is_open):
        '''
        Collapse the file manager once a data set has been selected
        Args:
            n:                  Number of clicks in collapse button
            import_n_clicks:    Number of clicks in import button
            is_open:            Bool variable indicating if file manager is collapsed or not
        '''
        if n or import_n_clicks:
            return not is_open
        return is_open

    def _upload_zip(self, iscompleted, upload_filename):
        '''
        Unzip uploaded files and save them at upload folder root
        Args:
            iscompleted:            Flag indicating if the upload + unzip are complete
            upload_filenames:       List of filenames that were uploaded
        '''
        if not iscompleted:
            return False
        if upload_filename is not None:
            path_to_zip_file = pathlib.Path(self.upload_folder_root) / upload_filename[0]
            if upload_filename[0].split('.')[-1] == 'zip':
                zip_ref = zipfile.ZipFile(path_to_zip_file)                 # create zipfile object
                path_to_folder = pathlib.Path(self.upload_folder_root) / \
                                 upload_filename[0].split('.')[-2]
                if (upload_filename[0].split('.')[-2] + '/') in zip_ref.namelist():
                    zip_ref.extractall(pathlib.Path(self.upload_folder_root))  # extract file to dir
                else:
                    zip_ref.extractall(path_to_folder)
                zip_ref.close()     # close file
                os.remove(path_to_zip_file)
        return True
    
    def _load_dataset(self, browse_format, import_n_clicks, uploaded_data, update_data, \
                      clear_data_n, tiled_on, rows, selected_paths, tiled_uri, files_table, \
                      import_format):
        '''
        This callback displays manages the actions of file manager
        Args:
            browse_format:      File extension to browse
            import_n_clicks:    Number of clicks on import button
            delete_n_clicks:    Number of clicks on delete button
            move_dir_n_clicks:  Move button
            uploaded_data:      Flag that indicates if new data has been uploaded
            update_data:        Flag that indicates if the dataset can be updated
            clear_data_n:       Number of clicks on clear data button
            dest:               Destination path
            rows:               Selected rows
            selected_paths:     Selected paths in cache
        Returns
            files:              Filenames to be displayed in File Manager according to browse_format 
                                from docker/local path
            selected_files:     List of selected filename FROM DOCKER PATH (no subdirectories)
        '''
        changed_id = dash.callback_context.triggered[0]['prop_id']
        if changed_id in 'import-dir.n_clicks' and not update_data:
            return dash.no_update, dash.no_update, dash.no_update
        elif changed_id == 'clear-data.n_clicks' and not update_data:
            return dash.no_update, dash.no_update, []
        elif changed_id == 'clear-data.n_clicks':
            return dash.no_update, [], dash.no_update
        data_project = DataProject(data=[])
        if tiled_on:
            data_type = 'tiled'
        else:
            data_type = 'local'
        browse_data = data_project.browse_data(data_type, browse_format, \
                                               tiled_uri = tiled_uri,
                                               dir_path=self.data_folder_root)
        if bool(rows) and changed_id != 'tiled-switch.on':
            for row in rows:
                selected_row = files_table[row]['uri']
                data_project.data += data_project.browse_data(data_type, import_format, \
                                                              tiled_uri = selected_row,
                                                              dir_path = selected_row)
        if changed_id == 'tiled-switch.on':
            selected_data = dash.no_update
        else:
            selected_data = data_project.get_dict()
        browse_data = DataProject(data=browse_data).get_table_dict()
        return browse_data, selected_data, dash.no_update
