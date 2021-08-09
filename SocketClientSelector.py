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
                #print("Thread {} got some work: {}".format(self, self.w))
            #print("writer connecting...")
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
                #print("Socket still active...")
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
    size = 20
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
        try:
            time.sleep(1)
            print("Active threads: {}".format(len(threading.enumerate())))
            show_remaining_work_in_threadpool(threadpool)
            for _thread in threadpool:
                if not _thread.work.empty() and thread.w == None:
                    continue # pool still alive, skip else
            else:
                break
        except Exception:
            continue

    print(len(threadpool))
    show_remaining_work_in_threadpool(threadpool)
    print("Thread pool drained and work is complete.")
