import os
from unittest.case import TestCase

from pyyacc3.resolver import Resolver


class TestResolver(TestCase):

    def env(self, **kwargs):
        for k, v in kwargs.items():
            os.environ[k] = v
            self.addCleanup(lambda: os.environ.pop(k))

    def test_get_extra_overlays_1(self):
        r = Resolver(None, None)
        self.assertEqual(r.get_extra_overlays(), [])

    def test_get_extra_overlays_default(self):
        self.env(YACC__OVERLAY="{moo: 1}")
        r = Resolver(None, None)
        self.assertEqual(r.get_extra_overlays(), [dict(moo=1)])

    def test_get_file_overlay(self):
        self.env(YACC_RESOLVER__OVERLAYS="[bad.yaml]")
        r = Resolver(os.path.dirname(__file__), None)
        self.assertEqual(r.get_extra_overlays(), [{'afooadsf': {'bar': 'baz'}}])

    def test_get_file_overlay_not_found(self):
        self.env(YACC_RESOLVER__OVERLAYS="[bad.yaml]")
        r = Resolver("/", None)
        self.assertRaises(IOError, r.get_extra_overlays)
