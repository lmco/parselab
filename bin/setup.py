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
Generate the necessary files for a new protocol directory for use with a target generator module
'''

import argparse
import os
from importlib import import_module

import context
from src.ParselabLogger import ParselabLogger
from src.utils import gen_util

def parse_args():
    ''' Consume the arguments from the commandline for use throughout the script '''

    parser = argparse.ArgumentParser(description='Generate the parseLab structure with respect to a target parseLab \
                                                  generator module')
    parser.add_argument('--list', action='store_true', help="List all of the currently available generators")
    parser.add_argument('--protocol', help='The target path to where this script should generate the necessary files \
                                            to use parseLab - also known as the protocol directory')
    parser.add_argument('--module', help='The parseLab parser generator module that will be used. NOTE: Supply this \
                                          argument with the python module path notation. See README for example')
    parser.add_argument('--mute', help='Disable log generation', action='store_false')
    parser.add_argument('--print', help='Print the logs to the terminal', action='store_true')

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

    # Get the target directory path, also referred to as the protocol directory
    protocol_dirpath = os.path.abspath(args.protocol)

    if args.module:
        # Before importing the module, interpret args.module from the shorter input version
        args.module = gen_util.lookup_generator_name(args.module, names)
        if args.module is None:
            err_msg = "Module not found"
            log.error(err_msg)
            print(err_msg)
            raise Exception(err_msg)

        # Load the ParselabGenerator sublcass module
        module = import_module(args.module)

        module_name = args.module.split('.')[-1]

        # From the module, get the parser generator class object from the module
        generator_class = getattr(module, module_name)

        # From the parseLab module's class, get the path to the desired setup directory
        data_dir = generator_class.get_setup_directory()
        setup_dirname = generator_class.get_setup_directory_name()
    else:
        data_dir = None
        setup_dirname = None

    log.info("Creating directory structure in (%s)" % (protocol_dirpath))
    gen_util.create_setup_dir_structure(data_dir=data_dir, dirpath=protocol_dirpath, setup_dirname=setup_dirname)

    success_msg = "Created directory structure in (%s)" % (protocol_dirpath)
    log.info(success_msg)
    print(success_msg)

if __name__ == '__main__':
    main()
