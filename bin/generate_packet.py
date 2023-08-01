#!/usr/bin/env python3
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
Generate a single packet instance for a specific message
'''

import argparse

import context
from src.ParselabLogger import ParselabLogger
from src.PacketGenerator import PacketGenerator
from src.utils import gen_util

def handle_arguments():
    ''' Consume the arguments from the commandline for use throughout the script '''

    parser = argparse.ArgumentParser(description="Generate a packet using a parseLab structured protocol directory. \
Note: This script is not really meant to be used, but rather to just test the PacketGenerator class.  The \
PacketGenerator class is expected to be imported into another script and leveraged through it")
    parser.add_argument('--protocol', action='store', type=gen_util.dir_path, \
            help="The name of the generated protocol directory (relative path is fine)", required=True)
    parser.add_argument('--msg', action='store', type=str, \
            help='The name of the message type for the packet you would like to generate', required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--valid', action='store_true', \
            help='Use this to denote that the generated packet should be valid according to the protocol spec')
    group.add_argument('--invalid', action='store_true', \
            help='Use this to denote that the packet should be invalid according to the protocol spec')
    parser.add_argument('--mute', help='Disable log generation', action='store_false')
    parser.add_argument('--print', help='Print the logs to the terminal', action='store_true')

    args = parser.parse_args()

    return args

def main():
    ''' Main execution function '''

    args = handle_arguments()
    log = ParselabLogger(print_logs=args.print, create_log=args.mute)

    packet_generator = PacketGenerator(args.protocol, log)
    serialized_bytes, serialized_size, is_valid, _ = packet_generator.generate_packet_from_name(args.msg, args.valid)

    hexdump = PacketGenerator.hexdump_bytes(serialized_bytes, serialized_size)
    print("[%sVALID] - %s" % ("IN" if not is_valid else "", hexdump))

if __name__ == '__main__':
    main()
