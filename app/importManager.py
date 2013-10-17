# Import of the py_correlator C++ glue module became a bit complicated due to the need
# for 32- and 64-bit builds on Windows. Pulling import code into its own module allows
# a one-liner wherever py_correlator is needed: "from importManager import py_correlator"

import platform

if platform.uname()[0] == "Windows":
	# 10/16/2013 brg: On Windows, we need both 32- and 64-bit builds and thus must import the
	# correct flavor of py_correlator.  This seems to be the most reliable way to determine
	# whether we're running against 32- or 64-bit Python.
	import sys
	is64bit = sys.maxsize > 2**32

	if is64bit == True:
		print "64-bit Python detected, importing py_correlator64"
		import py_correlator64 as py_correlator
	else:
		print "32-bit Python detected, importing py_correlator (32-bit)"
		import py_correlator
else:
	import py_correlator
	print "OS X detected, importing only version of py_correlator"

