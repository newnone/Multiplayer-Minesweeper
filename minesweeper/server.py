#!/usr/bin/python3.2

from socket import *
from minesweeper.message import *
from concurrent.futures import Future, ThreadPoolExecutor


class MineSweeperServer:
    HOST = ''
    PORT_DEFAULT = 3666
    LISTEN_BACKLOG = 0
    MAX_CLIENTS = 4

    def __init__(self, board, port=PORT_DEFAULT, debug=False):
        self.board = board
        self.debug = debug
        self.futures_to_connections = dict()

        self.server = socket(AF_INET, SOCK_STREAM)
        self.server.bind((self.HOST, port))
        self.server.listen(self.LISTEN_BACKLOG)

        self.executor = ThreadPoolExecutor(self.MAX_CLIENTS)
        self.is_closed = False

        # TO-DO Replace print statements with more appropriate log primitives for debugging
        if debug:
            print("Listening at port %d..." % port)

    def __repr__(self):
        repr_unknown = "unknown"

        if not self.is_closed:
            host = self.server.getsockname()[0] or repr_unknown
            port = self.server.getsockname()[1] or repr_unknown
        else:
            host = port = None

        return "<%s object, host = %s, port = %s, debug = %s>" %\
               (MineSweeperServer.__name__, host, port, self.debug)

    def __iter__(self):
        return iter(self.futures_to_connections.values())

    def close(self):
        for future in self.futures_to_connections.keys():
            self.make_shutdown_client().shutdown_client(future)

        self.server.shutdown(SHUT_RDWR)
        self.server.close()
        self.is_closed = True

        if self.debug:
            print(repr(self))

    def run_next_connection(self):
        if self.is_full():
            if self.debug:
                print(
                    "Reached maximum number of connections: %d/%d occupied" %
                    (len(self.futures_to_connections), self.MAX_CLIENTS)
                )
            return None
        else:
            connection = Connection(
                self.board,
                self.server.accept()[0],
                self.debug
            )
            future = self.executor.submit(connection)
            future.add_done_callback(self.make_shutdown_client())
            future.add_done_callback(self.make_close_if_no_connections())

            self.futures_to_connections[future] = connection

            return future, self.futures_to_connections[future]

    def is_full(self):
        return len(self.futures_to_connections) >= self.MAX_CLIENTS

    # Perhaps not the most elegant way to fix the argument passing of Future's add_done_callback(), but I expect
    # this closure to work, and this is what matters at the moment of this writing.
    # A future improvement may be something to consider.
    def make_shutdown_client(self):

        def shutdown_client(future):
            if future is not None:
                connection = self.futures_to_connections[future]

                if connection is not None:
                    connection.close()
                del self.futures_to_connections[future]

                if self.debug:
                    print("Connection closed: %d/%d still running" %
                          (len(self.futures_to_connections), self.MAX_CLIENTS))

        return shutdown_client

    def make_close_if_no_connections(self):

        def close_if_no_connections(future):
            if len(self.futures_to_connections) == 0:
                self.close()

        return close_if_no_connections


class Connection:

    def __init__(self, board, client, debug=False):
        self.board = board
        self.client = client
        self.debug = debug

    def __repr__(self):
        return repr(self.client)

    def __del__(self):
        self.close()

    def __call__(self, *args, **kwargs):
        return self.start()

    def start(self):
        if self.debug:
            print("%s:%s connected" % self.client.getpeername())

        # TO-DO Verify open() is being used correctly
        with open(self.client.fileno()) as stream:
            in_message = UTSMessage.parse_infer_type(stream.readline())

            while in_message is not None:
                if self.debug:
                    print("%s: %s" % (self.client, in_message))

                out_message = self._craft_out_from_in_message(UTSMessage.parse_infer_type(in_message))
                in_message = UTSMessage.parse_infer_type(stream.readline())

    def close(self):
        client_string = str(self.client)

        if self.client is not None:
            self.client.close()

        if self.debug:
            print("%s closed" % client_string)

    def _craft_out_from_in_message(self, in_message):
        result = None

        if type(in_message) is UTSLookMessage:
            pass
        elif type(in_message) is UTSDigMessage:
            pass
        elif type(in_message) is UTSFlagMessage:
            pass
        elif type(in_message) is UTSDeflagMessage:
            pass
        elif type(in_message) is UTSHelpRequestMessage:
            pass
        elif type(in_message) is UTSByeMessage:
            pass

        return result
