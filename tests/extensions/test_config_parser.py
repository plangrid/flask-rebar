from unittest import TestCase

from plangrid.flask_toolbox.extensions.config_parser import ConfigParser
from plangrid.flask_toolbox.extensions.config_parser import MissingConfiguration


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
