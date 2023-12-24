import enum

from flask_rebar.swagger_generation import swagger_words as sw
from werkzeug.routing import BaseConverter
from werkzeug.routing import ValidationError


class TodoType(str, enum.Enum):
    user = "user"
    group = "group"


class TodoTypeConverter(BaseConverter):
    def to_python(self, value):
        try:
            return TodoType(value)
        except ValueError:
            raise ValidationError()

    def to_url(self, obj):
        return obj.value

    @staticmethod
    def to_swagger():
        return {
            sw.type_: sw.string,
            sw.enum: [t.value for t in TodoType],
        }
