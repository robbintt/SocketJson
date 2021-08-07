''' Simple json socket object

Problem: s.accept() does not return a socket of the class of parent socket...
S.O answer: https://stackoverflow.com/questions/45207430/extending-socket-socket-with-a-new-attribute
This answer is garbage but seems like it will work. This is a huge weakness in this crappy socket library.

Based on 'python-protobuf-simple-socket-rpc'.
Code: https://github.com/exante/python-protobuf-simple-socket-rpc/blob/master/src/protobuf_simple_socket_rpc/socket_rpc.py

Also used struct packing pattern from: https://stackoverflow.com/questions/2038083/how-to-use-python-and-googles-protocol-buffers-to-deserialize-data-sent-over-tc
'''
import json
import socket
import struct

class SocketJson(socket.socket):
    ''' socket json implementation
    '''
    def __init__(self, *args: int, **kwargs: int) -> None:
        '''
        '''
        # similar invocation to super in this context
        self = socket.socket.__init__(self, *args, **kwargs)
        # alternative super implementation
        # super().__init__(*args, **kwargs)

    # todo: also add type and compression type (gzip or none) headers
    def json_recv(self) -> bytes:
        '''
        '''
        #type = self.read(1)
        size = struct.unpack("H", self.recv(2))[0]
        data = self.recv(size)
        return data # TODO: handle jsonify from bytes in return

    # TODO: When does the data go from json to bytes?
    def json_send(self, data: bytes) -> None:
        '''
        '''
        self.sendall(struct.pack("H", len(data)))
        self.sendall(data)
        return

    @classmethod
    def _socket_copy_with_inheritance(cls, sock):
        _fd = socket.dup(sock.fileno())
        _copy = cls(sock.family, sock.type, sock.proto, fileno=_fd)
        _copy.settimeout(sock.gettimeout())
        return _copy

    def accept(self, *args, **kwargs):
        ''' Replace the python default socket instance with a SocketJson instance

        From: https://stackoverflow.com/a/45209878
        '''
        _conn, addr = super().accept(*args, **kwargs)
        return self._socket_copy_with_inheritance(_conn), addr
