import selectors
import socket
import threading

import socketutf8

class Server(threading.Thread):

    def __init__(self, clientsocket, addr, *args, **kwargs):
        self.sock = clientsocket
        self.addr = addr
        self.server_running = True
        self.sel = selectors.DefaultSelector()
        super().__init__(*args, **kwargs)

    def run(self):
        self.sel.register(self.sock, selectors.EVENT_READ, self.handle_connection)
        while self.server_running:
            events = self.sel.select(timeout=1)
            for key, mask in events:
                callback = key.data
                #callback(key.fileobj, mask)
                callback()

    def handle_connection(self):
        print("accept {} from: {}".format(self.sock, self.addr))
        #print(self.sock.struct_recv().decode('utf-8'))
        res = self.sock.struct_recv().decode('utf-8')
        if res == 0:
            return
        else:
            print(res)
        self.sel.unregister(self.sock)
        self.sock.close()

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
    while True:
        clientsocket, addr = s.accept()
        # This is used in conjunction with selector to handle 
        clientsocket.setblocking(False)
        server = Server(clientsocket, addr)
        # this thread needs to receive shutdown Event (not daemon so it cleans up)
        server.start()

    # use a contextmanager instead
    s.close()
