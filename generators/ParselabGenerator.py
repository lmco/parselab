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
This module contains all of the necessary data and logic for producing the ParselabGenerator abstract class
'''

import os

from src.ParselabLogger import ParselabLogger
from src.utils import gen_util

class ParselabGenerator:
    '''This is the Abstract class which all parseLab generator modules are to derrive from.

    Adhering to the interface provided here will allow your generator module to leverage all of the capablities found
    within parseLab.'''

    def __init__(self, protocol_dir=None, is_stateful=True, logger=None, debug_mode=False):
        self.log = logger
        if self.log is None:
            self.log = ParselabLogger(print_logs=False)
        self.spec_data = None
        self.debug_mode = debug_mode
        self.backend_name = ''
        self.is_stateful = is_stateful
        self.protocol_dir = None
        self.set_protocol_directory(protocol_dir)

    @classmethod
    def create_instance(cls, *args, **kwargs):
        ''' Creates an instance of this class; factory method '''
        return cls(*args, **kwargs)

    def set_protocol_directory(self, protocol_dir):
        ''' Pass this module a path to the target protocol directory '''
        self.log.info("Setting protocol directory: %s" % (protocol_dir))
        if protocol_dir is None or not os.path.isdir(protocol_dir):
            err_msg = "Target protocol directory (%s) is not a valid directory!" % (protocol_dir)
            raise NotADirectoryError(err_msg)
        self.protocol_dir = os.path.abspath(protocol_dir)

    def set_spec_data(self, spec_data):
        ''' Pass this module the protocol and mission spec data '''
        self.spec_data = spec_data

    def generate_parser(self):
        ''' Generate a parser in the specified module\'s backend.  This
        is expected to output a list of all generated files\' paths'''
        raise NotImplementedError()

    def generate_test(self, testcase_dir, protocol_dir, print_results=True):
        ''' Generate an executable file which leverages the parseLab generator
        with the testcase found in the target testcase dir.  This function is
        expected to return a list of strings holding the path to the generated
        files which represent the test'''
        raise NotImplementedError()

    def run_test_from_testcase(self, testcase_dir, protocol_dir):
        ''' Attempt to execute the test found in the supplied testcase directory.
        This is expected to return an integer representing the number of messaages
        in the test which returned an unexpected value (ex: a valid message was
        blocked by the parser).  A successful test will return a value of 0 '''
        raise NotImplementedError()

    @staticmethod
    def get_setup_directory():
        ''' It is assumed that parseLab modules will have a set of setup files
        that is necessary for generating its parsers.  This function points to
        the directory where this module's boilerplate for the setup files will
        be.  For example: since the Hammer module creates a C parser, it is
        helpful to have a Makefile be generated alongside the parser to compile
        it - there is a standard Makefile saved in the Hammer module's setup
        directory that is copied into the location of the generated parser '''
        raise NotImplementedError()

    @staticmethod
    def get_setup_directory_name():
        ''' Get the name that the setup directory should have once it gets
        copied into the target protocol directory '''
        raise NotImplementedError()

    @staticmethod
    def get_generated_code_header(comment_string):
        ''' Get a string which holds the comment header which should be placed
        above all generated code files '''
        if not os.path.isfile(gen_util.generated_code_header_file):
            raise FileNotFoundError()
        with open(gen_util.generated_code_header_file, 'r') as f:
            code_header_string = ''
            for line in f:
                code_header_string += "%s%s" % (comment_string, line)
            return code_header_string

    @staticmethod
    def append_generated_code_header(comment_string, content, space=1):
        ''' Add a header that denotes that denotes that the file is generated and should not be hand-modified
        without understanding the circumstances'''
        return ParselabGenerator.get_generated_code_header(comment_string) + '\n'*space + content
