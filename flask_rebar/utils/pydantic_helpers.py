# safe to import, even if pydantic isn't installed
from typing import Any, Optional
from marshmallow import Schema

try:
    import pydantic

    PYDANTIC = True
except ImportError:
    PYDANTIC = False


def get_pydantic_schema(model: Any) -> Optional[Schema]:
    if not PYDANTIC:
        return None
    model_class = model if isinstance(model, type) else type(model)
    if not issubclass(model_class, pydantic.BaseModel):
        return None

    # Imported lazily: flask_rebar.utils.pydantic imports from the flask_rebar
    # package, which is still mid-initialization when this module is first
    # loaded (flask_rebar/__init__.py -> request_utils -> here).
    from flask_rebar.utils.pydantic import schema_for

    return schema_for(model_class)
