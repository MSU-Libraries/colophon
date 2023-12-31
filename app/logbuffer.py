"""
Loging buffering
"""
import logging
import itertools
from logging.handlers import BufferingHandler

class LogBuffer(BufferingHandler):
    """
    Buffer log entries (level and message) for later logging, maybe.
    """
    # pylint: disable=protected-access
    buffered_handlers = []
    the_buffer = None

    @classmethod
    def start_buffer(cls):
        """Replace existing root loghandler(s) with an instance of LogBuffer, which
        will buffer log messages until end_buffer() is called."""
        if cls.the_buffer is not None:
            raise RuntimeError("Called LogBuffer.start_buffer() while a buffer is already started.")

        logger = logging.getLogger()
        logging._acquireLock()
        # Grab the existing handlers
        while logger.hasHandlers():
            cls.buffered_handlers.append(logger.handlers.pop(0))
        # Put the buffer handler in place
        cls.the_buffer = cls(cls.buffered_handlers)
        logger.addHandler(cls.the_buffer)
        logging._releaseLock()

    @classmethod
    def end_buffer(cls, *, discard=False):
        """Stop buffering and restore the original root loghandler(s). Optionally, discard
        all log message since the buffer started.
        Args:
            discard: If True, discard all messages since start_buffer; else writes buffered logs.
        """
        if cls.the_buffer is None:
            raise RuntimeError("Called LogBuffer.end_buffer() while a no buffer was started.")

        logger = logging.getLogger()
        logging._acquireLock()
        # Either write logs or throw them away
        if discard:
            cls.the_buffer.clear()
        else:
            cls.the_buffer.flush()
        # Restore the previous handlers
        logger.removeHandler(cls.the_buffer)
        cls.the_buffer = None
        for handler in cls.buffered_handlers:
            logger.addHandler(handler)
        cls.buffered_handlers.clear()
        logging._releaseLock()

    def __init__(self, targets: list):
        super().__init__(10000)
        self.targets = targets

    def clear(self):
        """Discard all buffered log messages"""
        self.acquire()
        try:
            self.buffer.clear()
        finally:
            self.release()

    def flush(self):
        """Write all buffered messages to original loghandlers, emptying buffer"""
        self.acquire()
        try:
            for record, target in itertools.product(self.buffer, self.targets):
                target.handle(record)
            self.buffer.clear()
        finally:
            self.release()
