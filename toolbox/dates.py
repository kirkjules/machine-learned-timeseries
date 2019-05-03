import pytz
import logging
import calendar
from dateutil.tz import tzlocal
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

    def __init__(self, date, local_tz=None, conv_tz=None):
        """
        To convert any local time to UTC and back.
        :param date: provided in string format %Y-%m-%d %H:%M:%S.
        :param local_tz: timzone to localise given datetime with.
        :param conv_tz: target timezone to convert datetime to.
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
        :param limit: used by datetime generators to yield up-to-date time
        range.
        """
        if from_ is not None:
            self.from_date = Conversion(from_, local_tz=local_tz).utc_date

        if to is not None:
            self.to_date = Conversion(to, local_tz=local_tz).utc_date
        else:
            self.to_date = Conversion(datetime.strftime(datetime.now(),
                                                        "%Y-%m-%d %H:%M:%S"
                                                        )).utc_date

    def time_val(self, date, no_days=[], select=0, hour=0, minute=0,
                 year_by_day=False):
        """
        Business logic for validating an appropriate query time variable.
        Oanda candles api will error if requesting data for an invalid
        timestamp, i.e. outside trading hours for a given ticker. Note, hour
        and minute params are relevant to the intended granularity.
        :param hour: 0 to 23 int value to precise the timestamp hour value.
        :param minute: 0 to 59 int value to precise the timestamp minute value.
        :param year_by_day: boolean preventing dt value returning Dec 31, 1700h
        New York local time, for daily candle query. Note, granularities less
        than daily can still be queried on Dec 31, e.g M15 -> Dec 31, 16:45:00.
        """
        dt_s = []
        for dt in calendar.Calendar().itermonthdates(date.year, date.month):
            if dt.month != date.month:
                pass
            elif dt.isoweekday() in no_days:
                pass
            elif year_by_day is True and dt.day == 31:
                pass
            else:
                dt_s.append(dt)

        dt = dt_s[select]
        dt = datetime(dt.year, dt.month, dt.day, hour, minute)
        return datetime.strftime(dt, "%Y-%m-%d %H:%M:%S")

    def by_calendar_year(self, no_days=[], from_hour=17, from_minute=0,
                         to_hour=17, to_minute=0, year_by_day=True, period=1):
        """
        Generator to query y number of years where the current year is 1. The
        function wraps the more general time_val function which validates
        appropriate start and end timestamp values for a calendar year time
        range. Returned value is a tuple of start and end datetime objects in
        UTC time converted from "America/New_York" local time defined by
        time_val dates and hour and minute arguments. Inputs are treated as
        New York time since this is where the exchange is located and therefore
        the most appropriate place to define business logic around.
        """
        dP = 0
        while dP in list(range(period)):
            start = self.time_val(datetime(self.to_date.year - dP, 1, 1),
                                  hour=from_hour, minute=from_minute,
                                  year_by_day=year_by_day, no_days=no_days)
            utc_start = Conversion(start, local_tz="America/New_York").utc_date
            if dP == 0:
                utc_end = self.to_date
            else:
                end = self.time_val(datetime(self.to_date.year - dP, 12, 31),
                                    select=-1, hour=to_hour, minute=to_minute,
                                    year_by_day=year_by_day, no_days=no_days)
                utc_end = Conversion(end, local_tz="America/New_York").utc_date
            yield(utc_start, utc_end)
            dP += 1

    def by_financial_year(self, no_days=[], from_hour=17, from_minute=0,
                          to_hour=17, to_minute=0, year_by_day=False,
                          period=1):

        dP = 0
        s = 0
        if self.to_date.astimezone(pytz.timezone("America/New_York")) <\
           datetime(datetime.now().year, 6, 30, 17,
                    tzinfo=pytz.timezone("America/New_York")):
            dP += 1
            s += 1

        while dP in list(range(period + s)):
            start = self.time_val(datetime(self.to_date.year - dP, 7, 1),
                                  hour=from_hour, minute=from_minute,
                                  year_by_day=year_by_day, no_days=no_days)
            utc_start = Conversion(start, local_tz="America/New_York").utc_date
            if dP == s:
                utc_end = self.to_date
            else:
                end = self.time_val(datetime(self.to_date.year - dP + 1, 6,
                                             30),
                                    select=-1, hour=to_hour, minute=to_minute,
                                    year_by_day=year_by_day, no_days=no_days)
                utc_end = Conversion(end, local_tz="America/New_York").utc_date
            yield(utc_start, utc_end)
            dP += 1

    def by_quarter(self, no_days=[], from_hour=17, from_minute=0,
                   to_hour=17, to_minute=0, year_by_day=False,
                   period=1):
        # Set the iterator to zero.
        dP = 0
        # Start at system time converted to New York local time.
        now = self.to_date.astimezone(pytz.timezone("America/New_York"))
        # Creater a locator, a float calculated from the month number plus
        # the day number devided by the total days in the month.
        s_loc = now.month +\
            now.day /\
            calendar.monthrange(now.year, now.month)[1]
        months = [1, 4, 7, 10]
        s_months = months.copy()
        # Input the locator in a list of start months for yearly quarters.
        s_months.append(s_loc)
        # Sort the list into ascending order.
        s_months.sort()
        # Find the index of the locator in the sorted list.
        ind = s_months.index(s_loc)
        # Use the locator index to find the month number that is immediately
        # preceeding it in the list. This will the first start month.
        month = s_months[ind - 1]
        # Set the start year as the this year.
        s_year = now.year

        while dP in list(range(period)):
            # Find the index of the start month in the list without the
            # locator. This is the list that will be iterated over.
            s_ind = months.index(month)
            months_ = months * (int(dP / 4) + 1)
            # Use the index to re-find the month, not the subtraction of dP
            # set to zero for the first iteration.
            s_month = months_[s_ind - dP]
            # Set the year to decrease with eath quarter starting in Oct.
            # Ignore for the first iteration.
            if s_month == 10 and dP != 0:
                s_year -= 1
            # Set the start date.
            s_date = datetime(s_year, s_month, 1)
            start = self.time_val(s_date, hour=from_hour, minute=from_minute,
                                  year_by_day=year_by_day, no_days=no_days)
            utc_start = Conversion(start, local_tz="America/New_York").utc_date
            if dP == 0:
                utc_end = self.to_date
            else:
                # Base the end date off the start date.
                e_month = s_month + 2
                e_day = calendar.monthrange(s_year, e_month)[1]
                end = self.time_val(datetime(s_year, e_month, e_day),
                                    select=-1, hour=to_hour, minute=to_minute,
                                    year_by_day=year_by_day, no_days=no_days)
                utc_end = Conversion(end, local_tz="America/New_York").utc_date
            yield(utc_start, utc_end)
            dP += 1

    def by_month(self, no_days=[], from_hour=17, from_minute=0,
                 to_hour=17, to_minute=0, year_by_day=False,
                 period=1):
        dP = 0
        now = self.to_date.astimezone(pytz.timezone("America/New_York"))
        s_loc = now.month +\
            now.day /\
            calendar.monthrange(now.year, now.month)[1]
        months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        s_months = months.copy()
        s_months.append(s_loc)
        s_months.sort()
        ind = s_months.index(s_loc)
        month = s_months[ind - 1]
        s_year = now.year

        while dP in list(range(period)):
            s_ind = months.index(month)
            months_ = months * (int(dP / 12) + 1)
            s_month = months_[s_ind - dP]
            if s_month == 12 and dP != 0:
                s_year -= 1
            s_date = datetime(s_year, s_month, 1)
            start = self.time_val(s_date, hour=from_hour, minute=from_minute,
                                  year_by_day=year_by_day, no_days=no_days)
            utc_start = Conversion(start, local_tz="America/New_York").utc_date
            if dP == 0:
                utc_end = self.to_date
            else:
                e_day = calendar.monthrange(s_year, s_month)[1]
                end = self.time_val(datetime(s_year, s_month, e_day),
                                    select=-1, hour=to_hour, minute=to_minute,
                                    year_by_day=year_by_day, no_days=no_days)
                utc_end = Conversion(end, local_tz="America/New_York").utc_date
            yield(utc_start, utc_end)
            dP += 1

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
