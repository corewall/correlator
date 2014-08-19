#!/usr/bin/env python

## For Mac-OSX
#/usr/bin/env pythonw

import platform
platform_name = platform.uname()

import random, sys, os, re, time, ConfigParser, string
from datetime import datetime
import xml.sax

from importManager import py_correlator

import constants as const
import globals as glb
import model


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
	loadedSites = []
	for siteName in siteNames:
		site = model.SiteData(siteName)

		siteFile = open(glb.DBPath + 'db/' + siteName + '/datalist.db', 'r+')
		siteLines = siteFile.readlines()
		for idx, line in enumerate(siteLines):
			siteLines[idx] = siteLines[idx].strip('\r\n')

		ParseHoleSets(site, siteLines)
		ParseHoles(site, siteLines)
		ParseOthers(site, siteLines)
		#site.dump()
		loadedSites.append(site)

	return loadedSites

def LoadSiteNames():
	dbRootFile = open(glb.DBPath + 'db/datalist.db', 'r+')
	loadedSites = []
	for site in dbRootFile:
		site = site.strip()
		if site == '' or site in loadedSites:
			continue
		else:
			loadedSites.append(site)
	return sorted(loadedSites)

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
			ParseTableData(strat, tokens)
			site.stratTables.append(strat)
		elif tokens[0] == 'age':
			age = model.AgeTable()
			ParseTableData(age, tokens)
			site.ageTables.append(age)
		elif tokens[0] == 'series':
			series = model.SeriesTable()
			ParseTableData(series, tokens)
			site.seriesTables.append(series)
		elif tokens[0] == 'image':
			image = model.ImageTable()
			ParseTableData(image, tokens)
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
