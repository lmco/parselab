# How to Use a Generated parseLab Parser

Once parseLab has generated a proper parser for the target protocol, the source code that gets generated can be leveraged by a desired application.
Since parseLab is able to generate different langauges, there is no standard way to leverage the generated code into a target applicatoin.
For this guide, C-Hammer will be used to demonstate this process by compiling the generated Hammer code into a shared library and linking it into both C++ and Python.
We will also be using the UDP protocol, so it is explected that the other guide's that describe UDP are well understood.

## How to Use a Generated Hammer Parser with a Target Application

The general work-flow for this process is to use the Makefile provided with the generated Hammer code to generate a shared library (.so file).
With this shared library, we can either link against it when compiling a C/C++ program or we can use the `ctypes` library in Python to import it for use in a python script.
The generated Hammer code will provide an interface into the parser than can be leveraged after linking/importing the library.
Before we take a look at this interface, we will create a new protocol directory to work with for this guide.

```bash
# Go to parselab/bin
cd ${PARSELAB_REPO}/bin

# Create a new protocol directory for us to work with
./setup.py --protocol ../protocols/udp_app --module hammer

# Verify it was created
ls ../protocols/udp_app
> hammer/  protocol.json

# Copy the UDP example protocol specification to this directory
cp ../examples/udp/protocol.json ../protocols/udp_app/protocol.json
```

Once again, we will use UDP as an example.
At this point, our new protocol directory is prepped for code generation.

```bash
# Go to parselab/bin
cd ${PARSELAB_REPO}/bin

# Generate the parser code
./generate_parser.py --protocol ../protocols/udp_app --module hammer

# Observe generated file structure
ls ${PARSELAB_REPO}/protocols/udp_app/hammer/out
> include/  Makefile  src/  tests/
```

Now that the code was generated, lets take a look at the files that were generated - specifically the `src/parser.c`.
Inside `src/parser.c` we can find two functions: `int parse(const uint8_t* msg, int size` and `HParser *init_parser(void)`.
These two functions are more than enough to parse the serialized data for your application.

### What is the init_parser() Function?

The `init_parser()` function is responsible for returning an instance of the `HParser` object, which contains all of the parse rules for the target protocol.
The `HParser` object works with the `h_parse()` function, which can be seen in the `parse()` function.
The contents of this function are not important to understand at this time, and can mostly be ignored.
Technically, to leverage the shared library to its fullest, this function is all you need to reference with your target application.
However, for simplicity, we have also created the `parse()` function which can be referenced for an easy start to get parsing.

### What is the parse() Function?

The `parse()` function contains the logic which actually runs the Hammer parser against a set of input data.
As stated above, the way that this happens is through the `h_parse()` function in tandem with the `HParser` object returned from `init_parser()`.

``` C
int parse(const uint8_t* msg, int size) {
    size_t inputsize = size;
    uint8_t input[inputsize];

    memcpy(input, msg, inputsize);
    const HParser *parser = init_parser();
    HParseResult* result = h_parse(parser, input, inputsize);

    if (result != NULL) {
        return 0;
    }
    return 1;
}
```

This function's job is to consume serialized data, instantiate an instance of our generated parser, parse the data, then return the parse sucess status.
The parse success status is handled by checking if the return value of `h_parse` is NULL (or not).
If the returned value _is_ NULL, then the parse failed.
Likewise, if the returned value _is not_, then the parse succeeded.

For many cases, this boolean return value is sufficient... but for the cases where it is not, users are able to circumvent this parse function and create their own inside the target application or with a wrapper library around this one.

## Using the Shared Library Functions

If we jump over to the [cpp application example](../examples/cpp_application), we can find two python scripts: `simple.py` and `custom.py`.
These two scripts represent the two options that users have: 
    simple.py - Leverage the provided `parse()` function and only process boolean return values.
    custom.py - Circumvent the provided `parse()` function and define custom logic for how the parse result should be processed.

### Using the Provided parse() Function

Upon inspection of `simple.py`, we can find a pretty straight forward way of using our generated parser's shared library.

```python
#!/usr/bin/env python3

import ctypes
import struct

from UDP import UDP

def main():
    # Import parse() function from libparser.so
    libparser = ctypes.CDLL("libparser.so")

    # Generate a UDP message
    udp_msg = UDP(25515, 32316, "This is a data payload")

    # Parse the UDP Message
    ret = libparser.parse(udp_msg.serialized, len(udp_msg.serialized))
    if not ret:
        print("pass")
    else:
        print("fail")

if __name__ == '__main__':
    main()
```

Although the nicities of Python makes this relatively simple, the process is pretty much the same across all languages that can import/link/include C code through shared libraries.

We can see that after importing the library, it is as simple as calling the provided `parse()` function and checking its boolean return value.

For this simple example, we are just calling `print()` on the result, but this could be expanded to do anything from logging parse results to actively dropping packets that fail the parse so that they don't reach down-stream components in the application.

#### Running the Simple Example Script

In order to run the `simple.py` script, you need to have created the `udp_app` protocol directory as directed above.
Once the `udp_app` is created and a parser was generated for it, run the following lines:

```bash
# Go to the C++ application example directory
cd ${PARSELAB_REPO}/examples/cpp_application

# Run the build script
./build.sh

# Run simple.py
./simple.py
> pass
```

### Creating a Custom parse() Function

Although it could have been done in Python, to show more ways of referencing the generated parser's shared library, the `custom.py` script leverages a `parse()` function that was written in a C++ application.
With that being said, instead of looking at `custom.py`, we will start with `parse_wrapper.cpp` which contains the code for the custom `parse()` function.

Taking a look at the custom `parse()` function, `custom_parse()`, we can see that it starts off pretty simiar to the provided `parse()` function.

```C
extern "C" udp_msg_t* custom_parse(const uint8_t* msg, int size) {
    size_t inputsize = size;
    uint8_t input[inputsize];
    memcpy(input, msg, inputsize);

    // Create an instace of our generated parser
    const HParser *parser = init_parser();

    // Run the input data through the parser
    HParseResult* result = h_parse(parser, input, inputsize);

    ...
}
```

In the first part of the code, we create the buffer from the input data that we want to pass into `h_parse`.
We then instantiate the `HParser` object from our library's `init_parser` function.

Just like before, we get an `HParseResult` object from parsing the data.
However, unlike just checking if this object was NULL or not, we are going to do some processing on the `HParseResult` (assuming it wasn't returned as NULL).


```C
extern "C" udp_msg_t* custom_parse(const uint8_t* msg, int size) {
    ...

    HParseResult* result = h_parse(parser, input, inputsize);

    // Allocate enough memory for a udp_msg_t which we will set as a return
    // from this function
    udp_msg_t* udp_msg = (udp_msg_t*)malloc(sizeof(udp_msg_t));

    ...
}
```

Lets pretend that we want to consume the parsed data that comes from the `HParsedResult` and put it into a struct that defines the UDP format: `udp_msg_t`.
To do that, we will first create a pointer instance of this struct (technically, this does not need to be a pointer, but it adds some extra complications with freeing memory that I wanted to show later)
Now that we have an instance of the `udp_msg_t` struct, we can start filling out the data by pulling the data out of the returned `HParsedResult` object.

Before that though, it is important to understand what the `HParsedResult` _is_.
However, this is not going to be a Hammer Library tutorial, so I would heavily recommend going through the Hammer code and trying to understand the data types contained in the `HParsedResult`, which can be found in Hammer's repo in `hammer/src/hammer.h`. 
The `src/hammer.h` and `src/glue.h` are very helpful resources for understanding all of the data types and concepts within Hammer.

Knowledge of Hammer's `HParseToken` and `HParseResult` isn't _required_ but definitely advised past this point.

So lets see how we can go about filling in our new `udp_msg_t` struct:


```C
extern "C" udp_msg_t* custom_parse(const uint8_t* msg, int size) {
    ...

    udp_msg_t* udp_msg = (udp_msg_t*)malloc(sizeof(udp_msg_t));

    if (result != NULL) {
        udp_msg->src_port = H_CAST_UINT(result->ast->seq->elements[0]);
        udp_msg->dest_port = H_CAST_UINT(result->ast->seq->elements[1]);
        udp_msg->length = H_CAST_UINT(result->ast->seq->elements[2]);
        udp_msg->checksum = H_CAST_UINT(result->ast->seq->elements[3]);
        ...
    }
    ...
}
```

I have omitted any comments from this file, as to not make this document overly long and hard to read, but there are comments on almost every line in this file if you open it up yourself.

First, we should notice the `result != NULL` check which is the same as the provided `parse()` function.
We need to check this first, because if the returned result was NULL, we won't be able to process anything from it.

We then iterate over the variables within the `udp_msg_t` struct and set them equal to data we can pull from the `HParseResult` object.
Starting with the `src_port` variable, we see that we are using the `H_CAST_UINT` macro from the Hammer library which converts a `HParsedToken` into a `uint` data type.
Inside of this macro, we are doing a lot of pointing... but its not as bad as it looks.
First, we take the `result` which is of type `HParseResult` and get the `ast`, or "AbstractSyntaxTree" from it.
The ast is a tree structure which represents the grammar that denotes the parsed object.
In our case, our ast is rather simple, it is mostly a flat array that we need to iterate over.
As a result, we then need to grab the `seq` or "token sequence" from the `ast`, then grab the `elements` or "list of `HParseToken` objects that are in our "token sequence".
Since the `src_port` is the first element in our sequence (as defined by our protocol specification file), we grab the `0th` element and convert that to a `uint`.

We can pretty much just keep repeating this same structure until we get to the `data` field, which is only slightly more complicated.
The `data` field is an array of `uint8_t` objects.
This means that when we get to this `HParseToken` element in the `ast`, it is actually a "token sequence" on its own.
Because of the nested nature of this, we can see a second `seq->elements` reference.

```C
extern "C" udp_msg_t* custom_parse(const uint8_t* msg, int size) {
    ...

    if (result != NULL) {
        ...

        udp_msg->checksum = H_CAST_UINT(result->ast->seq->elements[3]);
        for (int i = 0; i < udp_msg->length; i++) {
            udp_msg->data[i] = H_CAST_UINT(result->ast->seq->elements[4]->seq->elements[i]);
        }
    }

    ...
}
```

Since the `data` field is a "token sequence" or `seq` on its own, we then have to grab the elements of it to iterate over it, which is done with the second `->seq->elements` references.
Just like we iterate over the `ast` elements, we do the same with the `data` `HParseToken` object.
As we iterate, using the length found in the `2nd` element of the `ast`, we put the data into our `udp_msg->data` array one by one.

At this point, the entire `HParseResult` was processed and your target applicatoin is able to do anything with it.
But the NULL case still needs to be handled.
I have chosen to simply zero-out the struct for NULL instances, but obviously every application is going to have a different need.

```C
extern "C" udp_msg_t* custom_parse(const uint8_t* msg, int size) {
    ...

    if (result != NULL) {
        ...
    }
    else {
        udp_msg->src_port = 0;
        udp_msg->dest_port = 0;
        udp_msg->length = 0;
        udp_msg->checksum = 0;
    }

    return udp_msg;
}
```

At this point, our custom `parse()` function is completed and can be used.

I have chosen to use it in a small Python script, similar to `simply.py`.


### Using a Custom parse() Function

Using the custom parse function is the same as using the simple parse function, but since our custom parse function is doing more than just returning a boolean, it might be helpful to see an implementation of it.

For that, we can take a look at `custom.py`.

However, since the process to implement the different return value is more of an exercise in the chosen languge of the target application as opposed to parseLab/Hammer specific, I'm not going to explain it here.

#### Running the Custom Example Script

In order to run the `custom.py` script, you need to have created the `udp_app` protocol directory as directed above.
Once the `udp_app` is created and a parser was generated for it, run the following lines:

```bash
# Go to the C++ application example directory
cd ${PARSELAB_REPO}/examples/cpp_application

# Run the build script
./build.sh

# Run custom.py
./custom.py
> Parsed Data:
>   Source Port: 25515
>   Destination Port: 32316
>   Payload Length: 22
>   Checksum: 2009
>   Data: This is a data payload
```
