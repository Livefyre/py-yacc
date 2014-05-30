'''
Created on Jan 4, 2013

@author: nino
'''
import urlparse
'''
Created on Jan 2, 2013

@author: nino
'''

from yaml import load as _load, dump as _dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from pyyacc.objects import ValueSpec, Requirement, Optional, \
    ConfigurationDescriptor, ConfigSet, to_url, ParseResult
from logging import getLogger

LOG = getLogger(__file__)

Loader.add_constructor("!spec", ValueSpec._yaml_constructor)
Loader.add_constructor("!required", Requirement._yaml_constructor)
Loader.add_constructor("!optional", Optional._yaml_constructor)
Loader.add_constructor("!URI", lambda loader, node: to_url(loader.construct_scalar(node)))
Loader.add_constructor("!uri", lambda loader, node: to_url(loader.construct_scalar(node)))
Loader.add_constructor("!url", lambda loader, node: to_url(loader.construct_scalar(node)))
# this gets a little funky.
# Dumper.add_representer(ParseResult, lambda dumper, data: dumper.represent_scalar("!uri", data.geturl()))


class ConfigurationBuilder(object):
    def __init__(self, descriptor):
        self.descriptor = descriptor

    def build(self, *overlays):
        params = ConfigSet()
        for section in self.descriptor.keys():
            params[section] = {}
            for key, setting in self.descriptor[section].items():
                if not isinstance(setting, ValueSpec):
                    LOG.debug("ignoring non-spec value for '%s': %s", key, setting)
                    continue
                value = setting.value
                for i, o in enumerate(overlays):
                    if key in o.get(section, {}):
                        value = o[section][key]
                        LOG.debug("%s.%s found in overlay %d", section, key, i)
                if isinstance(value, Optional):
                    LOG.debug("%s.%s is optional, but not defined, skipping", section, key)
                    continue
                params[section][key] = value
        return params

    def validate(self, params, ignored=[]):
        errors = {}
        for section in self.descriptor.keys():
            for key, setting in self.descriptor[section].items():
                if not isinstance(setting, ValueSpec):
                    LOG.debug("ignoring non-spec value for '%s': %s", key, setting)
                    continue
                if isinstance(setting.value, Optional) and key not in params[section]:
                    continue
                value = params[section][key]
                if isinstance(value, Requirement):
                    if value.description in ignored:
                        del params[section][key]
                        continue
                    errors[(section, key)] = value
                    continue
                if not isinstance(value, setting.obj_type):
                    errors[(section, key)] = TypeError("expected %s, got %s (from %s)" % (setting.obj_type, type(value), value))
        return errors


def load(stream, Loader=Loader):
    return _load(stream, Loader=Loader)


def dump(params, stream, Dumper=Dumper, **kwargs):
    return _dump(params, stream, Dumper=Dumper, **kwargs)


def parse(fd):
    """Parse the provided YAML. Assuming this is a well-formed map at the root, it returns a `ConfigurationDescriptor`."""
    v = load(fd)
    if isinstance(v, dict):
        return ConfigurationDescriptor(v)
    return v


def unparse(stream, params, **kwargs):
    """Serialize the parameters to the stream as YAML."""
    dump(params, stream, **kwargs)


def build(*yamls):
    """Produces a builder and compiled dictionary of params."""
    if not yamls:
        return None, None
    desc = yamls[0]
    descriptor = parse(open(desc))
    builder = ConfigurationBuilder(descriptor)
    params = builder.build(*filter(bool, [parse(open(f)) for f in yamls[1:]]))
    return builder, params


if __name__ == '__main__':
    import sys, pprint
    yamls = sys.argv[1:]
    builder, params = build(*yamls)
    errs = builder.validate(params)
    if errs:
        for (section, key), err in errs.iteritems():
            print "%s:\n  %s: %s" % (section, key, err)
        sys.exit(1)
    else:
        print "No errors"
        sys.exit(0)
