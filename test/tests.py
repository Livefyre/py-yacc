'''
Created on Jan 4, 2013

@author: nino
'''
import unittest
import os
from pyyacc.parser import parse, ConfigurationBuilder
from yaml.scanner import ScannerError
from nose.tools import assert_raises
import StringIO
from pyyacc.objects import Requirement, Optional, ValueSpec,\
    ConfigurationDescriptor, ConfigSet
from urlparse import ParseResult
from pyyacc.facades import ConfigParserFacade


class BaseTest(unittest.TestCase):
    def open(self, filename):
        f = os.path.join(os.path.dirname(__file__), filename)
        return open(f)
    
    def fd(self, string):
        return StringIO.StringIO(string)


class TestParser(BaseTest):
    def test_parse_doc(self):
        v = parse(self.open("spec.yaml"))
        assert isinstance(v, ConfigurationDescriptor)
    
    def test_parse_bad(self):
        with assert_raises(ScannerError):
            parse(self.open("bad.yaml"))
            
    def test_parse_requirement(self):
        x = parse(self.fd("""!required "abc" """))
        assert isinstance(x, Requirement)
        
    def test_parse_optional(self):
        x = parse(self.fd("""!optional "abc" """))
        assert isinstance(x, Optional)

    def test_parse_uri(self):
        x = parse(self.fd("""!URI "smtp://host:25/" """))
        assert isinstance(x, ParseResult)
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


class TestBuilder(BaseTest):
    def test_build_1(self):
        x = parse(self.fd("""!spec\ntype: !!int "0"\ndescription:\nvalue: 1\ndeprecated: true"""))
        b = ConfigurationBuilder(dict(section=dict(param=x)))
        params = b.build()
        assert isinstance(params, ConfigSet)
        assert params['section']['param'] == 1
        
    def test_build_2(self):
        x = parse(self.fd("""!spec\ntype: !!int "0"\ndescription:\nvalue: 1\n"""))
        b = ConfigurationBuilder(dict(section=dict(param=x),
                                      section_1=dict(param=x)))
        params = b.build()
        assert params['section']['param'] == 1
        assert params['section_1']['param'] == 1
        
    def test_overlay_1(self):
        x = parse(self.fd("""!spec\ntype: !!int "0"\ndescription:\nvalue: 1\n"""))
        y = parse(self.fd("""section:\n param: 2"""))
        b = ConfigurationBuilder(dict(section=dict(param=x)))
        params = b.build(y)
        assert params['section']['param'] == 2
        
    def test_overlay_2(self):
        x = parse(self.fd("""!spec\ntype: !!int "0"\ndescription:\nvalue: 1\n"""))
        y = parse(self.fd("""section:\n param: 2"""))
        z = parse(self.fd("""section:\n param: 3"""))
        b = ConfigurationBuilder(dict(section=dict(param=x)))
        params = b.build(y, z)
        assert params['section']['param'] == 3

    def test_overlay_3(self):
        x = parse(self.fd("""!spec\ntype: !!int "0"\ndescription:\nvalue: !optional\n"""))
        b = ConfigurationBuilder(dict(section=dict(param=x)))
        params = b.build()
        assert 'param' not in params['section']
        
    def test_validator_no_errors(self):
        x = parse(self.fd("""!spec\ntype: !!int "0"\ndescription:\nvalue: !required\n"""))
        y = parse(self.fd("""section:\n param: 1"""))
        b = ConfigurationBuilder(dict(section=dict(param=x)))
        params = b.build(y)
        assert params['section']['param'] == 1

        errors = b.validate(params)
        assert not errors

    def test_validator_required(self):
        x = parse(self.fd("""!spec\ntype: !!int "0"\ndescription:\nvalue: !required\n"""))
        b = ConfigurationBuilder(dict(section=dict(param=x)))
        params = b.build()
        assert params['section']['param'] != 1
        errors = b.validate(params)
        assert ('section', 'param') in errors
        assert isinstance(errors[('section', 'param')], Requirement)
        
    def test_validator_type_error(self):
        x = parse(self.fd("""!spec\ntype: !!int "0"\ndescription:\nvalue: !required\n"""))
        y = parse(self.fd("""section:\n param: foo"""))
        b = ConfigurationBuilder(dict(section=dict(param=x)))
        params = b.build(y)
        assert params['section']['param'] == 'foo'

        errors = b.validate(params)
        assert errors
        assert ('section', 'param') in errors
        assert isinstance(errors[('section', 'param')], TypeError)

class TestConfigParserFacade(BaseTest):
    def test1(self):
        v = parse(self.open("spec.yaml"))
        assert isinstance(v, ConfigurationDescriptor)
        c = ConfigurationBuilder(v).build()
        f = ConfigParserFacade(v, c)
        
        def compare(method, section, key):
            assert f.has_section(section)
            assert f.has_option(section, key)
            assert key in f.options(section)
            assert key in dict(f.items(section))
            assert method(section, key) == c.value(section, key), (section, key)
        
        compare(f.get, "email", "from_address")
        compare(f.getint, "tests", "int")
        compare(f.getboolean, "tests", "bool")
        compare(f.getfloat, "tests", "float")
        
