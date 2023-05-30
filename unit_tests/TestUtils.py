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


''' TestUtils.py conatins all of the necessary classes and functions which are used across multiple
parseLab unit tests '''

import os
import shutil

invalid_directory_err = "The directory strcture for this unit test is incorrect. Please re-clone the parselab repo"

def rm_files(target_dir, except_list=None):
    ''' Remove all of the files in a target directory, excluding those of which are passed in with the
    `except_list` list argument '''
    if not os.path.isabs(target_dir):
        raise Exception("rm_files() Must be supplied an absolute path; relative paths are not accepted")

    if except_list is None:
        except_list = []
    files = [os.path.join(target_dir, f) for f in os.listdir(target_dir) if f not in except_list]

    for f in files:
        if os.path.isdir(f):
            shutil.rmtree(f)
        elif os.path.isfile(f):
            os.remove(f)
        else:
            raise Exception("Unexpected file (%s) found in target_dir. Aborting")
