import pytz
import logging
from datetime import datetime, timedelta
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
        self.tz_date = datetime.strftime(obj.replace(tzinfo=tz),
                                         "%Y-%m-%d %H:%M:%S%z")

        # Convert to UTC datetime
        utc = pytz.UTC
        self.utc_date = self.tz_date.astimezone(utc)

        # Functionality to convert to any chosen timezone
        if conv_tz is None:
            self.conv_date = conv_tz

        elif conv_tz in pytz.common_timezones:  # Set timezone as stated
            self.conv_date = self.utc_date.astimezone(pytz.timezone(conv_tz))

        else:
            self.conv_date = None

        # datetime.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())
        # '2019-04-24T13:18:16+0700'


class Select():
    """
    Generates datetime variable sets from predefined business logic.
    """

    def __init__(self, from_=None, to=None, local_tz=None):
        """
        Initialise datestring arguments into UTC time.

        If no arguments are provided all methods will use datetime.now().

        All times are converted to UTC time.
        """
        if from_ is not None:
            self.from_date = Conversion(from_, local_tz=local_tz).utc_date

        if to is not None:
            self.to_date = Conversion(to, local_tz=local_tz).utc_date
        else:
            self.to_date = Conversion(datetime.now()).utc_date

    def by_generic(self, date, _type="start"):

        if _type == "start":
            fac = 0
        elif _type == "end":
            fac = 1

        if date.isoweekday() == (5 + fac):  # Friday or Saturday
            dt = date + (timedelta(days=2))
        elif date.isoweekday() == (6 + fac):  # Saturday or Sunday
            dt = date + (timedelta(days=1))
        else:
            dt = date

        return dt

    def by_calendar_year(self, granularity="D", years=1):
        dY = 0
        while dY in list(range(years)):
            start = self.by_generic(datetime(self.to_date.year - dY, 1, 1),
                                    _type="start")
            utc_start = Conversion(start.replace(hours=17),
                                   local_tz="America/New_York").utc_date
            if dY == 0:
                end = self.to_date
            else:
                end = self.by_generic(datetime(self.to_date.year - dY, 12, 31),
                                      _type="end")
                utc_end = Conversion(end.replace(hours=16),
                                     local_tz="America/New_York").utc_date
            yield(utc_start, utc_end, dY)
            dY += 1

    def by_financial_year():
        pass

    def by_quarter():
        pass

    def by_month():
        pass

    def by_week():
        pass

    def by_day():
        pass

    def calendar_year_to_date():
        pass

    def financial_year_to_date():
        pass

    def quarter_to_date():
        pass

    def week_to_date():
        pass

    def day_to_time():
        pass
