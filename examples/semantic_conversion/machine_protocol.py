import struct

class MEP:
    ''' MEP is the "Machine Example Protocol", and this is the class that represents the
    data for a MEP message '''

    def __init__(self, message_id, sender_id, target_id):
        self.message_id = message_id
        self.sender_id = sender_id
        self.target_id = target_id

    @property
    def serialized(self):
        ret = b''
        ret += struct.pack('>B', self.message_id)
        ret += struct.pack('>H', self.sender_id)
        ret += struct.pack('>H', self.target_id)
        return ret

    @classmethod
    def unpack(cls, data):
        unpacked_data = struct.unpack('>BHH', data)
        mid = unpacked_data[0]
        sid = unpacked_data[1]
        tid = unpacked_data[2]
        return MEP(mid, sid, tid)
