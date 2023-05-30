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


''' GenerateParser.py contains all of the necessary classes and functions pertaining to running the unit
tests responsible for validating the generation of a parser when requested of a parseLab generator module '''

import os

from unit_tests.ParselabTest import ParselabTest
from unit_tests import TestUtils
from src.ProtocolDirectoryParser import ProtocolDirectoryParser
from src.utils import gen_util

class GenerateParser(ParselabTest):
    ''' GenerateParser contains the properties and functions for validating that the target parseLab generator
    module is properly generating an executable parser '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.protocol_dir = os.path.join(self.__get_test_dir(), 'test_protocol')

    def __get_test_dir(self):
        ''' Get the path to the directory which contains the pre-made protocol directory for this test '''
        return os.path.join(gen_util.PARSELAB_TOP, gen_util.unit_tests_dirname, 'GenerateParser')

    def clean(self):
        ''' Remove all of the remaining files from a previous instance of this test '''
        self.log.info("Cleaning up test directory")
        expected_files = [gen_util.protocol_spec_filename]

        protocol_dir = os.path.abspath(self.protocol_dir)
        TestUtils.rm_files(protocol_dir, expected_files)

    def run(self):
        ''' Execute this test.
        1. Clean up any remaining files from previous tests
        2. Parse the pre-made protocol directory
        3. Generate the files and parser code for the target parseLab generator module
        4. Verify that all of the files that the module stated to have generated were actually placed
            onto the file sytem
        '''
        # Clean up any files from previous tests
        self.clean()

        protocol_dir = os.path.abspath(self.protocol_dir)
        directory_parser = ProtocolDirectoryParser(protocol_dir, logger=self.log)

        if not directory_parser.check_valid():
            err_msg = "The directory structure for this unit test is incorrect.  Please re-clone the parseLab repo"
            self.log.error(err_msg)
            raise Exception(err_msg)

        # Load the Generator Under Test
        self.log.info("Creating an instance of the Generator Under Test")
        generator = self.generator_class.create_instance(protocol_dir=protocol_dir, \
                                                              logger=self.log, \
                                                              is_stateful=directory_parser.is_stateful())

        # Run the setup steps (required to properly generate a parser)
        data_dir = self.generator_class.get_setup_directory()
        setup_dirname = self.generator_class.get_setup_directory_name()

        self.log.info("Creating directory structure using Generator Under Test")
        gen_util.create_setup_dir_structure(data_dir, self.protocol_dir, setup_dirname, ignore_parselab_data=True)

        # Get the protocol/mission specifiction data
        self.log.info("Getting protocol and misison specification data")
        spec_data = directory_parser.get_spec_data()
        generator.set_spec_data(spec_data)

        # Generate the parser
        self.log.info("Generating the parser from the test data set")
        generated_files = generator.generate_parser()

        for f in generated_files:
            self.log.info("Verifying File Existence (%s)" % (f))
            if not os.path.isfile(f):
                return gen_util.TEST_FAIL, "generate_parser() Returned file (%s) but it does not exist!" % (f)

        return gen_util.TEST_PASS, None
