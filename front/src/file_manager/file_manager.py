import os
import shutil, pathlib, zipfile

import dash
from dash import html, dcc, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
import dash_daq as daq
import dash_uploader as du

from file_manager.file_path import FilePath, ListFilePaths


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
                    "Toggle File Manager",
                    id="collapse-button",
                    size="lg",
                    className="m-2",
                    color="secondary",
                    outline=True,
                    n_clicks=0,
                ),
                dbc.Button(
                    "Clear Images",
                    id="clear-data",
                    size="lg",
                    className="m-2",
                    color="secondary",
                    outline=True,
                    n_clicks=0,
                ),
                dbc.Collapse(
                    self.init_file_manager(),
                    id="collapse",
                    is_open=True,
                ),
            ]
        )
        pass

    def init_file_manager(self):
        file_manager = html.Div([
            dbc.Card([
                dbc.CardBody(id='data-body',
                            children=[
                                dbc.Label('1. Upload a new file or a zipped folder:', 
                                          className='mr-2'),
                                html.Div([
                                    du.Upload(id="dash-uploader",
                                              max_file_size=self.max_file_size,
                                              cancel_button=True,
                                              pause_button=True
                                              )],
                                    style={'textAlign': 'center',
                                            'width': '770px',
                                            'padding': '5px',
                                            'display': 'inline-block',
                                            'margin-bottom': '10px',
                                            'margin-right': '20px'},
                                ),
                                dbc.Label('2. Choose files/directories:', 
                                          className='mr-2'),
                                dbc.Row([
                                    dbc.Col(
                                        dbc.Row([
                                            dbc.Col(dbc.InputGroupText("Browse Format: ",
                                                                       style={'height': '2.5rem', 
                                                                              'width': '100%'}),
                                                    width=5),
                                            dbc.Col(dcc.Dropdown(
                                                        id='browse-format',
                                                        options=[
                                                            {'label': 'dir', 'value': 'dir'},
                                                            {'label': 'all (*)', 'value': '*'},
                                                            {'label': '.png', 'value': '*.png'},
                                                            {'label': '.jpg/jpeg', 'value': '*.jpg,*.jpeg'},
                                                            {'label': '.tif/tiff', 'value': '*.tif,*.tiff'},
                                                            {'label': '.txt', 'value': '*.txt'},
                                                            {'label': '.csv', 'value': '*.csv'},
                                                        ],
                                                        value='dir',
                                                        style={'height': '2.5rem', 'width': '100%'}),
                                                    width=7)
                                        ], className="g-0"),
                                        width=4,
                                    ),
                                    dbc.Col([
                                        dbc.Button("Delete the Selected",
                                                id="delete-files",
                                                className="ms-auto",
                                                color="danger",
                                                size='sm',
                                                outline=True,
                                                n_clicks=0,
                                                style={'width': '100%', 'height': '2.5rem'}
                                            ),
                                        dbc.Modal([
                                            dbc.ModalHeader(dbc.ModalTitle("Warning")),
                                            dbc.ModalBody("Files cannot be recovered after deletion. \
                                                          Do you still want to proceed?"),
                                            dbc.ModalFooter([
                                                dbc.Button(
                                                    "Delete", 
                                                    id="confirm-delete", 
                                                    color='danger', 
                                                    outline=False, 
                                                    className="ms-auto", 
                                                    n_clicks=0
                                                )])
                                            ],
                                            id="file-modal",
                                            is_open=False,
                                            style = {'color': 'red'}
                                        )
                                    ], width=2),
                                    dbc.Col(
                                        dbc.Row([
                                            dbc.Col(
                                                dbc.InputGroupText("Import Format: ",
                                                                    style={'height': '2.5rem', 
                                                                            'width': '100%'}),
                                                                            width=5),
                                            dbc.Col(dcc.Dropdown(
                                                    id='import-format',
                                                    options=[
                                                        {'label': 'all files (*)', 'value': '*'},
                                                        {'label': '.png', 'value': '*.png'},
                                                        {'label': '.jpg/jpeg', 'value': '*.jpg,*.jpeg'},
                                                        {'label': '.tif/tiff', 'value': '*.tif,*.tiff'},
                                                        {'label': '.txt', 'value': '*.txt'},
                                                        {'label': '.csv', 'value': '*.csv'},
                                                    ],
                                                    value='*',
                                                    style={'height': '2.5rem', 'width': '100%'}),
                                                    width=7)
                                        ], className="g-0"),
                                        width=4
                                    ),
                                    dbc.Col(
                                        dbc.Button("Import",
                                                id="import-dir",
                                                className="ms-auto",
                                                color="secondary",
                                                size='sm',
                                                outline=True,
                                                n_clicks=0,
                                                style={'width': '100%', 'height': '2.5rem'}
                                        ),
                                        width=2,
                                    ),
                                ]),   
                                dbc.Row([
                                    dbc.Col(
                                        dbc.Label('3. (Optional) Move a file or folder into a new directory:', 
                                                  className='mr-2'),
                                    ),
                                    dbc.Col(
                                        dbc.Button(
                                            "Open File Mover",
                                            id="file-mover-button",
                                            size="sm",
                                            className="mb-3",
                                            color="secondary",
                                            outline=True,
                                            n_clicks=0
                                        ),
                                    )
                                ]),     
                                dbc.Collapse(
                                    html.Div([
                                        dbc.Col([
                                            dbc.Label("Home data directory (Docker HOME) is '{}'.\
                                                        Dataset is by default uploaded to '{}'. \
                                                        You can move the selected files or directories \
                                                        (from File Table) into a new directory."\
                                                      .format(self.data_folder_root, 
                                                              self.upload_folder_root), 
                                                        className='mr-5'),
                                            html.Div([
                                                dbc.Label('Move data into directory:', className='mr-5'),
                                                dcc.Input(id='dest-dir-name', 
                                                            placeholder="Input relative path to Docker HOME", 
                                                            style={'width': '40%', 
                                                                   'margin-bottom': '10px'}),
                                                dbc.Button("Move",
                                                            id="move-dir",
                                                            className="ms-auto",
                                                            color="secondary",
                                                            size='sm',
                                                            outline=True,
                                                            n_clicks=0,
                                                            style={'width': '22%', 'margin': '5px'}),
                                            ],
                                            style = {'width': '100%', 
                                                    'display': 'flex', 
                                                    'align-items': 'center'},
                                            )
                                        ])
                                    ]),
                                    id="file-mover-collapse",
                                    is_open=False,
                                ),
                                html.Div([
                                        dbc.Label('4. (Optional) Load data through Tiled', 
                                                style = {'margin-right': '10px'}),
                                        dbc.InputGroup([
                                            dbc.InputGroupText("URI"), 
                                            dbc.Input(placeholder="tiled uri", id='tiled-uri')
                                        ]),
                                        daq.BooleanSwitch(
                                            id='tiled-switch',
                                            on=False,
                                            color="#9B51E0")
                                    ],
                                    style = {'width': '100%', 
                                            'display': 'flex', 
                                            'align-items': 'center', 
                                            'margin': '10px', 
                                            'margin-left': '0px'},
                                ),
                                # html.Div([ html.Div([dbc.Label('5. (Optional) Show Local/Docker Path')], 
                                #                     style = {'margin-right': '10px'}),
                                #             daq.ToggleSwitch(
                                #                 id='my-toggle-switch',
                                #                 value=False
                                #             )],
                                #     style = {'width': '100%', 
                                #             'display': 'flex', 
                                #             'align-items': 'center', 
                                #             'margin': '10px', 
                                #             'margin-left': '0px'},
                                # ),
                                html.Div(
                                    children=[
                                        dash_table.DataTable(
                                            id='files-table',
                                            columns=[
                                                {'name': 'Type', 'id': 'file_type'},
                                                {'name': 'File Table', 'id': 'file_path'},
                                                {'name': 'File Location', 'id': 'file_location'}
                                            ],
                                            data = [],
                                            hidden_columns = ['file_type', 'file_location'],
                                            row_selectable='single',
                                            style_cell={'padding': '0.5rem', 'textAlign': 'left'},
                                            fixed_rows={'headers': False},
                                            css=[{"selector": ".show-hide", "rule": "display: none"}],
                                            style_data_conditional=[
                                                {'if': {'filter_query': '{file_type} = dir'},
                                                    'color': 'blue'},
                                                ],
                                            style_table={'height':'18rem', 'overflowY': 'auto'}
                                            ),
                                        dcc.Store(id='confirm-update-data', data=True),
                                        dcc.Store(id='confirm-clear-data', data=False),
                                        dcc.Store(id='docker-file-paths', data=[]),
                                        dcc.Store(id='upload-data', data=False),
                                        ]
                                    )
                                ]),
            ],
            id="file-manager",
            )
        ])
        return file_manager
    
    def init_callbacks(self, app):
        app.callback(
            Output("collapse", "is_open"),
            [Input("collapse-button", "n_clicks"),
             Input('import-dir', 'n_clicks'),
             State("collapse", "is_open")]
        )(self._toggle_collapse)

        app.callback(
            Output("file-mover-collapse", "is_open"),
            [Input("file-mover-button", "n_clicks"),
             State("file-mover-collapse", "is_open")]
        )(self._file_mover_collapse)

        app.callback(
            Output("file-modal", "is_open"),
            [Input("delete-files", "n_clicks"),
             Input("confirm-delete", "n_clicks"),  
             State("file-modal", "is_open")]
        )(self._toggle_modal_delete_files)

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
             Input('confirm-delete','n_clicks'),
             Input('move-dir', 'n_clicks'),
             Input('upload-data', 'data'),
             Input('confirm-update-data', 'data'),
             Input('clear-data', 'n_clicks'),
             Input('tiled-switch', 'on'),
             State('dest-dir-name', 'value'),
             State('files-table', 'selected_rows'),
             State('docker-file-paths', 'data'),
             State('tiled-uri', 'value')]
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

    @staticmethod
    def _file_mover_collapse(n, is_open):
        '''
        Collapse the file moving options in file manager
        Args:
            n:          Number of clicks in file mover collapse button
            is_open:    Bool variable indicating if the file mover is collapsed or not
        '''
        if n:
            return not is_open
        return is_open
    
    @staticmethod
    def _toggle_modal_delete_files(n1, n2, is_open):
        '''
        
        '''
        if n1 or n2:
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
    
    def _load_dataset(self, browse_format, import_n_clicks, delete_n_clicks, move_dir_n_clicks, \
                      uploaded_data, update_data, clear_data_n, tiled_on, dest, rows, \
                      selected_paths, tiled_uri):
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
        
        files_class = ListFilePaths()
        if False: # tiled_on:
            files.paths_from_tiled(tiled_uri)
            ## reshape the table to hide the tiled_uri paths!!!!!! and display nodes only!!!
        else:
            
            files = files_class.paths_from_dir(self.data_folder_root, browse_format, sort=False)
            selected_files = []
            if bool(rows):
                for row in rows:
                    selected_files.append(files.filepaths[row].__dict__)
            if changed_id == 'confirm-delete.n_clicks':
                for filepath in selected_files:
                    if os.path.isdir(filepath['file_path']):
                        shutil.rmtree(filepath['file_path'])
                    else:
                        os.remove(filepath['file_path'])
                selected_files = []
                files.paths_from_dir(self.data_folder_root, browse_format, sort=False)
            elif changed_id == 'move-dir.n_clicks':
                if dest is None:
                    dest = ''
                destination = self.data_folder_root / dest
                destination.mkdir(parents=True, exist_ok=True)
                if bool(rows):
                    for source in ListFilePaths(selected_paths):
                        if os.path.isdir(source.file_path):
                            files.move_dir(source.file_path, str(destination))
                            shutil.rmtree(source.file_path)
                        else:
                            files.move_a_file(source['file_path'], str(destination))
                    selected_files = []
                    files.paths_from_dir(self.data_folder_root, browse_format, sort=False)
        files = files_class.docker_to_local_path(files, self.docker_home, self.local_home)
        return files, selected_files, dash.no_update
