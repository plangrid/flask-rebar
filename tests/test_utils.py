"""
    Test Generic Utilities
    ~~~~~~~~~~~~~~~~~~~~~~

    Tests for the generic (i.e., non-request) utilities.

    :copyright: Copyright 2019 Autodesk, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
import unittest
import warnings
from flask_rebar.utils.deprecation import deprecated, deprecated_parameters
from flask_rebar.utils.deprecation import config as deprecation_config


@deprecated_parameters(old_param1="new_param1", old_param2=("new_param2", "v99"))
def _add(new_param1=42, new_param2=99):
    return new_param1 + new_param2


@deprecated()
def _deprecated_func1():
    return 1


@deprecated("new_func2")
def _deprecated_func2():
    return 2


@deprecated(("new_func3", "99"))
def _deprecated_func3():
    return 3


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
            self.assertIs(w[0].category, FutureWarning)

    def test_parameter_deprecation_warning_type(self):
        """Deprecation supports specifying type of warning"""
        deprecation_config.warning_type = DeprecationWarning
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = _add(old_param1=50, new_param2=0)
            self.assertEqual(result, 50)
            self.assertEqual(len(w), 1)
            self.assertIs(w[0].category, DeprecationWarning)
        # reset (as deprecation_config is "global")
        deprecation_config.warning_type = FutureWarning


class TestFunctionDeprecation(unittest.TestCase):
    def test_bare_deprecation(self):
        """Deprecate function with no specified alternative"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = _deprecated_func1()
            self.assertEqual(result, 1)
            self.assertEqual(len(w), 1)
            self.assertEqual(str(w[0].message), "_deprecated_func1 is deprecated")

    def test_versionless_replacement(self):
        """Deprecate function with specified alternative, no end-of-life version"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = _deprecated_func2()
            self.assertEqual(result, 2)
            self.assertEqual(len(w), 1)
            self.assertIn("_deprecated_func2 is deprecated", str(w[0].message))
            self.assertIn("use new_func2", str(w[0].message))
            self.assertNotIn("version", str(w[0].message))

    def test_versioned_replacement(self):
        """Deprecate function with specified alternative, specified end-of-life version"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = _deprecated_func3()
            self.assertEqual(result, 3)
            self.assertEqual(len(w), 1)
            self.assertIn("_deprecated_func3 is deprecated", str(w[0].message))
            self.assertIn("use new_func3", str(w[0].message))
            self.assertIn("version 99", str(w[0].message))
