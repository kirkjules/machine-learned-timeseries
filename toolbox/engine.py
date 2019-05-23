import os
import copy
import logging
import dates
# import functools
import multiprocessing
from pprint import pprint
from api import oanda, exceptions
from queue import Queue
from threading import Thread, Lock

log = logging.getLogger(__name__)


class Worker(Thread):

    def __init__(self, date_gen, func, **kwargs):
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
        self.date_gen = date_gen
        self.func = func
        self.kwargs = kwargs
        self.arg_list = []
        for parameter_set in self.date_gen:
            sub_list = []
            sub_list.append(self.func)
            for parameter in parameter_set.keys():
                self.kwargs["queryParameters"][parameter] = \
                        parameter_set[parameter]
            sub_list.append(self.kwargs)  # kwargs)
            self.arg_list.append(copy.deepcopy(sub_list))

    def run_single(self):
        """
        Functional to sequential download ticker data as defined by each
        dataset in the iterable self.queue.
        The functional intential uses a for loop. For more optimized methods
        threading and multiprocessing options are defined below.
        """
        results = []
        for iterable in self.arg_list:
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
                # k[(queryParameters["from"], queryParameters["to"])] = resp
                log.info("{0}, {1}: {2}".format(os.getpid(),
                                                queryParameters["from"]
                                                .replace(".000000000Z", ""),
                                                queryParameters["to"]
                                                .replace(".000000000Z", "")))
                results.append(resp)  # k

        # pprint(results)
        return results


class ConcurrentWorker(Worker):  # Thread

    def __init__(self, date_gen, func, **kwargs):
        super().__init__(date_gen, func, **kwargs)
        self.__lock = Lock()
        self.__q = Queue()

    def __thread_func(self, iterable):  # parameter_set):
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
            with self.__lock:
                # k[(queryParameters["from"], queryParameters["to"])] = resp
                log.info("{0}, {1}: {2}".format(os.getpid(),
                                                queryParameters["from"]
                                                .replace(".000000000Z", ""),
                                                queryParameters["to"]
                                                .replace(".000000000Z", "")))
        return resp

    def __threader(self, d):
        while True:
            # get the job from the front of the queue
            item = self.__q.get()
            if item is None:
                break
            d.append(self.__thread_func(item))
            # d[item[1]["queryParameters"]["from"]] = self.__thread_func(item)
            self.__q.task_done()

    def run_concurrently(self):
        # q = Queue()
        t = []
        results = []
        for i in range(4):
            thread = Thread(target=self.__threader, args=(results,))
            # this ensures the thread will die when the main thread dies
            # can set t.daemon to False to keep running
            thread.daemon = True
            thread.start()
            t.append(thread)

        self.__q.join()

        # for job in self.date_gen:  # dates.Select().by_month(period=20)
        for job in self.arg_list:
            self.__q.put(job)

        for i in range(4):
            self.__q.put(None)

        for threads in t:
            threads.join()

        pprint(results)
        return results


class ParallelWorker(Worker):

    def __init__(self, date_gen, func, **kwargs):
        super().__init__(date_gen, func, **kwargs)

    def init_lock(self, l_):
        global lock
        lock = l_

    def target(self, iterable):
        # k = {}
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
            # k[(queryParameters["from"], queryParameters["to"])] = resp
            lock.acquire()
            log.info("{0}, {1}: {2}".format(os.getpid(),
                                            queryParameters["from"]
                                            .replace(".000000000Z", ""),
                                            queryParameters["to"]
                                            .replace(".000000000Z", "")))
            lock.release()
        return resp  # k

    def run_parallel(self):  # (d, date_gen, func, **kwargs)
        l_ = multiprocessing.Lock()
        pool = multiprocessing.Pool(processes=4,
                                    initializer=self.init_lock,
                                    initargs=(l_,))
        results = []
        for i in pool.map(self.target, self.arg_list):
            results.append(i)

        pool.close()
        pool.join()
        pprint(results)


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
    date_gen = dates.Select().by_month(period=25)
    date_list = []
    for i in date_gen:
        date_list.append(i)
    d = {}
    configFile = "config.ini"
    instrument = "AUD_JPY"
    queryParameters = {"granularity": "M15"}
    live = False
    start_time = time.time()
    print("ConcurrentWorker\n")
    ConcurrentWorker(d=d,
                     date_gen=date_list,
                     func=func,
                     configFile=configFile,
                     instrument=instrument,
                     queryParameters=queryParameters,
                     live=live).run_concurrently()
    print("--- %s seconds ---" % (time.time() - start_time))
    print("\nParallelWorker\n")
    start_time = time.time()
    ParallelWorker(date_gen=date_list,
                   func=func,
                   configFile=configFile,
                   instrument=instrument,
                   queryParameters=queryParameters,
                   live=live).run_parallel()
    print("--- %s seconds ---" % (time.time() - start_time))
"""
    start_time = time.time()
    Worker(date_gen=date_list,
           func=func,
           configFile=configFile,
           instrument=instrument,
           queryParameters=queryParameters,
           live=live).run_single()
    print("--- %s seconds ---" % (time.time() - start_time))
"""
