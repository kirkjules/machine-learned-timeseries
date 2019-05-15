import logging
from queue import Queue
from threading import Thread

log = logging.getLogger(__name__)


class DownloadWorker(Thread):

    def __init__(self, queue, func, **kwargs):
        Thread.__init__(self)
        self.queue = queue
        self.func = func
        self.kwargs = kwargs

    def run_single(self):
        for i in self.queue:
            from_, to = i
            self.kwargs["queryParameters"]["from"] = from_
            self.kwargs["queryParameters"]["to"] = to
            try:
                self.func(self.kwargs["configfile"],
                          self.kwargs["instrument"],
                          self.kwargs["queryParameters"],
                          self.kwargs["live"])
            except Exception as e:
                log.info(e)
            finally:
                print("Completed.")

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
