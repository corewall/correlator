#!python.exe

import copy

import platform
import os
import socket
import sys
import traceback

platform_name = platform.uname()
if platform_name[5] == "i386":
	os.system('sh swap_intel_library')
elif platform_name[5] == "powerpc":
	os.system('sh swap_ppc_library')

#!/usr/bin/env python

## For Mac-OSX
#/usr/bin/env pythonw

import wx
from wx.lib import plot
import pandas
import UniversalAnalytics

import random, sys, re, time, ConfigParser, string, uuid, pickle
import getpass
from datetime import datetime

from importManager import py_correlator

import canvas
import dialog
import frames
import dbmanager
import version as vers
from affine import AffineBuilder, AffineCoreInfo, aci, acistr, isTie, isSet, isImplicit
import splice
import tabularImport
import prefs

app = None
Prefs = None
User_Dir = os.path.expanduser("~")

myPath = User_Dir  + "/Documents/Correlator/" + vers.BaseVersion + "/"
if platform_name[0] == "Windows":
	myPath =  User_Dir  + "\\Correlator\\" + vers.BaseVersion + "\\"
myTempPath = myPath

global_logName = "" 
global_logFile = None 

def opj(path):
	"""Convert paths to the platform-specific separator"""
	return apply(os.path.join, tuple(path.split('/')))

class MainFrame(wx.Frame):
	def __init__(self, winsize, user):
		wx.Frame.__init__(self, None, -1, "Correlator " + vers.ShortVersion,
						 wx.Point(0,100), winsize, style=wx.DEFAULT_FRAME_STYLE | wx.FRAME_FLOAT_ON_PARENT)

		self.statusBar = self.CreateStatusBar()

		self.user = user
		self.Width = winsize[0]
		self.Height = winsize[1]
		#self.Width, self.Height = self.GetClientSizeTuple()
		self.scroll = 1 
		self.half = (self.Width / 2) - 32 
		# make the menu
		self.SetMenuBar(self.CreateMenu())
		
		self.sectionSummary = None
		self.affineManager = AffineController(self)
		self.spliceManager = SpliceController(self)

		self.RawData = ""
		self.SmoothData = ""
		self.CoreStart =0
		self.CoreLast =0
		self.ScrollMax =0
		self.HScrollMax =0
		self.CoreNo = 0
		self.depthStep = 0.11
		self.minDepthStep = 0.11
		self.winLength = 1.0 
		self.leadLag = 1.0 
		self.min = 999
		self.max = -999
		self.AffineChange = False 
		self.SpliceChange = False 
		self.EldChange = False 
		self.AgeChange = False 
		self.TimeChange = False 
		self.leg = None
		self.site = None
		self.shiftHole = None 
		self.shiftCore = None 
		self.shiftOffset = None 
		self.shiftType = None 
		self.spliceHoleA = None 
		self.spliceCoreA = None 
		self.spliceDepthA = None 
		self.spliceHoleB = None 
		self.spliceCoreB = None 
		self.spliceType = None 
		self.showCompositePanel = 1 
		self.showSplicePanel = 0 
		self.showELDPanel = 0 
		self.showReportPanel = 1
		self.spliceDepthA = None
		self.spliceDepthB = None
		self.fulls =0
		self.selectedColumn = 0
		self.compositePanel = "" 
		self.splicePanel = ""
		self.spliceIntervalPanel = "" 
		self.eldPanel = "" 
		self.filterPanel = ""
		self.autoPanel = ""
		self.agePanel = ""
		self.optPanel = ""
		self.smoothDisplay = 1 
		self.splicedOpened = 0
		self.noOfHoles = 0
		self.noOfSameTypeHoles = 0
		self.logFileptr = global_logFile
		self.logName = global_logName
		self.Window = canvas.DataCanvas(self)
		self.topMenu = frames.TopMenuFrame(self)
		self.dataFrame = None
		self.PrevDataType = "" 
		self.CurrentDir = ""
		self.CurrentType = ""
		self.CurrentDataNo = -1
		self.LOCK = 0
		self.IDLE = 0
		self.FOCUS = 1
		self.Directory = ""
		self.DBPath = "-"
		self.client = None

		self.Window.affineBroadcaster.addListener(self.compositePanel.TiePointCountChanged)

		wx.EVT_IDLE(self, self.OnIDLE)

	def INIT_CHANGES(self):
		self.AffineChange = False 
		self.SpliceChange = False 
		self.EldChange = False 
		self.AgeChange = False 
		self.TimeChange = False 

	def OnIDLE(self, event):
		if app == None:
			return

		if app.IsActive() == True:
			if self.FOCUS == 0: 
				if self.mitool.IsChecked() == True:
					self.topMenu.Show(True)
					self.topMenu.Iconize(False)
				self.FOCUS = 1

			if self.IsIconized():
				if self.IDLE == 0:
					self.topMenu.Show(False)
					if platform_name[0] == "Windows":	
						self.topMenu.Iconize(True)
					self.IDLE = 1
			else:
				if self.IDLE == 1:
					if self.mitool.IsChecked():
						self.topMenu.Show(True)
					if platform_name[0] == "Windows":	
						self.topMenu.Iconize(False)
					self.IDLE = 0 
		else:
			self.topMenu.Show(False)
			if platform_name[0] == "Windows":	
				self.topMenu.Iconize(True)
			self.FOCUS = 0 

	def CheckAutoELD(self):
		if (self.autoPanel.selectedNo != -1) and (self.autoPanel.ApplyFlag == 0):
			return False
		return True

	def UpdateSize(self, width, height):
		self.Width = width 
		self.Height = height 

	def DoesFineTune(self):
		if self.Window.SpliceData != []:
			if self.AffineChange == True:
				return  True
		return False

	def GetPref(self, prefkey, default=""):
		return Prefs.get(prefkey, default)

	def CreateMenu(self):
		self.statusBar.SetStatusText('Done')

		# File
		menuFile = wx.Menu()
		menuBar = wx.MenuBar()

		prefsItem = menuFile.Append(wx.ID_PREFERENCES, "&Preferences...\tCTRL+,", "Edit application preferences")
		self.Bind(wx.EVT_MENU, self.OnPreferences, prefsItem)

		#self.miFileDB = menuFile.Append(-1, "&Access Database\tCtrl-E", "Access database")

		#self.miCleanFiles = menuFile.Append(-1, "Formatting Data Files", "Formatting data file")
		#self.Bind(wx.EVT_MENU, self.OnFormatData, self.miCleanFiles)

		self.miPath = menuFile.Append(-1, "Change Data Repository Path", "Edit current data repository path")
		self.Bind(wx.EVT_MENU, self.OnPATH, self.miPath)

		self.miImport = menuFile.Append(-1, "Import Data from Existing Repository", "Import data from one or more sites in an existing repository")
		self.Bind(wx.EVT_MENU, self.OnIMPORT_DATA, self.miImport)

		menuFile.AppendSeparator()

		# self.miConnection = menuFile.Append(-1, "Connect to Corelyzer", "Connect to Corelyzer")
		# self.Bind(wx.EVT_MENU, self.OnCONNECTION, self.miConnection)

		# menuFile.AppendSeparator()

		self.miFileSave = menuFile.Append(wx.ID_SAVE, "", "Save changes")
		self.Bind(wx.EVT_MENU, self.OnSave, self.miFileSave)

		menuFile.AppendSeparator()

		# 1/15/2019 brg: We've elected to hide these menu items for now. Functionality
		# is available from other controls, or unused (Core-Log) at present.
		# self.miFileClear = menuDummy.Append(-1, "Clear All Ties\tCtrl-C", "Clear all")
		# self.Bind(wx.EVT_MENU, self.OnClearAllData, self.miFileClear)

		# self.miFileClearco = menuDummy.Append(-1, "Clear All Shifts", "Clear composite ties")
		# # self.Bind(wx.EVT_MENU, self.OnClearComposite, self.miFileClearco)

		# self.miFileClearsp = menuDummy.Append(-1, "Clear All Splice Ties", "Clear splice ties")
		# self.Bind(wx.EVT_MENU, self.OnClearSpliceTie, self.miFileClearsp)

		# self.miFileClearsa = menuDummy.Append(-1, "Clear All Core-Log Ties", "Clear core-log ties")
		# self.Bind(wx.EVT_MENU, self.OnClearSAGANTie, self.miFileClearsa)

		# menuFile.AppendSeparator()

		miFileExit = menuFile.Append(wx.ID_EXIT, "&Exit\tCtrl-X", "Exit Correlator")
		self.Bind(wx.EVT_MENU, self.OnExitAction, miFileExit)
		self.Bind(wx.EVT_CLOSE, self.OnClose)
		menuBar.Append(menuFile, "&File")

		# View 
		menuView = wx.Menu()
		self.mitool = menuView.AppendCheckItem(-1, "Show Toolbar", "Show/hide toolbar")
		self.mitool.Check(True)
		self.Bind(wx.EVT_MENU, self.SHOWToolbar, self.mitool)

		menuView.AppendSeparator()
		self.miplot = menuView.AppendCheckItem(-1, "Plot Discrete Points", "Plot data as points instead of a line")
		self.Bind(wx.EVT_MENU, self.SETPlotMode, self.miplot)

		self.miptsizeup = menuView.Append(-1, "Increase Point Size", "Make discrete data points larger")
		self.Bind(wx.EVT_MENU, self.SetPT_SIZEUP, self.miptsizeup)
		
		self.miptsizeDown = menuView.Append(-1, "Decrease Point Size", "Make discrete data points smaller")
		self.Bind(wx.EVT_MENU, self.SetPT_SIZEDOWN, self.miptsizeDown)

		menuView.AppendSeparator()
		self.mitiesizeup = menuView.Append(-1, "Increase Tie Point Size", "Make affine tie points larger")
		self.Bind(wx.EVT_MENU, self.SetTIE_SIZEUP, self.mitiesizeup)

		self.mitiesizeDown = menuView.Append(-1, "Decrease Tie Point Size", "Make affine tie points smaller")
		self.Bind(wx.EVT_MENU, self.SetTIE_SIZEDOWN, self.mitiesizeDown)

		self.mitiewidthup = menuView.Append(-1, "Increase Tie Line Thickness", "Make TIE lines thicker")
		self.Bind(wx.EVT_MENU, self.SetTIE_WIDTHUP, self.mitiewidthup)
		self.mitiewidthDown = menuView.Append(-1, "Decrease Tie Line Thickness", "Make TIE lines thinner")
		self.Bind(wx.EVT_MENU, self.SetTIE_WIDTHDOWN, self.mitiewidthDown)

		menuView.AppendSeparator()
		self.misecond = menuView.AppendCheckItem(-1, "Show Splice Window", "Splice Window")#Splice/Log Window", "Splice/Log window")
		self.misecond.Check(True)
		self.Bind(wx.EVT_MENU, self.SHOWSplice, self.misecond)

		# self.miIndependentScroll = menuView.AppendCheckItem(-1, "Independent Splice Scrollbar", "Composite and splice areas scroll independently")
		# self.miIndependentScroll.Check(False)
		# self.Bind(wx.EVT_MENU, self.IndependentScrollSelected, self.miIndependentScroll)

		# 11/2/2013 brg: Removing for now - graph area layouts can get pretty screwed up
		# with repeated font size changes (the top graph info area can end up in negative
		# coordinates and thus not show up). If we need this functionality back, use actual
		# font metrics instead of the current "add or subtract 5 for each increment/decrement
		# of font size" approach in SETTextSizeUp/Down(). Also, don't load/save "fontsize"
		# preference, which retains the custom fontsize value.
		#menuView.AppendSeparator()
		#self.mitextsizeup = menuView.Append(-1, "Text Size Up", "Text Size Up")
		#self.Bind(wx.EVT_MENU, self.SETTextSizeUp, self.mitextsizeup)
		#self.mitextsizeDown = menuView.Append(-1, "Text Size Down", "Text Size Down")
		#self.Bind(wx.EVT_MENU, self.SETTextSizeDown, self.mitextsizeDown)

		menuView.AppendSeparator()
		self.miScrollbigger = menuView.Append(-1, "Wider Scrollbars", "Make scrollbars wider")
		self.Bind(wx.EVT_MENU, self.UseWideScrollbars, self.miScrollbigger)
		self.miScrollnormal = menuView.Append(-1, "Narrower Scrollbars", "Make scrollbars narrower")
		self.Bind(wx.EVT_MENU, self.UseNarrowScrollbars, self.miScrollnormal)
		
		menuBar.Append(menuView, "&View")

		# Help 
		menuHelp = wx.Menu()
		self.miAbout = menuHelp.Append(wx.ID_ABOUT, "About Correlator\tF1", "")
		self.Bind(wx.EVT_MENU, self.OnAbout, self.miAbout)
		menuBar.Append(menuHelp, "&Help")

		# Debug
		menuDebug = wx.Menu()
		self.miDebugShowBounds = menuDebug.AppendCheckItem(-1, "Show Plot Bounds", "Show colored lines indicating bounds of hole plot rectangles, etc")
		self.Bind(wx.EVT_MENU, self._debugShowBounds, self.miDebugShowBounds)
		self.miDebugShowFPS = menuDebug.AppendCheckItem(-1, "Show Frames Per Second (FPS)", "Show frames drawn per second...move mouse continuously for meaningful values")
		self.Bind(wx.EVT_MENU, self._debugShowFPS, self.miDebugShowFPS)
		menuBar.Append(menuDebug, "&Debug")

		# self.OnDisableMenu(0, False)

		# bind keystrokes to the frame
		# self.Bind(wx.EVT_KEY_DOWN, self.OnKeyEvent)
		return menuBar
	
	def OnPreferences(self, event):
		dlg = dialog.ApplicationPreferencesDialog(self, Prefs.getAll())
		if dlg.ShowModal() == wx.ID_OK:
			Prefs.setAll(dlg.prefsMap)
			Prefs.write()

	def OnIMPORT_DATA(self, event):
		opendlg = wx.DirDialog(self, "Select Repository Directory to Import", myPath)
		ret = opendlg.ShowModal()
		path = opendlg.GetPath()
		opendlg.Destroy()
		updated = False
		if ret == wx.ID_OK:
			# check....
			if os.access(path + '/datalist.db', os.F_OK) == False:
				self.OnShowMessage("Error", "It doesn't have datalist.db", 1)
				return
			datalist = []
			dblist_f = open(self.DBPath + 'db/datalist.db', 'r+')
			for line in dblist_f:
				if len(line) > 0:
					token = line.split()
					if len(token) == 0:
						continue
					first_token = token[0]
					datalist.append(first_token)
			dblist_f.close()

			dblist_f = open(self.DBPath + 'db/datalist.db', 'a+')
			importdb_f = open(path + '/datalist.db', 'r+')
			workingdir = os.getcwd()
			os.chdir(path)
			single_flag = False
			first_token = ""
			for line in importdb_f:
				if len(line) > 0:
					token = line.split()
					if len(token) == 0:
						continue
					first_token = token[0]
					if first_token.find("-", 0) >= 0:
						found_flag = False
						for dataitem in datalist: 
							if first_token == dataitem:
								found_flag = True 
								break
						if found_flag == True:
							os.chdir(workingdir)
							self.OnShowMessage("Error", "There is already " + first_token, 1)
							os.chdir(path)
						else:
							dblist_f.write("\n"+ first_token+"\n")
							cmd = "cp -rf " +  first_token + " " + self.DBPath + "db/"
							if sys.platform == 'win32':
								os.chdir(self.DBPath+ "db")
								if os.access(first_token, os.F_OK) == False:
									os.mkdir(first_token)
								os.chdir(path + "\\" + first_token)
								cmd = "copy * \"" + self.DBPath + "db\\" + first_token + "\""
								#print "[DEBUG] " + cmd
								os.system(cmd)								
								os.chdir(path)
							else:
								#print "[DEBUG] " + cmd
								os.system(cmd)
							updated = True 
							if self.logFileptr != None:
								global_logFile.write("Add Data Repository: " + first_token + "\n")
					else:
						single_flag = True 
						break
			if single_flag == True:
				first_token = ""
				for line in importdb_f:
					if len(line) > 0:
						token = line.split()
						if len(token) == 0:
							continue
						if token[0] == "file:":
							filename = token[1]
							start = 0
							last = filename.find("-", start)
							start = last + 1
							last = filename.find("-", start)
							first_token = filename[0:last]
							break
				found_flag = False
				for dataitem in datalist: 
					if first_token == dataitem:
						found_flag = True 
						break
				if found_flag == True:
					os.chdir(workingdir)
					self.OnShowMessage("Error", "There is already " + first_token, 1)
					os.chdir(path)
				else:
					dblist_f.write("\n"+ first_token+"\n")
					os.chdir(self.DBPath+ "db")
					if os.access(first_token, os.F_OK) == False:
						os.mkdir(first_token)
					os.chdir(path)
					cmd = "cp -rf * " + self.DBPath + "db/" + first_token
					if sys.platform == 'win32':
						cmd = "copy * \"" + self.DBPath + "db\\" + first_token + "\""
						#print "[DEBUG] " + cmd
						os.system(cmd)
					else:
						#print "[DEBUG] " + cmd
						os.system(cmd)
					updated = True 
					if self.logFileptr != None:
						global_logFile.write("Add Data Repository: " + first_token + "\n")
			os.chdir(workingdir)
			importdb_f.close()
			dblist_f.close()

			if updated == True:
				self.dataFrame.dataPanel.ClearGrid()
				self.dataFrame.tree.DeleteAllItems()
				self.dataFrame.root = self.dataFrame.tree.AddRoot("Root")
				self.dataFrame.repCount = 0
				self.dataFrame.OnLOADCONFIG()
				self.OnShowMessage("Information", "Successfully Imported", 1)


	def IMPORTRepository(self):
		while True:
			opendlg = wx.DirDialog(self, "Select Previous Repository Directory", myPath)
			ret = opendlg.ShowModal()
			path = opendlg.GetPath()
			opendlg.Destroy()
			if ret == wx.ID_OK:
				if os.access(path + '/default.cfg', os.F_OK) == False:
					self.OnShowMessage("Error", "It's not Repository Root", 1)
					continue
				if os.access(path + '/db/datalist.db', os.F_OK) == False:
					self.OnShowMessage("Error", "It's not Repository Root", 1)
					continue

				workingdir = os.getcwd()
				os.chdir(path)
				cmd = "cp -rf * " + myPath
				if sys.platform == 'win32':
					cmd = "copy * \"" + myPath + "\""
				os.system(cmd)
				os.chdir(workingdir)

				#cmd = "rm -rf  " + path
				#if sys.platform == 'win32':
				#	cmd = "rd /s /q " + path
				#os.system(cmd)
				break
			else:
				break

	def SHOWToolbar(self, event):
		self.topMenu.Show(self.mitool.IsChecked())

	def SETPlotMode(self, event):
		if self.miplot.IsChecked() == False:
			self.Window.DiscretePlotMode = 0 
		else:
			self.Window.DiscretePlotMode = 1
		self.Window.UpdateDrawing()
		

	def SHOWSplice(self, event):
		if self.misecond.IsChecked() == True:
			self.OnActivateWindow(1)
		else:
			self.OnActivateWindow(0)

	# def IndependentScrollSelected(self, event):
	# 	self.SetIndependentScroll(self.miIndependentScroll.IsChecked())

	def OnUpdateHelp(self):
		self.Window.helpText.Clear()
		self.Window.helpText.LoadFile("help/help_index.txt")

	def OnUpdateReport(self):
		self.logFileptr.close()
		#self.Window.reportText.Clear()
		#self.Window.reportText.LoadFile(self.DBPath + global_logName)
		self.OnReOpenLog()

	def OnReOpenLog(self):
		global_logFile = open(self.DBPath + global_logName, "a+")
		self.logFileptr = global_logFile

	def SetPT_SIZEUP(self, evt):
		self.Window.DiscreteSize = self.Window.DiscreteSize + 1
		self.Window.UpdateDrawing()

	def SetPT_SIZEDOWN(self, evt):
		self.Window.DiscreteSize = self.Window.DiscreteSize - 1
		if self.Window.DiscreteSize < 1:
			self.Window.DiscreteSize = 1
		self.Window.UpdateDrawing()

	def SetTIE_SIZEUP(self, evt):
		self.Window.tieDotSize = self.Window.tieDotSize + 2 
		self.Window.UpdateDrawing()

	def SetTIE_SIZEDOWN(self, evt):
		self.Window.tieDotSize = self.Window.tieDotSize - 2 
		if self.Window.tieDotSize < 8:
			self.Window.tieDotSize = 8 
		self.Window.UpdateDrawing()

	def SetTIE_WIDTHUP(self, evt):
		self.Window.tieline_width +=  1
		if self.Window.tieline_width > 3:
			self.Window.tieline_width = 3
		self.Window.UpdateDrawing()

	def SetTIE_WIDTHDOWN(self, evt):
		self.Window.tieline_width -=  1
		if self.Window.tieline_width < 1:
			self.Window.tieline_width = 1 
		self.Window.UpdateDrawing()

	def SETTextSizeUp(self, evt):
		size = self.Window.stdFont.GetPointSize() + 1
		self.Window.stdFont.SetPointSize(size)
		
		self.Window.startDepthPix = self.Window.startDepthPix + 5
		self.Window.startAgeDepth = self.Window.startAgeDepth + 5
		self.Window.UpdateDrawing()
		
	def SETTextSizeDown(self, evt):
		size = self.Window.stdFont.GetPointSize() - 1
		self.Window.stdFont.SetPointSize(size)
		
		self.Window.startDepthPix = self.Window.startDepthPix - 5
		self.Window.startAgeDepth = self.Window.startAgeDepth -5		
		self.Window.UpdateDrawing()
		
	def UseWideScrollbars(self, evt):
		self.Window.ScrollSize = 25
		self.UPDATESCROLL()
		self.Window.UpdateDrawing()
							
	def UseNarrowScrollbars(self, evt):
		self.Window.ScrollSize = 15
		self.UPDATESCROLL()	
		self.Window.UpdateDrawing()

	def _debugShowBounds(self, evt):
		self.Window.showBounds = self.miDebugShowBounds.IsChecked()
		self.Window.UpdateDrawing()

	def _debugShowFPS(self, evt):
		self.Window.showFPS = self.miDebugShowFPS.IsChecked()
		self.Window.UpdateDrawing()
	
	# scrollTuple: (bitmap, x, y)
	def ScaleScrollbar(self, scrollKey, newx, newy, horizontal=False):
		bitmap, x, y = self.Window.DrawData[scrollKey]
		image = bitmap.ConvertToImage() # must convert to bitmap to rescale

		# rescale based on scrollbar's orientation
		scaleWidth = self.Window.ScrollSize if not horizontal else image.GetWidth()
		scaleHeight = image.GetHeight() if not horizontal else self.Window.ScrollSize
		image.Rescale(scaleWidth, scaleHeight)

		newScrollData = (image.ConvertToBitmap(), x if newx == None else newx, y if newy == None else newy)
		self.Window.DrawData[scrollKey] = newScrollData

	def UPDATESCROLL(self):
		self.ScaleScrollbar("MovableSkin", -self.Window.ScrollSize - 5, None)
		self.ScaleScrollbar("Skin", -self.Window.ScrollSize, None)
		self.ScaleScrollbar("HScroll", None, -self.Window.ScrollSize, horizontal=True)

	# 1/15/2019 hiding these menu items				
	# def OnDisableMenu(self, type, enable):
	# 	if type == 1 or type == 0: 
	# 		self.miFileClear.Enable(enable)
	# 		self.miFileClearco.Enable(enable)
	# 		self.miFileClearsp.Enable(enable)
	# 		self.miFileClearsa.Enable(enable)

	# update global Evaluation Graph parameters
	def OnEvalSetup(self, depthStep, winLength, leadLag):
		self.depthStep = depthStep
		self.winLength = winLength
		self.leadLag = leadLag
		py_correlator.setEvalGraph(self.depthStep, self.winLength, self.leadLag)

	def OnAdjustCore(self, opt, type):
		self.Window.OnAdjustCore(opt, type)

	def OnUndoAffineShift(self):
		self.affineManager.undo()
		self.UpdateData()

	def OnUpdateDepth(self, depth):
		self.compositePanel.OnUpdateDepth(depth)
		
	# Preferences "Depth Ruler Scale" min/max changed
	def OnUpdateDepthRange(self, minDepth, maxDepth, updateScroll=True):
		self.Window.rulerStartDepth = minDepth
		self.Window.SPrulerStartDepth = minDepth
		x = (self.Window.Height - self.Window.startDepthPix)
		self.Window.pixPerMeter = x / float(maxDepth - minDepth)

		if updateScroll:
			self.Window.UpdateScroll(1)
			self.Window.UpdateScroll(2)
		self.Window.InvalidateImages()
		self.Window.UpdateDrawing()
		self.Window.UpdateDrawing() # brgtodo 9/6/2014 core area doesn't update completely without, why?
		
	# update start depth of graph area
	def OnUpdateStartDepth(self, startDepth, updateScroll=True):
		self.Window.rulerStartDepth = startDepth
		self.Window.SPrulerStartDepth = startDepth
		# no need to mess with self.Window.pixPerMeter, keep it as is
		if updateScroll:
			self.Window.UpdateScroll(1)
			self.Window.UpdateScroll(2)
		self.Window.UpdateDrawing()
		self.Window.UpdateDrawing() # brgtodo 9/6/2014 core area doesn't update completely without, why?

	def OnUpdateDepthStep(self):
		self.depthStep = py_correlator.getAveDepStep()
		self.minDepthStep = int(10000.0 * float(self.depthStep)) / 10000.0

		self.compositePanel.OnUpdatePlots()
		self.splicePanel.OnUpdate()
		self.eldPanel.OnUpdate()
		self.OnEvalSetup(self.depthStep, self.winLength, self.leadLag)

	def OnUpdateGraphSetup(self, idx):
		if idx == 1:
			self.compositePanel.OnUpdatePlots()
		elif idx == 2:
			self.Window.UpdateSpliceEvalPlot()
		elif idx == 3:
			self.eldPanel.OnUpdate()

	def GetSpliceCore(self):
		l = self.Window.GetSpliceCore()
		return l 

	def OnSplice(self):
		self.Window.OnSpliceCore()
		
	def AddSpliceCore(self, coreinfo):
		self.spliceManager.add(coreinfo)

	def OnUndoSplice(self):
		self.Window.OnUndoSplice()

	def OnUpdateGraph(self):
		self.compositePanel.OnUpdateDrawing()
		if self.showSplicePanel == 1: 
			self.spliceIntervalPanel.OnUpdate()
		elif self.showELDPanel == 1:
			self.eldPanel.OnUpdateDrawing()


	# parse returned data from evalcoef/evalcoef_splice and add to appropriate graph
	def OnAddFirstGraph(self, coef, depth1, depth2):
		start = 0
		last = 0
		l = []
		startx = self.leadLag * -1
		numleadLag = int(self.leadLag / self.depthStep) * 2 +1

		offset = 0.0
		win_length = depth2 - self.winLength
		actual_start = 0.0
		max = -1.0
		best = 0
		len_max = len(coef) -1
		for i in range(numleadLag): 
			last = coef.find(",", start)
			if start == last:
				break
			depth = float(coef[start:last])
			start = last +1
			last = coef.find(",", start)
			if start == last:
				break
			value = float(coef[start:last])

			if max < value:
				max = value
				best = depth 
			l.append( (depth, value) ) 
			start = last +1
			if start >= len_max:
				break

		bestdata = [ (best, -0.05), (best, 0.05) ] # best correlation

		if len(l) <= 1:
			l = [ (-1.0, -1.0), (0, 0), (1.0, 1.0) ]

		self.compositePanel.OnAddFirstData(l, bestdata, best)
		if self.showSplicePanel == 1: 
			self.spliceIntervalPanel.OnAddFirstData(l, bestdata, best)
		elif self.showELDPanel == 1:
			self.eldPanel.OnAddFirstData(l, bestdata, best)


	def OnAddGraph(self, coef, depth1, depth2):
		start = 0
		last = 0
		l = []
		startx = self.leadLag * -1
		numleadLag = int(self.leadLag / self.depthStep) * 2 +1
		win_length = depth2 - self.winLength

		max = len(coef) -1
		for i in range(numleadLag): 
			last = coef.find(",", start)
			if start == last:
				break
			depth = float(coef[start:last])
			start = last +1
			last = coef.find(",", start)
			if start == last:
				break
			value = float(coef[start:last])
			l.append( (depth, value) ) 
			start = last +1
			if start >= max:
				break

		self.compositePanel.OnAddData(l)
		if self.showSplicePanel == 1: 
			self.spliceIntervalPanel.OnAddData(l)
		elif self.showELDPanel == 1:
			self.eldPanel.OnAddData(l)

	# Called when Exit menu item or button is used. Pass None
	# for OnClose() event since triggeirng event was a CommandEvent,
	# not a CloseEvent and therefore doesn't have the Veto() method.
	def OnExitAction(self, event):
		self.OnClose(event=None)

	# Bound directly only to wx.EVT_CLOSE, triggered by native window "X"
	# button. In that case event is a CloseEvent, which should be vetoed
	# if user opts to Cancel exit.
	# event - a CloseEvent if triggered by wx.EVT_CLOSE, otherwise None
	def OnClose(self, event):
		if self.client != None:
			if self.Window.HoleData != []: 
				try:
					self.client.send("delete_all\n")
				except Exception, E:
					print "[DEBUG] Disconnect to the corelyzer"
			try:
				self.client.send("quit\n")
			except Exception, E:
				print "[DEBUG] Disconnect to the corelyzer"
			self.client.close()
			self.client = None
			print "[DEBUG] Close connection to Corelyzer"

		if self.CurrentDir != '' and self.UnsavedChanges():
			ret = self.OnShowMessage("About", "Do you want to save changes?", 2)
			if ret == wx.ID_OK:
				self.topMenu.OnSAVE(event)
				self.AffineChange = False
				self.SpliceChange = False
				self.EldChange = False
				self.AgeChange = False
				self.TimeChange = False

		ret = self.OnShowMessage("About", "Do you want to Exit?", 2)
		if ret == wx.ID_CANCEL:
			if event is not None:
				event.Veto()
			return

		self.SavePreferences()
		if self.logFileptr != None:
			s = "\n" + str(datetime.today()) + "\n"
			self.logFileptr.write(s)
			self.logFileptr.write("Close of Session.\n\n")
			self.logFileptr.close()
			self.logFileptr = None

		self.Window.Close(True)
		self.dataFrame.Close(True)
		self.topMenu.Close(True)
		self.Destroy()
		app.ExitMainLoop()

	def UnsavedChanges(self):
		affineChange = self.affineManager.isDirty()
		spliceChange = self.spliceManager.isDirty()
		return affineChange or spliceChange

	# show/hide splice window
	def OnActivateWindow(self, event):
		if self.Window.spliceWindowOn == 1:
			self.Window.spliceWindowOn = 0
			self.Window.splicerBackX = self.Window.splicerX # save old splicerX
			self.Window.splicerX = self.Window.Width + 45 
			self.optPanel.showSpliceWindow.SetValue(False)
			# self.optPanel.indSpliceScroll.Enable(False)
		else:
			self.Window.spliceWindowOn = 1
			self.Window.splicerX = self.Window.splicerBackX
			self.optPanel.showSpliceWindow.SetValue(True)
			# self.optPanel.indSpliceScroll.Enable(True)
		self.Window.UpdateDrawing()

	# enable/disable independent splice scrolling
	# def SetIndependentScroll(self, enable):
	# 	self.Window.independentScroll = enable
	# 	self.optPanel.indSpliceScroll.SetValue(enable)
	# 	self.miIndependentScroll.Check(enable)

	def RebuildComboBox(self, comboBox, typeNames):
		comboBox.Clear()
		if len(typeNames) > 0:
			for datatype in typeNames:
				if comboBox.FindString(datatype) == wx.NOT_FOUND:
					comboBox.Append(datatype)
			comboBox.SetSelection(0)

	def RefreshTypeComboBoxes(self):
		if self.filterPanel.locked == False:
			holeData = self.Window.HoleData

			# extract type names from self.Window.HoleData
			typeNames = []
			if len(holeData) > 0:
				for holeIdx in range(len(holeData)):
					typeNames.append(holeData[holeIdx][0][0][2])

			self.RebuildComboBox(self.filterPanel.all, typeNames)
			self.filterPanel.SetTYPE(event=None) # update controls to reflect current selection
			self.RebuildComboBox(self.optPanel.variableChoice, typeNames)
			self.optPanel.SetTYPE(event=None)

	def UpdateSECTION(self):
		self.Window.SectionData = []
		ret = py_correlator.getData(18)
		if ret != "":
			self.ParseSectionSend(ret)

	def UpdateCORE(self):
		self.Window.HoleData = []
		ret = py_correlator.getData(0)
		if ret != "":
			self.LOCK = 0
			self.PrevDataType = ""
			self.ParseData(ret, self.Window.HoleData)
			self.UpdateMinMax()
			self.LOCK = 1

	def UpdateSMOOTH_CORE(self):
		self.Window.SmoothData = []
		ret = py_correlator.getData(1)
		if ret != "":
			self.filterPanel.OnLock()
			self.ParseData(ret, self.Window.SmoothData)
			self.filterPanel.OnRelease()

	def InitSPLICE(self):
		ret = py_correlator.getData(2)
		if ret != "":
			self.ParseSpliceData(ret, False)

	# 2/22/2017 does this do anything at this point? Shouldn't be any splice data on C++ side
	def UpdateSPLICE(self, locked):
		self.Window.SpliceData = []
		ret = ""
		if locked == True: 
			ret = py_correlator.getData(15)
		else:
			ret = py_correlator.getData(3)
		if ret != "":
			self.filterPanel.OnLock()
			self.ParseData(ret, self.Window.SpliceData)
			self.filterPanel.OnRelease()


	def UpdateSMOOTH_SPLICE(self, locked):
		self.Window.SpliceSmoothData = []
		ret =""
		if locked == True: 
			ret = py_correlator.getData(16)
		else:
			ret = py_correlator.getData(4)
		if ret != "":
			self.filterPanel.OnLock()	
			self.ParseData(ret, self.Window.SpliceSmoothData)
			self.filterPanel.OnRelease()


	def UpdateLOGSPLICE(self, locked):
		self.Window.LogSpliceData = []
		if self.Window.isLogMode == 1:
			ret =""
			if locked == True: 
				ret = py_correlator.getData(14)
			else:
				ret = py_correlator.getData(8)
			if ret != "":
				self.filterPanel.OnLock()
				self.ParseData(ret, self.Window.LogSpliceData)
				self.filterPanel.OnRelease()


	def UpdateSMOOTH_LOGSPLICE(self, locked):
		#if self.Window.isLogMode == 1 and len(self.Window.SpliceData) > 0:
		#	locked = True
		self.Window.LogSpliceSmoothData = []
		ret = ""
		if locked == True: 
			ret = py_correlator.getData(17)
		else:
			ret = py_correlator.getData(10)
		if ret != "":
			self.filterPanel.OnLock()	
			self.ParseData(ret, self.Window.LogSpliceSmoothData)
			self.filterPanel.OnRelease()
		else:
			ret = py_correlator.getData(4)
			if ret != "":
				self.filterPanel.OnLock()	
				self.ParseData(ret, self.Window.LogSpliceSmoothData)
				self.filterPanel.OnRelease()

	def UpdateELD(self, locked):
		self.filterPanel.OnLock()
		self.UpdateCORE()
		self.UpdateSMOOTH_CORE()

		self.UpdateLOGSPLICE(locked)
		self.UpdateSMOOTH_LOGSPLICE(locked)
		self.Window.UpdateDrawing()
		self.filterPanel.OnRelease()
		self.UpdateSaganTie()

	def UpdateSaganTie(self):
		ret = py_correlator.getData(20)
		self.Window.LogTieList = []
		self.ParseTieData(ret, self.Window.LogTieList)

	def UpdateData(self):
		self.UpdateCORE()
		self.UpdateSMOOTH_CORE()
		self.UpdateSPLICE(False)
		self.UpdateShiftTie()
		self.Window.UpdateDrawing()

	def UpdateShiftTie(self):
		ret = py_correlator.getData(21)
		self.Window.ShiftTieList = []
		self.ParseShiftTieData(ret, self.Window.ShiftTieList)
		#print self.Window.ShiftTieList

	def OnAbout(self, event):
		dlg = dialog.AboutDialog(None, vers.ShortVersion)
		dlg.Centre()
		dlg.ShowModal()
		dlg.Destroy()

	def OnShowMessage(self, type, msg, numButton, makeNoDefault=False):
		dlg = dialog.MessageDialog(self, type, msg, numButton, makeNoDefault)
		dlg.Centre(wx.CENTER_ON_SCREEN)
		ret = dlg.ShowModal()
		dlg.Destroy()
		return ret

	def AddTieInfo(self, info, depth):
		self.eldPanel.AddTieInfo(info, depth)

	def UpdateTieInfo(self, info, depth, tieNo):
		self.eldPanel.UpdateTieInfo(info, depth, tieNo)

	def ClearSaganTie(self, tieNo):
		if tieNo == -1:
			self.Window.LogTieData = []
			self.Window.logTie = -1
			self.LogselectedTie = -1
			self.Window.LogSpliceData = []
			py_correlator.cleanData(5)
		self.Window.UpdateDrawing()

	def OnOpenAffineData(self, event):
		opendlg = wx.FileDialog(self, "Open AFFINE DATA file", self.Directory, "",wildcard = "Affine Table (*.affine.table)|*.affine.table|XML files(*.xml)|*.xml" )

		ret = opendlg.ShowModal()
		path = opendlg.GetPath()
		opendlg.Destroy()
		if ret == wx.ID_OK:
			py_correlator.openAttributeFile(path, 0)
			s = "Affine Table: " + path + "\n\n"
			self.logFileptr.write(s)
			#if self.showReportPanel == 1:
			#	self.OnUpdateReport() 
			self.UpdateData()

	def OnSaveAffineData(self, event):
		opendlg = wx.FileDialog(self, "Save AFFINE DATA file", self.Directory, "",wildcard = "Affine Table (*.affine.table)|*.affine.table|XML files(*.xml)|*.xml" , style =wx.SAVE)
		ret = opendlg.ShowModal()
		path = opendlg.GetPath()
		filterindex = opendlg.GetFilterIndex()
		if filterindex == 0:
			index = path.find(".affine.table", 0)
			if index == -1:
				path = path + ".affine.table"
		elif filterindex == 1:
			index = path.find(".xml", 0)
			if index == -1:
				path = path + ".xml"

		opendlg.Destroy()
		if ret == wx.ID_OK:
			py_correlator.saveAttributeFile(path, 1)

	# def OnCONNECTION(self, event):
	# 	if self.client is None:
	# 		#HOST = '127.0.0.1'
	# 		HOST = 'localhost'
	# 		PORT = 17799
	# 		for res in socket.getaddrinfo(HOST, PORT, socket.AF_INET, socket.SOCK_STREAM):
	# 			af, socktype, proto, canonname, sa = res
	# 			try:
	# 				self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto)
	# 			except socket.error, msg:
	# 				self.client = None
	# 				continue
	# 			try: 
	# 				self.client.connect(sa)
	# 			except socket.error, msg:
	# 				self.client.close()
	# 				self.client = None
	# 				continue
	# 			break

	# 		if self.client is None:
	# 			#print "[DEBUG] Could not open socket to Corelyzer"
	# 			self.OnShowMessage("Error", "Could not open socket to Corelyzer", 1)
	# 			return False 
	# 		else:
	# 			#print "[DEBUG] Connected to Corelyzer"
	# 			self.OnShowMessage("Information", "Connected to Corelyzer", 1)
	# 			if self.Window.HoleData != []:
	# 				# TEST
	# 				#self.client.send("load_section\t199\t1218\ta\t1\th\t1\t10\n")
	# 				#self.client.send("load_section\t199\t1218\ta\t1\th\t2\t11\n")
	# 				#self.client.send("load_section\t199\t1218\ta\t1\th\t3\t12\n")
	# 				##########

	# 				self.client.send("delete_all\n")

	# 				# load_lims_table
	# 				filename = self.dataFrame.OnGET_IMAGE_FILENAME()
	# 				for name in filename:
	# 					cmd = "load_lims_table\t" + name + "\n"
	# 					self.client.send(cmd)
	# 					#print "[DEBUG] send to Corelyzer: "  + str(cmd)

	# 				# load_core JULIAN
	# 				#ret = py_correlator.getData(18)
	# 				#self.ParseSectionSend(ret)

	# 				cmd = "affine_table\t" + self.CurrentDir + "tmp.affine.table\n" 
	# 				#print "[DEBUG] send to Corelyzer: "  + str(cmd)
	# 				self.client.send(cmd)

	# 				#client.send("load_lims_table\t/Users/julian/Desktop/CRDownloader-data/1239/holeBC.dat\n")
	# 				# self.client.send("show_depth_range\t"+str(self.Window.rulerStartDepth)+"\t"+str(self.Window.rulerEndDepth)+"\n")
	# 				# self.client.send("jump_to_depth\t"+str(self.Window.rulerStartDepth)+"\n")
	# 				#print "[DEBUG] " + str(self.Window.rulerStartDepth) + "\t" + str(self.Window.rulerEndDepth)
	# 				_depth = (self.Window.rulerStartDepth + self.Window.rulerEndDepth) / 2.0
	# 				self.client.send("show_depth_range\t" + str(_depth-0.7) + "\t" + str(_depth+0.7) + "\n")

	# 			self.miConnection.SetText("Close Connection to Corelyzer")
	# 			return True 
	# 	else:
	# 		if self.Window.HoleData != []:
	# 			try:
	# 				self.client.send("delete_all\n")
	# 			except Exception, E:
	# 				print "[DEBUG] Disconnect to the corelyzer"
	# 		try:
	# 			self.client.send("quit\n")
	# 		except Exception, E:
	# 			print "[DEBUG] Disconnect to the corelyzer"
	# 		self.client.close()
	# 		self.client = None
	# 		self.miConnection.SetText("Connect to Corelyzer")
	# 		print "[DEBUG] Close connection to Corelyzer"
	# 		self.OnShowMessage("Information", "Close connection to Corelyzer", 1)
	# 		return False 
			

	def OnPATH(self, event):
		opendlg = wx.DirDialog(self, "Select Directory", self.DBPath)
		ret = opendlg.ShowModal()
		path = opendlg.GetPath()
		opendlg.Destroy()
		if ret == wx.ID_OK:
  			path_len = len(path) -3
			dir_name = path[path_len:path_len+3]                      
			if sys.platform == 'win32':
				if dir_name == "\\db":
					path = path[0:path_len] 
			else:
				if dir_name == "/db":
					path = path[0:path_len] 
			#print "[DEBUG]", path
			oldDBPath = self.DBPath 
			if platform_name[0] == "Windows":
				self.DBPath = path  + "\\"
			else:
				self.DBPath = path  + "/"

			self.dataFrame.PathTxt.SetValue("Path: " + self.DBPath)
			prefile = self.DBPath + "db"
			if os.access(prefile, os.F_OK) == False:
				os.mkdir(prefile)
			self.dataFrame.dataPanel.ClearGrid()
			self.dataFrame.tree.DeleteAllItems()
			self.dataFrame.root = self.dataFrame.tree.AddRoot("Root")
			self.dataFrame.repCount = 0
			self.INIT_CHANGES()
			self.OnNewData(None)
			self.Window.range = []
			self.Window.AltSpliceData = []
			self.Window.selectedType = ""

			# CHECK PATH is CORRELATOR DIRECTORY...... or NOT
			#print "[DEBUG] Data Repository path is changed: " + self.DBPath

			if os.access(path+"/tmp", os.F_OK) == False:
				os.mkdir(path + "/tmp")
				cmd = "cp ./tmp/*.* \"" + path + "/tmp\""
				if platform_name[0] == "Windows":
					cmd = "copy tmp\\*.* \"" + path + "\\tmp\""
				os.system(cmd)
			else:
				if os.access(path+"/tmp/datatypelist.cfg", os.F_OK) == False:
					cmd = "cp ./tmp/*.* \"" + path + "/tmp\""
					if platform_name[0] == "Windows":
						cmd = "copy tmp\\*.* \"" + path + "\\tmp\""
					os.system(cmd)
				
			#if os.access(path + "/log", os.F_OK) == False:
			if os.path.exists(path + "/log") == False:
				#os.mkdir(path + "/log")
				print "no log dir, trying to create..."
				os.makedirs(path + "/log")

			if self.logFileptr != None:
				self.logFileptr.close()
				self.logFileptr = open(path + "/" + global_logName, "a+")
				global_logFile = self.logFileptr

				global_logFile.write("Start of Session:\n")
				s = "BY " + getpass.getuser()  + "\n"
				global_logFile.write(s)
				s = str(datetime.today()) + "\n\n"
				global_logFile.write(s)
				global_logFile.write("Change Repository Directory Path: \n")
				global_logFile.write("from " + oldDBPath + " to " + path + "\n\n")

			self.dataFrame.OnLOADCONFIG()
				
	def UpdateLogData(self):
		if len(self.Window.LogData) > 0:	
			self.Window.LogData = []
			ret = py_correlator.getData(5)
			if ret != "":
				self.filterPanel.OnLock()
				self.ParseData(ret, self.Window.LogData)
				self.Window.minRangeLog = self.min
				self.Window.maxRangeLog = self.max
				self.Window.coefRangeLog = self.Window.logHoleWidth / (self.max - self.min)
				#print "[DEBUG] Log data is updated"
				self.filterPanel.OnRelease()
				self.Window.UpdateDrawing()


	def UpdateSMOOTH_LogData(self):
		if len(self.Window.LogData) > 0:	
			self.Window.LogSMData = []
			ret = py_correlator.getData(19)
			if ret != "":
				self.filterPanel.OnLock()
				self.ParseData(ret, self.Window.LogSMData)
				self.Window.minRangeLog = self.min
				self.Window.maxRangeLog = self.max
				self.Window.coefRangeLog = self.Window.logHoleWidth / (self.max - self.min)
				#print "[DEBUG] Log sm data is updated"
				self.filterPanel.OnRelease()
				#self.Window.UpdateDrawing()

	def OnUpdateLogData(self, flag):
		self.Window.LogData = []
		ret = py_correlator.getData(5)
		if ret != "":
			self.filterPanel.OnLock()
			self.ParseData(ret, self.Window.LogData)
			self.filterPanel.OnRelease()
			self.Window.minRangeLog = self.min
			self.Window.maxRangeLog = self.max
			self.Window.coefRangeLog = self.Window.logHoleWidth / (self.max - self.min)
		self.Window.isLogShifted = flag 


	def UpdateStratData(self):
		ret = py_correlator.getData(7)
		if ret != "": 
			self.Window.StratData = []
			start =0
			last =0
			last = ret.find(",", start)
			hole_number = int(ret[start:last])
			start = last +1

			loop_flag = True
			last = ret.find("#", start)
			if start == last:
				loop_flag = False 

			while loop_flag:
				last = ret.find(":", start)
				if start == last:
					start = last +1
					last = ret.find("#", start)
					if start == last:
						break
					last = ret.find(",", start)
					hole_number = int(ret[start:last])
					start = last +1
					if ret[start:start+1] == ':':
						continue
					if ret[start+1:start+2] == '#':
						break

				last = ret.find("#", start)
				if start == last:
					break

				last = ret.find(",", start)
				# order 
				order = ret[start:last]
				start = last +1
				last = ret.find(",", start)

				# name 
				name = ret[start:last]
				start = last +1
				last = ret.find(",", start)

				# label
				label = ret[start:last]
				start = last +1
				# start
				last = ret.find(",", start)
				startvalue = float(ret[start:last])
				start = last +1
				# stop
				last = ret.find(",", start)
				stopvalue = float(ret[start:last])
				start = last +1
				# mbsf-start
				last = ret.find(",", start)
				rawstartvalue = float(ret[start:last])
				start = last +1
				# mbsf-stop
				last = ret.find(",", start)
				rawstopvalue = float(ret[start:last])
				start = last +1
				# age 
				last = ret.find(",", start)
				agevalue = float(ret[start:last])
				start = last +1
				# type 
				last = ret.find(",", start)
				typevalue = int(ret[start:last])
				start = last +1
				l = []
				stratinfo = order, hole_number, name, label, startvalue, stopvalue, rawstartvalue, rawstopvalue, agevalue, typevalue
				l.append(stratinfo)
				self.Window.StratData.append(l)

				if self.Window.maxAgeRange < agevalue:
					self.Window.maxAgeRange = int(agevalue) + 2 
					#self.agePanel.maxAge.SetValue(str(self.Window.maxAgeRange))

				last = ret.find(":", start)
				if start == last:
					start = last +1
					last = ret.find("#", start)
					if start == last:
						break
					last = ret.find(",", start)
					hole_number = int(ret[start:last])
					start = last +1
					if ret[start:start+1] == ':':
						continue
					if ret[start+1:start+2] == '#':
						break

				last = ret.find("#", start)
				if start == last:
					break

	# Clear all loaded data.
	def OnNewData(self, event):
		if self.Window.HoleData != []:
			#self.logFileptr.write("Closed All Files Loaded. \n\n")
			if event != None and self.client != None:
				try:
					self.client.send("delete_all\n")
				except Exception, E:
					print "[DEBUG] Disconnect to the corelyzer"
					self.client.close()
					self.client = None
		self.RawData = ""
		self.SmoothData = "" 
		self.CurrentDataNo = -1
		self.Window.OnInit()
		self.compositePanel.OnInitUI()
		self.sectionSummary = None # brg?
		self.affineManager.clear()
		self.spliceManager.clear()
		self.spliceIntervalPanel.OnInitUI()
		self.eldPanel.OnInitUI()
		self.autoPanel.OnInitUI(True)
		self.agePanel.OnInitUI()
		py_correlator.cleanData(1)
		py_correlator.cleanData(2)
		self.Window.ClearCompositeTies()
		self.dataFrame.needsReload = False
		self.affineManager.clear()
		self.spliceManager.clear()
		self.Window.SpliceHole = []
		self.Window.SpliceData = []
		self.Window.SpliceSmoothData = []
		self.Window.SpliceTieData = []
		self.Window.RealSpliceTie = []
		self.Window.SPGuideCore = []
		self.Window.SpliceCore = []
		self.Window.CurrentSpliceCore = -1
		self.Window.isLogShifted = False 
		self.Window.LogTieData = [] 
		self.Window.logTie = -1
		self.UpdateLogData()
		self.UpdateData()
		self.OnClearSAGANTie(None)
		self.Window.UpdateDrawing()
		self.Window.DisableDisplayControls()

	def OnClearSpliceTie(self, event):
		py_correlator.cleanData(4)
		self.OnClearSpliceAll()

	def OnClearSAGANTie(self, event):
		py_correlator.cleanData(9)
		self.Window.LogTieData = [] 
		self.Window.logTie = -1
		self.Window.saganDepth = -1
		self.Window.PreviewLog[0] = -1
		self.Window.PreviewLog[1] = -1
		self.Window.PreviewLog[2] = 1.0 
		self.Window.PreviewLog[3] = 0 
		self.Window.PreviewLog[4] = -1
		self.Window.PreviewLog[5] = -1
		self.Window.PreviewLog[6] = 1.0 
		self.UpdateELD(True)
		if self.Window.hole_sagan != -1:
			self.Window.OnUpdateHoleELD()
		self.eldPanel.OnInitUI()
		self.autoPanel.OnInitUI(False)
		self.Window.UpdateDrawing()
		if self.Window.ELDapplied == False and self.Window.LogData != []:
			self.autoPanel.OnButtonEnable(0, True)

	def OnClearSpliceAll(self):
		self.Window.HoleData = []
		self.Window.SpliceHole = []
		self.Window.SpliceData = []
		self.Window.SpliceSmoothData = []
		self.Window.SpliceTieData = []
		self.Window.RealSpliceTie = []
		self.Window.SPGuideCore = []
		self.Window.SpliceCore = []
		self.Window.RealSpliceTie = []
		self.Window.CurrentSpliceCore = -1
		self.UpdateData()

	def OnClearLog(self, event):
		py_correlator.cleanData(5)
		self.Window.LogData = []
		self.Window.LogTieData = [] 
		self.Window.logTie = -1
		self.Window.isLogMode = 0 
		self.Window.autocoreNo = []
		self.eldPanel.SetFlag(False)
		self.Window.UpdateDrawing()

	def OnClearStrat(self, event):
		py_correlator.cleanData(6)
		self.Window.StratData = []
		self.agePanel.OnNewStratList()
		self.agePanel.OnClearList(1)
		self.Window.UpdateDrawing()


	def OnSaveCoreData(self, event):
		opendlg = wx.FileDialog(self, "Save Core Data file", self.Directory, "","*.*" , style =wx.SAVE)
		ret = opendlg.ShowModal()
		path = opendlg.GetPath()
		opendlg.Destroy()
		if ret == wx.ID_OK:
			py_correlator.saveCoreData(path)

	def OnSave(self, event):
		self.topMenu.OnSAVE(event)

	# utility routine to write a single preference key-value pair to file
	def WritePreferenceItem(self, key, value, file):
		keyStr = key + ": "
		valueStr = str(value) + "\n"
		file.write(keyStr + valueStr)

	# save user options/preferences
	def SavePreferences(self):
		cmd = "cp "
		if sys.platform == 'win32':
			cmd = "copy "
		cmd += myPath + "/default.cfg " + myPath + "/tmp/.default.cfg" 
		os.system(cmd)
		
		f = open(myPath + '/default.cfg', 'w+')
		f.write("[applications] \n")
		
		self.WritePreferenceItem("fullscreen", self.fulls, f)

		winPT = self.GetPosition()
		if winPT[0] < 0 or winPT[1] < 0:
			winPT = [0, 0]
		self.WritePreferenceItem("winx", winPT[0], f)

		if sys.platform != 'win32':
			if winPT[0] < 800 and winPT[1] == 0:
				self.WritePreferenceItem("winy", 100, f)
			else:
				self.WritePreferenceItem("winy", winPT[1], f)
		else:
			self.WritePreferenceItem("winy", winPT[1], f)

		width, height = self.GetClientSizeTuple()
		self.WritePreferenceItem("width", width, f)
		self.WritePreferenceItem("height", height, f)

		ssvalue = 1 if self.Window.independentScroll else 0
		self.WritePreferenceItem("secondscroll", ssvalue, f)

		if (width - self.Window.splicerX) < 10:
			self.Window.splicerX = width / 2
		self.WritePreferenceItem("middlebarposition", self.Window.splicerX, f)

		self.WritePreferenceItem("startdepth", self.Window.rulerStartDepth, f)
		self.WritePreferenceItem("secondstartdepth", self.Window.SPrulerStartDepth, f)
		# self.WritePreferenceItem("datawidth", self.optPanel.holeWidthSlider.GetValue(), f)
		self.WritePreferenceItem("plotwidth", self.optPanel.plotWidthSlider.GetValue(), f)
		self.WritePreferenceItem("imagewidth", self.optPanel.imageWidthSlider.GetValue(), f)
		self.WritePreferenceItem("rulerunits", self.Window.GetRulerUnitsStr(), f)
		self.WritePreferenceItem("rulerscale", self.optPanel.depthZoomSlider.GetValue(), f)

		rulerRangeStr = str(self.optPanel.depthRangeMin.GetValue()) + " " + str(self.optPanel.depthRangeMax.GetValue())
		self.WritePreferenceItem("rulerrange", rulerRangeStr, f)

		self.WritePreferenceItem("tiedotsize", self.Window.tieDotSize, f)
		self.WritePreferenceItem("tiewidth", self.Window.tieline_width, f)
		self.WritePreferenceItem("splicewindow", self.Window.spliceWindowOn, f)
		#self.WritePreferenceItem("fontsize", self.Window.stdFont.GetPointSize(), f) # see 11/2/2013 brg
		self.WritePreferenceItem("fontstartdepth", self.Window.startDepthPix, f)
		self.WritePreferenceItem("scrollsize", self.Window.ScrollSize, f)

		showSectionDepths = 1 if self.Window.showSectionDepths == True else 0
		self.WritePreferenceItem("showSectionDepths", showSectionDepths, f)

		showCoreImages = 1 if self.Window.showCoreImages == True else 0
		self.WritePreferenceItem("showCoreImages", showCoreImages, f)

		showCoreInfo = 1 if self.Window.showCoreInfo == True else 0
		self.WritePreferenceItem("showCoreInfo", showCoreInfo, f)

		showOutOfRangeData = 1 if self.Window.showOutOfRangeData == True else 0
		self.WritePreferenceItem("showOutOfRangeData", showOutOfRangeData, f)

		showColorLegend = 1 if self.Window.showColorLegend == True else 0
		self.WritePreferenceItem("showColorLegend", showColorLegend, f)

		showlineInt = 1 if self.Window.showHoleGrid == True else 0
		self.WritePreferenceItem("showline", showlineInt, f)

		shiftclueInt = 1 if self.Window.showAffineShiftInfo == True else 0
		self.WritePreferenceItem("showAffineShiftInfo", shiftclueInt, f)
		
		showAffineTieArrows = 1 if self.Window.showAffineTieArrows == True else 0
		self.WritePreferenceItem("showAffineTieArrows", showAffineTieArrows, f)
		
		self.WritePreferenceItem("tab", self.Window.sideNote.GetSelection(), f)
		self.WritePreferenceItem("path", self.Directory, f)
		self.WritePreferenceItem("dbpath", self.DBPath, f)

		winPT = self.topMenu.GetPosition()
		self.WritePreferenceItem("toolbar", str(winPT[0]) + " " + str(winPT[1]), f)

		self.WritePreferenceItem("shiftrange", self.optPanel.tie_shift.GetValue(), f)
		self.WritePreferenceItem("leadlag", self.leadLag, f)
		self.WritePreferenceItem("winlength", self.winLength, f)

		colorStr = ""
		for colorItem in [self.Window.colorDict[key] for key in self.Window.colorDictKeys]:
			colorStr += str(colorItem[0]) + " " + str(colorItem[1]) + " " + str(colorItem[2]) + " "
		self.WritePreferenceItem("colors", colorStr, f)

		overlapColorStr = ""
		for i in range(9): 
			colorItem = self.Window.overlapcolorList[i].Get()
			overlapColorStr = overlapColorStr + str(colorItem[0]) + " " + str(colorItem[1]) + " " + str(colorItem[2]) + " "
		self.WritePreferenceItem("overlapcolors", overlapColorStr, f)

		f.close()

	def OnInitDataUpdate(self, redraw=True):
		self.UpdateCORE()
		self.UpdateSMOOTH_CORE()
		if redraw:
			self.Window.UpdateDrawing()
		return

	################################################################################################
	# Most Correlator to Corelyzer communication routines live here - TODO: move to separate module!
	#
	def UndoSpliceSectionSend(self):
		if self.client == None:
			return

		# recover
		if self.spliceHoleA != None and self.spliceType != "first":
			active = False
			for data in self.Window.SectionData:
				if self.spliceHoleA == data[0] and self.spliceCoreA == data[1]: 
					if active == False:
						start_depth = float(data[4])
						end_depth = float(data[5])
						if (self.spliceDepthA >= start_depth) and (self.spliceDepthA <= end_depth):
							self.client.send("delete_section\t"+self.leg+"\t"+self.site+"\t"+data[0]+"\t"+data[1]+"\t"+data[2]+"\t"+data[3]+"\t"+ data[6] + "\t" + data[7] + "\n")
							self.client.send("cut_interval_to_new_track\t"+self.leg+"\t"+self.site+"\t"+data[0]+"\t"+data[1]+"\t"+data[2]+"\t"+data[3]+"\t"+ data[6]+ "\t" + data[7] + "\tspiliced\n")
							active = True
					elif active == True:
						self.client.send("delete_section\t"+self.leg+"\t"+self.site+"\t"+data[0]+"\t"+data[1]+"\t"+data[2]+"\t"+data[3]+"\t"+ data[6] + "\t" + data[7] + "\n")
						self.client.send("cut_interval_to_new_track\t"+self.leg+"\t"+self.site+"\t"+data[0]+"\t"+data[1]+"\t"+data[2]+"\t"+data[3]+"\t"+ data[6]+ "\t" + data[7] + "\tspiliced\n")
						active = True
				else:
					if active == True:
						break
		# delete
		if self.spliceHoleB != None:
			active = False
			for data in self.Window.SectionData:
				if self.spliceHoleB == data[0] and self.spliceCoreB == data[1]: 
					self.client.send("delete_section\t"+self.leg+"\t"+self.site+"\t"+data[0]+"\t"+data[1]+"\t"+data[2]+"\t"+data[3]+"\t"+ data[6] + "\t" + data[7] + "\n")
					active = True
				else:
					if active == True:
						break

		self.spliceHoleA = None 
		self.spliceHoleB = None 


	def NewDATA_SEND(self):
		if self.client != None and self.Window.HoleData != []:
			self.client.send("delete_all\n")

			filenames = self.dataFrame.OnGET_IMAGE_FILENAME()
			for name in filenames:
				cmd = "load_lims_table\t" + name + "\n"
				#print "[DEBUG] send to Corelyzer: "  + str(cmd)
				self.client.send(cmd)

			py_correlator.saveAttributeFile(self.CurrentDir + 'tmp.affine.table'  , 1)
			cmd = "affine_table\t" + self.CurrentDir + "tmp.affine.table\n" 
			#print "[DEBUG] send to Corelyzer: "  + str(cmd)
			self.client.send(cmd)

			#ret = py_correlator.getData(18)
			#self.ParseSectionSend(ret)

	def UpdateSend(self):
		if self.client != None:
			cmd = "affine_table\t" + self.CurrentDir + "tmp.affine.table\n" 
			#print "[DEBUG] send to Corelyzer: "  + str(cmd)
			self.client.send(cmd)

	def SpliceSectionSend(self, hole, core, depth, type, tiedNo):
		if self.client != None and tiedNo <= 0:
			self.spliceType = type
			if type == "split":
				self.spliceHoleA = hole
				self.spliceCoreA = core
				self.spliceDepthA = depth 
			else:
				self.spliceHoleB = hole
				self.spliceCoreB = core

			active = False
			for data in self.Window.SectionData:
				if hole == data[0] and core == data[1]: 
					if active == False and type != "first":
						start_depth = float(data[4])
						end_depth = float(data[5])
						if (type == None) and (depth <= end_depth):
							try:
								temp_depth = depth * float(data[6]) / float(data[4])
								self.client.send("cut_interval_to_new_track\t"+self.leg+"\t"+self.site+"\t"+data[0]+"\t"+data[1]+"\t"+data[2]+"\t"+data[3]+"\t"+ data[6]+ "\t" + data[7] + "\tspiliced\n")
								self.client.send("split_section\t"+self.leg+"\t"+self.site+"\t"+data[0]+"\t"+data[1]+"\t"+data[2]+"\t"+data[3]+"\t"+data[6]+"\t"+data[7]+"\t"+ "0.00\t" + str(temp_depth)+"\n")

								active = True
								self.spliceDepthB = depth
							except Exception, E:
								#print "[DEBUG] Disconnect to the corelyzer"
								self.client.close()
								self.client = None
								return
						elif (type == "split") and (depth >= start_depth) and (depth <= end_depth):
							try:
								temp_depth = depth * float(data[6]) / float(data[4])
								self.client.send("split_section\t"+self.leg+"\t"+self.site+"\t"+data[0]+"\t"+data[1]+"\t"+data[2]+"\t"+data[3]+"\t"+data[6]+"\t"+data[7]+"\t"+str(temp_depth)+ "\t" + data[7]+"\n")
								active = True
								self.spliceDepthA = depth
							except Exception, E:
								#print "[DEBUG] Disconnect to the corelyzer"
								self.client.close()
								self.client = None
								return
					else: 
						try:
							if type != "split":
								self.client.send("cut_interval_to_new_track\t"+self.leg+"\t"+self.site+"\t"+data[0]+"\t"+data[1]+"\t"+data[2]+"\t"+data[3]+"\t"+ data[6] + "\t" + data[7] + "\tspiliced\n")
								active = True
							else:
								self.client.send("delete_section\t"+self.leg+"\t"+self.site+"\t"+data[0]+"\t"+data[1]+"\t"+data[2]+"\t"+data[3]+"\t"+ data[6] + "\t" + data[7] + "\n")
								active = True
						except Exception, E:
							#print "[DEBUG] Disconnect to the corelyzer"
							self.client.close()
							self.client = None
							return
				else:
					if active == True:
						return
		elif self.client != None:
			active = False
			for data in self.Window.SectionData:
				if hole == data[0] and core == data[1]: 
					if active == False:
						start_depth = float(data[4])
						end_depth = float(data[5])
						if (type == "split") and (self.spliceDepthA >= start_depth) and (self.spliceDepthA <= end_depth):
							try:
								self.client.send("delete_section\t"+self.leg+"\t"+self.site+"\t"+data[0]+"\t"+data[1]+"\t"+data[2]+"\t"+data[3]+"\t"+ data[6] + "\t" + data[7] + "\n")

								self.client.send("cut_interval_to_new_track\t"+self.leg+"\t"+self.site+"\t"+data[0]+"\t"+data[1]+"\t"+data[2]+"\t"+data[3]+"\t"+ data[6] + "\t" + data[7] + "\tspiliced\n")

								active = True
							except Exception, E:
								#print "[DEBUG] Disconnect to the corelyzer"
								self.client.close()
								self.client = None
								return
						elif type == None: 
							if (self.spliceDepthB >= start_depth) and (self.spliceDepthB <= end_depth):
								self.client.send("delete_section\t"+self.leg+"\t"+self.site+"\t"+data[0]+"\t"+data[1]+"\t"+data[2]+"\t"+data[3]+"\t"+ data[6] + "\t" + data[7] + "\n")

								self.client.send("cut_interval_to_new_track\t"+self.leg+"\t"+self.site+"\t"+data[0]+"\t"+data[1]+"\t"+data[2]+"\t"+data[3]+"\t"+ data[6] + "\t" + data[7] + "\tspiliced\n")
								#self.SpliceSectionSend(hole, core, depth, type, 1)
								return
							else:
								self.client.send("cut_interval_to_new_track\t"+self.leg+"\t"+self.site+"\t"+data[0]+"\t"+data[1]+"\t"+data[2]+"\t"+data[3]+"\t"+ data[6] + "\t" + data[7] + "\tspiliced\n")
					else: 
						try:
							if type == "split":
								self.client.send("cut_interval_to_new_track\t"+self.leg+"\t"+self.site+"\t"+data[0]+"\t"+data[1]+"\t"+data[2]+"\t"+data[3]+"\t"+ data[6] + "\t" + data[7] + "\tspiliced\n")
								active = True
						except Exception, E:
							#print "[DEBUG] Disconnect to the corelyzer"
							self.client.close()
							self.client = None
							return
				else:
					if active == True:
						#if type == "split":
						#	self.SpliceSectionSend(hole, core, depth, type, 1)
						break	


	def UndoShiftSectionSend(self):
		if self.shiftHole != None:
			self.ShiftSectionSend()
			self.shiftHole = None 

	def TieUpdateSend(self, leg, site, holeA, coreA, holeB, coreB, tie_depth, shift):
		if self.client != None:
			ret1 = self.GetSectionNoWithDepth(holeB, coreB, tie_depth)
			# ret1 = type, section_number
			cmd  = "tie_update\t" + str(leg) + "\t"+ str(site) + "\t" + str(holeA) + "\t" + str(coreA) + "\t" + str(leg) + "\t"+ str(site) + "\t" + str(holeB) + "\t" + str(coreB) + "\t" + str(ret1[1]) + "\t" + str(ret1[0]) + "\t" + str(tie_depth) + "\t" + str(shift) + "\n"
			#print "[DEBUG] send to Corelyzer: " + cmd
			try:
				self.client.send(cmd)
			except Exception, E:
				#print "[DEBUG] Disconnect to the corelyzer"
				self.client.close()
				self.client = None
			
	def clearSend(self):
		#def clearSend(self, leg, site, holeA, coreA, holeB, coreB, tie_depth):
		if self.client != None:
			#ret1 = self.GetSectionNoWithDepth(holeB, coreB, tie_depth)
			#cmd  = "tie_update\t" + str(leg) + "\t"+ str(site) + "\t" + str(holeA) + "\t" + str(coreA) + "\t" + str(leg) + "\t"+ str(site) + "\t" + str(holeB) + "\t" + str(coreB) + "\t" + str(ret1[1]) + "\t" + str(ret1[0]) + "\t" + "0.0" + "\n"
			#print "[DEBUG] send to Corelyzer: " + cmd

			cmd = "affine_table\t" + self.CurrentDir + "tmp.affine.table\n" 
			#print "[DEBUG] send to Corelyzer: "  + str(cmd)
			try:
				self.client.send(cmd)
			except Exception, E:
				print "[DEBUG] Disconnect to the corelyzer"
				self.client.close()
				self.client = None

	def FineTuneSend(self, leg, site, holeA, coreA, holeB, coreB, tie_depth):
		if self.client != None:
			self.Window.selectedTie = -1
			self.Window.UpdateDrawing()
			tune_flag = self.OnShowMessage("About", "Do you want to process find tune?", 2)
			if tune_flag == wx.ID_OK:
				ret1 = self.GetSectionNo(holeA, coreA)
				ret2 = self.GetSectionNo(holeB, coreB)
				cmd  = "fine_tune\t" + str(leg) + "\t"+ str(site) + "\t" + str(holeA) + "\t" + str(coreA) + "\t" + str(ret1[1]) + "\t1\t" + str(ret1[0]) + "\t"  + str(leg) + "\t"+ str(site) + "\t" + str(holeB) + "\t" + str(coreB) + "\t" + str(ret2[1]) + "\t1\t" + str(ret2[0]) + "\t" + str(tie_depth) + "\n"
				#print "[DEBUG] send to Corelyzer: " + cmd
				try:
					self.client.send(cmd)
				except Exception, E:
					print "[DEBUG] Disconnect to the corelyzer"
					self.client.close()
					self.client = None
				hold_dlg = dialog.HoldDialog(self)
				hold_dlg.Show(True)
				#print "[DEBUG] ... waiting for floating data"
				recvdata = self.client.recv(1024)
				start = recvdata.find('\t', 0)
				shift = 0.0
				if start > 0:
					shift = float(recvdata[0:start])

				#print "[DEBUG] got data: " + str(recvdata) + " = " + str(shift)
				hold_dlg.Close()
				hold_dlg.Destroy()
				self.Window.SetFocusFromKbd()
				return shift

		return 0.0
		

	def ShowCoreSend(self, leg, site, hole, core):
		if self.client != None:
			core_Type = '-'
			start_section = '-' 
			end_section = '-' 
			shift = '-'
			for data in self.Window.SectionData:
				if hole == data[0] and core == data[1]: 
					core_Type = data[2] 
					if start_section == '-':
						start_section = data[3]
					end_section = data[3]
					shift = data[8]
			msg = 'load_core\t' + leg + '\t' + site + '\t' + hole + '\t' + core + '\t' + core_Type + '\t'
			msg += start_section + '\t' + end_section + '\t' + shift + '\n'
			#print "[DEBUG-showCoreSend] send to Corelyzer: " + msg 

			try:
				self.client.send(msg)
			except Exception, E:
				print "[DEBUG] Disconnect to the corelyzer"
				self.client.close()
				self.client = None


	def GetSectionNo(self, hole, core):
		flag = False
		idx = 0
		type = '-'
		for data in self.Window.SectionData:
			if hole == data[0] and core == data[1]: 
				flag = True 
				idx = data[3]
				type = data[2]
			elif flag == True:
				break
		return idx, type

	# JULIAN
	def GetSectionNoWithDepth(self, hole, core, depth):
		flag = False
		idx = 0
		type = '-'
		prev_depth = 0.0
		for data in self.Window.SectionData:
			if hole == data[0] and core == data[1]: 
				flag = True 
				if depth >= prev_depth and depth < data[4]:
					break

				idx = data[3]
				type = data[2]
				if depth >= data[4] and depth <= data[5]:
					break
				prev_depth = data[5] 
			elif flag == True:
				break
		return idx, type

	def GetSectionAtDepth(self, leg, hole, core, type, depth):
		affineShift = self.affineManager.getShiftDistance(hole, core)
		mbsfDepth = depth - affineShift
		sectionNumber = self.sectionSummary.getSectionAtDepth(leg, hole, core, mbsfDepth)
		if sectionNumber is not None:
			sectionTopDepth = self.sectionSummary.getSectionTop(leg, hole, core, sectionNumber)
			offset = round((mbsfDepth - sectionTopDepth) * 100.0, 1)
		#print "{}{}; section at depth {} - shift {} = {} is section {}".format(hole, core, depth, affineShift, depth - affineShift, section)
			return sectionNumber, offset
		else:
			return "[none]", "[none]"
		
		#return py_correlator.getSectionAtDepth(hole, core, type, depth)


	def ShiftSectionSend(self):
		if self.client != None:
			"""
			self.shiftHole = hole
			self.shiftCore = core
			self.shiftOffset = -offset
			self.shiftType = type
			active = False
			for data in self.Window.SectionData:
				if hole == data[0] and core == data[1]: 
					try:
						cmd = "shift_section\t"+self.leg+"\t"+self.site+"\t"+data[0]+"\t"+data[1]+"\t"+data[2]+"\t"+data[3]+"\t"+ str(offset)+"\n"
						self.client.send(cmd)
						#print "[DEBUG] send to Corelyzer: " + cmd
						active = True
					except Exception, E:
						print "[DEBUG] Disconnect to the corelyzer"
						self.client.close()
						self.client = None
						return
				else:
					if active == True:
						if type == 2:
							return
						else:
							if hole == data[0]:
								try:
									cmd = "shift_section\t"+self.leg+"\t"+self.site+"\t"+data[0]+"\t"+data[1]+"\t"+data[2]+"\t"+data[3]+"\t"+ str(offset)+"\n"
									self.client.send(cmd)
									#print "[DEBUG] send to Corelyzer: " + cmd
								except Exception, E:
									print "[DEBUG] Disconnect to the corelyzer"
									self.client.close()
									self.client = None
									return
							else:
								return
			"""

			cmd = "affine_table\t" + self.CurrentDir + "tmp.affine.table\n" 
			#print "[DEBUG] send to Corelyzer: "  + str(cmd)
			self.client.send(cmd)
	###
	### End (most) Correlator to Corelyzer communication methods
	#################################################################

	def ParseSectionSend(self, data):
		self.Window.SectionData = []
		start = 0
		# site 
		last = data.find(",", start)
		site = data[start:last] 
		self.site = site
		start = last +1
		# leg 
		last = data.find(",", start)
		leg = data[start:last]
		self.leg = leg
		start = last +1
		# hole 
		last = data.find(",", start)
		hole = data[start:last]
		start = last +1
		prevHole = ""
		prevCore = ""
		prevType = ""
		prevSecNo = ""
		startSecNo = "-" 
		shift = ""
		secInfo = None

		while True:
			last = data.find("@", start)
			if start == last:
				start = last + 1
				last = data.find(",", start)
				shift = data[start:last] 
				start = last + 1

			last = data.find(":", start)
			if start == last:
				start = last + 1
				last = data.find("#", start)
				if start == last:
					break
				else:
					# site 
					last = data.find(",", start)
					site = data[start:last] 
					start = last +1
					# leg 
					last = data.find(",", start)
					leg = data[start:last]
					start = last +1
					# hole 
					last = data.find(",", start)
					hole = data[start:last]
					start = last +1

			# core id 
			last = data.find(",", start)
			core = int(data[start:last])
			start = last +1
			# type 
			last = data.find(",", start)
			type = data[start:last]
			start = last +1
			# section number 
			last = data.find(",", start)
			secNo = data[start:last]
			start = last +1
			# depth start
			last = data.find(",", start)
			depth_start = float(data[start:last])
			start = last +1
			# depth end 
			last = data.find(",", start)
			depth_end = float(data[start:last])
			start = last +1
			# top 
			last = data.find(",", start)
			top = data[start:last]
			start = last +1
			# bottom 
			last = data.find(",", start)
			bottom = data[start:last]
			start = last +1

			if hole != prevHole or core != prevCore:
				if startSecNo == "-":
					startSecNo = secNo
				else:
					startSecNo = secNo
					secInfo_modified = (secInfo[0], secInfo[1], secInfo[2], secInfo[3], secInfo[4], secInfo[5], secInfo[6], secInfo[7], shift)
					self.Window.SectionData.append(secInfo_modified)
			else:
				if secInfo != None:
					self.Window.SectionData.append(secInfo)

			secInfo = (hole, core, type, secNo, depth_start, depth_end, top, bottom, '-')

			prevCore = core
			prevHole = hole
			prevType = type
			prevSecNo = secNo


		if startSecNo != "-":
			if secInfo != None:
				secInfo_modified = (secInfo[0], secInfo[1], secInfo[2], secInfo[3], secInfo[4], secInfo[5], secInfo[6], secInfo[7], shift)
				self.Window.SectionData.append(secInfo_modified)


	def ParseHole(self, start, last, data, output):
		hole = []
		# site 
		last = data.find(",", start)
		site = data[start:last] 
		start = last +1
		# leg 
		#self.Window.HoleData = []
		last = data.find(",", start)
		leg = data[start:last]
		start = last +1
		# data type
		last = data.find(",", start)
		type = data[start:last]
		start = last +1
		self.CoreNo = 0 
		if type == "GRA":
			type = "Bulk Density(GRA)"

		# brg 11/18/2015: top and bottom are actually min/max section offset for the hole,
		# NOT min/max depths of hole. Those values are parsed out in ParseData() if needed...
		# top, bottom, min, max, 
		# 4 times
		temp =[]
		for i in range(4):
			last = data.find(",", start)
			temp.append(float(data[start:last])) 
			start = last +1

		if self.min > temp[2]:
			self.min = temp[2]
		if self.max < temp[3]:
			self.max = temp[3]

		# hole-name
		last = data.find(",", start)
		holename = data[start:last] 

		# BLOCKED DETAILED TYPE  
		#regHole = type + " Hole " + holename
		#self.filterPanel.OnRegisterHole(regHole)
		self.PrevDataType = type

		start = last +1
		# how-many-hole
		last = data.find(",", start)
		coreNum = int(data[start:last])
		start = last +1

		last = data.find("#", start)
		if start != last:
			for i in range(coreNum):
				self.ParseCore(start, last, hole, holename, data)
				start = self.CoreStart
				last = self.CoreLast 

			#holeinfo = site, leg, type, temp[0], temp[1], temp[2], temp[3], holename, self.CoreNo 
			holeinfo = site, leg, type, temp[0], temp[1], temp[2], temp[3], holename, coreNum 
			hole.insert(0, holeinfo)
			temp =[]
			temp.append(hole)
			output.append( temp )
		else:
			self.CoreStart = start
			self.CoreLast = last


	def ParseCore(self, start, last, hole, holename, data):
		# core-number, top, bottom, min, max, values, affine
		temp =[]
		last = data.find(",", start)
		coreNum = data[start:last]
		#print "Parsing core {}{}: ".format(holename, coreNum),
		temp.append(coreNum)
		start = last +1

		last = data.find(":", start)
		if start == last:
			start = last + 1
			self.CoreStart = start
			self.CoreLast = last
			return
		
		# find affine shift for core if present
		#affineStr = ""
		affineShift = round(self.affineManager.getShiftDistance(holename, coreNum), 3) if self.affineManager.hasShift(holename, coreNum) else 0
		#affineStr = "affine shift of {}".format(affineShift)
		#print "Getting data...AffineManager sez {}{} has {}".format(holename, coreNum, affineStr)

		#for i in range(6):
		# I believe 'squish' is the compression percentage for ELD 
		for key in ['coreTop', 'coreBottom', 'coreMin', 'coreMax', 'affineShift', 'squish']:
			last = data.find(",", start)
			coreProperty = float(data[start:last])
			#print "{} = {},".format(key, coreProperty),
			if key == 'affineShift':
				#print "affine = {}".format(coreProperty)
				temp.append(affineShift)
			else: 
				temp.append(coreProperty) 
			start = last + 1
			
		#print "" # newline after core number and properties

		corelist = [] 
		#value = ()	

		last = data.find(",", start)
		annot = data[start:last] 
		start = last +1

		last = data.find(",", start)
		quality = data[start:last] 
		start = last +1

		# Get Section Information
		last = data.find(":", start)
		sections = []
		while start != last: 
			last = data.find(",", start)
			sec_depth = float(data[start:last]) + affineShift # apply affine
			start = last +1
			sections.append(sec_depth)

			last = data.find(":", start)
		start = last + 1
		
		#print "annot = {}, quality = {}, sections = {}".format(annot, quality, sections)

		# Get Data
		last = data.find(":", start)
		if start == last:
			start = last + 1
			self.CoreStart = start
			self.CoreLast = last
		else: 
			while True:
				last = data.find(",", start)
				v_value = float(data[start:last]) + affineShift # apply affine
				start = last +1
				last = data.find(",", start)
				v_data = float(data[start:last])
				start = last +1
				corelist.append((v_value, v_data))
				last = data.find(":", start)
				if start == last:
					# Create a "core data" item, which looks like the following: 
					# (1-based core index in hole, top, bottom, mindata, maxdata, affine offset, stretch, annotated type,
					# core quality, sections (list of each sections' top depth), list of all core's depth/data tuple-pairs
					coreinfo = temp[0], temp[1], temp[2], temp[3], temp[4], temp[5], temp[6], annot, quality, sections, corelist
					hole.append(coreinfo)
					start = last + 1
					self.CoreStart = start
					self.CoreLast = last
					self.CoreNo = self.CoreNo + 1
					break

	def ParseData(self, data, output):
		if data != "":
			self.noOfSameTypeHoles = 0
			if self.filterPanel.locked == False:
				self.noOfHoles = 0

			self.min = 9999.99 
			self.max = -9999.99 
			start =0
			last =0
			last = data.find(",", start)
			# brg 11/18/2015: Minimum depth of hole...apparently we just toss this value
			value = float(data[start:last]) 
			start = last +1
			last = data.find(",", start)
			# brg 11/18/2015: Maximum depth of hole...used only for self.ScrollMax
			value = float(data[start:last]) 
			self.ScrollMax = value
			start = last +1

			while True:
				self.ParseHole(start, last, data, output)
				if self.filterPanel.locked == False:
					self.noOfHoles = self.noOfHoles + 1
				start = self.CoreStart
				last = self.CoreLast 
				last = data.find("#", start)
				if start == last:
					break

			#if self.LOCK == 0:
			#	if self.noOfHoles != 0 and self.filterPanel.locked == False:
			#		self.noOfSameTypeHoles = self.noOfHoles - self.noOfSameTypeHoles
			#		for n in range(self.noOfSameTypeHoles):
			#			self.Window.OnChangeHoleRange(self.min, self.max)
			#	self.min = 999
			#	self.max = -999

			self.HScrollMax = 30.0 + (len(self.Window.HoleData) * self.Window.holeWidth)

	# 1/29/2014 brgtodo: unreachable statements
	def UpdateMinMax(self):
		#pass
		self.Window.minRange = 0 
		#self.Window.minRange = self.min 
		return 
		self.Window.maxRange = self.max 
		if (self.max - self.min) != 0:
			self.Window.coefRange = self.Window.holeWidth / (self.Window.maxRange - self.Window.minRange)

	def ParseSaganData(self, data):
		if data != "":
			start =0
			last =0
			last = data.find("#", start)
			if start == last:
				return	

			tie_list = [] 
			while True:
				# hole-name, coreid, depth, hole-name, coreid, depth
				# hole-name 
				last = data.find(",", start)
				id = int(data[start:last])
				start = last +1

				# type
				last = data.find(",", start)
				start = last +1
				# annotation
				last = data.find(",", start)
				start = last +1

				last = data.find(",", start)
				holeA = data[start:last]
				start = last +1
				last = data.find(",", start)
				coreA = int(data[start:last])
				start = last +1
				last = data.find(",", start)
				depthA = float(data[start:last])
				start = last +1
				# hole-name 
				# type
				last = data.find(",", start)
				start = last +1
				# annotation
				last = data.find(",", start)
				start = last +1
				last = data.find(",", start)
				holeB = data[start:last]
				start = last +1
				last = data.find(",", start)
				coreB = int(data[start:last])
				start = last +1
				last = data.find(",", start)
				depthB = float(data[start:last])
				start = last +1
				last = data.find(":", start)
				start = last +1
				# setup SaganData
				tie_list.append( (id, holeA, coreA, holeB, coreB, depthA, depthB) )
				last = data.find("#", start)
				if start == last:
					break
			self.Window.SetSaganFromFile(tie_list)


	def ParseTieData(self, data, data_list):
		if data != "":
			start =0
			last =0

			while True:
				# hole-index, x, y
				last = data.find(",", start)
				hole_idx = int(data[start:last])
				start = last +1
				l = []

				while True:
					last = data.find(":", start)
					if start == last:
						start = last +1
						break

					last = data.find(",", start)
					x = float(data[start:last])
					start = last +1
					l.append(x)

					last = data.find(",", start)
					x = float(data[start:last])
					start = last +1
					l.append(x)

				data_list.append( (hole_idx, l) )

				last = data.find("#", start)
				if start == last:
					break


	def ParseShiftTieData(self, data, data_list):
		if data != "":
			start =0
			last =0

			while True:
				# hole-index, x, y
				last = data.find(",", start)
				hole_index = int(data[start:last])
				start = last +1
				l = []

				hole_name = None
				while True:
					last = data.find(":", start)
					if start == last:
						start = last +1
						break

					last = data.find(",", start)
					hole_name = data[start:last]
					start = last +1

					last = data.find(",", start)
					x = int(data[start:last])
					start = last +1
					l.append(x)

					last = data.find(",", start)
					x = float(data[start:last])
					start = last +1
					l.append(x)

					last = data.find(",", start)
					x = float(data[start:last])
					start = last +1
					l.append(x)

				if hole_name != None:
					data_list.append( (hole_index, hole_name, l) )

				last = data.find("#", start)
				if start == last:
					break


	def ParseSpliceData(self, data, flag):
		if data != "":
			self.Window.SpliceCore = []
			start =0
			last =0
			last = data.find("#", start)
			if start == last:
				return	

			tie_list = [] 
			while True:
				# hole-name, type, annotation, coreid, depth, hole-name, coreid, depth
				# id
				last = data.find(",", start)
				id = int(data[start:last])
				start = last +1

				# first hole-name 
				last = data.find(",", start)
				type = int(data[start:last])
				start = last +1
				last = data.find(",", start)
				annotation = ""
				strtypeA = ""
				if start != last:
					annotation = data[start:last]
				start = last +1
				if type == 30:
					strtypeA = "GRA"
				elif type == 31:
					strtypeA = "Pwave"
				elif type == 32:
					strtypeA = "Susceptibility"
				elif type == 33:
					strtypeA = "Natural Gamma"
				elif type == 34:
					strtypeA = "Reflectance"
				elif type == 37:
					strtypeA = annotation
				last = data.find(",", start)
				holeA = data[start:last]
				start = last +1
				last = data.find(",", start)
				coreA = int(data[start:last])
				start = last +1
				last = data.find(",", start)
				depthA = float(data[start:last])
				start = last +1

				# seoncd hole-name 
				last = data.find(",", start)
				type = int(data[start:last])
				start = last +1
				last = data.find(",", start)
				annotation = ""
				strtypeB = ""
				if start != last:
					annotation = data[start:last]
				start = last +1
				if type == 30:
					strtypeB = "GRA"
				elif type == 31:
					strtypeB = "Pwave"
				elif type == 32:
					strtypeB = "Susceptibility"
				elif type == 33:
					strtypeB = "Natural Gamma"
				elif type == 34:
					strtypeB = "Reflectance"
				elif type == 37:
					strtypeB = annotation
				last = data.find(",", start)
				holeB = data[start:last]
				start = last +1
				last = data.find(",", start)
				coreB = int(data[start:last])
				start = last +1
				last = data.find(",", start)
				depthB = float(data[start:last])
				start = last +1
				last = data.find(":", start)
				start = last +1
				# setup SpliceData
				tie_list.append( (id, strtypeA, holeA, coreA, strtypeB, holeB, coreB, depthA, depthB) )
				last = data.find("#", start)
				if start == last:
					break
			self.Window.SetSpliceFromFile(tie_list, flag)

	def NewDrawing(self,cfgfile, new_flag):
		self.Window.DrawData = self.LoadPreferencesAndInitDrawData(cfgfile, new_flag)
		self.Window.UpdateDrawing()

	def ShowDataManager(self):
		if self.UnsavedChanges() == True:
			ret = self.OnShowMessage("About", "Do you want to save?", 0)
			if ret == wx.ID_YES:
				self.topMenu.OnSAVE(None) # dummy event
		if self.dataFrame.IsShown() == False:
			self.Window.Hide()
			self.dataFrame.Show(True)
			#self.midata.Check(True)
			self.topMenu.dbbtn.SetLabel("Go to Display")
		self.Layout()

	def ShowDisplay(self):
		if self.dataFrame.needsReload:
			msg = "The Enable/Disable state of files was changed. " \
				"To apply these changes, select Load from the right-click menu.\n\n" \
				"Continue to the Display?"
			self.dataFrame.needsReload = False # warn only once
			if self.OnShowMessage("Data Manager Change(s) Detected", msg, 0, makeNoDefault=True) != wx.ID_YES:
				return

		self.dataFrame.propertyIdx = None
		self.dataFrame.Show(False)

		# force DataCanvas to update bitmap dimensions - otherwise the
		# control panel comes out 2x too far to the left
		self.Window.OnSize(None)

		self.Window.Show(True)
		#self.midata.Check(False)
		self.topMenu.dbbtn.SetLabel("Go to Data Manager")
		self.Layout()

	# brg 1/8/2014: move to utils module or the like?
	""" Convert data type string to integer (and non-empty annotation string if data type is user-defined)"""
	def TypeStrToInt(self, typeStr):
		type = 7 # custom type
		annot = ""
		if typeStr == "Bulk Density(GRA)":
			type = 1 
		elif typeStr.lower() == "pwave": # expecting 'Pwave' or 'PWave'
			type = 2 
		elif typeStr == "Susceptibility":
			type = 3 
		elif typeStr.replace(' ', '') == "NaturalGamma": # expecting 'Natural Gamma' or 'NaturalGamma'
			type = 4 
		elif typeStr == "Reflectance":
			type = 5 
		elif typeStr == "Other":
			type = 6
		else:
			annot = typeStr
		return type, annot

	""" Convert data type string to output filename suffix. When Exporting data, the suffix
	is 'adj', in all other cases it's 'fix' """
	def TypeStrToFileSuffix(self, typeStr, useExportSuffix=False):
		suffix = "adj" if useExportSuffix else "fix"
		result = ""
		if typeStr == "Bulk Density(GRA)":
			result = "gr" + suffix
		elif typeStr.lower() == "pwave":
			result = "pw" + suffix
		elif typeStr == "Susceptibility":
			suffix = "sus" + suffix
		elif typeStr.replace('  ', '') == "NaturalGamma":
			result = "ng" + suffix
		elif typeStr == "Reflectance":
			result = "refl" + suffix
		# 1/20/2014 brgtodo: May not be correct for export case...previous code
		# ignored the possibility of an Other type being passed in. However, this
		# does yield the correct suffix (type only, no adj/fix suffix) on Export.
		else:
			result = typeStr
		return result

	def LoadPreferencesAndInitDrawData(self, cfgfile, new_flag):
		# unused
# 		self.positions= [ (77,32) , (203,32), (339,32),
# 						 (77,152) , (203,152), (339,152),
# 						 (77,270) , (203,270), (339,270),
# 						 (77,390) , (203,390), (339,390) ]

		DrawData = {}

		self.config = ConfigParser.ConfigParser()
		self.config.read(cfgfile)
		
		scroll_start = self.Window.startDepthPix * 0.7
		#l = []

		#self.Width, self.Height = self.GetClientSizeTuple()
		if self.config.has_option("applications", "width"):
			str_temp =  self.config.get("applications", "width")
			if len(str_temp) > 0:
				self.Width = int ( str_temp )
		if self.config.has_option("applications", "height"):
			str_temp =  self.config.get("applications", "height")
			if len(str_temp) > 0:
				self.Height = int ( str_temp )
		if self.Width <= 0:
			self.Width = 800
		if self.Height <= 0:
			self.Height = 600

		self.SetClientSize((self.Width, self.Height))

		#skin = self.config.get("applications", "skin")

		if self.config.has_option("applications", "fullscreen"):
			self.fulls = int ( self.config.get("applications", "fullscreen") )
			if self.fulls == 1:
				#self.ShowFullScreen(True, wx.FULLSCREEN_ALL)
				# temporal solution
				self.Width, self.Height = wx.DisplaySize()
				self.Height = self.Height -100 
				self.SetClientSize((self.Width, self.Height))

		win_x = 0
		win_y = 0
		if self.config.has_option("applications", "winx"):
			str_temp = self.config.get("applications", "winx")
			if len(str_temp) > 0:
				win_x = int ( str_temp )
		if self.config.has_option("applications", "winy"):
			str_temp = self.config.get("applications", "winy")
			if len(str_temp) > 0:
				win_y = int ( str_temp )
			#if win_y == 0:
			#	win_y = 100

		if platform_name[0] != "Windows" and win_y == 0:
			if win_x < 800:
				win_y = 50

		#print "[DEBUG] Window Position:" + str(win_x) + " " + str(win_y)

		# 1/8/2019 brg: Logic to handle multiple displays, hook up once we have
		# SplashScreen opening after prefs loading (as MainFrame is)
		# so it too can be placed in the appropriate display (currently always opens
		# in primary display).
		# displays = [wx.Display(didx) for didx in range(wx.Display.GetCount())]
		# display_width = sum([disp.GetGeometry().GetWidth() for disp in displays])
		# display_height = sum([disp.GetGeometry().GetHeight() for disp in displays])
		display_x, display_y = wx.DisplaySize()
		if (win_x > display_x) or (win_y > display_y):
			win_x = 0
			win_y = 23 

		self.SetPosition((win_x, win_y))

# 		win_width = self.Width
# 		win_height = self.Height
# 		#print "[DEBUG] Window Width = " + str(win_width) + " " + str(win_height)
# 		if sys.platform != 'win32':
# 			win_height = self.Height + 40
# 		else:
# 			win_width = win_width + 8
# 			win_height = self.Height + 76
		
		# 4/10/2014 brg: init depends on self.DBPath among others...
		self.dataFrame = dbmanager.DataFrame(self)
		
		conf_str = ""
		conf_array = []

		#if self.config.has_option("applications", "middlebarposition"):
		#	str_temp =  self.config.get("applications", "middlebarposition")
		#	if len(str_temp) > 0:
		#		conf_value = int ( str_temp ) 
		#		if conf_value > (display_x -340):
		#			conf_value = display_x - 340
		#		self.Window.splicerX = conf_value
		#if self.Window.splicerX  < 150:
		#	self.Window.splicerX = 180

		#if self.config.has_option("applications", "startdepth"):
		#	str_temp = self.config.get("applications", "startdepth")
		#	if len(str_temp) > 0:
		#		conf_value = float ( str_temp )
		#		self.Window.rulerStartDepth = conf_value 

		if self.config.has_option("applications", "tiedotsize"):
			str_temp = self.config.get("applications", "tiedotsize")
			if len(str_temp) > 0:
				conf_value = int ( str_temp )
				self.Window.tieDotSize = conf_value 

		if self.config.has_option("applications", "tiewidth"):
			str_temp = self.config.get("applications", "tiewidth")
			if len(str_temp) > 0:
				conf_value = int ( str_temp )
				self.Window.tieline_width = conf_value 

		#if self.config.has_option("applications", "secondstartdepth"):
		#	str_temp = self.config.get("applications", "secondstartdepth")
		#	if len(str_temp) > 0:
		#		conf_value = float ( str_temp )
		#		self.Window.SPrulerStartDepth = conf_value 

		self.Window.rulerUnits = "m" # default to meters
		if self.config.has_option("applications", "rulerunits"):
			rulerUnitsStr = self.config.get("applications", "rulerunits")
			if len(rulerUnitsStr) > 0:
				self.Window.rulerUnits = rulerUnitsStr
		unitIndex = self.Window.GetRulerUnitsIndex()
		self.optPanel.unitsPopup.SetSelection(unitIndex)

		if self.config.has_option("applications", "rulerrange"):
			conf_str = self.config.get("applications", "rulerrange")
			if len(conf_str) > 0:
				conf_array = conf_str.split()
				self.optPanel.depthRangeMin.SetValue(conf_array[0])
				self.optPanel.depthRangeMax.SetValue(conf_array[1])
				self.optPanel.OnDepthViewAdjust(None)

		if self.config.has_option("applications", "rulerscale"):
			str_temp = self.config.get("applications", "rulerscale")
			if len(str_temp) > 0:
				conf_value = int ( str_temp )
				self.optPanel.depthZoomSlider.SetValue(conf_value)
				self.optPanel.OnRulerOneScale(None)

		if self.config.has_option("applications", "shiftrange"):
			str_temp = self.config.get("applications", "shiftrange")
			if len(str_temp) > 0:
				conf_value = float ( str_temp )
				self.optPanel.tie_shift.SetValue(str_temp)
				self.optPanel.OnTieShiftScale(None)

		if self.config.has_option("applications", "splicewindow"):
			str_temp = self.config.get("applications", "splicewindow")
			if len(str_temp) > 0:
				conf_value = int ( str_temp )
			if conf_value == 0:
				self.Window.spliceWindowOn = 1 
				self.OnActivateWindow(1)
				self.misecond.Check(False)
			else: 
				self.Window.spliceWindowOn = 0 
				self.OnActivateWindow(0)
				self.misecond.Check(True)
		
		conf_value = 0
		if self.config.has_option("applications", "secondscroll"):
			str_temp = self.config.get("applications", "secondscroll")
			if len(str_temp) > 0:
				conf_value = int(str_temp)
			# if conf_value == 0:
			# 	self.SetIndependentScroll(False)
			# else:
			# 	self.SetIndependentScroll(True)

		if self.config.has_option("applications", "colors"):
			conf_str = self.config.get("applications", "colors") 
			if len(conf_str) > 0:
				# saved color string is of form "R0 G0 B0 R1 G1 B1...". Order corresponds to
				# self.Window.colorDictKeys, so 'mbsf' color is (R0, G0, B0), 'ccsfTie'
				# is (R1, G1, B1), and so on.
				rgbs = conf_str.split()
				if len(rgbs) % 3 != 0 or len(rgbs) % len(self.Window.colorDictKeys):
					print("Expected {} saved color components, found {}, using defaults.".format(3 * len(self.Window.colorDictKeys), len(rgbs)))
				else:
					for index, key in enumerate(self.Window.colorDictKeys):
						color = wx.Colour(int(rgbs[index * 3]), int(rgbs[index * 3 + 1]), int(rgbs[index * 3 + 2]))
						self.Window.colorDict[key] = color

		if self.config.has_option("applications", "overlapcolors"):
			conf_str = self.config.get("applications", "overlapcolors") 
			if len(conf_str) > 0:
				conf_array = conf_str.split()
				self.Window.overlapcolorList = []
				for i in range(9):
					r = int(conf_array[i*3])
					g = int(conf_array[i*3+1]) 
					b = int(conf_array[i*3+2]) 
					self.Window.overlapcolorList.insert(i, wx.Colour(r, g, b))

		# see 11/2/2013 brg
		#if self.config.has_option("applications", "fontsize"):
		#	str_temp = self.config.get("applications", "fontsize")
		#	if len(str_temp) > 0:
		#		conf_value = int ( str_temp )
		#		self.Window.stdFont.SetPointSize(conf_value)
			
		if self.config.has_option("applications", "fontstartdepth"):
			str_temp = self.config.get("applications", "fontstartdepth")
			if len(str_temp) > 0:
				conf_value = float ( str_temp )			
				self.Window.startDepthPix = conf_value
				self.Window.startAgeDepth = conf_value
		
		if self.config.has_option("applications", "showline"):
			str_temp = self.config.get("applications", "showline")
			if len(str_temp) > 0:
				if str_temp == "1":
					self.Window.showHoleGrid = True 
					self.optPanel.showPlotLines.SetValue(True)
				else:
					self.Window.showHoleGrid = False 
					self.optPanel.showPlotLines.SetValue(False)

		if self.config.has_option("applications", "showSectionDepths"):
			str_temp = self.config.get("applications", "showSectionDepths")
			if len(str_temp) > 0:
				self.Window.showSectionDepths = True if str_temp == '1' else False 
				self.optPanel.showSectionDepths.SetValue(self.Window.showSectionDepths)

		if self.config.has_option("applications", "showCoreImages"):
			str_temp = self.config.get("applications", "showCoreImages")
			if len(str_temp) > 0:
				self.Window.showCoreImages = True if str_temp == '1' else False 
				self.optPanel.showCoreImages.SetValue(self.Window.showCoreImages)

		if self.config.has_option("applications", "showAffineShiftInfo"):
			str_temp = self.config.get("applications", "showAffineShiftInfo")
			if len(str_temp) > 0:
				self.Window.showAffineShiftInfo = True if str_temp == '1' else False 
				self.optPanel.showAffineShiftInfo.SetValue(self.Window.showAffineShiftInfo)

		if self.config.has_option("applications", "showAffineTieArrows"):
			str_temp = self.config.get("applications", "showAffineTieArrows")
			if len(str_temp) > 0:
				self.Window.showAffineTieArrows = True if str_temp == '1' else False 
				self.optPanel.showAffineTieArrows.SetValue(self.Window.showAffineTieArrows)

		if self.config.has_option("applications", "showCoreInfo"):
			str_temp = self.config.get("applications", "showCoreInfo")
			if len(str_temp) > 0:
				self.Window.showCoreInfo = True if str_temp == '1' else False 
				self.optPanel.showCoreInfo.SetValue(self.Window.showCoreInfo)

		if self.config.has_option("applications", "showOutOfRangeData"):
			str_temp = self.config.get("applications", "showOutOfRangeData")
			if len(str_temp) > 0:
				self.Window.showOutOfRangeData = True if str_temp == '1' else False 
				self.optPanel.showOutOfRangeData.SetValue(self.Window.showOutOfRangeData)

		if self.config.has_option("applications", "showColorLegend"):
			str_temp = self.config.get("applications", 'showColorLegend')
			if len(str_temp) > 0:
				self.Window.showColorLegend = True if str_temp == '1' else False
				self.optPanel.showColorLegend.SetValue(self.Window.showColorLegend)

		if self.config.has_option("applications", "scrollsize"):
			str_temp = self.config.get("applications", "scrollsize")
			if len(str_temp) > 0:
				conf_value = int ( str_temp )
				self.Window.ScrollSize = conf_value

		if self.config.has_option("applications", "discreteplotmode"):
			str_temp = self.config.get("applications", "discreteplotmode")
			if len(str_temp) > 0:
				conf_value = int ( str_temp )
				self.Window.DiscretePlotMode = conf_value
				if conf_value == 1:
					self.miplot.Check(True)
			
		if self.config.has_option("applications", "toolbar"):
			conf_str = self.config.get("applications", "toolbar")
			if len(conf_str) > 0:
				conf_array = conf_str.split()
				x = int(conf_array[0])
				y = int(conf_array[1])
				if x >= display_x:
					x = 300
				if y >= display_y:
					y = 200
				self.topMenu.SetPosition((x, y))
			
		#if self.config.has_option("applications", "startup"):
		#	conf_str = self.config.get("applications", "startup")
		#	if conf_str == "False":
		#		self.dataFrame.startupbtn.SetValue(False)
		#		self.dataFrame.startup = 0 
		#		self.midata.Check(False)

		if self.config.has_option("applications", "tab"):
			str_temp = self.config.get("applications", "tab")
			if len(str_temp) > 0:
				count = int(str_temp)
				if count >= self.Window.sideNote.GetPageCount():
					count = 1
				self.Window.sideNote.SetSelection(count)

		if self.config.has_option("applications", "leadlag"):
			str_temp = self.config.get("applications", "leadlag")
			if len(str_temp) > 0:
				self.leadLag = float(str_temp)

		if self.config.has_option("applications", "middlebarposition"):
			str_temp =  self.config.get("applications", "middlebarposition")
			if len(str_temp) > 0:
				conf_value = int ( str_temp ) 
				if conf_value > (display_x -340):
					conf_value = display_x - 340
				self.Window.splicerX = conf_value
		if self.Window.splicerX  < 150:
			self.Window.splicerX = 180

		if self.config.has_option("applications", "startdepth"):
			str_temp = self.config.get("applications", "startdepth")
			if len(str_temp) > 0:
				conf_value = float ( str_temp )
				self.Window.rulerStartDepth = conf_value 

		if self.config.has_option("applications", "secondstartdepth"):
			str_temp = self.config.get("applications", "secondstartdepth")
			if len(str_temp) > 0:
				conf_value = float ( str_temp )
				self.Window.SPrulerStartDepth = conf_value 

		if self.config.has_option("applications", "winlength"):
			str_temp = self.config.get("applications", "winLength")
			if len(str_temp) > 0:
				self.winLength = float(str_temp)

		self.OnUpdateGraphSetup(1)
		self.OnUpdateGraphSetup(2)
		self.OnUpdateGraphSetup(3)

		if new_flag == False:
			if self.config.has_option("applications", "dbpath"):
				str_temp = self.config.get("applications", "dbpath")
				if len(str_temp) > 0:
					if os.access(str_temp, os.F_OK) == True:
						str_len =  len(str_temp) -1
						self.DBPath = str_temp
						if platform_name[0] == "Windows":
							if str_temp[str_len] != "\\":
								self.DBPath = str_temp + "\\"
						else:
							if str_temp[str_len] != "/":
								self.DBPath = str_temp + "/"
						self.dataFrame.PathTxt.SetValue("Path: " + self.DBPath)
					else:
						self.DBPath = myPath
						self.dataFrame.PathTxt.SetValue("Path: " + self.DBPath)
		else:
			self.DBPath = myPath
			self.dataFrame.PathTxt.SetValue("Path: " + self.DBPath)


		if self.DBPath == "-":
			self.DBPath = User_Dir  + "/Documents/Correlator/" + vers.BaseVersion  + "/"
			if platform_name[0] == "Windows":
				self.DBPath =  User_Dir  + "\\Correlator\\" + vers.BaseVersion + "\\"
			self.dataFrame.PathTxt.SetValue("Path: " + self.DBPath)
			
			if os.access(self.DBPath, os.F_OK) == False:
				os.mkdir(self.DBPath)
			prefile = self.DBPath + "db"
			if os.access(prefile, os.F_OK) == False:
				os.mkdir(prefile)
			#print "[DEBUG] " + prefile + " is created"

		#print "[DEBUG] Data Repository path  is " + self.DBPath

		global_logFile = open(self.DBPath + global_logName, "a+")
		global_logFile.write("Start of Session:\n")
		s = "BY " + getpass.getuser()  + "\n"
		global_logFile.write(s)
		s = str(datetime.today()) + "\n\n"
		global_logFile.write(s)
		self.logFileptr = global_logFile

		self.dataFrame.OnLOADCONFIG()

		#data_loaded = False
		if self.config.has_option("applications", "data"):
			conf_str = self.config.get("applications", "data")
			conf_array = conf_str.split()
			# HYEJUNG DB
			#if (self.dataFrame.listPanel.GetCellValue(0, 0) != '') and (len(conf_array) > 0):
			#	if conf_array[0] != "-1":
			#		for data in conf_array:
			#			self.dataFrame.listPanel.SelectRow(int(data), True)
			#		self.CurrentDataNo = int(conf_array[0]) 
			#		data_loaded = self.dataFrame.OnLOAD(1)
					
			#self.CurrentDataNo = conf_value
			#if conf_value >= 0:
			#	self.dataFrame.listPanel.SelectRow(conf_value)
			#	data_loaded = self.dataFrame.OnLOAD(1)


		if self.config.has_option("applications", "path"):
			str_temp = self.config.get("applications", "path")
			if len(str_temp) > 0:
				self.Directory = str_temp

		# total hole width - still used for splice and log, supplanted
		# by coreImageWidth and plotWidth for composite area
		# if self.config.has_option("applications", "datawidth"):
		# 	str_temp = self.config.get("applications", "datawidth")
		# 	if len(str_temp) > 0:
		# 		conf_value = int(str_temp)
		# 		self.optPanel.holeWidthSlider.SetValue(conf_value)
		# 		self.optPanel.OnChangeHoleWidth(None)

		if self.config.has_option("applications", "plotwidth"):
			str_temp = self.config.get("applications", "plotwidth")
			if len(str_temp) > 0:
				conf_value = int(str_temp)
				self.optPanel.plotWidthSlider.SetValue(conf_value)
				self.optPanel.OnChangePlotWidth(None)

		if self.config.has_option("applications", "imagewidth"):
			str_temp = self.config.get("applications", "imagewidth")
			if len(str_temp) > 0:
				conf_value = int(str_temp)
				self.optPanel.imageWidthSlider.SetValue(conf_value)
				self.optPanel.OnChangeImageWidth(None)

		img = wx.Image(opj("images/scrollbutton1.jpg"))
		img.Rescale(self.Window.ScrollSize, img.GetHeight())
		bmp = img.ConvertToBitmap()			
		DrawData["Skin"] = (bmp, -self.Window.ScrollSize, scroll_start)

		img = wx.Image(opj("images/vscrollbutton1.jpg"))
		img.Rescale(img.GetWidth(), self.Window.ScrollSize)
		bmp = img.ConvertToBitmap()
		DrawData["HScroll"] = (bmp, self.Window.compositeX, -self.Window.ScrollSize)

		self.half = -self.Window.ScrollSize - 5

		img = wx.Image(opj("images/scrollbutton1.jpg"))
		img.Rescale(self.Window.ScrollSize, img.GetHeight())
		bmp = img.ConvertToBitmap()
		DrawData["MovableSkin"] = (bmp, self.half, scroll_start)
		
		img = wx.Image(opj("images/scrollbutton1.jpg"))
		img.Rescale(self.Window.ScrollSize, img.GetHeight())
		bmp = img.ConvertToBitmap()
		width = -self.Window.ScrollSize 
		DrawData["Interface"] = (bmp, width, scroll_start)

		img = wx.Image(opj("images/scrollbutton1.jpg"))
		img.Rescale(self.Window.ScrollSize, img.GetHeight())
		bmp = img.ConvertToBitmap()		
		DrawData["MovableInterface"] = (bmp, self.half, scroll_start)

		if self.ScrollMax != 0:
			self.Window.UpdateScroll(1)
			self.Window.UpdateScroll(2)
			self.Window.ScrollUpdate = 1

		return DrawData


class AffineController:
	def __init__(self, parent):
		self.parent = parent # MainFrame - oy, this dependency!
		self.affine = AffineBuilder() # AffineBuilder for current affine table
		self.undoStack = [] # track previous AffineBuilder states for undo
		self.dirty = False # has affine state changed since last save?
		self.currentAffineFile = None # most-recently loaded or saved affine file (if any)
	
	# remove all shifts, re-init state members
	def clear(self):
		self.affine.clear()
		self.undoStack = []
		self.dirty = False
		self.currentAffineFile = None
		
	def load(self, filepath):
		if filepath is not None:
			self.affine = AffineBuilder.createWithAffineFile(filepath, self.parent.sectionSummary)
			self.currentAffineFile = filepath
		else:
			self.affine = AffineBuilder.createWithSectionSummary(self.parent.sectionSummary)
		
	def save(self, affineFilePath):
		affineRows = []
		shifts = self.affine.getSortedShifts()
		for hole in self.affine.getSortedHoles():
			previousOffset = None
			for curShift in [s for s in shifts if s.core.hole == hole]:
				site = self.parent.Window.GetHoleSite(hole)
				if not site:
					# If data for hole isn't loaded, grab site from section summary.
					# We assume a single site is loaded at a time in Correlator.
					ssSites = self.parent.sectionSummary.getSites()
					site = list(ssSites)[0]
				coreType = self.parent.sectionSummary.getCoreType(site, hole, curShift.core.core)
				csf, dummy = self.parent.sectionSummary.getCoreRange(site, hole, curShift.core.core)
				csf = round(csf, 3)
				ccsf = round(csf + curShift.distance, 3)
				cumOff = round(curShift.distance, 3)
				diffOff = 0.0 if previousOffset is None else cumOff - previousOffset
				try:
					growthRate = round(ccsf / csf, 3)
				except ZeroDivisionError:
					growthRate = 0.0
					
				fixedTieCsf = shiftedTieCsf = fixedCore = ""
				if isTie(curShift):
					fixedTieCsf = curShift.fromDepth
					shiftedTieCsf = curShift.depth
					fixedCore = curShift.fromCore.GetHoleCoreStr()
				
				series = pandas.Series({'Site':site, 'Hole':hole, 'Core':curShift.core.core, 'Core type':coreType, \
										'Core top depth CSF-A (m)':csf, 'Core top depth CCSF (m)':ccsf, 'Cumulative offset (m)':round(cumOff,3), \
										'Differential offset (m)':round(diffOff, 3), 'Growth rate':growthRate, 'Shift type':curShift.typeStr(), \
										'Data used':curShift.dataUsed, 'Quality comment':curShift.comment, 'Reference core':fixedCore, \
										'Reference tie point CSF-A (m)':fixedTieCsf, 'Shift tie point CSF-A (m)':shiftedTieCsf})
				
				affineRows.append(series)
		if len(affineRows) > 0:
			df = pandas.DataFrame(columns=tabularImport.AffineFormat.req)
			df = df.append(affineRows, ignore_index=True)
			tabularImport.writeToFile(df, affineFilePath)
			self.currentAffineFile = affineFilePath
			self.dirty = False
		
	def updateGUI(self):
		self.parent.compositePanel.UpdateAffineTable()
		self.parent.compositePanel.UpdateUndoButton()
		
	def pushState(self):
		prevAffine = copy.deepcopy(self.affine)
		self.undoStack.append(prevAffine)
	
	def isDirty(self):
		return self.dirty

	def confirmBreaks(self, breaks):
		confirmed = True
		if len(breaks) > 0:
			msg = "This operation will break the following TIEs:\n\n"
			msg += "{}\n".format(self._makeBreaksString(breaks))
			msg += "Do you want to continue?"
			confirmed = self.parent.OnShowMessage("Confirm Breaks", msg, 0) == wx.ID_YES
		return confirmed

	def _makeBreaksString(self, breaks):
		bs = ""
		for b in breaks:
			bs += "{} > {}\n".format(b[0], b[1])
		return bs

	# shift a single untied core with method SET
	def set(self, hole, core, distance, dataUsed="", comment=""):
		if self.affine.isTie(aci(hole, core)):
			errmsg = "Core {}{} is shifted by a TIE and is part of a chain.\nIt cannot be SET unless that TIE is broken first.".format(hole, core)
			self.parent.OnShowMessage("Error", errmsg, 1)
			return

		setOp = self.affine.set(aci(hole, core), distance, dataUsed, comment)
		if not self.confirmBreaks(setOp.infoDict['breaks']):
			return
		if not self.removeShiftingCoresFromSplice(setOp.getCoresToBeMoved()):
			return
		self.pushState()
		self.affine.execute(setOp)
		self.dirty = True
		self.updateGUI()

	# Shift an entire chain by shifting chain root with method SET.
	# All descendants will remain TIEs.
	def setChainRoot(self, hole, core, distance, dataUsed="", comment=""):
		if self.affine.isRoot(aci(hole, core)):
			setChainOp = self.affine.setChainRoot(aci(hole, core), distance, dataUsed, comment)
			if not self.removeShiftingCoresFromSplice(setChainOp.getCoresToBeMoved()):
				return
			self.pushState()
			self.affine.execute(setChainOp)
			self.dirty = True
			self.updateGUI()
		else:
			msg = "The selected core, {}{}, is not the root core of a chain.\n" \
			"The root core must be selected to shift an entire chain.".format(hole, core)
			self.parent.OnShowMessage("Error", msg, 1)
		
	# shift all untied cores in a hole with method SET
	def setAll(self, hole, coreList, value, isPercent, dataUsed="", comment=""):
		site = self.parent.Window.GetHoleSite(hole)
		setAllOp = self.affine.setAll(hole, coreList, value, isPercent, site, self.parent.sectionSummary, dataUsed, comment)

		proceed = True
		tieCores = setAllOp.infoDict['tieCores']
		if len(tieCores) > 0:
			tieCoreNames = [str(c) for c in tieCores]
			msg = "The following cores are shifted by a TIE and are part of a chain:\n\n{}\n\n" \
			"They will not be SET unless you first break their TIEs. " \
			"Do you still want to SET untied cores?".format(', '.join(tieCoreNames))
			proceed = self.parent.OnShowMessage("Warning", msg, 0) == wx.ID_YES

		# warn/confirm about breaks for chain roots that will be moved...
		chainRoots = setAllOp.infoDict['chainRoots']
		if proceed and len(chainRoots) > 0:
			chainRootNames = [str(c) for c in chainRoots]
			breaksStr = self._makeBreaksString(setAllOp.infoDict['breaks'])
			msg = "The following cores are the root of a TIE chain:\n\n{}\n\n" \
			"Shifting them by SET will break the following TIEs:\n\n{}\n" \
			"Do you still want to proceed with this SET?".format(', '.join(chainRootNames), breaksStr)
			proceed = self.parent.OnShowMessage("Confirm Breaks", msg, 0) == wx.ID_YES

		if proceed: # warn/confirm about removing shifting cores from splice
			proceed = self.removeShiftingCoresFromSplice(setAllOp.getCoresToBeMoved())

		if proceed:
			self.pushState()
			self.affine.execute(setAllOp)
			self.dirty = True
			self.updateGUI()
			
	# fromDepth - MBSF depth of tie point on fromCore
	# depth - MBSF depth of tie point on core
	# Returns True if tie was made, False if not (user didn't confirm breaks)
	def tie(self, coreOnly, fromHole, fromCore, fromDepth, hole, core, depth, dataUsed="", comment=""):
		fromCoreInfo = aci(fromHole, fromCore)
		coreInfo = aci(hole, core)
		# adjust movable core's depth for affine
		mcdShiftDist = fromDepth - depth
		fromDepth = fromDepth - self.affine.getShift(fromCoreInfo).distance
		depth = depth - self.affine.getShift(coreInfo).distance
		
		tieOp = self.affine.tie(coreOnly, mcdShiftDist, fromCoreInfo, fromDepth, coreInfo, depth, dataUsed, comment)
		if not self.confirmBreaks(tieOp.infoDict['breaks']):
			return False
		if not self.removeShiftingCoresFromSplice(tieOp.getCoresToBeMoved()):
			return False

		self.pushState()
		self.affine.execute(tieOp)
		self.dirty = True
		self.updateGUI()
		return True

	# Find splice intervals with cores in shiftingCores, prompt user and remove
	# intervals if confirmed.
	# Return True if user confirmed, or no matching splice intervals were found.
	# Otherwise return False.
	def removeShiftingCoresFromSplice(self, shiftingCores):
		coresInSplice = []
		intervalsToRemove = []
		for sc in shiftingCores:
			intervals = self.parent.spliceManager.findIntervals(sc.hole, sc.core)
			if len(intervals) > 0:
				intervalsToRemove += intervals
				coresInSplice.append(sc)
		if len(intervalsToRemove) > 0:
			msg = "This operation affects cores included in the current splice:\n\n"
			msg += "{}\n\n".format(', '.join(sorted([str(sc) for sc in coresInSplice])))
			msg += "These cores will be removed from the splice, which cannot be undone.\n\n"
			msg += "Do you want to continue?"
			if self.parent.OnShowMessage("Splice Intervals Affected", msg, 0) == wx.ID_YES:
				for interval in intervalsToRemove:
					self.parent.spliceManager.delete(interval)
			else:
				self.parent.Window.ClearCompositeTies()
				return False
		return True

	def breakTie(self, coreStr):
		core = acistr(coreStr)
		if self.affine.hasShift(core) and isTie(self.affine.getShift(core)):
			self.pushState()
			self.affine.makeImplicit(core)
			self.dirty = True
			self.updateGUI()
			self.parent.Window.UpdateDrawing()

	def hasShift(self, hole, core):
		return self.affine.hasShift(aci(hole, str(core)))

	# return shift for hole-core combination
	def getShift(self, hole, core):
		return self.affine.getShift(aci(hole, str(core)))
	
	def getShiftColor(self, hole, core):
		shift = self.affine.getShift(aci(hole, str(core)))
		if isTie(shift):
			return self.parent.Window.colorDict['ccsfTie']
		elif isSet(shift):
			return self.parent.Window.colorDict['ccsfSet']
		elif isImplicit(shift) and shift.distance != 0.0:
			return self.parent.Window.colorDict['ccsfRel']
		else:
			return self.parent.Window.colorDict['mbsf']
		
	# if hole-core combination is a TieShift, return MCD depth of TIE point and AffineCoreInfo of parent core
	def getTieDepthAndParent(self, hole, core):
		shift = self.affine.getShift(aci(hole, str(core)))
		assert isTie(shift)
		return shift.depth + shift.distance, shift.fromCore
		
	# todo: part of AffineShift and subclasses?
	def getShiftTypeStr(self, hole, core):
		shift = self.affine.getShift(aci(hole, str(core)))
		return shift.typeStr()
	
	# return shift distance for hole-core
	def getShiftDistance(self, hole, core):
		return self.affine.getShift(aci(hole, str(core))).distance
	
	# gross, but useful
	def getCoreTop(self, coreinfo):
		# use section summary to get core's min and max values
		secsumm = self.parent.sectionSummary
		coremin, coremax = secsumm.getCoreRange(coreinfo.leg, coreinfo.hole, coreinfo.holeCore)
		return coremin
	
	# get rows for UI affine table: each tuple is hole+core, shift distance, and shift type
	def getAffineRowsForUI(self):
		rows = []
		for shift in self.affine.getSortedShifts():
			core = shift.core.GetHoleCoreStr()
			offset = str(shift.distance)
			shiftType = self.getShiftTypeStr(shift.core.hole, shift.core.core)
			if isTie(shift): # include reference core for ties
				shiftType += " ({})".format(shift.fromCore)
			rows.append((core, offset, shiftType))
		return rows

	# Return list of TIE chain roots as (hole, core) tuples
	def getChainRoots(self):
		roots = self.affine.getChainRoots()
		return [(str(r.hole), str(r.core)) for r in roots]
	
	# moveCore and fixedCore are CoreInfo objects
	def isLegalTie(self, moveCore, fixedCore):
		return self.affine.isLegalTie(aci(moveCore.hole, moveCore.holeCore), aci(fixedCore.hole, fixedCore.holeCore))
	
	def canUndo(self):
		return len(self.undoStack) > 0
	
	def undo(self):
		assert self.canUndo()
		prevAffineBuilder = self.undoStack.pop()
		self.affine = prevAffineBuilder
		self.dirty = True
		self.updateGUI()

	
# brgtodo 12/21/2015: still depends on MainFrame 
class SpliceController:
	def __init__(self, parent):
		self.parent = parent # MainFrame
		self.splice = splice.SpliceBuilder() # SpliceBuilder for current splice
		self.altSplice = splice.SpliceBuilder() # SpliceBuilder for alternate splice
		self.currentSpliceFile = None
		
		self.clear() # init selection, file state members
		
		self.selChangeListeners = []
		self.addIntervalListeners = []
		self.deleteIntervalListeners = []
		
	# splice interval selection
	def hasSelection(self):
		return self.selected is not None

	def _canDeselect(self):
		result = True
		if self.hasSelection():
			result = self.selected.valid()
		return result
	
	def _updateSelection(self, interval):
		if (interval != self.selected):
			self.selected = interval
			self._updateTies()
			self._onSelChange()
			
	def clear(self):
		self.splice.clear()
		self.altSplice.clear()
		self.currentSpliceFile = None
		self.selected = None # selected SpliceInterval
		self.selectedTie = None # selected splice handle
		self.topTie = None # brgtodo: rename to handles since these don't always represent a "TIE"
		self.botTie = None
		self.dirty = False # is self.splice in a modified, unsaved state?
		self.errorMsg = "All is well at the moment!"
		
	def count(self):
		return self.splice.count()
	
	def getDataTypes(self):
		return self.splice.getDataTypes()
	
	# return coreinfo for first interval in alternate splice
	def getAltInfo(self):
		info = None
		if self.altSplice.count() > 0:
			info = self.altSplice.getIntervalAtIndex(0).coreinfo
		return info
	
	def getIntervals(self):
		return self.splice.ints
	
	def getIntervalAtDepth(self, depth):
		return self.splice.getIntervalAtDepth(depth)
	
	def getIntervalAtIndex(self, index):
		return self.splice.getIntervalAtIndex(index)
	
	def getIntervalsInRange(self, mindepth, maxdepth):
		return self.splice.getIntervalsInRange(mindepth, maxdepth)

	def add(self, coreinfo):
		# replace native-side coremin/max with Section Summary values
		coremin, coremax = self.getCoreRange(coreinfo)
		coreinfo.minDepth = coremin
		coreinfo.maxDepth = coremax
		if self.splice.add(coreinfo):
			self._onAdd()
			
	def delete(self, interval):
		if self.hasSelection() and interval == self.selected:
			self.deleteSelected()
		else:
			self.splice.delete(interval)
		self.setDirty(self.count() > 0) # can't save a splice with zero intervals
		self._onDelete()
			
	def select(self, depth):
		good = False
		if self._canDeselect():
			good = True
			selInt = self.splice.getIntervalAtDepth(depth)
			self._updateSelection(selInt)
		else:
			self._setErrorMsg("Can't deselect current interval, it has zero length. You may delete.")
		return good
	
	def selectByIndex(self, index):
		if self._canDeselect():
			if len(self.splice.ints) > index:
				self._updateSelection(self.splice.ints[index])
		else:
			self._setErrorMsg("Can't deselect current interval, it has zero length. You may delete.")

	def getSelected(self):
		return self.selected
	
	def getSelectedIndex(self):
		return self.splice.ints.index(self.selected) if self.hasSelection() else -1
	
	def deleteSelected(self):
		if self.splice.delete(self.selected):
			self.selected = None
			self.selectTie(None)
			self.setDirty(self.count() > 0) # can't save a splice with zero intervals
			self._onSelChange()
			
	def selectTie(self, siTie):
		if siTie in self.getTies():
			self.selectedTie = siTie
		elif siTie is None:
			self.selectedTie = None
			
	def getSelectedTie(self):
		return self.selectedTie
	
	def getTies(self):
		result = []
		if self.topTie is not None and self.botTie is not None:
			result = [self.topTie, self.botTie]
		return result

	def _updateTies(self):
		if self.hasSelection():
			intAbove = self.splice.getIntervalAbove(self.selected)
			intBelow = self.splice.getIntervalBelow(self.selected)
			self.topTie = splice.SpliceIntervalTopTie(self.selected, intAbove)
			self.botTie = splice.SpliceIntervalBotTie(self.selected, intBelow)
		else:
			self.topTie = self.botTie = None

	def addSelChangeListener(self, listener):
		if listener not in self.selChangeListeners:
			self.selChangeListeners.append(listener)
			
	def removeSelChangeListener(self, listener):
		if listener in self.selChangeListeners:
			self.selChangeListeners.remove(listener)
			
	def addAddIntervalListener(self, listener):
		if listener not in self.addIntervalListeners:
			self.addIntervalListeners.append(listener)
			
	def removeAddIntervalListener(self, listener):
		if listener in self.addIntervalListeners:
			self.addIntervalListeners.remove(listener)
			
	def addDeleteIntervalListener(self, listener):
		if listener not in self.deleteIntervalListeners:
			self.deleteIntervalListeners.append(listener)
			
	def removeDeleteIntervalListener(self, listener):
		if listener in self.deleteIntervalListeners:
			self.deleteIntervalListeners.remove(listener)

	def _onAdd(self, dirty=True):
		self._updateTies()
		if dirty:
			self.setDirty()
		for listener in self.addIntervalListeners:
			listener()
			
	def _onDelete(self):
		for listener in self.deleteIntervalListeners:
			listener()

	def _onSelChange(self):
		for listener in self.selChangeListeners:
			listener()
			
	def isDirty(self):
		return self.dirty

	def setDirty(self, dirty=True):
		self.dirty = dirty
		
	def _setErrorMsg(self, msg):
		self.errorMsg = msg
		
	def getErrorMsg(self):
		return self.errorMsg
		
	def getCoreRange(self, coreinfo):
		# use section summary to get core's min and max values
		secsumm = self.parent.sectionSummary
		coremin, coremax = secsumm.getCoreRange(coreinfo.leg, coreinfo.hole, coreinfo.holeCore)
		affineOffset = self.parent.Window.findCoreAffineOffset(coreinfo.hole, coreinfo.holeCore)
		#print "{}: coremin = {}, coremax = {}".format(coreinfo.getHoleCoreStr(), coremin, coremax)
		return coremin + affineOffset, coremax + affineOffset
			
	def save(self, filepath):
		# better to create dependencies on SectionSummary and a non-existent "HoleDatabase" class, though
		# HoleData will do...though we only need it for affine stuff, so possibly an AffineManager?
		print "Saving splice to {}".format(filepath)
		
		rows = []
		
		secsumm = self.parent.sectionSummary
		#print str(secsumm.dataframe)
		#print "\n##############################\n"
		
		# brgtodo: write mm-rounded values? possible to get long wacky decimals at present
		for index, si in enumerate(self.splice.ints):
			site = si.coreinfo.leg # mixed-up site and leg, ugh.
			hole = si.coreinfo.hole
			core = si.coreinfo.holeCore
			#print "Saving Interval {}: {}".format(index, si.coreinfo.getHoleCoreStr())
			
			offset = self.parent.Window.findCoreAffineOffset(hole, core)
			#print "   affine offset = {}".format(si.coreinfo.getHoleCoreStr(), offset)
			# section summary is always in CSF-A, remove CCSF-A/MCD offset for calculations
			mbsfTop = round(si.getTop() - offset, 3)
			mcdTop = round(si.getTop(), 3)
			topSection = secsumm.getSectionAtDepth(site, hole, core, mbsfTop)
			if topSection is not None:
				topDepth = secsumm.getSectionTop(site, hole, core, topSection)
				topOffset = round((mbsfTop - topDepth) * 100.0, 1) # section depth in cm
			else:
				print "Skipping, couldn't find top section at top CSF depth {}".format(mbsfTop)
				continue
			
			mbsfBot = round(si.getBot() - offset, 3)
			mcdBot = round(si.getBot(), 3)
			botSection = secsumm.getSectionAtDepth(site, hole, core, mbsfBot)
			if botSection is not None:
				# bottom offset is poorly named: from the interval's bottom depth, it is the
				# offset from the top (not bottom) of the containing section
				botDepth = secsumm.getSectionTop(site, hole, core, botSection)
				botOffset = round((mbsfBot - botDepth) * 100.0, 1) # section depth in cm
			else:
				print "Skipping, couldn't find section at bottom CSF depth {}".format(mbsfBot)
				continue
			
			coreType = secsumm.getSectionCoreType(site, hole, core, botSection)
			
			# stub out for now: type for each of top and bottom? "CORE" type per Peter B's request?
			spliceType = "APPEND"
			if index < self.splice.count() - 1:
				if self.splice.ints[index+1].getTop() == si.getBot():
					spliceType = "TIE"
					
			#print "   topSection {}, offset {}, depth {}, mcdDepth {}\nbotSection {}, offset {}, depth {}, mcdDepth {}\ntype {}, data {}, comment {}".format(topSection, topOffset, mbsfTop, mbsfTop+offset, botSection, botOffset, mbsfBot, mbsfBot+offset, spliceType, si.coreinfo.type, si.comment)
			
			series = pandas.Series({'Site':site, 'Hole':hole, 'Core':core, 'Core Type':coreType, \
									'Top Section':topSection, 'Top Offset':topOffset, 'Top Depth CSF-A':mbsfTop, 'Top Depth CCSF-A':mcdTop, \
									'Bottom Section':botSection, 'Bottom Offset':botOffset, 'Bottom Depth CSF-A':mbsfBot, 'Bottom Depth CCSF-A':mcdBot, \
									'Splice Type':spliceType, 'Data Used':si.coreinfo.type, 'Comment':si.comment})
			rows.append(series)			
		if len(rows) > 0:
			df = pandas.DataFrame(columns=tabularImport.SITFormat.req)
			df = df.append(rows, ignore_index=True)
			#print "{}".format(df)
			tabularImport.writeToFile(df, filepath)
			self.currentSpliceFile = filepath
			self.setDirty(False)
			
	def load(self, filepath, destSplice, datatype=None):
		df = tabularImport.readFile(filepath)
		self.currentSpliceFile = filepath
		previousSpliceType = None
		previousAffBot = None
		for index, row in df.iterrows(): # itertuples() is faster if needed
			#print "Loading row {}: {}".format(index, str(row))
			coreinfo, affineOffset, top, bot, fileTop, fileBot, appliedTop, appliedBot = self.getRowDepths(row, datatype)
			coremin, coremax = self.getCoreRange(coreinfo)
			coreinfo.minDepth = coremin
			coreinfo.maxDepth = coremax
			if datatype is not None: # override file datatype
				coreinfo.type = datatype
				
			comment = "" if pandas.isnull(row["Comment"]) else str(row["Comment"])
			intervalTop = previousAffBot if previousSpliceType is not None and previousSpliceType.upper() == "TIE" and previousAffBot is not None else appliedTop
			previousSpliceType = row["Splice Type"]
			previousAffBot = appliedBot
			
			# skip invalid intervals?
			if intervalTop == previousAffBot:
				print "{}: top ({}) == bot ({}), interval has length zero, skipping".format(coreinfo.getHoleCoreStr(), intervalTop, previousAffBot)
				continue
			
			print "creating interval for {}: {} - {}".format(coreinfo.getHoleCoreStr(), intervalTop, previousAffBot)
			# 1/19/2016 brgtodo: catch ValueError (for invalid interval) and skip instead of failing?
			spliceInterval = splice.SpliceInterval(coreinfo, intervalTop, previousAffBot, comment)
			destSplice.addInterval(spliceInterval) # add to ints - should already be sorted properly
		
		#self._onAdd(dirty=False) # notify listeners that intervals have been added

	def loadSplice(self, filepath, datatype=None):
		self.clear()
		self.load(filepath, self.splice, datatype)
	
	def loadAlternateSplice(self, filepath, datatype):
		self.altSplice.clear()
		self.load(filepath, self.altSplice, datatype)
		
	def exportData(self, filepath, fileprefix, datatype, siteexp):
		#print "exportData: {}, prefix = {}, datatype = {}".format(filepath, fileprefix, datatype)
		exportRows = []
		secsumm = self.parent.sectionSummary
		for si in self.getIntervals():
			pts = [pt for pt in si.coreinfo.coredata if pt[0] >= si.getTop() and pt[0] <= si.getBot()]
			
			# brgtodo 12/29/2105: const '1' assumes same coretype in core, which I'm 99% sure is correct
			coreType = secsumm.getSectionCoreType(si.coreinfo.leg, si.coreinfo.hole, si.coreinfo.holeCore, '1')
			affineOffset = round(self.parent.Window.findCoreAffineOffset(si.coreinfo.hole, si.coreinfo.holeCore), 3)
			for p in pts:
				mbsf = p[0] - affineOffset
				section = secsumm.getSectionAtDepth(si.coreinfo.leg, si.coreinfo.hole, si.coreinfo.holeCore, mbsf)
				#print "seeking section at depth {}: result = {}".format(mbsf, section)
				if section is not None:
					secTop = secsumm.getSectionTop(si.coreinfo.leg, si.coreinfo.hole, si.coreinfo.holeCore, section)
					topOffset = round((mbsf - secTop) * 100, 2)
					botOffset = topOffset
					rawDepth = round(p[0] - affineOffset, 4)
					row = pandas.Series({'Exp':si.coreinfo.site, 'Site':si.coreinfo.leg, 'Hole':si.coreinfo.hole,
									'Core':si.coreinfo.holeCore, 'CoreType':coreType, 'Section':section, 'TopOffset':topOffset,
									'BottomOffset':botOffset, 'Depth':round(p[0], 4), 'Data':p[1], 'RunNo':'-', 'RawDepth':rawDepth, 'Offset':affineOffset})
					exportRows.append(row)
				else:
					print "Couldn't find section in {}{} at depth {}, skipping".format(si.coreinfo.hole, si.coreinfo.holeCore, mbsf)
		if len(exportRows) > 0:
			df = pandas.DataFrame(columns=tabularImport.CoreExportFormat.req)
			df = df.append(exportRows, ignore_index=True)
			#print "{}".format(df)
			exportPath = filepath + '/' + fileprefix + '_' + siteexp + '-' + datatype + '.csv'
			tabularImport.writeToFile(df, exportPath)

	# given a Splice Interval Table row from pandas.DataFrame, return core info,
	# applied affine shift, unshifed depths and shifted depths (both with file and applied affine) 
	def getRowDepths(self, row, datatype=None):
		hole = row["Hole"]
		core = str(row["Core"])
		if datatype is None:
			datatype = row["Data Used"]
			# older SIT tables may not have Data Used values...grab first available type
			# 3/19/2019: I believe the block below will always fail while Loading because
			# findCoreInfoByHoleCore() is checking DrawData["CoreInfo"], which will be empty
			# because we haven't drawn anything yet! It and other related methods should be
			# searching HoleData instead. Thankfully this is only an issue with old SIT tables
			# without a 'Data Used' column, which we're unlikely to encounter at this point.
			# But it also prevents us from substituting an available datatype if the 'Data Used'
			# type is unavailable.
			if datatype is None:
				ci = self.parent.Window.findCoreInfoByHoleCore(hole, core)
				datatype = ci.type
		if datatype == "NaturalGamma":
			datatype = "Natural Gamma"
		coreinfo = self.parent.Window.findCoreInfoByHoleCoreType_v2(hole, core, datatype)
		if coreinfo is None:
			print "Couldn't find hole {} core {} of type {}".format(hole, core, datatype)
			coreinfo = self.parent.Window.findCoreInfoByHoleCore(hole, core)
			if coreinfo is None:
				print "Couldn't even find hole {} core {}".format(hole, core)
				return
		
		# affine shift from currently-loaded affine table	
		affineOffset = self.parent.Window.findCoreAffineOffset(coreinfo.hole, coreinfo.holeCore)
		
		# file CSF and CCSF depths - ensure no sub-mm decimals
		top = round(row["Top Depth CSF-A"], 3)
		bot = round(row["Bottom Depth CSF-A"], 3)
		fileTop = round(row["Top Depth CCSF-A"], 3)
		fileBot = round(row["Bottom Depth CCSF-A"], 3)
		
		# CCSF depths with current affine applied
		appliedTop = round(top + affineOffset, 3)
		appliedBot = round(bot + affineOffset, 3)
		
		return coreinfo, affineOffset, top, bot, fileTop, fileBot, appliedTop, appliedBot
	
	# confirm applied affine shift matches file's CSF and CCSF difference
	def affineMatches(self, appliedVal, fileVal, coreinfo):
		TOLERANCE = 0.01
		diff = abs(fileVal - appliedVal)
		matches = diff <= TOLERANCE
		if not matches:
			msg = "Core {}: Applied affine shift ({}) does not match shift in Splice Table ({}), can't load splice.".format(coreinfo.getHoleCoreStr(), appliedVal.__repr__(), fileVal.__repr__())
			self._setErrorMsg(msg)
		return matches

	# do currently-applied affine shifts match corresponding Splice Interval file's shifts?
	# filepath: path to splice interval table to check against affine shifts
	def canApplyAffine(self, filepath):
		canApply = True
		df = tabularImport.readFile(filepath)
		for index, row in df.iterrows(): # itertuples() is faster if needed
			coreinfo, affineOffset, top, bot, fileTop, fileBot, appliedTop, appliedBot = self.getRowDepths(row)
			if not self.affineMatches(appliedTop, fileTop, coreinfo) or not self.affineMatches(appliedBot, fileBot, coreinfo):
				canApply = False
				break
		return canApply

	# Check whether all the datatype-core combinations required by a splice are
	# currently loaded. Returns a (boolean, dict) tuple. If the first element is
	# True, all required datatype-cores are loaded and the dict will be empty.
	# If False, required datatype-cores are missing, and are listed in the dict
	# with key=datatype name : value=a list of strings indicating missing cores
	# for that datatype.
	# splicePath: path to splice file to check against loaded cores
	def requiredDataIsLoaded(self, splicePath):
		missingData = {}
		df = tabularImport.readFile(splicePath)
		for index, row in df.iterrows():
			hole, core, datatype = row['Hole'], str(row['Core']), row['Data Used']
			if datatype == "NaturalGamma":
				datatype = "Natural Gamma"
			coreinfo = self.parent.Window.findCoreInfoByHoleCoreType_v2(hole, core, datatype)
			if coreinfo is None:
				missingCoreStr = "{}{}".format(str(hole), str(core))
				if datatype in missingData:
					missingData[datatype].append(missingCoreStr)
				else:
					missingData[datatype] = [missingCoreStr]
		return len(missingData) == 0, missingData

	# Return list of splice intervals matching specified hole and core.
	def findIntervals(self, hole, core):
		matches = [i for i in self.splice.ints if i.coreinfo.hole == hole and i.coreinfo.holeCore == core]
		return matches


class CorrelatorApp(wx.App):
	def __init__(self, new_version, cfg=myPath+"default.cfg"):
		self.cfgfile = cfg
		self.new = new_version
		self.showSplash = True
		wx.App.__init__(self,0)
		
	def OnInit(self):
		user = getpass.getuser()
		if self.showSplash:
			splash = dialog.SplashScreen(None, -1, user, vers.ShortVersion)
			splash.Centre()
			ret =  splash.ShowModal()
			user = splash.user
			splash.Destroy()
			if ret == wx.ID_CANCEL:
				if global_logFile != None:
					global_logFile.close()
					if sys.platform == 'win32':
						workingdir = os.getcwd()
						os.chdir(myPath)
						os.system('del ' + global_logName)
						os.chdir(workingdir)
					else:
						filename = myPath + global_logName
						os.system('rm \"'+ filename + '\"')
				return False

		winx = 460 
		winy = 600

		problemFlag = False 
		checklogFile = open(myTempPath + "success.txt", "r")
		line = checklogFile.readline()
		if len(line) == 0: 
			problemFlag = True
		elif line[0:5] == "start":
			problemFlag = True
		else:
			line = checklogFile.readline()
			winx = int(line)
			line = checklogFile.readline()
			winy = int(line)
			if (winx < 0) and (winy < 0):
				winx = 460
				winy = 600 
		checklogFile.close()

		self.frame = MainFrame((winx, winy), user)
		self.SetTopWindow(self.frame)

		# This is for version difference
		#if self.new == True:
		#	self.frame.IMPORTRepository()

		if problemFlag == True:
			defaultTempFile = open("./tmp/default.cfg", "r+")
			#print "[DEBUG] Configuration file is regenerated."
			line = defaultTempFile.read()
			defaultTempFile.close()
			defaultFile = open("default.cfg", "w+")
			defaultFile.write(line)
			defaultFile.close()

		startlogFile = open(myTempPath + "success.txt", "w+")
		startlogFile.write("start\n")
		startlogFile.close()

		self.frame.NewDrawing(self.cfgfile, self.new)
		self.frame.agePanel.OnAgeViewAdjust(None)
		self.frame.agePanel.OnDepthViewAdjust(None)
		self.frame.optPanel.OnDepthViewAdjust(None)

		# wait until now so self.frame.dataFrame exists
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(self.frame.dataFrame, 1, wx.EXPAND)
		sizer.Add(self.frame.Window, 1, wx.EXPAND)
		self.frame.SetSizer(sizer)

		self.frame.Show(True)
		self.frame.Window.Hide()
		self.frame.dataFrame.Show(True)
		self.frame.topMenu.Show(True)

		# ensure all data is cleared and all data-dependent Display controls are disabled
		self.frame.OnNewData(None)

		self.SetExitOnFrameDelete(False)

		return True


def reportUnhandledException(exc_type, exc_value, exc_traceback):
	err_msg = 'Correlator encountered an error:\n'
	err_msg += '\n'.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
	err_msg += 'Unhandled Exception'
	print(err_msg)
	dlg = wx.MessageDialog(None, err_msg, 'Exception', wx.OK | wx.ICON_ERROR)
	dlg.ShowModal()
	dlg.Destroy()

# override default unhandled exception handling - report error via GUI
sys.excepthook = reportUnhandledException

if __name__ == "__main__":

	new = False

	tempstamp = str(datetime.today())
	last = tempstamp.find(" ", 0)
	stamp = tempstamp[0:last] + "-"  
	
	# create ~/.correlator dir if none exists
	configDir = os.path.join(User_Dir, ".correlator")
	if not os.access(configDir, os.F_OK):
		os.mkdir(configDir)

	# check for preferences file, if none create default
	prefsPath = os.path.join(configDir, "prefs.pk")
	Prefs = prefs.Prefs(prefsPath)
	if not Prefs.contains("inferSectionSummary"):
		Prefs.set("inferSectionSummary", False)
	if not Prefs.contains("checkForSpliceCores"):
		Prefs.set("checkForSpliceCores", True)

	if platform_name[0] == "Windows":
		if os.access(User_Dir  + "\\Correlator\\", os.F_OK) == False:
			os.mkdir(User_Dir  + "\\Correlator\\")
			new = True
	else:
		if os.access(User_Dir  + "/Documents/Correlator/", os.F_OK) == False:
			os.mkdir(User_Dir  + "/Documents/Correlator/")
			new = True

	if os.access(myPath, os.F_OK) == False:
		os.mkdir(myPath)
		if new == True:
			new = False
		else: 
			new = True 

	if os.access(myPath+"tmp", os.F_OK) == False:
		os.mkdir(myPath + "tmp")
		cmd = "cp ./tmp/*.* " + myPath + "tmp"
		if platform_name[0] == "Windows":
			cmd = "copy tmp\\*.* \"" + myTempPath + "\""
		os.system(cmd)
		cmd = "cp " + myTempPath + "/tmp/default.cfg " + myPath
		if platform_name[0] == "Windows":
			cmd = "copy " + myTempPath + "\\tmp\\default.cfg \"" + myPath + "\""

		#print "[DEBUG] " + cmd
		os.system(cmd)

	if platform_name[0] == "Windows":
		myTempPath = myPath + "tmp\\"
	else:
		myTempPath = myPath + "tmp/"
	
	if os.access(myTempPath+"success.txt", os.F_OK) == False:
		cmd = "cp ./tmp/*.* " + myTempPath
		if platform_name[0] == "Windows":
			cmd = "copy tmp\\*.* \"" + myTempPath + "\""
		os.system(cmd)

	if os.access(myPath + '/log/', os.F_OK) == False:
		os.mkdir(myPath + '/log/')

#	tempstamp = str(datetime.today())
#	last = tempstamp.find(" ", 0)
#	stamp = tempstamp[0:last] + "-"

	start = last+ 1 
	last = tempstamp.find(":", start)
	stamp += tempstamp[start:last] + "-"
	start = last+ 1 
	last = tempstamp.find(":", last+1)
	stamp += tempstamp[start:last]

	global_logName = "log/" + getpass.getuser() + "." + stamp + ".txt"
	if platform_name[0] == "Windows":
		global_logName= "log\\" + getpass.getuser() + "." + stamp + ".txt"

	global_logFile = open(myPath + global_logName, "a+")
	global_logFile.write("Start of Session:\n")
	s = "BY " + getpass.getuser()  + "\n"
	global_logFile.write(s)
	s = str(datetime.today()) + "\n\n"
	global_logFile.write(s)

	ret = py_correlator.initialize("../DATA/current-test")
	app = CorrelatorApp(new)
	app.MainLoop()
	win_size = app.frame.Width, app.frame.Height

	py_correlator.finalize()

	startlogFile = open(myPath + "/tmp/success.txt", "w+")
	startlogFile.write("close\n")
	s = str(win_size[0]) + "\n"
	startlogFile.write(s)
	s = str(win_size[1]) + "\n"
	startlogFile.write(s)
	startlogFile.close()
