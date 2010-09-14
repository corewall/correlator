#
#	Makefile for correlater
#	
#	
COMPILER=g++
MYFLAGS=-I../include -arch i386 -arch ppc -arch x86_64
# MYFLAGS=-mmacosx-version-min=10.4 -I../include -I/Users/julian/dev/EVL/corelyzer/branches/required/mac/src/xerces-c-src_2_8_0/include -arch i386 

#LIBS=-L../../xerces-c_2_8_0-x86-macosx-gcc_4_0/lib -lxerces-c  
#LIBS=-L../../xerces-c_2_8_0-x86-macosx-gcc_4_0/lib -lxerces-c -lm -ldl 
# LIBS=-L/Users/julian/dev/EVL/corelyzer/branches/required/mac/src/xerces-c-src_2_8_0/lib -lxerces-c -lm -ldl 
#LIBS=-lm -ldl -L../lib -lxerces-c -lc
#LIBS=-lm -ldl -L../lib -L../../xerces-c_2_8_0-x86-macosx-gcc_4_0/lib/ -lxerces-c -lc

# How to build a shared library
SHLD_FLAGS = -shared

# Correlater library name
CORE_LIB = libcore.so

# Machine specific settings
MACHINE=$(shell uname -s)
   #Darwin  MacOSX
   #Linux   linux
ARCHITECTURE=$(shell uname -p)
   #i386  MacOSX
   #i686    Linux 32bit
   #x86_64  Linux 64bit
   #ia64    Linux Itanium 64bit
   #ppc64   Linux PPC PS3

ifeq ($(MACHINE), Darwin)
SHLD_FLAGS=-dynamiclib -flat_namespace -undefined suppress
CORE_LIB = libcore.dylib
else
SHLD_FLAGS=-shared
CORE_LIB=libcore.so
endif

#REMOVED XMLLoader.o from CORE_OBJ
CORE_OBJ= Data.o Hole.o Core.o GraValue.o PwaveValue.o Value.o Section.o \
	ReflectanceValue.o DataManager.o \
	DataParser.o NaturalGammaValue.o SusceptibilityValue.o \
	Actor.o CullFilter.o DecimateFilter.o GaussianFilter.o \
	Tie.o Strat.o FilterManager.o Correlator.o AutoCorrelator.o \
	CoreObject.o

DIRT= *.o core core.* *.so *.dylib

build: $(CORE_LIB) 

install: build
	cp $(CORE_LIB) ../lib 
	cp $(CORE_LIB) ../app

clean:
	rm -f $(DIRT)
	cd ../lib; rm -f $(CORE_LIB); cd ../src
	cd ../bin; rm -f $(CORE_LIB); cd ../src

$(CORE_LIB) : $(CORE_OBJ)
	$(COMPILER) $(SHLD_FLAGS) $(CORE_OBJ) -arch i386 -arch ppc -arch x86_64 $(LIBS) -o $(CORE_LIB)

static: $(CORE_OBJ)
	ar -cr libcore.a x86_64 $(CORE_OBJ)
	ranlib libcore.a

.cpp.o :
	$(COMPILER) $(MYFLAGS) -c -o $@ $<
