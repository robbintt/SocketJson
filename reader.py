import socket
import threading

import socketutf8

def manage_clientsocket(clientsocket, addr):
    print("Connection accepted from: {}".format(addr))
    with clientsocket:
        print(clientsocket.struct_recv().decode('utf-8'))


if __name__ == '__main__':
    #HOST = 'localhost'
    HOST = socket.gethostname() # for server
    PORT = 8080
    conn = (HOST, PORT)
    # consider a helper or default
    #sj = socketjson.SocketJson(socket.AF_INET, socket.SOCK_STREAM)
    s = socketutf8.SocketUtf8()

    print("reader binding...")
    s.bind(conn)
    print("reader listening...")
    s.listen(5) # "listen to 5 hosts should be plenty", sockets are disposable
    while True:
        clientsocket, addr = s.accept()
        t = threading.Thread(target=manage_clientsocket, args=(clientsocket, addr))
        t.start()

    # use a contextmanager instead
    s.close()
