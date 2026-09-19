from marshmallow import fields as mm_fields


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


class CustomString(mm_fields.String):
    pass
