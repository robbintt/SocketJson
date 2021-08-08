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

    # TODO: also add type to struct (utf8, bytes, json, ?)
    def struct_recv(self) -> str:
        # recv needs to be in a loop until returns 0, data can be partial
        compression, size = struct.unpack("=BH", self.recv(3))
        # recv needs to be in a loop until returns 0, data can be partial
        data = self.recv(size)
        self.close()
        if compression == 1:
            data = zlib.decompress(data)
        return data

    def struct_send(self, data: str, compression: bytes = 1) -> None:
        '''
        '''
        if compression == 1:
            data = zlib.compress(data)
        # do we need a loop for sendall? how do we flush it?
        self.sendall(struct.pack("=BH", compression, len(data)))
        # do we need a loop for sendall? how do we flush it?
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
