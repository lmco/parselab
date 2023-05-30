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


''' MessageType.py contains all of the classes and functions which pertain to processing and storing
information regarding a message type in the parseLab framework. '''

from . import gen_util

class MessageType:
    ''' Message type holds properties and functions about a message type which derrived from the protocol's
    specification format '''
    def __init__(self, name):
        self.name = name
        self.basename = name
        self.fields = []
        self.state_ids = []
        self.is_mission_type = False
        self.invalid_fields = []
        self.custom_data = {}

    def __repr__(self):
        return str(self.__dict__)

    def compare_mission_type(self, mission_type):
        ''' Determine if a mission type is of the same type as this message type '''
        return mission_type.basename == self.basename

    def compare_message_type(self, message_type):
        ''' Compare another message type against this one '''
        for field in message_type.fields:
            field_names_match = False
            for myField in self.fields:
                if field.name == myField.name:
                    field_names_match = True
            if not field_names_match:
                return False

            values_match = False
            for myField in self.fields:
                if str(field.value_def) == str(myField.value_def):
                    values_match = True
            if not values_match:
                return False

        return True

class MissionType():
    ''' MissionType holds properties and functions about a message type which is derrived from the mission's
    specification format '''
    def __init__(self, name, fields=None):
        self.name = name
        self.basename = name
        self.fields = fields if fields is not None else []
        self.custom_data = {}

class MissionTypeField():
    ''' MissionTypeFields holds properties and functions used for processing and storing information about a
    field in a mission type message '''
    def __init__(self, field_string, name='', value=''):
        if field_string is not None and field_string != '':
            self.parse_field_string(field_string)
        if name != '':
            self.name = name
        if value != '':
            self.value = value

        self.custom_data = {}

    def parse_field_string(self, field_string):
        ''' Parse a string which represents a field in a mission specification '''
        try:
            self.name, self.value = gen_util.adv_split(field_string, ':', '\"\'', '\"\'')
        except:
            err_msg = "MissionTypeField - Unable to parse the field: %s" % field_string
            #log_error(err_msg)
            raise SyntaxError(err_msg)

    def __str__(self):
        return "%s:%s" % (self.name, self.value)
