import inspect
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


async def maybe_await(function, *args, **kwargs):
    if inspect.iscoroutine(function):
        return await function(*args, **kwargs)
    else:
        return function(*args, **kwargs)
