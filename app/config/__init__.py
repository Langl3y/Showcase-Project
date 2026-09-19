from pathlib import Path
from typing import Dict, Any
import os
from .common import ConfigDict


root_path: Path = Path(__file__).parent
config: Dict[str, Any] = {}


def _load_py_file(filename: str, *, optional: bool = False):
    file_path = root_path.joinpath(filename)
    if not file_path.exists():
        if optional:
            return
        raise IOError(f'{str(file_path)!r} does not exists')

    c = {
        '__file__': str(file_path),
        '__name__': f'app.config.{filename.rstrip(".py")}',
    }
    exec(compile(file_path.read_text(), str(file_path), 'exec'), c)

    global config
    for k, v in c.items():
        cur_v = config.get(k, None)
        if not k.isupper():
            continue
        if (isinstance(cur_v, ConfigDict) and cur_v.values_replaceable
                and isinstance(v, dict)):
            cur_v.update(v)
        else:
            config[k] = v


_load_py_file('default.py')
if os.environ.get('TESTING') == '1' or os.environ.get('PYTEST_CURRENT_TEST'):
    _load_py_file('testing.py', optional=True)
_load_py_file('environment.py', optional=True)
