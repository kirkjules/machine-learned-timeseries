import pytz
import time
import logging
from datetime import datetime

log = logging.getLogger(__name__)

"""
Define preset time range as class methods: 1y, 1yTD, FY, FYTD, 6m, 3m, FQ,\
        FQTD, 5d, 1wTD, 1d, 1dTT, align to America/New_York timezone.\
        Note: Since the exchange is located in New York, all time ranges\
        will align with 1700h America/New-York timezone. This does not\
        change with DST as the exchange operates on local business hours.

Flow
1. State date/time range with datetime strings listed in ISO-8601 format.
2. Convert date/time to UTC.
Note: Parse to query in RFC3339 format, e.g. “YYYY-MM-DDTHH:MM:SS.nnnnnnnnnZ”
3. State granularity
Note: daily candles should keep default setting for dailyAlignment and\
        alignmentTimezone settings. Smooth must be set to True to ensure\
        same values as displayed by Oanda on the online portal.
4. Query data.
Note: any actions logged will be in UTC time. If the user needs a timestamp\
        displayed in local time this functionality will be applied in the\
        relevant functions and methods.
"""


class Conversion():

    def __init__(self, date, local=True, timezone=None):
        """
        To convert any local time to UTC and back.
        :date, provided in string format %Y-%m-%d %H:%M:%S.
        :local, flag if system timezone should be used for UTC conversion.
        :timezone, target timezone to convert date to.
        """
        self.date = date

        if local is True:
            local_tz = time.strftime("%z", time.localtime())  # e.g. +0700
        else:
            local_tz = "+0000"

        # Create a local timezone aware datetime object
        try:
            self.local = datetime.strptime(date + local_tz,
                                           "%Y-%m-%d %H:%M:%S%z")
        except ValueError as e:
            self.local = None
            self.utc = None
            self.convert = None
            log.exception(e)
        else:
            # Convert to UTC datetime
            utc = pytz.UTC
            self.utc = self.local.astimezone(utc)

            # Functionality to convert to any chosen timezone
            if timezone is not None:
                tz = pytz.timezone(timezone)
                self.convert = self.utc.astimezone(tz)
            else:
                self.convert = self.local

        # datetime.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())
        # '2019-04-24T13:18:16+0700'


class Select():

    def __init__(self, from_, to):
        """
        To record, convert and store date/time variables.
        """
        self.from_ = from_
        self.to = to
        self.utc_from = []
