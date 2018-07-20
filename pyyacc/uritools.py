import re
import urllib


MIMETYPE_REGEX = r'[\w]+\/[\w\-\+\.]+'
_MIMETYPE_RE = re.compile('^{}$'.format(MIMETYPE_REGEX))

CHARSET_REGEX = r'[\w\-\+\.]+'
_CHARSET_RE = re.compile('^{}$'.format(CHARSET_REGEX))

PARAM_REGEX = r'[^;,]'

DATA_URI_REGEX = (
    r'data:' +
    r'(?P<mimetype>{})?'.format(MIMETYPE_REGEX) +
    r'(?P<parameters>(?:\;\w+=[^;,]*)*)' +
    r'(?P<base64>\;base64)?' +
    r',(?P<data>.*)')
_DATA_URI_RE = re.compile(r'^{}$'.format(DATA_URI_REGEX), re.DOTALL)


class DataURI(str):
    def __new__(cls, raw=None, mimetype=None, b64=False, data='', params=None):
        if raw:
            mimetype, params, b64, data = DataURI._parse(raw)
        uri = super(DataURI, cls).__new__(cls, data)
        uri.mimetype = mimetype
        uri.parameters = params or {}
        uri.is_base64 = b64
        return uri

    @classmethod
    def _parse(cls, value):
        match = _DATA_URI_RE.match(value)
        if not match:
            raise ValueError("Not a valid data URI: %r" % value)
        mimetype = match.group('mimetype') or None
        params = match.group('parameters') or None
        if params:
            def _param(p):
                n, v = p.split("=", 1)
                return n, urllib.unquote(v)

            params = dict((_param(x) for x in filter(None, params.split(";"))))
        if match.group('base64'):
            data = match.group('data').decode('base64')
        else:
            data = urllib.unquote(match.group('data'))
        return mimetype, params, bool(match.group('base64')), data

    def fullstring(self):
        val = ["data:"]
        if self.mimetype:
            val.append(self.mimetype)
        if self.parameters:
            for k, v in sorted(self.parameters.items()):
                val.append(";%s=%s" % (k, urllib.quote(v)))
        if self.is_base64:
            val.append(";base64")
        val.append(",%s" % (self.encode("base64").replace('\n', '') if self.is_base64 else self))
        return "".join(val)