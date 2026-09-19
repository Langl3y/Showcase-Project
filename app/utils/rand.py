import secrets
import string

from .date_ import today


def new_hex_token(size: int = 32) -> str:
    return secrets.token_hex(size)


def new_verification_code(length: int = 6) -> str:
    return ''.join(secrets.choice(string.digits) for _ in range(length))


def new_file_key(length: int = 32, suffix: str = '') -> str:
    key = f'{today().strftime("%Y-%m-%d")}/{secrets.token_hex(length // 2).upper()}'
    if suffix:
        key = f"{key}.{suffix.lstrip('.')}"
    return key


def new_custom_file_key(folder_name: str, length: int = 32,
                        suffix: str = '') -> str:
    key = f'{folder_name}/{secrets.token_hex(length // 2).upper()}'
    if suffix:
        key = f'{key}{suffix}'
    return key
