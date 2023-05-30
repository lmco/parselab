# Installing parseLab

Since parseLab is a framework for developing code generators for different languages/libries, the installation process is a segmented between parseLab proper and the natively available parseLab generator modules.

## parseLab

This section describes the process to install the parseLab framework.

### Dependencies:

| PACKAGE | EARIEST TESTED VERSION | INSTALL METHOD |
|---------|------------------------|----------------|
| python3 | 3.6.9 | https://www.python.org/downloads/ |
| hexdump | 3.3 | pip install hexdump |
| bitstring | 3.1.9 | pip install bitstring |
| numpy | 1.19.5 | pip install numpy |

### Installation:

Installation is as simple as cloing te repo and getting all of the dependencies.


## Hammer

This section describes the process to install the Hammer library for use with parseLab's built-in Hammer generator module (as of April 2023).

### Dependencies:

| PACKAGE | EARIEST TESTED VERSION | INSTALL METHOD |
|---------|------------------------|----------------|
| hammer | cc733ff | https://github.com/UpstandingHackers/hammer |
| SCons | 4.5.2 | https://scons.org/ |

### Installation

1. Clone the hammer repo in the dependencies.
2. Run `scons` in the Hammer repo directory
3. Runs `scons install` in the Hammer repo directory
4. Ensure libhammer.so is in /usr/local/lib
5. Modify `.bashrc` to include `/usr/local/lib` in your `LD_LIBRARY_PATH`:

```bash
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib
```


## Daedalus

This section describes the process to install the Daedalus Data Description Language for use with parseLab's built-in Hammer generator module (as of April 2023)

### Dependencies

| PACKAGE | EARIEST TESTED VERSION | INSTALL METHOD |
|---------|------------------------|----------------|
| daedalus | 5581f67 | https://github.com/GaloisInc/daedalus |
| gmp | 6.1.2-10 | package manager |
| gmp-devel | 6.1.2-10 | package manager |
| ncurses | 6.1-9 | package manager |
| ncurses-compat-libs | 6.1-9 | package manager |
| ncurses-devel | 6.1-9 | package manager |

### Installation

1. Install cabal and cabal-install through your package manager

```bash
sudo apt install caball-install
```
2. Put cabal in your path if it is not already

```bash
# If this returns nothing, you need to add cabal to the path
which cabal

# Find cabal:
ls ~/.cabal/bin

ls ~/.ghcup/bin

# If neither of the above paths pointed to cabal, do a full search and look for the cabal executable
find / -name "*cabal*" 2>/dev/null

# Update your bashrc and point your path towards this executable
# ex: export PATH=$PATH:~/.cabal/bin

# Source your bashrc changes
source ~/.bashrc

# Make sure that you can reference it now
which cabal
```

3. Build the daedalus repo with cabal

```bash
# Pick a location where you want the Daedalus executable (the process that parses Daedalus code when working with Daedalus)
export DAEDALUS_PATH=~/.cabal/bin/

# Build the Daedalus Repo
cabal install --installdir=$DAEDALUS_PATH

# Update your bashrc so that the $DAEDALUS_PATH is in your PATH variable
#  Ex: export PATH=$PATH:~/.cabal/bin
```

4. Test to make sure daedalus installed properly

```bash
# Go to daedalus repo directory
cd ${DAEDALUS_TOP}

# Run the midi parser against a midi file and verify parse success
daedalus ../formats/midi.ddl -i ../tests/midi/inputs/moz_k99.midi
```

# Verifying Installation Success

Installation success is best measured by the ability to run the unit test suite against a target module.
Right now, the only native parseLab generator module that is capable of passing all of the unit tests is the Hammer module.
Therefore, we are now going to try to run the unit test suite against the Hammer module and verify that parseLab and Hammer were installed properly.
To verify Daedalus was installed, we can't leverage the unit tests, but we can still test its installation.

## Hammer

First, for Hammer verification:

```bash
# Go to the bin directory in parseLab
cd ${PARSELAB_TOP}/bin

# Run the unit test driver script against the Hammer generator module
./unit_tests.py --module hammer
> [Passed] unit_tests.ValueTypesTest.ValueTypesTest
> [Passed] unit_tests.GenerateParser.GenerateParser
> [Passed] unit_tests.Setup.Setup
> [Passed] unit_tests.GenerateTest.GenerateTest
> [Passed] unit_tests.DataTypesTest.DataTypesTest
```

If all of these tests pass, then both parseLab and Hammer are properly installed

## Daedalus

For Daedalus, we won't be able to run the unit tests driver script, but we can manually do something similar.
Don't worry too much about the steps, there are guides that explain what happening in more detail in the parselab/docs directory.

```bash
# Go to the bin directory in parseLab
cd ${PARSELAB_TOP}/bin

./setup.py --protocol ../protocols/test_UDP --module daedalus

cp ../examples/udp/protocol.json ../protocols/test_UDP/

./generate_parser.py --protocol ../protocols/test_UDP --module daedalus

./generate_testcase.py --protocol ../protocols/test_UDP --name test_01 --one_per --valid

./generate_test.py --protocol ../protocols/test_UDP \
                   --module daedalus \
                   --testcase ../protocols/test_UDP/testcases/test_01

./run_test.py --protocol ../protocols/test_UDP \
              --module daedalus
              --testcase ../protocols/test_UDP/testcases/test_01

# Verify that there was no error response when running the run_test.py driver script
```

If the test passes without an error response, both parseLab and Daedalus is properly installed
