#!/usr/bin/env python3
"""Convert the flask-restx Swagger 2.0 docs into a single OpenAPI 3 file.

Usage: python3 scripts/gen_openapi.py [-o openapi.yaml]
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

BLUEPRINTS = ('frontend', 'admin')
OPENAPI_VERSION = '3.0.3'
SPEC_TITLE = 'Hieu Ho Python Assessment API'
SPEC_VERSION = '1.0.0'
SPEC_DESCRIPTION = (
    'Every response is wrapped in {code, data, message}. `code` is 0 on '
    'success and the HTTP status stays 200 for handled errors, so clients '
    'must branch on `code`, not on the status.\n\n'
    'Error codes are allocated per domain: 100-199 user, 200-299 dog, '
    '300-399 file, 2 invalid argument.'
)


def _retarget_refs(node: Any) -> Any:
    """Rewrite #/definitions/X refs to #/components/schemas/X."""
    if isinstance(node, dict):
        return {
            k: (v.replace('#/definitions/', '#/components/schemas/')
                if k == '$ref' and isinstance(v, str) else _retarget_refs(v))
            for k, v in node.items()
        }
    if isinstance(node, list):
        return [_retarget_refs(i) for i in node]
    return node


def _convert_parameter(param: dict) -> dict:
    """Swagger 2 parameter -> OpenAPI 3 parameter."""
    schema_keys = ('type', 'format', 'enum', 'default', 'items',
                   'minimum', 'maximum', 'pattern')
    out = {k: v for k, v in param.items() if k not in schema_keys}
    schema = {k: v for k, v in param.items() if k in schema_keys}
    # OpenAPI 3 has no `file` type
    if schema.get('type') == 'file':
        schema = {'type': 'string', 'format': 'binary'}
    out['schema'] = schema or {'type': 'string'}
    out.pop('collectionFormat', None)
    return out


def _convert_operation(op: dict, consumes: list, produces: list) -> dict:
    out = {k: v for k, v in op.items()
           if k not in ('parameters', 'responses', 'consumes', 'produces')}
    consumes = op.get('consumes') or consumes or ['application/json']
    produces = op.get('produces') or produces or ['application/json']

    params, body, form = [], None, {}
    for param in op.get('parameters', []):
        location = param.get('in')
        if location == 'body':
            body = param
        elif location == 'formData':
            form[param['name']] = (
                {'type': 'string', 'format': 'binary'}
                if param.get('type') == 'file'
                else {'type': param.get('type', 'string')}
            )
            if param.get('description'):
                form[param['name']]['description'] = param['description']
        else:
            params.append(_convert_parameter(param))
    if params:
        out['parameters'] = params

    if body is not None:
        out['requestBody'] = {
            'required': body.get('required', False),
            'content': {ct: {'schema': body.get('schema', {})} for ct in consumes},
        }
        if body.get('description'):
            out['requestBody']['description'] = body['description']
    elif form:
        out['requestBody'] = {
            'required': True,
            'content': {'multipart/form-data': {
                'schema': {'type': 'object', 'properties': form}}},
        }

    responses = {}
    for status, resp in (op.get('responses') or {}).items():
        new = {'description': resp.get('description') or ''}
        if 'schema' in resp:
            new['content'] = {ct: {'schema': resp['schema']} for ct in produces}
        if 'headers' in resp:
            new['headers'] = {
                name: {'description': h.get('description', ''),
                       'schema': {'type': h.get('type', 'string')}}
                for name, h in resp['headers'].items()
            }
        responses[str(status)] = new
    out['responses'] = responses or {'200': {'description': 'Success'}}
    return out


def convert(swagger: dict, base_path: str) -> tuple[dict, dict, dict]:
    """Return (paths, schemas, security_schemes)."""
    consumes, produces = swagger.get('consumes', []), swagger.get('produces', [])
    methods = ('get', 'post', 'put', 'patch', 'delete', 'head', 'options')

    paths = {}
    for path, item in swagger.get('paths', {}).items():
        converted = {}
        shared = [_convert_parameter(p) for p in item.get('parameters', [])
                  if p.get('in') != 'body']
        for key, value in item.items():
            if key in methods:
                converted[key] = _convert_operation(value, consumes, produces)
            elif key != 'parameters':
                converted[key] = value
        if shared:
            converted['parameters'] = shared
        paths[f"{base_path.rstrip('/')}{path}"] = converted

    schemes = {}
    for name, defn in (swagger.get('securityDefinitions') or {}).items():
        scheme = dict(defn)
        scheme.pop('description', None) if not scheme.get('description') else None
        schemes[name] = scheme

    return (_retarget_refs(paths),
            _retarget_refs(swagger.get('definitions', {})),
            schemes)


def build(app) -> dict:
    client = app.test_client()
    paths: dict = {}
    schemas: dict = {}
    security: dict = {}
    tags: list = []
    seen_tags: set = set()

    for blueprint in BLUEPRINTS:
        resp = client.get(f'/{blueprint}/swagger.json')
        if resp.status_code != 200:
            raise SystemExit(f'{blueprint}: swagger.json returned {resp.status_code}')
        swagger = json.loads(resp.data)
        bp_paths, bp_schemas, bp_security = convert(
            swagger, swagger.get('basePath', f'/{blueprint}'))

        clash = set(paths) & set(bp_paths)
        if clash:
            raise SystemExit(f'path collision between blueprints: {sorted(clash)}')
        paths.update(bp_paths)
        schemas.update(bp_schemas)
        security.update(bp_security)
        for tag in swagger.get('tags', []):
            if tag['name'] not in seen_tags:
                seen_tags.add(tag['name'])
                tags.append(tag)

    spec = {
        'openapi': OPENAPI_VERSION,
        'info': {'title': SPEC_TITLE, 'version': SPEC_VERSION,
                 'description': SPEC_DESCRIPTION},
        'servers': [{'url': 'http://127.0.0.1:5000', 'description': 'local'}],
        'tags': tags,
        'paths': paths,
        'components': {'schemas': schemas, 'securitySchemes': security},
    }
    if security:
        spec['security'] = [{name: []} for name in security]
    return spec


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-o', '--output', default='openapi.yaml',
                        help='where to write the spec (default: openapi.yaml)')
    args = parser.parse_args()

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from app import create_app

    spec = build(create_app())

    try:
        from openapi_spec_validator import validate
        validate(spec)
        verdict = 'valid'
    except ImportError:
        verdict = 'not validated (pip install openapi-spec-validator)'

    Path(args.output).write_text(
        yaml.safe_dump(spec, sort_keys=False, allow_unicode=True, width=100))
    print(f'{args.output}: OpenAPI {OPENAPI_VERSION}, {len(spec["paths"])} paths, '
          f'{len(spec["components"]["schemas"])} schemas - {verdict}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
