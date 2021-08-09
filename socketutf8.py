''' Simple socket object

Future:
    - support types: utf8, binary
    - support gzip/gunzip with a flag in the struct
'''
import os
import socket
import struct
import sys
import time
import zlib

class SocketUtf8(socket.socket):
    ''' better socket implementation
    '''
    def __init__(self, *args: int, **kwargs: int) -> None:
        '''
        '''
        self._original_conn = None
        self.fd = None
        # default to INET STREAM
        # I think this is only a a STREAM class but not sure yet
        if not args:
            args = (socket.AF_INET, socket.SOCK_STREAM)
        super().__init__(*args, **kwargs)

    # TODO: also add type to struct (utf8, bytes, json, ?)
    def struct_recv(self) -> str:

        # recv needs to be in a loop until returns 0, data could be partial
        # TODO: Clean up data structures, dry out
        desc_size = 3
        desc = bytes()
        _desc = bytes()
        remaining_bytes = desc_size - len(desc)
        while not _desc and remaining_bytes:
            try:
                _desc = self.recv(remaining_bytes)
            except BlockingIOError:
                time.sleep(0.001)
        desc += _desc
        remaining_bytes = desc_size - len(desc)
        while remaining_bytes > 0:
            try:
                _desc = self.recv(remaining_bytes)
            except BlockingIOError:
                time.sleep(0.001)
                continue # reset loop
            desc += _desc
            remaining_bytes = desc_size - len(desc)
        compression, size = struct.unpack("=BH", desc)
        #print("Received size: {}".format(size))

        # recv needs to be in a loop until returns 0, data could be partial
        # TODO: Clean up data structures, dry out
        data = bytes()
        _data = bytes()
        remaining_bytes = size - len(data)
        while not _data and remaining_bytes:
            try:
                _data = self.recv(remaining_bytes)
            except BlockingIOError:
                time.sleep(0.001)
        data += _data
        remaining_bytes = size - len(data)
        while remaining_bytes > 0:
            try:
                _data = self.recv(remaining_bytes)
            except BlockingIOError:
                time.sleep(0.001)
                continue # reset loop
            data += _data
            remaining_bytes = size - len(data)

        if compression == 1:
            data = zlib.decompress(data)
        return data

    def struct_send(self, data: bytes, compression: int = 1) -> None:
        '''
        '''
        if compression == 1:
            data = zlib.compress(data)
        while True:
            try:
                self.sendall(struct.pack("=BH", compression, len(data)))
                break
            except BrokenPipeError:
                print(sys.exc_info())
                return -1
            except (BlockingIOError, Exception):
                print(sys.exc_info())
                time.sleep(0.001)
                continue # reset loop
                # need a timeout and let it be handled on client side
                # TODO: do the following if timeout
                #print(sys.exc_info())
                #return -1
        while True:
            try:
                self.sendall(data)
                break
            except BrokenPipeError:
                print(sys.exc_info())
                return -1
            except (BlockingIOError, Exception):
                print(sys.exc_info())
                time.sleep(0.001)
                continue # reset loop
                # need a timeout and let it be handled on client side
                # TODO: do the following if timeout
                #print(sys.exc_info())
                #return -1
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

    def _socket_copy_with_inheritance(self, sock):
        self.fd = socket.dup(sock.fileno())
        #print("fd: {}".format(self.fd))
        _copy = SocketUtf8(sock.family, sock.type, sock.proto, fileno=self.fd)
        _copy.settimeout(sock.gettimeout())
        sock.close()
        return _copy

    def accept(self, *args, **kwargs):
        ''' Copy the python3 lib socket fd over to one descended from this class

        From: https://stackoverflow.com/a/45209878
        '''
        self._original_conn, addr = super().accept(*args, **kwargs)
        return self._socket_copy_with_inheritance(self._original_conn), addr
        # don't fix my problem with fd cleanup
        self._original_conn.close()
        del(self._original_conn)

    def close(self, *args, **kwargs):
        #print("closing fd: {}".format(self.fd))
        #os.close(self.fd)
        #self._original_conn.close()
        super().close(*args, **kwargs)
