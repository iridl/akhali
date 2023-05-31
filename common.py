import uuid
import xarray as xr
import pingrid
import urllib
from inspect import signature, Parameter

def coerce_set(k):
    if type(k) == set:
        return k
    else:
        return {k}

class MaproomException(Exception):
    pass

class IDRegistry:
    def __init__(self):
        self._ids_in_use = dict()

    def add(self, id, kind):
        if id in self._ids_in_use.keys():
            raise MaproomException(f"ID `{id}` already in used ")
        else:
            self._ids_in_use[id] = kind

    def validate(self, id, kind):
        if id not in self._ids_in_use.keys():
            raise MaproomException(f"there is no such ID `{id}`")
        elif self._ids_in_use[id] not in coerce_set(kind):
            raise MaproomException(f"ID `{id}` is {self._ids_in_use[id]} not {kind}")
        else:
            pass

    def kind(self, id):
        return self._ids_in_use[id]

class CallbackRegistry:
    def __init__(self):
        self.defs = []


    def add(self, function, output, prop):
        self.defs.append({ 'function': function,
                           'output': output,
                           'prop': prop
                         })


def gensym():
    str(uuid.uuid4())

def dict_to_options(d):
    return [
        { 'label': k, 'value': v }
        for k, v in d.items()
    ]

def inverter(f):
    def wrapped(*args, **kwargs):
        result = f(*args, **kwargs)
        if type(result) is not bool:
            raise MaproomException("Did not return truth value")
        return not result
    return wrapped

def tile_url(prefix):
    def url(**kwargs):
        qstr = urllib.parse.urlencode(kwargs)
        return f"/{prefix}/{{z}}/{{x}}/{{y}}?{qstr}"
    return url

def tile_wrap(path, function):
    def tile(tz, tx, ty):
        x_min = pingrid.tile_left(tx, tz)
        x_max = pingrid.tile_left(tx + 1, tz)
        # row numbers increase as latitude decreases
        y_max = pingrid.tile_top_mercator(ty, tz)
        y_min = pingrid.tile_top_mercator(ty + 1, tz)

        data = xr.open_dataset(path)

        if (
                x_min > data['X'].max() or
                x_max < data['X'].min() or
                y_min > data['Y'].max() or
                y_max < data['Y'].min()
        ):
            return pingrid.image_resp(pingrid.empty_tile())

        res = data['X'][1].item() - data['X'][0].item()

        data = data.sel(
            X=slice(x_min - x_min % res, x_max + res - x_max % res),
            Y=slice(y_min - y_min % res, y_max + res - y_max % res),
        ).compute()

        args = []
        for p in list(signature(function).parameters.keys())[1:]:
            args.append(pingrid.parse_arg(p))

        tile = function(data, *args).rename({'X': "lon", 'Y': "lat"})

        result = pingrid.tile(tile, tx, ty, tz, None) # add clipping

        return result
    return tile
