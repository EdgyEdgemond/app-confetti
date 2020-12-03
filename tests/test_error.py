import pytest

from clt_util import error


class A404Error(error.NotFoundException):
    message = "a 404 message"


class A401Error(error.UnauthorisedException):
    message = "a 401 message"


class A400Error(error.BadRequestException):
    message = "a 400 message"


class A500Error(error.ServerException):
    message = "a 500 message"


@pytest.mark.parametrize("exc", [
    A404Error,
    A401Error,
    A400Error,
    A500Error,
])
def test_marshal(exc):
    e = exc("debug_message")

    assert e.marshal() == {
        "message": e.message,
        "debug_message": "debug_message",
    }
