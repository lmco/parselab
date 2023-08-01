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
Driver for JsonSpecParser
'''

import argparse
import os

import context

from src.JsonSpecParser import JsonSpecParser
from src.ProtocolDirectoryParser import ProtocolDirectoryParser
from src.ParselabLogger import ParselabLogger

def handle_arguments():
    ''' Consume the arguments from the commandline for use throughout the script '''
    parser = argparse.ArgumentParser(description="Parse Json Specification")
    parser.add_argument('--protocol', action='store', type=str, \
                        help='The name of the protocol directory (relative path is fine)', required=True)
    parser.add_argument('--print', help='Print the logs to the terminal', action='store_true')
    parser.add_argument('--mute', help='Disable the log generation', action='store_false')
    args = parser.parse_args()
    return args

def main():
    ''' Main execution function '''
    args = handle_arguments()

    # Create the logger
    log = ParselabLogger(print_logs=args.print, create_log=args.mute)

    # Get protocol path
    protocol_dirpath = os.path.abspath(args.protocol)
    while protocol_dirpath[-1] == '/':
        protocol_dirpath = protocol_dirpath[:-1]
    directory_parser = ProtocolDirectoryParser(protocol_dirpath, logger=log)
    protocol_spec = directory_parser.get_protocol_spec()

    # Parse Json
    spec_parser = JsonSpecParser(logger=log)
    spec_parser.parse_protocol_spec(protocol_spec)
    print(f"Protocol specification found in {protocol_dirpath}\nParsed successfully")

if __name__ == '__main__':
    main()
