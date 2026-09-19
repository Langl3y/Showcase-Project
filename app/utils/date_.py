import time
from datetime import datetime, timezone, timedelta


def current_timestamp() -> int:
    return int(time.time())


def current_milliseconds() -> int:
    return int(time.time() * 1000)


def now() -> datetime:
    return datetime.now(timezone.utc)


def today() -> datetime:
    return datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0)


def timestamp_to_datetime(ts: int) -> datetime:
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def str_to_datetime(s: str, fmt: str = '%Y-%m-%d %H:%M:%S') -> datetime:
    return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)


def datetime_to_str(dt: datetime, fmt: str = '%Y-%m-%d %H:%M:%S') -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime(fmt)
