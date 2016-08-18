"""CanQueue

This module provides a queue-based method of interaction with the CAN bus. Incoming messages are serviced by a thread and are added to the receive queue. Outgoing messages are enqueued and transmitted by the transmission thread.

"""

from canard import can
import multiprocessing

try:
    import queue
except ImportError:
    import Queue as queue

import time


def indirect_caller(instance, name, args=(), kwargs=None):
    """Indirect function caller for instance methods and multiprocessing to make CanQueue pickleable"""
    if kwargs is None:
        kwargs = {}
    return getattr(instance, name)(*args, **kwargs)


class CanQueue:
    """Queue-based interface to the CAN bus"""

    def __init__(self, can_dev, maxsize=0):
        self.can_dev = can_dev
        self.recv_process = multiprocessing.Process(target=indirect_caller, args=(self, 'recv_task'))
        self.send_process = multiprocessing.Process(target=indirect_caller, args=(self, 'send_task'))
        self.recv_queue = multiprocessing.Queue(maxsize=maxsize)
        self.send_queue = multiprocessing.Queue(maxsize=maxsize)

    def start(self):
        """Start the CAN device and queue processes"""
        self.can_dev.start()
        self.recv_process.start()
        self.send_process.start()

    def stop(self):
        """Stop the CAN device and queue processes"""
        self.recv_process.terminate()
        self.send_process.terminate()
        self.can_dev.stop()

    def send(self, msg):
        """Enqueue a message for sending"""
        self.send_queue.put(msg)

    def recv(self, timeout=1, filter=None):
        """Receive one message from the queue"""
        try:
            start_time = time.time()
            while True:
                msg = self.recv_queue.get(timeout=timeout)

                # TODO: Move filter to receive task
                if not filter:
                    return msg
                elif filter == msg.id:
                    return msg
                # ensure we haven't gone over the timeout
                if time.time() - start_time > timeout:
                    return None

        except queue.Empty:
            return None

    def recv_all(self, overrun=100):
        """Receive a list of all items in the queue"""
        result = []
        ctr = 0;

        # Loop through all items in the queue and add them to the list (up to "overrun" items)
        while (not self.recv_queue.empty()) and ctr < overrun:
            result.append(self.recv_queue.get())
            ctr += 1

        return result

    def recv_task(self):
        """CAN receiver, called by the receive process"""
        while True:
            msg = self.can_dev.recv()
            self.recv_queue.put(msg)

    def send_task(self):
        """CAN transmitter, called by the transmit process"""
        while True:
            msg = self.send_queue.get()
            self.can_dev.send(msg)


