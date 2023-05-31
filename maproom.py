import flask
import dash
from dash import html
from dash.dependencies import Output, Input, State
import dash_bootstrap_components as dbc
import dash_leaflet as dlf
from pathlib import Path
from inspect import signature, Parameter
from collections import OrderedDict

from common import MaproomException, IDRegistry, CallbackRegistry, gensym, inverter, tile_url, tile_wrap
import controls
from controls import Controls, Plots
import uuid

class Maproom:
    def __init__(self, title, prefix, auto=False):
        self.title = title
        self.prefix = prefix
        self.auto = auto

        # private
        self._ids = IDRegistry()
        self._data_sets = dict()
        self._callbacks = CallbackRegistry()

        self.controls = Controls(self._ids, self._callbacks)
        self.plots = Plots(self._ids, self._callbacks)
        self._markers = []
        self._layers = []

    def marker(self, id, position):
        self._ids.add(id, "marker")
        self._markers.append([id, position])

    def layer(self, label, function, data):
        if not callable(function):
            raise MaproomException("Did not pass a function")

        params = list(signature(function).parameters.keys())
        if params[0] != "data":
            raise MaproomException("First argument of function must be `data`")

        params = params[1:]
        for p in params:
            self._ids.validate(p, {"marker", controls.Control.KIND})

        self._layers.append({
            'label': label,
            'id': str(uuid.uuid4()),
            'function': function,
            'params': params,
            'data': data,
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
                        ] + [
                            dlf.Overlay(
                                dlf.TileLayer(
                                    id=l['id'],
                                ),
                                name=l['label'],
                                checked=False,
                            )
                            for l in self._layers
                        ]),
                        dlf.LayerGroup([
                            dlf.Marker(id=m[0], position=m[1], draggable=True)
                            for m in self._markers
                        ]),
                    ], id="__map", center=[-29.6100, 28.2336],
                    style={'width': '100%', 'height': '500px',
                           'margin-bottom': '10px',
                    })),
                    dbc.Row(self.plots.render()),
                ], width=9),
            ])
        ], style={ 'height': '100vh' }, fluid=True)
        for c in self._callbacks.defs:
            APP.callback(
                output=Output(c['output'], c["prop"]),
                inputs={
                    p: Input(p, "position" if self._ids.kind(p) == "marker" else "value")
                    for p in signature(c['function']).parameters.keys()
                }
            )(c['function'] if c['prop'] != "hidden" else inverter(c['function']))

        # if len(self._markers) > 1:
        #     APP.callback(
        #         Output(self._markers[0][0], "position"),
        #         Input("__map", "click_lat_lng"),
        #     )(lambda x: self._markers[0][1] if x is None else x)

        for i, l in enumerate(self._layers):
            APP.callback(
                output=Output(l['id'], 'url'),
                inputs={
                    p: Input(p, "value")
                    for p in l['params']
                }
            )(tile_url(f"tile-{i}"))

            server.route(f"/tile-{i}/<int:tz>/<int:tx>/<int:ty>")(
                tile_wrap(l['data'], l['function'])
            )
        return APP


    def start(self):
        SERVER = flask.Flask(__name__)
        APP = self.render(SERVER)
        APP.run_server(
            threaded=False,
        )
