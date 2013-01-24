'''
Created on Jan 4, 2013

@author: nino
'''
import urlparse

class ConfigurationDescriptor(dict): 
    pass

class ConfigSet(dict):
    def value(self, section, key):
        return self[section][key]

class ValueSpec(object):
    """Declares and documents acceptable values for a setting."""
    def __init__(self, value_type, description=None, value=None, examples=None, deprecated=False):
        self.obj_type = value_type
        self.value = value
        self.description = description
        self.examples = examples
        self.deprecated = deprecated
    
    @classmethod
    def _yaml_constructor(cls, loader, node):
        d = loader.construct_mapping(node)
        try:
            d['value_type'] = type(d.pop('type'))
        except KeyError:
            raise ValueError('type is required: %s' % d)
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

class ParseResult(urlparse.ParseResult):
    def __str__(self):
        return self.geturl()

def to_uri(v):
    p = urlparse.urlparse(v)
    p.__class__ = ParseResult
    return p