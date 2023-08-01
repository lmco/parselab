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


''' DType.py contains all of the necessary classes and functions which are used to parse and process
the data type component of a field in the protocol specification '''

import random
import numpy as np

from src.utils.GeneratedValue import GeneratedValue
from src.utils import gen_util

class Struct:
    ''' This class holds the data and value generation funcitons for the Struct object '''
    def __init__(self, name, members):
        self.name = name
        self.members = members

    def __str__(self):
        member_string = ''
        for m in self.members:
            member_string += "%s, " % m
        member_string = member_string[:-2]
        ret = "%s: %s" % (self.name, member_string)
        return ret

    def generate_valid_values(self):
        ''' Generate a list of GeneratedValue instances which represents a flat-list of valid values for
        this struct '''
        valid_values = list()
        for member in self.members:
            if member.dtype.is_struct:
                list_len = 1
                if member.dtype.is_list and not member.dtype.has_type_dependency:
                    list_len = member.dtype.list_count
                elif member.dtype.has_type_dependency:
                    if member.dtype.dependency.lower() not in gen_util.dependency_values:
                        err_msg = "DType::generate_valid_value() - Dependency (%s) is not in list of dependency_value \
keys: %s.\n Did you mean to put '\"dependee\":\"True\"' in the Dependee's field?" % (member.dependency, \
gen_util.dependency_values.keys())
                        raise SyntaxError(err_msg)
                    try:
                        list_len = int(gen_util.dependency_values[member.dtype.dependency.lower()])
                    except:
                        err_msg = "DType::generate_valid_value() - Cannot convert value (%s) to integer." % \
                                    (gen_util.dependency_values[member.dtype.dependency])
                        raise ValueError(err_msg)

                for _ in range(list_len):
                    member_values = member.dtype.struct_ref.generate_valid_values()
                    valid_values.extend(member_values)
            else:
                valid_value = member.generate_valid_value()
                valid_values.append(valid_value)

        return valid_values

# Class that holds information abnout the data type
#   such as the number of bits that are defined
#           if it is a list or not
#           what dependencies it has
class DType:
    ''' DType holds information about the data type component of a field in the
    protocol spec; information such as the number of bits that are defined. '''
    def __init__(self, dtype_string, dependee, field_name, struct_list):
        self.signed = False
        self.is_int = False
        self.is_float = False
        self.is_list = False
        self.is_struct = False
        self.struct_ref = None
        self.list_count = 0
        self.main_type = ''
        self.dependency = ''
        self.has_type_dependency = False
        self.is_big_endian = True
        self.dtype_string = dtype_string
        # Do other fields depend on this one?
        self.dependee = dependee
        self.field_name = field_name
        self.struct_list = struct_list
        self.parse_dtype_string(dtype_string)
        self.bounds = gen_util.get_bounds(self.get_size_in_bits(), self.signed)

    def __str__(self):
        if self.dependency != '':
            return '%s[%s]' % (self.main_type, self.dependency)
        return '%s' % self.main_type

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.dtype_string == self.dtype_string and \
                                                 self.dependee == other.dependee

    def __hash__(self):
        return hash((self.dtype_string, self.dependee))

    def parse_dtype_string(self, dtype_string):
        ''' Parse a string to pull out dtype information from it '''
        dt_string, list_ref = DType.split_list_reference_from_dtype_string(dtype_string)
        dt_string, endianness_char = DType.split_endianness_from_dtype_string(dt_string)
        self.main_type = dt_string
        self.set_list_info(list_ref)
        self.is_big_endian = not endianness_char == gen_util.sym_little_endian

        # Is this type a custom struct?
        struct_ref = self.is_valid_struct_reference()
        if struct_ref is not None:
            self.is_struct = True
            self.struct_ref = struct_ref
        elif self.is_native_dtype():
            pass
        else:
            err_msg = "Assigned type (%s) is not a native type, or a valid struct reference!" % dtype_string
            raise SyntaxError(err_msg)

        # If it is a dependee, is_int must be true
        if self.dependee != '' and not self.is_int:
            err_msg = "DType- (%s) Cannot be a dependee without being of a native integer type." % (dtype_string)
            raise SyntaxError(err_msg)

    def set_list_info(self, list_ref):
        ''' Process the list_ref, which is inside of the brackets in a data type specification. '''
        if list_ref is None:
            return
        self.is_list = True

        if list_ref.isdigit():
            self.list_count = int(list_ref)
            if self.list_count == 0:
                raise ValueError("List length cannot be zero")
            if self.list_count < 0:
                raise ValueError("List length cannot be negative")
            return

        if gen_util.adv_isalnum(list_ref, '_'):
            self.has_type_dependency = True
            self.dependency = list_ref
            return
        raise SyntaxError("Improperly formatted list dependency string: %s" % list_ref)

    @staticmethod
    def is_custom_dtype(dtype_string):
        ''' Is this dtype a valid struct name:
        Custom Struct Rules:
            - No numbers
            - only letters and underscores'''

        if not gen_util.adv_isalpha(dtype_string, '_'):
            return False
        return True

    def is_valid_struct_reference(self):
        ''' Is this dtype a struct with a valid reference? '''
        struct_names = (s.name for s in self.struct_list)
        if DType.is_custom_dtype(self.main_type):
            if self.main_type not in struct_names:
                return None
            for s in self.struct_list:
                if s.name == self.main_type:
                    return s
        return None

    def is_native_dtype(self):
        ''' Is this dtype a native type '''
        if self.main_type[0] in gen_util.sym_native_types:
            if self.main_type[0] == gen_util.sym_native_signed:
                self.signed = True
                self.is_int = True
            elif self.main_type[0] == gen_util.sym_native_unsigned:
                self.signed = False
                self.is_int = True
            elif self.main_type[0] == gen_util.sym_native_float:
                try:
                    float_size = int(self.main_type[1:])
                except ValueError as e:
                    err_msg = "Dtype - Unable to parse data type for field: %s, did you mean F32?\nError:\n%s" \
                                    % (self.field_name, str(e))
                    raise SyntaxError(err_msg)
                if float_size != gen_util.native_float_size:
                    err_msg = "Dtype - Data type for field (%s) is not allowed, did you mean F32?" \
                                    % (self.field_name)
                    raise SyntaxError(err_msg)

                self.is_float = True

            sz = None
            try:
                sz = int(self.main_type[1:])
            except ValueError:
                return False

            if sz is not None and sz <= 0:
                err_msg = "DType - Cannot have a main type whos size is zero or a negative nuber (%d)\n\t%s" % \
                            (sz, self.main_type)
                raise ValueError(err_msg)

            if sz is not None and sz > 0:
                return True

        return False

    @staticmethod
    def split_list_reference_from_dtype_string(dtype_string):
        ''' Split up the list reference string from the data type string and return a tuple with the results '''
        dep_open_count = dtype_string.count(gen_util.sym_dependency_open)
        dep_close_count = dtype_string.count(gen_util.sym_dependency_close)
        if dep_open_count != dep_close_count:
            raise SyntaxError("Mismatch in dependency brackets! (%s)" % dtype_string)
        if dep_open_count > 1:
            raise SyntaxError("Unexpected number of brackets in type (%s): %d" % (dtype_string, dep_open_count))

        if dep_open_count == 1:
            dt_string, list_ref = dtype_string.split(gen_util.sym_dependency_open)
            return dt_string, list_ref[:-1]

        return dtype_string, None

    @staticmethod
    def split_endianness_from_dtype_string(dtype_string):
        ''' Split the endianness character from the data type string and resturn a tuple with the results '''
        first_char = dtype_string[0]
        if first_char in [gen_util.sym_big_endian, gen_util.sym_little_endian]:
            return dtype_string[1:], first_char
        return dtype_string, None

    # returns the size in bits, given that this is a native, non custom, data type
    def get_size_in_bits(self):
        ''' Get the size of this data type in bits '''
        if self.is_native_dtype():
            sz = int(self.main_type[1:])
        else:
            return -1

        return sz

    def can_generate_invalid_instance(self):
        ''' Can this DType generate an invalid instance'''
        if self.is_list:
            return True
        if self.is_struct:
            for member in self.struct_ref.members:
                if member.can_generate_invalid_instance():
                    return True
        return False

    def generate_invalid_value(self):
        ''' Generate an invalid value for this data type. '''

        ret_type = gen_util.INVALID_TYPE.VALID_VALUE

        # Handle generating an invalid list
        if self.is_list:
            generated_list = self.generate_valid_value().value

            if not isinstance(generated_list, list):
                raise ValueError("generate_valid_Value() for DType.is_list=True returned a \
non-list object: %s" % (str(generated_list.value)))

            # pick to either add or remove a value from the array
            # if the length is too small to remove a value, then force add one
            if len(generated_list) <= 1 or random.random() < .5:
                # generate a single element of the list's data type
                self.is_list = False
                new_val = self.generate_valid_value()
                self.is_list = True
                generated_list.append(new_val.value)
                ret_type = gen_util.INVALID_TYPE.HIGH_LIST_LENGTH
                ret_val = generated_list
            else:
                # remove the last element from the list
                generated_list = generated_list[:-1]
                ret_type = gen_util.INVALID_TYPE.LOW_LIST_LENGTH
                ret_val = generated_list[:-1]

            return GeneratedValue(ret_type, ret_val, self)

        raise NotImplementedError("No current way to generate an invalid DType \
where the DType is not a list")


    # returns a random number based on the definition of the dtype
    def generate_valid_value(self):
        ''' Generate a valid value for this data type.  Ex: 34 is a valid number for a uint8_t type (U8) '''
        def get_rng_float(upper_, lower_):
            rng = np.random.default_rng()
            return float("{:.4f}".format((upper_ - lower_) * rng.random((1,), np.float32)[0]))

        def get_rng_int(upper_, lower_):
            return random.randint(upper_, lower_)

        ret_val = None
        ret_type = gen_util.INVALID_TYPE.VALID_VALUE

        list_len = 0
        if self.is_list and not self.has_type_dependency:
            list_len = self.list_count
        elif self.has_type_dependency:
            if self.dependency.lower() not in gen_util.dependency_values:
                err_msg = "DType::generate_valid_value() - Dependency (%s) is not in list of dependency_value \
keys: %s.\n Did you mean to put '\"dependee\":\"True\"' in the Dependee's field?" % (self.dependency, \
gen_util.dependency_values.keys())
                raise Exception(err_msg)
            try:
                list_len = int(gen_util.dependency_values[self.dependency.lower()])
            except:
                err_msg = "DType::generate_valid_value() - Cannot convert value (%s) to integer." % \
                            (gen_util.dependency_values[self.dependency])
                raise ValueError(err_msg)

        if self.is_float:
            upper = 10000
            lower = -10000
            if self.is_list:
                vals = []
                for _ in range(list_len):
                    vals.append(get_rng_float(upper, lower))
                ret_val = vals
            else:
                ret_val = get_rng_float(upper, lower)
        elif self.is_int:
            dtype_bounds = gen_util.get_bounds(self.get_size_in_bits(), self.signed)
            if self.is_list:
                vals = []
                for _ in range(list_len):
                    vals.append(get_rng_int(dtype_bounds[0], dtype_bounds[1]))
                ret_val = vals
            else:
                ret_val = get_rng_int(dtype_bounds[0], dtype_bounds[1])
                if self.dependee != '':
                    gen_util.dependency_values[self.dependee.lower()] = int(ret_val)
        else:
            err_msg = "DType::generate_valid_value() - Cannot create random value for non-int/non-float values."
            raise Exception(err_msg)

        if self.is_list and not isinstance(ret_val, list):
            raise ValueError("DType is a list of len=%d, but the GeneratedValue is not of type \
list: %s" % (list_len, ret_val))

        return GeneratedValue(ret_type, ret_val, self)
