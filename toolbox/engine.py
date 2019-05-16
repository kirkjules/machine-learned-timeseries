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

    def __threadTest(self, num):
        # when this exits, the print_lock is released
        with self.__lock:
            # print(num)
            # do_work function, aka function that hits api endpoint.
            for parameter in num.keys():
                self.kwargs["queryParameters"][parameter] = num[parameter]
                try:
                    data = self.func(self.kwargs["configFile"],
                                     self.kwargs["instrument"],
                                     self.kwargs["queryParameters"],
                                     self.kwargs["live"])
                except Exception as e:
                    log.info(e)
                finally:
                    print("From: {}".format(self.kwargs["queryParameters"]
                                            ["from"]))
                    return(data.df())

    def __threader(self, d):
        while True:
            # get the job from the front of the queue
            item = self.__q.get()
            if item is None:
                break
            # d.append(threadTest(item))
            d[item["from"]] = self.__threadTest(item)
            self.__q.task_done()

    def run(self):
        # q = Queue()
        t = []
        d = {}
        for i in range(4):
            thread = Thread(target=self.__threader, args=(d,))
            # this ensures the thread will die when the main thread dies
            # can set t.daemon to False to keep running
            thread.daemon = False
            thread.start()
            t.append(thread)

        self.__q.join()

        for job in self.date_gen:  # dates.Select().by_month(period=20)
            self.__q.put(job)

        print(t)

        for i in range(4):
            self.__q.put(None)

        for threads in t:
            threads.join()

        print(t)

        # pprint(d)
        for f in d.keys():
            print(d[f].head(5))


"""
def threadTest(num):
    # when this exits, the print_lock is released
    with print_lock:
        # print(num)
        # do_work function, aka function that hits api endpoint.
        for parameter in num.keys():
            kwargs["queryParameters"][parameter] = num[parameter]
            try:
                func(kwargs["configFile"],
                     kwargs["instrument"],
                     kwargs["queryParameters"],
                     kwargs["live"])
            except Exception as e:
                print(e)
            finally:
                print("From: {}".format(kwargs["queryParameters"]["from"]))
                return(kwargs["queryParameters"]["from"])



def threader(d):
    while True:
        # get the job from the front of the queue
        item = q.get()
        if item is None:
            break
        # d.append(threadTest(item))
        d[item["from"]] = threadTest(item)
        q.task_done()
"""

if __name__ == "__main__":
    """
    q = Queue()
    t = []
    d = {}
    for i in range(4):
        thread = Thread(target=threader, args=(d,))
        # this ensures the thread will die when the main thread dies
        # can set t.daemon to False to keep running
        thread.daemon = False
        thread.start()
        t.append(thread)

    q.join()

    for job in dates.Select().by_month(period=20):  # range(10):
        q.put(job)

    print(t)

    for i in range(4):
        q.put(None)

    for threads in t:
        threads.join()

    print(t)

    print(d.keys())
    """
    # print_lock = Lock()
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
                   live=False).run()
