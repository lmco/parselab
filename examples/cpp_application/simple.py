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


#!/usr/bin/env python3

'''
A simple example of using a Hammer parser in a python script.
'''

import ctypes

from UDP import UDP

def main():
    ''' Main Execution Function'''

    # Import parse() function from libparser.so
    libparser = ctypes.CDLL("libparser.so")

    # Generate a UDP message
    udp_msg = UDP(25515, 32316, "This is a data payload")

    # Parse the UDP Message
    ret = libparser.parse(udp_msg.serialized, len(udp_msg.serialized))
    if not ret:
        print("pass")
    else:
        print("fail")

if __name__ == '__main__':
    main()
