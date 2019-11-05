"""
The following class is written to be accessible and inherited by any class
throughout the api library.
"""
import os


class Api:
    """The base class from which all api calling classes will inherit. This
    class contains the functionality to read in connection information from a
    local yaml file.

    Parameters
    ----------
    filename : str
        The filename for the yaml file in which config data is stored.
    api : str
        The name of the api engine for which the relevent information is stored
        against.
    access : str
        The a sub-level used to segment api connection information.

    Attributes
    ----------
    details : dict
        The resulting information stored against the stated api and access
        levels. The dictionary keys will represent the information labels that
        relate to specific information the endpoint will require to be parsed.
    """
    def __init__(self):
        self.details = {}
        self.details["token"] = os.environ["OANDA_PRACTISE_TOKEN"]
