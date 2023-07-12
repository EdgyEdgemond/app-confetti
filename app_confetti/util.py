import dataclasses
import os
from typing import Any, Callable

sentinel = object()


def env(key: str, convert: Callable = str, **kwargs) -> dataclasses.Field:
    """
    A factory around `dataclasses.field` that can be used to load or default
    an envvar. If you wish to load from an external source, do that first and
    inject it's values into os.environ before instantiating your
    config/settings class.

    Args:
        key: in the format of either KEY or KEY:DEFAULT
        convert: a function that accepts a string and returns a different type
        kwargs: any remaining kwargs for `dataclasses.field`

    Returns:
        dataclasses.field

    Raises:
        KeyError: in the event an envvar isn't found and doesn't have a default
    """
    key, partition, default = key.partition(":")

    # handle `KEY:` for default of empty string as partition returns empty string when partition is missing.
    if partition == "":
        default = sentinel

    def default_factory(key: str = key, default: Any = default, convert: Callable = convert) -> None:  # noqa: ANN401
        value = os.environ.get(key)
        if value is None:
            if default != sentinel:
                value = default
            else:
                raise KeyError(key)

        try:
            return convert(value)
        except ValueError as e:
            msg = f"{key} {e!s}"
            raise ValueError(msg) from e

    return dataclasses.field(default_factory=default_factory, **kwargs)
