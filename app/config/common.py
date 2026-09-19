from typing import Mapping


class ConfigDict(dict):

    def __init__(self, items: Mapping, **kwargs):
        self._kwargs = kwargs
        super().__init__(items)

    @property
    def values_replaceable(self):
        return self._kwargs.get('values_replaceable', False)


def values_replaceable(items: Mapping):
    return ConfigDict(items, values_replaceable=True)
