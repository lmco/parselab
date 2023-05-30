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


''' GeneratedValue.py contains the necessary classes and functions for handling a value generated by
the parseLab framework '''

# This class is an object to define a valid/invalid value
class GeneratedValue():
    ''' GeneratedValue contains all of the properties and functions for storing information about a
    generated value which was generated by the parseLab framework '''
    def __init__(self, value_type, value, dtype):
        self.value_type = value_type
        self.value = value
        self.field = None
        self.dtype = dtype
        self.msg_type_name = ''

    def __str__(self):
        return "%s %s %s" % (self.field.name if self.field else '', self.dtype, self.value)

    def set_field(self, field):
        ''' Set the generated value's field (FieldDef) '''
        self.field = field

    def set_msg_type_name(self, msg_type_name):
        ''' Set the name of the message that this generated value is from '''
        self.msg_type_name = msg_type_name
