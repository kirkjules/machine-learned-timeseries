"""
The following class is written to be accessible and inherited by any class
throughout the api library.

"""
import yaml
import logging

# Set default logging handler to avoid "No handler found" warnings.
logging.getLogger(__name__).addHandler(logging.NullHandler())


class Api:
    """
    To access stored API variables.

    Most programs that offer an API will require identifying variables, for
    example an authentication token, to engage with its endpoints. The
    variables stored in a local `.yaml` file will be read into the `details`
    attribute. This attribute can then be used by a class defined in a
    sub-module via inheritance.


    Parameters
    ----------
    configFile : str
        The filename, with the relative path if required, of the .yaml
        configuration file where the API variables are stored.
        (The default is `config.yaml`, the chosen configuration filename
        stored in the directory from which the program is run.)
    api : str
        A variable matching a top-level key in the `.yaml` configuration file.
        The key will be the application name, or some identifiable variation.
        (The default is `oanda`, under which is stored the respective account
        ID and authentication token required to engage the API's endpoints.)
    access : str
        A variable matching a sub-level key under the given `api`.
        (The default is `practise`, precising that the practise platform's API
        variables and endpoints will be used by the submodule's function(s).)


    Attributes
    ----------
    details : dict
        Stores the variables sourced from the configuration file in a
        dictionary.


    Notes
    -----
    The class is intended to be inherited in submodules written to engage with
    a specific API. It is in those respective modules' top level class where
    the parameters will be redfined appropriately.


    Examples
    --------
    >>> from htp.api import Api
    >>> from pprint import pprint
    >>> var = Api(configFile="config.yaml", api="oanda", access="practise")
    >>> pprint(var.details)
    {'account-id': '101-011-6215953-001',
     'token': 'a4c4164e10bd1c4e5afb3038340c444f-a349aec867b5faed0113ed23c984193b',
     'url': 'https://api-fxpractice.oanda.com/v3/'}

    """
    def __init__(self, configFile="config.yaml", api="oanda",
                 access="practise"):

        self.configFile = configFile
        self.api = api
        self.access = access

        with open(self.configFile, 'r') as f:
            config = yaml.safe_load(f)

        self.details = config[self.api][self.access]
