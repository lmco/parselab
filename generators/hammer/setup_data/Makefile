SRC_DIR := src
INC_DIR := include
TEST_DIR := tests
OBJ_DIR := obj
BIN_DIR := bin

CC := cc
OBJ_FLAGS := -g -O -c -Wall
SO_FLAGS := -shared -fPIC
LDLIBS := -L /usr/local/lib -lhammer
INCLUDES := -I$(INC_DIR)

PARSER_C := $(SRC_DIR)/parser.c
PARSER_O := $(OBJ_DIR)/parser.o
PARSER_SO := $(OBJ_DIR)/parser.so

TEST_DIRS := ${sort ${dir ${wildcard ${TEST_DIR}/*/}}}

all: $(OBJ_DIR) $(PARSER_O) $(PARSER_SO) TESTS

DEBUG:
	@echo $(TEST_DIRS)

TESTS:
	@for dir in ${TEST_DIRS}; do\
		[ -d $${dir}/bin ] || mkdir $${dir}/bin;\
		$(CC) -o $${dir}/bin/test.bin $${dir}*/*.c ${SRC_DIR}/*.c  ${INCLUDES} -I$${dir}/inc ${LDLIBS}; \
	done

$(TEST_DIRS):
	@echo "\$\^: $^"
	@echo "\$\@: $@"	
	@echo "\$\<: $<"

$(OBJ_DIR):
	mkdir $@

$(BIN_DIR):
	mkdir $@

# create object file of the parser
$(PARSER_O): $(PARSER_C)
	@echo "Compiling parser into obj file..."
	$(CC) $(OBJ_FLAGS) $^ $(INCLUDES) $(LDLIBS) -o $@

$(PARSER_SO): $(PARSER_C)
	@echo "Compiling parser into library file..."
	$(CC) $(SO_FLAGS) $^ $(INCLUDES) $(LDLIBS) -o $@

clean:
	-rm -rf $(BIN_DIR)
	-rm -rf $(OBJ_DIR)
