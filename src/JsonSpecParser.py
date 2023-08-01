#!/usr/bin/env python3
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


''' JsonSpecParser.py contains all the necessary classes and functions for parsing a
json-based specification file and generating SpecData to be used throughout the
parseLab framework '''

from copy import deepcopy
import json

from src.ParselabLogger import ParselabLogger
from src.utils.FieldDef import FieldDef
from src.utils.MessageType import MessageType, MissionType, MissionTypeField
from src.utils.ValueDef import ValueDef
from src.utils.DType import DType, Struct
from src.utils import gen_util


class ProtocolSpecData:
    ''' ProtocolSpecData contains messages types which are NOT mission messages; The
    messages in this object are syntax ONLY '''
    def __init__(self, message_types, struct_list):
        self.message_types = message_types
        self.struct_list = struct_list

class MissionSpecData:
    ''' MissionSpecData contains message types which ARE mission messages; The
    messages in this object contain syntax and semantic information '''
    def __init__(self, mission_types):
        self.mission_types = mission_types

class JsonSpecParser:
    ''' The JsonSpecParser class is responsible for handling the parsing and processing
    of the json-based protocol specification file '''

    def __init__(self, logger=None):
        self.log = logger
        if self.log is None:
            self.log = ParselabLogger()
        self.struct_list = list()

    def parse_protocol_spec(self, spec_filepath):
        ''' Given a filepath, attempt to parse the file as if it is a json-format
        which specifies information about the target protocol.  Once parsed, the
        information from the file will be stored in this class for reference throughout
        the use of the parseLab framework '''
        self.log.info("Parsing protocol specification (%s)" % (spec_filepath))

        self.parse_custom_structs(spec_filepath)

        with open(spec_filepath, 'r') as spec_file:
            try:
                spec_data = json.load(spec_file)
            except Exception as e:
                err_msg = "Unable to load spec file (%s) with json.load() - Ensure that the protocol \
spec is correctly formatted!\n%s" % (spec_filepath, str(e))
                self.log.error(err_msg)
                raise Exception(err_msg)

        if spec_data is None:
            raise Exception("json.load() Returned null; unexpected")

        message_types = []

        # this iterates over the full message object
        for msg_obj in spec_data[gen_util.protocol_types_k]:

            # prioritize "msg_name" first. if it doesn't exist, use "name" instead.
            if gen_util.msg_spec_name_k in msg_obj:                     # msg_name
                msg = MessageType(msg_obj[gen_util.msg_spec_name_k])
            elif gen_util.name_k in msg_obj:                            # name
                msg = MessageType(msg_obj[gen_util.name_k])
            else:
                err_msg = "All messages are required to have a name!"
                self.log.error(err_msg)
                raise Exception(err_msg)

            self.log.info("Parsing information about message type: %s" % (msg.name))

            field_data = msg_obj[gen_util.fields_k]
            msg_ignore = msg_obj.get(gen_util.ignore_k)
            if msg_ignore is not None:
                if msg_ignore.lower() == 'true':
                    self.log.info("Skipping processing of message type")
                    continue

            # this iterates over each field within the message object
            for field_obj in field_data:
                field = self.create_field_from_json_dict(field_obj, msg.name)
                if field is None:
                    continue
                msg.fields.append(field)

            message_types.append(msg)
            non_custom_keys = [gen_util.name_k, \
                               gen_util.msg_spec_name_k, \
                               gen_util.fields_k]
            custom_keys = [key for key in list(msg_obj.keys()) if key not in non_custom_keys]

            if len(custom_keys) > 0:
                for k in custom_keys:
                    msg.custom_data[k] = msg_obj.get(k)

                self.log.info("Custom attributes found on message (%s)" % (msg.name))
                for k in list(msg.custom_data.keys()):
                    self.log.info("   [%s] : [%s]" % (k, msg.custom_data.get(k)))

        spec_data = ProtocolSpecData(message_types, self.struct_list)
        return spec_data

    def parse_custom_structs(self, structs_filepath):
        ''' Given a filepath, attempt to parse the file as json-format and extract information
        about custom structs defined in it for use in the message type definitions in the
        protocol specification '''
        self.log.info("Parsing Custom Objects in file: %s" % (structs_filepath))

        with open(structs_filepath, 'r') as structs_file:
            try:
                structs_data = json.load(structs_file)
            except Exception as e:
                err_msg = "Unable to load structs file (%s) with json.load() - Ensure that the \
file is correctly formatted!\n%s" % (structs_filepath, str(e))
                self.log.error(err_msg)
                raise Exception(err_msg)

        if structs_data is None:
            err_msg = "Json.load() returned null; unexpected"
            self.log.error(err_msg)
            raise Exception(err_msg)

        if gen_util.structs_k not in structs_data:
            return

        for struct_obj in structs_data[gen_util.structs_k]:
            if gen_util.struct_name_k in struct_obj:
                struct_name = struct_obj.get(gen_util.struct_name_k)
            elif gen_util.name_k in struct_obj:
                struct_name = struct_obj.get(gen_util.name_k)
            else:
                err_msg = "All structss are required to have a name!"
                self.log.error(err_msg)
                raise SyntaxError(err_msg)

            if gen_util.ignore_k in struct_obj:
                self.log.info("Skipping struct (%s)" % struct_name)
                continue

            if not gen_util.struct_members_k in struct_obj:
                err_msg = "All structs are required to have a members list!"
                self.log.error(err_msg)
                raise SyntaxError(err_msg)

            member_data = struct_obj.get(gen_util.struct_members_k)
            members = []

            for member_obj in member_data:
                member_field = self.create_field_from_json_dict(member_obj, struct_name)
                members.append(member_field)
            s = Struct(struct_name, members)
            self.struct_list.append(s)

            if gen_util.field_value_k in struct_obj:
                err_msg = "Structs cannot have a value associated to them!"
                self.log.error(err_msg)
                raise SyntaxError(err_msg)

    def create_field_from_json_dict(self, field_obj, owner_name):
        ''' Create a FieldDef object from a JSON object '''
        # REQUIRED FIELD ATTRIBUTES
        # prioritize "field_name" first. if it doesn't exist, use "name" instead.
        if gen_util.field_spec_name_k in field_obj:
            field_name = field_obj.get(gen_util.field_spec_name_k)
        elif gen_util.name_k in field_obj:
            field_name = field_obj.get(gen_util.name_k)
        else:
            err_msg = "All message fields are required to have a name!"
            self.log.error(err_msg)
            raise Exception(err_msg)
        self.log.info("Parsing information about field: %s" % (field_name))

        field_type = field_obj.get(gen_util.field_type_k)
        if field_type is None or str(field_type) == '':
            err_msg = "All message fields are required to have a type!"
            self.log.error(err_msg)
            raise Exception(err_msg)

        # If this field has an ignore tag, ignore the field
        field_ignore = field_obj.get(gen_util.ignore_k)
        if field_ignore is not None:
            if field_ignore.lower() == 'true':
                self.log.info("Skipping processing of field")
                return None

        # If this field has a strict tag, the specified value cannot
        #  be fuzzed as invalid
        value_strict = field_obj.get(gen_util.strict_k)
        value_strict = value_strict is not None and value_strict.lower() == 'true'

        # OPTIONAL FIELD ATTRIBUTES
        field_value = field_obj.get(gen_util.field_value_k)
        field_dependee = field_obj.get(gen_util.field_dependee_k)
        if field_dependee:
            field_dependee = field_name
        else:
            field_dependee = ''

        # Custom field attributes
        non_custom_keys = [gen_util.name_k, \
                           gen_util.field_spec_name_k, \
                           gen_util.field_type_k, \
                           gen_util.field_value_k, \
                           gen_util.field_dependee_k, \
                           gen_util.strict_k]
        custom_keys = [key for key in list(field_obj.keys()) if key not in non_custom_keys]

        dtype = DType(field_type, field_dependee, field_name, self.struct_list)
        if dtype.is_struct and field_value not in (None, ''):
            err_msg = "Fields with a struct data type cannot have a value definition! (%s - %s)" % \
                        (field_name, field_value)
            self.log.error(err_msg)
            raise SyntaxError(err_msg)
        value = ValueDef(dtype, field_value, 0)
        field = FieldDef(field_name, value, dtype, line_num=0, strict=value_strict)
        field.message_name = owner_name

        if len(custom_keys) > 0:
            for k in custom_keys:
                field.custom_data[k] = field_obj.get(k)

            self.log.info("Custom attributes found on field (%s)" % (field.name))
            for k in list(field.custom_data.keys()):
                self.log.info("   [%s] : [%s]" % (k, field.custom_data.get(k)))

        self.log.info("Field info: %s" % (str(field)))

        return field

    def parse_mission_spec(self, spec_filepath):
        ''' Given a filepath, attempt to parse the file as a json file and pull out information
        about a specified protocol's semantic information such as message type sequence and field
        differences based on message order '''
        self.log.info("Parsing mission specification file (%s)" % (spec_filepath))

        with open(spec_filepath, 'r') as spec_file:
            try:
                spec_data = json.load(spec_file)
            except Exception as e:
                err_msg = "Unable to load spec file (%s) with json.load() - Ensure that the mission \
spec is correctly formatted!\n%s" % (spec_filepath, str(e))
                self.log.error(err_msg)
                raise Exception(err_msg)

        if spec_data is None:
            raise Exception("json.load() Returned null; unexpected")

        mission_types = []
        for msg_obj in spec_data[gen_util.mission_types_k]:
            # prioritize "msg_name" first. if it doesn't exist, use "name" instead.
            if gen_util.msg_spec_name_k in msg_obj:                 # msg_name
                msg_name = msg_obj.get(gen_util.msg_spec_name_k)
            elif gen_util.name_k in msg_obj:                        # name
                msg_name = msg_obj.get(gen_util.name_k)
            else:
                err_msg = "All messages are required to have a name!"
                self.log.error(err_msg)
                raise Exception(err_msg)
            field_data = msg_obj.get(gen_util.fields_k)
            non_custom_keys = [gen_util.name_k, \
                               gen_util.msg_spec_name_k, \
                               gen_util.fields_k]
            custom_keys = [key for key in list(msg_obj.keys()) if key not in non_custom_keys]
            mission_type = MissionType(msg_name)

            if len(custom_keys) > 0:
                for k in custom_keys:
                    mission_type.custom_data[k] = msg_obj.get(k)

                self.log.info("Custom attributes found on mission type (%s)" % (mission_type.name))
                for k in list(mission_type.custom_data.keys()):
                    self.log.info("   [%s] : [%s]" % (k, mission_type.custom_data.get(k)))

            if field_data is None:
                mission_types.append(mission_type)
                continue
            fields = []
            for field_obj in field_data:
                # prioritize "field_name" first. if it doesn't exist, use "name" instead.
                if gen_util.field_spec_name_k in field_obj:
                    field_name = field_obj.get(gen_util.field_spec_name_k)
                elif gen_util.name_k in field_obj:
                    field_name = field_obj.get(gen_util.name_k)
                else:
                    err_msg = "All message fields are required to have a name!"
                    self.log.error(err_msg)
                    raise Exception(err_msg)
                field_value = field_obj.get(gen_util.field_value_k)
                field = MissionTypeField(None, field_name, field_value)
                # get custom data

                non_custom_keys = [gen_util.name_k, \
                                   gen_util.field_spec_name_k, \
                                   gen_util.field_value_k]
                custom_keys = [key for key in list(field_obj.keys()) if key not in non_custom_keys]

                if len(custom_keys) > 0:
                    for k in custom_keys:
                        field.custom_data[k] = field_obj.get(k)

                    self.log.info("Custom attributes found on field (%s)" % (field.name))
                    for k in list(field.custom_data.keys()):
                        self.log.info("   [%s] : [%s]" % (k, field.custom_data.get(k)))

                fields.append(field)
            mission_type.fields = fields
            mission_types.append(mission_type)

        spec_data = MissionSpecData(mission_types)
        return spec_data

    def create_stateful_mtype(self, mission_type, protocol_type, state_id):
        ''' Convert a protocol type message into a mission type message and set its state_id '''
        new_mtype = deepcopy(protocol_type)
        new_mtype.name = '%s_STATE_%s' % (new_mtype.name, state_id)
        new_mtype.state_ids.append(state_id)

        self.log.info("Mission type (%s) being created as a derivative of message type (%s)" % \
                            (mission_type.name, protocol_type.name))

        for mission_field in mission_type.fields:
            found = False
            for mtype_field in new_mtype.fields:
                if mission_field.name == mtype_field.name:
                    found = True
                    # set the value def
                    try:
                        self.log.info("Generating a ValueDef for field (%s) in message (%s)" % \
                                            (mission_field.name, mission_type.name))
                        value_def = ValueDef(mtype_field.dtype, mission_field.value)
                    except:
                        err_msg = "Unable to generate a ValueDef from mission type: %s" % mission_type.name
                        self.log.error(err_msg)
                        raise Exception(err_msg)

                    mtype_field.value_def = value_def

                    # combine the custom data for this field
                    for k in list(mission_field.custom_data.keys()):
                        self.log.info("Adding custom field attribute (%s) to the message type (%s)'s field (%s)" % \
                                            (k, new_mtype.name, mtype_field.name))
                        mtype_field.custom_data[k] = mission_field.custom_data.get(k)

            if not found:
                err_msg = "Could not find field with matching name (%s) for message type (%s)" % \
                                (mission_field.name, mission_type.name)
                self.log.error(err_msg)
                raise Exception(err_msg)

        # Take the custom attributes from the mission type and add it to the newly created stateful mtype
        for k in list(mission_type.custom_data.keys()):
            self.log.info("Adding custom mission type attribute (%s) to the stateful message type (%s)" % \
                                (k, new_mtype.name))
            new_mtype.custom_data[k] = mission_type.custom_data.get(k)

        return new_mtype

    def add_mission_type(self, mission_type, protocol_data, state_id):
        ''' Add a mission type to the existing list of mission types.  If the mission type is already in this
        list, then append the state ID which denotes which state the system needs to be in for the new mission
        type to be valid '''
        for message_type in protocol_data.message_types:
            # if a message type matches the mission type's fields
            if message_type.compare_mission_type(mission_type):
                self.log.info("Found matching message type in protocol spec data: %s" % (message_type.name))
                new_type = self.create_stateful_mtype(mission_type, message_type, state_id)
                new_type.is_mission_type = True
                # if the new type is the same field values as an existing type, append the state_id onto the
                #   existing type rather than appending this new type to the list of message types
                found_match = False
                matching_type = None
                for _message_type in protocol_data.message_types:
                    if _message_type.compare_message_type(new_type):
                        found_match = True
                        matching_type = _message_type

                if found_match:
                    self.log.info("Adding a state id to message")
                    matching_type.state_ids.append(state_id)
                    return protocol_data

                self.log.info("Adding the message type (%s) to the spec_data" % (new_type.name))
                protocol_data.message_types.append(new_type)
                return protocol_data

        return protocol_data

    def add_mission_types_to_protocol_defs(self, mission_data, protocol_data):
        ''' Combine the mission types with the protocol types to create one larger set '''
        state_id = 0
        for mission_type in mission_data.mission_types:
            self.log.info("Adding %s to protocol data" % (mission_type.name))
            protocol_data = self.add_mission_type(mission_type, protocol_data, state_id)
            state_id += 1

        return protocol_data
