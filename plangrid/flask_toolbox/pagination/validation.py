from flask import g
from marshmallow import fields, ValidationError

from plangrid.flask_toolbox import messages


class USE_APPLICATION_DEFAULT(object):
    pass


class Skip(fields.Integer):
    ERROR_MSG = messages.invalid_skip_value

    def __init__(self, default=0, **kwargs):
        # "missing" is used on deserialize
        super(Skip, self).__init__(default=default, missing=default, **kwargs)

    def _deserialize(self, val, attr, obj):
        try:
            val = int(val)
        except ValueError:
            raise ValidationError(self.ERROR_MSG)
        return super(Skip, self)._deserialize(val, attr, obj)

    def _serialize(self, val, attr, obj):
        try:
            val = int(val)
        except ValueError:
            raise ValidationError(self.ERROR_MSG)
        return super(Skip, self)._serialize(val, attr, obj)

    def _validate(self, val):
        if val < 0:
            raise ValidationError(self.ERROR_MSG)
        return super(Skip, self)._validate(val)


class Limit(fields.Integer):
    ERROR_MSG = messages.invalid_limit_value

    def __init__(self, default=USE_APPLICATION_DEFAULT, **kwargs):
        super(Limit, self).__init__(missing=default, **kwargs)

    def _deserialize(self, val, attr, obj):
        if isinstance(val, USE_APPLICATION_DEFAULT):
            val = g.pagination_limit_max
        try:
            val = int(val)
        except ValueError:
            raise ValidationError(self.ERROR_MSG)
        return super(Limit, self)._deserialize(val, attr, obj)

    def _serialize(self, val, attr, obj):
        try:
            val = int(val)
        except ValueError:
            raise ValidationError(self.ERROR_MSG)
        return super(Limit, self)._serialize(val, attr, obj)

    def _validate(self, val):
        if val <= 0:
            raise ValidationError(self.ERROR_MSG)
        limit_max = g.pagination_limit_max
        if val > limit_max:
            raise ValidationError(messages.limit_over_max(limit_max))
        return super(Limit, self)._validate(val)
