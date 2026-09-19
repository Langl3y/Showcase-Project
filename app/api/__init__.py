# -*- coding: utf-8 -*-

import json
from importlib import import_module
from pkgutil import walk_packages

from flask import Blueprint, Flask, make_response, request
from flask_restx import Namespace
from pygtrie import StringTrie

from app.api.common import Api, JsonEncoder
from app.config import config

from . import admin, frontend

_before_request = StringTrie(separator='/')


def init_app(app: Flask):
    exposed_docs = set(config.get('EXPOSED_DOCS', ()))
    test_token = config.get('DEFAULT_TEST_TOKEN', '')

    def output_json(data, code, headers=None):
        _resp = make_response(json.dumps(data, cls=JsonEncoder), code)
        _resp.headers.extend(headers or {})
        return _resp

    def import_sub_mods(_mod, _url_prefix, _api):
        for _, _mod_name, _is_pkg in walk_packages(_mod.__path__):
            _sub_mod = import_module(f'{_mod.__name__}.{_mod_name}')
            _sub_url_prefix = (getattr(_sub_mod, 'url_prefix', '')
                               or f'/{_mod_name.replace("_", "-")}')
            _sub_url_prefix_full = f'{_url_prefix}{_sub_url_prefix}'
            _ns = getattr(_sub_mod, 'ns', None)
            if _ns is not None:
                _api.add_namespace(_ns, path=_sub_url_prefix_full)

            if _is_pkg:
                import_sub_mods(_sub_mod, _sub_url_prefix_full, _api)

    for mod in [frontend, admin]:
        mod_name = mod.__name__.split('.')[-1]
        url_prefix = (getattr(mod, 'url_prefix', '')
                      or f'/{mod_name.replace("_", "-")}')
        bp = Blueprint(mod_name, __name__, url_prefix=url_prefix)
        api = Api(bp,
                  title=f'APIs ({url_prefix})',
                  doc='/swagger/' if mod_name in exposed_docs else False,
                  version=getattr(mod, 'api_version', '1.0'),
                  security=['Authorization'])
        ns = Namespace(mod_name,
                       authorizations={
                           'Authorization': {
                                'type': 'apiKey',
                                'in': 'header',
                                'name': 'AUTHORIZATION',
                                'description': (f'test token: {test_token}'
                                                if test_token else '')
                            }
                       })
        api.add_namespace(ns)
        app.register_blueprint(bp)

        before_request = getattr(mod, 'before_request', None)
        if callable(before_request):
            _before_request[url_prefix] = before_request

        mod.api = api
        mod.ns = ns

        api.representation('application/json')(output_json)
        import_sub_mods(mod, '', api)

    @app.before_request
    def app_before_request():
        _handler = _before_request.longest_prefix(request.full_path).value
        if not _handler:
            return

        _handler()
