import yaml
import logging

# Set default logging handler to avoid "No handler found" warnings.
logging.getLogger(__name__).addHandler(logging.NullHandler())


class Api:

    def __init__(self, configFile="config.yaml", api="oanda",
                 access="practise", **kwargs):

        self.configFile = configFile
        self.api = api
        self.access = access

        with open(self.configFile, 'r') as f:
            config = yaml.safe_load(f)

        self.details = config[self.api][self.access]
