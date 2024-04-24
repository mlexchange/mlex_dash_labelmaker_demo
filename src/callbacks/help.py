import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback


@callback(
    Output("modal-help", "is_open", allow_duplicate=True),
    Output("help-body", "children", allow_duplicate=True),
    Input("tab-help-button", "n_clicks"),
    State("modal-help", "is_open"),
    State("tab-group", "value"),
    prevent_initial_call=True,
)
def toggle_help_modal(tab_n_clicks, is_open, tab_value):
    """
    This callback toggles the modal with help instructions
    Args:
        tab_n_clicks:           Number of clicks in tab help button
        is_open:                Open/close status of help modal
        tab_value:              Current tab
    Returns:
        open_modal:             Open/close status of help modal
        modal_text:             Help modal text
    """
    if tab_value == "similarity":
        body_txt = [
            dbc.Label("1. Select a trained model to start.", className="mr-2"),
            dbc.Label(
                "2. Click on the image of interest. Then click Find Similar Images \
                                button below.",
                className="mr-2",
            ),
            dbc.Label(
                "3. The image display updates according to the trained model results. \
                                Label as usual.",
                className="mr-2",
            ),
            dbc.Label(
                "4. To exit this similarity based display, click Stop Find Similar \
                                Images.",
                className="mr-2",
            ),
        ]

    else:  # Probability
        body_txt = [
            dbc.Label("1. Select a trained model to start.", className="mr-2"),
            dbc.Label(
                "2. Select the label name to be assigned accross the dataset in \
                                the dropdown beneath Probability Threshold.",
                className="mr-2",
            ),
            dbc.Label(
                "3. Use the slider to setup the probability threshold.",
                className="mr-2",
            ),
            dbc.Label("4. Click Label with Threshold.", className="mr-2"),
        ]

    return not is_open, body_txt
