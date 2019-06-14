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


@deprecated_parameters(
    old_param1="new_param1",  # rename with no predicted end-of-life version
    old_param2=("new_param2", "v99"),  # rename with predicted end-of-life version
    old_param3=("new_param3",),  # rename with a poorly formed tuple
    old_param4=("new_param4", None),  # rename with explicitly None end-of-life version
    old_param5=(None, "v99.5"),  # no rename with explicit end-of-life version
    old_param6=None,  # deprecated param with no replacement, no specific end-of-life-version
    old_param7=(None, None),  # same as 6, but for the truly pedantic
    old_param8=(),  # could imagine someone accidentally doing this.. :P
)
def _add(
    new_param1=0,
    new_param2=0,
    new_param3=0,
    new_param4=0,
    old_param5=0,
    old_param6=0,
    old_param7=0,
    old_param8=0,
):
    return (
        new_param1
        + new_param2
        + new_param3
        + new_param4
        + old_param5
        + old_param6
        + old_param7
        + old_param8
    )


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

        # with both (using poorly formed tuples)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = _add(old_param3=3, old_param4=4)
            self.assertEqual(result, 7)
            self.assertEqual(len(w), 2)
            msg1 = str(w[0].message)
            msg2 = str(w[1].message)
            self.assertTrue(
                ("old_param3" in msg1 and "old_param4" in msg2)
                or ("old_param3" in msg2 and "old_param4" in msg1)
            )
            self.assertIs(w[0].category, FutureWarning)

        # with no replacement but specific expiration
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = _add(new_param1=1, old_param5=5)
            self.assertEqual(result, 6)
            self.assertEqual(len(w), 1)
            msg = str(w[0].message)
            self.assertIn("old_param5 is deprecated", msg)
            self.assertIn("v99.5", msg)
            self.assertNotIn("new_param", msg)
            self.assertIs(w[0].category, FutureWarning)

        # with no replacement (specified as None)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = _add(new_param1=1, old_param5=5)
            self.assertEqual(result, 6)
            self.assertEqual(len(w), 1)
            msg = str(w[0].message)
            self.assertIn("old_param5 is deprecated", msg)
            self.assertIn("v99.5", msg)
            self.assertNotIn("new_param", msg)
            self.assertIs(w[0].category, FutureWarning)

        # with no replacement -- specified as explicit (None, None) and implicit ()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = _add(old_param7=7, old_param8=8)
            self.assertEqual(result, 15)
            self.assertEqual(len(w), 2)
            msgs = {str(w[0].message), str(w[1].message)}
            expected_msgs = {"old_param7 is deprecated", "old_param8 is deprecated"}
            self.assertEqual(expected_msgs, msgs)
            self.assertIn("v99.5", msg)
            self.assertNotIn("new_param", msg)

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
