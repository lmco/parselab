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


''' gen_util.py is a catch-all file which contains information that needs to be leveraged
repeatedly throughout the parseLab framework '''

from enum import Enum
import math
import os
import random
import shutil
import struct
import time
from bitstring import BitArray

## important symbols for parsing protocol and mission specification
PARSELAB_TOP = os.path.join('/home', 'parsival', 'parselab')
pwd = os.path.abspath(os.path.dirname(__file__))
PARSELAB_TOP = os.path.abspath(os.path.join(pwd, '../../'))
SRC_DIR = os.path.join(PARSELAB_TOP, 'src')
SRC_DATA_DIR = os.path.join(SRC_DIR, 'data')
GENERATORS_DIR = os.path.join(PARSELAB_TOP, 'generators')
DATA_DIR = os.path.join(PARSELAB_TOP, 'data')
STUBS_DIR = os.path.join(DATA_DIR, 'stub_files')

# general modes
debug_mode = False
print_log_info = False

# util files
generated_code_header_filename = "GeneratedCodeHeader.txt"
generated_code_header_file = os.path.join(STUBS_DIR, generated_code_header_filename)

# spec files
protocol_spec_filename = 'protocol.json'
mission_spec_filename = 'mission.json'
mission_states_dirname = 'mission'
mission_states_transition_filename = 'transitions.txt'
mission_states_ext = 'spec'

# json spec keys
mission_types_k = "mission_types"
protocol_types_k = "protocol_types"
name_k = "name"
msg_spec_name_k = "msg_name"
fields_k = "fields"
field_spec_name_k = "field_name"
field_value_k = "value"
field_type_k = "type"
field_dependee_k = "dependee"
field_dependency_k = "dependency"
ignore_k = 'ignore'
strict_k = 'strict'

# testcase info
testcase_dirname = 'testcases'
results_filename = 'results.txt'
test_message_extension = '.bin'

colors = {
    'Reset' : '\033[0;0m',
    'Red' : '\033[0;31m',
    'Green' : '\033[0;32m',
    'Yellow' : '\033[0;33m',
}

# unit test info
unit_tests_dirname = 'unit_tests'
TEST_PASS = 0
TEST_FAIL = 1
TEST_EXCEPT = 2

# general
sym_ignore = '#'
sym_directive = '%'

# type info
sym_mtype = '='
sym_field = ' '
sym_endfield = '\n'

# name info
sym_dependee = '@'

# value info
sym_choice = '|'
sym_range_open = '('
sym_range_close = ')'
sym_list_open = '['
sym_list_close = ']'
sym_delimiter = ','
sym_string = "'"
sym_escape = '\\'

# dtype info
sym_dependency_open = '['
sym_dependency_close = ']'
sym_native_unsigned = 'U'
sym_native_signed = 'I'
sym_native_float = 'F'
sym_native_double = 'D'
sym_little_endian = '<'
sym_big_endian = '>'
sym_native_types = [sym_native_signed, sym_native_unsigned, sym_native_float, sym_native_double]
native_float_size = 32

# dictionary of dependencies and their values
dependency_values = {}

# types of invalid value
class INVALID_TYPE(Enum):
    ''' Enmerated values representing the types of way that a generated value can be invalid (or valid) '''
    VALID_VALUE = 0             # An invalid value was not possible
    INVALID_VALUE = 1           # Generic definition for invalid value
    GREATER_THAN_BOUNDS = 2     # The generated value was above the specified bounds
    LESS_THAN_BOUNDS = 3        # The generated value was below the specified bounds
    SWAP_LIST_ITEMS = 4         # Two items in an otherwise valid generated list were swapped
    LOW_LIST_LENGTH = 5         # There are one too few items in the generated list
    HIGH_LIST_LENGTH = 6        # There are one too many items in the generated list


def copy_directory_to_tmp(source_dir):
    ''' Using shutil, copy a directory (source_dir) to tmp '''
    dirname = os.path.basename(source_dir)
    dirname_time = dirname + '_' + str(int(time.time()))
    tmp_dir = os.path.join('/tmp', dirname_time)

    if os.path.isdir(tmp_dir):
        shutil.rmtree(tmp_dir)

    shutil.copytree(source_dir, tmp_dir)

def create_setup_dir_structure(data_dir, dirpath, setup_dirname, ignore_parselab_data=False):
    ''' Instantate a setup directory with the base structure for the respective parseLab generator
    data_dir:               path to directory which contains the directory structure for this generator's setup info
    dirpath:                path to the protocol directory that the setup directory will be placed into
    setup_dirname:          name of the newly created setup directory in the protocol directory
    ignore_parselab_data:   should the mission/json/readme files be copied into the new setup directory
    '''

    # create the new dirpath
    if not os.path.exists(dirpath):
        os.mkdir(dirpath)

    if setup_dirname:
        # get the path for where to put necessary setup data for the target module
        setup_dirpath = os.path.join(dirpath, setup_dirname)

        # delete it if one already exists in the target path
        if os.path.isdir(setup_dirpath):
            shutil.rmtree(setup_dirpath)
        # move the base setup data into this new target
        shutil.copytree(data_dir, setup_dirpath)

    if ignore_parselab_data:
        return

    files = [f for f in os.listdir(SRC_DATA_DIR) if os.path.isfile(os.path.join(SRC_DATA_DIR, f)) \
                                                 and os.path.splitext(f)[1] != '.swp']

    for f in files:
        new_file_path = os.path.join(dirpath, f)
        if not os.path.isfile(new_file_path):
            shutil.copy(os.path.join(SRC_DATA_DIR, f), dirpath)

def get_mission_spec(protocol_dir):
    ''' Get the mission specification file out of the supplied protocol directory '''
    mission_spec = os.path.join(protocol_dir, mission_spec_filename)
    if not os.path.isfile(mission_spec):
        return None
    return mission_spec

def get_protocol_spec(protocol_dir):
    ''' Get the protocol specification file out of the supplied protocol directory '''
    protocol_spec = os.path.join(protocol_dir, protocol_spec_filename)
    if not os.path.isfile(protocol_spec):
        return None

    return protocol_spec

def convert_int_to_hex_str(value, size):
    ''' given an integer value, convert it into a hex string '''
    u_int = (size // 8) * 2
    hex_val = format(value, '0' + str(u_int) + 'x')
    padded_hex = pad_hex_str(hex_val)
    return padded_hex

def pad_hex_str(hex_str):
    ''' given a hex string, drop the 0x and pad the string with appropriate 0s '''
    stripped_hex = hex_str.split('0x')[-1]
    lpad_count = len(stripped_hex)%2
    padded_hex = stripped_hex.rjust(lpad_count + len(stripped_hex), '0')
    return padded_hex

def adv_split(string, delimiter, opening=None, closing=None):
    ''' Split a string into a list based on a supplied delimiter with the ability to ignore the delimeter between
    supplied opening and closing characters
            string:         string to split
            delimieter:     character to split the string against
            opening:        string of characters to mark the start of a section to ignore the delimeter
            closing:        string of characters to mark the end of a section which ignored the delimeter'''
    # the delimiter must be a single character
    if len(delimiter) != 1:
        return None

    has_special_segment = False
    if opening is not None and closing is not None:
        has_special_segment = True

    split_list = []
    curr_segment = ''
    in_ignore = False

    for c in enumerate(string):
        if has_special_segment:
            if c in opening:
                in_ignore = True
            elif c in closing:
                in_ignore = False

        if not in_ignore and c == delimiter:
            split_list.append(curr_segment)
            curr_segment = ''
        else:
            curr_segment += c

    split_list.append(curr_segment)
    return split_list

def extract(string, opening, closing):
    ''' Extract a substring based on opening and closing characters - cannot handle nested objects
            string:     string to extract from
            opening:    character to mark the start of a section to extract
            closing:    character to mark the end of a section to extract

            return:     list of substrings as a result of the opening and closing characters'''
    sections = []
    curr_section = ''
    in_section = False

    for c in enumerate(string):
        if c == opening:
            if in_section:
                raise SyntaxError("Error: extract() - (%s) Nested objects cannot be handled with this function" % \
                                    (string))
            in_section = True
            curr_section += c
        elif c == closing:
            if not in_section:
                raise SyntaxError("Error: extract() - (%s) Closing character discovered before opening character" % \
                                    (string))
            in_section = False
            sections.append(curr_section)

    if not in_section:
        raise SyntaxError("Error: extract() - (%s) Closing character never found before end of string" % (string))

def carrot(index, prefix):
    ''' Create an error message's carrot pointer
            index:      how many characters to the right should the carrot be placed
            prefix:     how the line with the carrot should start - e.g. if the above string has a single space
                        before printing the string, the carrot line needs this as well'''
    return prefix + index*' ' + '^'

def adv_isalnum(string, allowed_characters=None):
    ''' determine if a string is alphanumeric or within a list of allowed characters '''
    if string.isalnum():
        return True
    if allowed_characters is not None:
        for c in string:
            if c.isalnum() or c in allowed_characters:
                continue
            return False
    return True

def get_bounds(size, signed):
    ''' Determine the upper and lower integer bounds given the number of bits and signedness of the object
         INCLUSIVE BOUNDS'''

    min_bound = None
    max_bound = None

    if signed:
        min_bound = -pow(2, size-1)
        max_bound = pow(2, size-1) - 1
    else:
        min_bound = 0
        max_bound = pow(2, size)-1

    return (min_bound, max_bound)

# s = source number
# m = multiple
def next_multiple(s, m):
    ''' determine the next multiple of `m` from `s`'''
    return m * ((s-1) // m) + m

def float2int(f):
    ''' Convert a float to int using the python struct lib '''
    i = struct.unpack('>I', struct.pack('>f', f))[0]
    return i

def serialize(vals):
    ''' Convert a list of values into a serialized list of bytes '''
    size = 0
    serial = 0

    for val in vals:
        dtype_size = val.dtype.get_size_in_bits()
        val_size = dtype_size
        val_serialized = 0
        tmp = None
        fmt, padding = create_struct_format(val, '>' if val.dtype.is_big_endian else '<')

        if val.dtype.is_float:
            if isinstance(val.value, float):
                val_serialized = float2int(val.value)
            elif isinstance(val.value, list):
                val_size = 0
                for v in val.value:
                    val_size += dtype_size
                    val_serialized = val_serialized << dtype_size
                    val_serialized |= float2int(v)
        elif val.dtype.is_int:
            if isinstance(val.value, int):
                if val.dtype.signed:
                    try:
                        val_serialized = struct.pack(fmt, val.value)
                    except struct.error as e:
                        print("Unable to pack value: %s into format: %s\n%s" % (str(val.value), fmt, e))
                        raise e
                else:
                    try:
                        val_serialized = struct.pack(fmt, val.value)
                    except struct.error as e:
                        print("Unable to pack value: %s into format: %s\n%s" % (str(val.value), fmt, e))
                        raise e
                if val.dtype.is_big_endian is False and dtype_size > 8 and dtype_size % 8 == 0:
                    val_serialized = struct.unpack(fmt, attempt_reverse_bytes(val_serialized, dtype_size))[0]
                else:
                    val_serialized = struct.unpack(fmt, val_serialized)[0]
            elif isinstance(val.value, list):
                val_size = 0
                if val.dtype.signed:
                    fmt = '<i'
                for v in val.value:
                    val_size += dtype_size
                    val_serialized = val_serialized << dtype_size
                    try:
                        tmp = struct.pack(fmt, v)
                    except Exception as e:
                        raise e
                    if dtype_size > 8 and dtype_size % 8 == 0:
                        serialized_value = struct.unpack(fmt, attempt_reverse_bytes(tmp, dtype_size))[0]
                    else:
                        serialized_value = struct.unpack(fmt, tmp)
                        serialized_value = serialized_value[0]
                    val_serialized |= serialized_value
            else:
                raise Exception("Integer DTypes must resolve to either a int or list type for their values!")

        if val_serialized < 0:
            val_serialized += (1 << val_size)
        if not val.dtype.is_big_endian:
            val_serialized = val_serialized >> padding
        size += val_size
        serial = serial << val_size
        serial |= val_serialized
    ## move the pad bits to the right size of the value
    extra_padding = size % 8
    serial = serial << extra_padding

    return (serial, size)

def deserialize(val, size):
    ''' Turn a value into a list of 8-bit integers
            val:        a large integer which represents the serialized data form the packet
            size:       the true number of bits which the serialized data needs.  Note, the serialized data is
                        of a size+padding where padding=(size % 8)'''
    size_of_octet = 8
    vals = []
    tmp = 0
    num_vals = math.ceil(size / size_of_octet)
    for _ in range(num_vals):
        tmp = val & 0xFF
        vals.insert(0, "{0:#0{1}x}".format(tmp, 4))
        val = val >> size_of_octet

    return vals

def deserialzed_string(vals):
    ''' Take a list of hex values ([0xFF, 0xEE, 0xDD, ...]) and concatenate them '''
    string = ""
    for val in vals:
        string += val[2:]

    return string

def attempt_reverse_bytes(value, size):
    ''' convert the vaule into a byte array, then reverse it, and return the value '''
    size = size / 8
    v = bytearray(value)
    v.reverse()
    v = bytes(v)
    return v

def create_struct_format(value, endian_sym):
    ''' Convert a parseLab value into the struct library formata string '''
    def get_next_octet_offset(size):
        if size % 8 == 0:
            return size
        return size + (8 - size % 8)

    fmt = ''
    sz = value.dtype.get_size_in_bits()
    pad = 0
    max_octet_offset = 0
    used_octet_offset = get_next_octet_offset(sz)

    if value.dtype.is_int:
        if sz == 1:
            fmt = '?'
            max_octet_offset = 8
        elif sz <= 8:
            fmt = 'b'
            max_octet_offset = 8
        elif sz <= 16:
            fmt = 'h'
            max_octet_offset = 16
        elif sz <= 32:
            fmt = 'i'
            max_octet_offset = 32
        else:
            fmt = 'q'
            max_octet_offset = 64

        if not value.dtype.signed:
            fmt = fmt.upper()

    elif value.dtype.is_float:
        fmt = 'f'
        max_octet_offset = 32

    pad = (max_octet_offset - used_octet_offset)

    return endian_sym + fmt, pad

def dir_path(string):
    ''' For use as the argparse add_argument 'type' parameter for arguments that are expected to
    be an existing directory'''
    if os.path.isdir(string):
        return string
    raise NotADirectoryError(string)

def strnum_to_int(string, signed):
    ''' Convert a signed/unsigned string based binary number into a python integer '''
    val = BitArray(string)
    if signed:
        return val.int
    return val.uint

def list_available_generators():
    ''' Get a string list of all the existing parseLab generators - this is based on the directories
    under ~/parselab/generators '''
    dirs = [os.path.join(GENERATORS_DIR, d) for d in os.listdir(GENERATORS_DIR) \
                if os.path.isdir(os.path.join(GENERATORS_DIR, d))]

    generators = []
    for d in dirs:
        if '__pycache__' in d:
            continue
        for f in os.listdir(d):
            name_list = []
            if 'Generator.py' in f and '.swp' not in f:
                fullname = ("%s.%s.%s" % ("generators", os.path.basename(d), os.path.splitext(f)[0]))
                generate_generator_names(fullname, name_list, generators)
                generators.append(name_list)

    return generators

def print_available_generators(generator_names):
    '''Print the available generator modules in a nicely formatted list'''
    print("List of all available generator modules and their shortcuts:")
    for name in generator_names:
        print(name[0], end=" ")
        print(name[1:])

def generate_generator_names(name, names, allnames):
    ''' Take an arbitrary name of a generator in the format <Name>Generator (e.g. HammerGenerator) and
    split it into shorter, more readable names. Additionally, check for name conflicts across multiple
    generators. '''

    # generate valid input names
    names.append(name)
    name = name.split('.')
    name = name[len(name)-1]
    names.append(name)
    i = name.find('Generator')
    name = name[0:i]
    names.append(name)
    names.append(name[0:1])
    name = name.lower()
    names.append(name)
    names.append(name[0:1])

    # find conflicts, pop from both lists
    for prev_name in allnames:
        for curr_name in names:
            if curr_name in prev_name:
                pi = prev_name.index(curr_name)
                ci = names.index(curr_name)
                prev_name.pop(pi)
                names.pop(ci)

def lookup_generator_name(module, names):
    ''' Take in the shortcut module, and look up which generator in names it refers to. '''
    m = 'Not Found'
    for name in names:
        if module in name:
            m = name[0]
    if m == 'Not Found':
        return None
    return m

def string_to_number(string):
    ''' Take a string, supposedly representing a number, and convert it to either an int or a float.
    Returns None if the supplied string is neither an int or a float'''
    # want to catch everything
    try:
        return int(string)
    except:
        pass

    try:
        return float(string)
    except:
        pass
#pylitn:enable=bare-except
    return None

def sign(num):
    '''Return either +1 or -1 to represent if the provided number is positive or negative '''
    if num >= 0:
        return 1
    return -1

def get_random_float(lo, hi, w):
    ''' Get a random float between [lo, hi] and have w many decimal places'''
    f = random.uniform(lo, hi)
    return float(("{:.%df}" % w).format(f))

def get_random_int(lo, hi):
    ''' Get a random int between [lo, hi] (inclusive) '''
    return random.randint(lo, hi)
