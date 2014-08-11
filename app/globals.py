# globals.py
#
# Contains app-level properties and routines. Created as alternative to
# existing model of maintaining such elements in correlator.py:MainFrame
# and accessing them through stored references to MainFrame ("self.parent").
# This should be a nicer way for modules to access data like the current
# database path, user, etc.

# brgtodo 8/4/2014: Better name? application.py? shared.py? allthestuffs.py?

import os

### Variables

DBPath = "-" # path to db folder root (e.g. ~/Documents/Correlator/1.8.0/)
LastDir = "" # most recent directory from/to which a file was loaded/saved


### Functions

""" Return list of user-defined data types """
def GetUserTypes():
	types = []
	filename = DBPath + 'tmp/datatypelist.cfg'
	if os.access(filename, os.F_OK) == True:
		f = open(filename, 'r+')
		for line in f:
			typeStr = line.rstrip()
			if len(typeStr) > 0:
				types.append(typeStr)
		f.close()
	return types
