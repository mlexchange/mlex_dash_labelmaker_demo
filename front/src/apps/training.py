import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from app import app
import pandas as pd
#from app import work_queue
import templates
import numpy as np
import plotly.express as px
from mlex_api.mlex_api import job_dispatcher
from mlex_api.mlex_api.job_dispatcher import workQueue
import os
import pathlib

# GLOBAL PARAMS
AMQP_URL = os.environ['AMQP_URL']
ROOT_DIR = pathlib.Path('/data/labelmaker_temp')
EXP_DIR = ROOT_DIR/'exp/'
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
                        {'label' :'XCeption', 'value': 'Xception'},
                        {'label' :'VGG16', 'value': 'VGG16'},
                        {'label' :'ResNet101', 'value': 'ResNet101'},
                        {'label' :'ResNet152', 'value': 'ResNet152'},
                        {'label' :'ResNet50V2', 'value': 'ResNet50v2'},
                        {'label' :'ResNet50', 'value': 'ResNet50'},
                        {'label' :'Resnet152', 'value': 'ResNet152v2'},
                        {'label' :'InceptionV3', 'value': 'InceptionV3'},
                        {'label' :'DenseNet201', 'value': 'DenseNet201'},
                        {'label' :'NASNetLarge', 'value': 'NASNetLarge'},
                        {'label' :'InceptionResNetV2', 'value': 'InceptionResNetV2'},
                        {'label' :'DenseNet160', 'value': 'DenseNet160'},
                    ],
                    id='dropdown-model-name',
                )
            ]
        ),
        dbc.FormGroup(
            [
                dbc.Label('Batch Size'),
                dcc.Slider(min=1, max=64, step=2,value=4,
                           id='slider-batch-size')
                
            ]
            
        ),
        dbc.FormGroup(
            [
                dbc.Label('Epochs'),
                dcc.Slider(min=1, max=400, step=50, value = 50,
                           id='slider-epochs'),
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
                dbc.Button(id='button-train', children='Train', outline=True)
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
        data = pd.read_csv('./data/labelmaker_temp/exp/output/logs/output.csv', sep='\s+',names=['accuracy', 'loss'] )
        fig = px.line(data, labels={'index':'epoch'})
        
       # print(data[1])
    except:

        fig = dash.no_update
    return fig 

@app.callback(Output('dummy', 'children'),
              Input('button-train', 'n_clicks'),
              State('dropdown-model-name', 'value'),
              State('slider-batch-size', 'value'),
              State('slider-epochs','value'),
              State('model-save-name','value'),
              prevent_initial_call=True,
              )
def react_train(
    button_train_n_clicks,
    dropdown_model_name_value,
    slider_batch_size_value,
    slider_epochs_value,
    model_save_name_value,
):
    # TODO need to add json schema for args
    # the Train.py script uses the following order for args
    # python Train.py train_dir test_dir valid_dir output_dir model_name pooling batch_size epochs stepochs
    input_dir = ROOT_DIR
    output_dir = EXP_DIR
    args = '{} {} {} {} {} {} {}'.format(
        input_dir,
        output_dir,
        dropdown_model_name_value,
        'None',
        slider_batch_size_value,
        slider_epochs_value,
        10
    )
    description = 'launch tensorflow ml job'
    # TODO add long lasting work_queue
    # current implementation is not what pika recommends
    # added because we don't have robust connection handling -- if the
    # connection is dropped, it will not reform connection. This way, more
    # robust, but slower
    work_queue = workQueue(AMQP_URL)
    simple_job = job_dispatcher.simpleJob(
        job_description=description,
        job_type='training',
        deploy_location='local',
        docker_uri='aasgreen/mlexchange_tensorflow_models',
        docker_cmd='python Train.py',
        kw_args=args,
        work_queue=work_queue,
        GPU=True,
    )
    print(simple_job.js_payload)
    simple_job.launch_job()
    work_queue.close()
    return []

layout = html.Div(
    [
        header,
        sidebar,
        content_dashboard,
        html.Div(id='dummy',children=[] )
    ]
)

if __name__ == "__main__":
    app.run_server(port=8050, debug=True, host = "0.0.0.0")
