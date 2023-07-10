# How to make a parseLab Protocol Specification File for MAVLink

This guide is designed to provide additional information about the protocol specification file than the [UDP protocol specification guide](./UDP_protocol_specification.md) and should be treated as a part 2 to be completed after that guide.

The UDP guide is helpful to get up and running with the basics of parseLab, but this document will explore a couple of features that parseLab provides to aid in the generation of tests and parsers.
These features will be in the form of additional attributes in the JSON objects that make up the message and field specifiactions.

### Building the MAVLink Specification

We will start with just creating a protocol directory and `protocol.json` for MAVLink.

```bash
# From parselab/bin
./setup.py --protocol ../protocols/mavlink
```

As we create the `protocol.json`, we will use the [MAVLink documentation](https://mavlink.io/en/messages/common.html) for reference.
If we visit the MAVLink documentation, we can see that there are over 100 messages defined, for simplicity, we will just define:

* [HEARTBEAT](https://mavlink.io/en/messages/common.html#HEARTBEAT)
* [PARAM_SET](https://mavlink.io/en/messages/common.html#PARAM_SET)
* [COMMAND_LONG](https://mavlink.io/en/messages/common.html#PARAM_SET)

If we take a look at the documentation for each message type, the associated table is not the entire payload of the message; it is omitting a header structure that is prepended to all MAVLink messages.

The header is as follows:

| Field Name | Type | Value Constraint |
|------------|------|------------------|
| MAGIC | U8 | 253 or 254 |
| LENGTH | U8 | X |
| ICOMP | U8 | |
| COMP | U8 | |
| SEQ | U8 | |
| SYSID | U8 | |
| COMPID | U8 | |
| MSG_ID | U24 | X |

Take note of the value constaints for each of these fields.
Starting with the `MAGIC` field, we can see a value constraint of 253 or 254, but we have seen this type of constraint with the UDP guide.
Next we see that `LENGTH` and `MSG_ID` have an X for their value constraint.
There are some fields in the header that are constants for certain message types; these X's represent those fields.
Next is the fields without a value constaint, meaning that the parser will just parse for N many bits that make up this field with no regard for their values.

We'll start with the HEARTBEAT message.

#### Heartbeat Message Specification

| Field Name | Type | Value Constraint |
|------------|------|------------------|
| MAGIC | U8 | 253 or 254 |
| LENGTH | U8 | *9* |
| ICOMP | U8 | |
| COMP | U8 | |
| SEQ | U8 | |
| SYSID | U8 | |
| COMPID | U8 | |
| MSG_ID | U24 | *0* |
| TYPE | U8 | (0, 42) |
| AUTOPILOT | U8 | (0, 20) |
| BASE_MODE | U8 | 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40 or 0x80 |
| CUSTOM_MODE | U32 | |
| SYSTEM_STATUS | U8 | (0, 8) |
| MAVLINK_VERSION | U8 | |

Notice that we prepended the table with the information from the MAVLink header, but we added the correct values for `LENGTH` and `MSG_ID` that correspond to the HEARTBEAT message.
The values that we are getting for the value constaints come from the enumerated values found on the MAVLink docs.

Lets go through and make each one in the `protocol.json`.
First setup the HEARTBEAT message:

```json
{
    "protocol_types": [
        {
            "name": "HEARTBEAT",
            "fields": [

            ]
        }
    ]
}
```

And now lets start filling in each of the fields:

```json
"fields": [
    {
        "name": "MAGIC",
        "type": "U8",
        "value": "253|254"
    }
]
```

Quick pause to point out the way that we handle the choice operation for value constaints that can allow for different values; here, we are defining "253 or 254" as "253|254".
You can learn more about different ways of using the choice operator in the [generic protocol specification guide](./protocol_specification_architecture.md).

Now moving onto the definition of the next few fields that don't need a call-out, as they are basics as described in the UDP guide.

```json
"fields": [
    {
        "name": "MAGIC",
        "type": "U8",
        "value": "253|254"
    },
    {
        "name": "LENGTH",
        "type": "U8",
        "value": "9"
    },
    {
        "name": "ICOMP",
        "type": "U8"
    },
    {
        "name": "COMP",
        "type": "U8"
    },
    {
        "name": "SEQ",
        "type": "U8"
    },
    {
        "name": "SYSID",
        "type": "U8"
    },
    {
        "name": "COMPID",
        "type": "U8"
    },
    {
        "name": "MSG_ID",
        "type": ">U24",
        "value": "0"
    }
] 
```

We have now finished the header, but the interesting bit here is actually in the `MSG_ID` field specification.
This is the first time we have shown a value constraint on a multi-byte data type; as a result, we must discuss endianness.
In parseLab, the default is Big Endian, which means that if no endianness identifier (`<` or `>`) was found, it would assume Big Endian.
For our case here, since MAVLink orients its fields in a Big Endian format, it is a little redundant.
But given that it was the first time we handle a multi-byte field that we need to care about the dat for, it is relevant to bring up.

Now for the rest of the fields:

```json
"fields": [
    {
        "name": "MAGIC",
        "type": "U8",
        "value": "253|254"
    },
    {
        "name": "LENGTH",
        "type": "U8",
        "value": "9"
    },
    {
        "name": "ICOMP",
        "type": "U8"
    },
    {
        "name": "COMP",
        "type": "U8"
    },
    {
        "name": "SEQ",
        "type": "U8"
    },
    {
        "name": "SYSID",
        "type": "U8"
    },
    {
        "name": "COMPID",
        "type": "U8"
    },
    {
        "name": "MSG_ID",
        "type": "U24",
        "value": "0"
    },
    {
        "name": "TYPE",
        "type": "U8"
        "value": "(0,42)"
    },
    {
        "name": "AUTOPILOT",
        "type": "U8"
        "value": "(0,20)"
    },
    {
        "name": "BASE_MODE",
        "type": "U8"
        "value": "0x01 | 0x02 | 0x04 | 0x08 | 0x10 | 0x20 | 0x40 | 0x80"
    },
    {
        "name": "CUSTOM_MODE",
        "type": "U8"
    },
    {
        "name": "SYSTEM_STATUS",
        "type": "U8"
        "value": "(0,8)"
    },
    {
        "name": "MAVLINK_VERSION",
        "type": "U8"
        "comment": "Don't want to limit the version with this parser"
    }
] 
```

I have added an attribute to the field definition for `MAVLINK_VERSION` that we have not explored yet.
This attribute actually isn't even known to parseLab.
The parseLab system that processes the specification files will consume any and all attributes on the field or message specifications.
If parseLab recognizes the attribute, it will process it accordingly.
If parseLab does NOT recognize the attribute, it will save it in a dictionary of `custom_data` on the `FieldDef` object.
This custom data gets passed into the generator modules (see [Creating a Custom Generator Module](./creating_custom_generator_modules.md) for more information about generator modules) in the event that a backend needs more data than what parseLab natively provides.
In this case, we used the `comment` attribute to just hold some information that would be useful to the next reader.

At this point, we have now completed the specificaiton for the `HEARTBEAT` message.
Repeating this process for the `PARAM_SET` and `COMMAND_LONG` messages is the next step.

#### Param Set Message Specification 

`PARAM_SET` fields

| Field Name | Type | Value Constraint |
|------------|------|------------------|
| MAGIC | U8 | 253 or 254 |
| LENGTH | U8 | 23 |
| ICOMP | U8 | |
| COMP | U8 | |
| SEQ | U8 | |
| SYSID | U8 | |
| COMPID | U8 | |
| MSG_ID | U24 | 23 |
| TARGET_SYSTEM | U8 | |
| TARGET_COMPONENT | U8 | |
| PARAM_ID | CHAR[16] | |
| PARAM_VALUE | FLOAT | |
| PARAM_TYPE | U8 | (1,10) |

This is the first time that we are trying to parse a `CHAR` in the protocol specification guides.
Since a `char` is the same thing as an unsigned 8-bit integer, any time that a char is used, it is safe to replace it with a `U8` in the protocol specification file.
We are also seeing an array definition with a constant length associated to it.
The `char[16]`, or `U8[16]` once the char is resolved, is just saying that this field will have be parsed as a sequence of 16 unsigned 8-bit intgers with no regard for any of their values.
For the purpose of this guide, lets put a value constraing on this field.
We will pretend that this field needs its `char[16]` array to look like `"abcdefghijklmnop"` and write the field specification accordingly.

Here is the JSON format for the `PARAM_ID` field, since it is the only field with a new concept:

```json
{
    "name": "PARAM_ID",
    "type": "U8[16]",
    "value": "[a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p]"
}
```

#### Command Long Specification

`COMMAND_LONG` fields

| Field Name | Type | Value Constraint |
|------------|------|------------------|
| MAGIC | U8 | 253 or 254 |
| LENGTH | U8 | 33 |
| ICOMP | U8 | |
| COMP | U8 | |
| SEQ | U8 | |
| SYSID | U8 | |
| COMPID | U8 | |
| MSG_ID | U24 | 76 |
| TARGET_SYSTEM | U8 | |
| TARGET_COMPONENT | U8 | |
| COMMAND | U16 |  |
| CONFIRMATION | U8 | |
| PARAMS | F32[7] | |

I picked this one to show off the use of the `F32` data type, which represents a 32-bit float.
At this time, parseLab can only support floats using the IEEE 754 representation for a 32-bit floating point number.
Much like the last message specification, I am going to create a superficial value constraint on this field for sake of demonstrating parseLab features.

Let's add a value constraint that says that each float in the list must be between (i * 10, i * 10 + 5.0) where i is the index of the list.
Unforunately, at this time, parseLab does not support arithmatic in the protocol specification file, but we can do this by hand.

| Index | Range |
|-------|-------|
| 0 | (0, 5) |
| 1 | (10, 15) |
| 2 | (20, 25) |
| 3 | (30, 35) |
| 4 | (40, 45) |
| 5 | (50, 55) |
| 6 | (60, 65) |

Since the rest of the fields don't contain new concepts, I will just write out the JSON for the `PARAMS` field with our superficial value constraint.

```json
{
    "name": "PARAMS",
    "type": "F32[7]",
    "value": "[(0, 5),(10, 15),(20, 25),(30, 35),(40, 45),(50, 55),(60, 65)]"
}
```

This shows that we are able to nest value some value constraints into others.
In this case, we are nesting the ValueRange constraint into a ValueList constraint.
We could have put it inside of a ValueChoice constarint just as easily.
The limitations for this can be better understood by reading the [protocol specification guide](./protocol_specification_architecture.md)

Feel free to grab a completed version of this [MAVLink protocol specification](examples/tutorial_mavlink/1_protocol.json) in the `parselab/examples/tutorial_mavlink` directory, or go forward and attempt to write it yourself before we move to the next step.

#### The Strict Attribute

Sometimes when generating data, it can be convenient to force the fuzzer to ignore some fields when attempting to invalidate a message stucture.
Generating values for MAVLink is one of those times. 
Since MAVLink operates with a Message ID structure, if that value gets modified, your system may not recognize it as the correct message anymore.
It is often beneficial to know for a fact how your sytem handles weird versions of a particular message rather than seeing how your system handles a message that theorhetically doesn't exist (if the fuzzer modifes the Message ID to a value out of the set of all IDs).

That is what the `strict` attribute is for.

Before we apply it to the MALink protocol specification's `protocol.json` file, we will first run the testcase generator without it and observe all the fields that an invalid test may affect without the strict attribute.

To ensure that we will randomly get at least one attempt to modify the `MSG_ID` field, we will create an invalid testcase that creates 1000 messages, and look for how many times the `MSG_ID` field is modified.

```bash
# From parselab/bin
./generate_testcase.py --protocol ../protocols/mavlink --msg_count 1000 --invalid --name invalid_1000
> Created log file: /tmp/parselab/parselab_1682948124.log
> Successfully generated testcase (../protocols/mavlink/testcases/invalid_1000)

# Print the number of lines that the results.txt file told us that "MSG_ID" was the modified field
#  Note: This will be different for every testcase, but should be > 0
grep -o 'MSG_ID' ../protocols/mavlink/testcases/invalid_1000/results.txt | wc -l
> 240
```

When we ran the `MSG_ID` counter over the testcase's `results.txt` file, we saw that we had 240 times where the testcase modified the `MSG_ID` field to invalidate the message.
Now, lets apply the `strict` attribute to each of the `MSG_ID` fields.
Below is an example for the `HEARTBEAT` message, but make sure to add it to the other message's `MSG_ID` fields as well.

```json
{
    "name": "MSG_ID",
    "type": "U24",
    "value": "0",
    "strict": "true"
}
```

And running the same command as last time, except, this time we will use 1500 invalid messages:

```bash
# From parselab/bin
./generate_testcase.py --protocol ../protocols/mavlink/ --msg_count 1500 --invalid --name invalid_1500
> Created log file: /tmp/parselab/parselab_1682949161.log
> Successfully generated testcase (../protocols/mavlink/testcases/invalid_1500)

# Print the number of lines that the results.txt file told us that "MSG_ID" was the modified field
grep -o 'MSG_ID' ../protocols/mavlink/testcases/invalid_1500/results.txt | wc -l
> 0
```

If we scan through the `results.txt` of the second test, we see that there isn't a single instance of `MSG_ID` anymore.
This is because the `strict` attribute told parseLab that it can never use this field to generate an invalid message instance.

#### The Ignore Attribute

Sometimes while doing development, it can annoying having to debug with a json script as input since you cant "comment out" a json object.
This is where the `ignore` attribute comes into play.

The `ignore` attribute allows either a message specification block, or a field specification block, to be ignored by parseLab when processing the protocol spefication file.
Much like the `strict` tag, you can just pass it into the target message/field specification block.
Here is an example for how we would *ignore* the `HEARTBEAT`'s `MSG_ID` field, rather than making it strict:

```json
{
    "name": "MSG_ID",
    "type": "U24",
    "value": "0",
    "ignore": "true"
}
```

## Creating Custom Generators

Now that we have explored the space of making protocol specification, we can walk through the process of [building a custom parseLab generator module](./creating_custom_generator_modules.md).
