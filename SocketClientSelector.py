import json
import math
import selectors
import socket
import threading
import queue

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
        self.work = queue.Queue()
        super().__init__(*args, **kwargs)

    def _reset_socket(self):
        del self.sock
        self.sock = socketutf8.SocketUtf8()

    def run(self):

        while True:
            w = self.work.get()
            print("Thread got some work: {}".format(w))
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

            while self.sock:
                print("Socket still active...")
                events = self.sel.select()
                for key, mask in events:
                    callback = key.data
                    callback(key.fileobj, mask)
            # an atomic finally: this is executed when we hit the loop exit normally
            else:
                print("Resetting socket!")
                self._reset_socket()

    def writesock(self, _, __):
        ''' not sure how to use key.fileobj and mask in this context yet, maybe useless
        '''

        print("WRITESOCK is happening with fd {} and mask {}!".format(_, __))

        # struct.error: ushort format requires 0 <= number <= (32767 *2 +1)
        data = 'a' * (2**16 - 1)
        try:
            self.sock.struct_send(data.encode('utf-8'), compression=0)
        except OSError:
            self.sel.unregister(self.sock)
            print("Too many open files... raising to parent")
            raise

        # add context manager
        print("Exiting gracefully...")
        self.sock.close()
        print("Socket closed: {}".format(self.sock))
        self.sel.unregister(self.sock) # maybe after closing the socket to keep count correctly?
        self.sock = None

def create_threadpool(ThreadClass, size, *args, **kwargs):
    pool = list()
    while size > 0:
        pool.append(ThreadClass(*args, **kwargs))
        size -= 1
    return pool

def start_threadpool(pool):
    for t in pool:
        t.start()

def show_remaining_work_in_threadpool(pool):
    for _thread in pool:
        print(_thread, _thread.work.qsize())


if __name__ == '__main__':
    import time
    import sys

    HOST = socket.gethostname()
    PORT = 8080
    conn = (HOST, PORT)
    work_count = 10000

    # now it's time to build a thread pool, and each thread can have a selector pool and work on each of its fds
    system_fds = 250
    size = int(math.floor(system_fds/10)) # around 10 selectors per thread
    threadpool = create_threadpool(Client, size, conn)
    print("Threadpool size: {}".format(len(threadpool)))

    # dummy work for now
    work = list(range(work_count)) # the contents of work don't matter yet, but the send data could go here... it's currently in the Client thread as things evolved.

    # distribute work evenly
    for i, w in enumerate(work):
        # modulo by length of threadpool to distribute work
        threadpool[i%len(threadpool)].work.put(w)

    start_threadpool(threadpool)
    #print("Active threads: {}".format(len(threading.enumerate())))
    #exit(0)

    while threadpool:
        time.sleep(1)
        print("Active threads: {}".format(len(threading.enumerate())))
        show_remaining_work_in_threadpool(threadpool)
        for i, _thread in enumerate(threadpool):
            if _thread.work.empty():
                del threadpool[i]

    print("Thread pool drained and work is complete.")



    '''
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
    '''
