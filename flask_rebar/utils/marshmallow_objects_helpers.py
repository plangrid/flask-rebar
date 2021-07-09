try:
    import marshmallow_objects as mo

    MARSHMALLOW_OBJECTS = True
except ImportError:
    MARSHMALLOW_OBJECTS = False


def get_marshmallow_objects_schema(model):
    if MARSHMALLOW_OBJECTS and (
        isinstance(model, mo.Model) or issubclass(model, mo.Model)
    ):
        return model.__get_schema_class__()
    else:
        return None


if MARSHMALLOW_OBJECTS:

    class NestedTitledModel(mo.NestedModel):
        """
        Use this class instead of mashmallow_object.NestedModel if you need to supply
        __swagger_title__ to override the default of {MyModelClass}Schema
        """

        def __init__(self, nested, title, **kwargs):
            super(NestedTitledModel, self).__init__(nested, **kwargs)
            self.schema.__swagger_title__ = title


else:

    class NestedTitledModel(object):
        """
        This version of NestedTitledModel will exist if marshmallow-objects is not present
        """

        def __init__(self):
            raise ImportError(
                "To use NestedTitledModel you must install marshmallow-objects"
            )
