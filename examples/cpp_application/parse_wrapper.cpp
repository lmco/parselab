#include "parse_wrapper.h"

using namespace std;

// Function to free the allocated memory
extern "C" void free_udp_msg(udp_msg_t* msg) {
    free(msg);
}

// Our custom parser function which is able to do more processing than
//  return a simple boolean for parse result
extern "C" udp_msg_t* custom_parse(const uint8_t* msg, int size) {
    size_t inputsize = size;
    uint8_t input[inputsize];
    memcpy(input, msg, inputsize);

    // Create an instace of our generated parser
    const HParser *parser = init_parser();

    // Run the input data through the parser
    HParseResult* result = h_parse(parser, input, inputsize);

    // Allocate enough memory for a udp_msg_t which we will set as a return
    // from this function
    udp_msg_t* udp_msg = (udp_msg_t*)malloc(sizeof(udp_msg_t));

    // If the result of the parse is NULL, we had a parse failure
    //  and we cannot inspect the abstract syntax tree (AST)
    if (result != NULL) {
        // result->ast will point at the ast of the parsed object
        //  ast->seq will get the sequence object from the ast
        //   seq->elements will get the list of elements in the sequence
        //    elements[0] will get the first element (source portin this case)

        // H_CAST_UINT is a Hammer macro which converts a ParseToken into a uint
        //  We can take this uint and set it as the target value
        udp_msg->src_port = H_CAST_UINT(result->ast->seq->elements[0]);
        udp_msg->dest_port = H_CAST_UINT(result->ast->seq->elements[1]);
        udp_msg->length = H_CAST_UINT(result->ast->seq->elements[2]);
        udp_msg->checksum = H_CAST_UINT(result->ast->seq->elements[3]);
        for (int i = 0; i < udp_msg->length; i++) {
            // Since the Data field is an array, we need to access the sequence array (seq->elements)
            //  of the parsed Data field (seq->elements[4])
            // Just like before, we can iterate over `elements` and cast it as a UINT and set it
            //  in the udp_msg
            udp_msg->data[i] = H_CAST_UINT(result->ast->seq->elements[4]->seq->elements[i]);
        }
    }
    else {
        // zero out the return data
        udp_msg->src_port = 0;
        udp_msg->dest_port = 0;
        udp_msg->length = 0;
        udp_msg->checksum = 0;
    }

    // return the processed udp_msg
    return udp_msg;
}
