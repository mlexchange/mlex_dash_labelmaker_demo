from dash.dependencies import Input, Output, State

from app_layout import app
from callbacks.display_order import display_index
from callbacks.display import update_output, full_screen_thumbnail, select_thumbnail, deselect,\
    update_hide_button_text, display_indicator, toggle_tabs_collapse
from callbacks.help import toggle_help_modal
from callbacks.manage_labels import toggle_color_picker_modal, label_selected_thumbnails,\
    save_labels, load_from_splash_modal
from callbacks.update_models import update_trained_model_list
from callbacks.warning import toggle_modal_unlabel_warning


app.clientside_callback(
    """
    function(n_clicks, tab_value, mlcoach_url, data_clinic_url) {
        if (tab_value == 'mlcoach') {
            window.open(mlcoach_url);
        } else if (tab_value == 'data_clinic') {
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


if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8057)
