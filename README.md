         ===========================================================
         |                                                         |
         |                                    __          __       |
         |        ____  _____ _____________  / /   ____  / /_      |
         |       / __ \/ __  / ___/ ___/ _ \/ /   / __ `/ __ \     |
         |      / /_/ / /_/ / /  (__  )  __/ /___/ /_/ / /_/ /     |
         |     / ,___/\__,_/_/  /____/\___/_____/\__,_/_.___/      |
         |    /_/                                                  |
         |                                                         |
         ===========================================================

# What is parseLab

"parseLab" is the name of a tool/framework created by Lockheed Martin ATL which is designed to generate protocol parsers, fuzz protocol messages, and provide the services necessary for building custom protocol parser generators.
The tool portion of parseLab is what allows the user to:

* generate parsers with native parser generators and parsing libraries
* generate valid messages according to a target protocol
* generate invalid messages according to a target protocol

The framework portion of parseLab is what allows the user to build custom protocol generators for parsing libraries that are not yet defined by parseLab.

Currently, parseLab ships with support for generating parsers using the [Hammer C-library](https://github.com/UpstandingHackers/hammer), and the [Daedalus Data Definition Language](https://github.com/GaloisInc/daedalus).
*Note: The Daedalus generator module is very much a limited portion of the Daedalus language.*
The Hammer generator module can, and should, be used as an example for any custom generator modules that a user might want to create.

# What is a parseLab Generator Module?

A guide for walking through the process of building a custom generator module can be found [here](docs/creating_custom_generator_modules.md).

The generator modules are really the heart of the parseLab system, without them, very little can be done with parseLab.
Each of the parseLab Generator Modules are to be derived from the [ParselabGenerator class](generators/ParselabGenerator.py) in order to properly function inside of the parseLab framework.
This `ParselabGenerator` class provides the interface functions that the rest of parseLab will leverage.
When creating a custom generator, the user will overload these interface functions with their own logic.

These generator modules are what hold all of the logic for generating the source code to make parsers for a target parsing library/language along with the logic for generating and running source code which passes in message data into the generated parser.

The interface functions that are defined in the generator modules have a very loose set of requirements.
Since we are not capable of knowing all of the quirks of every target parsing language/library, we have simply written a system that provides the user with as much information necessary to go forth and build a parser code generator.


# Installing parseLab

There are only a few dependencies for parselab-proper, while the dependencies for the natively supported generator modules are slightly more involved.

As a result, the [install guide](docs/install_guide.md) splits up the installation process based on the desired support.

For example, if you would like to only leverage the message generation aspect of parseLab, you don't need to install anything for the generator modules.
Similarly, if you would like to only generate parsers for the Hammer C-library, you can just follow the parseLab and Hammer installation steps.

# Guides/Walkthroughs

For a full understanding of parseLab, it is reccomended to follow the parseLab guides in the following sequence:

1. [Install Guide](docs/install_guide.md)
    - Successful installation allows for following the rest of the guides
2. [Creation of a Protocol Specification File with UDP](docs/UDP_protocol_specification.md)
    - Data is passed into parseLab through protocol specification files
    - The UDP format is a simple format that is easily understood as a first attempt at creating a protocol specification file
3. [Using the UDP Protocol Specification to Generate UDP Messages](docs/UDP_testcase_generation.md)
    - With a completed UDP protocol specification, it is now possible to generate valid and invalid instances of UDP messages
4. [Creation of a Protocol Specification File with MAVLink](docs/MAVLink_protocol_specification.md)
    - Learn more about the functionality of the protocol specification file while creating a new specification for the MAVLink protocol
5. [Using Custom Structs in a Protocol Specification File](docs/structs_in_protocol_specification.md)
    - Learn how to expand the capabaility of the protocol specification through the use of custom struct definitions.
6. [Creating a Custom Generator Module with Hammer's Python Bindings](docs/creating_custom_generator_modules.md)
    - With the understanding of what parseLab is capable of with existing generator modules, creating one for a new parsing library is now possible
7. [Understanding the Inner-Mechanisms of parseLab and Protocol Specification Files](docs/protocol_specification_architecture.md)
    - When creating a new generator module, it is important to understand the data that is being passed into the modules, this document goes into more details about this effort
8. [Creating a Semantic Parser with parseLab](docs/syntax_to_semantic_parser.md)
    - Go through the steps to generate a parseLab syntax parser and learn how to convert it to support semantic parsing

# Quick Start

For this section, it is assumed that the [Install Guide](docs/install_guide.md) was successfully completed for at least parseLab and Hammer.

```bash
# Start where parseLab was cloned
cd bin

# Ensure that the Hammer generator is passing all unit tests
./unit_tests.py --module hammer

# Generate a protocol directory for CAN with the files for Hammer
./setup.py --protocol ../protocols/can --module hammer

# Observe the new directory and its contents
ls ../protocols/can

# Copy the protocol specification from can example in the examples/ directory
cp ../examples/can/protocol.json ../protocols/can/protocol.json

# Remove the mission specification from the new can protocol directory
rm ../protocols/can/mission.json

# Generate a CAN parser using Hammer
./generate_parser.py --protocol ../protocols/can --module hammer

# Observe the generated code
less ../protocols/can/hammer/out/src/parser.c

# Generate a testcase consisting of 10 valid CAN messages
./generate_testcase.py --protocol ../protocols/can --msg_count 10 --valid --name myTest

# Observe the generated CAN messages
less ../protocols/can/testcases/myTest/myTest.xxd

# Generate test code for the new testcase
./generate_test.py --protocol ../protocols/can --module hammer --testcase ../protocols/can/testcases/myTest

# Observe the generated test code
less ../protocols/can/hammer/out/tests/myTest/src/test.c

# Run the generated parser against the generated testcase code
./run_test.py --protocol ../protocols/can --module hammer --testcase ../protocols/can/testcases/myTest
```

If everything went well, all 10 test messages should have successfully been "correctly accepted by parser".



-------------------------------------------------------------------------------

ACKNOWLEDGMENT
This material is based upon work supported by the Defense Advanced Research Projects Agency (DARPA) under Contract No. HR0011-19-C-0077.
Any opinions, findings and conclusions or recommendations expressed in this material arethose of the author(s) and do not necessarily reflect the views of the Defense Advanced Research Projects Agency (DARPA).

Distribution Statement "A" (Approved for Public Release, Distribution Unlimited).
