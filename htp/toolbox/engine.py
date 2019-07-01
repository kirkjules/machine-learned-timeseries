import os
import copy
import logging
import multiprocessing
from queue import Queue
from threading import Thread, Lock
from htp.api import exceptions

log = logging.getLogger(__name__)


class Worker(Thread):

    def __init__(self, date_gen, func, **kwargs):
        """
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
            sub_list = {}  # []
            # sub_list.append(self.func)
            sub_list["func"] = self.func
            for parameter in parameter_set.keys():
                self.kwargs["queryParameters"][parameter] = \
                        parameter_set[parameter]
            # sub_list.append(self.kwargs)  # kwargs)
            for argument in self.kwargs.keys():
                sub_list[argument] = self.kwargs[argument]
            self.arg_list.append(copy.deepcopy(sub_list))

    def run(self):
        """
        Function to sequentially download ticker data as defined by each
        dataset in the iterable self.arg_list.
        The function intentially uses a for loop. For more optimized methods,
        threading and multiprocessing options are defined below.
        """
        results = []
        for iterable in self.arg_list:
            func = iterable.pop("func")
            resp = None
            try:
                data = func(**iterable)
            except exceptions.OandaError as e:
                resp = e.oanda_msg
            except exceptions.ApiError as e:
                resp = e
                log.info(resp)
            else:
                resp = data  # .df()
            finally:
                log.info("{0}, {1}: {2}".format(
                    os.getpid(), iterable["queryParameters"]["from"]
                    .replace(".000000000Z", ""), iterable["queryParameters"]
                    ["to"].replace(".000000000Z", "")))
                results.append(resp)  # k

        return results


class ConcurrentWorker(Worker):  # Thread

    def __init__(self, date_gen, func, **kwargs):
        super().__init__(date_gen, func, **kwargs)
        self.__lock = Lock()
        self.__q = Queue()

    def __thread_func(self, iterable):  # parameter_set):
        """
        Private function that wraps api function.
        :param iterable: the item/job as it is parsed from the queue of
        jobs. Specifically it is a list type item whose values correspond to
        arguments in the target api function.
        """
        func = iterable.pop("func")
        resp = None
        try:
            data = func(**iterable)
        except exceptions.OandaError as e:
            resp = e.oanda_msg
        except exceptions.ApiError as e:
            resp = e
            with self.__lock:
                log.info(resp)
        else:
            resp = data  # .df()
        finally:
            with self.__lock:
                log.info("{0}, {1}: {2}".format(
                    os.getpid(), iterable["queryParameters"]["from"]
                    .replace(".000000000Z", ""), iterable["queryParameters"]
                    ["to"].replace(".000000000Z", "")))
        return resp

    def __threader(self, d):
        while True:
            # get the job from the front of the queue
            item = self.__q.get()
            if item is None:
                break
            d.append(self.__thread_func(item))
            self.__q.task_done()

    def run(self):
        """
        Method to run the target function as wrapped by __thread_func and
        directed by __threader, concurrently, on multiple threads.
        """
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

        for job in self.arg_list:
            self.__q.put(job)

        for i in range(4):
            self.__q.put(None)

        for threads in t:
            threads.join()

        # pprint(results)
        return results


class ParallelWorker(Worker):

    def __init__(self, date_gen, func, **kwargs):
        """
        ParallelWorker is a class that inherits from Worker for necessary
        attributes and then provides a pool of workers for the parsed
        task and arguments to be worked on in parallel.
        """
        super().__init__(date_gen, func, **kwargs)

    def init_lock(self, l_):
        """
        Lock initialiser used in the pool setup.
        """
        global lock
        lock = l_

    def target(self, iterable):
        """
        Target function that wraps the original api function.
        :param iterable: a list that contains to values, the first is the
        function name that will interact with the api, the second is a
        dictionary with keys matching the api function arguments.
        """
        func = iterable.pop("func")
        resp = None
        try:
            data = func(**iterable)
        except exceptions.OandaError as e:
            resp = e.oanda_msg
        except exceptions.ApiError as e:
            lock.acquire()
            resp = e
            log.info(resp)
            lock.release()
        else:
            resp = data  # .df()
        finally:
            lock.acquire()
            log.info("{0}, {1}: {2}".format(os.getpid(),
                                            iterable["queryParameters"]["from"]
                                            .replace(".000000000Z", ""),
                                            iterable["queryParameters"]["to"]
                                            .replace(".000000000Z", "")))
            lock.release()
        return resp  # k

    def run(self):  # (d, date_gen, func, **kwargs)
        """
        Method to run target function in parallel. The pool of workers is
        initialised with a lock that is used for logging in the target
        function.
        """
        l_ = multiprocessing.Lock()
        pool = multiprocessing.Pool(processes=4,
                                    initializer=self.init_lock,
                                    initargs=(l_,))
        results = []
        for i in pool.map(self.target, self.arg_list):
            results.append(i)

        pool.close()
        pool.join()

        # pprint(results)
        return results


if __name__ == "__main__":
    import time
    # from pprint import pprint
    from htp.api import oanda
    from htp.toolbox import dates

    f = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=f)

    func = oanda.Candles.to_df
    date_gen = dates.Select().by_month(period=5, no_days=[5, 6],
                                       year_by_day=True)
    date_list = []
    for i in date_gen:
        date_list.append(i)

    instrument = "AUD_JPY"
    queryParameters = {"granularity": "D"}
    cf = os.path.join(os.path.dirname(__file__), "../..", "config.yaml")

    start_time = time.time()
    d = Worker(date_gen=date_list,
               func=func,
               configFile=cf,
               instrument=instrument,
               queryParameters=queryParameters).run()
    # pprint(d)
    print("--- %s seconds ---" % (time.time() - start_time))
    """
    start_time = time.time()
    print("ConcurrentWorker\n")
    d = ConcurrentWorker(d=d,
                         date_gen=date_list,
                         func=func,
                         configFile=cf,
                         instrument=instrument,
                         queryParameters=queryParameters).run()
    print("--- %s seconds ---" % (time.time() - start_time))

    print("\nParallelWorker\n")
    start_time = time.time()
    ParallelWorker(date_gen=date_list,
                   func=func,
                   configFile=cf,
                   instrument=instrument,
                   queryParameters=queryParameters).run()
    pprint(d)
    print("--- %s seconds ---" % (time.time() - start_time))
    """
