# Creating and Using Custom Structs in a Protocol Specification File

It is not always possible to create a protocol specification file while only using the primitive parseLab data types:
`unsigned int`, `int`, and `float`.
These times usually present themselves when the protocol requires a list of objects.
For example, if a protocol for a drone has a message which contains a list of waypoints and the information for the waypoint is contained in a struct, and the list of way points is variable.
In this guide, we will explore how to go about achieving this with a protocol specificaiton file.

## Custom Message Format

For this guide, we will be creating a protocol specification for a single `DRONE STATUS` message.
This status message will encode the following information:
 * Drone ID: One integer for the drone's ID number
 * Drone Velocity: Three floats for the drone's velocity in X, Y, Z axes
 * Drone Position: Three floats for the drone's GPS position
 * Drone Orientation: Three floats for the drone's yaw, pitch, and roll
 * Current Waypoint: One Integer for the type of the current waypoint, and three floats for the GPS position of it
 * Waypoints Loaded: One integer for the size of the Loaded Waypoints list
 * List of Loaded Waypoints: A variable list of waypoints which describe each waypoints type and position

## Creating the Drone Status Message without Structs

Before incorportating structs, lets attempt to make a protocol specification for this status message without custom structs.

### NOTE: At this point, it is assumed that the guide for [Creating a UDP](./UDP_protocol_specification.md) and [MAVLink](./MAVLink_protocol_specification.md) protocol specifications are well understood, and the basics of writing a protocol specification will not be discussed in this guide.

We can start by writing the specifications for each component in the drone's velocity, position, and orientation:


```json
{
    "name": "STATUS_MESSAGE",
    "fields": [
        {
            "name": "ID",
            "type": "U8"
        },
        {
            "name": "velocity_x",
            "type": "F32"
        },
        {
            "name": "velocity_y",
            "type": "F32"
        },
        {
            "name": "velocity_z",
            "type": "F32"
        },
        {
            "name": "position_lat",
            "type": "F32"
        },
        {
            "name": "position_lon",
            "type": "F32"
        },
        {
            "name": "position_alt",
            "type": "F32"
        },
        {
            "name": "orientation_yaw",
            "type": "F32"
        },
        {
            "name": "orientation_pitch",
            "type": "F32"
        },
        {
            "name": "orientation_roll",
            "type": "F32"
        },
    ]
}
```

So far, this is totally fine and structs are not required.
We will continue and add the information for the current waypoint.
Since the `current waypoint` is encoded with an integer describing the type of waypoint, followed by three floats describing the position of the waypoint, we will add a `U8` field followed by three `F32` fields.

```json
{
    "name": "STATUS_MESSAGE",
    "fields": [
        {
            "name": "ID",
            "type": "U8"
        },
        {
            "name": "velocity_x",
            "type": "F32"
        },
        {
            "name": "velocity_y",
            "type": "F32"
        },
        {
            "name": "velocity_z",
            "type": "F32"
        },
        {
            "name": "position_lat",
            "type": "F32"
        },
        {
            "name": "position_lon",
            "type": "F32"
        },
        {
            "name": "position_alt",
            "type": "F32"
        },
        {
            "name": "orientation_yaw",
            "type": "F32"
        },
        {
            "name": "orientation_pitch",
            "type": "F32"
        },
        {
            "name": "orientation_roll",
            "type": "F32"
        },
        {
            "name": "curr_waypoint_type",
            "type": "U8"
        },
        {
            "name": "curr_waypoint_lat",
            "type": "F32"
        },
        {
            "name": "curr_waypoint_lon",
            "type": "F32"
        },
        {
            "name": "curr_waypoint_alt",
            "type": "F32"
        },
    ]
}
```

Again, still doing _okay_ without custom structs.
However, once we begin to describe the information about the variable list of waypoints, we see an issue.
Since, in parseLab, a `list` type is defined as `<type>[<list_length>]`, we would want to define the waypoints list as `Waypoint[NumberOfLoadedWaypoints]`.
With the default parseLab types, `unsigned int`, `int,` and `float`, this would not be possible.
This is where structs come into play.

In parseLab, structs are defined very similar to messages.
We will create a struct, with name `Waypoint`, which has four members: `Type`, `lat`, `lon`, and `alt`.

```json
{
    "structs": [
        {
            "struct_name": "Waypoint",
            "members": [
                {
                    "name": "Type",
                    "type": "U8"
                },
                {
                    "name": "lat",
                    "type": "F32"
                },
                {
                    "name": "lon",
                    "type": "F32"
                },
                {
                    "name": "alt",
                    "type": "F32"
                }
            ]
        }
    ],
    "protocol_types": [
        ...
    ]
}
```

The `structs` element of the protocol specification json file needs to be placed above the `protocol_types` element.

Now that parseLab has the `structs` element to reference when processing the `protocol_types`, the `Waypoint` struct can be used in the `type` definition of a message field.

With this custom `Waypoint` data type, lets create the variable list of loaded waypoints:


```json
{
    "structs": [
        {
            "struct_name": "Waypoint",
            "members": [
                {
                    "name": "Type",
                    "type": "U8"
                },
                {
                    "name": "lat",
                    "type": "F32"
                },
                {
                    "name": "lon",
                    "type": "F32"
                },
                {
                    "name": "alt",
                    "type": "F32"
                }
            ]
        }
    ],
    "protocol_types": [

        ...

        {
            "name": "NumberOfLoadedWaypoints",
            "type": "U8"
            "dependee": "True"
        },
        {
            "name": "WaypointsLoaded",
            "type": "Waypoint[NumberOfLoadedWaypoints]"
        },
    ]
}
```

With this, we can now describe our variable list of waypoint objects in the protocol specifiction file.
As it currently stands, the protocol specification file is completely valid and can be used for generating a parser and testcase information.
We can go further though; parseLab is capable of nested structs.
In our `Waypoint` object, we have `lat`, `lon`, and `alt`, which we also use for the positional information of the drone itself at another point in the `STATUS_MESSAGE`.
It seems beneficial to make this into a new struct: `coord_t`, which represents GPS coordinates.
So lets create that, and modify the `Waypoint` struct to use it.

```json

"structs": [
    {
        "struct_name": "coord_t",
        "members": [
            {
                "name": "lat",
                "type": "F32"
            },
            {
                "name": "lon",
                "type": "F32"
            },
            {
                "name": "alt",
                "type": "F32"
            }
        ]
    },
    {
        "struct_name": "Waypoint",
        "members": [
            {
                "name": "Type",
                "type": "U8"
            },
            {
                "name": "Position",
                "type": "coord_t"
            }
        ]
    }
]
```

We can also modify the `protocol_types` and update the `STATUS_MESSAGE` to use these new types:

```json
{
    "name": "STATUS_MESSAGE",
    "fields": [
        {
            "name": "ID",
            "type": "U8"
        },
        {
            "name": "velocity_x",
            "type": "F32"
        },
        {
            "name": "velocity_y",
            "type": "F32"
        },
        {
            "name": "velocity_z",
            "type": "F32"
        },
        {
            "name": "Position",
            "type": "coord_t"
        },
        {
            "name": "orientation_yaw",
            "type": "F32"
        },
        {
            "name": "orientation_pitch",
            "type": "F32"
        },
        {
            "name": "orientation_roll",
            "type": "F32"
        },
        {
            "name": "curr_waypoint",
            "type": "Waypoint"
        },
        {
            "name": "NumberOfLoadedWaypoints",
            "type": "U8"
            "dependee": "True"
        },
        {
            "name": "WaypointsLoaded",
            "type": "Waypoint[NumberOfLoadedWaypoints]"
        },
    ]
}
```

Just like we combined the positional coordinates into a `coord_t` struct, we can do the same with the `velocity` and `orientation` information.

If you were to go forward and completely "struct-ify" this `STATUS_MESSAGE`, it might end up looking like [this](../examples/struct_definitions/protocol.json):

### NOTE: The names in the following file snippit are inconsistent with the rest of the guide up until this point

```json
{
    "structs": [
        {
            "struct_name": "vel_t",
            "members": [
                {
                    "name": "X",
                    "type": "F32"
                },
                {
                    "name": "Y",
                    "type": "F32"
                },
                {
                    "name": "Z",
                    "type": "F32"
                }
            ]
        },
        {
            "struct_name": "coord_t",
            "members": [
                {
                    "name": "Latitude",
                    "value": "(0, 360)",
                    "type": "F32"
                },
                {
                    "name": "Longitude",
                    "value": "(0, 360)",
                    "type": "F32"
                },
                {
                    "name": "Altitude",
                    "type": "F32"
                }
            ]
        },
        {
            "struct_name": "orientation_t",
            "members": [
                {
                    "name": "Roll",
                    "value": "(-180, 180)",
                    "type": "F32"
                },
                {
                    "name": "Pitch",
                    "value": "(-180, 180)",
                    "type": "F32"
                },
                {
                    "name": "Yaw",
                    "value": "(-180, 180)",
                    "type": "F32"
                }
            ]
        },
        {
            "struct_name": "telem_t",
            "members": [
                {
                    "name": "Velocity",
                    "type": "vel_t"
                },
                {
                    "name": "Position",
                    "type": "coord_t"
                },
                {
                    "name": "Orientation",
                    "type": "orientation_t"
                }
            ]
        },
        {
            "struct_name": "waypoint_t",
            "members": [
                {
                    "name": "WaypointType",
                    "value": "0|1|2|4|8",
                    "type": "U8"
                },
                {
                    "name": "Position",
                    "type": "coord_t"
                }
            ]
        }
    ],
    "protocol_types": [
        {
            "name": "STATUS_MSG",
            "fields": [
                {
                    "name": "ID",
                    "type": "U8"
                },
                {
                    "name": "Telemetry",
                    "type": "telem_t"
                },
                {
                    "name": "CurrentWaypoint",
                    "type": "waypoint_t"
                },
                {
                    "name": "WaypointsRemaining",
                    "type": "U8",
                    "value": "(0, 8)",
                    "dependee": "true"
                },
                {
                    "name": "WaypointsList",
                    "type": "waypoint_t[WaypointsRemaining]"
                }
            ]
        }
    ]
}
```

## Verifying the New Protocol Specification File

Lets now create a new protocol directory, and use this protocol specification to generate a C-Hammer parser.

The following commands will do this for us:

```bash
# Change directory to get to bin/ inside of the parseLab repo
$ cd ${PARSELAB_REPO}/bin

# Create the protocol directory for this drone message
$ ./setup.py --protocol ../protocols/drone --module hammer

# Copy the protocol specification, that we just made, into the new protocol directory
$ cp ../examples/struct_definitions/protocol.json ../protocols/drone/protocol.json

# Generate the parser with C-Hammer
$ ./generate_parser.py --protocol ../protocols/drone --module hammer
```

It might be helpful to look at the generated file `../protocols/drone/hammer/out/src/parser.c` and compare it to another generated parser that does not leverage structs, to see how they differ, but we will not do that here.

Instead, we will run the `quick_test.py` script to demonstrate that we can succesfully generate a parser using structs, along with valid and invalid testcases to test against the new parser.

```bash
# Change directory to get to the bin/ inside of the parseLab repo
$ cd ${PARSELAB_REPO}/bin

# Run the quick_test script
$ ./quick_test.py --protocol ../protocols/drone/ --module hammer --msg_count 100 --name valid_01 --valid
```

If everything goes to plan, this should return a long output of 100 "success" messages.

At this point, we have explored the capabilities of having struct definitions in our protocol specification files.
