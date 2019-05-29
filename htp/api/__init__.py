import yaml
import logging
# import configparser

# Set default logging handler to avoid "No handler found" warnings.
logging.getLogger(__name__).addHandler(logging.NullHandler())


class Api:

    def __init__(self, configFile="config.yaml", api="oanda",
                 access="practise", **kwargs):  # configFile, live):

        self.configFile = configFile
        self.api = api
        self.access = access

        # config = configparser.ConfigParser()
        with open(self.configFile, 'r') as f:
            # config.read_file(f)
            config = yaml.safe_load(f)

        self.details = config[self.api][self.access]

        # if live is True:
        #    self.key = config["api-fxtrade.oanda.com"]["authtoken"]
        #    self.base = "https://api-fxtrade.oanda.com/v3/"

        # elif live is False:
        #    self.key = config["api-fxpractice.oanda.com"]["authtoken"]
        #    self.base = "https://api-fxpractice.oanda.com/v3/"

        # self.headers = {"Content-Type": "application/json",
        #                "Authorization": "Bearer {0}".format(self.key)}
