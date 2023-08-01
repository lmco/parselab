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


''' PacketGenerator.py contains all the necessary classes and functions for
generating valid and invalid messages using a supplied protocol specification '''

import random
import os
import hexdump

from src.ParselabLogger import ParselabLogger
from src.ProtocolDirectoryParser import ProtocolDirectoryParser
from src.utils import gen_util

result_codes = {
    0 : "PASS",
    1 : "FAIL",
}

class PacketGenerator:
    ''' The PacketGenerator class is responsible for consuming a protocol directory
        which holds specification data about a particular message format and generating
        invalid/valid messages for a supplied type of message '''

    def __init__(self, protocol_dir, logger=None):
        self.log = logger
        if self.log is None:
            self.log = ParselabLogger(print_logs=False)

        if not os.path.isdir(protocol_dir):
            raise NotADirectoryError("Supplied protocol directory is not an existing directory!")

        self.protocol_dir = protocol_dir
        self.directory_parser = ProtocolDirectoryParser(self.protocol_dir, self.log)
        self.spec_data = self.directory_parser.get_spec_data()

    def generate_packet_from_name(self, msg_name, valid):
        ''' Generate a single packet which conforms(valid=True) or does not conform(valid=False) to the protocol spec
        param   str:msg_name        The name of the message type that should be generated
        param   bool:valid          Should the generated packet be valid or invalid with respect to the protocol spec

        return  (bytearray:msg_bytes, int:result_code, list:invalid_fields) '''
        validity_str = 'valid' if valid else 'invalid'
        self.log.info("Generating a %s %s packet" % (validity_str, msg_name))

        for msg_type in self.spec_data.message_types:
            if msg_name.lower() == msg_type.name.lower():
                return self.fuzz_msg_type(msg_type, valid)

        return None, None, None, None

    def generate_packet_from_msg(self, msg_type, valid):
        ''' Generate a single packet which conforms(valid=True) or does not conform(valid=False) to the protocol spec
        param   MessageType:msg_type        The type of message that should be generated
        param   bool:valid                  Should the generated packet be valid or invalid with
                                              respect to the protocol spec

        return  (bytearray:msg_bytes, int:result_code, list:invalid_fields) '''
        validity_str = 'valid' if valid else 'invalid'
        self.log.info("Generating a %s %s packet" % (validity_str, msg_type.name))
        return self.fuzz_msg_type(msg_type, valid)

    def fuzz_msg_type(self, msg_type, valid):
        ''' Use the packet generation functions to generate a packet which conforms (valid=True),
        or does not conform (valid=False) to the protocol specificaiton
        param   MessageType:msg_type        The type of message that should be generated
        param   bool:valid                  Should the generated packet be valid or invalid with
                                              respect to the protocol spec

        return  (bytearray:serialized_value, int:serialized_size, bool:is_valid)'''
        def generate_valid_field(field):
            gen_value = field.generate_valid_value()
            gen_value.set_field(field)
            return gen_value

        def generate_valid_struct(self, struct_field):
            field_values_list = list()
            self.log.info("   Generating a valid struct (%s)" % (struct_field.dtype.struct_ref))
            list_len = 1
            if struct_field.dtype.is_list:
                if not struct_field.dtype.has_type_dependency:
                    list_len = field.dtype.list_count
                else:
                    if struct_field.dtype.dependency.lower() not in gen_util.dependency_values:
                        err_msg = "dependency (%s) is not in list of dependency_value keys: %s.\n did you mean to \
put '\"dependee\":\"true\"' in the dependee's struct_field?" % (struct_field.dtype.dependency.lower(), \
gen_util.dependency_values.keys())
                        self.log.error(err_msg)
                        raise Exception(err_msg)
                    try:
                        list_len = int(gen_util.dependency_values[struct_field.dtype.dependency.lower()])
                    except:
                        err_msg = "cannot convert value (%s) to integer." % \
                                     (gen_util.dependency_values[struct_field.dtype.dependency])
                        self.log.error(err_msg)
                        raise ValueError(err_msg)

            for _ in range(list_len):
                struct_values = struct_field.dtype.struct_ref.generate_valid_values()
                for struct_value in struct_values:
                    self.log.info("     %s" % struct_value)
                    field_values_list.append(struct_value)
                self.log.info("")
            return field_values_list

        def generate_invalid_field(field):
            gen_value = field.generate_invalid_value()
            gen_value.set_field(field)
            return gen_value

        def generate_invalid_struct(self, struct_field):
            field_values_list = list()
            struct_ref = struct_field.dtype.struct_ref
            self.log.info(" Generating an invalid struct (%s)" % (struct_ref.name))
            invalid_info = gen_util.INVALID_TYPE.VALID_VALUE
            if struct_field.dtype.is_list:
                list_len = 1
                if not struct_field.dtype.has_type_dependency:
                    list_len = field.dtype.list_count
                else:
                    if struct_field.dtype.dependency.lower() not in gen_util.dependency_values:
                        err_msg = "dependency (%s) is not in list of dependency_value keys: %s.\n did you mean to \
put '\"dependee\":\"true\"' in the dependee's struct_field?" % (struct_field.dtype.dependency.lower(), \
gen_util.dependency_values.keys())
                        self.log.error(err_msg)
                        raise SyntaxError(err_msg)
                    try:
                        list_len = int(gen_util.dependency_values[struct_field.dtype.dependency.lower()])
                    except:
                        err_msg = "cannot convert value (%s) to integer." % \
                                     (gen_util.dependency_values[struct_field.dtype.dependency])
                        self.log.error(err_msg)
                        raise ValueError(err_msg)
                self.log.info("    Generating a list with extra elements")
                list_len += 1
                for i in range(list_len):
                    invalid_info = gen_util.INVALID_TYPE.HIGH_LIST_LENGTH
                    struct_field.dtype.is_list = False
                    struct_values = generate_valid_struct(self, struct_field)
                    struct_field.dtype.is_list = True
                    field_values_list.extend(struct_values)
            else:
                corruptable_members = list()
                corrupted_member_index = -1
                for i, member in enumerate(struct_ref.members):
                    self.log.info("Checking if struct member (%s) can be invalid..." % (member.name))
                    if member.can_generate_invalid_instance():
                        self.log.info("  Member (%s) can be invalid" % member.name)
                        corruptable_members.append((i, member))
                    else:
                        self.log.info("  Member (%s) cannot be invalid" % member.name)

                if len(corruptable_members) > 0:
                    self.log.info("There are %d members that can be corrupted" % len(corruptable_members))
                    rand_value = random.randrange(0, len(corruptable_members))
                    corrupted_member = corruptable_members[rand_value]
                    corrupted_member_index = corrupted_member[0]

                self.log.info("Corrupting member: %s" % corrupted_member[1].name)
                for i, member in enumerate(struct_ref.members):
                    if member.dtype.is_struct:
                        if i == corrupted_member_index:
                            self.log.info("Generating an invalid struct for member: %s" % member.name)
                            invalid_info, invalid_fields = generate_invalid_struct(self, member)
                            field_values_list.extend(invalid_fields)
                            for f in invalid_fields:
                                self.log.info("    %s" % (f))
                            self.log.info("")
                        else:
                            self.log.info("Generating a valid struct for member: %s" % member.name)
                            valid_fields = generate_valid_struct(self, member)
                            field_values_list.extend(valid_fields)
                            for f in valid_fields:
                                self.log.info(" %s" % (f))
                            self.log.info("")
                    else:
                        if i == corrupted_member_index:
                            self.log.info("Generating an invalid value for member: %s" % (member.name))
                            generated_value = generate_invalid_field(member)
                            invalid_info = '%s - %s' % (member.name, generated_value.value_type.name)
                        else:
                            self.log.info("Generating a valid value for member: %s" % (member.name))
                            generated_value = generate_valid_field(member)

                        generated_value.set_field(member)
                        self.log.info("     %s" % (generated_value))
                        field_values_list.append(generated_value)

            self.log.info("Generated with invalid_info: %s" % invalid_info)
            return invalid_info, field_values_list

        valid_string = 'n invalid' if not valid else ' valid'
        self.log.info("Attempting to fuzz a%s instance of message type: %s" % (valid_string, msg_type.name))

        generated_value = None
        field_values_list = []
        is_valid = valid
        invalid_info = ''

        if valid:
            for field in msg_type.fields:
                self.log.info("Generating a valid field (%s)" % (field.name))
                if field.dtype.is_struct:
                    generated_struct_values = generate_valid_struct(self, field)
                    field_values_list.extend(generated_struct_values)

                else:
                    generated_value = generate_valid_field(field)
                    self.log.info("    %s" % generated_value)
                    field_values_list.append(generated_value)
        else:
            invalid_fields = []
            for i, field in enumerate(msg_type.fields):
                self.log.info("Checking if field (%s) can be invalid..." % (field.name))
                if field.can_generate_invalid_instance():
                    self.log.info("Appending field (%s) to list of potential fields to corrupt" % (field.name))
                    invalid_fields.append((i, field))

            if len(invalid_fields) == 0:
                self.log.warn("Messages without value constraints cannot have an invalid value. \
Generating a valid value for (%s) instead" % (msg_type.name))
                corrupted_field_index = -1
                is_valid = True
            else:
                corrupted_field = invalid_fields[random.randrange(0, len(invalid_fields))]
                corrupted_field_index = corrupted_field[0]
                is_valid = False

            for i, field in enumerate(msg_type.fields):

                if field.dtype.is_struct:
                    struct_ref = field.dtype.struct_ref
                    if i == corrupted_field_index:
                        self.log.info("Generating an invalid struct field (%s :: %s)" % \
                                      (field.name, struct_ref.name))
                        invalid_info, struct_field_list = generate_invalid_struct(self, field)
                    else:
                        self.log.info("Generating an valid struct field (%s :: %s)" % \
                                      (field.name, struct_ref.name))
                        struct_field_list = generate_valid_struct(self, field)

                    field_values_list.extend(struct_field_list)
                else:
                    if i == corrupted_field_index:
                        self.log.info("Generating an invalid field (%s)" % (field.name))
                        generated_value = generate_invalid_field(field)
                        invalid_info = '%s - %s' % (field.name, generated_value.value_type.name)
                    else:
                        self.log.info("Generating a valid field (%s)" % (field.name))
                        generated_value = generate_valid_field(field)

                    self.log.info("Appending %s to list of field values" % (generated_value))
                    field_values_list.append(generated_value)

        serialized_value, serialized_size = gen_util.serialize(field_values_list)
        return serialized_value, serialized_size, is_valid, invalid_info

    @staticmethod
    def hexdump_bytes(msg, size):
        ''' Generate a string containing the hexdump for a given string of message bytes '''
        hex_msg_str = gen_util.convert_int_to_hex_str(msg, size)
        try:
            hex_bytes = bytes.fromhex(hex_msg_str)
        except ValueError as e:
            raise ValueError("Unable to convert from hex (%s)\n%s" % (hex_msg_str, str(e)))
        return hexdump.hexdump(hex_bytes, result='return')

    @staticmethod
    def serialized_to_hex(msg, num_bytes):
        ''' Convert the bytearray string representation into a format without the leading 0x'''
        hex_msg = hex(msg)[2:]
        represented_chars = len(hex_msg)
        missing_zeros = num_bytes // 4 - represented_chars
        for _ in range(missing_zeros):
            hex_msg = "0" + hex_msg

        return hex_msg
