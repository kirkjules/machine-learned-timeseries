class ApiError(Exception):
    """
    Exception raised when an api function returns an error message.
    Raised for instance where an invalid token returns an insufficient
    authorization error from the endpoint, or when the underlying requests
    library returns an error.
    :ivar cause: the cause of the exception being raised, when not none this
                 will itself be an exception instance, this is useful for
                 creating a chain of exceptions for versions of python where
                 this is not yet implemented/supported natively.
                 (ref. "https://github.com/openstack/tooz")
    """
    def __init__(self, message, cause=None):
        super().__init__(message)
        self.cause = cause


class OandaError(ApiError):
    """
    Exception raised when function interacting with the Oanda api returns
    an endpoint error message.
    """
    pass
