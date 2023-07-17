set -x

cd ../../protocols/mep/hammer/out
make

cd -

ln -s ../../protocols/mep/hammer/out/obj/parser.so libparser.so

export LD_LIBRARY_PATH=`pwd`:/usr/local/lib
echo ${LD_LIBRARY_PATH}
