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
Run the suite of unit tests against a parseLab module.  This is used to validate that the target generator module
is fully capable to handle all of the interfaces supplied by parseLab.
'''

import argparse
import os
import sys
import traceback
from importlib import import_module

import context
from src.ParselabLogger import ParselabLogger
from src.utils import gen_util

def parse_args():
    ''' Consume the arguments from the commandline for use throughout the script '''

    parser = argparse.ArgumentParser(description='Run the list of unit tests against a target generator module')
    parser.add_argument('--list', action='store_true', help="List all of the currently available generators")
    parser.add_argument('--module', type=str, help='The parseLab generator module that will be used to generate the \
parser')
    parser.add_argument('--test', type=str, help='The name of the test that should be targetted during this run', \
        nargs='?', const='', default='')
    parser.add_argument('--clean', help='Run the clean function against all of the unit tests', action='store_true')
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

    if args.module is None:
        err_msg = "--module is a required argument. Please use this to pass in the target ParselabGenerator module. \
Use --list for a list of all available generator modules"
        log.error(err_msg)
        raise SyntaxError(err_msg)

    # Find all of the unit tests in the unit test directory
    unit_tests_dir = os.path.join('..', gen_util.unit_tests_dirname)

    if not os.path.isdir(unit_tests_dir):
        err_msg = "Missing unit test directory (%s). Missing required repo files or not running this script from \
parselab/bin"
        log.error(err_msg)
        raise SyntaxError(err_msg)

    unit_test_dirs = [os.path.join(unit_tests_dir, d) for d in os.listdir(unit_tests_dir) \
                                                      if valid_unit_test_dir(os.path.join(unit_tests_dir, d))]

    unit_test_modules = []
    for test_dir in unit_test_dirs:
        if args.test != '' and args.test != os.path.basename(test_dir):
            continue
        test_script = os.path.basename(test_dir)
        test_script_path = os.path.join(test_dir, test_script + '.py')
        if os.path.isfile(test_script_path):
            log.info("Test Found: %s" %(test_script_path))
        else:
            log.warn("Expected test (%s) but none was found.  Please read the README for information about how to \
create unit test scripts" % (test_script_path))

        test_script_path = test_script_path.split('../')[-1]
        module_path = os.path.splitext(test_script_path)[0]
        module_path = module_path.replace('/', '.')
        unit_test_modules.append(module_path)

    # Before importing the module, interpret args.module from the shorter input version
    args.module = gen_util.lookup_generator_name(args.module, names)
    if args.module is None:
        err_msg = "Module not found"
        log.error(err_msg)
        print(err_msg)
        raise Exception(err_msg)

    tests = {}
    for module_path in unit_test_modules:
        log.info("Creating Unit Test Instance for ParselabTest Module (%s)" % (module_path))
        module = import_module(module_path, package='parselab')
        test_class = getattr(module, module_path.split('.')[-1])
        tests[module_path] = test_class.create_instance(target_module=args.module, logger=log)

        log.info("Successfully created instance of ParselabTest module (%s)" % (module_path))

    results = {}
    for module_path in tests:
        test = tests[module_path]

        log.info("Cleaning Directory for Test Instance (%s)" % (module_path))
        test.clean()
        if args.clean:
            continue

        try:
            log.info("Running Unit Test Instance (%s)" % (module_path))
            results[module_path] = test.run()
        # Disabling broad-except because we want to catch all exceptions so we can log it appropraitely in our
        #   results object
        except Exception:
            results[module_path] = (gen_util.TEST_EXCEPT, str(traceback.format_exc()))

    for module_path in results:
        result, msg = results[module_path]
        print_str = ''
        color = gen_util.colors['Reset']
        if result == gen_util.TEST_PASS:
            color = gen_util.colors['Green']
            print_str = "[Passed] %s" % (module_path)
        elif result == gen_util.TEST_FAIL:
            color = gen_util.colors['Red']
            print_str = "[Failed] %s -- %s" % (module_path, msg)
        else:
            color = gen_util.colors['Yellow']
            print_str = "[EXCEPT] %s -- %s" % (module_path, msg)
        print(color + print_str + gen_util.colors['Reset'])
        log.info(print_str)

def valid_unit_test_dir(test_dir):
    ''' Determine if the supplied test directory is correctly structured'''
    test_script = os.path.basename(test_dir)
    test_script_path = os.path.join(test_dir, test_script + '.py')
    if os.path.isdir(test_dir) and os.path.isfile(test_script_path):
        return True

    return False

if __name__ == '__main__':
    main()
