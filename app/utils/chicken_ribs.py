class NamedObject:
    def __init__(self, name: str):
        self._name = name

    def __repr__(self):
        return self._name

    def __str__(self):
        return self._name

    def __bool__(self):
        return False


def classproperty(f):
    class _ClassProperty:
        def __init__(self, fget):
            self.fget = fget

        def __get__(self, obj, owner):
            return self.fget(owner)

    return _ClassProperty(f)
