set -x

cd ../../protocols/udp_app/hammer/out
make

cd -

ln -s ../../protocols/udp_app/hammer/out/obj/parser.so libparser.so
ln -s ../../protocols/udp_app/hammer/out/include/parser.h parser.h

build_custom_lib() {
    g++ -Wall -c -o parse_wrapper.o -c parse_wrapper.cpp -I. -lhammer -lparser

    g++ -Wall -shared -o libcustomparser.so parse_wrapper.o -I. -L. -lhammer -lparser
}

clean() {
    rm parse_wrapper.o
}

clean
build_custom_lib

export LD_LIBRARY_PATH=`pwd`:/usr/local/lib
echo ${LD_LIBRARY_PATH}

clean
