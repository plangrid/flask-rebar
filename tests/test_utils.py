"""
    Test Generic Utilities
    ~~~~~~~~~~~~~~~~~~~~~~

    Tests for the generic (i.e., non-request) utilities.

    :copyright: Copyright 2019 Autodesk, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
import unittest
import warnings
from flask_rebar.utils import deprecated_parameters


@deprecated_parameters(old_param1="new_param1", old_param2=("new_param2", "v99"))
def _add(new_param1=42, new_param2=99):
    return new_param1 + new_param2


@deprecated_parameters(
    warn_type=DeprecationWarning,
    old_param1="new_param1",
    old_param2=("new_param2", "v99"),
)
def _subtract(new_param1=42, new_param2=99):
    return new_param1 - new_param2


class TestParameterDeprecation(unittest.TestCase):
    def test_parameter_deprecation_none(self):
        """Function with deprecated params, called with new (or no) names used does not warn"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            # test with unnamed args
            result = _add(1, 2)
            self.assertEqual(result, 3)
            self.assertEqual(len(w), 0)
            # test with "new" named args
            result = _add(new_param1=3, new_param2=5)
            self.assertEqual(result, 8)
            self.assertEqual(len(w), 0)

    def test_parameter_deprecation_warnings(self):
        """Function with deprecated param names warns (with expiration version if specified)"""
        # without version spec
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = _add(old_param1=1, new_param2=2)
            self.assertEqual(result, 3)
            self.assertEqual(len(w), 1)
            self.assertIn("old_param1", str(w[0].message))
            self.assertNotIn("new_param2", str(w[0].message))
            self.assertIs(w[0].category, FutureWarning)

        # with version spec
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = _add(new_param1=1, old_param2=2)
            self.assertEqual(result, 3)
            self.assertEqual(len(w), 1)
            self.assertNotIn("old_param1", str(w[0].message))
            self.assertIn("new_param2", str(w[0].message))
            self.assertIn("v99", str(w[0].message))
            self.assertIs(w[0].category, FutureWarning)

        # with both
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = _add(old_param1=1, old_param2=2)
            self.assertEqual(result, 3)
            self.assertEqual(len(w), 2)
            msg1 = str(w[0].message)
            msg2 = str(w[1].message)
            self.assertTrue(
                ("old_param1" in msg1 and "old_param2" in msg2)
                or ("old_param1" in msg2 and "old_param2" in msg1)
            )
            self.assertIn("old_param1", str(w[0].message))
            self.assertIn("old_param2", str(w[1].message))
            self.assertIs(w[0].category, FutureWarning)

    def test_parameter_deprecation_warning_type(self):
        """Function with deprecated params supports specifying type of warning"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = _subtract(old_param1=50, new_param2=0)
            self.assertEqual(result, 50)
            self.assertEqual(len(w), 1)
            self.assertIs(w[0].category, DeprecationWarning)
