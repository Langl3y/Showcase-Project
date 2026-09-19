import re


def camel_to_underscore(name: str) -> str:
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def underscore_to_camel(name: str) -> str:
    components = name.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def remove_prefix(text: str, prefix: str) -> str:
    if text.startswith(prefix):
        return text[len(prefix):]
    return text


def remove_suffix(text: str, suffix: str) -> str:
    if text.endswith(suffix):
        return text[:-len(suffix)]
    return text


def hide_text_default(text: str, start: int = 3, end: int = 3) -> str:
    if not text:
        return ''
    if len(text) <= start + end:
        return '*' * len(text)
    return text[:start] + '*' * (len(text) - start - end) + text[-end:]
