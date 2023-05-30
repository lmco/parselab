#!/usr/bin/env bash
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


SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
PARSELAB_TOP=$SCRIPTPATH/../
BIN=$PARSELAB_TOP/bin

pushd .
cd $BIN

python3 ./unit_tests.py --module hammer
python3 ./setup.py --protocol ../protocols/can --module hammer
cp ../examples/can/protocol.json ../protocols/can/protocol.json
rm ../protocols/can/mission.json
python3 ./generate_parser.py --protocol ../protocols/can --module hammer
python3 ./generate_testcase.py --protocol ../protocols/can --name myTest --msg_count 10 --valid
python3 ./generate_test.py --protocol ../protocols/can --module hammer --testcase ../protocols/can/testcases/myTest
python3 ./run_test.py --protocol ../protocols/can --module hammer --testcase ../protocols/can/testcases/myTest

popd
