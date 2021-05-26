import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from app import app
import templates
import numpy as np
import plotly.express as px
from mlex_api.mlex_api import job_dispatcher

header = templates.header()
FA = "https://use.fontawesome.com/releases/v5.8.1/css/all.css"
#app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP, FA])

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 60,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}# the styles for the main content position it to the right of the sidebar and
# add some padding.
CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

sidebar = html.Div(
    [
        html.H1(""),
        html.H4("Training"),
        html.Hr(),
        html.H6(
            "Model Options"
        ),
        dbc.FormGroup(
            [
                dbc.Label("ML Model"),
                dcc.Dropdown(
                    options=[
                        {'label' :'XCeption', 'value': 'xception'},
                        {'label' :'VGG16', 'value': 'vgg16'},
                        {'label' :'ResNet101', 'value': 'resnet101'},
                        {'label' :'ResNet152', 'value': 'resnet152'},
                        {'label' :'ResNet50V2', 'value': 'resnet50v2'},
                        {'label' :'ResNet50', 'value': 'resnet50'},
                        {'label' :'Resnet152', 'value': 'resnet152v2'},
                        {'label' :'InceptionV3', 'value': 'InceptionV3'},
                        {'label' :'DenseNet201', 'value': 'DenseNet201'},
                        {'label' :'NASNetLarge', 'value': 'NASNetLarge'},
                        {'label' :'InceptionResNetV2', 'value': 'InceptionResNetV2'},
                        {'label' :'DenseNet160', 'value': 'DenseNet160'},
                    ]
                )
            ]
        ),
        dbc.FormGroup(
            [
                dbc.Label('Batch Size'),
                dcc.Slider(min=1, max=64, step=2,value=4)
                
            ]
            
        ),
        dbc.FormGroup(
            [
                dbc.Label('Epochs'),
                dcc.Slider(min=1, max=400, step=50, value = 50),
            ]
        ),
        dbc.FormGroup(
            [
            dbc.Label('Save Model As...'),
            dbc.Input(type='text', id='model-save-name', placeholder = 'Enter Model Save Name')
            ]
        ),
        dbc.FormGroup(
            [
                dbc.Button('Train', outline=True)
            ]
        )
    ],
    style=SIDEBAR_STYLE
)
content_dashboard = html.Div(id = 'training-content', children=[
html.H1('Training Results'), 
    dcc.Graph(id='plot'),
    dcc.Interval(
        id='interval-component',
        interval=1*100,
        n_intervals=0
    )
],style = CONTENT_STYLE)

@app.callback(Output('plot', 'figure'),
              Input('interval-component', 'n_intervals'),
              )
def update_graph(n):
    try:
        data = np.loadtxt('./data/logs/output.csv')
        fig = px.line(data.T[1], labels={'x':'epoch', 'y':'loss'})
        
        print(data[1])
    except:

        fig = dash.no_update
    return fig 


layout = html.Div(
    [
        header,
        sidebar,
        content_dashboard,
    ]
)

if __name__ == "__main__":
    app.run_server(port=8050, debug=True, host = "0.0.0.0")
