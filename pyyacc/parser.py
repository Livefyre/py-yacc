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
    from yaml import Loader, Dumper
    
from pyyacc.objects import ValueSpec, Requirement, Optional

Loader.add_constructor("!spec", ValueSpec._yaml_constructor)
Loader.add_constructor("!required", Requirement._yaml_constructor)
Loader.add_constructor("!optional", Optional._yaml_constructor)
Loader.add_constructor("!URI", lambda loader, node: urlparse.urlparse(loader.construct_scalar(node)))


class Configuration(object):
    class _proxy(object):
        def __init__(self, config, section):
            self.config = config
            self.section = section 
            
        def __getattr__(self, name):
            return self.config.get(self.section, name)
    
    def __init__(self, descriptor, params):
        self._descriptor = descriptor
        self._params = params
        
    def get(self, section, name):
        return self._params[section][name]
    
    def __getattr__(self, section):
        return self._proxy(self, section)


class ConfigurationBuilder(object):
    def __init__(self, descriptor):
        self.descriptor = descriptor
        
    def build(self, *overlays):
        params = {}
        for section in self.descriptor.keys():
            params[section] = {}
            for key, setting in self.descriptor[section].items():
                value = setting.value
                for o in overlays:
                    if key in o.get(section, {}):
                        value = o[section][key]
                if isinstance(value, Optional):
                    continue
                params[section][key] = value
        return params
    
    def validate(self, params):
        errors = {}
        for section in self.descriptor.keys():
            for key, setting in self.descriptor[section].items():
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
    return load(fd, Loader)
                

if __name__ == '__main__':
    import sys, pprint
    descriptor = load(open(sys.argv[1]), Loader)
    yamls = [load(open(f), Loader) for f in sys.argv[2:]]
    print "*"*50, "Descriptor"
    pprint.pprint(descriptor, depth=3)
    b = ConfigurationBuilder(descriptor)
    params = b.build(*yamls)
    print "*"*50, "Params"
    pprint.pprint(params)
    print "*"*50, "Errors"
    pprint.pprint(b.validate(params))
    
    c = Configuration(descriptor, params)
    assert c.email.from_address == c.get("email", "from_address")
    