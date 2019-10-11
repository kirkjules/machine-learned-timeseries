import rq
import time
import redis
import multiprocessing
from queue import Queue
from functools import partial
from threading import Thread, Lock


redis_conn = redis.Redis()
q = rq.Queue(connection=redis_conn)


def launch_task(func, *args, **kwargs):
    """Function to enqueue target function with arguments and return a job id
    """
    job = q.enqueue(func, *args, **kwargs)
    return job.get_id()


def queue_completed(tasks):
    """Blocking function to hang while job id is not present in Finished
    Registry."""
    for i in tasks:
        while i not in rq.registry.FinishedJobRegistry(queue=q):
            time.sleep(1)
    return True


class Worker:
    """
    Class that defines a wrapper that actions a target function over elements
    presented in an iterable data structure in a sequential process.

    This is also the base class in the module from which initial attributes are
    inherited and used to establish wrappers that action concurrent and
    parallel processes respectively.

    See Also
    --------
    ConcurrentWorker
    ParallelWorker
    """
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
            The function with, if any, positional and keyword arguments
            included.

        iterable
            The iterable parsed above.

        iterable_arg
            The target function's keyword tha parses the iterable's element.

        Examples
        --------
        >>> from copy import deepcopy
        >>> from htp.api.oanda import Candles
        >>> from htp.toolbox.dates import Select
        >>> instrument = "AUD_JPY"
        >>> func = Candles.to_df
        >>> queryParameters = {"granularity": "D"}
        >>> date_gen = Select().by_month(
        ...     period=2, no_days=[5, 6], year_by_day=True)
        >>> date_list = []
        >>> for i in date_gen:
        ...     queryParameters["from"] = i["from"]
        ...     queryParameters["to"] = i["to"]
        ...     date_list.append(deepcopy(queryParameters))
        >>> d = Worker(func, "queryParameters", iterable=date_list,
        ...     instrument=instrument)
        >>> print(d.func)
        functools.partial(<bound method Candles.to_df of <class \
'htp.api.oanda.Candles'>>, instrument='AUD_JPY')
        """
        self.func = partial(func, *args, **kwargs)
        self.iterable = iterable
        self.iterable_arg = iterable_arg

    @classmethod
    def sync(cls, *args, **kwargs):
        """
        To execute the target function sequentially across the given iterable's
        elements, with the provided positional and keyword arguments.

        Returns
        -------
        list
            A list, where the elements represent the respective results from
            calling the target function on each value stored in the iterable.

        Examples
        --------
        >>> from copy import deepcopy
        >>> from htp.api.oanda import Candles
        >>> from htp.toolbox.dates import Select
        >>> instrument = "AUD_JPY"
        >>> func = Candles.to_df
        >>> queryParameters = {"granularity": "D"}
        >>> date_gen = Select().by_month(
        ...     period=2, no_days=[5, 6], year_by_day=True)
        >>> date_list = []
        >>> for i in date_gen:
        ...     queryParameters["from"] = i["from"]
        ...     queryParameters["to"] = i["to"]
        ...     date_list.append(deepcopy(queryParameters))
        >>> d = Worker.sync(func, "queryParameters", iterable=date_list,
        ...     instrument=instrument)
        >>> print(d[1].head())
                               open    high     low   close
        2019-06-02 21:00:00  75.068  75.487  74.968  75.401
        2019-06-03 21:00:00  75.396  75.696  75.082  75.606
        2019-06-04 21:00:00  75.604  75.904  75.404  75.585
        2019-06-05 21:00:00  75.594  75.776  75.280  75.628
        2019-06-06 21:00:00  75.632  75.817  75.492  75.738
        """
        k = cls(*args, **kwargs)
        st = []
        for i in iter(k.iterable):
            st.append(k.func(**{k.iterable_arg: i}))

        return st


class ConcurrentWorker(Worker):
    """
    Class that inherit from `Worker` and subsequently provides concurrent
    processing functionality to a target function.

    See Also
    --------
    Worker
    """
    def __init__(self, func, iterable_arg, *args, **kwargs):
        """
        Class initialiser that inherits from the `Worker` class and assigns
        private attributes required to concurrently process a target function
        across given elements in an iterable.

        Attributes
        ----------
        _lock
        _queue

        See Also
        --------
        Worker.__init__
        """
        super().__init__(func, iterable_arg, *args, **kwargs)
        self._lock = Lock()
        self._queue = Queue()

    def _threader(self, st):
        """
        Threader function that feeds items from the queue to the target
        function.

        Parameters
        -----------
        st : list
            An empty list into which the returned values from the target
            function are stored.
        """
        while True:
            item = self._queue.get()
            if item is None:
                break
            st.append(self.func(**{self.iterable_arg: item}))
            self._queue.task_done()

    def crt(self):
        """
        Function that assembles the required components to action the target
        function concurrently against an iterable's elements stored in a queue.

        Returns
        -------
        list
            A list of elements, each the respective result of the target
            function working on a given value present in the iterable.
        """
        t = []
        results = []
        for i in range(4):
            thread = Thread(target=self._threader, args=(results,))
            thread.daemon = True
            thread.start()
            t.append(thread)

        self._queue.join()

        for job in self.iterable:
            self._queue.put(job)

        for i in range(4):
            self._queue.put(None)

        for threads in t:
            threads.join()

        return results


class Parallel(Worker):
    """
    Class that inherit from `Worker` and subsequently provides parallel
    processing functionality to a target function.

    See Also
    --------
    Worker
    """
    def __init__(self, func, iterable_arg, *args, **kwargs):
        """
        ParallelWorker is a class that inherits from Worker for necessary
        attributes and then provides a pool of workers for the parsed
        task and arguments to be worked on in parallel.

        See Also
        --------
        Worker.__init__
        """
        super().__init__(func, iterable_arg, *args, **kwargs)

    def _init_lock(self, l_):
        """
        Lock initialiser used in the pool setup.
        """
        global lock
        lock = l_

    def _arg_kw(self, func, k, iterable):
        """
        Internal helper function to parse the elements stored in an iterable as
        keyword arguments in the target function.
        """
        return func(**{k: iterable})

    @classmethod
    def worker(cls, *args, lock_func=None, lock_arg=None, **kwargs):
        """
        Method to run target function in parallel. The pool of workers is
        initialised with a lock that is used for logging in the target
        function.

        Returns
        -------
        list
            A list of elements, each the respective result of the target
            function working on a given value present in the iterable.
        """
        k = cls(*args, **kwargs)
        if lock_func is None:
            lock_func = k._init_lock
            lock_arg = multiprocessing.Lock()

        pool = multiprocessing.Pool(
            processes=3, initializer=lock_func, initargs=(lock_arg,))
        results = []
        for i in pool.map(partial(k._arg_kw, k.func, k.iterable_arg),
                          k.iterable):
            results.append(i)

        pool.close()
        pool.join()

        return results


if __name__ == "__main__":
    import os
    import pandas as pd
    from loguru import logger
    from copy import deepcopy
    from pprint import pprint
    from htp.api.oanda import Candles
    from htp.toolbox.dates import Select

    # f = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    # logging.basicConfig(level=logging.INFO, format=f)

    logger.enable("htp.api.oanda")

    cf = os.path.join(os.path.dirname(__file__), "../..", "config.yaml")
    instrument = "AUD_JPY"
    func = Candles.to_df
    queryParameters = {"granularity": "D"}
    # date_gen = Select().by_month(period=5, no_days=[6], year_by_day=True)
    date_gen = Select(
        from_="2019-03-04 21:00:00", to="2019-06-15 22:00:00",
        local_tz="America/New_York").by_month()
    date_list = []
    for i in date_gen:
        queryParameters["from"] = i["from"]
        queryParameters["to"] = i["to"]
        date_list.append(deepcopy(queryParameters))
    # sys.exit()
    start_time = time.time()
    d = Parallel.worker(
        func, "queryParameters", iterable=date_list, configFile=cf,
        instrument=instrument)
    pprint(pd.concat(d, axis=0))
    print("--- %s seconds ---" % (time.time() - start_time))

    """
    start_time = time.time()
    d = ConcurrentWorker(
        func, "queryParameters", iterable=date_list, configFile=cf,
        instrument=instrument).crt()
    pprint(d)
    print("--- %s seconds ---" % (time.time() - start_time))

    start_time = time.time()
    d = Worker(
        func, "queryParameters", iterable=date_list, configFile=cf,
        instrument=instrument).seq()
    pprint(d)
    print("--- %s seconds ---" % (time.time() - start_time))
    """
