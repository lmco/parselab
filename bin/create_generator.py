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
Generates the necessary code to server as a boilerplate for a new parseLab generator module.
'''

import argparse
import os

import context
from src.ParselabLogger import ParselabLogger
from src.utils import gen_util

def handle_arguments():
    ''' Consume the arguments from the commandline for use throughout the script '''

    parser = argparse.ArgumentParser(description="Create a new ParselabGenerator class and associated directory")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--name', action='store', type=valid_generator_name, \
        help="The name of the ParselabGenerator being created (case-insensitive, case will be overwritten). " + \
             "A new directory will be created under %s. " % (os.path.join(gen_util.GENERATORS_DIR, '<name>')) + \
             "A new generator module will be created with the name <Name>Generator.py and will be put in the \
referenced directory. ")
    group.add_argument('--list', action='store_true', \
        help="List all of the currently available generators")
    parser.add_argument('--mute', action='store_false', \
        help="Disable log generation")
    parser.add_argument('--print', action='store_true', \
        help="Print the logs to the terminal")

    return parser.parse_args()

def valid_generator_name(name):
    '''Determine if the provided name is a valid generator name'''
    # is alphanumeric? (can contain underscores)
    if not gen_util.adv_isalnum(name, allowed_characters='_'):
        raise Exception("--name argument can only take alphanumeric characters or underscores")

    if name[0].isdigit():
        raise Exception("--name argument cannot have a number as the first character")

    if name[0] == '_':
        raise Exception("--name argument cannot have an underscore as the first character")

    return name

def arg_name_to_module_name(arg_name):
    ''' Convert the string provided by the commandline arguments into the proper format for a module '''
    return arg_name[0].upper() + arg_name[1:].lower() + 'Generator'

def main():
    ''' Main execution function '''

    args = handle_arguments()

    # Detect available generators
    names = gen_util.list_available_generators()

    # Check if requesting list of modules
    if args.list:
        gen_util.print_available_generators(names)
        return

    log = ParselabLogger(print_logs=args.print, create_log=args.mute)

    module_name = arg_name_to_module_name(args.name)
    log.info("Creating a new ParselabGenerator module class (%s) and directory structure" % (module_name))

    # Format the generator stub with the new generator's information
    generator_stub_filepath = os.path.join(gen_util.STUBS_DIR, 'StubGenerator.py.stub')
    generator_stub = ''
    with open(generator_stub_filepath, 'r') as f:
        try:
            generator_stub = f.read()
        except Exception as e:
            err_msg = "Unable to read generator stub file, if you cannot fix this, please re-clone the repo. \
Error:\n%s" % str(e)
            log.error(err_msg)
            raise Exception(err_msg)

    generator_module_text = generator_stub.format(generator_name=module_name, backend_name="\"%s\"" % (args.name))

    # create the directory structure for the new generator
    new_generator_dir = os.path.join(gen_util.GENERATORS_DIR, args.name)
    log.info("Creating a new generator directory (%s)" % (new_generator_dir))

    if os.path.isdir(new_generator_dir):
        err_msg = "Cannot create a new directory where one already exists. Please delete existing directory (%s)" \
                            % (new_generator_dir)
        log.error(err_msg)
        raise Exception(err_msg)

    try:
        os.makedirs(new_generator_dir)
    except Exception as e:
        err_msg = "Unable to create new directory for generator (%s)\n%s" % (new_generator_dir, str(e))
        log.error(err_msg)
        raise Exception(err_msg)

    # create the __init__ file in the new directory
    init_filepath = os.path.join(new_generator_dir, '__init__.py')
    log.info("Creating __init__.py file (%s)" % (init_filepath))
    try:
        os.close(os.open(init_filepath, os.O_CREAT))
    except Exception as e:
        err_msg = "Unable to create file %s\n%s" % (init_filepath, str(e))
        log.error(err_msg)
        raise Exception(err_msg)

    # write the new module into the new directory
    new_generator_filepath = os.path.join(new_generator_dir, module_name + '.py')
    log.info("Creating new generator module file (%s)" % (new_generator_filepath))
    if os.path.isfile(new_generator_filepath):
        err_msg = "module (%s) already exists! please delete existing generator directory if you would like to \
generate a new one" % (new_generator_filepath)
        log.error(err_msg)
        raise Exception(err_msg)

    with open(new_generator_filepath, 'w+') as f:
        f.write(generator_module_text)

    # create the setup_data directory
    new_setup_dirpath = os.path.join(new_generator_dir, 'setup_data')
    log.info("Creating setup data directory (%s)" % (new_setup_dirpath))
    try:
        os.makedirs(new_setup_dirpath)
    except Exception as e:
        err_msg = "Unable to create setup directory for generator (%s)\n%s" % (new_setup_dirpath, str(e))
        log.error(err_msg)
        raise Exception(err_msg)

if __name__ == '__main__':
    main()
