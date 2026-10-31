import collections.abc
import typing


def thaw(value: object) -> typing.Any:  # noqa: ANN401 - the caller indexes the plain copy
    """A deep copy of a frozen fixture as the plain dicts and lists the product code is given."""
    if isinstance(value, collections.abc.Mapping):
        return {key: thaw(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [thaw(item) for item in value]
    return value
