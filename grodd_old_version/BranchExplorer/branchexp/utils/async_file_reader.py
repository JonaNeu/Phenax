import queue
import threading


class AsynchronousFileReader(threading.Thread):
    """ Helper class to implement asynchronous reading of a file in a separate
    thread. Pushes read lines on a queue to be consumed in another thread. """

    __author__ = "soxofaan on GitHub"

    def __init__(self, fd):
        self.fd = fd
        self.queue = queue.Queue()
        threading.Thread.__init__(self)
        self.daemon = True
        self.shutdown_flag = threading.Event()

    def run(self):
        """ The body of the thread: read lines and put them on the queue. """
        while not self.shutdown_flag.is_set():
            line = self.fd.readline()
            if not line:
                break
            self.queue.put(line)

    def eof(self):
        """ Check whether there is no more content to expect. """
        return not self.is_alive() and self.queue.empty()

    def readlines(self):
        """ Get currently available lines. """
        while not self.queue.empty():
            yield self.queue.get()
