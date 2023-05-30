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
parseLab generator module for the Daedalus Data Description Language by Galois
    Daedalus: https://github.com/GaloisInc/daedalus
'''

import os
import stat
import subprocess

from generators.ParselabGenerator import ParselabGenerator

from src.TestcaseGenerator import TestMessage
from src.utils.Value import ValueRange #, ValueList, ValueSingle, ValueChoice
from src.utils import gen_util

class DaedalusGenerator(ParselabGenerator):
    ''' This class holds all of the logic and data for generating and running the daedalus code necessary to build a
    parser for a target protocol, using the Daedalus Data Description Language written by Galois '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.backend_name = "daedalus"
        self.output_directory = os.path.join(self.protocol_dir, self.backend_name)
        self.test_directory = os.path.join(self.output_directory, 'tests')
        self.protocol_name = os.path.basename(self.protocol_dir)

        # UPDATE ME
        self.DAEDALUS_REPO_PATH = '/home/parsival/tools/daedalus'
        # Check to make sure that a pointer to the daedalus repo is assigned
        if not os.path.isdir(self.DAEDALUS_REPO_PATH):
            raise FileNotFoundError("Please update DaedalusGenerator.py with the correct path to the cloned \
Daedalus directory")

    def generate_parser(self):
        ''' Generates the daedalus source code necessary for defining a parser for the target protocol \
        specification '''

        self.log.info("Generating a %s parser" % (self.backend_name))

        if self.spec_data is None:
            err_msg = "There is no spec data set! Cannot generate a parser without spec data."
            self.log.error(err_msg)
            raise AttributeError(err_msg)

        daedalus_standard_lib_path = os.path.join(self.DAEDALUS_REPO_PATH, "lib/Daedalus.ddl")

        ddl_text = ''

        # Add Imports
        imports = list()
        imports.append('import Daedalus')

        ddl_text += '\n'.join(imports)
        ddl_text += '\n\n'

        # Build Main
        main_declaration = Declaration('Main', ['$$ = MessageTypes'])
        ddl_text += main_declaration.as_text()
        ddl_text += '\n\n'

        # Build Top Level Choice Parser
        msg_types_declaration = Declaration('MessageTypes', list())

        choice_statement = 'messages = '
        msg_parser_names = list()
        for msg_type in self.spec_data.message_types:
            msg_parser_names.append(msg_type.name.lower()[0].upper() + msg_type.name.lower()[1:])
        choice_def = ' | '.join(msg_parser_names)
        choice_statement += choice_def
        msg_types_declaration.add_statement(choice_statement)

        ddl_text += msg_types_declaration.as_text()
        ddl_text += '\n\n'

        # Build Low Level Message Parsers
        for msg_type in self.spec_data.message_types:
            msg_declaration_name = msg_type.name.lower()[0].upper() + msg_type.name.lower()[1:]
            msg_declaration = Declaration(msg_declaration_name, list())
            for field in msg_type.fields:
                dtype = field.dtype
                size = dtype.get_size_in_bits()
                signed_prefix = 'U' if not dtype.signed else 'S'
                endian_prefix = 'BE' if dtype.is_big_endian else 'LE'
                if size == 8:
                    endian_prefix = ''
                dependee_suffix = ''
                if dtype.dependee != '':
                    dependee_suffix = ' as uint 64'

                s = ''
                field_name = field.name.lower() + '_'
                if dtype.is_int:
                    if size not in [8, 16, 32, 64]:
                        raise NotImplementedError("Currently only supporting integers of sizes 8, 16, 32, and 64")
                    ddl_type = "%s%sInt%d" % (endian_prefix, signed_prefix, size)
                    if dtype.is_list:
                        list_len = str(dtype.list_count)
                        if dtype.dependency != '':
                            list_len = dtype.dependency.lower() + '_'
                        s = "%s = Many %s %s" % (field_name, list_len, ddl_type)
                    else:
                        s = "%s = %s%s" % (field_name, ddl_type, dependee_suffix)

                elif dtype.is_float:
                    pass
                else:
                    raise ValueError("Unexpected value")
                # Add type check statement

                msg_declaration.add_statement(s)

                # Add constraint check statement
                if field.value_def.value is not None:
                    value = field.value_def.value

                    if isinstance(value, ValueRange):
                        min_s = "%s >= %s" % (field_name, value.min_bound)
                        max_s = "%s <= %s" % (field_name, value.max_bound)
                        msg_declaration.add_statement(min_s)
                        msg_declaration.add_statement(max_s)

            ddl_text += msg_declaration.as_text()
            ddl_text += '\n\n'

        # Add output directory if doesn't exist
        if not os.path.isdir(self.output_directory):
            os.makedirs(self.output_directory)

        # Write out to files
        ddl_filename = '%s.ddl' % (self.protocol_name)
        ddl_filepath = os.path.join(self.output_directory, ddl_filename)

        with open(ddl_filepath, 'w') as f:
            f.write(ddl_text)

        # Make a symlink to the daedalus ddl in this output directory
        symlink_dstpath = os.path.join(self.output_directory, "Daedalus.ddl")
        if not os.path.exists(symlink_dstpath):
            os.symlink(daedalus_standard_lib_path, symlink_dstpath)

        return [ddl_filepath, symlink_dstpath]

    def generate_test(self, testcase_dir, protocol_dir, print_results=False):
        # Dadalus TODO:
        #   Build a .sh script that will do `daedalus run <ddl_file> -i <testcase_msg.bin>` for each bin file
        #    in the supplied testcase directory

        self.log.info("Generate a test script that iterates over all the testcases in the provided testcase dir")

        results_file = os.path.join(testcase_dir, gen_util.results_filename)
        test_messages = list()
        with open(results_file) as f:
            for line in f.readlines():
                split_line = line.strip().split(' - ')
                filename = split_line[0]
                validity = split_line[1]
                valid = validity == 'valid'
                self.log.info("Generating a (%s) TestMessage instance" % (valid))
                self.log.info("Derrived from validation = %s" % (validity))
                tm = TestMessage(filename, valid, testcase_dir)
                test_messages.append(tm)

        testcase_name = os.path.basename(os.path.dirname(testcase_dir))
        testfile_filepath = os.path.join(self.test_directory, testcase_name + '.sh')
        testfile_filepath = os.path.abspath(testfile_filepath)
        parser_filepath = os.path.join(self.output_directory, self.protocol_name + '.ddl')
        parser_filepath = os.path.abspath(parser_filepath)
        testfile_text = '#!/usr/bin/env bash\n'
        testfile_text += 'rv=0\n\n'
        for tm in test_messages:
            tm_filepath = os.path.abspath(os.path.join(testcase_dir, tm.filename))
            testfile_text += 'daedalus run %s -i %s > /dev/null\n' % (parser_filepath, tm_filepath)
            testfile_text += 'rv=`expr $rv + $?`\n\n'

        testfile_text += 'exit ${rv}'

        # make test directory inside daedalus dir
        if not os.path.isdir(self.test_directory):
            os.makedirs(self.test_directory)

        with open(testfile_filepath, 'w') as f:
            f.write(testfile_text)

        st = os.stat(testfile_filepath)
        os.chmod(testfile_filepath, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        return [testfile_filepath]

    def run_test_from_testcase(self, testcase_dir, protocol_dir):
        testcase_name = os.path.basename(os.path.dirname(testcase_dir))
        testfile_filepath = os.path.join(self.test_directory, testcase_name + '.sh')

        self.log.info("Running test %s" % (testfile_filepath))
        rv = subprocess.call([testfile_filepath], shell=True, stdout=None)
        self.log.info("Test executed with return code=%d" % (rv))

        return rv


    @staticmethod
    def get_setup_directory():
        filepath = os.path.dirname(os.path.realpath(__file__))
        return os.path.join(filepath, 'setup_data')

    @staticmethod
    def get_setup_directory_name():
        return 'daedalus'

class Declaration:
    ''' This class holds all of the logic and data for generating a Daedalus Declaration.
    Ex:
        def Main =
            block
                <Statement>
                <Statement>
    '''

    def __init__(self, name, statements):
        self.name = name
        self.statements = statements

    def add_statement(self, statement):
        ''' Append a single statement to the list of statements owned by this Delcaration object '''
        if isinstance(statement, list):
            raise TypeError("add_statement does not accept lists; consider using add_statements() instead")
        self.statements.append(statement)

    def add_statements(self, statements):
        ''' Append a list of statements to the list of statements owned by this Delcaration object '''
        if not isinstance(statements, list):
            raise TypeError("add_statements can only accept lists; consider using add_statement() instead")
        self.statements.extend(statements)

    def as_text(self):
        ''' Format the Declaration as it would appear in-line of a daedalus source code file '''
        body = ''
        for s in self.statements:
            body += '        %s\n' % s
        ret = '''def {name} =
    block
{body}\n'''.format(name=self.name, \
                         body=body)

        return ret

#class Statement:
#    def __init__(self):
#        pass
#
#class RangeStatement(Statement):
#    def __init__(self):
#        pass
#
#class ChoiceStatement(Statement):
#    def __init__(self):
#        pass
#
#class ListStatement(Statement):
#    def __init__(self):
#        pass

class Function(Declaration):
    ''' This class holds all of the logic and data for genearting a Daedalus Function.
    Ex:
        def addNumber ret a b =
            a + b
    '''

    def __init__(self, name, statements, arg_names):
        super().__init__(name, statements)
        self.arg_names = arg_names

    def as_text(self):
        ''' Format the Function as it would appear in-line of a daedalus source code file '''
        arg_names_str = ' '.join(self.arg_names)
        body = ''
        for s in self.statements:
            body += '    %s\n' % s
        ret = '''def {name} {arg_names} =
    {body}\n'''.format(name=self.name, \
                     arg_names=arg_names_str, \
                     body=body)

        return ret
