from base64 import b64decode
from datetime import datetime
import functools
import json
from urllib.parse import quote

import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import dash_table_experiments as dt
from flask import Flask

from .simulation import run_simulation


default_params = (
{
    "R0": 8.3e3,
    "start_time": 2000,
    "end_time": 2030,
    "time_steps": 300,
    "bodies": [
    {
        "hash": "Sgr A*",
        "m": 4.2e6,
        "x": 0,
        "y": 0,
        "z": 0,
        "vx": 0,
        "vy": 0,
        "vz": 0
    },
    {
        "hash": "S2",
        "m": 0,
        "a": 0.126,
        "e": 0.884,
        "inc": 2.34,
        "Omega": 3.96,
        "omega": 1.15,
        "T": 2002.33,
        "primary": "Sgr A*"
    }]
})

empty_csv = "data:text/csv;charset=utf-8,"

# App Setup

flask_app = Flask(__name__)
dash_app = dash.Dash(__name__, server=flask_app)

dash_app.css.append_css(
{
    "external_url": "https://stackpath.bootstrapcdn.com/bootstrap/4.1.1/css/bootstrap.min.css"
})

# App Layout

dash_app.layout = html.Div(
    className="container",
    children=(
    [
        html.Div(
            children=(
            [
                dcc.Upload(
                    id="upload-data",
                    className="jumbotron",
                    children=(
                        html.Div(
                            className="text-center",
                            children=(
                                html.Button("Upload Parameter File",
                                    className="btn btn-outline-dark btn-lg")
                            )
                        )
                    ),
                    multiple=False
                ),
                html.Div(id="confirm-upload", className="text-center"),
                html.Div(id="confirm-simulation", className="text-center")
            ])
        ),

        html.Hr(),

        html.Div(
            className="row",
            children=(
            [
                html.Div(
                    className="col-lg-6",
                    children=(
                        dcc.Graph(id="2d-graph")
                    )
                ),
                html.Div(
                    className="col-lg-6",
                    children=(
                        dcc.Graph(id="3d-graph")
                    )
                )
            ])
        ),
        
        html.Hr(),

        html.Div(
            className="row",
            children=(
                html.Div(
                    className="col-lg-12",
                    children=(
                    [
                        dcc.Graph(id="1d-graph"),
        
                        html.Div(
                            className="text-center",
                            children=(
                                dcc.RadioItems(
                                    className="btn-group btn-group-toggle",
                                    labelClassName="btn btn-secondary",                    
                                    id="1d-graph-picker",
                                    options=(
                                    [
                                        {"label": "x", "value": "x"},
                                        {"label": "y", "value": "y"},
                                        {"label": "z", "value": "z"},
                                        {"label": "vx", "value": "vx"},
                                        {"label": "vy", "value": "vy"},
                                        {"label": "vz", "value": "vz"},
                                        {"label": "vzD", "value": "vzD"}
                                    ]),
                                    value="vz",
                                )
                            )
                        )
                    ])
                )
            )
        ),

        html.Hr(),

        html.Div(
            className="row",
            children=(
                html.Div(
                    className="col-lg-12",
                    children=(
                    [
                        dcc.Graph(id="parameter-graph"),
        
                        html.Div(
                            className="text-center",
                            children=(
                                dcc.RadioItems(
                                    className="btn-group btn-group-toggle",
                                    labelClassName="btn btn-secondary",                    
                                    id="parameter-graph-picker",
                                    options=(
                                    [
                                        {"label": "a", "value": "a"},
                                        {"label": "e", "value": "e"},
                                        {"label": "inc", "value": "inc"},
                                        {"label": "Omega", "value": "Omega"},
                                        {"label": "omega", "value": "omega"},
                                        #{"label": "T", "value": "T"},
                                        {"label": "P", "value": "P"}
                                    ]),
                                    value="a",
                                )
                            )
                        )
                    ])
                )
            )
        ),

        html.Hr(),

        html.Div(
            className="row",
            children=(
                html.Div(
                    className="col-lg-12",
                    children=(
                    [            
                        dcc.Dropdown(id="table-selector", options=[]),
                        html.Div(id="data-table", className="pt-3 pb-3"),
                        html.Div(
                            className="text-center pb-5",
                            children=(
                                html.A(
                                    "Download Table",
                                    id="download-link",
                                    className="btn btn-secondary",
                                    download="data.csv",
                                    href=empty_csv
                                )
                            )
                        )
                    ])
                )
            )
        ),

        html.Div(id="params-cache", style={"display": "none"}),
        html.Div(id="update-signal", style={"display": "none"}),
        html.Div(dt.DataTable(rows=[{}]), style={"display": "none"})
    ])
)

## Data Upload

@dash_app.callback(Output("params-cache", "children"),
                  [Input("upload-data", "contents"),
                   Input("upload-data", "filename"),
                   Input("upload-data", "last_modified")])
def upload_data(contents, filename, date):
    if contents is not None:
        content_type, content_string = contents.split(",")
        content_string = b64decode(content_string)
        try:
            params = json.loads(content_string.decode("utf-8"))
            params["error"] = 0
            params["message"] = f"Sucessfully loaded {filename}!"
        except:
            params = {}
            params["error"] = 1
            params["message"] = f"An error occured while loading {filename}!"
        return json.dumps(params)
    else:
        params = default_params
        params["error"] = 0
        params["message"] = ""
        return json.dumps(params)

@dash_app.callback(Output("confirm-upload", "children"),
                  [Input("params-cache", "children")])
def confirm_upload(json_data):
    params = json.loads(json_data)
    return html.P(params["message"])

# Simulation

@functools.lru_cache(maxsize=32)
def global_store(json_data):
    params = json.loads(json_data)
    if not params["error"]:      
        return run_simulation(params)

@dash_app.callback(Output("update-signal", "children"),
                  [Input("params-cache", "children")])
def compute_value(json_data):
    global_store(json_data)
    return json_data

@dash_app.callback(Output("confirm-simulation", "children"),
                   [Input("update-signal", "children")])
def confirm_simulation(json_data):
    params = json.loads(json_data)
    if not params["error"]:
        simulation = global_store(json_data)
        return html.P(simulation["message"])
    return html.P("")

# Graphs

@dash_app.callback(Output("2d-graph", "figure"),
                  [Input("update-signal", "children")])
def update_2d_graph(json_data):
    figure = (
    {
        "data": []
    })
    params = json.loads(json_data)
    if not params["error"]:  
        simulation = global_store(json_data)
        if not simulation["error"]:
            figure["data"] = (
            [
                {
                    "x": df["x"],
                    "y": df["y"],
                    "name": name,
                    "type": "scatter",
                    "mode": "lines+markers",
                    "marker": {"size": 5}
                }
                for name, df in simulation["data"].items()
            ])
            figure["layout"] = (
            {
                "xaxis":
                {
                    "title": "x"
                },
                "yaxis":
                {
                    "title": "y",
                    "scaleanchor": "x",
                    "scaleratio": 1
                }
            })
    return figure

@dash_app.callback(Output("3d-graph", "figure"),
                  [Input("update-signal", "children")])
def update_3d_graph(json_data):
    figure = (
    {
        "data": []
    })
    params = json.loads(json_data)
    if not params["error"]: 
        simulation = global_store(json_data)
        if not simulation["error"]:
            figure["data"] = (
            [
                {
                    "x": df["x"],
                    "y": df["y"],
                    "z": df["z"],
                    "name": name,
                    "type": "scatter3d",
                    "mode": "lines+markers",
                    "marker": {"size": 5}
                }
                for name, df in simulation["data"].items()
            ])
            figure["layout"] = (
            {
                "scene": {"aspectmode": "data"}
            })
    return figure    

def update_1d_graph(key):
    def func_wrapper(func):
        def create_figure(json_data, picker_value):
            figure = (
            {
                "data": []
            })
            params = json.loads(json_data)
            if not params["error"]: 
                simulation = global_store(json_data)
                if not simulation["error"]:
                    figure["data"] = (
                    [
                        {
                            "x": df["t"],
                            "y": df[picker_value],
                            "name": name,
                            "type": "scatter",
                            "mode": "lines+markers",
                            "marker": {"size": 5}
                        }
                        for name, df in simulation[key].items()
                    ])
                    figure["layout"] = (
                    {
                        "xaxis":
                        {
                            "title": "t"
                        },
                        "yaxis": 
                        {
                            "title": picker_value
                        }
                    })
            return figure
        return create_figure
    return func_wrapper   

@dash_app.callback(Output("1d-graph", "figure"),
                  [Input("update-signal", "children"),
                   Input("1d-graph-picker", "value")])
@update_1d_graph("data")
def update_orbit_graph():
    pass

@dash_app.callback(Output("parameter-graph", "figure"),
                  [Input("update-signal", "children"),
                   Input("parameter-graph-picker", "value")])
@update_1d_graph("orbits")
def update_parameter_graph():
    pass

# Table

@dash_app.callback(Output("table-selector", "value"),
                  [Input("params-cache", "children")])
def reset_table_selector(json_data):
    return None

@dash_app.callback(Output("table-selector", "options"),
             [Input("update-signal", "children")])
def update_table_selector(json_data):
    params = json.loads(json_data)
    if not params["error"]:
        simulation = global_store(json_data)
        if not simulation["error"]:
            return (
            [
                {
                    "label": name,
                    "value": name
                }
                for name in simulation["data"].keys()
            ])
    return []

@dash_app.callback(Output("data-table", "children"),
                  [Input("table-selector", "value"),
                   Input("update-signal", "children")])
def update_table(name, json_data):
    if name is not None:
        params = json.loads(json_data)
        if not params["error"]:        
            simulation = global_store(json_data)
            if not simulation["error"]:
                df = simulation["data"][name]
                return dt.DataTable(rows=df.to_dict("records"))
    return []

@dash_app.callback(Output("download-link", "href"),
                  [Input("table-selector", "value"),
                   Input("update-signal", "children")])
def update_download_link(name, json_data):
    if name is not None:
        params = json.loads(json_data)
        if not params["error"]:   
            simulation = global_store(json_data)
            if not simulation["error"]:
                df = simulation["data"][name]
                csv = df.to_csv(index=False, encoding="utf-8")
                csv = f"data:text/csv;charset=utf-8,{quote(csv)}"
                return csv
    return empty_csv
