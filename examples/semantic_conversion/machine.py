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


#!/usr/bin/env python3

'''
A Module containing the information for a Machine and Controller simulation
'''

import argparse
import ctypes
from machine_protocol import MEP

PARSE_PASS = 0
PARSE_FAIL = 1

# message IDS
message_ids = ['NOP', 'POWER_ON', 'POWER_OFF', 'START', 'STOP', 'PAUSE']
NOP = 0
POWER_ON = 1
POWER_OFF = 2
START = 3
STOP = 4
PAUSE = 5

# states
states = ['OFF', 'DEFAULT', 'RUNNING', 'PAUSED']
OFF = 0
DEFAULT = 1
RUNNING = 2
PAUSED = 3

class Machine:
    ''' This class holds the data and functionality for the 'Machine' that
    is interfaced with through the usage of the MEP (Machine Example
    Protocol) '''

    def __init__(self, uid, use_parser):
        self.state = OFF
        self.uid = uid
        self.parser = ctypes.CDLL("libparser.so")
        self.use_parser = use_parser

    def consume_message(self, msg):
        ''' The machine will consume 'msg' and change its state accordingly,
        but first it needs to pass the message through the parser if
        PARSER_ACTIVE == True'''

        if self.use_parser:
            ret = self.parser.semantic_parse(msg, len(msg))
            if ret == PARSE_FAIL:
                print("Machine:    DROPPING PACKET - PARSE FAILURE")
                return
        mep_msg = MEP.unpack(msg)
        mid = mep_msg.message_id

        if mid == NOP:
            print("Machine:      Recv: NOP")
        elif mid == POWER_OFF:
            print("Machine:      Recv: POWER_OFF")
            self.state = OFF
        elif mid == POWER_ON:
            print("Machine:      Recv: POWER_ON")
            self.state = DEFAULT
        elif mid == START:
            print("Machine:      Recv: START")
            self.state = RUNNING
        elif mid == STOP:
            print("Machine:      Recv: STOP")
            self.state = DEFAULT
        elif mid == PAUSE:
            print("Machine:      Recv: PAUSE")
            self.state = PAUSED

        print("Machine:      New state: %s" % states[self.state])
        return

class Controller:
    ''' This class interacts with the Machine and tells it what to do by
    sending it MEP messages '''

    def __init__(self, machine, uid):
        self.machine = machine
        self.uid = uid

    def send_mep_message(self, mep):
        ''' Send a MEP message to the machine '''
        print("Controller: Sending %s" % (message_ids[mep.message_id]))
        self.machine.consume_message(mep.serialized)

def main():
    '''Main Execution Function'''
    parser = argparse.ArgumentParser(description="Machine simulation for MEP protocol")
    parser.add_argument('--parse', action='store_true', help='Should the Machine use the parser?')
    args = parser.parse_args()

    machine = Machine(3, args.parse is not None)
    controller = Controller(machine, 16)

    # Create message instances
    nop_msg = MEP(NOP, controller.uid, machine.uid)
    power_on_msg = MEP(POWER_ON, controller.uid, machine.uid)
    power_off_msg = MEP(POWER_OFF, controller.uid, machine.uid)
    start_msg = MEP(START, controller.uid, machine.uid)
    stop_msg = MEP(STOP, controller.uid, machine.uid)
    pause_msg = MEP(PAUSE, controller.uid, machine.uid)

    controller.send_mep_message(power_on_msg)
    controller.send_mep_message(pause_msg)
    controller.send_mep_message(start_msg)
    controller.send_mep_message(pause_msg)
    controller.send_mep_message(stop_msg)
    controller.send_mep_message(power_off_msg)
    controller.send_mep_message(nop_msg)



if __name__ == '__main__':
    main()
