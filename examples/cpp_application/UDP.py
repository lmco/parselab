import struct

class UDP:
    def __init__(self, src_port, dst_port, data):
        self.src_port = src_port
        self.dst_port = dst_port
        self.length = len(data)
        self.checksum = 0
        for i in data:
            self.checksum += ord(i)
        self.data = data
    
    @property
    def serialized(self):
        # Since the generated parser works on serialized data,
        #  we need to serailize the UDP message appropriately
        ret = b''
        # We are using '>H' because the protocol specification file for
        #  UDP describes the fields as big endian, which is denoted by
        #  the '>' character
        ret += struct.pack('>H', self.src_port)
        ret += struct.pack('>H', self.dst_port)
        ret += struct.pack('>H', self.length)
        ret += struct.pack('>H', self.checksum)
        for i in self.data:
            ret += struct.pack('>B', ord(i))

        return ret
