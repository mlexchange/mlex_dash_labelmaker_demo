import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from app import app
from apps import welcome, thumbnail_tab#, training

url_bar_and_contents = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content'),
    thumbnail_tab.t_cache
    
])

app.layout = url_bar_and_contents

app.validation_layout = html.Div([
    url_bar_and_contents,
    welcome.layout,
    thumbnail_tab.layout,
    thumbnail_tab.t_cache,
    #training.layout
])
@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_age(pathname):
    print(pathname)
    if pathname == '/':
        return welcome.layout
    elif pathname == '/data':
        return thumbnail_tab.layout
    # elif pathname == '/training':
    #     return training.layout
    else:
        return '404'

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0')

