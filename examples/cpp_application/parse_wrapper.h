#ifndef __PARSER_WRAPPER_H__
#define __PARSER_WRAPPER_H__

#include <iostream>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>

// UDP data struct
typedef struct {
    uint16_t src_port;
    uint16_t dest_port;
    uint16_t length;
    uint16_t checksum;
    uint8_t data[512];
} udp_msg_t;

// Mark as extern to avoid mangling from c++
extern "C" {
#include "hammer/hammer.h"
#include "hammer/glue.h"
#include "parser.h"

void free_udp_msg(udp_msg_t* msg);
udp_msg_t* custom_parse(const uint8_t* msg, int size);
}

#endif
