import os
import urllib.parse
from logging import getLogger

from pyyacc3.yml import register

LOG = getLogger(__name__)


class _Scalar(object):
    'Provides a simple representer.'

    @classmethod
    def _yaml_representer(cls, dumper, data):
        return dumper.represent_scalar(cls._yaml_tag, "%s" % data, style='"')


@register("!spec")
class ValueSpec(object):
    """Declares and documents acceptable values for a setting."""

    def __init__(self,
                 type,
                 description=None,
                 value=None,
                 examples=None,
                 deprecated=False,
                 sensitive=False):  # @ReservedAssignment
        self.type = type
        self.optional = isinstance(value, Optional)
        self.value = None if self.optional else value
        self.description = description
        self.examples = examples
        self.deprecated = deprecated
        self.sensitive = sensitive
        self.error = None

    def validate(self, input_, fail=False):
        if input_ is None:
            if self.optional:
                return None
        if isinstance(input_, Requirement):
            if fail:
                raise ValueError("Value was undefined: %s" % input_)
            return input_
        if not isinstance(input_, self.expected_type):
            t = TypeError("TypeError - expected %s, got %s; val: %s" %
                          (self.expected_type, type(input_), input_))
            if fail:
                raise t
            return ConfigError(str(t))

    @classmethod
    def _yaml_constructor(cls, loader, node):
        d = loader.construct_mapping(node)
        if 'type' not in d:
            raise ValueError('type is required: %s' % d)
        if 'description' not in d:
            raise ValueError('description is required: %s' % d)
        return cls(**d)

    def coerce(self, input_):
        if getattr(self.type, 'pyyacc_coerce',
                   None) and not getattr(input_, '_pyyacc_no_coerce', False):
            input_ = self.type.pyyacc_coerce(input_)
        return input_

    @property
    def expected_type(self):
        if isinstance(self.type, list) and len(self.type):
            return tuple(type(t) for t in self.type)
        return type(self.type)

    def __repr__(self):
        return "ValueSpec(%s)" % (self.__dict__)


@register("!required")
class Requirement(_Scalar):
    _pyyacc_no_coerce = True

    def __init__(self, description):
        self.description = description

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.description)

    @classmethod
    def _yaml_constructor(cls, loader, node):
        return cls(loader.construct_scalar(node))

    def __eq__(self, b):
        return b.description == self.description


@register("!optional")
class Optional(_Scalar):
    _pyyacc_no_coerce = True

    def __repr__(self):
        return "%s" % (self.__class__.__name__)

    @classmethod
    def _yaml_constructor(cls, loader, node):
        return cls()


@register("!uri")
class URI(str, _Scalar):

    @classmethod
    def _yaml_constructor(cls, loader, node):
        return cls.pyyacc_coerce(loader.construct_scalar(node))

    @classmethod
    def pyyacc_coerce(cls, input_):
        p = cls(input_)
        p.validate()
        return p

    def parse(self):
        return urllib.parse.urlparse(self)

    def validate(self):
        """
        We don't want to be too strict here, as this could include
        file:///... mongo connection strings etc.
        """
        if not self:
            return
        p = self.parse()
        if not p.scheme:
            raise ValueError("Unparseable URL: %s" % self)


@register("!err")
class ConfigError(ValueError, _Scalar):

    @classmethod
    def _yaml_constructor(cls, loader, node):
        return cls.pyyacc_coerce(loader.construct_scalar(str(node)))


@register("!environment")
class EnvVar(str, _Scalar):
    """A pointer to a value in the environment."""

    def __new__(cls, name):
        evar = super(EnvVar, cls).__new__(cls, name)
        return evar

    def resolve(self, default=None):
        from pyyacc3.yml import load
        try:
            val = os.environ[self]
        except KeyError:
            if default:
                return default
            raise
        else:
            try:
                return load(val)
            except:
                LOG.warning("Error parsing environment value from %s", self)
                raise

    @classmethod
    def _yaml_constructor(cls, loader, node):
        name = loader.construct_scalar(node)
        return cls(name)
