"""
Decorators for attaching OpenAPI vendor extensions to handler functions.

The :class:`SwaggerV3Generator` reads ``func.__openapi_extensions__`` and
deep-merges it into the operation object during spec generation. These
decorators are the supported way to populate that attribute.
"""

from typing import Any, Callable


def openapi_extension(key: str, value: Any) -> Callable[[Callable], Callable]:
    """Attach a single ``x-*`` vendor extension to a handler function.

    Example::

        @registry.handles(rule="/foo", method="GET")
        @openapi_extension("x-rate-limit", {"per-minute": 100})
        def get_foo():
            ...

    :param key: extension key (must start with ``x-``).
    :param value: extension value (any JSON-serializable structure).
    :raises ValueError: if ``key`` does not start with ``x-``.
    """
    if not key.startswith("x-"):
        raise ValueError(f"OpenAPI vendor extension keys must start with 'x-': {key!r}")

    def decorator(func: Callable) -> Callable:
        extensions = getattr(func, "__openapi_extensions__", None)
        if extensions is None:
            extensions = {}
            func.__openapi_extensions__ = extensions  # type: ignore[attr-defined]
        extensions[key] = value
        return func

    return decorator


def openapi_extensions(**kwargs: Any) -> Callable[[Callable], Callable]:
    """Attach multiple ``x-*`` vendor extensions to a handler function.

    Keyword argument names with underscores are converted to ``x-`` keys by
    replacing underscores with hyphens; pass already-prefixed keys via
    :func:`openapi_extension` instead when you need exact control.

    Example::

        @registry.handles(rule="/foo", method="GET")
        @openapi_extensions(
            **{"x-rate-limit": {"per-minute": 100}, "x-internal": True}
        )
        def get_foo():
            ...

    :raises ValueError: if any key does not start with ``x-``.
    """
    for key in kwargs:
        if not key.startswith("x-"):
            raise ValueError(
                f"OpenAPI vendor extension keys must start with 'x-': {key!r}"
            )

    def decorator(func: Callable) -> Callable:
        extensions = getattr(func, "__openapi_extensions__", None)
        if extensions is None:
            extensions = {}
            func.__openapi_extensions__ = extensions  # type: ignore[attr-defined]
        extensions.update(kwargs)
        return func

    return decorator
