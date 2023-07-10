# The parseLab Testcase Generator (Fuzzer)

The parseLab Testcase Generator is a fuzzer which targets specific fields as defined by the supplied protocol specification.
A standard fuzzer will typically generate random strings of bytes; our fuzzer is capable of having the awareness of the correct format of a message and generating values which align, or don't align, to the fields which make up the message type.

We built our testcase system in a way that splits up the generation of test data and test code.
Test data is built with our TestcaseGenerator, while test code (the code which pulls the test data and runs it against a parser) is built with a specified parseLab generator module.
For now, we will just leverage the Testcase Generator, and not discuss any parseLab generator modules.

## Using the Testcase Generator

For this document, we are going to use the UDP protocol specification that we created in the [Protocol Specification guide](./UDP_protocol_specification.md):


```json
{
    "protocol_types": [
        {
            "name": "UDP_MESSAGE",
            "fields" : [
                {
                    "name": "SRC_PORT",
                    "type": "U16"
                },
                {
                    "name": "DEST_PORT",
                    "type": "U16"
                },
                {
                    "name": "LENGTH",
                    "type": "U16",
                    "value": "(1,512)",
                    "dependee": true
                },
                {
                    "name": "CHECKSUM",
                    "type": "U16"
                },
                {
                    "name": "DATA",
                    "type": "U8[LENGTH]"
                }
            ]
        }
    ]
}
```

To leveage the Testcase Generator, we will use the `bin/generate_testcase.py` driver script.
To use `generate_testcase.py` we will need to pass it a few required arguments: 

* `--protocol`
* `--name`
* `--valid/invalid`
* `--msg_count/one_per`.

## Generating a Valid Message

We are now going to be generating a single, valid, UDP message with the Testcase Generator.
To achieve this, we need to pass in a set of specific arguments to the driver script:

    * `--protocol ../protocols/udp`
        - This tells the driver that it needs to leverage the protocol specification as defined in the UDP directory
    * `--name valid_docs_test_1`
        - This creates a name for the testcase that you are going to generate; this can be anything except the name of an existing testcase
    * `--one_per`
        - This requests that the driver generate just one message instance for each message type defined in the protocol specification.  Since our protocol specifcation only defines a single message type, we know what that one instance is going to be
    * `--valid`
        - This requests that the driver generate a valid instance of all the messages that it will build


```bash
# Go to the bin directory of the parseLab cloned repo
cd ${PARSELAB_TOP}/bin

# Run the generate_tescase.py driver as follows:
./generate_testcase.py --protocol ../protocols/udp \
                       --name valid_docs_test_1 \
                       --one_per \
                       --valid
```

After running the commands, a new directory (`../protocols/udp/testcases/valid_docs_test_1` will be formed.
Inside this new directory will be the following files:

```bash
ls ../protocols/udp/testcases/valid_docs_test_1
> 0000_UDP_MESSAGE.bin  results.txt  valid_docs_test_1.xxd
```

### What makes up a Generated Testcase Directory?

In every generated testcase, there will always be a series of `.bin` files, along with a `results.txt` file and a `<testcase name>.xxd` file.

The series of `.bin` files contain a binary blob which makes up a single generated message.
The naming convention is as follows: `<uid>_<message type name>.bin`.
The naming convention shows a unique identifier, along with the name of the message type that this binary blob was generated to align with.

The `results.txt` file is simply a newline-separated list which denotes the validity of each message in the testcase directory.

In our case:: 

```bash
cat ../protocols/udp/testcases/valid_docs_test_1/results.txt
> 0000_UDP_MESSAGE - valid
```

The `<testcase name>.xxd` file, or in our case `valid_docs_test_1.xxd`, mainly is used to quickly view the generated messages in an xxd-style view.
The `.xxd` file depicts the validity, uid, message type, and contents (xxd-style) of every `.bin` file in the testcase directory.

In our case:

```bash
cat ../protocols/udp/testcases/valid_docs_test_1/valid_docs_test_1.xxd

> [VALID] 0 UDP_MESSAGE
> 00000000: 51 EE FD 61 00 17 ED FF  20 EE 69 6A 86 A1 DC 0C  Q..a.... .ij....
> 00000010: A9 A8 40 73 2D CC 78 8E  AF 52 7B DE C5 2B D7     ..@s-.x..R{..+.
```

## Generating a Set of Invalid UDP Messages

Previously, we created a single, valid, instance of a UDP message.
Now, we will go through the process of generating 15 invalid UDP messages so that we can observe the way that the fuzzer goes about generating an invalid message.

To do this, we will use the `generate_testcase.py` driver script again, but pass in different arguments.
The arguments we will use are as follows:

    * `--protocol ../protocols/udp`
        - Target the protocol specificaiton found in the UDP directory
    * `--name invalid_docs_test_1`
        - Create a testcase with the name `invalid_docs_test_1`
    * `--msg_count 15`
        - Generate 15 different messages.  It is important to note that if there are multiple message types defined in the protocol specificatoin, this will arbitrarily pick 15 random message types to generate messages for.  In our case, we only have the one type, so all 15 will be of our one type
    * `invalid`
        - This requests that the driver attempt to generate all messages as invalid.  NOTE: it is not guaranteed that a message type has the ability to be invalid!

```bash
# Go to the bin directory of the parseLab cloned repo
cd ${PARSELAB_TOP}/bin

# Run the generate_testcase.py driver as follows:
./generate_testcase.py --protocol ../protocols/udp \
                       --name invalid_docs_test_1 \
                       --msg_count 15 \
                       --invalid
```

After running the commands, a new directory (`../protocols/udp/testcases/valid_docs_test_1`) will be formed with the following contents:

```bash
ls ../protocols/udp/testcases/invalid_docs_test_1
> 0000_UDP_MESSAGE.bin  0001_UDP_MESSAGE.bin  0002_UDP_MESSAGE.bin  0003_UDP_MESSAGE.bin  0004_UDP_MESSAGE.bin  0005_UDP_MESSAGE.bin  0006_UDP_MESSAGE.bin  0007_UDP_MESSAGE.bin  0008_UDP_MESSAGE.bin  0009_UDP_MESSAGE.bin  0010_UDP_MESSAGE.bin  0011_UDP_MESSAGE.bin  0012_UDP_MESSAGE.bin  0013_UDP_MESSAGE.bin  0014_UDP_MESSAGE.bin  invalid_docs_test_1.xxd  results.txt
```

The stucture of this testcase directory is the same as the one generated when we requested a valid testcase above.
However, in this testcase, we can see that there are 15 messages - this is due to our `--msg_count 15` argument.

### Invaild Testcase Processing

Unlike the valid testcase above, the `results.txt` file has a little bit more information in it for an invalid testcase.
Messages which were able to be generated with invalid values/structures will have a couple more descriptors per line:

```bash
cat ../protocols/udp/testcases/valid_docs_test_1/results.txt
> 0000_UDP_MESSAGE - valid

head -n 1 ../protocols/udp/testcases/invalid_docs_test_1/results.txt
> 0000_UDP_MESSAGE - invalid - LENGTH - GREATER_THAN_BOUNDS
```

**NOTE: The contents of the `results.txt` will most likely be different for everyone, so ignore the exact values during this sub-section.**

As expected, the file will contain the unique name for each generated message, along with its validity (in this case `invalid`).
However, we can also see that there are two new fields shown: `LENGTH` and `GREATER_THAN_BOUNDS`.
The 3rd element in the '-' separated list denotes which field was "corrupted" to make the overall message not conform to the message type's format specification.
In this case, we see that generated message `#0000` has an invalid `LENGTH` field, and it was deemed invalid due to a `GREATER_THAN_BOUNDS` modification.
If we take a look at the format of the UDP message, the `LENGTH` field has a value constraint on it, which restricts the value of the `LENGTH` field to unsigned integers between 1 and 512.
In our testcase, we can see that the modifier `GREATER_THAN_BOUNDS` means that the fuzzer created a value for the `LENGTH` field which is greater than the bounds defined in the protocol specification.

#### Types of Invalid Fields

There are multiple types of invalid modifiers:

 * `GREATER_THAN_BOUNDS` - This field was generated to have a value that is greater than the supplied bounds (5, 25) => 26
 * `LESS_THAN_BOUNDS` - This field was generated to have a value that is less than the supplied bounds. Ex: (5, 25) => 4
 * `HIGH_LIST_LENGTH` - This field was generated to have more values in its array than was expected. Ex: U8[3] => [25, 91, 12, 83]
 * `LOW_LIST_LENGTH` - This field was generated to have less values in its array than was expected. Ex: U8[3] => [82, 66]
 * `INVALID VALUE` - This is a default descriptor and is a fallback in the event that the invalid modifier does not have a better description yet.
 * `VALID VALUE` - This field was not able to produce an invalid value, and fell back to being valid.

## Some Fields and Messages Can Never Be Invalid

Our goal is not to use this fuzzer to identify poorly formated data, but rather to identify seemingly valid data (aligns with protocol specification), but may have unintended consequences that would want to be noticed.
As a result, our testcase generator will always maintain the data type of the field, when creating a generated message's binary blob.
Because of this, there is not always a way to generate an invalid value for a field that does not have a value constraint.

### Invalid Fields

Since we maintain the correct size of all the fields when we generate data, consider the following field from the UDP specification and try to come up with a value that we could generate, which would be rejected by this description.

```json
{
    "name": "SRC_PORT",
    "type": "U16"
}
```

The provided field, `SRC_PORT` is an unsigned 16-bit integer, with no value constriants.
This means that *ANY* value, which is 16-bits long, can properly be defined by this field specification.
Because of this, when you inspect the `results.txt` file from the invalid testcase, you may notice that there are only two fields (`LENGTH` and `DATA`) which are generated as invalid.

This is because the `LENGTH` field has a value attribute (which gives the ability to find a value outside of the constrained set) and the `DATA` field is a list which means we are always cabale of either adding too many, or too little, elements to the list.

### Invalid Messages

Due to the impossiblity of generating an invalid field for certain field specifications, it also means that it can be impossible to generate an invalid message for certain message type specifications.
As our goal for this fuzzer is to maintain the syntactic correctness of a message definition while generating values, we also do not add or remove fields from a generated message, because then we believe that it can no longer be considered that message anymore.

Imagine the following, fictional,  message specification:

```json
{
    "name": "always_valid_message",
    "fields": [
        {
            "name": "always_valid_field_01",
            "type": "U8"
        },
        {
            "name": "always_valid_field_02",
            "type": "U4"
        },
        {
            "name": "always_valid_field_03",
            "type": "U12"
        }
    ]
}
```

Observing the 3 fields, where none of them are array data types, or have any value constraints, we can see that none of these fields can produce an invlaid value instance.
Since a message's validity is defined as the sum of the validity of each field (all fields valid = valid message; one field invalid = invalid message), we then can see that this message specifiation has no way of producing an invalid instance for it within our testcase.

## Using the Generated Data

At this point, we have properly generated both valid, and invalid, UDP messages that can be used for testing.
Because the output of this process is just a series of binary files, you are free to leverage them for whatever process you'd like.

In [another document](./UDP_test_generation.md) we will discuss how to leverage parseLab's test code generator which leverages the data produced in this document through the use of a specified parseLab generator module.
