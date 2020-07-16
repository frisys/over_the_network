import json
import logging
import logging.handlers
import pickle
import socketserver
import struct


class LogRecordStreamHandler(socketserver.StreamRequestHandler):
    """
    Handler for a streaming logging request.
    This basically logs the record using whatever logging policy is configured locally.
    """
    def handle(self):
        """
        Handle multiple requests - each expected to be a 4-byte length,
        followed by the LogRecord in pickle format. Logs the record
        accoding to whatever policy is configured locally.
        :return:
        """
        while True:
            chunk = self.connection.recv(4)
            if len(chunk) < 4:
                break
            slen = struct.unpack(">L", chunk)[0]
            chunk = self.connection.recv(slen)
            while len(chunk) < slen:
                chunk = chunk + self.connection.recv(slen - len(chunk))
            obj = self.unpickle(chunk)
            my_param = json.loads(obj["my_param"])
            print("parameter from client side : %s" % my_param["logger"])
            record = logging.makeLogRecord(obj)
            self.handle_log_record(record)

    def unpickle(self, data):
        return pickle.loads(data)

    def handle_log_record(self, record):
        """
        if a name is specified, we use the named logger rather than the one
        implied by the record.
        :param record:
        :return:
        """
        if self.server.logname is not None:
            name = self.server.logname
        else:
            name = record.name
        logger = logging.getLogger(name)
        # N.B. EVERY record gets logged. This is because Logger.handle
        # is normally called AFTER logger-level filtering. If you want
        # to do filtering, do it at the client end to save wasting
        # cycles and network bandwidth!
        logger.handle(record)


class LogRecordSocketReceiver(socketserver.ThreadingTCPServer):
    """
    simple TCP socket-based logging receiver suitable for testing.
    """
    allow_reuse_address = 1

    def __init__(self, server_address='localhost',
                 port=logging.handlers.DEFAULT_TCP_LOGGING_PORT,
                 handler=LogRecordStreamHandler):
        socketserver.ThreadingTCPServer.__init__(self, (server_address, port), handler)
        self.abort = 0
        self.timeout = 1
        self.logname = None

    def serve_until_stopped(self):
        import select
        abort = 0
        while not abort:
            rd, wr, ex = select.select([self.socket.fileno()],
                                       [], [],
                                       self.timeout)
            if rd:
                self.handle_request()
            abort = self.abort


def main():
    logging.basicConfig(
        format="%(relativeCreated)5d %(name)-15s %(levelname)-8s %(message)s"
    )
    tcp_server = LogRecordSocketReceiver()
    print("About to start TCP server...")
    tcp_server.serve_until_stopped()


if __name__ == "__main__":
    main()
