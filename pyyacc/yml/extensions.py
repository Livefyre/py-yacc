import urlparse
from pyyacc.yml import register
from logging import getLogger
from pyyacc.uritools import DataURI
from pyyacc.cstore import CredentialStore, CREDENTIAL_MIMETYPE

LOG = getLogger(__name__)


class ConfigRoot(dict):
    """A root document. Not exactly a yaml node, but the root."""

    def validate(self, params):
        """
        Identify any errors in the aggregated configuration.
        :returns: dict
        """
        errors = {}
        for section in self.keys():
            for key, setting in self[section].items():
                if not isinstance(setting, ValueSpec):
                    LOG.debug("ignoring non-spec value for '%s': %s", key, setting)
                    continue
                self._validate_key(errors, params, section, key, setting)
        return errors

    def _validate_key(self, errors, params, section, key, setting):
        if isinstance(setting.value, Optional) and key not in params[section]:
            return
        value = params[section][key]
        if isinstance(value, Requirement):
            errors[section, key] = value
            return
        if not isinstance(value, setting.obj_type):
            errors[section, key] = TypeError(
                "expected %s, got %s (from %s)" % (setting.obj_type, type(value), value))


@register("!spec")
class ValueSpec(object):
    """Declares and documents acceptable values for a setting."""

    def __init__(self, type, description=None, value=None, examples=None, deprecated=False):
        self.type = type
        self.value = value
        self.description = description
        self.examples = examples
        self.deprecated = deprecated

    @classmethod
    def _yaml_constructor(cls, loader, node):
        d = loader.construct_mapping(node)
        if 'type' not in d:
            raise ValueError('type is required: %s' % d)
        if 'description' not in d:
            raise ValueError('description is required: %s' % d)
        return cls(**d)

    def coerce(self, input_):
        if getattr(self.type, 'pyyacc_coerce', None) and not getattr(input_, '_pyyacc_no_coerce', False):
            input_ = self.type.pyyacc_coerce(input_)
        return input_

    @property
    def obj_type(self):
        if isinstance(self.type, list) and len(self.type):
            return tuple(type(t) for t in self.type)
        return type(self.type)

    def __repr__(self):
        return "ValueSpec(%s)" % (self.__dict__)


@register("!required")
class Requirement(object):
    _pyyacc_no_coerce = True

    def __init__(self, description):
        self.description = description

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.description)

    @classmethod
    def _yaml_constructor(cls, loader, node):
        return cls(loader.construct_scalar(node))


@register("!optional")
class Optional(object):
    _pyyacc_no_coerce = True

    def __repr__(self):
        return "%s" % (self.__class__.__name__)

    @classmethod
    def _yaml_constructor(cls, loader, node):
        return cls()


@register("!uri")
class URI(unicode):
    @classmethod
    def _yaml_constructor(cls, loader, node):
        return cls.pyyacc_coerce(loader.construct_scalar(node))

    @classmethod
    def pyyacc_coerce(cls, input_):
        p = cls(input_)
        p.validate()
        return p

    def parse(self):
        return urlparse.urlparse(self)

    def validate(self):
        """We don't want to be too strict here, as this could include file:///... mongo connection strings etc."""
        if not self:
            return
        p = self.parse()
        if not p.scheme:
            raise ValueError("Unparseable URL: %s" % self)


@register("!credential")
class Credential(DataURI):
    @classmethod
    def _yaml_constructor(cls, loader, node):
        return cls.pyyacc_coerce(loader.construct_scalar(node))

    @classmethod
    def pyyacc_coerce(cls, input_):
        if input_ is None:
            input_ = ''
        if not isinstance(input_, basestring):
            raise ValueError(input_)
        input_ = str(input_)

        if input_.startswith("data:"):
            p = cls(input_)
        else:
            p = cls(mimetype=CREDENTIAL_MIMETYPE,
                    params=dict(name="", provider=""), data=input_)

        resolved = CredentialStore.get(p)
        if resolved != None:
            if resolved.startswith("data:" + CREDENTIAL_MIMETYPE):
                # handle the case where the value is provided back as a data URI
                resolved = str(DataURI(resolved))
            p = cls(mimetype=CREDENTIAL_MIMETYPE,
                    params=p.parameters, b64=p.is_base64, data=resolved)
        return p
