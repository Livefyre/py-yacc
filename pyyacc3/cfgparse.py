class ConfigParserAdaptor(object):
    """Provides a duck-type interface to a read-only ConfigParser object."""

    def __init__(self, params):
        self._params = params

    def get(self, section, name, type_=None):  # @ReservedAssignment
        v = self._params[section][name]
        if type_:
            assert isinstance(v, type_), (type(v), type_)
        return v

    def getboolean(self, section, name):
        return self.get(section, name, bool)

    def getint(self, section, name):
        return self.get(section, name, (int, int))

    def getfloat(self, section, name):
        return self.get(section, name, float)

    def getdict(self, section, name):
        """Extension"""
        return self.get(section, name, dict)

    def getlist(self, section, name):
        """Extension"""
        return self.get(section, name, (list, tuple))

    def has_section(self, section):
        return section in self._params

    def has_option(self, section, name):
        return name in self._params[section]

    def options(self, section):
        return list(self._params[section].keys())

    def items(self, section):
        return list(self._params[section].items())

    def sections(self):
        return list(self._params.keys())

    def to_dict(self):
        return self._params

    def set(self, section, key, value):
        sect = self._params.setdefault(section, {})
        sect[key] = value
