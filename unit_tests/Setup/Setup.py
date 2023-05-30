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


''' Setup.py contains all of the necessary classes and functions pertaining to running the unit
tests responsible for validating that the target parseLab generator module is able to properly
generate the necessary file structure inside the target protocol directory. '''

import os

from unit_tests.ParselabTest import ParselabTest
from src.utils import gen_util

class Setup(ParselabTest):
    ''' Setuy contains the properties and functions for validating that the target parseLab generator
    module is properly generating the necessary file structure inside the target protocol directory '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        ''' Remove all of the remaining files from a previous instance of this test '''
        self.log.info("Nothing to clean")

    def run(self):
        ''' Execute this test.
        1. Clean any remaining files from previous tests
        2. Generate the necessary directory structure for the target protocol directory
        3. Ensure that the directory was created properly '''
        # Clean up any files from previous tests
        self.clean()

        self.log.info("Testing: get_setup_directory()")
# Want to catch everything
        try:
            data_dir = self.generator_class.get_setup_directory()
        except Exception as e:
            return gen_util.TEST_FAIL, "get_setup_directory() Threw an error: \n%s" % str(e)

        if data_dir is not None and not os.path.isdir(data_dir):
            return gen_util.TEST_FAIL, "get_setup_directory() Returned an invalid directory (%s)" % (data_dir)

        self.log.info("Testing: get_setup_directory_name()")
# Want to catch everything
        try:
            setup_dirname = self.generator_class.get_setup_directory_name()
        except Exception as e:
            return gen_util.TEST_FAIL, "get_setup_directory_name() Threw an error: %s" % str(e)

        if setup_dirname is None or setup_dirname == '':
            return gen_util.TEST_FAIL, "get_setup_directory_name() Returned a None or empty dirname"

        pass_msg = ''
        if data_dir is None or data_dir == '':
            pass_msg = "WARN: get_setup_directory() Returned None or an empty string"

        return gen_util.TEST_PASS, pass_msg
