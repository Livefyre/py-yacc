from yaml import load as _load, dump as _dump
try:
    from yaml import CLoader as __Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader as __Loader, Dumper
from logging import getLogger

LOG = getLogger(__name__)
EXTENSION_REGISTRY = {}


def register(type_, factory="_yaml_constructor"):
    def _wrapper(cls):
        def _register(loader):
            loader.add_constructor(type_, getattr(cls, factory))

        EXTENSION_REGISTRY[type_] = _register
        return cls
    return _wrapper


def _register_types():
    for type_ in EXTENSION_REGISTRY.keys():
        LOG.info("registering `%s`", type_)
        EXTENSION_REGISTRY.pop(type_)(__Loader)


def load(stream, Loader=None):
    return _load(stream, Loader=Loader or getLoader())


def dump(params, stream, Dumper=Dumper, **kwargs):
    return _dump(params, stream, Dumper=Dumper, **kwargs)


def getLoader():
    _register_types()
    return __Loader