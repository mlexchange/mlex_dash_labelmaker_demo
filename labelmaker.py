import os

import dash
from dash import MATCH, ClientsideFunction, Input, Output, State, dcc
from file_manager.data_project import DataProject

from src.app_layout import app, long_callback_manager
from src.callbacks.display import (  # noqa: F401;
    deselect,
    display_indicator_off,
    display_indicator_on,
    full_screen_thumbnail,
    toggle_tabs_collapse,
    update_hide_button_text,
    update_output,
    update_probabilities,
    update_rows,
)
from src.callbacks.display_order import (  # noqa: F401
    disable_buttons,
    go_to_first_page,
    go_to_last_page,
    go_to_next_page,
    go_to_prev_page,
    go_to_users_input,
    undo_sort_or_hide_labeled_images,
    update_image_order,
)
from src.callbacks.help import toggle_help_modal  # noqa: F401
from src.callbacks.manage_labels import (  # noqa: F401
    label_selected_thumbnails,
    load_from_splash_modal,
    toggle_color_picker_modal,
)
from src.callbacks.update_models import update_trained_model_list  # noqa: F401
from src.callbacks.warning import toggle_modal_unlabel_warning  # noqa: F401
from src.labels import Labels

APP_PORT = os.getenv("APP_PORT", 8057)
APP_HOST = os.getenv("APP_HOST", "127.0.0.1")


app.clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="transform_image"),
    Output({"type": "thumbnail-src", "index": MATCH}, "src"),
    Input("log-transform", "on"),
    Input({"type": "processed-data-store", "index": MATCH}, "data"),
    prevent_initial_call=True,
)


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
    Output("dummy1", "data"),
    Input("goto-webpage", "n_clicks"),
    State("tab-group", "value"),
    State("mlcoach-url", "data"),
    State("data-clinic-url", "data"),
    prevent_initial_call=True,
)


@app.long_callback(
    Output("storage-modal", "is_open"),
    Output("storage-body-modal", "children"),
    Input("confirm-save-splash", "n_clicks"),
    State({"base_id": "file-manager", "name": "data-project-dict"}, "data"),
    State("labels-dict", "data"),
    State("tagger-id", "value"),
    manager=long_callback_manager,
    prevent_initial_call=True,
)
def save_labels_to_splash(
    button_confirm_splash_n_clicks,
    data_project_dict,
    labels_dict,
    tagger_id,
):
    """
    This callback saves the labels to disk or to splash-ml
    Args:
        button_confirm_splash_n_clicks: Button to confirm save to splash-ml
        data_project_dict:              Data project information
        labels_dict:                    Dictionary of labeled images (docker path), as follows:
                                        {filename1: [label1, label2], ...}
        tagger_id:                      ID to identify the user/tagger
    Returns:
        storage_modal_open:             Open/closes the confirmation message
        storage_body_modal:             Confirmation message
    """
    labels = Labels(**labels_dict)
    if sum(labels.num_imgs_per_label.values()) > 0:
        # Load data project
        data_project = DataProject.from_dict(data_project_dict)

        status = labels.save_to_splash(tagger_id, data_project)
        # Remove None elements
        status = list(filter(None, status))
        if len(status) == 0:
            response = "Labels stored in splash-ml"
        else:
            response = f"Error. {status}"
        return True, response

    return True, "No labels to save"


@app.long_callback(
    Output("download-out", "data"),
    Output("storage-modal", "is_open", allow_duplicate=True),
    Output("storage-body-modal", "children", allow_duplicate=True),
    Input("button-save-disk", "n_clicks"),
    State({"base_id": "file-manager", "name": "data-project-dict"}, "data"),
    State("labels-dict", "data"),
    manager=long_callback_manager,
    prevent_initial_call=True,
)
def save_labels_to_disk(
    button_save_disk_n_clicks,
    data_project_dict,
    labels_dict,
):
    """
    This callback saves the labels to disk or to splash-ml
    Args:
        button_save_disk_n_clicks:      Button to save to disk
        data_project_dict:              Data project information
        labels_dict:                    Dictionary of labeled images (docker path), as follows:
                                        {filename1: [label1, label2], ...}
    Returns:
        download_out:                   Download output
        storage_modal_open:             Open/closes the confirmation message
        storage_body_modal:             Confirmation message
    """
    labels = Labels(**labels_dict)
    if sum(labels.num_imgs_per_label.values()) > 0:
        # Load data project
        data_project = DataProject.from_dict(data_project_dict)

        path_save = labels.save_to_directory(data_project)
        response = "Download will start shortly"
        return (dcc.send_file(f"{path_save}.zip", filename="files.zip"), True, response)

    return dash.no_update, True, "No labels to save"


@app.callback(
    Output("storage-modal", "is_open", allow_duplicate=True),
    Input("close-storage-modal", "n_clicks"),
    prevent_initial_call=True,
)
def close_storage_modal(close_modal_n_clicks):
    """
    This callback closes the storage modal
    Args:
        close_modal_n_clicks: Button to close the confirmation message
    Returns:
        storage_modal_open:  Open/closes the confirmation message
    """
    return False


@app.callback(
    Output("modal-save-splash", "is_open", allow_duplicate=True),
    Input("button-save-splash", "n_clicks"),
    Input("confirm-save-splash", "n_clicks"),
    State("modal-save-splash", "is_open"),
    prevent_initial_call=True,
)
def toggle_splash_modal(
    button_save_splash_n_clicks,
    button_confirm_splash_n_clicks,
    storage_modal_open,
):
    """
    This callback toggles the splash modal
    Args:
        button_save_splash_n_clicks:    Button to save to splash-ml
        button_confirm_splash_n_clicks: Button to confirm save to splash-ml
    Returns:
        storage_modal_open:             Open/closes the confirmation message
    """
    return not storage_modal_open


if __name__ == "__main__":
    app.run_server(host=APP_HOST, port=APP_PORT, debug=True)
