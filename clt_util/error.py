class HttpException(Exception):
    """
    A base exception designed to support all API error handling.
    All exceptions should inherit from this or a subclass of it (depending on the usage),
    this will allow all apps and libraries to maintain a common exception chain
    """
    def __init__(self, message, debug_message=None, status=500):
        super().__init__(message)
        self.status = status
        self.message = message
        self.debug_message = debug_message

    def marshal(self):
        return {
            "message": self.message,
            "debug_message": self.debug_message,
        }


class ServerException(HttpException):
    status = 500
    message = None

    def __init__(self, debug_message=None):
        super().__init__(self.message, debug_message, self.status)


class BadRequestException(HttpException):
    status = 400
    message = None

    def __init__(self, debug_message=None):
        super().__init__(self.message, debug_message, self.status)


class UnauthorisedException(HttpException):
    status = 401
    message = None

    def __init__(self, debug_message=None):
        super().__init__(self.message, debug_message, self.status)


class NotFoundException(HttpException):
    status = 404
    message = None

    def __init__(self, debug_message=None):
        super().__init__(self.message, debug_message, self.status)
