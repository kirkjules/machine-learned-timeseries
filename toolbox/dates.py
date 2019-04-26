import pytz
import logging
from datetime import datetime
from dateutil.tz import tzlocal

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

    def __init__(self, date, local_tz=None, conv_tz=None):
        """
        To convert any local time to UTC and back.
        :date, provided in string format %Y-%m-%d %H:%M:%S.
        :local, flag if system timezone should be used for UTC conversion.
        :timezone, target timezone to convert date to.
        """
        try:
            obj = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            raise(e)

        self.date = date

        if local_tz is None:  # Infer timezone from system
            tz = tzlocal()

        elif local_tz in pytz.common_timezones:  # Set timezone as stated
            tz = pytz.timezone(local_tz)

        else:  # Set timezone as utc as final backup
            tz = pytz.utc

        # Create a timezone aware datetime object
        self.date_tz = datetime.strftime(obj.replace(tzinfo=tz),
                                         "%Y-%m-%d %H:%M:%S%z")

        # Convert to UTC datetime
        utc = pytz.UTC
        self.date_utc = self.date_tz.astimezone(utc)

        # Functionality to convert to any chosen timezone
        if conv_tz is None:
            self.convert = None

        elif local_tz in pytz.common_timezones:  # Set timezone as stated
            tz = pytz.timezone(conv_tz)
            self.convert = self.date_utc.astimezone(tz)

        else:
            self.convert = None

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
