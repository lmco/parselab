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
Generate a 'testcase' for a specified protocol specification.  This essentially runs the fuzzer and generates the data
for an invalid, or valid, series of messages
'''

import argparse

import context
from src.ParselabLogger import ParselabLogger
from src.TestcaseGenerator import TestcaseGenerator
from src.utils import gen_util

def handle_arguments():
    ''' Consume the arguments from the commandline for use throughout the script '''

    parser = argparse.ArgumentParser(description="Generate a testcase using the parseLab structured protocol \
directory.")
    parser.add_argument('--protocol', action='store', type=gen_util.dir_path, \
            help="The path to the generated protocol directory (relative path is fine)", required=True)
    parser.add_argument('--name', action='store', type=str, \
            help="The name of this test", required=True)
    count_group = parser.add_mutually_exclusive_group(required=True)
    count_group.add_argument('--msg_count', action='store', type=int, default=0, \
            help="The number of messages that should be present in this testcase")
    count_group.add_argument('--one_per', action='store_true', \
            help="Should the test consist of one test-message per message definition in the protocol spec, rather \
than the number specified by msg_count")
    valid_group = parser.add_mutually_exclusive_group(required=True)
    valid_group.add_argument('--valid', action='store_true', \
            help='Use this to denote that the generated packet should be valid according to the protocol spec')
    valid_group.add_argument('--invalid', action='store_true', \
            help='Use this to denote that the packet should be invalid according to the protocol spec')
    parser.add_argument('--mute', help='Disable log generation', action='store_false')
    parser.add_argument('--print', help='Print the logs to the terminal', action='store_true')

    return parser.parse_args()

def main():
    ''' Main execution function '''

    args = handle_arguments()

    log = ParselabLogger(print_logs=args.print, create_log=args.mute)

    log.info("Creating a TestcaseGenerator instance for protocol directory: %s" % (args.protocol))
    testcase_generator = TestcaseGenerator(args.protocol, logger=log)
    valid_str = 'valid' if args.valid else 'invalid'
    msg_count_str = "%s message types" % str(args.msg_count) if not args.one_per else "one packet per message type"
    log.info("Generating a %s testcase with %s, name=%s" % (valid_str, msg_count_str, args.name))
    testcase_dir = testcase_generator.generate_testcase(args.valid, args.msg_count, args.name, args.one_per)

    print("Successfully generated testcase (%s)" % testcase_dir)

if __name__ == '__main__':
    main()
