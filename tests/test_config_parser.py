from unittest import TestCase

from flask_rebar.config_parser import ConfigParser
from flask_rebar.config_parser import MissingConfiguration
from flask_rebar.config_parser import truthy


class TestTruthy(TestCase):
    def test_truthy_values(self):
        for val in (True, 'True', 'true', '1', 1):
            self.assertTrue(truthy(val))

    def test_falsey_values(self):
        for val in (False, 'False', 'false', '0', 0, None):
            self.assertFalse(truthy(val))


class TestConfigParser(TestCase):
    def test_resolve_from_source(self):
        parser = ConfigParser()
        parser.add_param('FOO')
        config = parser.resolve(
            sources=[
                {'FOO': 1}
            ]
        )
        self.assertEqual(config, {'FOO': 1})

    def test_fallback_to_depper_sources(self):
        parser = ConfigParser()
        parser.add_param('FOO')
        config = parser.resolve(
            sources=[
                {'BAR': 2},
                {'FOO': 1}
            ]
        )
        self.assertEqual(config, {'FOO': 1})

    def test_default_to_none(self):
        parser = ConfigParser()
        parser.add_param('FOO')
        config = parser.resolve(
            sources=[
                {'BAR': 2},
                {'BAR': 1}
            ]
        )
        self.assertEqual(config, {'FOO': None})

    def test_set_default(self):
        parser = ConfigParser()
        parser.add_param('FOO', default=3)
        config = parser.resolve(
            sources=[
                {'BAR': 2},
                {'BAR': 1}
            ]
        )
        self.assertEqual(config, {'FOO': 3})

    def test_coerce(self):
        parser = ConfigParser()
        parser.add_param('FOO', coerce=str)
        config = parser.resolve(
            sources=[
                {'FOO': 1}
            ]
        )
        self.assertEqual(config, {'FOO': '1'})

    def test_required(self):
        parser = ConfigParser()
        parser.add_param('FOO', required=True)
        with self.assertRaises(MissingConfiguration):
            parser.resolve(
                sources=[
                    {'BAR': 1}
                ]
            )
