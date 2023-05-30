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
Generate the source code for a parser in a target backend given a supplied protocol specification
'''

import argparse
import os
import sys
from importlib import import_module

import context
from src.ProtocolDirectoryParser import ProtocolDirectoryParser
from src.ParselabLogger import ParselabLogger
from src.utils import gen_util

def parse_args():
    ''' Consume the arguments from the commandline for use throughout the script '''
    parser = argparse.ArgumentParser(description='Generate a parser given a supplied parseLab module')
    parser.add_argument('--list', action='store_true', help="List all of the currently available generators")
    parser.add_argument('--protocol', type=gen_util.dir_path, help='The directory path to where the protocol data \
exists.  See setup.py for more information about configuring parseLab properly for generation')
    parser.add_argument('--module', type=str, help='The parseLab generator module that will be used to generate the \
parser')
    parser.add_argument('--mute', help='Disable log generation', action='store_false')
    parser.add_argument('--print', help='Print the logs to the terminal', action='store_true')

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    return parser.parse_args()

def main():
    ''' Main execution function '''

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
    log.info("Generating parser for supplied module (%s)" % (args.module))
    parser_files = generator.generate_parser()

    for f in parser_files:
        log.info("Verifying existence of file (%s)" % (f))
        if not os.path.isfile(f):
            err_msg = "generate_parser() returned a None type or path to non-existent file when returning list of \
supposedly generated parser files"
            log.error(err_msg)
            raise Exception(err_msg)

    success_message = "Generated a parser for supplied module (%s)\nGenerated files: %s" % (args.module, parser_files)
    log.info(success_message)
    print(success_message)

if __name__ == '__main__':
    main()
