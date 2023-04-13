import flask
import dash
from dash import html
from dash.dependencies import Output, Input, State
import dash_bootstrap_components as dbc
import dash_leaflet as dlf
from pathlib import Path
from inspect import signature, Parameter
from collections import OrderedDict
import uuid

class IdAlreadyInUse(Exception):
    pass

class UndefinedId(Exception):
    pass

class WrongKind(Exception):
    pass

class DataNotDefined(Exception):
    pass

class ControlNotDefined(Exception):
    pass

class InvalidControlElement(Exception):
    pass

class InvalidComputeFunction(Exception):
    pass

class InvalidDefault(Exception):
    pass

class MaproomException(Exception):
    pass



class Maproom:
    def __init__(self, title, prefix):
        self.title = title
        self.prefix = prefix

        # private
        self._ids_in_use = dict()
        self._data_sets = dict()
        self._tabs = OrderedDict()
        self._blocks = OrderedDict()
        self._layers = []

    # private methods
    def _add_id(self, id, kind):
        if id in self._ids_in_use.keys():
            raise IdAlreadyInUse(id)
        else:
            self._ids_in_use[id] = kind

    def _validate_id(self, id, kind):
        if id not in self._ids_in_use.keys():
            raise UndefinedId(id, kind)
        elif self._ids_in_use[id] != kind:
            raise WrongKind(id, self._ids_in_use[id], kind)
        else:
            pass

    def _add_component(self, ctrl, block, label):
        if block is not None and label is not None:
            raise MaproomException("control must be added to a block or labeled")
        elif block is not None and label is None:
            self._validate_id(block, "block")
            self._blocks[block]['content'].append(ctrl)
        elif block is None and label is not None:
            self._blocks[str(uuid.uuid4())] = {
                'label': label,
                'content': [ ctrl ],
            }
        else:
            raise MaproomException("no label or block specified")


    # public methods
    def data(self, id, path):
        self._add_id(id, "data")
        self._data_sets[id] = Path(path)

    def tab(self, id, label):
        self._add_id(id, "tab")
        self._tabs[id] = {
            'label': label,
            'content': []
        }

    def block(self, id, label):
        self._add_id(id, "block")
        self._blocks[id] = {
            'label': label,
            'content': []
        }

    class _Control:
        def __init__(self, maproom, id, block, label):
            self.maproom = maproom
            self.id = id
            self.maproom._add_id(id, "control")
            self.maproom._add_component(self, block, label)


    class _Month(_Control):
        FULL = [ 'january', 'february', 'march', 'april', 'may',
                 'june', 'july', 'august', 'september', 'october',
                 'november', 'december' ]
        ABBR = [ 'jan', 'feb', 'mar', 'apr', 'may', 'jun',
                 'jul', 'aug', 'sep', 'oct', 'nov', 'dec' ]

        def __init__(self, maproom, id, default, block, label):
            self.default = default.lower()
            if self.default in Maproom._Month.FULL:
                self.default = default_mon[0:3]
            elif self.default in Maproom._Month.ABBR:
                pass
            else:
                raise InvalidDefault(default)

            super().__init__(maproom, id, block, label)

        def render(self):
            return dbc.Select(
                id=self.id, value=self.default, size="sm",
                className="m-1 d-inline-block w-auto", options=[
                    {"label": "January", "value": "jan"},
                    {"label": "February", "value": "feb"},
                    {"label": "March", "value": "mar"},
                    {"label": "April", "value": "apr"},
                    {"label": "May", "value": "may"},
                    {"label": "June", "value": "jun"},
                    {"label": "July", "value": "jul"},
                    {"label": "August", "value": "aug"},
                    {"label": "September", "value": "sep"},
                    {"label": "October", "value": "oct"},
                    {"label": "November", "value": "nov"},
                    {"label": "December", "value": "dec"},
                ])

    class _Select(_Control):
        def __init__(self, maproom, id, options, default, block, label):
            self.options = options
            if default is None:
                self.default= options[0]
            elif default not in options:
                raise InvalidDefault(default)
            else:
                self.default = default

            super().__init__(maproom, id, block, label)

        def render(self):
            return dbc.Select(
                id=self.id, value=self.default, size="sm",
                className="m-1 d-inline-block w-auto",
                options=[ { 'label': o, 'value': o } for o in self.options ]
            )


    # components
    def text(self, txt, block):
        self._add_component(txt, block, None)

    def month(self, id, default='jan', block=None, label=None):
        Maproom._Month(self, id, default, block, label)

    def select(self, id, options, default=None, block=None, label=None):
        Maproom._Select(self, id, options, default, block, label)

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
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(v['label']),
                        dbc.CardBody([
                            c.render() if isinstance(c, Maproom._Control) else c
                            for c in v['content']
                        ]),
                    ], className="mb-4 ml-4 mr-4")
                    for _, v in self._blocks.items()
                ], width=3),
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
                    ], style={'width': '100%', 'height': '500px' })),
                    dbc.Row(dbc.Tabs([
                        dbc.Tab(t['content'], label=t['label'])
                        for _, t in self._tabs.items()
                    ])),
                ], width=9),
            ])
        ], style={ 'height': '100vh' }, fluid=True)
        return APP


    def start(self):
        SERVER = flask.Flask(__name__)
        APP = self.render(SERVER)
        APP.run_server(
            threaded=False,
        )
