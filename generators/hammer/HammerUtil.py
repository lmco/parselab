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
This module holds helper information for the HammerGenerator class to leverage
'''

import os

# filenames and information
actions_dirname = 'actions'
directives_dirname = 'directives'
includes_filename = 'includes.txt'
macros_filename = 'macros.txt'
functions_dirname = 'functions'
info_dirname = 'info'
objects_dirname = 'objects'
struct_ext = '.struct'
enum_ext = '.enum'
action_ext = '.act'
function_ext = '.fun'
global_variables_dirname = 'global_variables'
global_variables_filename = 'global_variables.txt'
makefile_filename = "Makefile"
tests_dirname = 'tests'
include_dirname = 'include'
src_dirname = 'src'
generated_parser_filename = 'parser.c'
generated_header_filename = 'parser.h'
generated_output_dirpath = os.path.join('hammer', 'out')
generated_test_src_dirname = 'src'
generated_test_inc_dirname = 'inc'
test_filename = 'test.c'
data_c_filename = 'data.c'
data_h_filename = 'data.h'

exec_test_dirpath = 'bin/test.bin'
makefile_filename = 'Makefile'

# Generator information
native_hammer_sizes = [8, 16, 32, 64]

#backend info
valid_backends = ['PACKRAT', 'LALR']

# rule definitions
#ARULE = 1
#VRULE = 2
#AVRULE = 3
A_MASK = 0b01
V_MASK = 0b10
RULE = 0
ARULE = RULE | A_MASK
VRULE = RULE | V_MASK
AVRULE = RULE | A_MASK | V_MASK

# action/validator type
NONE = 0
ACTION = 1
VALIDATOR = 2
STATE_VALIDATOR = 3
ACTION_VALIDATOR = 4
prefix_dict = {NONE: '', ACTION : 'A', ACTION_VALIDATOR : 'AV', VALIDATOR : 'V', STATE_VALIDATOR : 'V'}

# Protocol dir setup information
file_path = os.path.dirname(os.path.realpath(__file__))
setup_dirpath = os.path.join(file_path, 'setup_data')
setup_dirname = 'hammer'

# Test Generation information
def generate_test_paths(protocol_dir, testcase_dir):
    ''' Generate all of the necessary path information for a generated test '''
    if testcase_dir[-1] != '/':
        testcase_dir += '/'
    out_filepath = os.path.join(protocol_dir, generated_output_dirpath)
    tests_dirpath = os.path.join(out_filepath, tests_dirname)
    testcase_name = os.path.basename(os.path.dirname(testcase_dir))
    out_testcase_dirpath = os.path.join(tests_dirpath, testcase_name)
    src_testcase_dirpath = os.path.join(out_testcase_dirpath, generated_test_src_dirname)
    inc_testcase_dirpath = os.path.join(out_testcase_dirpath, generated_test_inc_dirname)
    test_filepath = os.path.join(src_testcase_dirpath, test_filename)
    data_c_filepath = os.path.join(src_testcase_dirpath, data_c_filename)
    data_h_filepath = os.path.join(inc_testcase_dirpath, data_h_filename)
    test_exe_filepath = os.path.join(out_testcase_dirpath, exec_test_dirpath)

    return out_filepath, tests_dirpath, testcase_name, out_testcase_dirpath, src_testcase_dirpath, \
           inc_testcase_dirpath, test_filepath, data_c_filepath, data_h_filepath, test_exe_filepath
