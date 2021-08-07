'''
'''
import socketjson
import socket

if __name__ == '__main__':

    HOST = 'localhost'
    PORT = 8080
    conn = (HOST, PORT)
    # consider a helper
    sj = socketjson.SocketJson(socket.AF_INET, socket.SOCK_STREAM)

    print("writer connecting...")
    sj.connect(conn)

    print("Sending json...")
    sj.json_send(b'hello world')
    print("Sent json, closing...")
    sj.close()
    print("Exiting gracefully...")
