import dash
from dash import Input, Output, State, callback
import numpy as np
from labels import Labels


@callback(
    Output("modal-un-label", "is_open"),
    Output({'base_id': 'file-manager', 'name': "confirm-update-data"}, "data"),

    Input("un-label-all", "n_clicks"),
    Input("confirm-un-label-all", "n_clicks"),
    Input({'base_id': 'file-manager', 'name': "import-dir"}, "n_clicks"),
    Input({'base_id': 'file-manager', 'name': "clear-data"}, "n_clicks"),
    Input({'base_id': 'file-manager', 'name': "refresh-data"}, "n_clicks"),

    State("labels-dict", "data"),
    prevent_initial_call=True
)
def toggle_modal_unlabel_warning(unlabel_all_clicks, confirm_unlabel_all_clicks, n_import, n_clear,
                                 n_refresh, labels_dict):
    '''
    This callback toggles a modal with unlabeling warnings
    Args:
        unlabel_all_clicks:         Number of clicks of unlabel all button
        confirm_unlabel_all_clicks: Number of clicks of confirm unlabel all button
        n_import:                   Number of clicks of import button
        n_clear:                    Number of clicks of clear data button
        n_refresh:                  Number of clicks of refresh data button
        labels_dict:                Dictionary with labeling information, e.g. 
                                    {filename1: [label1,label2], ...}
    Returns:
        modal_is_open:              [Bool] modal unlabel warning is open
        update_data:                Flag indicating that new data can be imported from file manager
    '''
    changed_id = dash.callback_context.triggered[0]['prop_id']
    modal_is_open = False
    update_data = True
    labels = Labels(**labels_dict)
    if changed_id != 'confirm-un-label-all.n_clicks' and \
        np.sum(np.array(list(labels.num_imgs_per_label.values())))>0:      # if there are labels
        if changed_id == 'un-label-all.n_clicks':
            update_data = dash.no_update
        else:
            update_data = False
        modal_is_open = True
    return modal_is_open, update_data