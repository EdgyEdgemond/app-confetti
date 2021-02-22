import ast
import dataclasses
import os


def str_to_literal(val):
    """
    Construct an object literal from a str, but leave other types untouched
    """
    if isinstance(val, str):
        try:
            return ast.literal_eval(val)
        except ValueError:
            pass
    return val


def env(key, convert=str, **kwargs):
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
    key, _, default = key.partition(":")

    def default_factory(key=key, default=default, convert=convert):
        _special = {
            "__NONE__": None,
            "__EMPTY__": "",
            "__TRUE__": True,
            "__FALSE__": False,
        }
        value = os.environ.get(key)
        if value is None:
            if default:
                value = default
            else:
                raise KeyError(key)

        if value in _special:
            return _special[value]

        return convert(value)

    return dataclasses.field(default_factory=default_factory, **kwargs)
