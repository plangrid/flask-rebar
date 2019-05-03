# hack to reintroduce backward-compatibility as SwaggerV2Generator used to live in swagger_generator.py

from flask_rebar.swagger_generation.swagger_generator_base import SwaggerGenerator
from flask_rebar.swagger_generation.swagger_generator_v2 import (
    SwaggerV2Generator,
)  # noqa
from flask_rebar.swagger_generation.swagger_generator_v3 import (
    SwaggerV3Generator,
)  # noqa
