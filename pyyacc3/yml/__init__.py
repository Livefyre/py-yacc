from logging import getLogger

from yaml import dump as _dump
from yaml import load as _load

try:
    from yaml import CLoader as __Loader, CDumper as __Dumper
except ImportError:
    from yaml import Loader as __Loader, Dumper as __Dumper

LOG = getLogger(__name__)
EXTENSION_REGISTRY = {}


def register(type_, factory="_yaml_constructor", repr_="_yaml_representer"):

    def _wrapper(cls):
        cls._yaml_tag = type_

        def _register(loader, dumper):
            loader.add_constructor(type_, getattr(cls, factory))
            dump = getattr(cls, repr_, None)
            if dump:
                dumper.add_representer(cls, dump)

        EXTENSION_REGISTRY[type_] = _register
        return cls

    return _wrapper


def _register_types():
    for type_ in list(EXTENSION_REGISTRY.keys()):
        EXTENSION_REGISTRY.pop(type_)(__Loader, __Dumper)


def load(stream, Loader=None):
    return _load(stream, Loader=Loader or getLoader())


def dump(params, stream, Dumper=None, **kwargs):
    return _dump(params, stream, Dumper=Dumper or getDumper(), **kwargs)


def getLoader():
    _register_types()
    return __Loader


def getDumper():
    _register_types()
    return __Dumper
