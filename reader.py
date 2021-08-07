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

    print("reader binding...")
    sj.bind(conn)
    print("reader listening...")
    sj.listen()
    conn, addr = sj.accept()
    with conn:
        print(conn.json_recv())

    sj.close()
