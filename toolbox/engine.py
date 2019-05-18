import dates
import logging
# from pprint import pprint
from api import oanda
from queue import Queue
from threading import Thread, Lock

log = logging.getLogger(__name__)


class DownloadWorker(Thread):

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
        self.__lock = Lock()
        self.__q = Queue()

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
                try:
                    data = self.func(self.kwargs["configFile"],
                                     self.kwargs["instrument"],
                                     self.kwargs["queryParameters"],
                                     self.kwargs["live"])
                except Exception as e:
                    log.info(e)
                finally:
                    msg = "Ticker data from {0} to {1} processed.".format(
                        self.kwargs["queryParameters"]["from"],
                        self.kwargs["queryParameters"]["to"])
                    log.info(msg)
                    # print("From: {}".format(self.kwargs["queryParameters"]
                    #                        ["from"]))
                    return(data.df())

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
            thread.daemon = False
            thread.start()
            t.append(thread)

        self.__q.join()

        for job in self.date_gen:  # dates.Select().by_month(period=20)
            self.__q.put(job)

        # print(t)

        for i in range(4):
            self.__q.put(None)

        for threads in t:
            threads.join()

        return self.d
        # print(t)

        # pprint(d)
        # for f in d.keys():
        #    print(d[f].head(5))


if __name__ == "__main__":
    kwargs = {"configFile": "config.ini",
              "instrument": "AUD_JPY",
              "queryParameters": {"granularity": "D"},
              "live": False}
    func = oanda.Candles
    date_gen = dates.Select().by_month(period=5)
    d = {}
    DownloadWorker(d=d,
                   date_gen=date_gen,
                   func=func,
                   configFile="config.ini",
                   instrument="AUD_JPY",
                   queryParameters={"granularity": "D"},
                   live=False).run_concurrently()
    for f in d.keys():
        print(d[f].head(5))
