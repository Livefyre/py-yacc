'''
Created on Jan 4, 2013

@author: nino
'''
import urlparse
'''
Created on Jan 2, 2013

@author: nino
'''

from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader
    
from pyyacc.objects import ValueSpec, Requirement, Optional,\
    ConfigurationDescriptor, ConfigSet
from logging import getLogger

LOG = getLogger(__file__)

Loader.add_constructor("!spec", ValueSpec._yaml_constructor)
Loader.add_constructor("!required", Requirement._yaml_constructor)
Loader.add_constructor("!optional", Optional._yaml_constructor)
Loader.add_constructor("!URI", lambda loader, node: urlparse.urlparse(loader.construct_scalar(node)))
        

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
    
    def validate(self, params):
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
                    errors[(section, key)] = value
                    continue
                if not isinstance(value, setting.obj_type):
                    errors[(section, key)] = TypeError("expected %s, got %s" % (setting.obj_type, type(value)))
        return errors
    
def parse(fd):
    """Return a ConfigurationDescriptor"""
    v = load(fd, Loader)
    if isinstance(v, dict):
        return ConfigurationDescriptor(v)
    return v
