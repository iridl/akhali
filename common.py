import uuid

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
        elif self._ids_in_use[id] != kind:
            raise MaproomException(f"ID `{id}` is {self._ids_in_use[id]} not {kind}")
        else:
            pass


def gensym():
    str(uuid.uuid4())

def dict_to_options(d):
    return [
        { 'label': k, 'value': v }
        for k, v in d.items()
    ]
