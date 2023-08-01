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


''' FieldDef contains al of the necessary functions and classes which are responsbile for parsing and processing
lines of the specification files which represent a field in the message format'''

from src.utils.Value import ValueList, ValueChoice

class FieldDef:
    ''' FieldDef contains all of the functions and information necessary for defining a message field '''
    def __init__(self, name, value_def, dtype, line_num=None, strict=False):
        self.name = name
        self.value_def = value_def
        self.dtype = dtype
        self.line_num = line_num
        self.strict = strict
        self.check_valid()
        self.can_generate_invalid_value = self.can_generate_invalid_instance()
        self.custom_data = {}
        self.message_name = ''

    def __str__(self):
        return "%s %s %s" % (self.name, self.value_def, self.dtype)

    def print_error(self, use_line_num=False):
        '''Use the information in this class to return a formatted string that the error message can use'''
        if use_line_num and self.line_num is not None:
            return "[%d] %s %s %s" % (self.line_num, self.name, self.value_def, self.dtype)
        return str(self)

    def check_valid(self):
        ''' Determine if the field is valid given the following checks:
            - dtype matches value_def (a U8 DType cannot have a list as the value)
            - dtype size matches value_def size (a U8 cannot have a value of 512)
            - dtype's dependency already is defined '''
        def in_bounds(value):
            if isinstance(value, float):
                return True

            min_bound, max_bound = self.dtype.bounds
            if min_bound <= value <= max_bound:
                return True

            return False

        if self.value_def.value is not None:
            # check to make sure that the values match the data type size (if native)
            for value in self.value_def.value.get_all_single_values():
                if self.dtype.is_int:
                    value = int(value.value)
                elif self.dtype.is_float:
                    value = float(value.value)
                # returns -1 if custom data type
                size = self.dtype.get_size_in_bits()
                if size != -1 and not in_bounds(value):
                    err_msg = "FieldDef - Value (%s) is not valid for the specified data type (%s)" % \
                                        (value, self.dtype)
                    raise ValueError(err_msg)

            types_list = self.value_def.value.get_all_types()
            if self.dtype.is_list:
                # if dtype is a list, the value_def should be of type ValueList or a choice of lists
                if isinstance(self.value_def.value, ValueChoice):
                    for item in self.value_def.value.contents:
                        if not isinstance(item, ValueList):
                            raise SyntaxError("Fields with dependencies must have values defined by lists.\
\n\t\tUsage: NAME,[ITEM,ITEM],BASE_TYPE[2]\n\t\t       NAME,[ITEM,ITEM]|[ITEM,ITEM],BASE_TYPE[2]\n\t%s" % \
                                                    self.print_error(True))
                        # if it is a list, it sould have dtype.list_count or less items in it
                        if len(item.contents) > self.dtype.list_count:
                            raise SyntaxError("Cannot have more items in the value list than specified in \
the type definition.\n\t\tNu of items in list: %d     Size of list: %d\n\t%s" % \
                                                    (len(self.value_def.value.contents),
                                                     self.dtype.list_count,
                                                     self.print_error(True)))
                # if dtype is a list, and the value is not a choice, the value needs to be a ValueList
                if not isinstance(self.value_def.value, ValueList):
                    err_msg = "FieldDef - Fields with dependencies must have values defined by lists.\n\t\tUsage: \
NAME,[ITEM,ITEM],BASE_TYPE[2]\n\t\t       NAME,[ITEM,ITEM]|[ITEM,ITEM],BASE_TYPE[2]\n\t%s" % self.print_error(True)
                    raise SyntaxError(err_msg)
                if len(self.value_def.value.contents) > self.dtype.list_count:
                    err_msg = "FieldDef - Cannot have more items in the value list than specified in the type \
definition.\n\tNumber of items in list: %d     Size of list: %d\n\t%s" % \
                                (len(self.value_def.value.contents),
                                 self.dtype.list_count,
                                 self.print_error(True))
                    raise SyntaxError(err_msg)

            # if dtype is not a list, there should be no lists in the value object
            elif ValueList in types_list:
                err_msg = "FieldDef - A field without a dependency cannot have a list in the value \
definition.\n\t%s" % self.print_error(True)
                raise SyntaxError(err_msg)

            # if value is a valueList, then the dtype should be a list
            if isinstance(self.value_def.value, ValueList) and not (self.dtype.is_list or self.dtype.dependency == ''):
                err_msg = "FieldDef - Value definition contains a list, but the data type is not supplied with a \
dependency.\n\t%s" % self.print_error(True)
                raise SyntaxError(err_msg)

    def can_generate_invalid_instance(self):
        ''' Determine if this FieldDef can generate an invalid instance given its properties '''
        if self.strict:
            return False
        # if there isn't a value, use the dtype to determne if its possible
        if self.value_def.value is None:
            return self.dtype.can_generate_invalid_instance()
        # if there is a value, check the bounds of the value...
        return self.value_def.can_generate_invalid_instance()

    def generate_valid_value(self):
        ''' Generate a value value for this field '''
        if self.value_def.value is not None:
            generated_value = self.value_def.generate_valid_value()
            generated_value.set_field(self)
            return generated_value
        generated_value = self.dtype.generate_valid_value()
        generated_value.set_field(self)
        return generated_value

    def generate_invalid_value(self):
        ''' Generate an invalid value for this field '''
        if self.value_def.value is not None:
            return self.value_def.generate_invalid_value()
        if self.dtype.can_generate_invalid_instance():
            return self.dtype.generate_invalid_value()
        return self.dtype.generate_valid_value()
