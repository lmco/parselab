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

'''
Example generator module used in the "Creating a Custom parseLab Generator" Guide.

This generator uses the python bindings for Special Circumstance's Hammer parsing library built for
the C language.

Functionality is limited, but sufficient as a starting path for learning parseLab module creation.
'''

import os
import subprocess

from generators.ParselabGenerator import ParselabGenerator
from src.TestcaseGenerator import TestMessage

from src.utils.Value import ValueRange
from src.utils import gen_util

class PyhammerGenerator(ParselabGenerator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.backend_name = "pyHammer"
        self.protocol_name = os.path.basename(self.protocol_dir)
        self.output_directory = os.path.join(self.protocol_dir, self.backend_name)
        self.test_directory = os.path.join(self.output_directory, 'tests')

    def generate_parser(self):
        self.log.info("Generating a %s parser" % (self.backend_name))

        if self.spec_data is None:
            err_msg = "There is no spec data set! Cannot generate a parser without spec data."
            self.log.error(err_msg)
            raise AttributeError(err_msg)

        # List of filepaths that we have generated with this function
        ret_files = list()

        # String to hold all of the lines of code that we will write our to the source code file
        parser_text = ''

        # list of imports that can be imported with "import <x>"
        simple_imports = ['hammer']
        # list of imports that can be imported with "from <x> import <y>, where each element
        #   is a tuple(x, y)
        from_imports = list()

        # Append the import information to the parser text
        if len(simple_imports) == 0:
            self.log.err("There are no simple imports; Must at least import hammer!")
        for simple_import in simple_imports:
            parser_text += 'import %s\n' % (simple_import)
        parser_text += '\n'

        if len(from_imports) == 0:
            self.log.warn("There are no from imports")
        for from_import in from_imports:
            parser_text += 'from %s import %s' % (from_import[0], from_import[1])
        parser_text += '\n'

        parser_text += self.__generate_parser_func()
        parser_text += '\n'

        self.log.info("Completed generation of parser code")

        # Add the output directory of it doesn't exist
        if not os.path.isdir(self.output_directory):
            os.makedirs(self.output_directory)

        # Establish filepath for parser
        parser_filename = '%s_parser.py' % (self.protocol_name)
        parser_filepath = os.path.join(self.output_directory, parser_filename)
        ret_files.append(parser_filepath)

        # Write it out to a file
        with open(parser_filepath, 'w') as f:
            f.write(parser_text)

        return ret_files

    # NEW PRIVATE FUNCTION (__ before a function denotes private function in python)
    def __generate_parser_func(self):
        parser_func = ''

        # Create function definition
        parser_func += 'def init_%s_parser():\n' % (self.protocol_name)

        # Make final parse rule
        msg_parser_names = [msg_type.name + '_parser' for msg_type in self.spec_data.message_types]
        protocol_parser_rule_name = '%s_parser' % (self.protocol_name)
        protocol_parser_rule = '%s = hammer.sequence(%s)' % (protocol_parser_rule_name, \
                                                              ', '.join(msg_parser_names))
        message_parser_rules = list()
        field_parser_rules = list()
        ## Iterate through the message types specified in the spec_data
        for msg_type in self.spec_data.message_types:
            fld_rules = list()
            # Iterate over the fields in this message type
            for field in msg_type.fields:
                dtype = field.dtype
                size = dtype.get_size_in_bits()
                signed_prefix = 'u' if not dtype.signed else ''
                value = field.value_def.value
                h_type = ''
                # Hammer has library functions for parsing ints vs floats
                if dtype.is_int:
                    # Hammer only has simple integer parsers for these values
                    if size not in [8, 16, 32, 64]:
                        raise NotImplementedError("Generator does not support size=%d" % size)
                    # Define the data type according to hammer's library
                    h_type = 'hammer.%sint%d()' % (signed_prefix, size)
                    # Hammer can support series of a data type, AKA a list
                    if dtype.is_list:
                        # Dependencies are covered in the UDP_protocol_specification.md guide
                        if dtype.has_type_dependency:
                            # Not possible in pyHammer, replace with a many() combinator
                            ## Note: this will only work if field is at the end of the message frame
                            h_type = 'hammer.many(%s)' % (h_type)
                        else:
                            h_type = 'hammer.repeat_n(%s, %s)' % (h_type, dtype.list_count)
                    else:
                        # Add a value constraint if exists
                        if value is not None:
                            # parseLab has multiple Value types, but we will only do ValueRange right now
                            if isinstance(value, ValueRange):
                                h_type = 'hammer.int_range(%s, %s, %s)' % (h_type, value.min_bound, value.max_bound)
                            else:
                                raise NotImplementedError("Generator does not support value type=%s" % \
                                                          type(ValueChoice))
                else:
                    raise NotImplementedError("Generator does not support non-integer dtypes")
                # Build the parse rule for the field and put it in our array
                field_rule_name = '%s__%s_parser' % (msg_type.name, field.name)
                field_rule = '%s = ' % (field_rule_name)
                field_rule += h_type
                field_parser_rules.append(field_rule)
                fld_rules.append(field_rule_name)
            # Add an "end stream" parser to the end of the field parser list
            fld_rules.append('hammer.end_p()')
            field_rule_list_str = ', '.join(fld_rules)
            # Create the message rule as a sequence of all its field parsers
            msg_rule = '%s_parser = hammer.sequence(%s)' % (msg_type.name, field_rule_list_str)
            message_parser_rules.append(msg_rule)
        # Write out all of the parsers to the running text string
        tab = ' '*4
        parser_func += tab + '\n    '.join(field_parser_rules) + '\n\n'
        parser_func += tab + '\n    '.join(message_parser_rules) + '\n\n'
        parser_func += tab + protocol_parser_rule + '\n'
        # The function we are building must return the final parser for it to be used
        parser_func += tab + 'return %s' % (protocol_parser_rule_name)
        return parser_func

    def generate_test(self, testcase_dir, protocol_dir, print_results=False):
        self.log.info("Generating a test script that iterates over the messages in the directory: %s" % (testcase_dir))
        test_files = list()

        # Get the results file
        results_file = os.path.join(testcase_dir, gen_util.results_filename)
        test_messages = []
        with open(results_file, 'r') as f:
            for line in f.readlines():
                split_line = line.strip().split(' - ')
                filename = split_line[0]
                validity = split_line[1]
                valid = validity == 'valid'
                # Build a TestMessage with this information
                self.log.info("Creating a (%s) TestMessage instance from %s" % (valid, filename))
                tm = TestMessage(filename, valid, testcase_dir)
                test_messages.append(tm)

        # Setup imports
        first_imports = ['import os, sys', \
                         'sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))']
        simple_imports = ['%s_parser' % (self.protocol_name)]
        from_imports = list()

        # Build up test file
        test_text = ''
        tab = ' '*4

        # Add imports
        for first_import in first_imports:
            test_text += first_import + '\n'
        for simple_import in simple_imports:
            test_text += 'import %s\n' % (simple_import)
        for from_import in from_imports:
            test_text += 'from %s import %s' % (from_import[0], from_import[1])
        test_text += '\n'

        # Make a main
        test_text += 'def main():\n'

        # Define parser
        test_text += tab + 'parser = %s_parser.init_%s_parser()\n' % (self.protocol_name, self.protocol_name)
        test_text += '\n'

        # Add a tuple array of all the binary filepaths and their validity
        tm_paths_str = tab + 'message_paths = ['
        for tm in test_messages:
            tm_path = os.path.abspath(os.path.join(testcase_dir, tm.filename))
            tm_valid = tm.result
            tm_paths_str += '("%s", %s), ' % (tm_path, tm_valid)
        tm_paths_str = tm_paths_str[:-2]
        tm_paths_str += ']\n\n'
        test_text += tm_paths_str

        # Add logic to iterate over the tuple arrayand run parser against its contents
        file_reader_text = '''    # Iterate over binary files and run contents against parser
    for (fp, result) in message_paths:
        with open(fp, 'rb') as f:
            ba = bytearray(f.read())
        # Passing bytes through parser
        parse_result = parser.parse(bytes(ba))
        
        if parse_result is not None and {debug_mode}:
            print(parse_result)

        msg_name = os.path.basename(fp)
        test_result = (parse_result is not None) == result
        test_pass_str = 'PASS' if test_result else 'FAIL'
        correct_prefix = 'in' if not test_result else ''
        action_str = 'accepted' if parse_result else 'rejected'
        status_str = 'was %scorrectly %s by the parser' % (correct_prefix, action_str)
        print('[%s] Test %s %s' % (test_pass_str, msg_name, status_str))\n\n'''.format(debug_mode=gen_util.debug_mode)
        test_text += file_reader_text

        # Add module check
        test_text += "if __name__ == '__main__':\n    main()\n"

        testcase_name = os.path.basename(os.path.dirname(testcase_dir))
        testfile_filepath = os.path.join(self.test_directory, testcase_name + '.py')
        testfile_filepath = os.path.abspath(testfile_filepath)
        test_files.append(testfile_filepath)

        if not os.path.isdir(self.test_directory):
            os.makedirs(self.test_directory)

        with open(testfile_filepath, 'w') as f:
            f.write(test_text)

        return test_files

    def run_test_from_testcase(self, testcase_dir, protocol_dir):
        testcase_name = os.path.basename(os.path.dirname(testcase_dir))
        testfile_filepath = os.path.join(self.test_directory, testcase_name + '.py')
        testfile_fliepath = os.path.abspath(testfile_filepath)

        self.log.info("Running test %s" % (testfile_filepath))
        cmd = "python3 %s" % (testfile_filepath)
        rv = subprocess.call([cmd], shell=True, stdout=None)
        self.log.info("Test executed with return code=%d" % (rv))

        return rv

    @staticmethod
    def get_setup_directory():
        this_file_filepath = os.path.realpath(__file__)
        this_file_dirpath = os.path.dirname(this_file_filepath)
        setup_data_dirpath = os.path.join(this_file_dirpath, 'setup_data')
        return setup_data_dirpath

    def get_setup_directory_name():
        return "pyHammer"
