import pytz
import logging
import calendar
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
        if local_tz is None:
            self.tz_date = obj.replace(tzinfo=tzlocal())
        else:
            self.tz_date = tz.localize(obj)

        # Convert to UTC datetime
        utc = pytz.UTC
        self.utc_date = self.tz_date.astimezone(utc)

        # Functionality to convert to any chosen timezone
        if conv_tz in pytz.common_timezones:  # Set timezone as stated
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
            self.to_date = Conversion(datetime.strftime(datetime.now(),
                                                        "%Y-%m-%d %H:%M:%S"
                                                        )).utc_date

    def time_val(self, date, no_days=[5, 6], select=0, hour=0, minute=0,
                 by_year=False):
        """
        Business logic for validating an appropriate query time variable.
        Oanda candles api will error if requesting data for an invalid
        timestamp, i.e. outside trading hours for a given ticker.
        """
        dt_s = []
        for dt in calendar.Calendar().itermonthdates(date.year, date.month):
            if dt.month != date.month:
                pass
            elif dt.isoweekday() in no_days:
                pass
            elif by_year is True and dt.day == 31:
                pass
            else:
                dt_s.append(dt)

        dt = dt_s[select]
        dt = datetime(dt.year, dt.month, dt.day, hour, minute)
        return dt

    def by_calendar_year(self, granularity="D", years=1):
        dY = 0
        while dY in list(range(years)):
            start = self.time_val(datetime(self.to_date.year - dY, 1, 1),
                                  hour=17,
                                  by_year=True)
            utc_start = Conversion(start, local_tz="America/New_York").utc_date
            if dY == 0:
                utc_end = self.to_date
            else:
                end = self.time_val(datetime(self.to_date.year - dY, 12, 31),
                                    select=-1,
                                    hour=17,
                                    by_year=True)
                utc_end = Conversion(end, local_tz="America/New_York").utc_date
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
