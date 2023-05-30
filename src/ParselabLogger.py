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


''' The ParselabLogger Module contains all classes and functions necessary to
facilitate the needs of the centralized logger for the parseLab framework. '''

import inspect
import logging
import os
import time

class ParselabLogger:
    ''' The ParselabLogger is designed to sync logging across instantiations of
        various classes within the parseLab framework.  Rather than each class
        piping its logging to a different file, this class is designed to hold
        a centralized log which all of the parseLab classes can write to. '''

    def __init__(self, log_dir='/tmp/parselab/', log_name='parselab', use_time=True, \
                       ext='.log', print_logs=False, create_log=True):
        self.mute = not create_log
        self.log_dir = log_dir
        self.log_name = log_name
        self.use_time = use_time
        self.print_logs = print_logs
        if self.mute:
            return
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)
        log_file = os.path.join(log_dir, log_name)
        if use_time:
            str_time = str(int(time.time()))
            log_file = '%s_%s' % (log_file, str_time)
        self.log_file = log_file + ext

        logging.basicConfig(filename=self.log_file, \
                            filemode='w', \
                            format="%(asctime)s - %(message)s", \
                            level=logging.DEBUG)
        print("Created log file: %s" % (self.log_file))

    @staticmethod
    def get_caller_function_name():
        ''' This is used to get the name and other information from the stack
            which lead to the current stack frame. '''
        curr_frame = inspect.currentframe()
        caller_frame = inspect.getouterframes(curr_frame, 2)[5]
        func_module = inspect.getmodule(caller_frame[0]).__name__
        if func_module == '__main__':
            func_module = os.path.basename(inspect.getmodule(caller_frame[0]).__file__)
        func_name = caller_frame[3]
        line_num = caller_frame[2]
        return "%s::%s:%s" % (func_module, func_name, str(line_num))

    def check_print(func):
        ''' Decorator used to determine if the logger should pipe the logs
            to the terminal '''
        def inner(*args, **kwargs):
            self = args[0]
            log_msg = func(*args, **kwargs)
            if self.print_logs and log_msg is not None:
                print(log_msg)
        return inner

    def check_mute(func):
        ''' Decorator used to determine if the logger should pipe the logs
            to the output file '''
        def inner(*args, **kwargs):
            self = args[0]
            if not self.mute:
                return func(*args, **kwargs)
            return None
        return inner

    @staticmethod
    def create_log_msg(msg, log_type):
        ''' Static Function for logging a message based on its log type. '''
        return "(%s) [%s] %s" % (log_type, ParselabLogger.get_caller_function_name(), msg)

    @check_print
    @check_mute
    def info(self, msg):
        ''' Log an info-level message '''
        log_msg = ParselabLogger.create_log_msg(msg, 'INFO')
        logging.info(log_msg)
        return log_msg

    @check_print
    @check_mute
    def error(self, msg):
        ''' Log an error-level message '''
        log_msg = ParselabLogger.create_log_msg(msg, 'ERRO')
        logging.error(log_msg)
        return log_msg

    @check_print
    @check_mute
    def warn(self, msg):
        ''' Log a warning-level message '''
        log_msg = ParselabLogger.create_log_msg(msg, 'WARN')
        logging.warning(log_msg)
        return log_msg
