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
TODO: Modify DocString
'''

from ParselabGenerator import ParselabGenerator

# TODO: Replace `Base` with your desired generator name
class BaseGenerator(ParselabGenerator):
    ''' TODO: Add class DocString'''

    backend_name = 'Base'

    def __init__(self, *args, **kwargs):
       super().__init__(*args, **kwargs)
        # TODO: Replace 'Base' with your desired generator name

    def generate_parser(self):
        ''' Generate and return the source code files to build a parser in the target DDL '''
        # TODO: Place necessary logic to generate a parser in your target Data Description Language
        # TODO: Make sure to return a list of the files which you want to verify the creation of during testing
        raise NotImplementedError()

    def generate_test(self, testcase_dir, protocol_dir, print_results=False):
        ''' Generate and return the source code files to run a test when provided a testcase directory '''
        # TODO: Place necessary logic to generate a test in your target Data Description Language
        # TODO: Make sure to return a list of the files which you want to verify the creation of during testing
        raise NotImplementedError()

    def run_test_from_testcase(self, testcase_dir, protocol_dir):
        ''' Execute the test in the supplied testcase directory using the logic in your target DDL '''
        # TODO: Place necessary logic to execute the test which was generated with generate_test()
        # TODO: Execute the test
        raise NotImplementedError()

    @staticmethod
    def get_setup_directory():
        ''' Get a path to the directory that contains any necessary file structure to execute a file in your
        target DDL '''
        # TODO: Every generator module is expected to, but not required to, have a directory containing a set of
        #  important files which will be useful when generating parser or test files.  This is referred to as the
        #  setup directory and is assumed to sit somewhere in parserlab/parselab_generators/<your_generator>/<setup_dir>
        #  meaning that this funciton would return that path
        raise NotImplementedError()

    @staticmethod
    def get_setup_directory_name():
        ''' When building a new protocol directory, the setup files will be placed in a new directory with this name.
        Ex: Hammer has a setup directory with multiple files that aid the generation of the hammer source code.  These
        files get placed into a directory as follows: <protocol_dir>/hammer/
              "hammer" is what this function returns for the HammerGenerator module'''
        # TODO: Return a string representing what you would like to name the directory placed inside the protocol
        #  directory which contains all of the generated files for this generator module
        return BaseGenerator.backend_name
