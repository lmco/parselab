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


''' Value.py contains all of the classes and functions which process and store information about
the value defined by the ValueDef class

Value vs ValueDef:
    Value:
        A value is a way to define constraints for how the parser should parse a given set of bytes.

        This value might be a single value such as '5' which would tell the parser that for that field,
        the bytes that represent it must be equal to 5.

        This value might instead be a list value such as [0x3, 0x105, 0x391] which would mean that the
        parser must parse the bytes for the list field as 0x3 followed by 0x105, followed by 0x391.

    ValueDef:
        A ValueDef is a way to contain the information that was passed into the parseLab framework through
        the protocol/mission specifation formats.  The ValueDef has the original line that was parsed
        to generate the information about the value, the data type that is used to represent the value,
        along with meta information that persists across value definitions in the specification file.

        The ValueDef is also responsible for holding the particular `Value` type (ValueSingle, ValueRange,
        ValueList, ValueChoice) for its respective field definition.
'''

import itertools
import random
import numpy as np

from src.utils.GeneratedValue import GeneratedValue
from src.utils import gen_util

# Umbrella term to categorize the different ValueTypes
class Value:
    ''' Value is an abstract class which is used to hold properties and functions which are
    used by all of the Value Types '''
    empty = True

class ValueList(Value):
    ''' ValueList holds the different ValueType objects that the field definition uses to denote an ordered list '''
    def __init__(self, values_string, dtype):
        self.dtype = dtype
        self.contents = self.parse_list_string(values_string)
        if self.contents is not None:
            self.empty = False

    def __str__(self):
        print_str = 'LIST('
        for item in self.contents:
            print_str += '%s, ' % str(item)
        return print_str[:-2] + ')'

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        if not self.dtype == other.dtype:
            return False
        if not len(self.contents) == len(other.contents):
            return False

        self_sorted_contents = sorted(self.contents)
        other_sorted_contents = sorted(other.contents)

        for i in range(len(self_sorted_contents)):
            if not self_sorted_contents[i] == other_sorted_contents[i]:
                return False
        return True

    def __hash__(self):
        return hash(tuple(sorted(self.contents) + [self.dtype]))

    def __lt__(self, other):
        for i in range(len(self.contents)):
            # If other list does not have this index, it is smaller, return False
            if i > len(other.contents):
                return False
            if self.contents[i] == other.contents[i]:
                continue
            # True if this element is not equal, but self is smaller
            # False if this elemenet is not equal, but self is larger
            return self.contents[i] < other.contents[i]
        # To get here means that other.contents is longer than self.contents but all items were equal
        #  up until the end of self, so take the longer list as greater than
        return False

    def get_all_single_values(self):
        ''' Iterate over the items in the list and recurse into them to determine all of the ValueSingle components
        that make up this list '''
        values_list = []
        if not self.empty:
            for item in self.contents:
                values_list.extend(item.get_all_single_values())

        return values_list

    def get_all_types(self):
        ''' Get all of the types that are contained in this list, along with the types that are contained in each
        element '''
        types_list = [type(self)]
        if not self.empty:
            for item in self.contents:
                types_list.extend(item.get_all_types())

        return types_list

    def parse_list_string(self, values_string):
        ''' Given a string that represnts a list, parse out the information and create a ValueList '''
        def parse_segment(segment):
            # parse the segment to determine what type of value that it is
            parsed_segment = None
            try:
                parsed_segment = ValueChoice(segment, self.dtype)
            except SyntaxError:
                pass
            except ValueError:
                pass

            if parsed_segment.empty:
                try:
                    parsed_segment = ValueRange(segment, self.dtype)
                except SyntaxError:
                    pass
                except ValueError:
                    pass

            if parsed_segment.empty:
                try:
                    parsed_segment = ValueSingle(segment, self.dtype)
                except SyntaxError:
                    pass
                except ValueError:
                    pass

            if parsed_segment.empty:
                err_msg = "ValueList - Unexpected Error: ValueList() - Unable to parse a section of the \
value field\n\t%s\n\tDid you use the wrong data type (%s) for this list?" % (values_string, self.dtype)
                raise SyntaxError(err_msg)

            return parsed_segment

        is_list = True
        if gen_util.sym_string in values_string and \
           values_string[0] == gen_util.sym_string and \
           values_string[-1] == gen_util.sym_string:
            is_list = False

        if is_list and (values_string[0] != gen_util.sym_list_open or values_string[-1] != gen_util.sym_list_close):
            return None

        #strip the brackets which bookend the list string
        values_string = values_string[1:-1]
        in_a_range = False
        in_a_string = False
        list_items = []
        curr_segment = ''
        segment_list = []

        for i, c in enumerate(values_string):
            curr_segment += c
            if c == gen_util.sym_list_open:
                err_msg = "ValueList - Cannot have nested list statements.\n\t%s%s" % \
                                (values_string, gen_util.carrot(i, '\n\t'))
                raise SyntaxError(err_msg)
            if c == gen_util.sym_list_close:
                err_msg = "ValueList - Unexpected termination of list statement\n\t%s%s" % \
                                (values_string, gen_util.carrot(i, '\n\t'))
                raise SyntaxError(err_msg)
            if c == gen_util.sym_range_open:
                if in_a_range:
                    err_msg = "ValueList - Cannot have nested range statements.\n\t%s%s" % \
                                (values_string, gen_util.carrot(i, '\n\t'))
                    raise SyntaxError(err_msg)
                in_a_range = True
                continue
            if c == gen_util.sym_range_close:
                if in_a_range:
                    in_a_range = False
                    continue
                err_msg = "ValueList - Unexpected termination of range statement\n\t%s%s" % \
                            (values_string, gen_util.carrot(i, '\n\t'))
                raise SyntaxError(err_msg)

            if c == gen_util.sym_delimiter:
                if is_list and not in_a_range:
                    segment_list.append(curr_segment[:-1].strip())
                    curr_segment = ''

        if in_a_string:
            raise SyntaxError("Missing trailing ' character in character element definition\n\t%s" % \
                    (values_string))

        if is_list:
            segment_list.append(curr_segment.strip())
        else:
            segment_list = list(curr_segment)
        for segment in segment_list:
            list_items.append(parse_segment(segment))

        return list_items

    def generate_name(self):
        ''' Generate a name for the parse rule that represents this list '''
        name = 'LIST__'
        for item in self.contents:
            name += item.generate_name() + '__'
        name = name[:-2]

        return name

    def generate_valid_value(self):
        ''' Generate a value value for this ValueList '''
        values = []
        for pdef in self.contents:
            try:
                valid_element = pdef.generate_valid_value().value
                values.append(valid_element)
            except:
                err_msg = "ValueList::generate_valid_value() - Aborting. Unable to generate a random value \
for parser definition: %s" % str(pdef)
                raise Exception(err_msg)
        return GeneratedValue(gen_util.INVALID_TYPE.VALID_VALUE, values, self.dtype)

    def can_generate_invalid_instance(self):
        ''' Determine if this list can generate an invalid instance '''
        return True

    def generate_invalid_value(self):
        ''' Generate an invalid value for this ValueList '''
        value_type = gen_util.INVALID_TYPE.VALID_VALUE
        ret_val = None

        ## ATTEMPT 1
        # Iterate over all the contents and see if any can be invalidated
        invalidable = list()
        for value in self.contents:
            if value.can_generate_invalid_instance():
                invalidable.append(value)

        num_invalidable = len(invalidable)
        if num_invalidable > 0:
            value_type = gen_util.INVALID_TYPE.INVALID_VALUE
            invalid_opt = invalidable[random.randint(0, num_invalidable-1)]
            generated_value = invalid_opt.generate_invalid_value()
            return generated_value

        ## ATTEMPT 2
        # Make the number of items not match the expected length
        values = list()
        for element in self.contents:
            values.append(element.generate_valid_value().value)

        if len(self.contents) < 1 or random.random() < .5:
            # if length is 0, we always will have to add an item because we
            #   cant remove the last instance of a 0 length array
            value_type = gen_util.INVALID_TYPE.HIGH_LIST_LENGTH
            self.dtype.is_list = False
            # Add a random value in the possible DType boundries
            values.append(self.dtype.generate_valid_value().value)
            self.dtype.is_list = True
            ret_val = values
        else:
            # Remove the last instance of the array
            value_type = gen_util.INVALID_TYPE.LOW_LIST_LENGTH
            ret_val = values[:-1]

        return GeneratedValue(value_type, ret_val, self.dtype)

class ValueChoice(Value):
    ''' ValueChoice contains all of the necessary properties and functions to define a value type which is
    made up of a set of other Value Types that the parser can choose from to determine the parse result '''
    def __init__(self, values_string, dtype):
        self.dtype = dtype
        self.contents = self.parse_choice_string(values_string)
        if self.contents is not None:
            self.empty = False
            self.check_valid()

    def __str__(self):
        print_str = 'OR('
        for item in self.contents:
            print_str += '%s, ' % str(item)
        return print_str[:-2] + ')'

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        if not self.dtype == other.dtype:
            return False
        if not len(self.contents) == len(other.contents):
            return False

        self_sorted_contents = sorted(self.contents)
        other_sorted_contents = sorted(other.contents)
        for i in range(len(self.contents)):
            if self_sorted_contents[i] != other_sorted_contents[i]:
                return False

        return True

    def __hash__(self):
        return hash(tuple(sorted(self.contents) + [self.dtype]))

    def __lt__(self, other):
        self_sorted_contents = sorted(self.contents)
        other_sorted_contents = sorted(other.contents)
        for i in range(len(self.contents)):
            # If other list does not have this index, it is smaller, return False
            if i > len(other.contents):
                return False
            if self_sorted_contents[i] == other_sorted_contents[i]:
                continue
            # If self at this index is smaller, return True
            # If self at this index is greater, return False
            return self_sorted_contents[i] < other_sorted_contents[i]
        # To get here means that other.contents is longer than self.contents but all items were equal
        #  up until the end of self, so take the longer list as greater than
        return False


    def get_all_single_values(self):
        ''' Get all of the `ValueSingle`s which recusively make up this ValueChoice '''
        values_list = []
        if not self.empty:
            for item in self.contents:
                values_list.extend(item.get_all_single_values())

        return values_list

    def get_all_types(self):
        ''' Get all of the types which recursively make up this ValueChoice '''
        types_list = [type(self)]
        if not self.empty:
            for item in self.contents:
                types_list.extend(item.get_all_types())

        return types_list

    def parse_choice_string(self, values_string):
        ''' Given a string, parse out the information to create a ValueChoice '''
        def parse_segment(segment):
            # parse the segment to determine what type of value that it is
            parsed_segment = None
            try:
                parsed_segment = ValueList(segment, self.dtype)
            except SyntaxError:
                pass
            except ValueError:
                pass

            if parsed_segment.empty:
                try:
                    parsed_segment = ValueRange(segment, self.dtype)
                except SyntaxError:
                    pass
                except ValueError:
                    pass

            if parsed_segment.empty:
                try:
                    parsed_segment = ValueSingle(segment, self.dtype)
                except SyntaxError:
                    pass
                except ValueError:
                    pass

            if parsed_segment.empty:
                err_msg = "ValueChoice - Unexpected Error: ValueChoice() - Unable to parse a section \
of the value field\n\t%s" % values_string
                raise SyntaxError(err_msg)

            return parsed_segment

        if gen_util.sym_choice not in values_string:
            return None

        in_a_list = False
        in_a_range = False
        curr_segment = ''
        segment_list = []
        choice_set = set()

        for i, c in enumerate(values_string):
            curr_segment += c
            if c == gen_util.sym_list_close:
                if in_a_list:
                    in_a_list = False
                    continue
                err_msg = "ValueChoice - Unexpected termination of list statement.\n\t%s%s" % \
                                (values_string, gen_util.carrot(i, '\n\t'))
                raise SyntaxError(err_msg)
            if c == gen_util.sym_list_open:
                if in_a_list:
                    err_msg = "ValueChoice - Cannot have nested list statments.\n\t%s%s" % \
                                    (values_string, gen_util.carrot(i, '\n\t'))
                    raise SyntaxError(err_msg)
                in_a_list = True
                continue
            if c == gen_util.sym_range_open:
                if in_a_range:
                    err_msg = "ValueChoice - Cannot have nested range statements.\n\t%s%s" % \
                                    (values_string, gen_util.carrot(i, '\n\t'))
                    raise SyntaxError(err_msg)
                in_a_range = True
                continue
            if c == gen_util.sym_range_close:
                if in_a_range:
                    in_a_range = False
                    continue
                err_msg = "ValueChoice - Unexpected termination of a range statement.\n\t%s%s" % \
                                (values_string, gen_util.carrot(i, '\n\t'))
                raise SyntaxError(err_msg)

            if c == gen_util.sym_choice:
                if values_string[i+1] == gen_util.sym_choice:
                    err_msg = "ValueChoice - Cannot have two choice symbols (%s) next to each other.\n\t%s%s" % \
                                    (gen_util.sym_choice, values_string, gen_util.carrot(i, '\n\t'))
                    raise SyntaxError(err_msg)
                if not in_a_list:
                    segment_list.append(curr_segment[:-1])
                    curr_segment = ''

        if len(segment_list) == 0:
            return None

        segment_list.append(curr_segment)
        for segment in segment_list:
            choice = parse_segment(segment)
            choice_set.add(choice)

        if isinstance(list(choice_set)[0], ValueRange):
            choice_set = set(ValueRange.combine_values(list(choice_set)))
        return sorted(list(choice_set))

    def generate_name(self):
        ''' Generate a name for the name of the parse rule which defines this ValueChoice '''
        name = 'CHOICE__'
        for item in self.contents:
            name += item.generate_name() + '__'

        name = name[:-2]
        return name

    def generate_valid_value(self):
        ''' Generate a valid value for this ValueChoice '''
        # pick one of the definitions in the choice options list and generate a random value for it
        opt = self.contents[random.randrange(len(self.contents)) - 1]

        try:
            return opt.generate_valid_value()
        except ValueError as e:
            err_msg = "ValueChoice::generate_valid_value() - Aborting. Unable to generate random value \
for parser definition: %s\n%s" % (str(opt), e)
            raise ValueError(err_msg)

    def generate_invalid_value(self):
        ''' Generate an invalid value for this ValueChoice '''

        choice_0 = self.contents[0]
        ret_type = gen_util.INVALID_TYPE.INVALID_VALUE

        if isinstance(choice_0, ValueSingle):
            ret_val = ValueSingle.generate_number_not_in_set(set(self.contents))
        elif isinstance(choice_0, ValueRange):
            ret_val = ValueRange.generate_number_not_in_set(set(self.contents))
        elif isinstance(choice_0, ValueList):
            ret_val = self.contents[random.randint(0, len(self.contents)-1)]
            ret_val = ret_val.generate_invalid_value()
        elif isinstance(choice_0, ValueChoice):
            raise Exception("Cannot have nested ValueChoice definitions")
        else:
            raise Exception("Unexpected codepath, choice type: %s" % type(choice_0))

        return GeneratedValue(ret_type, ret_val, self.dtype)

    def check_valid(self):
        ''' Is the list of possible values a valid set of options '''
        if len(self.contents) < 1:
            err_msg = "ValueChoice::check_valid() - The choice operator must not be empty"
            raise Exception(err_msg)

        # check if all of the contents are of the same type
        first_type = type(self.contents[0])
        for item in self.contents:
            if not isinstance(item, first_type):
                err_msg = "ValueChoice::check_valid() - Value choice cannot be a set of different subtypes. \
All items in choice operator must be of the same type."
                raise Exception(err_msg)

    def can_generate_invalid_instance(self):
        ''' Can this ValueChoice generate an invalid value '''
        choice_type = type(self.contents[0])
        ret_val = True
        if choice_type == ValueSingle:
            if self.dtype.is_float:
                ret_val = True
            else:
                set_size = self.dtype.bounds[1] - self.dtype.bounds[0]

                if set_size == len(self.contents):
                    ret_val = False

        elif choice_type == ValueRange:
            combined_ranges = ValueRange.combine_values(self.contents)
            dtype_bounds = self.dtype.bounds
            if len(combined_ranges) == 1:
                main_range = combined_ranges[0]
                if main_range.min_bound.value == dtype_bounds[0] and main_range.max_bound.value == dtype_bounds[1]:
                    ret_val = False

        elif choice_type == ValueList:
            for item in self.contents:
                if not item.can_generate_invalid_instance():
                    ret_val = False
        else:
            raise Exception("Invalid code path; ValueChoice must be composed of ValueSingle, ValueRange, or ValueList \
elenents.")

        return ret_val

# ValueRange holds two ValueSingle items which denote a min and max range for the field
class ValueRange(Value):
    ''' ValueRange contains the necessary properties and functions for defining a Value Type which consists
    of two ValueSingles which represent the boundaries on a range of possible values for the parser to determine the
    parse result '''
    def __init__(self, values_string, dtype):
        self.dtype = dtype
        bounds = self.parse_range_string(values_string)
        if bounds is not None:
            self.min_bound = ValueSingle(bounds[0], dtype)
            self.max_bound = ValueSingle(bounds[1], dtype)

        if bounds is not None:
            self.empty = False

    def __str__(self):
        return 'RANGE(%s,%s)' % (str(self.min_bound.value), str(self.max_bound.value))

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return isinstance(other, type(self)) and \
                self.dtype == other.dtype and \
                self.min_bound == other.min_bound and \
                self.max_bound == other.max_bound

    def __hash__(self):
        return hash((self.min_bound, self.max_bound, self.dtype))

    def __lt__(self, other):
        return self.min_bound.value < other.min_bound.value

    @staticmethod
    def combine_ranges(r1, r2):
        ''' Given two ValueRange objects, attempt to combine them into one '''
        def in_range(a, r):
            if r.min_bound.value <= a <= r.max_bound.value:
                return True
            return False

        def under_range(a, r):
            if a < r.min_bound.value:
                return True
            return False

        def over_range(a, r):
            if a > r.max_bound.value:
                return True
            return False

        new_range = r1
        # if a is in (x,y)
        if in_range(r1.min_bound.value, r2):
            # b cannot be under_range

            # if b is in (x,y)
            if in_range(r1.max_bound.value, r2):
                new_range = r2

            # if b is above (x,y)
            if over_range(r1.max_bound.value, r2):
                new_range.max_bound = r1.max_bound
                new_range.min_bound = r2.min_bound

        # if a is under (x,y)
        if under_range(r1.min_bound.value, r2):
            # if b is under (x,y)
            if under_range(r1.max_bound.value, r2):
                #new_range = r2
                # if a and b are both under (x,y) then
                #  they are disjoint
                return None

            # if b is in (x,y)
            if in_range(r1.max_bound.value, r2):
                new_range.min_bound = r1.min_bound
                new_range.max_bound = r2.max_bound

            # if b is above(x,y)
            # new range = r1

        # if a is over (x,y)
        if over_range(r1.min_bound.value, r2):
            # if a is over the other range, then they are disjoint, return None
            return None

        return new_range

    @staticmethod
    def combine_values(val_list):
        ''' Given a list of values, attempt to combine any ranges that might be overlapping and could
        be simplified '''
        combined_ranges = val_list
        prev_len = -1

        # if the previous loop's length and the current length are the same, nothing happened
        #  during the last loop, it is now done
        while prev_len != len(combined_ranges):
            # Get all of the combinations of the current ranges
            range_combinations = list(itertools.combinations(combined_ranges, 2))

            # Iterate over all of the combinations and see if they combine
            for rc in range_combinations:
                combined = ValueRange.combine_ranges(rc[0], rc[1])
                if combined is not None:
                    combined_ranges.append(combined)
                    combined_ranges.remove(rc[0])
                    combined_ranges.remove(rc[1])

            # Store the existing length to compare for the next loop
            prev_len = len(combined_ranges)

        return list(set(combined_ranges))

    def get_all_single_values(self):
        ''' Since a ValueRange is composed of two ValueSingle values, return a list which contains ValueSingles
        represnting the lower and upper bound '''
        values_list = []
        if not self.empty:
            values_list.extend(self.min_bound.get_all_single_values())
            values_list.extend(self.max_bound.get_all_single_values())

        return values_list

    def get_all_types(self):
        ''' Get all of the types that represent the upper and lower bound Values '''
        types_list = [type(self)]
        if not self.empty:
            types_list.extend(self.min_bound.get_all_types())
            types_list.extend(self.max_bound.get_all_types())

        return types_list

    def parse_range_string(self, values_string):
        ''' Given a string, parse out the information necessary to populate this class with ValueRange information '''
        if gen_util.sym_range_open not in values_string or gen_util.sym_range_close not in values_string:
            return None
        if values_string[0] != gen_util.sym_range_open or values_string[-1] != gen_util.sym_range_close:
            return None

        if values_string.count(gen_util.sym_delimiter) > 1:
            second_delimiter_index = values_string.find(gen_util.sym_delimiter,
                                                        values_string.find(gen_util.sym_delimiter) + 1)
            err_msg = "ValueRange - Cannot have more than one range statement delimiters (%s) in a single range \
statement.\n\t%s%s" % (gen_util.sym_delimiter, values_string, gen_util.carrot(second_delimiter_index, '\n\t'))
            raise SyntaxError(err_msg)

        values_string = values_string[1:-1]
        curr_segment = ''
        range_item = []
        for i, c in enumerate(values_string):
            curr_segment += c
            if c in [gen_util.sym_range_open, gen_util.sym_range_close]:
                err_msg = "ValueRange - Cannot have nested range statements.\n\t%s%s" % \
                            (values_string, gen_util.carrot(i, '\n\t'))
                raise SyntaxError(err_msg)
            if c == gen_util.sym_choice:
                err_msg = "ValueRange - Cannot have a choice Statement in a range statement.\n\t%s%s" % \
                            (values_string, gen_util.carrot(i, '\n\t'))
                raise SyntaxError(err_msg)
            if c == gen_util.sym_delimiter:
                if curr_segment == '':
                    err_msg = "ValueRange - Unexpected range delimiter (%s) before declaring the minimum \
bound.\n\t%s%s" % (gen_util.sym_delimiter, values_string, gen_util.carrot(i, '\n\t'))
                    raise SyntaxError(err_msg)
                range_item.append(curr_segment[:-1])
                curr_segment = ''

        range_item.append(curr_segment)
        if curr_segment == '':
            err_msg = "ValueRange - Unexpected termination of range statement; maybe missing a upper \
bound.\n\t%s" % values_string
            raise SyntaxError(err_msg)

        if len(range_item) != 2:
            err_msg = "ValueRange - Unexpected Error - Too many arguments in range statement.\n\t%s" % \
                            values_string
            raise SyntaxError(err_msg)

        min_number = gen_util.string_to_number(range_item[0])
        if min_number is None:
            err_msg = "ValueRange - Lower bound of range (%s, %s) cannot be converted into a number" % \
                            (range_item[0], range_item[1])
            raise ValueError(err_msg)

        max_number = gen_util.string_to_number(range_item[1])
        if max_number is None:
            err_msg = "ValueRange - Upper bound of range (%s, %s) cannot be converted into a number" % \
                            (range_item[0], range_item[1])
            raise ValueError(err_msg)

        if min_number >= max_number:
            err_msg = "ValueRange - Lower bound (%s) for range must be less than the upper bound (%s)." % \
                            (range_item[0], range_item[1])
            raise ValueError(err_msg)

        return range_item

    def generate_name(self):
        ''' Generate a name for the parse rule that is generated for this ValueRange '''
        return 'RANGE__%s_%s' % (self.min_bound.value, self.max_bound.value)

    def generate_valid_value(self):
        ''' Generate a random value that fits between the lower and upper bounds of the range '''
        ret_val = 0
        rng = np.random.default_rng()
        if self.min_bound.value > self.max_bound.value:
            err_msg = "ValuesRange::generate_valid_value() - Aborting: lower bound (%d) is greater than upper \
bound (%d).  Returning value of 0" % (self.min_bound.value, self.max_bound.value)
            raise ValueError(err_msg)

        if self.dtype.is_float:
            ret_val = (self.max_bound.value - self.min_bound.value) * \
                      rng.random((1,), np.float32)[0] + \
                      self.min_bound.value
            ret_val = float("{:.4f}".format(ret_val))
        else:
            ret_val = random.randrange(self.min_bound.value, self.max_bound.value)

        return GeneratedValue(gen_util.INVALID_TYPE.VALID_VALUE, ret_val, self.dtype)

    def generate_invalid_value(self):
        ''' Generate a value that exists outside of the lower and upper bounds of the range '''
        def set_above_range():
            return gen_util.INVALID_TYPE.GREATER_THAN_BOUNDS, self.max_bound.value + 1

        def set_below_range():
            return gen_util.INVALID_TYPE.LESS_THAN_BOUNDS, self.min_bound.value - 1

        value_type = gen_util.INVALID_TYPE.VALID_VALUE
        ret_val = None
        _min, _max = gen_util.get_bounds(self.dtype.get_size_in_bits(), self.dtype.signed)

        # if the min bound of the data type matches the min bound of the range,
        #  you can only create an invalid value ABOVE the range
        if self.min_bound.value == _min:
            mod_func = set_above_range
        # if the max bound of the data type matches the max bound of the range,
        #  you can only create an invalid value BELOW the range
        elif self.max_bound.value == _max:
            mod_func = set_below_range
        # if neither are the case, randomly pick one
        else:
            if random.random() < 0.5:
                mod_func = set_above_range
            else:
                mod_func = set_below_range

        value_type, ret_val = mod_func()

        return GeneratedValue(value_type, ret_val, self.dtype)

    def can_generate_invalid_instance(self):
        ''' Determine if this range has the ability to produce values outside of it '''
        dtype_bounds = self.dtype.bounds
        if self.min_bound.value == dtype_bounds[0] and self.max_bound.value == dtype_bounds[1]:
            return False
        return True

    @staticmethod
    def generate_number_not_in_set(range_set):
        '''If provided a set of ValueRange values, find a number that is not in the set of numbers bound
        by the set of ranges '''

        if len(range_set) < 2:
            raise Exception("Cannot generate number outside of set where number of \
elements are less than 2")

        # Pick a random index from the range_set and grab a value between the
        #  chosen range and the range[n+1]
        #       Since ranges will be combined: [x, n] [n, y] -> [x,y],
        #        it guarantees that there will be at least one value between
        #        ranges

        range_list = sorted(list(range_set))
        low_idx = random.randint(0, len(range_set)-2)
        low_range = range_list[low_idx]
        high_range = range_list[low_idx + 1]

        dtype = range_list[0].dtype

        if dtype.is_int:
            #randint is inclusive
            rand_func = random.randint
            _min = low_range.max_bound.value + 1
            _max = high_range.min_bound.value - 1
        elif dtype.is_float:
            rand_func = random.uniform
            _min = -100000
            _max = 100000

        return rand_func(_min, _max)

class ValueSingle(Value):
    ''' ValueSingle contains all of the properties and functions necessary for parsing and processing information
    about single values defined in the protocol/mission specification files '''
    def __init__(self, values_string, dtype):
        self.dtype = dtype
        self.value = self.parse_single_value(values_string)
        if self.value is not None:
            self.empty = False

    def __str__(self):
        if self.value is not None:
            return str(self.value)
        if self.dtype is not None:
            return str("Value does not exist; Dtype=%s" % str(self.dtype.dtype_string))
        return ''

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.value == other.value and self.dtype == other.dtype

    def __hash__(self):
        return hash((self.value, self.dtype.get_size_in_bits(), self.dtype.signed, self.dtype.is_float))

    def __lt__(self, other):
        return self.value < other.value

    def get_all_single_values(self):
        ''' Return a list that just contains this object '''
        return [self]

    def get_all_types(self):
        ''' Get a list of the types that are contained in the Value '''
        return [type(self)]

    def parse_single_value(self, values_string):
        ''' Given a string representing a value, parse it to determine if the string is a single value or not '''
        binary_num = False
        char_val = None

        # check for any symbols which would mean that it is not a ValueSingle
        for c in enumerate(values_string):
            if c in [gen_util.sym_list_open,
                     gen_util.sym_list_close,
                     gen_util.sym_range_open,
                     gen_util.sym_range_close,
                     gen_util.sym_choice]:
                return None

        if values_string[0] == gen_util.sym_string and values_string[0] == gen_util.sym_string:
            char_val = values_string[1:-1]
            if char_val == '':
                raise SyntaxError("Cannot have an empty character value")

        # handle the case where the user defines it as a hex or binary value
        if len(values_string) > 1 and values_string[0] == '0':
            type_char = values_string[1]
            if type_char in ['x', 'b']:
                binary_num = True

        # Convert string character into string number which can be processed like all other number inputs
        if len(values_string) == 1 and values_string.isalpha():
            values_string = str(ord(values_string))

        if char_val is not None:
            values_string = str(ord(char_val))

        if values_string != '':
            if self.dtype.is_int:
                if binary_num:
                    ret_val = gen_util.strnum_to_int(values_string, self.dtype.signed)
                else:
                    ret_val = int(values_string)
                return ret_val
            if self.dtype.is_float:
                if binary_num:
                    err_msg = "ValueSingle - Cannot use hex or binary representation to define a float field."
                    raise SyntaxError(err_msg)
                ret_val = float(values_string)
                return ret_val

            err_msg = "ValueSingle - Unexpected code path. Could not parse string (%s) for self: %s" % \
                        (values_string, str(self))
            raise Exception(err_msg)
        return None

    def generate_valid_value(self):
        ''' Generate a value based on the data type for this value '''
        return GeneratedValue(gen_util.INVALID_TYPE.VALID_VALUE, self.value, self.dtype)

    def generate_invalid_value(self):
        ''' Generate an invalid value based on the data type for this value '''
        value_type = gen_util.INVALID_TYPE.INVALID_VALUE

        # get a random value that fits in this data type
        #  NOTE: This is a little cheaty, it creates up to 10 valid values,
        #   and checks to see if the valid value (valid for this data type)
        #   DOES NOT match the expected value, and if thats the case,
        #   an invalid value was generated
        self.dtype.is_list = False
        invalid_data = self.dtype.generate_valid_value().value
        cnt = 0
        if invalid_data == self.value:
            while invalid_data == self.value and cnt < 10:
                invalid_data = self.dtype.generate_valid_value().value
                cnt += 1
        self.dtype.is_list = True

        if invalid_data == self.value:
            value_type = gen_util.INVALID_TYPE.VALID_VALUE

        return GeneratedValue(value_type, invalid_data, self.dtype)

    def generate_name(self):
        ''' Generate a name for this value '''
        return '%s' % self.value

    def can_generate_invalid_instance(self):
        ''' Can this value generate an invalid instance?'''
        return True

    @staticmethod
    def generate_number_not_in_set(value_single_set):
        ''' Generate a random number not in the provided set of ValueSingles'''
        dtype = list(value_single_set)[0].dtype
        dtype_bounds = gen_util.get_bounds(dtype.get_size_in_bits(), dtype.signed)
        if len(value_single_set) == (dtype_bounds[1] - dtype_bounds[0]):
            raise Exception("The set contains all values in the bounds defined by the\
data type; cannot generate a number outside of the provided set")
        values_list = list()
        for i in value_single_set:
            values_list.append(i.value)

        # Brute force pick random floats, VERY low chance for infinite collisions
        if dtype.is_float:
            # arbitrary range boundries
            min_bound = -1000000
            max_bound = 1000000
            ret = random.uniform(min_bound, max_bound)
            while ret in values_list:
                ret = random.uniform(min_bound, max_bound)
            return ret

        # Pick a random number within the bounds of the data type
        #   if this value is not one of the ones in the values set, youre good
        #   if this value IS one of the values in the values set, begin to do
        #      an incremental search outwards from the random value
        #           Meaning if you pick 15 and the set is [10,50), the algo will
        #           increment by 1 and check 16, then see 16 is also in the set,
        #           so it will then decrement by 2 and check 14, etc until
        #           getting to 9 and then returning 9

        base = random.randint(dtype_bounds[0], dtype_bounds[1])
        offset = 0
        while base + offset in values_list:
            sign = gen_util.sign(offset)
            offset = abs(offset) + 1
            offset *= sign

        return base + offset
