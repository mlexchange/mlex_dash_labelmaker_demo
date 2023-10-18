import dash
from dash import Input, Output, callback

from utils.model_utils import get_trained_models_list
from app_layout import USER


@callback(
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
    elif tab_value == 'data_clinic':
        mlcoach_models = dash.no_update
        data_clinic_models = get_trained_models_list(USER, tab_value)
    else:
        return dash.no_update, dash.no_update
    return mlcoach_models, data_clinic_models