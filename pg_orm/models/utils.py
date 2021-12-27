import inspect
import asyncio
import enum
from distutils.util import strtobool


def quote(arg=None):
    """Adds quotes to the given argument if the data type is str"""
    if arg is None:
        return ""
    try:
        return int(arg)
    except ValueError:
        try:
            return float(arg)
        except ValueError:
            try:
                return bool(strtobool(arg))
            except ValueError:
                return f"'{str(arg)}'"


def maybe_await(function, *args, **kwargs):
    if inspect.iscoroutinefunction(function):
        return asyncio.get_event_loop().run_until_complete(function(*args, **kwargs))
    else:
        return function(*args, **kwargs)


class QueryParamStyle(enum.Enum):
    qmark = "?"
    numeric = ":{number}"
    named = ":{name}"
    format = "%s"
    pyformat = "%({name})s"
    native_postgresql = "${number}"
