''' Simple socket object

Future:
    - support types: utf8, binary
    - support gzip/gunzip with a flag in the struct
'''
import socket
import struct
import zlib

class SocketUtf8(socket.socket):
    ''' better socket implementation
    '''
    def __init__(self, *args: int, **kwargs: int) -> None:
        '''
        '''
        # default to INET STREAM
        # I think this is only a a STREAM class but not sure yet
        if not args:
            args = (socket.AF_INET, socket.SOCK_STREAM)
        super().__init__(*args, **kwargs)

    # TODO: also add type to struct (binary, utf8, bytes, json?)
    def struct_recv(self) -> str:
        compression, size = struct.unpack("=cH", self.recv(3))
        data = self.recv(size)
        if compression == b'1':
            data = zlib.decompress(data)
        return data

    def struct_send(self, data: str, compression: bytes = b'1') -> None:
        '''
        '''
        if compression == b'1':
            data = zlib.compress(data)
        self.sendall(struct.pack("=cH", compression, len(data)))
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
