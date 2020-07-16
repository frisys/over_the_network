import json
import logging
import logging.handlers
import pickle
import struct
from typing import Optional


class HogeSocketHandler(logging.handlers.SocketHandler):
    def __init__(self, host: str, port: Optional[int], params: dict):
        super().__init__(host, port)
        self.params = params

    def makePickle(self, record):
        """
        Pickles the record in binary format with a length prefix, and
        returns it ready for transmission across the socket.
        """
        ei = record.exc_info
        if ei:
            # just to get traceback text into record.exc_text ...
            _ = self.format(record)
        # See issue #14436: If msg or args are objects, they may not be
        # available on the receiving end. So we convert the msg % args
        # to a string, save it as msg and zap the args.
        d = dict(record.__dict__)
        d['msg'] = record.getMessage()
        d['args'] = None
        d['exc_info'] = None
        d['my_param'] = json.dumps(self.params)
        # Issue #25685: delete 'message' if present: redundant with 'msg'
        d.pop('message', None)
        s = pickle.dumps(d, 1)
        slen = struct.pack(">L", len(s))
        return slen + s


root_logger = logging.getLogger('')
root_logger.setLevel(logging.DEBUG)
socket_handler = HogeSocketHandler('localhost', logging.handlers.DEFAULT_TCP_LOGGING_PORT, {"logger": "root"})
# don't bother with a formatter, since a socket handler sends the event as
# an unformatted pickle
root_logger.addHandler(socket_handler)

# Now, we can log to the root logger, or any other logger. First the root...
logging.info('Jackdaws love my big sphinx of quarts.')

# Now, define a couple of other loggers which might represent areas in your
# application:

root_logger.handlers.clear()
socket_handler_2 = HogeSocketHandler('localhost', logging.handlers.DEFAULT_TCP_LOGGING_PORT, {"logger": "logger1"})
root_logger.addHandler(socket_handler_2)
logger1 = logging.getLogger('myapp.area1')
logger1.debug('Quick zephyrs blow, vexing daft Jim.')
logger1.info('How quickly daft jumping zebras vex.')

root_logger.handlers.clear()
socket_handler_3 = HogeSocketHandler('localhost', logging.handlers.DEFAULT_TCP_LOGGING_PORT, {"logger": "logger2"})
root_logger.addHandler(socket_handler_3)
logger2 = logging.getLogger('myapp.area2')
logger2.warning('Jail zesty vixen who grabbed pay from quack.')
logger2.error('The five boxing wizards jump quickly.')
