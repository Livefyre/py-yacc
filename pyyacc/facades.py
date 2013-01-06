'''
Created on Jan 5, 2013

@author: nino
'''

class ConfigParserFacade(object):
    """Provides a duck-type interface to a read-only ConfigParser object."""
    def __init__(self, descriptor, params):
        self._descriptor = descriptor
        self._params = params
        
    def get(self, section, name, type=None): #@ReservedAssignment
        v = self._params[section][name]
        if type:
            assert isinstance(v, type)
        return v
        
    def getboolean(self, section, name):
        return self.get(section, name, bool)
    
    def getint(self, section, name):
        return self.get(section, name, (int, long))
    
    def getfloat(self, section, name):
        return self.get(section, name, float)
    
    def has_section(self, section):
        return section in self._params

    def has_option(self, section, name):
        return name in self._params[section]
    
    def options(self, section):
        return self._params[section].keys() 

    def items(self, section):
        return self._params[section].items()
    
    def sections(self):
        return self._params.keys()

