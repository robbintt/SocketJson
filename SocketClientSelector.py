import json
import selectors
import socket
import threading

import socketutf8


class Client(threading.Thread):
    ''' Manage a socket connection
    '''

    def __init__(self, conn, *args, **kwargs):
        '''
        '''
        self.sel = selectors.DefaultSelector()
        self.conn = conn
        self.sock = socketutf8.SocketUtf8()
        super().__init__(*args, **kwargs)


    def run(self):

        print("writer connecting...")
        try:
            self.sock.connect(self.conn)
            self.sock.setblocking(False)
            # how does DefaultSelector interact with other selectors? It's at the system level, how? (see lpi book p 1330)
            # but 1 selector per thread also seems strange. trying selector as class variable
            self.sel.register(self.sock, selectors.EVENT_WRITE, self.writesock)
        except ConnectionRefusedError:
            print("Connection refused... giving up.")
            raise
        except socket.gaierror:
            print("Connection refused... giving up.")
            raise
        except IOError:
            print("Write refused... giving up.")
            raise
        except Exception:
            print("Not sure what happend... giving up.")
            raise

        while True:
            events = self.sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)
                return # we only handle one selector per thread, investigate other control flows here

    def writesock(self, _, __):
        ''' not sure how to use key.fileobj and mask in this context yet, maybe useless
        '''

        print("WRITESOCK is happening with fd {} and mask {}!".format(_, __))

        # struct.error: ushort format requires 0 <= number <= (32767 *2 +1)
        data = 'a' * (2**16 - 1)
        try:
            self.sock.struct_send(data.encode('utf-8'), compression=0)
        except OSError:
            client.sel.unregister(self.sock)
            print("Too many open files... raising to parent")
            raise

        # add context manager
        print("Exiting gracefully...")
        self.sel.unregister(self.sock) # maybe after closing the socket to keep count correctly?
        self.sock.close()
        print("Socket closed.")

if __name__ == '__main__':
    import time
    import sys

    HOST = socket.gethostname()
    PORT = 8080
    conn = (HOST, PORT)

    c = 0
    total = 10000
    num_conn = 0
    max_conn = 250
    # also need to measure closed connections
    while c < total and len(threading.enumerate()) > 0:
        #time.sleep(0.01) # 100 qps works fine with no threading and selectors on server
        #time.sleep(0.005) # 250 qps is fine with no threading and selectors on server
        # i could timeit... to see real world
        #time.sleep(0.0025) # 500 qps is fine with no threading and selectors on server
        #time.sleep(0.001) #  WORKS with new server selectors only implementation... probably better to move servers to thread pool where threads = selectors/10 or something.
        time.sleep(0.0005) # takes way longer than 0.0005 * 10000 = 5 seconds, more like 9.3 seconds. so we are at the cap for client selectors/threads=1 at 2000 qps
        #time.sleep(0.0001) # does not work with new server selectors only and 1 selector/thread on client... also transaction leak? only 9388/10000 results accounted for this run...
        try:
            print("Attempt # {}".format(c))
            print("Active threads: {}".format(len(threading.enumerate())))
            if num_conn < max_conn:
                num_conn += 1
            else:
                time.sleep(1)
                raise Exception("Too many connections, recycling thread.")
                continue
            Client(conn).start()
        except Exception:
            num_conn -= 1
            # thread will gc itself?
            continue
        finally:
            # not perfect, but captures the idea.
            # exceptions will sometimes succeed and then have an exception.
            c += 1
            num_conn -= 1
    print("{} socket connections successfully written.".format(num_conn))
