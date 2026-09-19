from typing import Any, Optional, Dict


class _ErrorWithResponseCodeMeta(type):
    _response_code_to_error_ = {}

    def __new__(mcs, name, bases, dct):
        cls = super().__new__(mcs, name, bases, dct)

        rc_attr = 'response_code'
        r_code = getattr(cls, rc_attr, None)
        if r_code is not None and isinstance(r_code, int):
            if not isinstance(r_code, (int, property)):
                raise TypeError(f'invalid response code: {r_code!r}')
            if not r_code:
                raise ValueError('response code must be non-zero')
            code_to_error = mcs._response_code_to_error_
            if r_code in code_to_error:
                if rc_attr in dct:
                    raise ValueError(
                        f'response code {r_code} is already registered to '
                        f'{code_to_error[r_code]!r}')
            else:
                code_to_error[r_code] = cls

        cls._message_title = name.replace('_', ' ')

        return cls

    @classmethod
    def response_code_to_class(mcs, code: int
                               ) -> Optional['_ErrorWithResponseCodeMeta']:
        return mcs._response_code_to_error_.get(code)

    @classmethod
    def get_all_response_codes(mcs) -> Dict[int, Dict[str, str]]:
        code_to_cls = mcs._response_code_to_error_
        return {
            code: {
                'module': cls.__module__,
                'class_name': cls.__name__,
                'message_template': cls.message_template,
                'message_title': cls._message_title
            }
            for code, cls in sorted(code_to_cls.items(), key=lambda x: x[0])
        }


class ErrorWithResponseCode(Exception, metaclass=_ErrorWithResponseCodeMeta):
    response_code: int = None
    message_template: str = '%(title)s: %(data)r'
    _message_title: str

    def __init__(self, data: Any = None, message: str = None, **kwargs: Any):
        if not data:
            self._data = {}
        elif isinstance(data, list) or isinstance(data, dict):
            self._data = data
        else:
            self._data = {'data': data}
        self._message = message
        self._kwargs = kwargs

    def __repr__(self):
        return f'{type(self).__name__}' \
               f'({self._data!r}, message={self.message!r})'

    @property
    def data(self):
        return self._data

    @property
    def code(self):
        return self.response_code

    @property
    def message(self) -> str:
        message = self._message
        if message is not None:
            return message
        kwargs = dict(
            title=self._message_title,
            data=self._data
        )
        kwargs.update(self._kwargs)
        try:
            return self.message_template % kwargs
        except (TypeError, KeyError):
            return self.message_template


class MultipleErrors(ErrorWithResponseCode):
    response_code = 9999
    message_template = "Multiple errors occurred"

    def __init__(self, errors: list):
        self.errors = errors
        self._data = [
            {
                "code": e.code,
                "message": e.message,
                "data": e.data
            } for e in errors
        ]
        self._message = None
        self._kwargs = {}
