import dash
from dash import Input, Output, State, dcc

from labels import Labels
from file_manager.data_project import DataProject
from app_layout import app, USER, long_callback_manager
from callbacks.display_order import display_index
from callbacks.display import update_output, full_screen_thumbnail, deselect,\
    update_hide_button_text, display_indicator, toggle_tabs_collapse, update_page_number, update_rows
from callbacks.help import toggle_help_modal
from callbacks.manage_labels import toggle_color_picker_modal, label_selected_thumbnails,\
    load_from_splash_modal
from callbacks.update_models import update_trained_model_list
from callbacks.warning import toggle_modal_unlabel_warning


app.clientside_callback(
    """
    function(n_clicks, tab_value, mlcoach_url, data_clinic_url) {
        if (tab_value == 'probability') {
            window.open(mlcoach_url);
        } else if (tab_value == 'similarity') {
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


@app.long_callback(
    Output('download-out', 'data'),
    Output('storage-modal', 'is_open'),
    Output('storage-body-modal', 'children'),
    Output('modal-save-splash', 'is_open'),

    Input('button-save-disk', 'n_clicks'),
    Input('button-save-splash', 'n_clicks'),
    Input('confirm-save-splash', 'n_clicks'),
    Input('close-storage-modal', 'n_clicks'),

    State({'base_id': 'file-manager', 'name': 'docker-file-paths'},'data'),
    State({'base_id': 'file-manager', 'name': 'project-id'}, 'data'),
    State('labels-dict', 'data'),
    State('tagger-id', 'value'),
    manager=long_callback_manager,
    prevent_initial_call=True
)
def save_labels(button_save_disk_n_clicks, button_save_splash_n_clicks, button_confirm_splash_n_clicks, 
                close_modal_n_clicks, file_paths, project_id, labels_dict, tagger_id):
    '''
    This callback saves the labels to disk or to splash-ml
    Args:
        button_save_disk_n_clicks:      Button to save to disk
        button_save_splash_n_clicks:    Button to save to splash-ml
        button_confirm_splash_n_clicks: Button to confirm save to splash-ml
        close_modal_n_clicks:           Button to close the confirmation message
        file_paths:                     Data project information
        project_id:                     Project id associated with the current data project
        labels_dict:                    Dictionary of labeled images (docker path), as follows: 
                                        {filename1: [label1, label2], ...}
        tagger_id:                      ID to identify the user/tagger
    Returns:
        download_out:                   Download output
        storage_modal_open:             Open/closes the confirmation message
        storag_body_modal:              Confirmation message
        modal_save_splash:              Open/close save to splash modal to collect the tagger id
    '''
    changed_id = dash.callback_context.triggered[-1]['prop_id']
    if changed_id == 'close-storage-modal.n_clicks':
        return dash.no_update, False, dash.no_update, False
    labels = Labels(**labels_dict)
    if sum(labels.num_imgs_per_label.values())>0:
        if 'confirm-save-splash.n_clicks' in changed_id:
            status = labels.save_to_splash(tagger_id, file_paths, project_id)
            if len(status)==0:
                response = 'Labels stored in splash-ml'
            else:
                response = f'Error. {status}'
            return dash.no_update, True, response, False
        elif 'button-save-disk.n_clicks' in changed_id:
            data_project = DataProject()
            data_project.init_from_dict(file_paths)
            path_save = labels.save_to_directory(data_project)
            response = 'Download will start shortly'
            return dcc.send_file(f'{path_save}.zip', filename="files.zip"), True, response, False
        else:
            return dash.no_update, False, dash.no_update, True
    return dash.no_update, True, 'No labels to save', False


if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8057)