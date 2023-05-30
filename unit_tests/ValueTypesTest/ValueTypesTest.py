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


''' ValueTypesTest.py contains all of the necessary classes and functions which pertain to the testing
of the different ValueTypes which  are supported by a parseLab generator module:
    * ValueSingle
    * ValueRange
    * ValueChoice
    * ValueList
'''

import os

from unit_tests.ParselabTest import ParselabTest
from unit_tests import TestUtils
from src.ProtocolDirectoryParser import ProtocolDirectoryParser
from src.utils import gen_util

class ValueTypesTest(ParselabTest):
    ''' ValueTypesTest is a class meant to test a target parseLab generator module's ability to generate
    a parser for each of the supported value types in parseLab'''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.protocol_dir = os.path.join(self.__get_test_dir(), 'test_protocol')
        self.testcase = os.path.join(self.protocol_dir, gen_util.testcase_dirname, 'value_types_test')

    def __get_test_dir(self):
        ''' Get the path to the directory that holds a suite of generic messages which are designed to
        test the ability for a generated parser to parse all of the data types available to the parseLab
        framework '''
        return os.path.join(gen_util.PARSELAB_TOP, gen_util.unit_tests_dirname, 'ValueTypesTest')

    def clean(self):
        ''' Remove all of the files that were generated as a result of a previous iteration of this test '''
        self.log.info("Cleaning up test directory")
        expected_files = [gen_util.protocol_spec_filename, 'testcases']

        protocol_dir = os.path.abspath(self.protocol_dir)
        TestUtils.rm_files(protocol_dir, expected_files)

    def run(self):
        ''' Execute the test.
        1. Clean up any existing files from previous tests
        2. Parse the pre-made protocol directory which contains a suite of test messages
        3. Generate a parser from the target parseLab module
        4. Execute the parser and run it against the suite of test messages
        5. Verify that the generated parser can properly handle the suite of test messages '''
        # Clean up any files from previous tests
        self.clean()

        protocol_dir = os.path.abspath(self.protocol_dir)
        directory_parser = ProtocolDirectoryParser(protocol_dir, logger=self.log)

        if not directory_parser.check_valid():
            self.log.info(TestUtils.invalid_directory_err)
            raise Exception(TestUtils.invalid_directory_err)

        self.log.info("Generating an instance of the Generator Under Test")
        generator = self.generator_class.create_instance(protocol_dir=protocol_dir, \
                                                              logger=self.log, \
                                                              is_stateful=directory_parser.is_stateful())

        # Run the setup steps
        data_dir = self.generator_class.get_setup_directory()
        setup_dirname = self.generator_class.get_setup_directory_name()

        self.log.info("Creating directory structure using Generator Under Test")
        gen_util.create_setup_dir_structure(data_dir, self.protocol_dir, setup_dirname, ignore_parselab_data=True)

        # Get the protocol/misison spec data
        self.log.info("Getting protocol and mission specification data")
        spec_data = directory_parser.get_spec_data()
        generator.set_spec_data(spec_data)

        # Generate the parser
        self.log.info("Generating the parser from the test data set")
        generator.generate_parser()

        # Verify that the target testcase exists / is_valid
        self.log.info("Validating target testcase directory of test: (%s)" % (self.testcase))
        if not directory_parser.verify_testcase(self.testcase):
            self.log.error(TestUtils.invalid_directory_err)
            raise Exception(TestUtils.invalid_directory_err)

        # Generate the test
        self.log.info("Generating an exectuable test with respect to testcase(%s)" % (self.testcase))
        generator.generate_test(self.testcase, self.protocol_dir, print_results=False)

        # Run the test and verify the output
        self.log.info("Running exectuable test for requrested testcase (%s)" % (self.testcase))
        fail_count = generator.run_test_from_testcase(self.testcase, self.protocol_dir)
        if fail_count > 0:
            return gen_util.TEST_FAIL, "run_test_from_testcase() Returned a fail_count of greater than 0"

        return gen_util.TEST_PASS, None
