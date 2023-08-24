# script to get a working build of C++ code on Yosemite

g++ -fno-strict-aliasing -fno-common -dynamic -I../include -DCORRELATOR_MACOSX -I /Library/Frameworks/Python.framework/Versions/3.9/include/python3.9/ -c -ggdb py_func.cpp

g++ -bundle -undefined dynamic_lookup py_func.o -L /Users/bgrivna/proj/corewall/correlator/lib -lcore -o py_correlator.so

cp py_correlator.so intel/

echo "Built."