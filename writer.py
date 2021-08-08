'''
'''
import socketjson
import socket
import json

if __name__ == '__main__':

    HOST = 'localhost'
    PORT = 8080
    conn = (HOST, PORT)
    # consider a helper
    sj = socketjson.SocketJson(socket.AF_INET, socket.SOCK_STREAM)

    print("writer connecting...")
    sj.connect(conn)

    print("Sending json...")
    # this should take a string and convert it to bytes
    some_utf8_string = json.dumps({"hello world": [1,2,3]})
    sj.utf8_send(some_utf8_string)
    print("Sent json, closing...")
    sj.close()
    print("Exiting gracefully...")
