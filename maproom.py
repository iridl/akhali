import flask
import dash
from dash import html
from dash.dependencies import Output, Input, State
import dash_bootstrap_components as dbc
import dash_leaflet as dlf
from pathlib import Path
from inspect import signature, Parameter
from collections import OrderedDict
from common import MaproomException, IDRegistry, gensym
from controls import Controls, Plots

def wrapper(f, prop):
    def wrapped(*args, **kwargs):
        result = f(*args, **kwargs)
        print(result)
        if not result:
            return {}
        else:
            return { 'display': None }
    if prop == "hidden":
        return wrapped
    else:
        return f

def wrapper2(f, prop):
    def wrapped(*args, **kwargs):
        result = f(*args, **kwargs)
        return not result
    if prop == "hidden":
        return wrapped
    else:
        return f

class Maproom:
    def __init__(self, title, prefix, auto=False):
        self.title = title
        self.prefix = prefix
        self.auto = auto

        # private
        self._ids = IDRegistry()
        self._data_sets = dict()
        self._callbacks = []

        self.controls = Controls(self._ids, self._callbacks)
        self.plots = Plots(self._ids, self._callbacks)
        self._layers = []

    # public methods
    def data(self, id, path):
        self._ids.add(id, "data")
        self._data_sets[id] = Path(path)

    def tab(self, id, label):
        self._add_id(id, "tab")
        self._tabs[id] = {
            'label': label,
            'content': []
        }

    def layer(self, label, data, inputs, function):
        self._validate_id(data, "data")

        for i in inputs:
            self._validate_id(i, "control")

        if not callable(function):
            raise InvalidComputeFunction

        sig = signature(function)
        # can be more precise than this
        if not(list(sig.parameters.keys()) == ['data', 'inputs']):
            raise InvalidComputeFunction

        self._layers.append({
            'label': label,
            'data': data,
            'inputs': inputs,
            'function': function,
        })


    # render/start
    def render(self, server):
        APP = dash.Dash(
            __name__,
            server=server,
            url_base_pathname=f"/{self.prefix}/",
            external_stylesheets=[
                dbc.themes.BOOTSTRAP,
            ],
        )
        APP.title = self.title
        APP.layout = dbc.Container([
            dbc.Row(html.H1(self.title)),
            dbc.Row([
                dbc.Col(self.controls.render(), width=3),
                dbc.Col([
                    dbc.Row(dlf.Map([
                        dlf.LayersControl([
                            dlf.BaseLayer(
                                dlf.TileLayer(
                                    opacity=0.6,
                                    url="https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png",
                                ),
                                name="Street",
                                checked=True,
                            ),
                            dlf.BaseLayer(
                                dlf.TileLayer(
                                    opacity=0.6,
                                    url="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png"
                                ),
                                name="Topo",
                                checked=False,
                            ),
                            dlf.Overlay(
                                dlf.TileLayer(
                                    id="map_raster",
                                ),
                                name="Raster",
                                checked=True,
                            ),
                        ]),
                    ], style={'width': '100%', 'height': '500px',
                              'margin-bottom': '10px',
                              })),
                    dbc.Row(self.plots.render()),
                ], width=9),
            ])
        ], style={ 'height': '100vh' }, fluid=True)
        print(self._callbacks)
        for c in self._callbacks:
            APP.callback(
                output=Output(c['output'], c["prop"]),
                inputs={
                    p: Input(p, "value")
                    for p in signature(c['function']).parameters.keys()
                }
            )(wrapper2(c['function'], c['prop']))
            # )(c['function'])
            # )(wrapper(c['function'], c['prop']))
        return APP


    def start(self):
        SERVER = flask.Flask(__name__)
        APP = self.render(SERVER)
        APP.run_server(
            threaded=False,
        )
