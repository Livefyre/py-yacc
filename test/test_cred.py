import unittest
from pyyacc.uritools import DataURI
from pyyacc.cstore import EnvironmentResolver
import os

class TestBackend(unittest.TestCase):
    pass

def cred(val='', **kwargs):
    d = DataURI(mimetype="application/vnd.pyyacc.credential",
                    params=kwargs, data=val)
    #print d.fullstring(), d.parameters
    return d

class TestEnvironmentResolver(unittest.TestCase):
    def test_none(self):
        self.assertEqual(EnvironmentResolver().get(cred()), None)
        self.assertEqual(EnvironmentResolver().get(cred(name="foo", provider="bar")), None)
        
    def test_simple(self):
        os.environ['bar__foo'] = "meow"
        self.assertEqual(EnvironmentResolver().get(cred(name="foo", provider="bar")), "meow")

    def test_case(self):
        os.environ['Bar__Foo'] = "meow"
        self.assertEqual(EnvironmentResolver().get(cred(name="Foo", provider="Bar")), "meow")

    def test_chars(self):
        os.environ['bar__foo_cow'] = "meow"
        self.assertEqual(EnvironmentResolver().get(cred(name="foo-cow", provider="bar")), "meow")

    def test_base64(self):
        os.environ['bar__foo_cow'] = "meow".encode("base64")
        self.assertEqual(EnvironmentResolver().get(cred(name="foo-cow", provider="bar")), "meow".encode("base64"))
