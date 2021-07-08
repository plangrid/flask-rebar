import marshmallow_objects as mo


class NestedTitledModel(mo.NestedModel):
    """
    Use this class instead of mashmallow_object.NestedModel if you need to supply
    __swagger_title__ to override the default of {MyModelClass}Schema
    """

    def __init__(self, nested, title, **kwargs):
        super(NestedTitledModel, self).__init__(nested, **kwargs)
        self.schema.__swagger_title__ = title
