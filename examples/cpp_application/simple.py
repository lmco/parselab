#!/usr/bin/env python3

import ctypes
import struct

from UDP import UDP

def main():
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
