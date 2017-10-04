import unittest

import marshmallow as m
from marshmallow import validate as v

from plangrid.flask_toolbox.framing.marshmallow_to_jsonschema import ALL_CONVERTERS, OUT
from plangrid.flask_toolbox.framing.marshmallow_to_jsonschema import ConverterRegistry
from plangrid.flask_toolbox.framing.marshmallow_to_jsonschema import IN
from plangrid.flask_toolbox.validation import CommaSeparatedList
from plangrid.flask_toolbox.validation import QueryParamList
from plangrid.flask_toolbox.validation import DisallowExtraFieldsMixin


class TestConverterRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = ConverterRegistry()
        self.registry.register_types(ALL_CONVERTERS)

    def test_primitive_types(self):
        for field, result in [
            (m.fields.Integer(), {'type': 'integer'}),
            (m.fields.String(), {'type': 'string'}),
            (m.fields.Number(), {'type': 'number'}),
            (m.fields.DateTime(), {'type': 'string', 'format': 'date-time'}),
            (m.fields.Date(), {'type': 'string', 'format': 'date'}),
            (m.fields.UUID(), {'type': 'string', 'format': 'uuid'}),
            (m.fields.Boolean(), {'type': 'boolean'}),
            (m.fields.Integer(missing=5), {'type': 'integer', 'default': 5}),
            (m.fields.Integer(allow_none=True), {'type': 'integer', 'x-nullable': True}),
            (m.fields.List(m.fields.Integer()), {'type': 'array', 'items': {'type': 'integer'}}),
            (m.fields.List(m.fields.Integer), {'type': 'array', 'items': {'type': 'integer'}}),
            (m.fields.Integer(description='blam!'), {'type': 'integer', 'description': 'blam!'}),
            (QueryParamList(m.fields.Integer()), {'type': 'array', 'items': {'type': 'integer'}, 'collectionFormat': 'multi'}),
            (CommaSeparatedList(m.fields.Integer()), {'type': 'array', 'items': {'type': 'integer'}, 'collectionFormat': 'csv'}),
            (m.fields.Integer(validate=v.Range(min=1)), {'type': 'integer', 'minimum': 1}),
            (m.fields.Integer(validate=v.Range(max=9)), {'type': 'integer', 'maximum': 9}),
            (m.fields.List(m.fields.Integer(), validate=v.Length(min=1)), {'type': 'array', 'items': {'type': 'integer'}, 'minItems': 1}),
            (m.fields.List(m.fields.Integer(), validate=v.Length(max=9)), {'type': 'array', 'items': {'type': 'integer'}, 'maxItems': 9}),
            (m.fields.String(validate=v.Length(min=1)), {'type': 'string', 'minLength': 1}),
            (m.fields.String(validate=v.Length(max=9)), {'type': 'string', 'maxLength': 9}),
            (m.fields.String(validate=v.OneOf(['a', 'b'])), {'type': 'string', 'enum': ['a', 'b']}),
            (m.fields.Dict(), {'type': 'object'}),
        ]:
            class Foo(m.Schema):
                a = field

            schema = Foo()
            json_schema = self.registry.convert(schema)

            self.assertEqual(
                json_schema,
                {
                    'type': 'object',
                    'title': 'Foo',
                    'properties': {
                        'a': result
                    }
                }
            )

    def test_dump_to(self):
        class Foo(m.Schema):
            a = m.fields.Integer(dump_to='b', required=True)

        schema = Foo()
        json_schema = self.registry.convert(schema)

        self.assertEqual(
            json_schema,
            {
                'type': 'object',
                'title': 'Foo',
                'properties': {
                    'b': {'type': 'integer'}
                },
                'required': ['b']
            }
        )

    def test_load_from(self):
        registry = ConverterRegistry(direction=IN)
        registry.register_types(ALL_CONVERTERS)

        class Foo(m.Schema):
            a = m.fields.Integer(load_from='b', required=True)

        schema = Foo()
        json_schema = registry.convert(schema)

        self.assertEqual(
            json_schema,
            {
                'type': 'object',
                'title': 'Foo',
                'properties': {
                    'b': {'type': 'integer'}
                },
                'required': ['b']
            }
        )

    def test_required(self):
        class Foo(m.Schema):
            a = m.fields.Integer(required=True)

        schema = Foo()
        json_schema = self.registry.convert(schema)

        self.assertEqual(
            json_schema,
            {
                'type': 'object',
                'title': 'Foo',
                'properties': {
                    'a': {'type': 'integer'}
                },
                'required': ['a']
            }
        )

    def test_object_description(self):
        class Foo(m.Schema):
            """I'm the description!"""
            a = m.fields.Integer()

        schema = Foo()
        json_schema = self.registry.convert(schema)

        self.assertEqual(
            json_schema,
            {
                'type': 'object',
                'title': 'Foo',
                'description': "I'm the description!",
                'properties': {
                    'a': {'type': 'integer'}
                }
            }
        )

    def test_nested(self):
        class Bar(m.Schema):
            a = m.fields.Integer()

        class Foo(m.Schema):
            a = m.fields.Nested(Bar)

        schema = Foo()
        json_schema = self.registry.convert(schema)

        self.assertEqual(
            json_schema,
            {
                'type': 'object',
                'title': 'Foo',
                'properties': {
                    'a': {
                        'type': 'object',
                        'title': 'Bar',
                        'properties': {
                            'a': {'type': 'integer'}
                        }
                    }
                }
            }
        )

    def test_many(self):
        class Foo(m.Schema):
            a = m.fields.Integer()

        schema = Foo(many=True)
        json_schema = self.registry.convert(schema)

        self.assertEqual(
            json_schema,
            {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'title': 'Foo',
                    'properties': {
                        'a': {'type': 'integer'}
                    }
                }
            }
        )

    def test_nested_many(self):
        class Bar(m.Schema):
            a = m.fields.Integer()

        class Foo(m.Schema):
            a = m.fields.Nested(Bar, many=True)

        schema = Foo()
        json_schema = self.registry.convert(schema)

        self.assertEqual(
            json_schema,
            {
                'type': 'object',
                'title': 'Foo',
                'properties': {
                    'a': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'title': 'Bar',
                            'properties': {
                                'a': {'type': 'integer'}
                            }
                        }
                    }
                }
            }
        )

    def test_method(self):
        class Foo(m.Schema):
            a = m.fields.Method(
                serialize='_get_on_dump',
                deserialize='_get_on_load'
            )

            def _get_on_dump(self, obj):
                pass
            _get_on_dump.__rtype__ = 'string'

            def _get_on_load(self, val):
                pass
            _get_on_load.__rtype__ = 'integer'

        for direction, expected_type in [(OUT, 'string'), (IN, 'integer')]:
            registry = ConverterRegistry(direction=direction)
            registry.register_types(ALL_CONVERTERS)
            schema = Foo()
            json_schema = registry.convert(schema)

            self.assertEqual(
                json_schema,
                {
                    'type': 'object',
                    'title': 'Foo',
                    'properties': {
                        'a': {'type': expected_type}
                    }
                }
            )

    def test_function(self):
        def _get_on_dump(obj):
            pass
        _get_on_dump.__rtype__ = 'string'

        def _get_on_load(val):
            pass
        _get_on_load.__rtype__ = 'integer'

        class Foo(m.Schema):
            a = m.fields.Function(
                serialize=_get_on_dump,
                deserialize=_get_on_load
            )

        for direction, expected_type in [(OUT, 'string'), (IN, 'integer')]:
            registry = ConverterRegistry(direction=direction)
            registry.register_types(ALL_CONVERTERS)
            schema = Foo()
            json_schema = registry.convert(schema)

            self.assertEqual(
                json_schema,
                {
                    'type': 'object',
                    'title': 'Foo',
                    'properties': {
                        'a': {'type': expected_type}
                    }
                }
            )

    def test_inheritance(self):
        class Foo(m.Schema):
            a = m.fields.Integer()

        class Bar(Foo):
            b = m.fields.Integer()

        schema = Bar()
        json_schema = self.registry.convert(schema)

        self.assertEqual(
            json_schema,
            {
                'type': 'object',
                'title': 'Bar',
                'properties': {
                    'a': {'type': 'integer'},
                    'b': {'type': 'integer'}
                }
            }
        )

    def test_additional_properties(self):
        class Foo(DisallowExtraFieldsMixin, m.Schema):
            a = m.fields.Integer()

        schema = Foo()
        json_schema = self.registry.convert(schema)

        self.assertEqual(
            json_schema,
            {
                'type': 'object',
                'title': 'Foo',
                'properties': {
                    'a': {'type': 'integer'}
                },
                'additionalProperties': False
            }
        )


if __name__ == '__main__':
    unittest.main()
