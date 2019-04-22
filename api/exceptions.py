class Oanda(Exception):
    """Base excpetion for all functions that interact with Oanda api."""
    def __init__(self, obj, msg=None):
        if msg is None:
            msg = "Oanda error message: {0}".format(
                obj.json()["errorMessage"])
        super(Oanda, self).__init__(msg)
        self.obj = obj
