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
Perform the processes of:
    1. generate_parser.py
    2. generate_testcase.py
    3. generate_test.py
    4. run_test.py
In a single commandline execution
'''

import argparse
import os
import sys
from importlib import import_module

import context
from src.ParselabLogger import ParselabLogger
from src.ProtocolDirectoryParser import ProtocolDirectoryParser
from src.TestcaseGenerator import TestcaseGenerator
from src.utils import gen_util

def parse_args():
    ''' Consume the arguments from the commmandline for use throughout the script '''
    parser = argparse.ArgumentParser(description='Execute a quick test for a new testcase and generated parser')
    parser.add_argument('--list', action='store_true', help="List all of the currently available generators")
    parser.add_argument('--protocol', type=gen_util.dir_path, help='The directory path to where the protocol data \
exists.  See setup.py for more information about configuring parseLab properly for generation')
    parser.add_argument('--module', type=str, help='The parseLab generator module that will be used to generate the \
parser')
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

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    return parser.parse_args()

def generate_parser(log, generator, module_name):
    ''' Generate the parser '''
    # Generate the parser
    log.info("Generating parser for supplied module (%s)" % (module_name))
    parser_files = generator.generate_parser()

    for f in parser_files:
        log.info("Verifying existence of file (%s)" % (f))
        if not os.path.isfile(f):
            err_msg = "generate_parser() returned a None type or path to non-existent file when returning list of \
supposedly generated parser files"
            log.error(err_msg)
            raise FileNotFoundError(err_msg)

    success_message = "Generated a parser for supplied module (%s)\nGenerated files: %s" % (module_name, parser_files)
    log.info(success_message)
    print(success_message)

def generate_testcase(log, protocol_path, msg_count, one_per_flag, testcase_name, valid_flag):
    ''' Generate the testcase and return the path to it'''
    log.info("Creating a TestcaseGenerator instance for protocol directory: %s" % (protocol_path))
    testcase_generator = TestcaseGenerator(protocol_path, logger=log)
    valid_str = 'valid' if valid_flag else 'invalid'
    msg_count_str = "%s message types" % str(msg_count) if not one_per_flag else "one packet per message type"
    log.info("Generating a %s testcase with %s, name=%s" % (valid_str, msg_count_str, testcase_name))
    testcase_dir = testcase_generator.generate_testcase(valid_flag, msg_count, testcase_name, one_per_flag)

    print("Successfully generated testcase (%s)" % testcase_dir)

    return testcase_dir

def generate_test(log, directory_parser, testcase_path, generator, protocol_dirpath):
    ''' Generate the test files for this testcase '''
    # Verify that the target testcase exists / is valid
    log.info("Validating target testcase directory")
    if not directory_parser.verify_testcase(testcase_path):
        err_msg = "The target testcase does not exist in the protocol directory (%s) or it is not configured \
properly.  Use the generate_testcase.py script to create a testcase to run aginst" % (protocol_dirpath)
        log.error(err_msg)
        raise FileNotFoundError(err_msg)

    # Generate an executable test with the requested testcase
    log.info("Generating an executable test with respect to testcase=%s" % (testcase_path))
    test_files = generator.generate_test(testcase_path, protocol_dirpath)

    for f in test_files:
        log.info("Verifying file existence (%s)" % (f))
        if not os.path.isfile(f):
            err_msg = "generate_test() returned a None type or an invalid path to one of the supposedly generated \
test files!"
            log.error(err_msg)
            raise FileNotFoundError(err_msg)

    success_msg = "Generated test files: %s" % (str(test_files))
    log.info(success_msg)
    print(success_msg)

def run_test(log, generator, protocol_dirpath, testcase_dirpath):
    ''' Build and run the test at the requested testcase '''
    # Run the executable test for the requested testcase
    log.info("Running exectuable test for requested testcase (%s)" % (testcase_dirpath))
    generator.run_test_from_testcase(testcase_dirpath, protocol_dirpath)


def main():
    ''' Main Execution Function '''
    # Parse command line arguments
    args = parse_args()

    # Detect available generators
    names = gen_util.list_available_generators()

    # Check if requesting list of modules
    if args.list:
        gen_util.print_available_generators(names)
        return

    # Create the logger
    log = ParselabLogger(print_logs=args.print, create_log=args.mute)

    # pre-process args
    if args.protocol is None:
        err_msg = "--protocol is a required argument. Please use this to pass in the path to the target protocol \
directory"
        log.error(err_msg)
        raise Exception(err_msg)

    if args.module is None:
        err_msg = "--module is a required argument. Please use this to pass in the target ParselabGenerator module. \
Use --list for a list of all available generator modules"
        log.error(err_msg)
        raise Exception(err_msg)

    # Get the protocol directory path
    protocol_dirpath = os.path.abspath(args.protocol)
    while protocol_dirpath[-1] == '/':
        protocol_dirpath = protocol_dirpath[:-1]
    directory_parser = ProtocolDirectoryParser(protocol_dirpath, logger=log)

    if not directory_parser.check_valid():
        err_msg = "The supplied protocol directory (%s) is not valid" % (protocol_dirpath)
        log.error(err_msg)
        raise Exception(err_msg)

    # Get the protocol/mission specification data
    log.info("Getting protocol (and mission) specification data")
    spec_data = directory_parser.get_spec_data()

    # Load a ParselabGenerator subclass module
    log.info("Importing parseLab Generator module")

    # Before importing the module, interpret args.module from the shorter input version
    args.module = gen_util.lookup_generator_name(args.module, names)
    if args.module is None:
        err_msg = "Module not found"
        log.error(err_msg)
        print(err_msg)
        raise Exception(err_msg)

    # Import the module
    module = import_module(args.module)

    # From the module, get the parselab generator class object from the module
    generator_class = getattr(module, args.module.split('.')[-1])

    # Create an instance of the parselab generator class
    log.info("Creating instance of the ParselabGenerator class")
    generator = generator_class.create_instance(protocol_dir=args.protocol, logger=log,
                                                is_stateful=directory_parser.is_stateful(),
                                                debug_mode=gen_util.debug_mode)

    # Supply the parselab generator with the spec data
    generator.set_spec_data(spec_data)

    # Generate the parser
    generate_parser(log, generator, args.module)

    # Generate the testcase
    testcase_dir = generate_testcase(log, args.protocol, args.msg_count, args.one_per, args.name, args.valid)

    # Generate the test files
    generate_test(log, directory_parser, testcase_dir, generator, protocol_dirpath)

    # Run the test files
    run_test(log, generator, protocol_dirpath, testcase_dir)

if __name__ == '__main__':
    main()
