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


''' ProtocolDirectoryParser.py contains all of the necessary classes and functions for properly parsing
protocol directories '''

import json
import os

from src.JsonSpecParser import JsonSpecParser
from src.ParselabLogger import ParselabLogger
from src.utils import gen_util

class ProtocolDirectoryParser:
    ''' The ProtocolDirectoryParser class contains all of the properties and functions which are used to
    parse and process the information within a supplied protocol directory '''
    def __init__(self, protocol_dir, logger=None):
        self.log = logger
        if self.log is None:
            self.log = ParselabLogger(print_logs=False)
        self.protocol_dir = protocol_dir
        self.is_valid = self.check_valid()
        self.check_mission_type()

    def check_valid(self):
        ''' Determine if the set protocol directory is valid or not; was it built properly? '''
        if not os.path.isdir(self.protocol_dir):
            self.log.warn("Supplied protocol directory (%s) does not exit" % (self.protocol_dir))
            return False

        protocol_spec_filepath = self.get_protocol_spec()
        if protocol_spec_filepath is None:
            self.log.warn("Protocol spec does not exist in protocol directory (%s) or is invalid" % (self.protocol_dir))
            return False

        self.log.info("Supplied protocol directory (%s) is valid." % (self.protocol_dir))
        return True

    def is_stateful(self):
        ''' Does this protocol directory contain stateful information? '''
        return (self.get_mission_states_dir() is not None) or (self.get_mission_spec() is not None)

    def check_mission_type(self):
        ''' Use this to determine if the protocol dir is using the mission spec or a modelio workspace.
    If modelio is used, then self.use_spec'''
        mission_states_dir = self.get_mission_states_dir()
        mission_spec = self.get_mission_spec()

        self.use_spec = False
        if mission_states_dir is None and mission_spec is not None:
            self.log.info("No mission states found; using mission spec")
            self.use_spec = True

    def get_protocol_spec(self):
        ''' Find and return the path to the protocol specification file used in this protocol directory '''
        protocol_spec_filepath = os.path.join(self.protocol_dir, gen_util.protocol_spec_filename)
        self.log.info("Verifying expected filepath of protocol spec file...")
        if not os.path.isfile(protocol_spec_filepath):
            self.log.warn("Protocol spec does not exist in protocol dir. Expected path: %s" % (protocol_spec_filepath))
            return None
        self.log.info("Verifying protocol spec is a non-empty file...")
        if os.path.getsize(protocol_spec_filepath) == 0:
            self.log.warn("Protocol spec is empty! Please fill out the protocol spec file with information \
about your target protocol.")
            return None

        return protocol_spec_filepath

    def get_mission_spec(self):
        ''' Find and return the path to the mission specificatoin file (if it exists) in this protocol directory '''
        mission_spec_filepath = os.path.join(self.protocol_dir, gen_util.mission_spec_filename)
        self.log.info("Checking expected filepath of mission spec file...")
        if not os.path.isfile(mission_spec_filepath):
            self.log.info("Mission spec does not exist in protocol dir. If this is unexpected, put mission spec \
file in to expected path: %s" % (mission_spec_filepath))
            return None
        self.log.info("Checking if mission spec is non-empty...")
        if os.path.getsize(mission_spec_filepath) == 0:
            self.log.warn("Mission spec file found, but it is empty! Ignoring mission spec file.")
            return None
        self.log.info("Checking if mission spec has no messages inside of it...")
        if not self.mission_json_has_data(mission_spec_filepath):
            self.log.warn("Mission spec file has no data inside! Ignoring mission spec file.")
            return None
        return mission_spec_filepath

    def mission_json_has_data(self, json_filepath):
        ''' Determine if the json-based mission specification file has data or if it is an empty structure '''
        with open(json_filepath, 'r') as spec_file:
            try:
                spec_data = json.load(spec_file)
            except Exception as e:
                err_msg = "Unable to load spec file (%s) with json.load() - Ensure that the spec file is correctly \
formatted!\n%s" % (json_filepath, str(e))
                self.log.error(err_msg)
                raise Exception(err_msg)

        if spec_data is None:
            raise Exception("json.load() returned null; unexpected")

        mission_types = spec_data["mission_types"]
        if isinstance(mission_types, list):
            if len(mission_types) == 0:
                return False
        else:
            err_msg = "Mission spec file is not appropriately defined.  The first json object needs to be a list \
named \"mission_types\""
            self.log.error(err_msg)
            raise Exception(err_msg)

        return True

    def get_mission_states_dir(self):
        ''' Get the directory where the mission states information is '''
        mission_states_dir = os.path.join(self.protocol_dir, gen_util.mission_states_dirname)
        if os.path.isdir(mission_states_dir):
            self.log.info("Mission states found in protocol directory")
            return mission_states_dir
        self.log.info("Mission states not found in protocol dir. Expected path: %s" % (mission_states_dir))
        return None

    def has_mission_states(self):
        ''' Does the target protocol directory utilize mission_states '''
        return self.get_mission_states_dir() is not None

    def get_mission_state_files(self):
        ''' Get all of the submission specification files '''
        states_dir = self.get_mission_states_dir()
        if states_dir is None:
            self.log.info("No mission states directory (%s) found in protocol directory" % (states_dir))
            return None
        state_files = [f for f in os.listdir(states_dir) \
                            if os.path.isfile(os.path.join(states_dir, f)) and os.path.splitext(f)[-1]]
        self.log.info("Found state files in mission states directory (%s)" % (states_dir))
        return state_files

    def get_transitions(self):
        ''' Get the transition specificaiton file '''
        states_dir = self.get_mission_states_dir()
        transition_file = os.path.join(states_dir, gen_util.mission_states_ext)
        if not os.path.isfile(transition_file):
            self.log.warn("No transition file found in mission states dir (%s)" % (states_dir))
            return None
        self.log.info("Found transition file in mission states dir (%s)" % (transition_file))
        return transition_file

    def get_spec_data(self):
        ''' Use the spec parser to extract information from the specification files and return the data '''
        protocol_spec = self.get_protocol_spec()
        if protocol_spec is None:
            err_msg = "There is no protocol spec found in the protocol directory (%s)" % (protocol_spec)
            self.log.error(err_msg)
            raise Exception(err_msg)

        # Parse the protocol spec
        spec_parser = JsonSpecParser(self.log)
        spec_data = spec_parser.parse_protocol_spec(protocol_spec)
        self.log.info("Successfully parsed protocol specification file")

        # Parse the mission spec (or MBSE diagram structure)
        if not self.is_stateful():
            self.log.info("No stateful information found")
            return spec_data

        if not self.use_spec:
            raise NotImplementedError("The MBSE workspace based specification is not imlemented")
        mission_spec = self.get_mission_spec()
        if mission_spec is not None:
            self.log.info("Mission specification file found: %s" % (mission_spec))
            mission_spec_data = spec_parser.parse_mission_spec(mission_spec)
            spec_data = spec_parser.add_mission_types_to_protocol_defs(mission_spec_data, spec_data)
            self.log.info("Added mission spec data to the protocol spec data")

        return spec_data

    def verify_testcase(self, testcase_dir):
        ''' Verify that the supplied testcase directory exists (where it should exist) in this protocol directory '''
        testcases_dir = os.path.join(self.protocol_dir, gen_util.testcase_dirname)
        self.log.info("Verifying existence the top level testcase directory (%s)" % (testcases_dir))
        if not os.path.isdir(testcases_dir):
            self.log.warn("The top level testcase directory (%s) does not exist!" % (testcases_dir))
            return False

        self.log.info("Verifying existence of the target testcase directory (%s)" % (testcase_dir))
        if not os.path.isdir(testcase_dir):
            self.log.warn("The target testcase directory (%s) does not exist!" % (testcase_dir))
            return False

        self.log.info("Verifying expected files in target testcase directory...")
        # Checking the results file and xxd file... this should be enough but obviously more checks could be helpful
        results_file = os.path.join(testcase_dir, gen_util.results_filename)
        if not os.path.isfile(results_file):
            self.log.warn("The target testcase directory does not have a results file (%s)" % (results_file))
            return False

        xxd_files = [f for f in os.listdir(testcase_dir) if os.path.splitext(f)[-1] == '.xxd']
        if len(xxd_files) <= 0:
            self.log.warn("There is no xxd file  in the testcase directory (%s)" % (testcase_dir))
            return False

        return True
