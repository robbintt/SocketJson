''' Simple socket object

Problem: s.accept() does not return a socket of the class of parent socket...
S.O answer: https://stackoverflow.com/questions/45207430/extending-socket-socket-with-a-new-attribute
This answer is garbage but seems like it will work. This is a huge weakness in this crappy socket library.

Based on 'python-protobuf-simple-socket-rpc'.
Code: https://github.com/exante/python-protobuf-simple-socket-rpc/blob/master/src/protobuf_simple_socket_rpc/socket_rpc.py

Also used struct packing pattern from: https://stackoverflow.com/questions/2038083/how-to-use-python-and-googles-protocol-buffers-to-deserialize-data-sent-over-tc
'''
import socket
import struct

class SocketUtf8(socket.socket):
    ''' better socket implementation
    '''
    def __init__(self, *args: int, **kwargs: int) -> None:
        '''
        '''
        # similar invocation to super in this context
        if not args:
            args = (socket.AF_INET, socket.SOCK_STREAM)
        super().__init__(*args, **kwargs)
        # alternative to super implementation
        #self = socket.socket.__init__(self, *args, **kwargs)

    # TODO: also add type and compression type (gzip or none) headers
    # TODO: for this class this can just wrap the parent method
    # TODO: why not have a more generic extension with types rather than cut-to-fit for utf8?
    def utf8_recv(self) -> str:
        '''
        '''
        #type = self.read(1)
        size = struct.unpack("H", self.recv(2))[0]
        print("Size: {}".format(size))
        data = self.recv(size)
        return data.decode('utf8')

    def utf8_send(self, data: str) -> None:
        '''
        '''
        data = data.encode('utf-8')
        self.sendall(struct.pack("H", len(data)))
        self.sendall(data)
        return

    def utf8_multipart_send(self, data: str) -> None:
        ''' Not tested
        '''
        maxlen = 65535 # size of "H" type: short
        # multipart send
        p = 0
        while p < len(data):
            _size_boundary = min(len(data), p+maxlen)
            _part = data[p, _size_boundary]
            _part = _part.encode('utf-8')
            self.sendall(struct.pack("H", len(_part)))
            self.sendall(_part)
            p += _size_boundary
        return

    @classmethod
    def _socket_copy_with_inheritance(cls, sock):
        _fd = socket.dup(sock.fileno())
        _copy = cls(sock.family, sock.type, sock.proto, fileno=_fd)
        _copy.settimeout(sock.gettimeout())
        return _copy

    def accept(self, *args, **kwargs):
        ''' Copy the python3 lib socket fd over to one descended from this class

        From: https://stackoverflow.com/a/45209878
        '''
        _conn, addr = super().accept(*args, **kwargs)
        return self._socket_copy_with_inheritance(_conn), addr
