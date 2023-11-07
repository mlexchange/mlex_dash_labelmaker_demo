import dash
from dash import Input, Output, State, callback, ALL

from query import Query


@callback(
    Output('image-order','data'),
    Output('find-similar-unsupervised', 'n_clicks'),
    Output('button-hide', 'n_clicks'),

    Input('exit-similar-unsupervised', 'n_clicks'),
    Input('find-similar-unsupervised', 'n_clicks'),
    Input('button-hide', 'n_clicks'),
    Input('button-sort', 'n_clicks'),
    Input('tab-group', 'value'),
    Input('labels-dict', 'data'),

    State({'type': 'thumbnail-name', 'index': ALL}, 'children'),
    State({'type': 'thumbnail-image', 'index': ALL}, 'n_clicks_timestamp'),
    State({'type': 'thumbnail-image', 'index': ALL}, 'n_clicks'),
    State('similarity-model-list', 'value'),
    State('image-order','data'),
    State('on-off-display', 'color'),
    State('button-hide', 'children'),
    prevent_initial_call=True)
def display_index(exit_similar_images, find_similar_images, button_hide_n_clicks, button_sort_n_clicks,
                  tab_selection, labels_dict, thumbnail_children, timestamp, thumb_n_clicks,
                  similarity_model, image_order, on_off_display, button_hide_text):
    '''
    This callback arranges the image order according to the following actions:
        - New content is uploaded
        - Buttons sort or hidden are selected
        - Find similar images display has been activated or deactivated
    Args:
        exit_similar_images:        Button "Exit Find Similar Images" has been clicked
        find_similar_images:        Button "Find Similar Images" has been clicked
        button_hide_n_clicks:       Hide button
        button_sort_n_clicks:       Sort button
        tab_selection:              Current tab [Manual, Similarity, Probability]
        labels_dict:                Dictionary with labeling information, e.g. 
                                    {filename1: [label1,label2], ...}
        thumbnail_children:         URIs of images in current page
        timestamp:                  Timestamps of selected images in current page - to find similar 
                                    images. Currently, one 1 image is selected for this operation
        thumb_n_clicks:             Number of clicks per card/filename in current page
        similarity_model:           Selected similarity-based model
        image_order:                Order of the images according to the selected action 
                                    (sort, hide, new data, etc)
        on_off_display:             Color display of ON(green)/OFF similarity-based search
        button_hide_text:           Text within "hide" button
    Returns:
        image_order:                Order of the images according to the selected action 
                                    (sort, hide, new data, etc)
        similar_img_clicks:         Reset number of clicks in similarity trigger button
        button_hide:                Reset number of clicks in hide button
    '''
    changed_id = dash.callback_context.triggered[0]['prop_id']
    query = Query(**labels_dict)
    similar_img_clicks = dash.no_update
    button_hide = dash.no_update
    num_imgs = len(query.labels_dict)
    if 'labels-dict.data' in changed_id and on_off_display != 'green' and \
        button_hide_text != 'Unhide':                       # Checks if new data has been uploaded
        if len(image_order) == num_imgs:
            return dash.no_update, dash.no_update, dash.no_update
        image_order = list(range(num_imgs))
    elif 'find-similar-unsupervised.n_clicks' in changed_id:
        for indx, n_click in enumerate(thumb_n_clicks):
            if n_click%2 == 0 or timestamp[indx] is None:
                timestamp[indx] = 0
        clicked_ind = timestamp.index(max(timestamp))       # retrieve clicked index
        if clicked_ind is not None and similarity_model:
            if similarity_model:
                image_order = query.similarity_search(similarity_model, 
                                                      thumbnail_children[int(clicked_ind)])
        else:                                      # if no image is selected, no update is triggered
            return dash.no_update, 0, dash.no_update
    elif changed_id == 'button-hide.n_clicks':
        similar_img_clicks = 0
        if button_hide_n_clicks % 2 == 1:
            image_order = query.hide_labeled()
        else:
            image_order = list(range(num_imgs))
    elif changed_id == 'exit-similar-unsupervised.n_clicks' or tab_selection=='probability':
        button_hide = 0
        similar_img_clicks = 0
        image_order = list(range(num_imgs))
    elif changed_id == 'button-sort.n_clicks':
        button_hide = 0
        similar_img_clicks = 0
        image_order = query.sort_labels()
    else:
        image_order = dash.no_update
    return image_order, similar_img_clicks, button_hide