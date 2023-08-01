##############################################################################
## Copyright 2022 Lockheed Martin Corporation                               ##
##                                                                          ##
## Licensed under the Apache License, Version 2.0 (the "License");          ##
## you may not use this file except in compliance with the License.         ##
## You may obtain a copy of the License at                                  ##
##                                                                          ##
##     http://www.apache.org/licenses/LICENSE-2.0                           ##
##                                                                          ##
## Unless required by applicable law or agreed to in writing, software      ##
## distributed under the License is distributed on an "AS IS" BASIS,        ##
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. ##
## See the License for the specific language governing permissions and      ##
## limitations under the License.                                           ##
##############################################################################


'''
A Module containing the class for the MEP message used in the Machine-Controller simulation
'''

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
        ''' serialize the data in this class '''
        ret = b''
        ret += struct.pack('>B', self.message_id)
        ret += struct.pack('>H', self.sender_id)
        ret += struct.pack('>H', self.target_id)
        return ret

    @classmethod
    def unpack(cls, data):
        ''' Create a class instance from serialized data '''
        unpacked_data = struct.unpack('>BHH', data)
        mid = unpacked_data[0]
        sid = unpacked_data[1]
        tid = unpacked_data[2]
        return MEP(mid, sid, tid)
