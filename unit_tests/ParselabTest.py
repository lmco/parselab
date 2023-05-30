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


''' ParselabTest.py contains all of the necessary classes and functions pertaining to the abstract concept
of a parseLab unit test '''

from importlib import import_module

from src.ParselabLogger import ParselabLogger
from src.utils import gen_util

class ParselabTest:
    ''' ParselabTest is meant to be an abstract class which contains properties
    and functions which are relevate to any and all parseLab unit tests. '''
    def __init__(self, target_module=None, logger=None):
        self.log = logger
        if self.log is None:
            self.log = ParselabLogger(print_logs=False)

        if target_module is None:
            err_msg = "ParselabTest modules must have a target generator module specified!"
            self.log.error(err_msg)
            raise Exception(err_msg)

        self.module_path = target_module
        self.module_name = target_module.split('.')[-1]
        self.module = import_module(self.module_path)

        self.generator_class = getattr(self.module, self.module_name)

    @classmethod
    def create_instance(cls, *args, **kwargs):
        ''' Create an instance of this class '''
        return cls(*args, **kwargs)

    def clean(self):
        ''' Remove any files or changes made by this test'''
        return

    def run(self):
        ''' Run this test. Expected to return boolean value
        return false    = FAIL
        return true     = PASS '''
        return gen_util.TEST_FAIL, "ParselabTest.run() Not implemented yet!"
