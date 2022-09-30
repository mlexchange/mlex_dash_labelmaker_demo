from dash import html
import dash_bootstrap_components as dbc


button_github = dbc.Button(
    "View Code on github",
    outline=True,
    color="primary",
    href="https://github.com/mlexchange/mlex_dash_labelmaker_demo",
    id="gh-link",
    style={"text-transform": "none"},
)


button_help = dbc.Button(
    "Help",
    outline=True,
    color="primary",
    id="button-help",
    style={"text-transform": "none"},
)


help_popup = dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Help")),
                    dbc.ModalBody(id='help-body')
                ], 
                id="modal-help",
                is_open=False,
                size="xl"
             )


def header():
    header= dbc.Navbar(
        dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.Img(
                                id="logo",
                                src='assets/mlex.png',
                                height="50px",
                            ),
                            md="auto",
                        ),
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.H3("MLExchange | Label Maker"),
                                        html.P("Scattering Data"),
                                    ],
                                    id="app-title",
                                )
                            ],
                            md=True,
                            align="center",
                        ),
                    ],
                    align="center",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.NavbarToggler(id="navbar-toggler"),
                                dbc.Collapse(
                                    dbc.Nav(
                                        [
                                            dbc.NavItem(button_help),
                                            dbc.NavItem(button_github),
                                            className="me-auto"
                                        ],
                                        navbar=True,
                                    ),
                                    id="navbar-collapse",
                                    navbar=True,
                                ),
                            ],
                            md=2,
                        ),
                    ],
                    align="center",
                ),
                help_popup  
            ],
            fluid=True,
        ),
        dark=True,
        color="dark",
        sticky="top",
    )
    return header
