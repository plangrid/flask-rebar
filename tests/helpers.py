import pytest

from flask_rebar.compat import MARSHMALLOW_V2, MARSHMALLOW_V3


skip_if_marshmallow_not_v2 = pytest.mark.skipif(not MARSHMALLOW_V2, reason="Only applicable for Marshmallow version 2")
skip_if_marshmallow_not_v3 = pytest.mark.skipif(not MARSHMALLOW_V3, reason="Only applicable for Marshmallow version 3")
