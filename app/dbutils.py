#!/usr/bin/env python

## For Mac-OSX
#/usr/bin/env pythonw

import platform
platform_name = platform.uname()

import random, sys, os, re, time, ConfigParser, string
from datetime import datetime
import wx

from importManager import py_correlator

import constants as const
import dialog
import globals as glb
import model
import xml_handler


""" Confirm existence of dirs and files corresponding to sites listed in root-level
datalist.db. If not, regenerate root datalist.db to reflect filesystem state. """
def ValidateDatabase():
	if os.access(glb.DBPath + 'db/', os.F_OK) == False :
		os.mkdir(glb.DBPath + 'db/')

	if os.access(glb.DBPath + 'db/datalist.db', os.F_OK) == False :
		root_f = open(glb.DBPath + 'db/datalist.db', 'w+')
		root_f.close()

	valid = True
	root_f = open(glb.DBPath + 'db/datalist.db', 'r+')
	for root_line in root_f :
		list = root_line.splitlines()
		if list[0] == '' :
			continue
		for data_item in list :
			if os.access(glb.DBPath + 'db/' + data_item + '/datalist.db', os.F_OK) == False :
				valid = False 
				break

	root_f.close()
	if not valid:
		print "[ERROR] Data list is not valid, DATALIST WILL BE RE-GENERATED"
		root_f = open(glb.DBPath + 'db/datalist.db', 'w+')
		list = os.listdir(glb.DBPath + 'db/')
		for dir in list :
			if dir != "datalist.db" :
				if dir.find("-", 0) > 0 :
					if os.access(glb.DBPath + 'db/' + dir + '/datalist.db', os.F_OK) == True :
						root_f.write(dir + "\n")
		root_f.close()

def LoadDatabase():
	ValidateDatabase()
	LoadSessionReports()
	siteNames = LoadSiteNames()
	loadedSites = LoadSites(siteNames)
	return loadedSites

def LoadSites(siteNames):
	loadedSites = {}
	for siteName in siteNames:
		siteFile = open(glb.DBPath + 'db/' + siteName + '/datalist.db', 'r+')
		siteLines = siteFile.readlines()
		for idx, line in enumerate(siteLines):
			siteLines[idx] = siteLines[idx].strip('\r\n')

		site = model.SiteData(siteName)
		ParseHoleSets(site, siteLines)
		ParseHoles(site, siteLines)
		ParseOthers(site, siteLines)
		#site.dump()
		loadedSites[siteName] = site

	return loadedSites

def LoadSiteNames():
	dbRootFile = open(glb.DBPath + 'db/datalist.db', 'r+')
	siteNames = []
	for site in dbRootFile:
		site = site.strip()
		if site == '' or site in siteNames:
			continue
		else:
			siteNames.append(site)
	return sorted(siteNames)

def SaveDatabase(siteDict):
	pass

def SaveSite(site):
	siteFileName = GetDBFilePath(site.name)
	siteFile = open(siteFileName, "w+")
	for hs in site.holeSets.values():
		WriteHoleSet(hs, siteFile)
	for affine in site.affineTables:
		WriteSavedTable(affine, "affinetable", siteFile)
	for splice in site.spliceTables:
		WriteSavedTable(splice, "splicetable", siteFile)
	for eld in site.eldTables:
		WriteSavedTable(eld, "eldtable", siteFile)
	for strat in site.stratTables:
		WriteSpecialSavedTable(strat, "strat", siteFile)
	for age in site.ageTables:
		WriteSpecialSavedTable(age, "age", siteFile)
	for series in site.seriesTables:
		WriteSpecialSavedTable(series, "series", siteFile)
	for image in site.imageTables:
		WriteSpecialSavedTable(image, "image", siteFile)
	for log in site.logTables:
		WriteDownholeLog(log, siteFile)
	siteFile.close()
		
def GetDBFilePath(siteName):
	return glb.DBPath + "db/" + siteName + "/datalist.db"

def GetSitePath(siteName):
	return glb.DBPath + "db/" + siteName + "/"

def GetSiteFilePath(siteName, fileName):
	return GetSitePath(siteName) + fileName

""" return max log number (e.g. the '2' in 6-4.DENSITY.2.log.dat)
	plus one - used when creating new logfile"""	
def GetNewLogNum(logList, datatype):
	result = 0
	for log in logList:
		idx1 = log.file.find('.') + 1
		idx2 = log.file.find('.', idx1) 
		if idx1 != -1 and idx2 != -1 and datatype == log.file[idx1:idx2]:
			idx2 += 1
			idx3 = log.file.find('.', idx2)
			if idx3 != -1:
				curNum = int(log.file[idx2:idx3])
				if curNum > result:
					result = curNum
	return str(result + 1)

def GetNewTableNum(tableList):
	""" return max table number (e.g. the '3' in 321-1390.3.affine.table)
	plus one - used when creating new saved table
	>>> GetNewTableNum([])
	'1'
	""" 
	result = 0
	for tab in tableList:
		idx1 = tab.file.find('.') + 1
		idx2 = tab.file.find('.', idx1)
		if idx1 != -1 and idx2 != -1:
			curNum = int(tab.file[idx1:idx2])
			if curNum > result:
				result = curNum
		else:
			print "Unexpected table filename format, couldn't find two periods"
	return str(result + 1)

def MakeTableFilename(siteName, tableNum, tableType):
	return siteName + '.' + tableNum + '.' + tableType + '.table'

def WriteHoleSet(holeSet, siteFile):
	for holeKey in sorted(holeSet.holes): # sorted acts on dictionary keys by default
		WriteHole(holeSet.holes[holeKey], siteFile)

	if holeSet.HasCull():
		WriteSavedTable(holeSet.cullTable, "culltable", siteFile)
	
	# HoleSet values
	WriteLine(siteFile, "typeData", MakeContinuousStr(holeSet.continuous))
	WriteLine(siteFile, "typeDecimate", str(holeSet.decimate))
	if holeSet.smooth.IsValid():
		WriteLine(siteFile, "typeSmooth", holeSet.smooth.MakeToken())
	WriteLine(siteFile, "typeMin", holeSet.min)
	WriteLine(siteFile, "typeMax", holeSet.max)
	siteFile.write("\n\n")

def WriteLine(destFile, key, value):
	line = "{}: {}\n".format(key, value)
	destFile.write(line)
	
def WriteToken(destFile, token):
	line = "{}: ".format(token)
	destFile.write(line)

def WriteHole(hole, siteFile):
	WriteLine(siteFile, "hole", hole.name)
	WriteLine(siteFile, "type", hole.holeSet.type)
	WriteLine(siteFile, "dataName", hole.dataName)
	WriteLine(siteFile, "depth", hole.depth)
	WriteLine(siteFile, "min", hole.min)
	WriteLine(siteFile, "max", hole.max)
	WriteLine(siteFile, "file", hole.file)
	WriteLine(siteFile, "source", hole.origSource)
	WriteLine(siteFile, "data", hole.data)
	WriteLine(siteFile, "enable", hole.GetEnableStr())
	WriteLine(siteFile, "updatedTime", hole.updatedTime)
	WriteLine(siteFile, "byWhom", hole.byWhom)
	siteFile.write("\n")
	
def WriteSavedTable(table, typeToken, siteFile):
	for token in [typeToken, table.file, table.updatedTime, table.byWhom, table.GetEnableStr()]:
		WriteToken(siteFile, token)
	if table.origSource == "":
		siteFile.write("-")
	else:
		WriteToken(siteFile, table.origSource)
	siteFile.write("\n\n")
	
# for age, timeseries, stratigraphy, image tables, which handle source file slightly differently than
# affine, splice, and ELD
def WriteSpecialSavedTable(table, typeToken, siteFile):
	for token in [typeToken, table.file, table.updatedTime, table.byWhom, table.origSource]:
		WriteToken(siteFile, token)
	siteFile.write(table.GetEnableStr())
	siteFile.write("\n\n")
	
def WriteDownholeLog(log, siteFile):
	tokens = ["log", log.file, log.updatedTime, log.byWhom, log.origSource, log.dataIndex,
				log.GetEnableStr(), log.dataType, log.min, log.max, log.decimate]
	if log.smooth.IsValid():
		tokens.append(log.smooth.MakeToken())

	for token in tokens:
		WriteToken(siteFile, token) 
	siteFile.write("\n\n") 
	
def MakeContinuousStr(cont):
	return "Continuous" if cont else "Discrete"

# parse single-line types
def ParseOthers(site, siteLines):
	for line in siteLines:
		tokens = line.split(': ')
		if tokens[0] == 'affinetable':
			affine = model.AffineData()
			ParseTableData(affine, tokens)
			site.affineTables.append(affine)
		elif tokens[0] == 'splicetable':
			splice = model.SpliceData()
			ParseTableData(splice, tokens)
			site.spliceTables.append(splice)
		elif tokens[0] == 'eldtable':
			eld = model.EldData()
			ParseTableData(eld, tokens)
			site.eldTables.append(eld)
		elif tokens[0] == 'log':
			log = model.DownholeLogTable()
			ParseDownholeLog(log, tokens)
			site.logTables.append(log)
		elif tokens[0] == 'strat':
			strat = model.StratTable()
			ParseSpecialTableData(strat, tokens)
			site.stratTables.append(strat)
		elif tokens[0] == 'age':
			age = model.AgeTable()
			ParseSpecialTableData(age, tokens)
			site.ageTables.append(age)
		elif tokens[0] == 'series':
			series = model.SeriesTable()
			ParseSpecialTableData(series, tokens)
			site.seriesTables.append(series)
		elif tokens[0] == 'image':
			image = model.ImageTable()
			ParseSpecialTableData(image, tokens)
			site.imageTables.append(image)

def ParseHoleSets(site, siteLines):
	curType = None
	for line in siteLines:
		tokens = line.split(': ')
		#if tokens[0] == 'type' and tokens[1] not in site.holeSets:
		#	curType = tokens[1]
		#	site.holeSets[tokens[1]] = HoleSet(curType)
		if tokens[0] == 'type':
			curType = tokens[1]
			site.AddHoleSet(curType)
		elif tokens[0] == 'typeData':
			site.holeSets[curType].continuous = ParseContinuousToken(tokens[1])
		elif tokens[0] == 'typeDecimate':
			site.holeSets[curType].decimate = ParseDecimateToken(tokens[1])
		elif tokens[0] == 'typeSmooth':
			site.holeSets[curType].smooth = ParseSmoothToken(tokens[1])
		elif tokens[0] == 'typeMin':
			site.holeSets[curType].min = tokens[1]
		elif tokens[0] == 'typeMax':
			site.holeSets[curType].max = tokens[1]
		elif tokens[0] == 'culltable' or tokens[0] == 'uni_culltable':
			cull = model.CullTable()
			ParseTableData(cull, tokens)
			site.holeSets[curType].cullTable = cull

# For some reason holes are the only data we serialize as multiple lines. Why?
# Maintaining as single lines (like everything else) would simplify parsing.
def ParseHoles(site, siteLines):
	curHole = None
	curType = None
	for line in siteLines:
		token = line.split(': ')
		if token[0] == 'hole':
			if curHole != None:
				site.AddHole(curType, curHole)
			curHole = model.HoleData(token[1])
		elif token[0] == 'type':
			curType = token[1]
		elif token[0] == "dataName":
			curHole.dataName = token[1]
		elif token[0] == "depth" :
			curHole.depth = token[1]
		elif token[0] == "file" :
			curHole.file = token[1]
		elif token[0] == "min" :
			curHole.min = token[1]
		elif token[0] == "max" :
			curHole.max = token[1]
		elif token[0] == "updatedTime" :
			curHole.updatedTime = token[1]
		elif token[0] == "enable" :
			curHole.enable = ParseEnableToken(token[1])
		elif token[0] == "byWhom" :
			curHole.byWhom = token[1]
		elif token[0] == "source" :
			curHole.origSource = token[1]
		elif token[0] == "data" :
			curHole.data = token[1]
	if curHole != None:
		site.AddHole(curType, curHole)

# parse routines for members maintained as numeric/boolean/etc rather than a string
def ParseEnableToken(enableToken):
	return enableToken == 'Enable'

def ParseContinuousToken(contToken):
	return contToken == 'Continuous'

def ParseDecimateToken(decToken):
	try:
		decInt = int(decToken)
		return decInt
	except ValueError:
		return 1

def ParseSmoothToken(smoothToken):
	if smoothToken == "":
		return model.SmoothData()
	else:
		toks = smoothToken.split()
		width = int(toks[0])
		unit = const.DEPTH if toks[1] == "Depth(cm)" else const.POINTS
		if toks[2] == "UnsmoothedOnly":
			style = const.UNSMOOTHED
		elif toks[2] == "SmoothedOnly":
			style = const.SMOOTHED
		elif toks[2] == "Smoothed&Unsmoothed":
			style = const.BOTH

	return model.SmoothData(width, unit, style)

def ParseTableData(table, tokens):
	table.file = tokens[1]
	table.updatedTime = tokens[2]
	table.byWhom = tokens[3]
	table.enable = ParseEnableToken(tokens[4])
	if len(tokens) > 5 and tokens[5] != '-':
		table.origSource = tokens[5]
		
# age, timeseries, image, stratigraphy are written in a slightly different format
# than affine, splice, and ELD tables - original source comes before enabled state
def ParseSpecialTableData(table, tokens):
	table.file = tokens[1]
	table.updatedTime = tokens[2]
	table.byWhom = tokens[3]
	table.origSource = tokens[4]
	table.enable = ParseEnableToken(tokens[5])
		
def ParseDownholeLog(log, tokens):
	log.file = tokens[1]
	log.updatedTime = tokens[2]
	log.byWhom = tokens[3]
	log.origSource = tokens[4]
	log.dataIndex = tokens[5]
	log.enable = ParseEnableToken(tokens[6])
	log.dataType = tokens[7]
	if len(tokens) >= 10:
		log.min = tokens[8]
		log.max = tokens[9]
	if len(tokens) >= 11:
		log.decimate = ParseDecimateToken(tokens[10])
	if len(tokens) >= 12:
		log.smooth = ParseSmoothToken(tokens[11])

""" Write header information for Correlator's internal hole data file format """
def WriteDataHeader(fout, typeStr):
	s = "# " + "Leg Site Hole Core CoreType Section TopOffset BottomOffset Depth Data RunNo " + "\n"
	fout.write(s)
	s = "# " + "Data Type " + typeStr + "\n"
	fout.write(s)
	s = "# " + "Updated Time " + str(datetime.today()) + "\n"
	fout.write(s)
	s = "# Generated By Correlator\n"
	fout.write(s)

def LoadSessionReports():
	reportList = [] # each report is represented as a tuple: (dir, user, time)
	list = os.listdir(glb.DBPath + 'log/')
	for dir in list :
		if dir != ".DS_Store" :
			last = dir.find(".", 0)
			user = dir[0:last]
			start = last + 1
			last = dir.find("-", start)
			last = dir.find("-", last+1)
			last = dir.find("-", last+1)
			time = dir[start:last] + " "
			start = last + 1
			last = dir.find("-", start)
			time += dir[start:last] + ":"
			start = last + 1
			last = dir.find(".", start)
			time += dir[start:last]
			reportTuple = (dir, user, time)
			reportList.append(reportTuple)
	return reportList

def ImportFile(parent, caption):
	dlg = wx.FileDialog(parent, caption, glb.LastDir, "", "*.*")
	result = dlg.ShowModal()
	path = dlg.GetPath() # full file path
	filename = dlg.GetFilename(); # filename only
	glb.LastDir = dlg.GetDirectory()
	dlg.Destroy()
	return result, path, filename

def ImportDownholeLog(parent, curSite):
	result, logPath, filename = ImportFile(parent, "Select a downhole log data file")
	if result == wx.ID_OK:
		dlg = dialog.ImportLogDialog(parent, -1, logPath, curSite)
		if dlg.valid and dlg.ShowModal() == wx.ID_OK:
			return True
	return False

def ImportAffineTable(parent, leg, site):
	result, origPath, filename = ImportFile(parent, "Select an affine table file")
	if result == wx.ID_OK :
		path = origPath
		last = path.find(".xml", 0)
		siteflag = False # does file's site/leg match destinaton site/leg?
		valid = False # is file formatting valid?
		main_form = False # if False, file needs header and conversion to ' \t\ delimiters
		if last < 0 :
			f = open(path, 'r+')
			for line in f :
				if line[0] == "#" :
					main_form = True 
					continue
				modifiedLine = line[0:-1].split()
				if modifiedLine[0] == 'null' :
					continue
				max = len(modifiedLine)
				if max == 1 :
					modifiedLine = line[0:-1].split('\t')
					max = len(modifiedLine)

				if max >= 7 and max <= 9:
					ynValue = modifiedLine[6].strip()
					if ynValue in ["N", 'Y']:
						valid = True

				if leg == modifiedLine[0] and site == modifiedLine[1].lstrip():
					siteflag = True 
				else:
					valid = False 

				break
			f.close()

			if valid == True and main_form == False :
				tmpFile = "\\.tmp_table" if sys.platform == "win32" else "/.tmp_table"
				ReformatFile(path, glb.LastDir + tmpFile, "Affine")
				path = glb.LastDir + tmpFile

		else: # XML file
			tmpFile = "\\.tmp_table" if sys.platform == 'win32' else "/.tmp_table"
			path = xml_handler.ConvertFromXML(path, glb.LastDir + tmpFile)
			handler = xml_handler.GetHandler()
			if handler.type == "affine table":
				valid = True
			if handler.site == site and handler.leg == leg:
				siteflag = True
			else:
				valid = False 

		if valid:
			glb.OnShowMessage("Information", "Successfully imported", 1)
			return model.AffineData(file=path, origSource=origPath)
		elif siteflag:
			glb.OnShowMessage("Error", "File doesn't match expected affine format", 1)
		else:
			glb.OnShowMessage("Error", "File isn't for " + leg + "-" + site, 1)
		
		return None


def ImportSpliceTable(parent, leg, site):
	result, origPath, filename = ImportFile(parent, "Select a splice table file")
	if result == wx.ID_OK :
		path = origPath
		last = path.find(".xml", 0)
		valid = False
		main_form = False
		if last < 0 :
			f = open(path, 'r+')
			valid = False
			for line in f :
				if line[0] == "#" :
					main_form = True 
					continue
				modifiedLine = line[0:-1].split()
				if modifiedLine[0] == 'null' :
					continue
				max = len(modifiedLine)
				if max == 1 :
					modifiedLine = line[0:-1].split('\t')
					max = len(modifiedLine)

				if max == 19 and modifiedLine[9].lower().strip() == 'tie':
					valid = True 
				#print "[DEBUG] " + site + " = " + modifiedLine[0] + " ? "
				if site == modifiedLine[0] :
					siteflag = True
				else :
					valid = False 
				break
			f.close()
			if valid == True and main_form == False :
				tmpFile = "\\.tmp_table" if sys.platform == "win32" else "/.tmp_table"
				ReformatFile(path, glb.LastDir + tmpFile, "Splice")
				path = glb.LastDir + tmpFile
		else: # XML file
			tmpFile = "\\.tmp_table" if sys.platform == 'win32' else "/.tmp_table"
			path = xml_handler.ConvertFromXML(path, glb.LastDir + tmpFile)
			handler = xml_handler.GetHandler()
			if handler.type == "splice table":
				valid = True
			if handler.site == site and handler.leg == leg:
				siteflag = True
			else:
				valid = False

		if valid:
			glb.OnShowMessage("Information", "Successfully imported", 1)
			return model.SpliceData(file=path, origSource=origPath)
		elif siteflag == True :
			glb.OnShowMessage("Error", "File doesn't match expected splice format", 1)
		else :
			glb.OnShowMessage("Error", "File isn't for " + leg + "-" + site, 1)
			
		return None
	
def ImportELDTable(parent, leg, site):
	result, origPath, filename = ImportFile(parent, "Select an ELD table file")
	if result == wx.ID_OK:
		path = origPath
		last = path.find(".xml", 0)
		valid = False
		main_form = False
		if last < 0 :
			f = open(path, 'r+')
			valid = False
			for line in f :
				modifiedLine = line[0:-1].split(' \t')
				max = len(modifiedLine)
				if max == 1 :
					modifiedLine = line[0:-1].split('\t')
					max = len(modifiedLine)
					if max == 1 :
						modifiedLine = line[0:-1].split()
						if modifiedLine[0] == 'null' :
							continue
						max = len(modifiedLine)

				eld_leg = ''
				eld_site = ''
				for k in range(1, max) :
					if modifiedLine[k] == 'Leg' :
						eld_leg = modifiedLine[k+1]			
					elif modifiedLine[k] == 'Site' :
						eld_site = modifiedLine[k+1]			
						break

				if line[0] == "E" : 
					valid = True

				if eld_leg.find(leg, 0) >= 0 and eld_site.find(site,0) >= 0 : 
					siteflag = True 
				else :
					valid = False 
				break
			f.close()
			if valid == True and main_form == False :
				tmpFile = "\\.tmp_table" if sys.platform == "win32" else "/.tmp_table"
				ReformatFile(path, glb.LastDir + tmpFile, "ELD")
				path = glb.LastDir + tmpFile
		else :
			tmpFile = "\\.tmp_table" if sys.platform == 'win32' else "/.tmp_table"
			path = xml_handler.ConvertFromXML(path, glb.LastDir + tmpFile)
			handler = xml_handler.GetHandler()
			if handler.type == "eld table":
				valid = True
			if handler.site == site and handler.leg == leg:
				siteflag = True
			else:
				valid = False 

		if valid == True :
			glb.OnShowMessage("Information", "Successfully imported", 1)
			return model.EldData(file=path, origSource=origPath)
		elif siteflag == True :
			glb.OnShowMessage("Error", "File doesn't match expected ELD format", 1)
		else :
			glb.OnShowMessage("Error", "File isn't for " + leg + "-" + site, 1)
		return None

# add header information to file, convert space or tab delimiters to
# Correlator's internal space+tab delimiter
# (this routine formerly dbmanager OnFORMATTING())
def ReformatFile(source, dest, tableType):
	fin = open(source, 'r+')
	#print "[DEBUG] FORMATTING : " + source + " to " + dest
	fout = open(dest, 'w+')

	if tableType == "Affine" :
		fout.write("# Leg, Site, Hole, Core No, Section Type, Depth Offset, Y/N\n")
		fout.write("# Generated By Correlator\n")
	elif tableType == "Splice" :
		fout.write("# Site, Hole, Core No, Section Type, Section No, Top, Bottom, Mbsf, Mcd, TIE/APPEND Site, Hole, Core No, Section Type, Section No, Top, Bottom, Mbsf, Mcd\n")
		fout.write("# Generated By Correlator\n")

	for line in fin :
		max = len(line)
		if max <= 1 :
			continue
		if tableType == "ELD" :
			if line[0] == "E" or line[0] == "O" or line[0] == "A" :
				fout.write(line)
				continue

		flag = False
		for i in range(max) :
			if line[i] == ' ' :
				if flag == False :		
					flag = True 
					fout.write(" \t")
			elif line[i] == '\t' :
				if flag == False  :
					fout.write(" \t")
					flag = True 
			else :
				flag = False
				fout.write(line[i])

	fout.close()
	fin.close()
	
def MoveFile(src, dest, copy=True):
	if sys.platform == 'win32':
		workingdir = os.getcwd()
		cmd = 'copy ' + src + ' ' + dest
		os.system(cmd)
		if not copy:
			cmd = 'del \"' + src + '\"'
			os.system(cmd)
		os.chdir(workingdir)
	else:
		cmd = 'cp \"' + src + '\" \"' + dest + '\"'
		os.system(cmd)
		if not copy:
			cmd = 'rm \"' + src + '\"'
			os.system(cmd)
			
def DeleteFile(filepath):
	if sys.platform == 'win32' :
		workingdir = os.getcwd()
		#os.chdir(glb.DBPath + 'db/' + title + '/')
		os.system('del \"' + filepath + '\"')
		os.chdir(workingdir)
		#self.parent.logFileptr.write("Delete " + filename + "\n\n")
	else :
		os.system('rm \"'+ filepath + '\"')
		#self.parent.logFileptr.write("Delete " + filename + "\n\n")	

# launch doctests if this module is run
if __name__ == "__main__":
	import doctest
	doctest.testmod()
