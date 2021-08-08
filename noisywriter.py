import json
import socket
import threading

import socketutf8


class Client(threading.Thread):
    ''' Manage a socket connection
    '''

    def __init__(self, conn, *args, **kwargs):
        '''
        '''
        self.conn = conn
        self.sock = socketutf8.SocketUtf8()
        super().__init__(*args, **kwargs)


    def run(self):
        print("writer connecting...")
        try:
            self.sock.connect(self.conn)
            self.sock.setblocking(False)
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
        # struct.error: ushort format requires 0 <= number <= (32767 *2 +1)
        data = 'a' * (2**16 - 1)
        try:
            self.sock.struct_send(data.encode('utf-8'), compression=0)
        except OSError:
            print("Too many open files... raising to parent")
            raise

        # add context manager
        print("Exiting gracefully...")
        self.sock.close()

if __name__ == '__main__':
    import time
    import sys

    HOST = socket.gethostname()
    PORT = 8080
    conn = (HOST, PORT)

    c = 0
    total = 1000
    num_conn = 0
    max_conn = 250
    # also need to measure closed connections
    while c < total and len(threading.enumerate()) > 0:
        #time.sleep(0.01) # 100 qps works fine with no threading and selectors
        #time.sleep(0.005) # 250 qps is fine with no threading and selectors
        # i could timeit... to see real world
        #time.sleep(0.0025) # 500 qps is fine with no threading and selectors
        time.sleep(0.001)
        try:
            print("Attempt # {}".format(c))
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
