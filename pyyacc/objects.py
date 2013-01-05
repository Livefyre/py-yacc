'''
Created on Jan 4, 2013

@author: nino
'''

class ConfigurationDescriptor(dict): 
    pass

class ConfigSet(dict):
    def value(self, section, key):
        return self[section][key]

class ValueSpec(object):
    """Declares and documents acceptable values for a setting."""
    def __init__(self, value_type, description=None, value=None, examples=None, deprecated=None):
        self.obj_type = type(value_type)
        self.value = value
        self.description = description
        self.examples = examples
        self.deprecated = deprecated
    
    @classmethod
    def _yaml_constructor(cls, loader, node):
        d = loader.construct_mapping(node)
        d['value_type'] = d.pop('type')
        if 'description' not in d:
            raise ValueError('description is required: %s' % d)
        return cls(**d)
            
    def __repr__(self):
        return "ValueSpec(%s)" % (self.__dict__)


class Requirement(object):
    def __init__(self, description):
        self.description = description
    
    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.description)

    @classmethod
    def _yaml_constructor(cls, loader, node):
        return cls(loader.construct_scalar(node))
    
class Optional(object):
    def __repr__(self):
        return "%s" % (self.__class__.__name__)

    @classmethod
    def _yaml_constructor(cls, loader, node):
        return cls()
