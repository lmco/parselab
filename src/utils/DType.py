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

# Class that holds information abnout the data type
#   such as the number of bits that are defined
#           if it is a list or not
#           what dependencies it has
class DType:
    ''' DType holds information about the data type component of a field in the
    protocol spec; information such as the number of bits that are defined. '''
    def __init__(self, dtype_string, dependee, field_name):
        self.signed = False
        self.is_int = False
        self.is_float = False
        self.is_list = False
        self.list_count = 0
        self.main_type = ''
        self.dependency = ''
        self.has_type_dependency = False
        self.is_big_endian = True
        self.dtype_string = dtype_string
        self.dependee = dependee
        self.field_name = field_name
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
        # dtype format:
        #   (req) SINGLE CHARACTER DEFINING TYPE
        #   (req) MULTIPLE CHARACTER DEFINING SIZE IN BITS
        #   (opt) BRACKET AROUND INTEGER DEFINING LENGTH OF LIST
        curr_segment = ''
        in_dependency_block = False

        if dtype_string[0] == gen_util.sym_little_endian or dtype_string[0] == gen_util.sym_big_endian:
            if dtype_string[0] == gen_util.sym_little_endian:
                self.is_big_endian = False

            dtype_string = dtype_string[1:]

        for i, c in enumerate(dtype_string):
            dep_str = ''.join([gen_util.sym_dependency_open, gen_util.sym_dependency_close, '_'])
            if not gen_util.adv_isalnum(c, dep_str):
                err_msg = "DType - Unexpected gen_util.symbol in field's data type section\n\t%s%s" % \
                            (dtype_string, gen_util.carrot(i, '\n\t'))
                raise SyntaxError(err_msg)

            curr_segment += c
            if c == gen_util.sym_dependency_open:
                if in_dependency_block:
                    err_msg = "DType - Cannot have nested dependencies.\n\t%s%s" % \
                                (dtype_string, gen_util.carrot(i, '\n\t'))
                    raise SyntaxError(err_msg)
                in_dependency_block = True
                if len(curr_segment) > 0:
                    self.main_type = curr_segment[:-1]
                    curr_segment = ''
                else:
                    err_msg = "DType - Cannot declare a dependency without a main type.  \
Usage: NAME,VALUIN_TYPE[DEPENDENCY]\n\t%s%s" % (dtype_string, gen_util.carrot(i, '\n\t'))
                    raise SyntaxError(err_msg)
                continue
            if c == gen_util.sym_dependency_close:
                if not in_dependency_block:
                    err_msg = "DType - Unexpected termination of dependency.\n\t%s%s" % \
                                (dtype_string, gen_util.carrot(i, '\n\t'))
                    #self.log.error(err_msg)
                    raise SyntaxError(err_msg)
                in_dependency_block = False
                if len(curr_segment) > 0:
                    self.dependency = curr_segment[:-1]
                    curr_segment = ''
                else:
                    err_msg = "DType - Cannot declare an empty dependency.  \
Usage: NAME,VALUIN_TYPE[DEPENDENCY]\n\t%s%s" % (dtype_string, gen_util.carrot(i, '\n\t'))
                    #self.log.error(err_msg)
                    raise SyntaxError(err_msg)
                continue

        if in_dependency_block:
            err_msg = "DType - Reached end of dependency definition without a dependency definition \
terminating character (%s)\n\t%s" % (gen_util.sym_dependency_close, dtype_string)
            raise SyntaxError(err_msg)
        if self.main_type == '':
            if curr_segment == '':
                err_msg = "DType - Reached end of field type definition without declaring a type.\n\t%s" % \
                            (dtype_string)
                raise SyntaxError(err_msg)
            self.main_type = curr_segment

        if self.dependency not in (None, ''):
            try:
                int_dependency = int(self.dependency)
                if int_dependency == 0:
                    err_msg = "DType - Cannot have a 0-value dependency field.\n\t%s" % dtype_string
                    raise ValueError(err_msg)
                self.list_count = int_dependency
                self.is_list = True
            except ValueError:
                if (self.dependency[0].isalpha() or self.dependency[0] == '_') and \
                        gen_util.adv_isalnum(self.dependency, '_'):
                    self.has_type_dependency = True
                    self.is_list = True
                else:
                    err_msg = "DType - Dependency has invalid name (%s).  First charcter must be alphabetical \
or an underscore, and entire string must be alphanumeric (underscores allowed)" % self.dependency
                    raise ValueError(err_msg)

        if self.dependee != '' and self.is_native_dtype() and not self.is_int:
            err_msg = "DType- (%s) Cannot be a dependee without being of an integer type." % self.dtype_string
            raise Exception(err_msg)

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
