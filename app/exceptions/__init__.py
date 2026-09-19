# Response code blocks: 1-99 basic, 100-199 user, 200-299 dog,
# 300-399 file, 10000+ invalid argument
from .base import ErrorWithResponseCode
from .basic import *
from .invalid_argument import *
from .user import *
from .dog import *
from .file import *
