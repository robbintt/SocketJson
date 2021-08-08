'''
'''
import socketutf8

if __name__ == '__main__':
    HOST = 'localhost'
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
    with conn:
        print(conn.utf8_recv())

    s.close()
