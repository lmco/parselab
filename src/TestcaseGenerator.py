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


''' TestcaseGenerator.py contains all of the functions and classes necessary to generate testcases which are
composed of series of fuzzed (invalid/valid) protocol messages using the chosen protocol specification'''

import os
import random

from src.ParselabLogger import ParselabLogger
from src.PacketGenerator import PacketGenerator
from src.utils import gen_util

class TestcaseGenerator:
    ''' TestcaseGenerator is responsible for generating a series of valid/invalid messages that either conform
    or DO NOT conform the supplied protocol and mission specifications '''

    def __init__(self, protocol_dir, logger=None):
        self.log = logger
        if self.log is None:
            self.log = ParselabLogger(print_logs=False)

        self.protocol_dir = protocol_dir
        self.packet_generator = PacketGenerator(protocol_dir, self.log)

    def generate_testcase(self, valid, msg_count, name, one_per=False):
        ''' Generate a single test case that is either valid or invalid and consists of <msg_count> messages
        param       bool:valid          Should the generated test be accepted or rejected by the parser
        param       int:msg_count       Number of messages that this testcase should consist of
        param       bool:one_per[False] Should the generated test consist of one message per defined in the \
                                         protocol spec instead of based on the msg count variable
        return      str:testcase_dir    The path to the generated testcase directory
        '''
        valid_prefix = 'n in' if not valid else ' '
        msg_count_str = "one packet per message" if msg_count == 0 else "%d messages" % msg_count
        self.log.info("Generating a%svalid testcase with %s named: %s" % (valid_prefix, msg_count_str, name))

        spec_data = self.packet_generator.spec_data
        msg_types = spec_data.message_types
        testcase = Testcase(name)

        list_to_generate = list()

        if one_per:
            list_to_generate = msg_types
        else:
            for _ in range(msg_count):
                list_to_generate.append(msg_types[random.randrange(0, len(msg_types))])

        for msg_type in list_to_generate:
            self.log.info("Attempting to generate a%svalid packet for message: %s" % (valid_prefix, msg_type.name))
            packet_data = self.packet_generator.generate_packet_from_msg(msg_type, valid)
            msg_bytes = packet_data[0]
            msg_size = packet_data[1]
            _valid = packet_data[2]
            invalid_info = packet_data[3]
            generated_msg = GeneratedMessage(msg_type, msg_bytes, msg_size, _valid, invalid_info)
            testcase.add_generated_msg(generated_msg)

        testcase_dirpath = self.create_testcase_dir(name, testcase)
        return testcase_dirpath

    def create_testcase_dir(self, testcase_name, testcase):
        ''' Create a new directory to hold the generated files for this testcase '''
        top_testcase_dir = os.path.join(self.protocol_dir, gen_util.testcase_dirname)
        if not os.path.isdir(top_testcase_dir):
            self.log.info("Creating new top level testcase directory (%s)" % (top_testcase_dir))
            os.mkdir(top_testcase_dir)

        new_testcase_dir = os.path.join(top_testcase_dir, testcase_name)
        if os.path.isdir(new_testcase_dir):
            err_msg = "Directory for testcase with name (%s) already exists!. Aborting" % (new_testcase_dir)
            self.log.error(err_msg)
            raise Exception(err_msg)

        os.mkdir(new_testcase_dir)

        testcase_xxd_filename = '%s.xxd' % testcase_name
        self.log.info("Generating the xxd-based testcase file (%s)" % (testcase_xxd_filename))
        testcase_xxd_path = os.path.join(new_testcase_dir, testcase_xxd_filename)
        testcase.generate_file(testcase_xxd_path)

        self.log.info("Generating all of the testcase's message binary files")
        testcase.generate_message_binary_files(new_testcase_dir)

        self.log.info("Generating the expected parse results file")
        testcase.generate_results_file(new_testcase_dir)

        return new_testcase_dir

class GeneratedMessage:
    ''' GeneratedMessage holds the contents and functions used to work with a single generated message '''
    def __init__(self, msg_type, msg_bytes, msg_size, valid, invalid_info=''):
        self.msg_type = msg_type
        self.msg_bytes = msg_bytes
        self.msg_size = msg_size
        self.valid = valid
        self.invalid_info = invalid_info

    def __str__(self):
        return PacketGenerator.hexdump_bytes(self.msg_bytes, self.msg_size)

    def __repr__(self):
        return self.__str__()

    def generate_binary_file(self, filepath):
        ''' Using the information in this class, generate a file that contains the bytes that represent this
        generated message '''
        hex_bytes = PacketGenerator.serialized_to_hex(self.msg_bytes, self.msg_size)
        padded_hex = gen_util.pad_hex_str(hex_bytes)
        binary = bytearray.fromhex(padded_hex)
        try:
            with open(filepath, 'wb+') as f:
                f.write(binary)
        except:
            raise Exception("Unable to generate a binary file")

class Testcase:
    ''' Testcase is responsible for containing all of the necessary properites and functions for a single test
    case '''
    def __init__(self, name):
        self.name = name
        self.messages = []

    def add_generated_msg(self, generated_msg):
        ''' Add a new generated message to this test case '''
        self.messages.append(generated_msg)

    def generate_filetext(self):
        ''' Create the text that will be placed into a file that represents this testcase '''
        file_text = ''
        for i, msg in enumerate(self.messages):
            file_text += '[VALID]' if msg.valid else '[INVALID]'
            file_text += ' %d %s' % (i, msg.msg_type.name)
            file_text += '\n'
            file_text += str(msg) + '\n\n'

        file_text = file_text.strip()
        return file_text

    def generate_file(self, filepath):
        ''' Generate a file at `filepath` which contains the information stored in this testcase class '''
        try:
            with open(filepath, 'w+') as f:
                f.write(self.generate_filetext())
        except:
            raise Exception("Unable to generate testcase file")

    def generate_message_binary_files(self, testcase_dir):
        ''' Generate a single binary file for each of the messages contained in this test case '''
        for i, msg in enumerate(self.messages):
            index = str(i).zfill(4)
            filename = '%s_%s%s' % (index, msg.msg_type.name, gen_util.test_message_extension)
            path = os.path.join(testcase_dir, filename)
            msg.generate_binary_file(path)

    def generate_results_file(self, testcase_dir):
        ''' Generate a results file that contains the results for all of the individual messages'
        expected parse result '''
        results_text = ''
        for i, msg in enumerate(self.messages):
            index = str(i).zfill(4)
            valid_str = 'valid' if msg.valid else 'invalid'
            invalid_info = (' - %s' % msg.invalid_info) if msg.invalid_info != '' else ''
            results_text += '%s_%s - %s%s\n' % (index, msg.msg_type.name, valid_str, invalid_info)

        results_text.strip()

        results_file = os.path.join(testcase_dir, gen_util.results_filename)
        try:
            with open(results_file, 'w+') as f:
                f.write(results_text)
        except:
            raise Exception("Unable to generate expected parse results file")

class TestMessage:
    ''' TestMessage is the class that is used to store information about a generated message when reading it from the
    test case directory's set of messages '''
    def __init__(self, basename, result, testcase_dir):
        self.basename = basename
        self.result = result
        self.filename = basename + gen_util.test_message_extension
        self.testcase_dir = testcase_dir
        self.filepath = os.path.join(self.testcase_dir, self.filename)
        self.bytes = self.get_bytes()

    def get_bytes(self):
        ''' Get the hex-format string which represents this message '''
        if os.path.isfile(self.filepath):
            with open(self.filepath, 'rb') as f:
                return f.read()

        return None
