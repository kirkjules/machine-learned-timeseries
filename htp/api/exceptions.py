class ApiError(Exception):
    """
    Exception raised when an api function returns an error message.
    Raised for instance where an invalid token returns an insufficient
    authorization error from the endpoint.
    The ApiError should be used as a place holder throughout development with
    a locally defined error message.
    Eventually endpoint functions should contain a specifically defined error
    class that inherits from ApiError.
    """
    def __init__(self, msg):
        super().__init__(msg)  # references/keeps the inherited variables
        self.msg = msg

    def __str__(self):
        return self.msg


class OandaError(ApiError):
    """
    Exception raised when function interacting with the Oanda api returns
    an endpoint error message.
    :param msg: Function appropriate message.
    :param oanda_msg: requests.json object containing the Oanda api response.
    """
    def __init__(self, msg, oanda_msg=None, status=None):
        super().__init__(msg)
        self.oanda_msg = oanda_msg
        if oanda_msg is not None:
            self.oanda_msg = oanda_msg["errorMessage"]
        self.status_code = status
        self.message = "{}: {}".format(self.msg, self.oanda_msg)

    def __str__(self):
        return self.message
