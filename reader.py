import socket

import socketutf8

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
    s.listen()
    conn, addr = s.accept()
    print("Connection accepted from: {}".format(addr))
    with conn:
        print(conn.struct_recv().decode('utf-8'))

    s.close()
