import logging
import configparser


logging.getLogger(__name__).addHandler(logging.NullHandler())


class Api:

    def __init__(self, configFile):

        config = configparser.ConfigParser()
        with open(configFile, 'r') as f:
            config.read_file(f)
        self.sections = config.sections()
        self.key = config["api-fxpractice.oanda.com"]["authtoken"]
