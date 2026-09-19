from enum import Enum, EnumMeta
from typing import Iterable, Union

from marshmallow import fields as mm_fields

from ...exceptions import InvalidArgument
from ...utils import list_enum_names, list_enum_values

PageField = mm_fields.Integer(
    required=False,
    missing=1,
    metadata={'desc': 'Page number, starting from 1', 'example': 1}
)

LimitField = mm_fields.Integer(
    required=False,
    missing=20,
    metadata={'desc': 'Items per page', 'example': 20}
)


class Object(mm_fields.Field):
    pass


class DecimalType(mm_fields.Decimal):
    pass


class EnumType(mm_fields.Field):
    pass


class EnumField(mm_fields.String):
    def __init__(self, enum: Union[EnumMeta, Iterable[str]],
                 enum_by_value: bool = False, **kwargs):
        if isinstance(enum, EnumMeta):
            enum_class = enum
            self.enum_by_value = enum_by_value
            if not enum_by_value:
                choices = list_enum_names(enum)
            else:
                choices = list_enum_values(enum)
            choices_set = None
        else:
            enum_class = None
            choices = list(enum)
            choices_set = frozenset(choices)

        self._enum_class = enum_class
        self._choices = choices
        self._choices_set = choices_set

        metadata = dict(kwargs.pop('metadata', None) or {})
        metadata.setdefault('desc', f'choices={choices}')
        super().__init__(metadata=metadata, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs
                     ) -> Union[Enum, str, None]:
        value = super()._deserialize(value, attr, data, **kwargs)
        if not self.required and not value:
            return None
        if (enum_cls := self._enum_class) is not None:
            if self.enum_by_value:
                try:
                    value = enum_cls(value)
                except ValueError as exc:
                    raise InvalidArgument(
                        message=f'{value!r} is not a valid {enum_cls} value'
                    ) from exc
            else:
                if not isinstance((v := getattr(enum_cls, value, None)), enum_cls):
                    raise InvalidArgument(
                        message=f'{value!r} is not a valid {enum_cls}')
                value = v
        elif value not in self._choices_set:
            raise InvalidArgument(message=f'invalid enum: {value!r}')
        return value


class CustomString(mm_fields.String):
    pass
