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
parseLab generator module for the Hammer parsing library by Special Circumstances
    hammer: https://github.com/UpstandingHackers/hammer
'''

import os
import shutil
import subprocess

from generators.ParselabGenerator import ParselabGenerator
from generators.hammer import HammerUtil

from src.TestcaseGenerator import TestMessage
from src.utils.Value import ValueList, ValueRange, ValueSingle, ValueChoice
from src.utils import gen_util

class HammerGenerator(ParselabGenerator):
    ''' This class holds all of the logic and data for generating and running the C code necessary to build a parser
    for a target protocol, using the Hammer parsing Library written in C '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.backend_name = 'Hammer'
        self.hammer_directory = os.path.join(self.protocol_dir, HammerUtil.setup_dirname)
        self.output_directory = os.path.join(self.hammer_directory, 'out')
        self.value_rules = dict()

    def generate_parser(self):
        ''' Generates the source code necessary to build a parser for the target protocol specification in the \
Hammer Data Description Language written in C'''
        if self.spec_data is None:
            err_msg = "There is no spec data set! Cannot generate a parser without spec data."
            self.log.error(err_msg)
            raise Exception(err_msg)

        self.log.info("Defining Value Combinators")
        for msg_type in self.spec_data.message_types:
            self.log.info("Generating sub-parsers for message: %s" % (msg_type.name))
            for field in msg_type.fields:
                self.log.info("Generating sub-parsers for field: %s" % (field.name))
                val = field.value_def.value
                curr_vals, curr_rules = Rule.generate_value_rules(val)
                for i, _ in enumerate(curr_vals):
                    v = curr_vals[i]
                    r = curr_rules[i]
                    if v not in self.value_rules:
                        self.value_rules[v] = r
                    self.log.info("  value_rule: %s" % (r))

        self.log.info("Generated value rules:")
        for v in self.value_rules:
            self.log.info("\t(%s) : [%s]" % (v, self.value_rules[v]))

        parser_text = ''

        # HEADER DIRECTIVE
        parser_text += '#include "parser.h"\n\n'

        # GLOBAL VARIABLES
        global_variables_filepath = os.path.join(self.hammer_directory,
                                                 HammerUtil.global_variables_dirname,
                                                 HammerUtil.global_variables_filename)
        global_variables = self.__generate_global_variables(global_variables_filepath)

        if len(global_variables) > 0:
            self.log.info("Adding the global variables found in %s. NOTE: The curr_state variable is a required \
variable which cannot be reqmoved if using mission types" % (global_variables_filepath))
            global_vars_section_comment = HammerGenerator.comment("Global Variables")
            parser_text += global_vars_section_comment
            for gvar in global_variables:
                parser_text += gvar + '\n'
            parser_text += '\n'

        # GENERAL FUNCTION DEFINITIONS
        functions_dirpath = os.path.join(self.hammer_directory, HammerUtil.functions_dirname)
        functions_string = self.__generate_functions(functions_dirpath)

        if functions_string != '':
            self.log.info("Adding user defined function definitions found in the functions directory: %s" % \
                    (functions_dirpath))
            functions_section_comment = HammerGenerator.comment("User Defined Functions")
            parser_text += functions_section_comment + '\n'
            parser_text += functions_string
        else:
            self.log.warn("There are no user defined function definitions found in the functions directory: %s" % \
                    (functions_dirpath))

        # ACTION FUNCTION DEFINITIONS
        actions_dirpath = os.path.join(self.hammer_directory, HammerUtil.actions_dirname)
        actions_string = self.__generate_actions(actions_dirpath)

        if actions_string != '':
            self.log.info("Adding user defined function definitions found in the actions directory: %s" % \
                    (actions_dirpath))
            actions_section_comment = HammerGenerator.comment("User Defined Actions")
            parser_text += actions_section_comment + '\n'
            parser_text += actions_string
        else:
            self.log.warn("There are no user defined action definitions found in the actions directory: %s" % \
                    (actions_dirpath))

        # PARSER ATTRIUTE FUNCTIONS
        self.log.info("Adding parser attribute functions to the parser")
        attr_func_section_comment = HammerGenerator.comment("Parser Attribute Functions")
        parser_text += attr_func_section_comment + '\n'

        attribute_funcs = self.__generate_function_attributes(self.spec_data)
        for attr_func in attribute_funcs:
            parser_text += str(attr_func) + '\n'
            parser_text += '\n'

        # PARSER FUNCTION
        self.log.info("Adding the main parser funciton: init_parser()")
        parser_func = self.__generate_parser_func(self.spec_data)
        parser_text += str(parser_func)
        parser_text += '\n'

        # GENERATE THE OUTPUT DIRECTORY'S DIRECTORY STRUCTURE
        if not self.__generate_output_directory(force_delete=True):
            err_msg = "Unable to generate output directory. Please delete %s" % (self.output_directory)
            self.log.error(err_msg)
            raise Exception(err_msg)

        # GENERATE THE MAKEFILE FOR THE OUTPUT DIRECTORY
            # grab the makefile from <protocol>/hammer/Makefile
            # and put the makefile into <protocol>/hammer/out/Makefile
        self.__move_makefile()

        # WRITE TO PARSER FILE
        parser_filepath = os.path.join(self.output_directory,
                                       HammerUtil.src_dirname,
                                       HammerUtil.generated_parser_filename)
        with open(parser_filepath, 'w') as f:
            f.write(HammerGenerator.append_generated_code_header('//', parser_text))
        self.log.info("Wrote generated parser to file (%s)" % (parser_filepath))

        # CREATE PARSER HEADER FILE
        self.log.info("Beginning creation of generated parser's header file")

        header_text = "#ifndef __PARSER_H__\n#define __PARSER_H__\n\n"

        # HEADER DIRECTIVE DEFINITIONS
        directives_dirpath = os.path.join(self.hammer_directory, HammerUtil.directives_dirname)
        if os.path.isdir(directives_dirpath):
            header_text += self.__generate_directives(directives_dirpath)
            self.log.info("Adding directives from files in directives directory (%s)" % (directives_dirpath))
        else:
            err_msg = "Missing directives directory from the hammer directory. Checked path: %s" % \
                            (directives_dirpath)
            self.log.error(err_msg)
            raise Exception(err_msg)

        # ENUM DEFINITIONS
        objects_dirpath = os.path.join(self.hammer_directory, HammerUtil.objects_dirname)
        enums_string = self.__generate_enums(objects_dirpath)

        if enums_string != "":
            self.log.info("Adding user defined enum definitions found in the objects directory (%s)" % \
                            (objects_dirpath))
            enums_section_comment = HammerGenerator.comment("User Defined Enums")
            header_text += enums_section_comment + '\n'
            header_text += enums_string

        # STRUCT DEFINITIONS
        structs_string = self.__generate_structs(objects_dirpath)

        if structs_string != "":
            self.log.info("Adding user defined struct definitions found in the objects directory (%s)" % \
                            (objects_dirpath))
            structs_section_comment = HammerGenerator.comment("User Defined Structs")
            header_text += structs_section_comment
            header_text += structs_string

        # CREATE PARSER'S PROTOCOTYPE DECLARATION
        header_text += "HParser *init_parser();\n\n"

        # CLOSING MACRO
        header_text += "#endif"

        # WRITE TO HEADER FILE
        header_filepath = os.path.join(self.output_directory,
                                       HammerUtil.include_dirname,
                                       HammerUtil.generated_header_filename)
        with open(header_filepath, 'w') as f:
            f.write(HammerGenerator.append_generated_code_header('//', header_text))

        self.log.info("Wrote generated header to file (%s)" % (header_filepath))
        self.log.info("Parser Generation Complete!")

        return [parser_filepath, header_filepath]

    def __generate_global_variables(self, global_variables_filepath):
        ''' Generate the lines of code for adding global varirables to the generated parser code '''
        self.log.info("Generating the global variables for use in %s" % HammerUtil.generated_parser_filename)

        if self.is_stateful:
            global_vars_list = ['int curr_state = -1;                    // Required']
        else:
            global_vars_list = []

        if global_variables_filepath is None:
            return global_vars_list

        with open(global_variables_filepath) as f:
            for line in f:
                if line[-1] == '\n':
                    line = line[:-1]

                if line[-1] == ';':
                    line = line[:-1]
                global_vars_list.append(line)

        return global_vars_list

    def __generate_enums(self, objects_dirpath):
        ''' Generate the lines of code for adding enums to the generated parser code '''
        self.log.info("Generating enum objects")
        return HammerGenerator.combine_files_into_string(objects_dirpath, HammerUtil.enum_ext)

    def __generate_structs(self, objects_dirpath):
        ''' Generate the lines of code for adding structs to the generated parser code '''
        self.log.info("Generating struct objects")
        return HammerGenerator.combine_files_into_string(objects_dirpath, HammerUtil.struct_ext)

    def __generate_actions(self, actions_dirpath):
        ''' Generate the lines of code for adding action functions to the generated parser code '''
        self.log.info("Generating user defined actions")
        return HammerGenerator.combine_files_into_string(actions_dirpath, HammerUtil.action_ext)

    def __generate_functions(self, functions_dirpath):
        ''' Generate the lines of code for adding functions to the generated parser code '''
        self.log.info("Generating user defined functions")
        return HammerGenerator.combine_files_into_string(functions_dirpath, HammerUtil.function_ext)

    def __generate_directives(self, directives_dirpath):
        ''' Generate the lines of code for adding macros/directives to the generated parser code '''
        self.log.info("Combining contents of files into the directives sub-directory (%s) into a single string" % \
                        (directives_dirpath))
        directives_string = ""
        directive_files = []
        include_directives_filename = os.path.join(directives_dirpath, HammerUtil.includes_filename)
        macros_directives_filename = os.path.join(directives_dirpath, HammerUtil.macros_filename)

        directive_files.append(include_directives_filename)
        directive_files.append(macros_directives_filename)

        for file in directive_files:
            if os.path.isfile(file):
                with open(file) as f:
                    for line in f:
                        directives_string += line
                    directives_string += '\n'
        return directives_string

    def __generate_function_attributes(self, spec_data):
        ''' Generate the lines of code for adding attribute functions to the generated parser code '''
        def try_append_attributes(func_attributes, new_attribute):
            if new_attribute.validator_func is not None and new_attribute.validator_func not in func_attributes:
                func_attributes.append(new_attribute.validator_func)
            if new_attribute.action_func is not None and new_attribute.action_func not in func_attributes:
                func_attributes.append(new_attribute.action_func)
            return func_attributes

        func_attributes = []
        for message_type in spec_data.message_types:
            self.log.info("Generating Validators/Actions for %s" % (message_type.name))
            if gen_util.debug_mode or message_type.state_ids != []:
                Rule.generate_message_type_rule(message_type)
                attr = Attribute(message_type.rule,
                                 message_type.rule.rule_type,
                                 None,
                                 None,
                                 message_type.state_ids)
                func_attributes = try_append_attributes(func_attributes, attr)

            for field in message_type.fields:
                for val in self.value_rules:
                    rule = self.value_rules[val]
                    attr = Attribute(rule, rule.rule_type, val.dtype, val)
                    func_attributes = try_append_attributes(func_attributes, attr)

                Rule.generate_field_rule(field)
                if gen_util.debug_mode:
                    field.rule.rule_type |= HammerUtil.A_MASK
                attr = Attribute(field.rule,
                                 field.rule.rule_type,
                                 field.dtype,
                                 field.value_def.value)
                func_attributes = try_append_attributes(func_attributes, attr)

        return func_attributes

    def __generate_parser_func(self, spec_data):
        ''' Generate the lines of code for building up the function that builds the parser combinators '''
        self.log.info("Generating the main parser function: init_parser() for use in %s" % \
                        (HammerUtil.generated_parser_filename))

        value_rules, field_rules, message_rules = self.__generate_rule_list(spec_data.message_types)

        value_rules_formatted = ''
        for rule in value_rules:
            value_rules_formatted += '    %s;\n' % str(rule)
        value_rules_formatted = value_rules_formatted[:-1]

        field_rules_formatted = ''
        for rule in field_rules:
            field_rules_formatted += '    // %s\n' % (rule.special_data["field_name"])
            field_rules_formatted += '    %s;\n\n' % str(rule)
        field_rules_formatted = field_rules_formatted[:-1]

        message_rules_formatted = ''
        for rule in message_rules:
            message_rules_formatted += '    %s;\n\n' % str(rule)
        message_rules_formatted = message_rules_formatted[:-1]

        ret_type = 'HParser *'
        func_name = 'init_parser'
        args = ['void']

        parser_body = '''    /*    VALUE RULES    */
{value_rules}

    /*    FIELD RULES    */
{field_rules}

    /*    MESSAGE RULES    */
{message_rules}

    /*    FINAL RULE    */
    {final_rule}

    return PARSER;'''.format(value_rules=value_rules_formatted,
                             field_rules=field_rules_formatted,
                             message_rules=message_rules_formatted,
                             final_rule=self.__define_final_rule())

        parser_func = Function(func_name, ret_type, args, parser_body)

        return parser_func


    def __generate_rule_list(self, message_types):
        ''' Generate all the combinators for the different sub-parsers needed '''
        field_rules_names = []
        field_rules = []
        value_rules = []

        for v in self.value_rules:
            value_rules.append(self.value_rules[v])

        for msg_type in message_types:
            self.log.info("Generating rules from %s's fields" % (msg_type.name))
            for field in msg_type.fields:
                Rule.generate_field_rule(field)
                field.rule.special_data["field_name"] = field.name
                if gen_util.debug_mode:
                    field.rule.rule_type |= HammerUtil.A_MASK
                if field.rule.name not in field_rules_names:
                    field_rules.append(field.rule)
                    field_rules_names.append(field.rule.name)

        message_rules = []
        for msg_type in message_types:
            Rule.generate_message_type_rule(msg_type)
            message_rules.append(msg_type.rule)

        return value_rules, field_rules, message_rules

    def __define_final_rule(self):
        ''' Generate the lines of code for defining the final rule combinator that encompasses all of the sub-parse
        rules'''
        self.log.info("Creating the final rule for the parser")
        final_rule_str = 'h_choice('
        # Add the mission types first
        for msg_type in self.spec_data.message_types:
            if msg_type.is_mission_type:
                final_rule_str += '%s, ' % (msg_type.rule.name)
        # Add regular message types second
        for msg_type in self.spec_data.message_types:
            if not msg_type.is_mission_type:
                final_rule_str += '%s, ' % (msg_type.rule.name)
        final_rule_str += 'NULL)'

        final_rule_str = 'H_RULE(PARSER, %s);' % (final_rule_str)

        return final_rule_str

    def __generate_output_directory(self, force_delete=False):
        ''' Generate the output directory that will house all of the souce code that is generated'''
        include_dir = os.path.join(self.output_directory, HammerUtil.include_dirname)
        src_dir = os.path.join(self.output_directory, HammerUtil.src_dirname)
        tests_dir = os.path.join(self.output_directory, HammerUtil.tests_dirname)

        self.log.info("Checking if output directory (%s) exists ..." % (self.output_directory))
        if os.path.isdir(self.output_directory):
            if force_delete:
                shutil.rmtree(self.output_directory)
            else:
                return False

        self.log.info("Output directory does not exist. Creating it now.")
        os.makedirs(self.output_directory)
        self.log.info("Creating the include directory (%s)" % (include_dir))
        os.mkdir(include_dir)
        self.log.info("Creating the src directory (%s)" % (src_dir))
        os.mkdir(src_dir)
        self.log.info("Creating the tests directory (%s)" % (tests_dir))
        os.mkdir(tests_dir)

        return True

    def __move_makefile(self):
        ''' Copy the make file from the setup data directory and put it into the output directory '''
        makefile_src = os.path.abspath(os.path.join(self.hammer_directory, HammerUtil.makefile_filename))
        makefile_dest = os.path.join(self.output_directory, HammerUtil.makefile_filename)
        shutil.copy(makefile_src, makefile_dest)
        self.log.info("Copied Makefile from (%s) to (%s)" % (makefile_src, makefile_dest))

    def generate_test(self, testcase_dir, protocol_dir, print_results=True):
        ''' Generate the lines of code and create new files that house the logic for running tests with the generated
        parser functions against a suite of data found in the supplied testcase directory '''
        self.log.info("Generating an executable Hammer file to run a test using testcase: %s" % (testcase_dir))

        # Create the testMessages
        results_file = os.path.join(testcase_dir, gen_util.results_filename)
        test_messages = []
        with open(results_file) as f:
            for line in f.readlines():
                split_line = line.strip().split(' - ')
                filename = split_line[0]
                validity = split_line[1]
                valid = validity == 'valid'
                self.log.info("Creating a (%s) TestMessage instance" % (valid))
                self.log.info("Derrived from validition = %s" % (validity))
                tm = TestMessage(filename, valid, testcase_dir)
                test_messages.append(tm)

        # Create the text for all of the files that will be generated
        self.log.info("GENERATING TEST FILETEXT")
        test_text = self.__generate_test_filetext(print_results)

        self.log.info("GENERATING DATA_C FILETEXT")
        data_c_text = self.__generate_data_c_text(test_messages)

        self.log.info("GENERATING DATA_H FILETEXT")
        data_h_text = self.__generate_data_h_text(test_messages)

        # Put the files into their respective locations <protocol_dir>/hammer/out/tests/[src/inc]/<file>
        test_paths = HammerUtil.generate_test_paths(protocol_dir, testcase_dir)
        src_testcase_dirpath = test_paths[4]
        inc_testcase_dirpath = test_paths[5]
        test_filepath = test_paths[6]
        data_c_filepath = test_paths[7]
        data_h_filepath = test_paths[8]

        if not os.path.isdir(src_testcase_dirpath):
            self.log.info("testcase/src does not exist, creating (%s)" % (src_testcase_dirpath))
            os.makedirs(src_testcase_dirpath)
        if not os.path.isdir(inc_testcase_dirpath):
            self.log.info("testcase/inc does not exist, creating (%s)" % (inc_testcase_dirpath))
            os.makedirs(inc_testcase_dirpath)

        files = {test_filepath : test_text,
                 data_c_filepath : data_c_text,
                 data_h_filepath : data_h_text}

        for file in files:
            self.log.info("Creating file %s" % file)
            with open(file, 'w+') as f:
                f.write(HammerGenerator.append_generated_code_header('//', files[file]))

        return list(files.keys())

    def __generate_data_c_text(self, test_messages):
        ''' Generate a c file which holds an array of all of the bytes which define the messages in the <test_messages>
        argument so that it can be referenced by a souce c file '''

        # convert the bytes into a c array string: {0x5, 0x15, 0x62, 0xb1}
        for tm in test_messages:
            tm.c_array = HammerGenerator.get_bytes_as_c_array(tm.bytes)

        # create the struct array
        struct_list = []
        for tm in test_messages:
            struct_list.append(HammerGenerator.create_test_message_struct(tm, 1))
        struct_c_array = ',\n'.join(struct_list)

        # create filetext
        filetext = '''#include "data.h"

int num_messages = {num_messages};

TestMessage_t messages[{num_messages}] = {{
{struct_array}
}};'''.format(struct_array=struct_c_array, num_messages=len(test_messages))

        return filetext

    def __generate_data_h_text(self, test_messages):
        ''' Generate the header file for the c data file '''
        filetext = '''#include <stdint.h>
#include <stdlib.h>

typedef struct {{
    char* msg_name;
    uint8_t* bytes;
    size_t size;
    int result;
}} TestMessage_t;

extern TestMessage_t messages[{num_messages}];
extern int num_messages;
'''.format(num_messages=len(test_messages))

        return filetext

    def __generate_test_filetext(self, print_results):
        ''' Generate the source lines of code for building up a test which runs a parser against the data stored in the
        data header and c files '''
        comment_str = '//' if not print_results  else ''
        filetext = '''#include <hammer/hammer.h>
#include <hammer/glue.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#include "parser.h"
#include "data.h"

#define PACKET_MAX_LEN 8096

typedef struct {{
    char* Reset;
    char* Red;
    char* Green;
    char* Yellow;
    char* Blue;
    char* Cyan;
}} colors_t;

colors_t colors = {{
    .Reset = "\\033[0m",
    .Red = "\\033[0;31m",
    .Green = "\\033[032m",
    .Yellow = "\\033[033m",
    .Blue = "\\033[034m",
    .Cyan = "\\033[036m",
}};


int main() {{
    HParser* parser_under_test = init_parser();
    uint8_t input[PACKET_MAX_LEN];
    HParseResult* result;
    int fail_count = 0;
    int ACCEPT = 1;
    int REJECT = 0;

    for (int i = 0; i < num_messages; i++) {{
        memcpy(input, messages[i].bytes, messages[i].size);
        result = h_parse(parser_under_test, input, messages[i].size);

        // if parse_result == NULL, parser rejected it
        // if results[i] == 0, the parser SHOULD reject it
        if (result == NULL) {{
            if (messages[i].result == ACCEPT) {{
                {comment}fprintf(stdout, "%s[FAIL] Message (%s) was incorrectly rejected by parser%s\\n", colors.Red, messages[i].msg_name, colors.Reset);
                fail_count++;
            }}
            else if (messages[i].result == REJECT) {{
                {comment}fprintf(stdout, "%s[PASS] Message (%s) was correctly rejected by parser%s\\n", colors.Green, messages[i].msg_name, colors.Reset);

            }}
        }}
        else {{
            if (messages[i].result == ACCEPT) {{
                {comment}fprintf(stdout, "%s[PASS] Message (%s) was correctly accepted by parser%s\\n", colors.Green, messages[i].msg_name, colors.Reset);
            }}
            else if (messages[i].result == REJECT) {{
                {comment}fprintf(stdout, "%s[FAIL] Message (%s) was incorrectly accepted by parser%s\\n", colors.Red, messages[i].msg_name, colors.Reset);
                fail_count++;
            }}
        }}
    }}

    return fail_count;
}}
'''.format(comment=comment_str)

        return filetext

    def __get_test_from_testcase(self, testcase_dir, protocol_dir):
        ''' Provided a testcase directory, extract a test executable from it '''
        out_filepath = os.path.join(protocol_dir, HammerUtil.generated_output_dirpath)
        tests_dirpath = os.path.join(out_filepath, HammerUtil.tests_dirname)
        testcase_dir += '/' if testcase_dir[-1] != '/' else ''
        testcase_name = os.path.basename(os.path.dirname(testcase_dir))
        out_testcase_dirpath = os.path.join(tests_dirpath, testcase_name)
        test_exe_filepath = os.path.join(out_testcase_dirpath, HammerUtil.exec_test_dirpath)

        return test_exe_filepath

    def run_test_from_testcase(self, testcase_dir, protocol_dir):
        ''' Provided a testcase directory, execute the test's executable inside of it '''
        test_paths = HammerUtil.generate_test_paths(protocol_dir, testcase_dir)
        out_filepath = test_paths[0]
        test_exe_filepath = test_paths[9]

        # Run the makefile
        self.log.info("Running makefile in hammer's output directory (%s)" % (out_filepath))
        rv = subprocess.call(["make clean"], shell=True, stdout=subprocess.PIPE, cwd=out_filepath)
        if rv > 0:
            self.log.warn("Unable to make clean in directory (%s)" % (out_filepath))
        rv = subprocess.call(["make"], shell=True, stdout=subprocess.PIPE, cwd=out_filepath)
        if rv > 0:
            self.log.warn("Unable to make in directory (%s)" % (out_filepath))

        test_exe_filepath = self.__get_test_from_testcase(testcase_dir, protocol_dir)
        test_exe_dirpath = os.path.dirname(test_exe_filepath)
        self.log.info("Running test %s" % (test_exe_filepath))
        rv = subprocess.call(['./test.bin'], shell=True, cwd=test_exe_dirpath, stdout=None)
        self.log.info("Test executed with return code=%d" % (rv))

        return rv

    @staticmethod
    def create_test_message_struct(test_message, tabs):
        ''' Define the format for the struct that contains the test data in the data c file '''
        tabs = '    ' * tabs
        string = '''{tab}{{
{tab}    "{msg_name}",
{tab}    (uint8_t[]){bytes_string},
{tab}    {message_len},
{tab}    {int_result}
{tab}}}'''.format(msg_name=test_message.basename,
            bytes_string=HammerGenerator.get_bytes_as_c_array(test_message.bytes),
            message_len=len(test_message.bytes),
            int_result=str(int((test_message.result))),
            tab=tabs)

        return string

    @staticmethod
    def get_bytes_as_c_array(_bytes):
        ''' Convert a python bytes list into a c array format '''
        bytes_list = ', '.join([hex(b) for b in _bytes])
        return '{%s}' % (bytes_list)

    @staticmethod
    def get_setup_directory():
        ''' Return the setup data directory path '''
        return HammerUtil.setup_dirpath

    @staticmethod
    def get_setup_directory_name():
        ''' Return the name that the generated setup data directory should have when placed into the protocol dir '''
        return HammerUtil.setup_dirname

    @staticmethod
    def get_dtype_h_type(dtype):
        '''Get the hammer type from a supplied parseLab DType object '''
        h_type = ''
        size = dtype.get_size_in_bits()

        if size != -1 and size in HammerUtil.native_hammer_sizes:
            int_type = 'uint'
            if dtype.signed:
                int_type = 'int'
            h_type = 'h_%s%d()' % (int_type, size)
        else:
            if dtype.is_native_dtype():
                lcase_signed = str(dtype.signed).lower()
                h_type = 'h_bits(%d, %s)' % (size, lcase_signed)
            else:
                h_type = dtype.main_type

        if not dtype.is_big_endian and size > 8:
            h_type = 'h_with_endianness(BYTE_LITTLE_ENDIAN, %s)' % (h_type)

        ldep = dtype.dependee.lower()

        if dtype.has_type_dependency:
            ldep = dtype.dependency.lower()
            h_type = 'h_length_value(h_get_value("%s"), %s)' % (ldep, h_type)

        if dtype.dependee != '':
            h_type = 'h_put_value(%s, "%s")' % (h_type, ldep)

        return h_type

    @staticmethod
    def generate_valuedef_combinator(value_def):
        ''' Generate the Hammer combinator for the provided value defintion '''
        if value_def.value is not None:
            return HammerGenerator.generate_field_combinator(value_def.value)
        if value_def.dtype is not None:
            return HammerGenerator.get_dtype_h_type(value_def.dtype)
        raise AttributeError("Supplied value_def (%s) does not have a Value or DType attribute defined" % (value_def))

    @staticmethod
    def generate_field_combinator(value):
        ''' Generate the Hammer combinator for the supplied value '''
        if isinstance(value, ValueSingle):
            combinator = Rule.generate_value_single_name(value)
            return combinator
        if isinstance(value, ValueRange):
            combinator = Rule.generate_value_name(value)
            return combinator
        if isinstance(value, ValueChoice):
            combinator = '\n' + 8*' ' + 'h_choice('
            for item in value.contents:
                combinator += '\n            ' + HammerGenerator.generate_field_combinator(item) + ','
            combinator += '\n' + 12*' ' + 'NULL)'
            return combinator
        if isinstance(value, ValueList):
            combinator = '\n' + 8*' ' + 'h_sequence('
            for item in value.contents:
                combinator += '\n' + 12*' ' + HammerGenerator.generate_field_combinator(item) + ','
            combinator += '\n' + 12*' ' + 'NULL)'
            return combinator
        raise ValueError("Supplied value (%s) is not of a known parseLab Value Type" % (value))

    @staticmethod
    def comment(msg, is_section=False, max_len=80):
        ''' Generate a C comment as either // or /*  */
           param:      msg             string to make into the comment
           param:      is_section      is the comment a /*  */ (true) or // (false)                -- DEFAULT - False
           param:      max_len         max length of the line (including the comment symbols)      -- DEFAULT - 80'''
        comment = ""
        curr_line = ""
        if is_section:
            curr_line += "/*\n * "
            comment_sym = ' * '
        else:
            curr_line += "// "
            comment_sym = '// '

        for char in msg:
            if char == '\n':
                curr_line += '\n'
                comment += curr_line
                curr_line = comment_sym
                continue

            if len(curr_line) >= max_len:
                curr_line += '\n'
                comment += curr_line
                curr_line = comment_sym

            curr_line += char

        curr_line += '\n'
        comment += curr_line

        if is_section:
            comment += ' */'

        return comment

    @staticmethod
    def combine_files_into_string(dirpath, file_extension):
        ''' long string concatenating all of the contents of each file which matches the extension '''
        file_contents = ""

        files = [f for f in os.listdir(dirpath) if \
            (os.path.isfile(os.path.join(dirpath, f)) and os.path.splitext(f)[1] == file_extension)]

        for file in files:
            with open(os.path.join(dirpath, file)) as f:
                for line in f:
                    file_contents += line
                file_contents += '\n'

        return file_contents

class Rule:
    ''' A class to contain all of the information contained in a Hammer "Rule", or Combaintor, and how to generate the
    necessary source lines of code for it '''

    def __init__(self, name, rule_string, rule_type=HammerUtil.RULE,):
        self.name = name
        self.rule_string = rule_string
        self.rule_type = rule_type
        self.special_data = dict()

    def __str__(self):
        rule_prefix = HammerUtil.prefix_dict[self.rule_type]
        return "H_%sRULE(%s, %s)" % (rule_prefix, self.name, self.rule_string)

    def __repr__(self):
        return self.__str__()

    @staticmethod
    def generate_message_type_rule(message_type):
        ''' Build up a Hammer Rule for the provided message type '''
        rule_str = "\n          h_sequence(\n" + ' '*12
        for field in message_type.fields:
            field_rule = Rule.generate_field_rule(field)
            rule_str += field_rule.name + ', \n' + ' '*12
        rule_str += "h_end_p(),\n" + ' '*12
        rule_str += "NULL)"
        rule_type = 0
        if len(message_type.state_ids) > 0:
            rule_type = HammerUtil.STATE_VALIDATOR
        message_type.rule = Rule(message_type.name, rule_str, rule_type)

    @staticmethod
    def generate_value_rules(value):
        ''' Generate a Hammer Rule for the provided value '''
        rules = list()
        vals = list()

        if isinstance(value, ValueSingle):
            vals.append(value)
            name = Rule.generate_value_name(value)
            if value.dtype.is_float:
                rule_str = HammerGenerator.get_dtype_h_type(value.dtype)
            elif value.dtype.get_size_in_bits() == 8 and not value.dtype.signed:
                rule_str = 'h_ch(%s)' % value.value
            else:
                rule_str = 'h_int_range(%s, %s, %s)' % \
                    (HammerGenerator.get_dtype_h_type(value.dtype), hex(value.value), hex(value.value))
            rule_type = HammerUtil.RULE

            if value.dtype.is_float:
                rule_type |= HammerUtil.V_MASK

            rules.append(Rule(name, rule_str, rule_type))
        elif isinstance(value, ValueRange):
            vals.append(value)
            rule_type = HammerUtil.RULE
            name = Rule.generate_value_name(value)
            if value.dtype.is_float:
                rule_type |= HammerUtil.V_MASK
                rule_str = "h_uint32()"
            else:
                rule_str = "h_int_range(%s, %s, %s)" % \
                    (HammerGenerator.get_dtype_h_type(value.dtype),
                     hex(value.min_bound.value),
                     hex(value.max_bound.value))
            rules.append(Rule(name, rule_str, rule_type))
        elif isinstance(value, ValueChoice):
            # iterate over the contents
            for val in value.contents:
                # Generate a rule for each value in the contents
                vs, rs = Rule.generate_value_rules(val)
                # take the returning list and extend it to the running vals list
                vals.extend(vs)
                rules.extend(rs)

        elif isinstance(value, ValueList):
            # iterate over the contents
            for val in value.contents:
                # Generate a rule for each value in the contents
                vs, rs = Rule.generate_value_rules(val)
                # take the returning list and extend it to the running vals list
                vals.extend(vs)
                rules.extend(rs)

        return vals, rules

    @staticmethod
    def generate_value_name(value):
        ''' Generate a name for a Hammer Rule which parses for the provided parseLab Value'''
        if value is None:
            raise ValueError("unexpected behaviour")
        dtype = value.dtype
        endianness = ''
        if not dtype.is_big_endian:
            endianness = 'LENDIAN_'

        name = 'V_'
        if isinstance(value, ValueSingle):
            if dtype.dependee == '':
                main_type = dtype.main_type
                name += value.generate_name()
                name += '__%s%s' % (endianness, main_type)
            else:
                name += dtype
        elif isinstance(value, (ValueRange, ValueChoice, ValueList)):
            main_type = dtype.main_type
            name += value.generate_name()
            name += '__%s%s' % (endianness, main_type)
        else:
            raise Exception("Not yet supported for (%s) - unexpected behaviour" % (type(value)))

        name = name.replace('-', 'neg')
        name = name.replace('.', 'o')
        return name

    @staticmethod
    def generate_value_single_name(value):
        ''' Generate a name for a Hammer Rule which parses for the provided ValueSingle '''
        if value is None:
            raise ValueError("unexpected behaviour")
        dtype = value.dtype
        endianness = ''
        if not dtype.is_big_endian:
            endianness = 'LENDIAN_'

        name = 'V_'
        if isinstance(value, ValueSingle):
            if dtype.dependee == '':
                main_type = dtype.main_type
                name += value.generate_name()
                name += '__%s%s' % (endianness, main_type)
            else:
                name += dtype
        else:
            raise Exception("Not yet supported for (%s) - unexpected behaviour" % (type(value)))

        name = name.replace('-', 'neg')
        name = name.replace('.', 'o')

        return name

    @staticmethod
    def generate_field_rule(field):
        ''' Generate a Hammer Rule which parses for the provided parseLab FieldDef '''
        def generate_name(field):
            ''' Generate name for a Hammer Rule which parses for the provided parseLab FieldDef '''
            endianness = ''
            name = "F_"
            if not field.dtype.is_big_endian:
                endianness = 'LENDIAN_'

            if field.dtype.dependee == '':
                main_type = field.dtype.main_type
                if field.value_def.value is None:
                    name += 'ANY_VALUE'
                else:
                    n = field.value_def.value.generate_name()
                    name += n

                name += '__%s%s' % (endianness, main_type)
            else:
                name = field.dtype.dependee
            name = name.replace('-', 'neg')
            name = name.replace('.', 'o')

            return name

        name = generate_name(field)

        rule_str = HammerGenerator.get_dtype_h_type(field.dtype)
        if field.value_def.value is not None:
            rule_str = HammerGenerator.generate_valuedef_combinator(field.value_def)
        else:
            if field.dtype.is_list:
                name += '_ARRAY_'
                if field.dtype.has_type_dependency:
                    name += '_%s_%s' % (field.dtype.dependency, field.message_name)
                else:
                    name += str(field.dtype.list_count)
                    rule_str = "h_repeat_n(%s, %s)" % (rule_str, field.dtype.list_count)

        rule_type = HammerUtil.RULE
        if field.value_def.value is not None:
            if field.dtype.is_float and isinstance(field.value_def.value, ValueSingle):
                rule_type |= HammerUtil.V_MASK

        field.rule = Rule(name, rule_str, rule_type)
        return field.rule

class Attribute:
    ''' Class which contains the logic and data for Hammer Attributes '''
    def __init__(self, rule, attr_type, dtype, value, state_ids=None):
        self.rule = rule
        self.attr_type = attr_type
        self.dtype = dtype
        self.value = value
        self.state_ids = state_ids

        self.action_func = None
        self.validator_func = None

        self.__generate_funcs()

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return self.rule == other.rule and \
               self.attr_type == other.attr_type and \
               self.dtype == other.dtype and \
               self.value == other.value and \
               self.state_ids == other.state_ids

    def __generate_funcs(self):
        ''' Generate the associated functions for building up this function attribute in the source code '''
        def float_validation(value):
            ''' Generate the logic for validating a float in a Hammer Attribute Function '''
            if isinstance(value, ValueSingle):
                body = '''    if (abs(p->ast->flt - {float_value}) < .001) {{
        return true;
    }}
    //fprintf(stdout, "{float_value} != %f\\n", p->ast->flt);
    return false;'''.format(float_value=value.value)
            elif isinstance(value, ValueRange):
                body = '''    if ({min_bound} <= p->ast->flt && p->ast->flt <= {max_bound}) {{
        return true;
    }}
    //fprintf(stdout, "%d is not in bounds: [{min_bound}, {max_bound}]", p->ast->flt);
    return false;'''.format(min_bound=value.min_bound.value, max_bound=value.max_bound.value)

            else:
                raise Exception("Float validation only supported for ValueSingle and ValueRange")

            return body

        def state_validation(state_ids):
            ''' Generate the logic for validating the state of the parser in a Hammer Attribute Function '''
            if len(state_ids) == 1:
                state_id_def = 'int state_id = %d;' % state_ids[0]
                state_id_check = '''if (curr_state == state_id - 1) {
        curr_state = state_id;
        return true;
    }

    return false;'''

                body = '''    {state_id_line}
    {state_id_check}'''.format(state_id_line=state_id_def, state_id_check=state_id_check)

            elif len(state_ids) > 1:
                state_list_string = '{ '
                for _id in state_ids:
                    state_list_string += '%d, ' % _id
                state_list_string = state_list_string[:-2] + ' }'
                state_id_def = 'int state_ids[%d] = %s;' % (len(state_ids), state_list_string)
                state_id_check = '''int i = 0;
    for (i = 0; i < %d; i++) {
        if (curr_state == state_ids[i] - 1) {
            curr_state = state_ids[i];
            return true;
        }
    }

    return false;''' % len(state_ids)

                body = '''    {state_id_line}
    {state_id_check}'''.format(state_id_line=state_id_def, state_id_check=state_id_check)

            else:
                err_msg = "Attribute - Cannot generate a state validation function without state ids!"
                raise Exception(err_msg)


            return body

        def action_debug(func_name):
            ''' Generate the logic for priting debug information in a Hammer Attribute Function '''
            return '''    printf("{func_name}  :  ");
    h_pprint(stdout, p->ast, 3, 1);

    return (HParsedToken *)p->ast;'''.format(func_name=func_name)

        if self.attr_type == HammerUtil.VALIDATOR or \
           self.attr_type == HammerUtil.STATE_VALIDATOR or \
           self.attr_type == HammerUtil.ACTION_VALIDATOR:
            func_name = 'validate_%s' % self.rule.name
            ret_type = 'bool'
            args = ['HParseResult *p', 'void *user_data']
            if self.dtype is not None and self.dtype.is_float:
                body = float_validation(self.value)
            elif self.state_ids is not None:
                body = state_validation(self.state_ids)
            else:
                err_msg = "Attribute - Only accepting float and state checking for validation."
                raise ValueError(err_msg)
            self.validator_func = Function(func_name, ret_type, args, body)

        elif self.attr_type == HammerUtil.ACTION or self.attr_type == HammerUtil.ACTION_VALIDATOR:
            func_name = 'act_%s' % self.rule.name
            ret_type = 'HParsedToken *'
            args = ['const HParseResult *p', 'void *user_data']
            body = ''

            if gen_util.debug_mode:
                body += action_debug(func_name)

            self.action_func = Function(func_name, ret_type, args, body)

# This class defines a C Function
class Function():
    ''' This class holds all of the logic and data for generating a Funciton in C '''
    def __init__(self, name, ret_type, args, body):
        self.name = name
        self.ret_type = ret_type
        self.args = args
        self.body = body

        self.__generate_function()

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return self.name == other.name and self.ret_type == other.ret_type and self.args == other.args

    def __str__(self):
        return self.function

    def __generate_function(self):
        ''' Generate the source lines of code for building a C function which matches the data stored in this class '''
        ret_type_str = self.ret_type
        if ret_type_str[-1] != '*':
            ret_type_str += ' '

        function = '%s%s(' % (ret_type_str, self.name)
        for arg in self.args:
            function += '%s, ' % arg
        function = function[:-2] + ') {\n'
        function += self.body + '\n}'

        self.function = function

        return function
