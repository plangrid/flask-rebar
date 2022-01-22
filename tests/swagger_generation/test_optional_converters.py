import mock
import pytest
import unittest
from importlib import reload


# HAAAAACKS - using importlib.reload will invalidate pre-existing imports in other test modules,
# even when imported "as" something else..  so we'll just use pytest-order to ensure this test always runs LAST.
@pytest.mark.order(-1)
class TestOptionalConverters(unittest.TestCase):
    def test_optional_enum_converter(self):
        import flask_rebar.swagger_generation.marshmallow_to_swagger as _m_to_s

        # by default these should be there because tests are run with extras installed
        self.assertIsNotNone(_m_to_s.EnumField)
        self.assertIsNotNone(_m_to_s.EnumConverter)
        self.assertTrue(
            any(
                [type(conv) is _m_to_s.EnumConverter for conv in _m_to_s.ALL_CONVERTERS]
            )
        )
        full_len = len(_m_to_s.ALL_CONVERTERS)  # for an extra sanity check

        # simulate marshmallow_enum not installed:
        with mock.patch("marshmallow_enum.EnumField", new=None):
            reload(_m_to_s)
            self.assertIsNone(_m_to_s.EnumField)
            self.assertIsNone(_m_to_s.EnumConverter)
            self.assertFalse(
                any(
                    [
                        type(conv) is _m_to_s.EnumConverter
                        for conv in _m_to_s.ALL_CONVERTERS
                    ]
                )
            )
            self.assertEqual(len(_m_to_s.ALL_CONVERTERS), full_len - 1)
