import StringIO
import unittest

from pyyacc.cstore import CredentialStore, EnvironmentResolver
from pyyacc.yml import load
from pyyacc.yml.extensions import Requirement, URI, ValueSpec, Optional,\
    Credential
import os


parse = load


class TestRegistration(unittest.TestCase):
    def test_required(self):
        load("!required cluster.yaml")


class TestParser(unittest.TestCase):
    def fd(self, string):
        return StringIO.StringIO(string)

    def test_parse_empty_cred(self):
        x = parse(self.fd("""!credential"""))
        assert isinstance(x, Credential)
        self.assertEqual(x, "")

    def test_parse_str_cred(self):
        x = parse(self.fd("""!credential "abc" """))
        assert isinstance(x, Credential)
        self.assertEqual(x, "abc")

    def test_parse_uri_cred(self):
        x = parse(self.fd("""!credential "data:,abc" """))
        assert isinstance(x, Credential)
        self.assertEqual(x, "abc")

    def test_parse_uri_cred2(self):
        x = parse(self.fd("""!credential "data:application/vnd.pyyacc.credential,abc" """))
        assert isinstance(x, Credential)
        self.assertEqual(x, "abc")

    def test_parse_uri_cred_b64(self):
        x = parse(self.fd("""!credential "data:application/vnd.pyyacc.credential;base64,YWJj" """))
        assert isinstance(x, Credential)
        self.assertEqual(x, "abc")

    def test_parse_uri_cred_param(self):
        x = parse(self.fd("""!credential "data:application/vnd.pyyacc.credential;name=123;base64,YWJj" """))
        assert isinstance(x, Credential)
        self.assertEqual(x.fullstring(), 'data:application/vnd.pyyacc.credential;name=123;base64,YWJj')
        self.assertEqual(x, "abc")
        self.assertEqual(x.parameters, dict(name="123"))

    def test_parse_uri_cred_params(self):
        x = parse(self.fd(
            """!credential "data:application/vnd.pyyacc.credential;name=123%3D;other=XXX;base64,YWJj" """))
        assert isinstance(x, Credential)
        self.assertEqual(x, "abc")
        self.assertEqual(x.fullstring(), 'data:application/vnd.pyyacc.credential;name=123%3D;other=XXX;base64,YWJj')
        self.assertEqual(x.parameters, dict(name="123=", other="XXX"))

    def test_parse_cred_env_resolver(self):
        os.environ['Unit_Test__key'] = 'meow'
        CredentialStore.add_resolver(EnvironmentResolver())
        x = parse(self.fd(
            """!credential "data:application/vnd.pyyacc.credential;provider=Unit%20Test;name=key," """))
        assert isinstance(x, Credential)
        self.assertEqual(x.fullstring(), 'data:application/vnd.pyyacc.credential;name=key;provider=Unit%20Test,meow')
        self.assertEqual(os.environ['Unit_Test__key'], "meow")
        self.assertEqual(x, "meow")

    def test_parse_cred_env_resolver_data_uri(self):
        os.environ['Unit_Test__key'] = 'data:application/vnd.pyyacc.credential;base64,' + "meow".encode("base64")
        CredentialStore.add_resolver(EnvironmentResolver())
        x = parse(self.fd(
            """!credential "data:application/vnd.pyyacc.credential;provider=Unit%20Test;name=key," """))
        assert isinstance(x, Credential)
        self.assertEqual(x.fullstring(), 'data:application/vnd.pyyacc.credential;name=key;provider=Unit%20Test,meow')
        self.assertEqual(x, "meow")

    def test_parse_requirement(self):
        x = parse(self.fd("""!required "abc" """))
        assert isinstance(x, Requirement)
        repr(x)

    def test_parse_optional(self):
        x = parse(self.fd("""!optional "abc" """))
        assert isinstance(x, Optional)
        repr(x)

    def test_parse_uri(self):
        x = parse(self.fd("""!uri "smtp://host:25/" """))
        assert isinstance(x, URI), type(x)
        assert str(x) == "smtp://host:25/"
        x = x.parse()
        assert x.hostname == "host"
        assert x.port == 25
        assert x.scheme == "smtp"

    def test_parse_spec(self):
        x = parse(self.fd("""!spec\ntype: !!int "0"\ndescription:\nvalue: 1"""))
        assert isinstance(x, ValueSpec)
        assert x.obj_type == int
        assert x.value == 1
        assert not x.description
        assert not x.examples
        assert not x.deprecated

        x = parse(self.fd("""!spec\ntype: !!int "0"\ndescription:\nvalue: 1\ndeprecated: true"""))
        assert x.deprecated
        repr(x)
