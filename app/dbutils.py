#!/usr/bin/env python

## For Mac-OSX
#/usr/bin/env pythonw

import platform
platform_name = platform.uname()

import random, sys, os, re, time, ConfigParser, string
from datetime import datetime

from importManager import py_correlator

import constants as const
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

def ImportAffineTable(leg, site):
	opendlg = wx.FileDialog(self, "Select a affine table file", glb.LastDir, "", "*.*")
	ret = opendlg.ShowModal()
	path = opendlg.GetPath()
	filename = opendlg.GetFilename();
	source_filename = path
	glb.LastDir = opendlg.GetDirectory()
	opendlg.Destroy()

	if ret == wx.ID_OK :
		last = path.find(".xml", 0)
		valid = False
		main_form = False
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

				if max == 9 or max == 7 or max == 8 :
					if modifiedLine[6] == '\tY' or modifiedLine[6] == '\tN' :
						valid = True 
					elif modifiedLine[6] == 'Y' or modifiedLine[6] == 'N' :
						valid = True 
					elif modifiedLine[6] == 'Y\r' or modifiedLine[6] == 'N\r' :
						valid = True 
					elif modifiedLine[6] == '\tY\r' or modifiedLine[6] == '\tN\r' :
						valid = True 

				if leg == modifiedLine[0] and site == RemoveFRONTSPACE(modifiedLine[1]) :
					siteflag = True 
				else :
					valid = False 

				break
			f.close()

			if valid == True and main_form == False :
				filename = ".tmp_table"
				if sys.platform == 'win32' :
					OnFORMATTING(path, glb.LastDir + "\\.tmp_table", "Affine")
					path = glb.LastDir + "\\.tmp_table"
				else :
					OnFORMATTING(path, glb.LastDir + "/.tmp_table", "Affine")
					path = glb.LastDir + "/.tmp_table"

		else : # last >= 0
			tmpFile = "\\.tmp_table" if sys.platform == 'win32' else "/.tmp_table"
			foo = xml_handler.ConvertFromXML(glb.LastDir + tmpFile)
#			self.handler.init()
#			if sys.platform == 'win32' :
#				self.handler.openFile(glb.LastDir + "\\.tmp_table")
#				self.parser.parse(path)
#				path = glb.LastDir + "\\.tmp_table"
#			else :
#				self.handler.openFile(glb.LastDir + "/.tmp_table")
#				self.parser.parse(path)
#				path = glb.LastDir + "/.tmp_table"
#			self.handler.closeFile()
			
			filename = ".tmp_table"
			if self.handler.type == "affine table" :
				valid = True
			if self.handler.site == site and self.handler.leg == leg :
				siteflag = True
			else :
				valid = False 

		if valid == True :
			type = self.Add_TABLE('AFFINE' , 'affine', False, True, source_filename)
			glb.OnShowMessage("Information", "Successfully imported", 1)
		elif siteflag == True :
			glb.OnShowMessage("Error", "It is not affine table", 1)
		else :
			glb.OnShowMessage("Error", "It is not for " + self.title, 1)
			
def RemoveFRONTSPACE(self, line):
	max = len(line)
	for i in range(max) :
		if line[i] != ' ' and line[i] != '\t' and line[i] != '\r' :
			return line[i:max]
	return line 

def OnFORMATTING(self, source, dest, tableType):
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
