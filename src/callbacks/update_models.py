import dash
from dash import Input, Output, callback

from src.app_layout import DATA_DIR, USER
from src.utils.model_utils import get_trained_models_list


@callback(
    Output("probability-model-list", "options"),
    Output("similarity-model-list", "options"),
    Input("tab-group", "value"),
    Input("probability-model-refresh", "n_clicks"),
    Input("similarity-model-refresh", "n_clicks"),
    prevent_initial_call=True,
)
def update_trained_model_list(
    tab_value, prob_refresh_n_clicks, similarity_refresh_n_clicks
):
    """
    This callback updates the list of trained models
    Args:
        tab_value:                      Tab option
        prob_refresh_n_clicks:          Button to refresh the list of probability-based trained models
        similarity_refresh_n_clicks:    Button to refresh the list of similarity-based trained models
    Returns:
        prob_model_list:                List of trained models in mlcoach
        similarity_model_list:          List of trained models in data clinic and mlcoach
    """
    if tab_value == "probability":
        prob_models = get_trained_models_list(
            USER, "mlcoach", False, DATA_DIR != "/app/work/data"
        )
        similarity_models = dash.no_update
    elif tab_value == "similarity":
        prob_models = dash.no_update
        data_clinic_models = get_trained_models_list(
            USER, "data_clinic", True, DATA_DIR != "/app/work/data"
        )
        ml_coach_models = get_trained_models_list(
            USER, "mlcoach", True, DATA_DIR != "/app/work/data"
        )
        similarity_models = data_clinic_models + ml_coach_models
    else:
        return dash.no_update, dash.no_update
    return prob_models, similarity_models
