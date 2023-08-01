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
A module containing the class definition for a UDP message
'''

import struct

class UDP:
    ''' A class which holds information and functions for using a UDP message '''

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
        ''' Method to serialize the data in this class '''
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
