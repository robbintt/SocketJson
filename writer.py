'''
'''
import socketutf8
import json

if __name__ == '__main__':

    HOST = 'localhost'
    PORT = 8080
    conn = (HOST, PORT)
    # consider a helper
    s = socketutf8.SocketUtf8()

    print("writer connecting...")
    s.connect(conn)

    print("Sending json...")
    # this should take a string and convert it to bytes
    some_utf8_string = json.dumps({"hello world": [1,2,3]})
    s.utf8_send(some_utf8_string)
    print("Sent json, closing...")
    s.close()
    print("Exiting gracefully...")
