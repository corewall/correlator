# globals.py
#
# Contains app-level properties and routines. Created as alternative to
# existing model of maintaining such elements in correlator.py:MainFrame
# and accessing them through stored references to MainFrame ("self.parent").
# This should be a nicer way for modules to access data like the current
# database path, user, etc.

# brgtodo 8/4/2014: Better name? application.py? shared.py? allthestuffs.py?

import os
import wx

import dialog

### Variables

MainFrame = None # ref to root window

# I/O vars
DBPath = "-" # path to db folder root (e.g. ~/Documents/Correlator/1.8.0/)
LastDir = "" # most recent directory from/to which a file was loaded/saved


### Functions

def OnShowMessage(type, msg, numButton): 
	dlg = dialog.MessageDialog(MainFrame, type, msg, numButton)
	dlg.Centre(wx.CENTER_ON_SCREEN)
	ret = dlg.ShowModal()
	dlg.Destroy()
	return ret

def GetTypeNum(type):
	type = 7 # user type
	if type == "NaturalGamma":
		type = 4
	elif type == "Susceptibility":
		type = 3
	elif type == "Reflectance":
		type = 5
	elif type == "Bulk Density(GRA)":
		type = 1
	elif type == "Pwave":
		type = 2
	elif type == "Other": # brgtodo "Other" may be a pre-custom type vestige
		type = 7
	return type

def GetTypeAbbv(type):
	datatype = type
	if type == "NaturalGamma":
		datatype = "ngfix"
	elif type == "Susceptibility":
		datatype = "susfix"
	elif type == "Reflectance":
		datatype = "reflfix"
	elif type == "Bulk Density(GRA)":
		datatype = "grfix" 
	elif type == "Pwave":
		datatype = "pwfix" 
	elif type == "Other":
		datatype = "otherfix"
	return datatype

# make internal db filename based on type
def MakeFileName(type, title, filetype):
	datatype = GetTypeAbbv(type)
	filename = title + '.' + datatype + '.' + filetype + '.table' 
	return filename


# User (Custom) Type f'ns
# brgtodo own module?
""" Return list of user-defined data types """
def GetUserTypes():
	types = []
	filename = DBPath + 'tmp/datatypelist.cfg' # brgtodo GetConfigFile()?
	if os.access(filename, os.F_OK) == True:
		f = open(filename, 'r+')
		for line in f:
			typeStr = line.rstrip()
			if len(typeStr) > 0:
				types.append(typeStr)
		f.close()
	return types

def UserTypeExists(type):
	return type in GetUserTypes()

def AddUserType(type):
	filename = DBPath + 'tmp/datatypelist.cfg'
	f = open(filename, 'a+')
	f.write('\n' + type)
	f.close()
