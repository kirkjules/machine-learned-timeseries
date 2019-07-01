import logging
from functools import partial


class Worker:

    def __init__(self, func, iterable_arg, *args, iterable=[], **kwargs):
        """
        Class initialiser to establish the target function, the iterable, and
        any positional or keywork arguments that should be parsed to the
        function.

        Parameters
        ----------
        func
            This can be any function that accepts a keyword argument that could
            be stored in an iterable data structure.

        iterable_arg : str
            The keyword that references the iterable argument in the target
            function.

        iterable : list
            An iterable containing elements that are individually parsed to the
            target function as a keyword argument.

        *args, **kwargs
            Any positional or keyword arguments required by the target function
            and remain constant.

        Attributes
        ----------
        func
            The functional with, if any, positional and keyword arguments
            included.

        iterable
            The iterable parsed above.
        """
        self.func = partial(func, *args, **kwargs)
        self.iterable = iterable
        self.iterable_arg = iterable_arg

    def seq(self):
        """
        To execute the target function sequentially across the given iterable's
        elements, with the provided positional and keyword arguments.

        Returns
        -------
        list
            A list, where the elements represent the respective results from
            calling the target function on each value stored in the iterable.
        """
        st = []
        for i in iter(self.iterable):
            print(i)
            st.append(self.func(**{self.iterable_arg: i}))

        return st


if __name__ == "__main__":
    import os
    import time
    from copy import deepcopy
    from pprint import pprint
    from htp.api.oanda import Candles
    from htp.toolbox.dates import Select

    f = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=f)

    cf = os.path.join(os.path.dirname(__file__), "../..", "config.yaml")
    instrument = "AUD_JPY"
    func = Candles.to_df
    queryParameters = {"granularity": "D"}
    date_gen = Select().by_month(period=5, no_days=[5, 6], year_by_day=True)
    date_list = []
    for i in date_gen:
        queryParameters["from"] = i["from"]
        queryParameters["to"] = i["to"]
        date_list.append(deepcopy(queryParameters))

    start_time = time.time()
    d = Worker(func,
               "queryParameters",
               iterable=date_list,
               configFile=cf,
               instrument=instrument).seq()
    pprint(d)
    print("--- %s seconds ---" % (time.time() - start_time))
