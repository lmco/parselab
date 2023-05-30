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
