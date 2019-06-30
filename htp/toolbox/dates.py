"""The module provides a series of generators that yield lists of dates
according to their respective implemented logics.

The following time ranges are defined as class methods: 1y, 1yTD, FY, FYTD, 6m,
3m, FQ, FQTD, 5d, 1wTD, 1d, 1dTT, align to America/New_York timezone.

Notes
-----
As this module was initially designed to facilitate querying the Oanda exchange
which is located in New York, all time ranges will align with 1700h
America/New-York timezone. This does not change with DST as the exchange
operates on local business hours.
"""

import pytz
import logging
import calendar
from dateutil.tz import tzlocal
from datetime import datetime, timedelta

log = logging.getLogger(__name__)


class Conversion:

    def __init__(self, date, local_tz=None, conv_tz=None):
        """
        To convert a given date-time to UTC and specified timezones.

        Parameters
        ----------
        date : str
            Provided in string format %Y-%m-%d %H:%M:%S.

        local_tz : str, optional
            Timzone to localise given datetime with. Must match a timezone
            contained in `pytz.common_timezones` database. (The default is
            None, which implies the system timezone should be used to make
            the given date timezone aware.)

        conv_tz : str, optional
            Target timezone to convert datetime to. Must match a timezone
            contained in `pytz.common_timezones` database. (The default is
            None, which implies the date does not need to be converted.)

        Attributes
        ----------
        tz_date : datetime.datetime
            A timezone aware datetime object against.

        utc_date : datetime.datetime
            The given timezone aware date converted to UTC timezone. Note if no
            local timezone is provided, or none can be inferred from the
            system, the date will be assumed to be in UTC. Thus tz_date will
            equal tz_date.

        conv_date : datetime.datetime or None
            The given date converted from the given local timezone, or UTC, to
            a given target timezone. If no target timezome (conv_tz) is
            provided then conv_date will be None.

        Examples
        --------
        >>> d = Conversion("2018-05-06 18:54:13", local_tz="Australia/Sydney",
        ...                conv_tz="America/New_York")
        >>> d.tz_date
        datetime.datetime(2018, 5, 6, 18, 54, 13, tzinfo=<DstTzInfo \
'Australia/Sydney' AEST+10:00:00 STD>)
        >>> d.utc_date
        datetime.datetime(2018, 5, 6, 8, 54, 13, tzinfo=<UTC>)
        >>> d.conv_date
        datetime.datetime(2018, 5, 6, 4, 54, 13, tzinfo=<DstTzInfo \
'America/New_York' EDT-1 day, 20:00:00 DST>)
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


class Select:
    """
    Generates datetime variable lists from predefined business logic.

    Notes
    -----
    Limitations:
        1. The Oanda API has a 5000 max session-per-query limit.
        Functionality has not been written to handle this error. This will
        result by using an inappropriate generator-granularity combination.
        2. Small timeframe generators have preset variables that are
        inappropriate to use with larger granularities. Resulting datetime
        variables will not be validated with the business logic that would
        prevent an out-of-range error.
    """

    def __init__(self, from_=None, to=None, local_tz=None):
        """
        Initialise datestring arguments into UTC time using the Conversion()
        class.

        Parameters
        ----------
        from_ : str
            Provided in string format %Y-%m-%d %H:%M:%S. The date from which
            the generated time range should start.

        to : str
            Provided in string format %Y-%m-%d %H:%M:%S. The date from which
            the generated time range should stop.

        local_tz : str, optional
            Timzone to localise given datetimes with. Must match a timezone
            contained in `pytz.common_timezones` database. (The default is
            None, which implies the system timezone should be used to make
            the given dates timezone aware.)

        Attributes
        ----------
        from_date : datetime.datetime
            The given `from_` parameter converted to UTC time.

        to_date : datetime.datetime
            The given `to` parameter converted to UTC time.

        date_range : int
            The number of years between the `from_` and `to` dates.

        Notes
        -----
        - If no arguments are provided all methods will use datetime.now().
        - All times are converted to UTC time.

        Examples
        --------
        >>> d = Select(from_="2018-05-06 18:54:13", to="2019-06-15 10:12:04",
        ...            local_tz="Australia/Sydney")
        >>> d.from_date
        datetime.datetime(2018, 5, 6, 8, 54, 13, tzinfo=<UTC>)
        >>> d.to_date
        datetime.datetime(2019, 6, 15, 0, 12, 4, tzinfo=<UTC>)
        >>> d.date_range
        2
        """
        if from_ is not None:
            self.from_date = Conversion(from_, local_tz=local_tz).utc_date

        if to is not None:
            self.to_date = Conversion(to, local_tz=local_tz).utc_date
        else:
            self.to_date = Conversion(datetime.strftime(datetime.now(),
                                                        "%Y-%m-%d %H:%M:%S"
                                                        )).utc_date
        self.date_range = None
        if from_:
            delta = self.to_date.year - self.from_date.year
            self.date_range = delta + 1

    def __fmt(self, utc_start, utc_end):
        d = {}
        d["from"] = datetime.strftime(utc_start, "%Y-%m-%dT%H:%M:%S.%f000Z")
        d["to"] = datetime.strftime(utc_end, "%Y-%m-%dT%H:%M:%S.%f000Z")
        return d

    @staticmethod
    def time_val(date, no_days=[], select=0, hour=0, minute=0,
                 year_by_day=False):
        """
        Business logic for validating an appropriate query time variable.
        Oanda candles api will error if requesting data for an invalid
        timestamp, i.e. outside trading hours for a given ticker. Note, hour
        and minute params are relevant to the intended granularity.
        Inputs are treated as New York time since this is where the exchange is
        located, thus the most appropriate place around which to define
        business logic.
        :param hour: 0 to 23 int value to precise the timestamp hour value.
        :param minute: 0 to 59 int value to precise the timestamp minute value.
        :param year_by_day: boolean preventing dt value returning Dec 31, 1700h
        New York local time, for daily candle query. Note, granularities less
        than daily can still be queried on Dec 31, e.g M15 -> Dec 31, 16:45:00.
        """
        dt_s = []
        # Iterate through dates in a given year-month.
        # Note the method's behviour to return dates preceeding and following
        # the given month, so as to complete a full week.
        for dt in calendar.Calendar().itermonthdates(date.year, date.month):
            # Don't consider dates earlier then the stated month.
            if dt.month < date.month and dt.year == date.year:
                pass
            # Don't consider days that are not business days as labelled in
            # `no_days`, e.g. Friday past 1659h till Sunday 1700h.
            elif dt.isoweekday() in no_days:
                pass
            # As noted, don't consider Dec 31 for daily granularity.
            # Must be specified by the user via the `year_by_day` keyword
            # argument.
            elif year_by_day is True and dt.day == 31:
                pass
            # Append the filter date to a list.
            else:
                dt_s.append(dt)
        # End date needs to be defined as the datetime value immediately before
        # the next start value. Not just the last possible value in the month.
        if select == -1:
            dt_fin = []
            for i in dt_s:
                if i.month != date.month and i.year >= date.year:
                    dt_fin.append(i)
            dt_fin.sort()
            try:
                dt_f = dt_fin[0]
            except IndexError:
                dt_f = dt_s[-1] + timedelta(days=1)
        else:
            # Select the date from the filtered list via index.
            dt_f = dt_s[select]
        # Annotate the chosen date with the speicifed `hour` and `minute`
        # variables.
        dt_f_ann = datetime(dt_f.year, dt_f.month, dt_f.day, hour, minute)
        return datetime.strftime(dt_f_ann, "%Y-%m-%d %H:%M:%S")

    def by_calendar_year(self, no_days=[6], from_hour=17, from_minute=0,
                         to_hour=17, to_minute=0, year_by_day=True, period=1):
        """
        Function to generate yearly range datetime pairs up to current date.
        Uses the time_val function to appropriately define the datetime value.
        Refer to above documentation.
        """
        # Check is a date range has been predefined by a set date from and to.
        # Use pre-define setting if true.
        if self.date_range:
            period = self.date_range
        # print(period)
        dP = 0
        # Iterate through n number of periods that have been defined to define
        # n sets of start and end datetime values that will be use separately
        # to query for timeseries data.
        while dP in list(range(period)):
            # Evaluate the timestamp against defined business hours as set by
            # keyword arguments parsed through the `time_val` class function.
            start = self.time_val(datetime(self.to_date.year - dP, 1, 1),
                                  hour=from_hour, minute=from_minute,
                                  year_by_day=year_by_day, no_days=no_days)
            # Convert the selected start date value, currently in New York
            # local time, to UTC time, to accurately query timeseries for the
            # Oanda API endpoint.
            utc_start = Conversion(start, local_tz="America/New_York").utc_date
            # Use the given to_date at the first iteration.
            # Note the generator works itself backwards in time, generating the
            # most recent start and end date pair first.
            if dP == 0:
                utc_end = self.to_date
            else:
                # Repeat the above noted logic for start date, for the end
                # date.
                end = self.time_val(datetime(self.to_date.year - dP, 12, 31),
                                    select=-1, hour=to_hour, minute=to_minute,
                                    year_by_day=year_by_day, no_days=no_days)
                utc_end = Conversion(end, local_tz="America/New_York").utc_date
            # If a from date is provided, resulting in a predefined date range
            # check that the most recently defined start date has not gone
            # beyond the start date in history. If it has, break the iteration
            # and the the from date as the start date for the final pairing.
            if self.date_range and utc_start < self.from_date:
                yield self.__fmt(self.from_date, utc_end)
                break
            yield self.__fmt(utc_start, utc_end)
            dP += 1

    def by_financial_year(self, no_days=[6], from_hour=17, from_minute=0,
                          to_hour=17, to_minute=0, year_by_day=False,
                          period=1):
        """
        Function to generate yearly range datetime pairs up to current date,
        aligned to the financial year.
        Uses the time_val function to appropriately define the datetime value.
        Refer to above documentation.
        """
        if self.date_range:
            period = self.date_range
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
            if self.date_range and utc_start < self.from_date:
                yield self.__fmt(self.from_date, utc_end)
                break
            yield self.__fmt(utc_start, utc_end)
            dP += 1

    def by_quarter(self, no_days=[6], from_hour=17, from_minute=0,
                   to_hour=17, to_minute=0, year_by_day=False,
                   period=1):
        if self.date_range:
            period = self.date_range * 4
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
        # preceeding it in the list. This will be the first start month.
        month = s_months[ind - 1]
        # Set the start year as this year.
        s_year = now.year

        while dP in list(range(period)):
            # Find the index of the start month in the list without the
            # locator. This is the list that will be iterated over.
            s_ind = months.index(month)
            # Duplicate the list for dP values exceeding the original list
            # length.
            months_ = months * (int(dP / 4) + 1)
            # Use the index to re-find the month, note the subtraction of dP
            # set to zero for the first iteration.
            s_month = months_[s_ind - dP]
            # Set the year to decrease with eath October quarter.
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
            if self.date_range and utc_start < self.from_date:
                yield self.__fmt(self.from_date, utc_end)
                break
            yield self.__fmt(utc_start, utc_end)
            dP += 1

    def by_month(self, no_days=[6], from_hour=17, from_minute=0,
                 to_hour=17, to_minute=0, year_by_day=False,
                 period=1):
        """
        Function to generate monthly range datetime pairs up to current date.
        Will subtract a year from the timestamp with each pair that ends in
        December.
        Uses the time_val function to appropriately define the datetime value.
        Refer to above documentation.
        """
        if self.date_range:
            period = self.date_range * 12
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
            if self.date_range and utc_start < self.from_date:
                yield self.__fmt(self.from_date, utc_end)
                break
            yield self.__fmt(utc_start, utc_end)
            dP += 1

    def by_week(self, no_days=[6], from_hour=17, from_minute=0, to_hour=17,
                to_minute=0, year_by_day=False, period=1):
        """
        Function to generate weekly range datetime pairs up to current date.
        Set variables within the function explicitly state start and end time
        range align with Sunday and Friday respectively, New York time.
        Don't use with daily or greater granularity as this will query a daily
        candle starting Friday 1700h which is out of range.
        """
        if self.date_range:
            period = self.date_range * 53
        dP = 0
        # Take utc date and convert to NY time.
        ny_time = self.to_date.astimezone(pytz.timezone("America/New_York"))
        ny_wd = ny_time.isoweekday()
        # Construct a reference for NY business week aligned to Sunday 1700h.
        ny_sunday = datetime(ny_time.year, ny_time.month, ny_time.day) -\
            timedelta(days=ny_wd)
        while dP in list(range(period)):
            # Initial Sunday will not be adjsuted with dP=0.
            start = ny_sunday - timedelta(days=7 * dP)
            # Sunday hour and minute is aligned to inputs, default 1700h.
            start = start.replace(hour=from_hour, minute=from_minute)
            fmt = datetime.strftime(start, "%Y-%m-%d %H:%M:%S")
            # Sunday datetime is converted to UTC for output.
            utc_start = Conversion(fmt, local_tz="America/New_York").utc_date
            if dP == 0:
                utc_end = self.to_date
            else:
                end = start + timedelta(days=7)
                end = end.replace(hour=to_hour, minute=to_minute)
                fmt = datetime.strftime(end, "%Y-%m-%d %H:%M:%S")
                utc_end = Conversion(fmt, local_tz="America/New_York").utc_date
            if self.date_range and utc_start < self.from_date:
                yield self.__fmt(self.from_date, utc_end)
                break
            yield self.__fmt(utc_start, utc_end)
            dP += 1

    def by_day(self, no_days=[6], from_hour=17, from_minute=0, to_hour=17,
               to_minute=0, year_by_day=False, period=1):
        """
        Function to generate daily range datetime pairs up to current date.
        Set variables within the function explicitly state start and end time
        range align with 1700h to 1659h+1day respectively, New York time.
        Don't use with daily or greater granularity.
        """
        if self.date_range:
            period = self.date_range * 366
        dP = 0
        s = 0
        # Take UTC date and convert to NY time.
        ny_time = self.to_date.astimezone(pytz.timezone("America/New_York"))
        # Construct a reference for NY business day aligned to 1700h.
        ref_time = datetime(ny_time.year, ny_time.month, ny_time.day, 17)
        ref_time = pytz.timezone("America/New_York").localize(ref_time)
        # Compare input time to reference time.
        if ny_time < ref_time:
            # If NY time less than 1700h the initial start value for the date
            # range will be the previous day, i.e. - timedelta(days=1).
            dP += 1
            s += 1

        while dP in list(range(period + s)):
            # Construct start time from ref time adjusted by timedelta.
            start = ref_time - timedelta(days=dP)
            start = start.replace(hour=from_hour, minute=from_minute)
            # Convert start datetime from current NY time to UTC for query.
            fmt = datetime.strftime(start, "%Y-%m-%d %H:%M:%S")
            utc_start = Conversion(fmt, local_tz="America/New_York").utc_date
            if dP == s:
                utc_end = self.to_date
            else:
                end = start + timedelta(days=1)
                end = end.replace(hour=to_hour, minute=to_minute)
                fmt = datetime.strftime(end, "%Y-%m-%d %H:%M:%S")
                utc_end = Conversion(fmt, local_tz="America/New_York").utc_date
            # Pass if start datetime value is a Friday or Saturday, as this is
            # outside business hours for all tickers.
            # if utc_start.isoweekday() in no_days:
            #    s += 1
            # else:
            if self.date_range and utc_start < self.from_date:
                yield self.__fmt(self.from_date, utc_end)
                # print("BREAKING")
                break
            yield self.__fmt(utc_start, utc_end)
            # if dP == (period + s - 1):
            #     print("FINISHED")
            dP += 1

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
