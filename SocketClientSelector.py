import json
import math
import selectors
import socket
import sys
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
        self.w = None # current job
        super().__init__(*args, **kwargs)

    def _reset_socket(self):
        self.sock = socketutf8.SocketUtf8()

    def run(self):

        while not self.work.empty() or self.w:
            if not self.w:
                self.w = self.work.get()
                print("Thread {} got some work: {}".format(self, self.w))
            print("writer connecting...")
            try:
                self.sock.connect(self.conn)
                self.sock.setblocking(False)
                # how does DefaultSelector interact with other selectors? It's at the system level, how? (see lpi book p 1330)
                # but 1 selector per thread also seems strange. trying selector as class variable
                self.sel.register(self.sock, selectors.EVENT_WRITE, self.writesock)
            except ConnectionRefusedError:
                print("Connection refused... continuing....")
            except socket.gaierror:
                print("Connection refused... continuing....")
            except IOError:
                print("Write refused... continuing....")
            except Exception:
                print("Not sure what happend... continuing....")

            while self.sock:
                print("Socket still active...")
                events = self.sel.select()
                for key, mask in events:
                    callback = key.data
                    callback(key.fileobj, mask)
            # an atomic finally: this is executed when we hit the loop exit normally
            else:
                #print("Resetting socket!")
                self._reset_socket()

    def writesock(self, _, __):
        ''' not sure how to use key.fileobj and mask in this context yet, maybe useless
        '''
        # struct.error: ushort format requires 0 <= number <= (32767 *2 +1)
        data = 'a' * (2**16 - 1)
        res = self.sock.struct_send(data.encode('utf-8'), compression=0)
        if res == -1:
            print("Send failed: {} work: {}".format(self, self.w))
            # Will this retry without putting it back on the stack?
            self.work.put(self.w)

        self.sel.unregister(self.sock) # maybe after closing the socket to keep count correctly?
        #print("Socket closing: {}".format(self.sock))
        self.sock.close()
        self.sock = None # fill while condition
        self.w = None # expire the work

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
        print("Thread {} jobs left: {}".format(_thread, _thread.work.qsize()))


if __name__ == '__main__':
    import time
    import sys

    HOST = socket.gethostname()
    PORT = 8080
    conn = (HOST, PORT)
    work_count = 10000

    # now it's time to build a thread pool, and each thread can have a selector pool and work on each of its fds
    system_fds = 250
    #size = int(math.floor(system_fds/10)) # around 10 selectors per thread
    size = 2
    threadpool = create_threadpool(Client, size, conn)
    print("Threadpool size: {}".format(len(threadpool)))

    # dummy work for now
    work = list(range(work_count)) # the contents of work don't matter yet, but the send data could go here... it's currently in the Client thread as things evolved.

    # distribute work evenly
    for i, w in enumerate(work):
        # modulo by length of threadpool to distribute work
        threadpool[i%len(threadpool)].work.put(w)

    show_remaining_work_in_threadpool(threadpool)
    start_threadpool(threadpool)

    while True:
        time.sleep(1)
        print("Active threads: {}".format(len(threading.enumerate())))
        show_remaining_work_in_threadpool(threadpool)
        for _thread in threadpool:
            if not _thread.work.empty():
                continue # pool still alive, skip else
        else:
            break

    print(len(threadpool))
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
