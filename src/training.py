import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

FA = "https://use.fontawesome.com/releases/v5.8.1/css/all.css"
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP, FA])

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
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
        html.H2("Train New Model", className="display-4"),
        html.Hr(),
        html.H6(
            "Training Options"
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
content = html.Div(id = 'page-content', children=html.H1('Training Results'), style = CONTENT_STYLE)

app.layout = html.Div(
    [
        sidebar, content
    ]
)

if __name__ == "__main__":
    app.run_server(port=8050, debug=True, host = "0.0.0.0")
