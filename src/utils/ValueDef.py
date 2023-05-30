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


''' ValueDef.py contains all of the necessary classes and functions for processing and storing information about
protocol field values defined in the protocol and mission specification formats'''

from src.utils.Value import ValueChoice, ValueList, ValueRange, ValueSingle
from src.utils import gen_util

class ValueDef:
    ''' ValueDef contains the properties and functions necessary for creating/parsing Value defined in the protocol
    and mission specification file '''
    def __init__(self, dtype, init_values=None, line_num=None):
        self.line_num = line_num
        self.dtype = dtype
        self.init_values = init_values
        if init_values is not None:
            self.interpret_values(init_values)
        else:
            self.value = None

    def __str__(self):
        if self.value is None:
            return "dtype: %s       value: %s" % (self.dtype, self.value)
        return str(self.value)

    def interpret_values(self, init_values):
        ''' parse a string and interpret the string as a value type '''
        if not isinstance(init_values, str):
            values_string = ','.join(init_values)
        else:
            values_string = init_values

        self.value_string = values_string

        value = ValueChoice(values_string, self.dtype)

        if value.empty:
            value = ValueList(values_string, self.dtype)

        if value.empty:
            value = ValueRange(values_string, self.dtype)

        if value.empty:
            value = ValueSingle(values_string, self.dtype)

        if value.empty:
            err_msg = "ValueDef - Unexpected Error - Unable to properly parse value portion of field \
definition.\n\t%s" % values_string
            #log_error(err_msg)
            raise Exception(err_msg)

        self.value = value

    def generate_valid_value(self):
        ''' Generate a valid tangible value for this value definition '''
        if self.dtype is None:
            err_msg = "ValueDef::generate_valid_value() - Unexpected: ValueDef (%s) does not have a \
DType associated to it." % str(self)
            raise Exception(err_msg)

        if self.value is not None:
            try:
                generated_value = self.value.generate_valid_value()
            except:
                err_msg = "ValueDef::generate_valid_value() - [line_%d] Unable to generate random \
value for field." % self.line_num
                raise Exception(err_msg)
        else:
            try:
                generated_value = self.dtype.generate_valid_value()
            except:
                err_msg = "ValueDef::generate_valid_value() - [line_%d] Unable to generate random \
value for field." % self.line_num
                raise Exception(err_msg)

        if self.dtype.dependee != '':
            gen_util.dependency_values[self.dtype.dependee.lower()] = generated_value.value

        return generated_value

    def generate_invalid_value(self):
        ''' Generate an invalid tangible value for this value defintion '''
        if self.dtype is None:
            err_msg = "ValueDef::generate_invalid_value() - Unexpected: ValueDef (%s) does not have a \
DType associated to it." % str(self)
            raise Exception(err_msg)

        if self.value is not None:
            try:
                generated_value = self.value.generate_invalid_value()
            except:
                err_msg = "ValueDef::generate_invalid_value() - [line_%d] Unable to generate random \
invalid value for field." % self.line_num
                raise Exception(err_msg)
        else:
            try:
                generated_value = self.dtype.generate_invalid_value()
            except:
                err_msg = "ValueDef::generate_invalid_value - [line_%d] Unable to generate random \
invalid value for field." % self.line_num
                raise Exception(err_msg)

        if self.dtype.dependee != '':
            gen_util.dependency_values[self.dtype.dependee.lower()] = generated_value.value

        return generated_value

    def can_generate_invalid_instance(self):
        ''' Determine if the value definition is possible to have an invalid value generated for it '''
        if self.value is None:
            return False
        return self.value.can_generate_invalid_instance()
