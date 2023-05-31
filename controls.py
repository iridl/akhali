import flask
import dash
from inspect import signature, Parameter
from dash import html
from dash.dependencies import Output, Input, State
import dash_bootstrap_components as dbc
import dash_leaflet as dlf
from collections import OrderedDict
from common import MaproomException, dict_to_options, gensym
import uuid


class Control:
    KIND = "control"
    def __init__(self, id):
        self.id = id


class Month(Control):
    MONTHS = OrderedDict([
        (m,  m[0:3].lower())
        for m in [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December',
        ]
    ])

    def __init__(self, id, default):
        if default not in self.MONTHS.values():
            raise MaproomException(f"`{default}` is not a valid three-letter month name")
        else:
            self.default = default
        super().__init__(id)

    def render(self):
        return dbc.Select(
            id=self.id, value=self.default, size="sm",
            className="m-1 d-inline-block w-auto",
            options=dict_to_options(self.MONTHS),
        )


class Select(Control):
    def __init__(self, id, options, default):
        self.options = options
        if default is None:
            self.default= options[0]
        elif default not in options:
            raise MaproomException(f"`{default}` is not in options list")
        else:
            self.default = default
        super().__init__(id)

    def render(self):
        return dbc.Select(
            id=self.id, value=self.default, size="sm",
            className="m-1 d-inline-block w-auto",
            options=[ { 'label': o, 'value': o } for o in self.options ]
        )


class Number(Control):
    def __init__(self, id, min, max, step, default):
        if (min is None) or (max is None):
            if default is not None:
                self.default = default
            else:
                self.default = 0
        elif max < min:
            raise MaproomException("upper bound of number must be higher than lower")
            raise MaproomException("max must be higher than min")
        else:
            if default is None:
                self.default = min
            elif default < min or default > max:
                raise MaproomException("invalid default value")
            else:
                self.default = default
        self.min = min
        self.max = max
        self.step = step
        super().__init__(id)

    def render(self):
        return dbc.Input(
            id=self.id, type="number", min=self.min, max=self.max, step=self.step,
            size="sm", className="m-1 d-inline-block w-auto", debounce=True,
            value=str(self.default)
        )


class Text(Control):
    def __init__(self, id, default):
        self.default = default
        super().__init__(id)

    def render(self):
        return dbc.Input(
            id=self.id, size="sm", value=str(self.default),
            className="m-1 d-inline-block w-auto",
        )


class Output(Control):
    def __init__(self, id, title):
        self.title = title
        super().__init__(id)

    def render(self):
        return dbc.Card([
            dbc.CardHeader(self.title),
            dbc.CardBody([
                html.P("", id=self.id)
            ]),
        ], className="mb-4 ml-4 mr-4")


class Groups:
    def __init__(self, ids, callbacks=[]):
        self._ids = ids
        self._groups = []
        self._callbacks = callbacks
        self._locked = False

    def empty():
        return not self._groups

    def group(self, title, id=None):
        if id is None:
            idx = str(uuid.uuid4())
        else:
            idx = id
        self._groups.append({'title': title,
                             'content': [],
                             'id': idx,
                             })

    def _add_element(self, elem):
        if not self._groups:
            raise MaproomException("please create a group first")
        else:
            if hasattr(elem, "id"):
                self._ids.add(elem.id, elem.KIND)
            self._groups[-1]['content'].append(elem)

    def _add_callback(self, function, output, prop):
        self._callbacks.append({ 'function': function,
                                 'output': output,
                                 'prop': prop
                                })

    def label(self, txt):
        self._add_element(txt)


class Controls(Groups):
    def __init__(self, ids, callbacks):
        super().__init__(ids, callbacks)

    def group(self, title, display=None):
        id = str(uuid.uuid4())
        if display is not None:
            if not callable(display):
                raise MaproomException("Did not pass a function")

            for p in signature(display).parameters.keys():
                self._ids.validate(p, Control.KIND)

            self._add_callback(display, id, "hidden")
        super().group(title, id)

    def month(self, id, default='jan'):
        self._add_element(Month(id, default))

    def select(self, id, options, default=None):
        self._add_element(Select(id, options, default))

    def number(self, id, min=None, max=None, step=1, default=None):
        self._add_element(Number(id, min, max, step, default))

    def text(self, id, default=""):
        self._add_element(Text(id, default))

    def render(self):
        return [
            html.Div(dbc.Card([
                dbc.CardHeader(g['title']),
                dbc.CardBody([
                    c.render() if isinstance(c, Control) else c
                    for c in g['content']
                ]),
            ], className="mb-4 ml-4 mr-4"), id = g['id'])
            for g in self._groups
        ]

class Plot:
    KIND = "plot"

    def __init__(self, id):
        self.id = id


class Plots(Groups):
    def __init__(self, ids, callbacks):
        super().__init__(ids, callbacks)

    def plot(self, id):
        p = Select(id, ["A", "B"], None)
        self._add_element("")

    def output(self, title, function):
        # id = gensym()
        id = str(uuid.uuid4())
        if not callable(function):
            raise MaproomException("Did not pass a function")

        for p in signature(function).parameters.keys():
            self._ids.validate(p, Control.KIND)

        self._add_element(Output(id, title))
        self._add_callback(function, id, "children")

    def render(self):
        return dbc.Tabs([
            dbc.Tab([
                c.render() if isinstance(c, Control) else c
                for c in g['content']
            ], label=g['title'], style={ 'margin-top': '10px' }, )
            for g in self._groups
        ])
