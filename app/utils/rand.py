import secrets
import string


def new_hex_token(size: int = 32) -> str:
    return secrets.token_hex(size)


def new_verification_code(length: int = 6) -> str:
    return ''.join(secrets.choice(string.digits) for _ in range(length))
