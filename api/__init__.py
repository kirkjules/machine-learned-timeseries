import logging
import configparser


logging.getLogger(__name__).addHandler(logging.NullHandler())


class Api:

    def __init__(self, configFile, live):

        config = configparser.ConfigParser()
        with open(configFile, 'r') as f:
            config.read_file(f)

        if live is True:
            self.key = config["api-fxtrade.oanda.com"]["authtoken"]
            self.base = "https://api-fxtrade.oanda.com/v3/"

        elif live is False:
            self.key = config["api-fxpractice.oanda.com"]["authtoken"]
            self.base = "https://api-fxpractice.oanda.com/v3/"

        self.headers = {"Content-Type": "application/json",
                        "Authorization": "Bearer {0}".format(self.key)}
