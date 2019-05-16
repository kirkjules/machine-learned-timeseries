import logging
from queue import Queue
from threading import Thread

log = logging.getLogger(__name__)


class DownloadWorker(Thread):

    def __init__(self, queue, func, **kwargs):
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
        Thread.__init__(self)
        self.queue = queue
        self.func = func
        self.kwargs = kwargs

    def run_single(self, d):
        """
        Functional to sequential download ticker data as defined by each
        dataset in the iterable self.queue.
        The functional intential uses a for loop. For more optimized methods
        threading and multiprocessing options are defined below.
        """
        for parameter_set in self.queue:
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
                d[self.kwargs["queryParameters"]["from"]] = data.json()
                print("Completed: {0} to {1}".format(
                    self.kwargs["queryParameters"]["from"],
                    self.kwargs["queryParameters"]["to"]))
                print("{0} {1}".format(data.status, len(data.df())))

    def run_thread(self):
        while True:
            # Get the work from the queue
            from_, to = self.queue.get()
            self.kwargs["arguments"]["from"] = from_
            self.kwargs["arguments"]["to"] = to
            try:
                self.func(self.kwargs)
            except Exception as e:
                log.info(e)
            finally:
                self.queue.task_done()


def thread_main(date_gen):
    # Create a queue to communicate with the worker threads.
    queue = Queue()
    for x in range(8):
        worker = DownloadWorker(queue)
        # Setting daemon to True will let the main thread exit even though
        # the workers are blocking
        worker.daemon = True
        worker.start()
    # Put the tasks into the queue as a tuple.
    for s in date_gen:
        log.info("Queueing {}".format(s))
        queue.put(s)
    # Causes the main thread to wait for the queue to finish processing
    # all the tasks.
    queue.join()
    log.info("Complete.")
