import json
import socket

import socketutf8

if __name__ == '__main__':

    HOST = '127.0.0.1'
    HOST = socket.gethostname()
    PORT = 8080
    conn = (HOST, PORT)
    # consider a helper
    s = socketutf8.SocketUtf8()

    print("writer connecting...")
    s.connect(conn)
    s.setblocking(False)

    print("Sending json...")
    # this should take a string and convert it to bytes
    some_utf8_string = json.dumps({"hello world": [1,2,3]})
    s.struct_send(some_utf8_string.encode('utf-8'))
    print("Sent json, closing...")
    s.close()
    print("Exiting gracefully...")
