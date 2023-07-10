# How to make a parseLab Protocol Specification file for UDP

The reference for UDP that we will use for this can be found [here](https://en.wikipedia.org/wiki/User_Datagram_Protocol#UDP_datagram_structure).
The only difference between our implementation and the one linked is that we are going to add a data field to the end of it.
Ignoring any application layer data, this UDP format is really straight forward to implement in parseLab.

## UDP Format

The format we are following has five fields: Source Port, Destination Port, Length, Checksum, and Data.
Except for the data field, all fields are 16-bit unsigned integers.

The Data field is a byte array where the length of it will correspond to the value found in the Length field.
This means that the Data field has a dependency on the Length field, thus making the Length a "dependee" field.

The Length field is also interesting because it has an additional constraint on it where its value must be between 1 and 512.
Because of this, while parsing the messages, we will have to add a constraint for the consumed value.


## Where do you write the Protocol Specification file?

Before a protocol specification file can be written, you must run the setup script found in the bin directory.
The setup script will build out something we refer to as a "Protocol Directory".

The protocol directory is essentially just where all of parseLab's output will go to when working with a target protocol.
Since parseLab is a framework that can handle having multiple generator modules which target different parsing backends, there will be sub-directories which contain all of the data generated/used by a specific generator module.

We found it good to have this protocol directory nearby, so we leverage parselab/protocol to store all of our generated protocol directories.

In our examples, we mostly will use the [Hammer library created by Special Cirumstances](https://github.com/UpstandingHackers/hammer).
Hammer is a parsing library for the C language, so all of the generated code for our examples using it will be written in C.
Since we are using Hammer, this setup script will create the nessary file structure for parseLab to generate code for Hammer.

```bash
# Change directory to get to the top of the parseLab repo
cd ${PARSELAB_REPO}

# Must be in the parselab/bin directory to execute the driver scripts
cd bin

# Create the Protocol Directory for UDP, with a specific target for Hammer
./setup.py --protocol ../protocols/udp/ --module hammer
```

After running the above commands, the following files and directories will be formed:

```bash
ls ../protocols/udp
> hammer protocol.json
```

In our case, we only want to talk abut the protocol.json right now.

## Writing a Protocol Specification file

Now that we have a protocol.json file to work with, we can start editing it with the information about UDP.
On first open of the protocol.json file, we can observe the following contents:

```json
{
    "protocol_types": [

    ]
}
```

The object `protocol_types` will be a list of all of the message types found in the target protocol.
In the case of UDP, there is only a single message type, so we will have a list of size one.

To begin, we will create a new object in the list and start defining the UDP message format.
Every message type object will consist of at least two sub-objects: `name`, and `fields`.
The `name` object is just the name of the message that you are describing (this would make a little more sense if there were more message types than just the one)
The `fields` object is a list of all the fields that define the messaqge type you are describing.

```json
{
    "protocol_types": [
        {
            "name": "UDP_MESSAGE",
            "fields" : [

            ]
        }
    ]
}
```

The `fields` list contains one or many objects that describe each of the fields in the target message type.
In our case, UDP, we have 5 fields: `SOURCE_PORT`, `DESTINATION_PORT`, `LENGTH`, `CHECKSUM`, `DATA`.
The `SOURCE_PORT`, `DESTINATION_PORT`, `LENGTH`, and `CHECKSUM` fields are all unsigned 16-bit integers, while `DATA` is an array of unsigned 8-bit integers.
In parseLab, we describe these two data types like U16 and U8[].
So now we will add those in to the list of fields.

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
                    "type": "U16"
                },
                {
                    "name": "CHECKSUM",
                    "type": "U16"
                },
                {
                    "name": "DATA",
                    "type": "U8[]"
                }
            ]
        }
    ]
}
```

Each field has at least two object attributes: `name` and `type`, which are the only required attributes.
However, there are multiple other attributes that we can apply to these.
In fact, the user can put any attribute on any message, or field object, and parseLab will provide that data to the user for use in a custom generator module.
For now, we will only focus on two other attributes.
First, we will look at the `value` attribute.  

The Value attribute is used for special constraints that limit the range of possible values to more than what is defined by the `type` attribute.
As we discussed in the first section, the Length field of a UDP message is limited to values between 1 and 512.
To define this constaint in parseLab, we can modify the `LENGTH` field's object to have a `value` attribute.

The `value` attribute that we are adding is for a range constraint.
A range constraint is defined with an open parenthesis '(', followed by a comma separated pair of integers, followed by a closed parenthesis ')'.
The range constraint is always inclusive ranges, so since we are working with numbers from 1 to 512, we would format our `value` attribute as follows:

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
                    "value": "(1,512)"
                },
                {
                    "name": "CHECKSUM",
                    "type": "U16"
                },
                {
                    "name": "DATA",
                    "type": "U8[]"
                }
            ]
        }
    ]
}
```

We aren't done with the `LENGTH` field yet though; since the field is used as a dependee for the `DATA` field's array defintion, we need to add the `dependee` attribute also.
This `dependee` attribute tells pareLab that the result found in this value is relevant for the parser generation of another field.

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
                    "type": "U8[]"
                }
            ]
        }
    ]
}
```

Since the `LENGTH` field is now defined such that it expects a reference, we can now add that reference to the `DATA` field that is dependant on the `LENGTH` value.

In parseLab, we can specify an array with either a reference to another field, or an unsigned integer value.
In this case, we are using the reference option, but in another examples we wil explore the use of a constant integer.

To do this, we will modify the array definition of the `DATA` field's type by adding the name of the dependee field in the bounds of the array brackets:

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

With this final step, we are now done and our protocol spefication is ready to be processed for parser or message generation.

## Testing the new protocol specification file

To verify that this protocol specification was written properly, we can run it through the `generate_parser.py` script.
If we are able to generate a parser with no errors, then our protocol specification file was successful!

```bash
# Go to the parselab/bin directory
cd ${PARSELAB_REPO}/bin

# Make sure that the unit tests pass for the Hammer module if this is the first time
#   running against it
./unit_tests.py --module hammer

# Run the parser generator script
./generate_parser --protocol ../protocols/udp --module hammer
```

If this was able to run without errors, then your protocol specification file was created properly!
To run tests against this generated parser, we will run through how to use the Testcase Generator in [another tutorial](docs/UDP_testcase_generation.md).
