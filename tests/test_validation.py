from datetime import datetime
from unittest import TestCase

from marshmallow import Schema
from marshmallow import ValidationError
from marshmallow import fields
from werkzeug.datastructures import MultiDict

from flask_rebar import messages
from flask_rebar.validation import ActuallyRequireOnDumpMixin
from flask_rebar.validation import CommaSeparatedList
from flask_rebar.validation import DisallowExtraFieldsMixin
from flask_rebar.validation import QueryParamList


class DisallowExtraFieldsSchema(Schema, DisallowExtraFieldsMixin):
    a = fields.String()
    b = fields.String(load_from='c')


class TestDisallowExtraFieldsMixin(TestCase):

    def test_nominal(self):
        _, errors = DisallowExtraFieldsSchema(strict=True).dump({})
        self.assertEqual(errors, {})

    def test_unexpected_field(self):
        data, errs = DisallowExtraFieldsSchema().load({'foo': 'bar'})
        self.assertEqual(errs, {'_schema': [messages.unsupported_fields(['foo'])]})

    def test_respects_load_from_and_attribute(self):
        data, errors = DisallowExtraFieldsSchema().load({'c': 'bar'})
        self.assertEqual({}, errors)
        self.assertEqual(data, {'b': 'bar'})

    def test_respects_exclude(self):
        schema = DisallowExtraFieldsSchema(exclude=('a',))
        data, errors = schema.load({'a': 'yz'})
        self.assertEqual(errors, {})
        self.assertEqual(data, {})

    def test_doesnt_break_for_non_object_schema(self):
        data, errors = DisallowExtraFieldsSchema().load(['im not supposed to be a list :)'])
        self.assertEqual(errors, {'_schema': [fields.Field.default_error_messages['type']]})
        self.assertEqual(data, {})


class ActuallyRequireOnDumpMixinSchema(Schema, ActuallyRequireOnDumpMixin):
    optional = fields.Str()
    value_optional = fields.Str(required=True, allow_none=True)
    value_required = fields.Str(required=True, allow_none=False)
    validation_required = fields.DateTime(required=True, allow_none=False)


class RequireOutpuMixinTest(TestCase):

    def setUp(self):
        super(RequireOutpuMixinTest, self).setUp()
        self.schema = ActuallyRequireOnDumpMixinSchema(strict=True)
        self.data = {
            'value_required': 'abc',
            'value_optional': None,
            'validation_required': datetime.now(),
        }

    def test_nominal(self):
        self.schema.dump(self.data)

    def test_required_missing(self):
        del self.data['value_required']
        with self.assertRaises(ValidationError) as ctx:
            self.schema.dump(self.data)
        self.assertIn('value_required', ctx.exception.messages['_schema'][0])

    def test_required_none(self):
        self.data['value_required'] = None
        with self.assertRaises(ValidationError) as ctx:
            self.schema.dump(self.data)
        self.assertIn('value_required', ctx.exception.messages['_schema'][0])

    def test_value_optional_missing(self):
        del self.data['value_optional']
        with self.assertRaises(ValidationError) as ctx:
            self.schema.dump(self.data)
        self.assertIn('value_optional', ctx.exception.messages['_schema'][0])

    def test_validation_works(self):
        self.data['validation_required'] = '123'
        with self.assertRaises(ValidationError) as ctx:
            self.schema.dump(self.data)
        # it's some sort of date error
        self.assertIn('cannot be formatted as a datetime',
                      ctx.exception.messages['validation_required'][0])


class StringList(Schema):
    foos = CommaSeparatedList(fields.String())


class IntegerList(Schema):
    foos = CommaSeparatedList(fields.Integer())


class TestCommaSeparatedList(TestCase):
    def test_deserialize(self):
        data, _ = StringList().load({'foos': 'bar'})
        self.assertEqual(data['foos'], ['bar'])

        data, _ = StringList().load({'foos': 'bar,baz'})
        self.assertEqual(data['foos'], ['bar', 'baz'])

        data, _ = IntegerList().load({'foos': '1,2'})
        self.assertEqual(data['foos'], [1, 2])

    def test_serialize(self):
        data, _ = StringList().dump({'foos': ['bar']})
        self.assertEqual(data['foos'], 'bar')

        data, _ = StringList().dump({'foos': ['bar', 'baz']})
        self.assertEqual(data['foos'], 'bar,baz')

        data, _ = IntegerList().dump({'foos': [1, 2]})
        self.assertEqual(data['foos'], '1,2')

    def test_deserialize_errors(self):
        _, errs = IntegerList().load({'foos': '1,two'})
        self.assertEqual(errs, {
            'foos': {1: ['Not a valid integer.']}
        })

    def test_serialize_errors(self):
        _, errs = IntegerList().dump({'foos': [1, 'two']})
        self.assertEqual(errs, {
            # Marshmallow's fields.List formats the dump errors differently
            # than load :shrug:
            'foos': ['Not a valid integer.']
        })


class StringQuery(Schema):
    foos = QueryParamList(fields.String())


class IntegerQuery(Schema):
    foos = QueryParamList(fields.Integer())


class TestQueryParamList(TestCase):
    def test_deserialize(self):
        query = MultiDict([('foos', 'bar')])
        data, _ = StringQuery().load(query)
        self.assertEqual(data['foos'], ['bar'])

        query = MultiDict([('foos', 'bar'), ('foos', 'baz')])
        data, _ = StringQuery().load(query)
        self.assertEqual(data['foos'], ['bar', 'baz'])

        query = MultiDict([('foos', 1), ('foos', 2)])
        data, _ = IntegerQuery().load(query)
        self.assertEqual(data['foos'], [1, 2])

    def test_deserialize_errors(self):
        query = MultiDict([('foos', 1), ('foos', 'two')])
        _, errs = IntegerQuery().load(query)
        self.assertEqual(errs, {
            'foos': {1: ['Not a valid integer.']}
        })
