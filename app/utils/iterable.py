from enum import EnumMeta
from typing import List


def list_enum_names(enum_class: EnumMeta) -> List[str]:
    return [e.name for e in enum_class]


def list_enum_values(enum_class: EnumMeta) -> List[str]:
    return [e.value for e in enum_class]
