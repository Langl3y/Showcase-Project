from flask import g

from app.api.common.request import get_request_language


url_prefix = '/admin'


def before_request():
    g.lang = get_request_language().value
