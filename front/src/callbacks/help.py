import dash
from dash import Input, Output, State, callback
import dash_bootstrap_components as dbc


@callback(
    Output("modal-help", "is_open"),
    Output("help-body", "children"),

    Input("button-help", "n_clicks"),
    Input("tab-help-button", "n_clicks"),

    State("modal-help", "is_open"),
    State("tab-group", "value"),
    prevent_initial_call=True
)
def toggle_help_modal(main_n_clicks, tab_n_clicks, is_open, tab_value):
    '''
    This callback toggles the modal with help instructions
    Args:
        main_n_clicks:          Number of clicks in main help button at the header
        tab_n_clicks:           Number of clicks in tab help button
        is_open:                Open/close status of help modal
        tab_value:              Current tab
    Returns:
        open_modal:             Open/close status of help modal
        modal_text:             Help modal text
    '''
    changed_id = dash.callback_context.triggered[0]['prop_id']
    # Main instructions
    if 'button-help.n_clicks' in changed_id:
        body_txt = [dbc.Label('1. Please use the File Manager on the left to import/load the dataset \
                               of interest.'),
                    dbc.Label('2. Click the DataClinic tab. Use the "Go to" button to open DataClinic \
                              and train unsupervised learning algorithms to estimate image similarity. \
                              Then, come back to the DataClinic tab in Label Maker to load the results \
                              and label batches of similar images.'),
                    dbc.Label('3. Click the Manual tab to manually label images or make corrections \
                              to the previous step. Save the current labels by clicking the button \
                              Save Labels to Disk.'),
                    dbc.Label('4. Click the MLCoach tab. Use the "Go to" button to open MLCoach and \
                              do supervised learning for image classification using the previously \
                              saved labels. Then, come back to the MLCoach tab in Label Maker to load \
                              the results and label the full dataset using their estimated probabilities. \
                              Click the Manual tab to manually label images or make corrections to \
                              the previous step.'),
                    dbc.Label('5. Finally, save all the labels by clicking the button Save Labels to \
                              Disk.')]
    # Tab instructions
    else:
        if tab_value == 'data_clinic':
            body_txt = [dbc.Label('1. Select a trained model to start.', 
                                  className='mr-2'),
                        dbc.Label('2. Click on the image of interest. Then click Find Similar Images \
                                  button below.', 
                                  className='mr-2'),
                        dbc.Label('3. The image display updates according to the trained model results. \
                                  Label as usual.', 
                                  className='mr-2'),
                        dbc.Label('4. To exit this similarity based display, click Stop Find Similar \
                                  Images.', 
                                  className='mr-2')]
        
        else:           # mlcoach
            body_txt = [dbc.Label('1. Select a trained model to start.', 
                                  className='mr-2'),
                        dbc.Label('2. Select the label name to be assigned accross the dataset in \
                                  the dropdown beneath Probability Threshold.', 
                                  className='mr-2'),
                        dbc.Label('3. Use the slider to setup the probability threshold.', 
                                  className='mr-2'),
                        dbc.Label('4. Click Label with Threshold.', 
                                  className='mr-2')]

    return not is_open, body_txt