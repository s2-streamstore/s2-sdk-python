from functools import wraps
from inspect import isasyncgenfunction, iscoroutinefunction


class S2Error(Exception):
    """
    Base class for all S2 related exceptions.
    """


S2Error.__module__ = "streamstore"


def fallible(f):
    @wraps(f)
    def sync_wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            if isinstance(e, S2Error):
                raise e
            raise S2Error(e) from e

    @wraps(f)
    async def async_gen_wrapper(*args, **kwargs):
        try:
            async for val in f(*args, **kwargs):
                yield val
        except Exception as e:
            if isinstance(e, S2Error):
                raise e
            raise S2Error(e) from e

    @wraps(f)
    async def coro_wrapper(*args, **kwargs):
        try:
            return await f(*args, **kwargs)
        except Exception as e:
            if isinstance(e, S2Error):
                raise e
            raise S2Error(e) from e

    if iscoroutinefunction(f):
        return coro_wrapper
    elif isasyncgenfunction(f):
        return async_gen_wrapper
    else:
        return sync_wrapper
