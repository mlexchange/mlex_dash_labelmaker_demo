from dash.dependencies import Input, Output, State

from app_layout import app
from callbacks.display_order import *
from callbacks.display import *
from callbacks.help import *
from callbacks.manage_labels import *
from callbacks.update_models import *
from callbacks.warning import *


app.clientside_callback(
    """
    function(n_clicks, tab_value, mlcoach_url, data_clinic_url) {
        if (tab_value == 'mlcoach') {
            window.open(mlcoach_url);
        } else if (tab_value == 'clinic') {
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
