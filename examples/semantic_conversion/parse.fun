int semantic_parse(const uint8_t* msg, int msg_length) {
    static struct state_t curr_state = {0};
    size_t input_size = msg_length + sizeof(curr_state);
    uint8_t* input = (uint8_t*)malloc(input_size);

    memcpy(input, &curr_state, sizeof(curr_state));
    memcpy(input + sizeof(curr_state), msg, msg_length);

    const HParser *parser = init_parser(&curr_state);
    HParseResult* result = h_parse(parser, input, input_size);

    free(input);

    if (result != NULL) {
        return 0;
    }
    return 1;
}
