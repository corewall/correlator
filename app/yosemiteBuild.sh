# script to get a working build of C++ code on Yosemite...and now Monterey (August 23 2023).
# Requires the 'core' library (C++ files in correlator/src built with `make install`).
#
# Had to update include path to point to Homebrew Python 3.11. Command `find /usr/local/Cellar -name Python.h`
# is quite useful!

g++ -fno-strict-aliasing -fno-common -dynamic -I../include -DCORRELATOR_MACOSX -I /usr/local/Cellar/python@3.11/3.11.3/Frameworks/Python.framework/Versions/3.11/include/python3.11/ -c -ggdb py_func.cpp

g++ -bundle -undefined dynamic_lookup py_func.o -L /Users/bgrivna/proj/corewall/correlator/lib -lcore -o py_correlator.so

cp py_correlator.so intel/

echo "Built."