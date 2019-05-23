import copy
import logging
import dates
import multiprocessing
from pprint import pprint
from api import oanda, exceptions
from queue import Queue
from threading import Thread, Lock

log = logging.getLogger(__name__)


class Worker(Thread):

    def __init__(self, d, date_gen, func, **kwargs):
        """
        :param queue: an iterable containing dictionary items whose keys
        correspond to the target api queryParameters. These queryParameters are
        contained in a dictionary argument that is parsed to the func that
        wraps the api. The parameter argument used by func is parsed as a
        kwarg.
        :param func: the function that wraps the api  whose arguments are
        parsed as kwargs.
        :param kwargs: where func arguments are parsed. One of these arguments
        will be the queryParameters dictionary that is modified by data present
        in the queue.
        """
        self.d = d
        self.date_gen = date_gen
        self.func = func
        self.kwargs = kwargs

    def run_single(self):
        """
        Functional to sequential download ticker data as defined by each
        dataset in the iterable self.queue.
        The functional intential uses a for loop. For more optimized methods
        threading and multiprocessing options are defined below.
        """
        for parameter_set in self.date_gen:
            for parameter in parameter_set.keys():
                self.kwargs["queryParameters"][parameter] = \
                        parameter_set[parameter]
            try:
                data = self.func(self.kwargs["configFile"],
                                 self.kwargs["instrument"],
                                 self.kwargs["queryParameters"],
                                 self.kwargs["live"])
            except Exception as e:
                log.info(e)
            finally:
                self.d[self.kwargs["queryParameters"]["from"]] = data.json()


class ConcurrentWorker(Worker):  # Thread

    def __init__(self, d, date_gen, func, **kwargs):
        super().__init__(self, d, date_gen, func, **kwargs)
        self.__lock = Lock()
        self.__q = Queue()

    def __thread_func(self, parameter_set):
        """
        Private function that wraps api function. Two important features are:
            1. self.__lock will preserve the kwargs["queryParameters"] dict,
            as it is modified with each item from the iterable. Necessary to
            ensure the api function is called accurately and written back to
            the correct key in the dictionary parsed in the following function.
            Additionally, this is useful for logging to present sequentially.
            2. The function is intentionally designed to generically update any
            queryParameters dict key:value pair. This should shape a framework
            for api endpoint functions.
        :param parameter_set: the item/job as it is parsed from the queue of
        jobs. Specifically it is a dict type item whose keys correspond to keys
        in the queryParameters argument for the api function.
        """
        # when this exits, the print_lock is released
        with self.__lock:
            # print(num)
            # do_work function, aka function that hits api endpoint.
            for parameter in parameter_set.keys():
                self.kwargs["queryParameters"][parameter] = \
                        parameter_set[parameter]
            log.info("Call commenced with queryParameters: {}"
                     .format(self.kwargs["queryParameters"]))
            try:
                data = self.func(self.kwargs["configFile"],
                                 self.kwargs["instrument"],
                                 self.kwargs["queryParameters"],
                                 self.kwargs["live"])
            except exceptions.OandaError as e:
                log.info(e.oanda_msg)
                resp = e.oanda_msg
            else:
                msg = "Ticker data from {0} to {1} processed.".format(
                    self.kwargs["queryParameters"]["from"],
                    self.kwargs["queryParameters"]["to"])
                log.info(msg)
                resp = data.df()
            finally:
                return resp

    def __threader(self, d):
        while True:
            # get the job from the front of the queue
            item = self.__q.get()
            if item is None:
                break
            # d.append(threadTest(item))
            d[item["from"]] = self.__thread_func(item)
            self.__q.task_done()

    def run_concurrently(self):
        # q = Queue()
        t = []
        # d = {}
        for i in range(4):
            thread = Thread(target=self.__threader, args=(self.d,))
            # this ensures the thread will die when the main thread dies
            # can set t.daemon to False to keep running
            thread.daemon = True
            thread.start()
            t.append(thread)

        self.__q.join()

        for job in self.date_gen:  # dates.Select().by_month(period=20)
            self.__q.put(job)

        for i in range(4):
            self.__q.put(None)

        for threads in t:
            threads.join()

        return self.d


class ParallelWorker(Worker):

    def __init__(self, date_gen, func, **kwargs):
        super().__init__(self, date_gen, func, **kwargs)

    def target(self, iterable):
        k = {}
        func = iterable[0]
        configFile = iterable[1]["configFile"]
        instrument = iterable[1]["instrument"]
        queryParameters = iterable[1]["queryParameters"]
        live = iterable[1]["live"]
        resp = None
        try:
            data = func(configFile, instrument, queryParameters, live)
        except exceptions.OandaError as e:
            resp = e.oanda_msg
        except Exception as e:
            resp = e
        else:
            resp = data.df().head(5)
        finally:
            k[(queryParameters["from"], queryParameters["to"])] = resp
        return k

    def run_parallel(self):  # (d, date_gen, func, **kwargs)
        arg_list = []
        for parameter_set in self.date_gen:
            sub_list = []
            sub_list.append(self.func)
            for parameter in parameter_set.keys():
                self.kwargs["queryParameters"][parameter] = \
                        parameter_set[parameter]
            sub_list.append(self.kwargs)  # kwargs)
            arg_list.append(copy.deepcopy(sub_list))

        with multiprocessing.Manager() as manager:
            ml = manager.list(arg_list)
            pool = multiprocessing.Pool(processes=4)
            for i in pool.map(self.target, ml):
                pprint(i)
            # for i in pool.map(self.target, l):
            #    pprint(i)
            pool.close()
            pool.join()


if __name__ == "__main__":
    import time
    # from pprint import pprint
    f = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=f)
    kwargs = {"configFile": "config.ini",
              "instrument": "AUD_JPY",
              "queryParameters": {"granularity": "D"},
              "live": False}
    func = oanda.Candles
    date_gen = dates.Select().by_month(period=50)
    date_list = []
    for i in date_gen:
        date_list.append(i)
    d = {}
    configFile = "config.ini"
    instrument = "AUD_JPY"
    queryParameters = {"granularity": "D"}
    live = False

    start_time = time.time()
    ParallelWorker(date_gen=date_list,
                   func=func,
                   configFile=configFile,
                   instrument=instrument,
                   queryParameters=queryParameters,
                   live=live).run_parallel()
    # main_complete(d=d, date_gen=date_gen, func=func, configFile=configFile,
    #              instrument=instrument, queryParameters=queryParameters,
    #              live=live)
    print("--- %s seconds ---" % (time.time() - start_time))
    """--- 0.18308568000793457 seconds ---"""

    # start_time = time.time()
    # print("--- %s seconds ---" % (time.time() - start_time))
    """--- 8.530192136764526 seconds ---"""
    """
    def target(parameter_set, func, configFile, instrument, queryParameters,
               live=False):
        # lock.acquire()
        for parameter in parameter_set.keys():
            queryParameters[parameter] = parameter_set[parameter]
        log.info("Call commenced with queryParameters: {}"
                 .format(queryParameters))
        try:
            data = func(configFile, instrument, queryParameters, live)
        except exceptions.OandaError as e:
            log.info(e.oanda_msg)
            resp = e.oanda_msg
        else:
            msg = "Ticker data from {0} to {1} processed.".format(
                queryParameters["from"],
                queryParameters["to"])
            log.info(msg)
            resp = data.df()
        finally:
            # lock.release()
            return resp

    def init(l):
        global lock
        lock = l

    def main_partial(func, configFile, instrument, queryParameters, live):
        iterable = []
        for i in dates.Select().by_month(period=5):
            iterable.append(i)
        # l_ = multiprocessing.Lock()
        # pool = multiprocessing.Pool(initializer=init, initargs=(l_,))
        pool = multiprocessing.Pool(processes=4)
        pool.map(functools.partial(target,
                                   func=func,
                                   configFile=configFile,  # "config.ini",
                                   instrument=instrument,  # "AUD_JPY",
                                   queryParameters=queryParameters,
                                   live=live), iterable)
        pool.close()
        pool.join()

    # start_time = time.time()
    # main_partial(func=func,
    #             configFile=configFile,  # "config.ini",
    #             instrument=instrument,  # "AUD_JPY",
    #             queryParameters=queryParameters,
    #             live=live)
    # print("--- %s seconds ---" % (time.time() - start_time))
    """
    """--- 2.61875319480896 seconds ---"""

    # configFile, instrument, queryParameters, live
