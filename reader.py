import selectors
import socket
import threading

import socketutf8

class Server(threading.Thread):
    ''' Use nonblocking sockets and selector for io multiplexing

    See example: https://docs.python.org/3.4/library/selectors.html#examples

    Explanation of select with threading: https://stackoverflow.com/a/43354727
    '''
    sel = selectors.DefaultSelector()
    def __init__(self, clientsocket, addr, *args, **kwargs):
        self.sock = clientsocket
        self.addr = addr
        self.server_running = True
        self.TIMEOUT = 3  # avoid stale connections
        super().__init__(*args, **kwargs)

    def run(self):
        Server.sel.register(self.sock, selectors.EVENT_READ, self.handle_connection)
        while self.server_running:
            try:
                events = Server.sel.select(timeout=self.TIMEOUT)
                for key, mask in events:
                    callback = key.data
                    #callback(key.fileobj, mask)
                    callback()
            except Exception:
                self.stop()

        print("Closing socket")
        self.sock.close()
        Server.sel.unregister(self.sock)
        print("Socket closed")
        del(self)

    def handle_connection(self):
        print("accept {} from: {}".format(self.sock, self.addr))
        #print(self.sock.struct_recv().decode('utf-8'))
        res = self.sock.struct_recv().decode('utf-8')
        message = "Result received, length {}".format(len(res)) + "\n"
        print(message)
        resfile = "results.txt"
        with open(resfile, 'a') as f:
            f.write(message)
        self.stop()

    def stop(self):
        self.server_running = False


if __name__ == '__main__':
    #HOST = 'localhost'
    HOST = socket.gethostname() # for server
    PORT = 8080
    conn = (HOST, PORT)
    # consider a helper or default
    #sj = socketjson.SocketJson(socket.AF_INET, socket.SOCK_STREAM)
    s = socketutf8.SocketUtf8()
    s.bind(conn)
    print("Listening...")
    s.listen(5) # "listen to 5 hosts should be plenty", sockets are disposable

    # potentially use Semaphore to handle threads = hosts... depends on socket impl
    # TODO: Seems like I need a sempahore for available system files...
    # I don't love semaphore for that, feels like I should just timeout...
    while True:
        try:
            clientsocket, addr = s.accept()
            # This is used in conjunction with selector to handle
            clientsocket.setblocking(False)
            server = Server(clientsocket, addr)
            # this thread needs to receive shutdown Event (not daemon so it cleans up)
            server.start()
        except Exception:
            import sys
            print(sys.exc_info())
            continue

    # use a contextmanager instead
    s.close()
