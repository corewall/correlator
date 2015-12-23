#!python.exe
import site # brg 12/4/2013 unused
import platform
import os
import socket
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

import random, sys, re, time, ConfigParser, string
import getpass
from datetime import datetime

from importManager import py_correlator

import canvas
import dialog
import frames
import dbmanager
import version as vers
import model
import splice
import tabularImport

app = None 
User_Dir = os.path.expanduser("~")

myPath = User_Dir  + "/Documents/Correlator/" + vers.BaseVersion + "/"
if platform_name[0] == "Windows" :
	myPath =  User_Dir  + "\\Correlator\\" + vers.BaseVersion + "\\"
myTempPath = myPath
WIN_WIDTH = 800
WIN_HEIGHT = 600

global_logName = "" 
global_logFile = None 

def opj(path):
	"""Convert paths to the platform-specific separator"""
	return apply(os.path.join, tuple(path.split('/')))


class MainFrame(wx.Frame):
	def __init__(self, winsize, user):
		wx.Frame.__init__(self, None, -1, "Correlator " + vers.ShortVersion,
						 wx.Point(0,100), winsize)

		self.statusBar = self.CreateStatusBar()

		self.user = user
		self.Width = winsize[0]
		self.Height = winsize[1]
		#self.Width, self.Height = self.GetClientSizeTuple()
		self.scroll = 1 
		self.half = (self.Width / 2) - 32 
		# make the menu
		self.SetMenuBar( self.CreateMenu() )
		
		self.sectionSummary = None
		self.spliceManager = SpliceController(self) #splice.SpliceManager(self)

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
		self.loadedSite = None

		wx.EVT_CLOSE(self, self.OnHide)
		wx.EVT_IDLE(self, self.OnIDLE)

	def SetLoadedSite(self, siteData):
		if isinstance(siteData, model.SiteData):
			self.loadedSite = siteData

	def GetLoadedSite(self):
		return self.loadedSite

	def INIT_CHANGES(self):
		self.AffineChange = False 
		self.SpliceChange = False 
		self.EldChange = False 
		self.AgeChange = False 
		self.TimeChange = False 

	def OnIDLE(self, event):
		if app == None :
			return

		if app.IsActive() == True :
			if self.FOCUS == 0 : 
				if self.mitool.IsChecked() == True :
					self.topMenu.Show(True)
					self.topMenu.Iconize(False)
				self.FOCUS = 1

			if self.IsIconized():
				if self.IDLE == 0 :
					self.topMenu.Show(False)
					if platform_name[0] == "Windows" :	
						self.topMenu.Iconize(True)
					self.IDLE = 1
			else :
				if self.IDLE == 1 :
					if self.mitool.IsChecked():
						self.topMenu.Show(True)
					if platform_name[0] == "Windows" :	
						self.topMenu.Iconize(False)
					self.IDLE = 0 
		else :
			self.topMenu.Show(False)
			if platform_name[0] == "Windows" :	
				self.topMenu.Iconize(True)
			self.FOCUS = 0 

	def CheckAutoELD(self):
		if (self.autoPanel.selectedNo != -1) and (self.autoPanel.ApplyFlag == 0) :
			return False
		return True


	def UpdateSize(self, width, height):
		self.Width = width 
		self.Height = height 
		WIN_WIDTH = width
		WIN_HEIGHT = height


	def DoesFineTune(self) :
		if self.Window.SpliceData != [] :
			if self.AffineChange == True :
				return  True
		return False

	def CreateMenu(self):
		self.statusBar.SetStatusText('Done')

		# File
		menuFile = wx.Menu()
		menuBar = wx.MenuBar()

		miFileNew = menuFile.Append(-1, "&New\tCtrl-N", "New data")
		self.Bind(wx.EVT_MENU, self.OnNewData, miFileNew)

		menuFile.AppendSeparator()

		#self.miFileDB = menuFile.Append(-1, "&Access Database\tCtrl-E", "Access database")

		#self.miCleanFiles = menuFile.Append(-1, "Formatting Data Files", "Formatting data file")
		#self.Bind(wx.EVT_MENU, self.OnFormatData, self.miCleanFiles)

		self.miPath = menuFile.Append(-1, "Data Repository Path", "Data repository path")
		self.Bind(wx.EVT_MENU, self.OnPATH, self.miPath)

		self.miImport = menuFile.Append(-1, "Import Data Repository", "Import Data repository")
		self.Bind(wx.EVT_MENU, self.OnIMPORT_DATA, self.miImport)

		menuFile.AppendSeparator()

		self.miConnection = menuFile.Append(-1, "Connect to Corelyzer", "Connect to Corelyzer")
		self.Bind(wx.EVT_MENU, self.OnCONNECTION, self.miConnection)

		menuFile.AppendSeparator()

		self.miFileSave = menuFile.Append(-1, "Save", "Save changes")
		self.Bind(wx.EVT_MENU, self.OnSave, self.miFileSave)

		menuFile.AppendSeparator()

		self.miFileClear = menuFile.Append(-1, "Clear All Ties\tCtrl-C", "Clear all")
		self.Bind(wx.EVT_MENU, self.OnClearAllData, self.miFileClear)

		self.miFileClearco = menuFile.Append(-1, "Clear All Shifts", "Clear composite ties")
		self.Bind(wx.EVT_MENU, self.OnClearComposite, self.miFileClearco)

		self.miFileClearsp = menuFile.Append(-1, "Clear All Splice Ties", "Clear splice ties")
		self.Bind(wx.EVT_MENU, self.OnClearSpliceTie, self.miFileClearsp)

		self.miFileClearsa = menuFile.Append(-1, "Clear All Core-Log Ties", "Clear core-log ties")
		self.Bind(wx.EVT_MENU, self.OnClearSAGANTie, self.miFileClearsa)

		menuFile.AppendSeparator()

		miFileExit = menuFile.Append(wx.ID_EXIT, "&Exit\tCtrl-X", "Exit demo")
		self.Bind(wx.EVT_MENU, self.OnExitButton, miFileExit)
		menuBar.Append(menuFile, "&File")

		# View 
		menuView = wx.Menu()
		self.mitool = menuView.AppendCheckItem(-1, "Toolbar", "Toolbar")
		self.mitool.Check(True)
		self.Bind(wx.EVT_MENU, self.SHOWToolbar, self.mitool)

		menuView.AppendSeparator()
		self.miplot = menuView.AppendCheckItem(-1, "Discrete Points", "Discrete Points")
		self.Bind(wx.EVT_MENU, self.SETPlotMode, self.miplot)

		self.miptsizeup = menuView.Append(-1, "Point Size Up", "Point Size Up")
		self.Bind(wx.EVT_MENU, self.SetPT_SIZEUP, self.miptsizeup)
		
		self.miptsizeDown = menuView.Append(-1, "Point Size Down", "Point Size Down")
		self.Bind(wx.EVT_MENU, self.SetPT_SIZEDOWN, self.miptsizeDown)

		menuView.AppendSeparator()
		self.mitiesizeup = menuView.Append(-1, "Tie Point Size Up", "Tie Point Size Up")
		self.Bind(wx.EVT_MENU, self.SetTIE_SIZEUP, self.mitiesizeup)

		self.mitiesizeDown = menuView.Append(-1, "Tie Point Size Down", "Tie Point Size Down")
		self.Bind(wx.EVT_MENU, self.SetTIE_SIZEDOWN, self.mitiesizeDown)

		self.mitiewidthup = menuView.Append(-1, "Tie Line Thickness Up", "Tie Line Thickness Up")
		self.Bind(wx.EVT_MENU, self.SetTIE_WIDTHUP, self.mitiewidthup)
		self.mitiewidthDown = menuView.Append(-1, "Tie Line Thickness Down", "Tie Line Thickness Down")
		self.Bind(wx.EVT_MENU, self.SetTIE_WIDTHDOWN, self.mitiewidthDown)

		menuView.AppendSeparator()
		self.misecond = menuView.AppendCheckItem(-1, "Splice/Log Window", "Splice/Log window")
		self.misecond.Check(True)
		self.Bind(wx.EVT_MENU, self.SHOWSplice, self.misecond)

		menuView.AppendSeparator()
		self.miscroll = menuView.AppendCheckItem(-1, "Second Scroll", "Second scroll")
		self.miscroll.Check(False)
		self.Bind(wx.EVT_MENU, self.SHOWScroll, self.miscroll)

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
		self.miScrollbigger = menuView.Append(-1, "Bigger Scroll", "Bigger Scroll")
		self.Bind(wx.EVT_MENU, self.UseWideScrollbars, self.miScrollbigger)
		self.miScrollnormal = menuView.Append(-1, "Smaller Scroll", "Smaller Scroll")
		self.Bind(wx.EVT_MENU, self.UseNarrowScrollbars, self.miScrollnormal)
		
		menuBar.Append(menuView, "&View")

		# Help 
		menuHelp = wx.Menu()
		self.miAbout = menuHelp.Append(wx.ID_ABOUT, "About Correlator\tF1", "")
		self.Bind(wx.EVT_MENU, self.OnAbout, self.miAbout)
		menuBar.Append(menuHelp, "&Help")

		self.OnDisableMenu(0, False)

		# bind keystrokes to the frame
		# self.Bind(wx.EVT_KEY_DOWN, self.OnKeyEvent)
		return menuBar
		

	def OnIMPORT_DATA(self, event):
		opendlg = wx.DirDialog(self, "Select Repository Directory to Import", myPath)
		ret = opendlg.ShowModal()
		path = opendlg.GetPath()
		opendlg.Destroy()
		updated = False
		if ret == wx.ID_OK :
			# check....
			if os.access(path + '/datalist.db', os.F_OK) == False :
				self.OnShowMessage("Error", "It doesn't have datalist.db", 1)
				return
			datalist = []
			dblist_f = open(self.DBPath + 'db/datalist.db', 'r+')
			for line in dblist_f :
				if len(line) > 0 :
					token = line.split()
					if len(token) == 0 :
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
			for line in importdb_f :
				if len(line) > 0 :
					token = line.split()
					if len(token) == 0 :
						continue
					first_token = token[0]
					if first_token.find("-", 0) >= 0 :
						found_flag = False
						for dataitem in datalist : 
							if first_token == dataitem :
								found_flag = True 
								break
						if found_flag == True :
							os.chdir(workingdir)
							self.OnShowMessage("Error", "There is already " + first_token, 1)
							os.chdir(path)
						else :
							dblist_f.write("\n"+ first_token+"\n")
							cmd = "cp -rf " +  first_token + " " + self.DBPath + "db/"
							if sys.platform == 'win32' :
								os.chdir(self.DBPath+ "db")
								if os.access(first_token, os.F_OK) == False :
									os.mkdir(first_token)
								os.chdir(path + "\\" + first_token)
								cmd = "copy * \"" + self.DBPath + "db\\" + first_token + "\""
								#print "[DEBUG] " + cmd
								os.system(cmd)								
								os.chdir(path)
							else :
								#print "[DEBUG] " + cmd
								os.system(cmd)
							updated = True 
							if self.logFileptr != None :
								global_logFile.write("Add Data Repository : " + first_token + "\n")
					else :
						single_flag = True 
						break
			if single_flag == True :
				first_token = ""
				for line in importdb_f :
					if len(line) > 0 :
						token = line.split()
						if len(token) == 0 :
							continue
						if token[0] == "file:" :
							filename = token[1]
							start = 0
							last = filename.find("-", start)
							start = last + 1
							last = filename.find("-", start)
							first_token = filename[0:last]
							break
				found_flag = False
				for dataitem in datalist : 
					if first_token == dataitem :
						found_flag = True 
						break
				if found_flag == True :
					os.chdir(workingdir)
					self.OnShowMessage("Error", "There is already " + first_token, 1)
					os.chdir(path)
				else :
					dblist_f.write("\n"+ first_token+"\n")
					os.chdir(self.DBPath+ "db")
					if os.access(first_token, os.F_OK) == False :
						os.mkdir(first_token)
					os.chdir(path)
					cmd = "cp -rf * " + self.DBPath + "db/" + first_token
					if sys.platform == 'win32' :
						cmd = "copy * \"" + self.DBPath + "db\\" + first_token + "\""
						#print "[DEBUG] " + cmd
						os.system(cmd)
					else :
						#print "[DEBUG] " + cmd
						os.system(cmd)
					updated = True 
					if self.logFileptr != None :
						global_logFile.write("Add Data Repository : " + first_token + "\n")
			os.chdir(workingdir)
			importdb_f.close()
			dblist_f.close()

			if updated == True :
				self.dataFrame.dataPanel.ClearGrid()
				self.dataFrame.tree.DeleteAllItems()
				self.dataFrame.root = self.dataFrame.tree.AddRoot("Root")
				self.dataFrame.repCount = 0
				self.dataFrame.OnLOADCONFIG()
				self.OnShowMessage("Information", "Successfully Imported", 1)


	def IMPORTRepository(self):
		while True :
			opendlg = wx.DirDialog(self, "Select Previous Repository Directory", myPath)
			ret = opendlg.ShowModal()
			path = opendlg.GetPath()
			opendlg.Destroy()
			if ret == wx.ID_OK :
				if os.access(path + '/default.cfg', os.F_OK) == False :
					self.OnShowMessage("Error", "It's not Repository Root", 1)
					continue
				if os.access(path + '/db/datalist.db', os.F_OK) == False :
					self.OnShowMessage("Error", "It's not Repository Root", 1)
					continue

				workingdir = os.getcwd()
				os.chdir(path)
				cmd = "cp -rf * " + myPath
				if sys.platform == 'win32' :
					cmd = "copy * \"" + myPath + "\""
				os.system(cmd)
				os.chdir(workingdir)

				#cmd = "rm -rf  " + path
				#if sys.platform == 'win32' :
				#	cmd = "rd /s /q " + path
				#os.system(cmd)
				break
			else :
				break

	def SHOWToolbar(self, event):
		if self.mitool.IsChecked() == False :
			self.optPanel.tool.SetValue(False)
			self.topMenu.Show(False)
		else :
			self.optPanel.tool.SetValue(True)
			self.topMenu.Show(True)

	def SETPlotMode(self, event):
		if self.miplot.IsChecked() == False :
			self.Window.DiscretePlotMode = 0 
		else :
			self.Window.DiscretePlotMode = 1
		self.Window.UpdateDrawing()
		

	def SHOWSplice(self, event):
		if self.misecond.IsChecked() == True :
			self.OnActivateWindow(1)
		else :
			self.OnActivateWindow(0)

	def SHOWScroll(self, event):
		if self.miscroll.IsChecked() == True :
			self.SetSecondScroll(1)
		else :
			self.SetSecondScroll(0)

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
		self.Window.DiscretetSize = self.Window.DiscretetSize + 1
		self.Window.UpdateDrawing()

	def SetPT_SIZEDOWN(self, evt):
		self.Window.DiscretetSize = self.Window.DiscretetSize - 1
		if self.Window.DiscretetSize < 1 :
			self.Window.DiscretetSize = 1
		self.Window.UpdateDrawing()

	def SetTIE_SIZEUP(self, evt):
		self.Window.tieDotSize = self.Window.tieDotSize + 2 
		self.Window.UpdateDrawing()

	def SetTIE_SIZEDOWN(self, evt):
		self.Window.tieDotSize = self.Window.tieDotSize - 2 
		if self.Window.tieDotSize < 8 :
			self.Window.tieDotSize = 8 
		self.Window.UpdateDrawing()

	def SetTIE_WIDTHUP(self, evt):
		self.Window.tieline_width +=  1
		if self.Window.tieline_width > 3 :
			self.Window.tieline_width = 3
		self.Window.UpdateDrawing()

	def SetTIE_WIDTHDOWN(self, evt):
		self.Window.tieline_width -=  1
		if self.Window.tieline_width < 1 :
			self.Window.tieline_width = 1 
		self.Window.UpdateDrawing()

	def SETTextSizeUp(self, evt):
		size = self.Window.font2.GetPointSize() + 1
		self.Window.font2.SetPointSize(size)
		
		self.Window.startDepth = self.Window.startDepth + 5
		self.Window.startAgeDepth = self.Window.startAgeDepth + 5
		self.Window.UpdateDrawing()
		
	def SETTextSizeDown(self, evt):
		size = self.Window.font2.GetPointSize() - 1
		self.Window.font2.SetPointSize(size)
		
		self.Window.startDepth = self.Window.startDepth - 5
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
				
	def OnDisableMenu(self, type, enable):
		if type == 1 or type == 0 : 
			self.miFileClear.Enable(enable)
			self.miFileClearco.Enable(enable)
			self.miFileClearsp.Enable(enable)
			self.miFileClearsa.Enable(enable)

	# update global Evaluation Graph parameters
	def OnEvalSetup(self, depthStep, winLength, leadLag):
		self.depthStep = depthStep
		self.winLength = winLength
		self.leadLag = leadLag
		py_correlator.setEvalGraph(self.depthStep, self.winLength, self.leadLag)

	def OnAdjustCore(self, opt, type, offset, comment):
		self.Window.OnAdjustCore(opt, type, offset, comment)

	def OnUndoCore(self, opt):
		self.Window.OnUndoCore(opt)

	def OnUpdateDepth(self, depth):
		self.compositePanel.OnUpdateDepth(depth)
		
	# Preferences "Depth Ruler Scale" min/max changed
	def OnUpdateDepthRange(self, min, max, updateScroll=True):
		self.Window.rulerStartDepth = min
		self.Window.SPrulerStartDepth = min
		x = (self.Window.Height - self.Window.startDepth) * self.Window.gap
		self.Window.length = x / (max - min) * 1.0

		if updateScroll:
			self.Window.UpdateScroll(1)
			self.Window.UpdateScroll(2)
		self.Window.UpdateDrawing()
		self.Window.UpdateDrawing() # brgtodo 9/6/2014 core area doesn't update completely without, why?
		
	# update start depth of graph area
	def OnUpdateStartDepth(self, startDepth, updateScroll=True):
		self.Window.rulerStartDepth = startDepth
		self.Window.SPrulerStartDepth = startDepth
		# no need to mess with self.Window.length, keep it as is
		if updateScroll:
			self.Window.UpdateScroll(1)
			self.Window.UpdateScroll(2)
		self.Window.UpdateDrawing()
		self.Window.UpdateDrawing() # brgtodo 9/6/2014 core area doesn't update completely without, why?

	def OnUpdateDepthStep(self):
		self.depthStep = py_correlator.getAveDepStep()
		self.minDepthStep = int(10000.0 * float(self.depthStep)) / 10000.0;

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
		if self.showCompositePanel == 1 :
			self.compositePanel.OnUpdateDrawing()
		elif self.showSplicePanel == 1 : 
			self.spliceIntervalPanel.OnUpdate()
		elif self.showELDPanel == 1 :
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
		for i in range(numleadLag) : 
			last = coef.find(",", start)
			if start == last :
				break;
			depth = float(coef[start:last])
			start = last +1
			last = coef.find(",", start)
			if start == last :
				break;
			value = float(coef[start:last])

			if max < value :
				max = value
				best = depth 
			l.append( (depth, value) ) 
			start = last +1
			if start >= len_max :
				break

		bestdata = [ (best, -0.05),( best, 0.05) ]

		if len(l) <= 1:
			l = [ (-1.0, -1.0), (0, 0), (1.0, 1.0) ]

		if self.showCompositePanel == 1 :
			self.compositePanel.OnAddFirstData(l, bestdata, best)
		elif self.showSplicePanel == 1 : 
			self.spliceIntervalPanel.OnAddFirstData(l, bestdata, best)
		elif self.showELDPanel == 1 :
			self.eldPanel.OnAddFirstData(l, bestdata, best)


	def OnAddGraph(self, coef, depth1, depth2):
		start = 0
		last = 0
		l = []
		startx = self.leadLag * -1
		numleadLag = int(self.leadLag / self.depthStep) * 2 +1
		win_length = depth2 - self.winLength

		max = len(coef) -1
		for i in range(numleadLag) : 
			last = coef.find(",", start)
			if start == last :
				break;
			depth = float(coef[start:last])
			start = last +1
			last = coef.find(",", start)
			if start == last :
				break;
			value = float(coef[start:last])
			l.append( (depth, value) ) 
			start = last +1
			if start >= max :
				break

		if self.showCompositePanel == 1 :
			self.compositePanel.OnAddData(l)
		elif self.showSplicePanel == 1 : 
			self.spliceIntervalPanel.OnAddData(l)
		elif self.showELDPanel == 1 :
			self.eldPanel.OnAddData(l)

	def OnHide(self, event):
		self.SavePreferences()

		WIN_WIDTH = self.Width 
		WIN_HEIGHT = self.Height 
		if self.logFileptr != None :
			s = "\n" + str(datetime.today()) + "\n"
			self.logFileptr.write(s)
			self.logFileptr.write("Close of Session.\n\n")
			self.logFileptr.close()
			self.logFileptr = None

		app.ExitMainLoop()

	def OnExitButton(self, event):
		if self.client != None :
			if self.Window.HoleData != [] : 
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

		if self.CurrentDir != '' and self.CHECK_CHANGES():
			ret = self.OnShowMessage("About", "Do you want to save changes?", 2)
			if ret == wx.ID_OK :
				self.topMenu.OnSAVE(event)

				self.AffineChange = False 
				self.SpliceChange = False 
				self.EldChange = False 
				self.AgeChange = False 
				self.TimeChange = False 

		ret = self.OnShowMessage("About", "Do you want to Exit?", 2)
		if ret == wx.ID_CANCEL :
			return

		self.SavePreferences()
		if self.logFileptr != None :
			s = "\n" + str(datetime.today()) + "\n"
			self.logFileptr.write(s)
			self.logFileptr.write("Close of Session.\n\n")
			self.logFileptr.close()
			self.logFileptr = None

		WIN_WIDTH = self.Width 
		WIN_HEIGHT = self.Height 

		self.Window.Close(True)
		self.dataFrame.Close(True)
		self.topMenu.Close(True)

		self.Close(True)

		app.ExitMainLoop()


	def CHECK_CHANGES(self):
		spliceChange = self.spliceManager.isDirty()
		return self.AffineChange or spliceChange or self.EldChange or self.AgeChange or self.TimeChange

	def OnActivateWindow(self, event):
		if self.Window.spliceWindowOn == 1 :
			self.Window.isSecondScrollBackup = self.Window.isSecondScroll 
			self.Window.isSecondScroll = 0
			self.Window.spliceWindowOn = 0
			self.Window.splicerBackX = self.Window.splicerX
			self.Window.splicerX = self.Window.Width + 45 
			self.optPanel.opt1.SetValue(False)
			self.optPanel.opt2.Enable(False)
		else :
			self.Window.isSecondScroll = self.Window.isSecondScrollBackup 
			self.Window.spliceWindowOn = 1 
			self.Window.splicerX = self.Window.splicerBackX
			self.optPanel.opt1.SetValue(True)
			self.optPanel.opt2.Enable(True)
		self.Window.UpdateDrawing()

	def SetSecondScroll(self, event):
		if self.Window.isSecondScroll == 1 : 
			self.Window.isSecondScroll = 0 
			self.optPanel.opt2.SetValue(False)
		else :
			self.Window.isSecondScroll = 1 
			self.optPanel.opt2.SetValue(True)


	def RebuildComboBox(self, comboBox, typeNames, hasSpliceData, hasLogData):
		prevSelected = comboBox.GetCurrentSelection()
		if prevSelected == -1 :
			prevSelected = 0

		comboBox.Clear()
		comboBox.Append("All Holes")
		for type in typeNames:
			typeStr = "All " + type
			if comboBox.FindString(typeStr) == wx.NOT_FOUND:
				comboBox.Append(typeStr)

		if hasSpliceData == True:
			comboBox.Append("Spliced Records")
		if hasLogData == True:
			comboBox.Append("Log")

		comboBox.SetSelection(prevSelected)
		if platform_name[0] == "Windows":
			comboBox.SetValue(comboBox.GetString(prevSelected))

		return prevSelected


	def RefreshTypeComboBoxes(self):
		if self.filterPanel.locked == False:
			holeData = self.Window.HoleData
			hasSpliceData = (self.Window.SpliceData != [])
			hasLogData = (self.Window.LogData != [])

			# extract type names
			typeNames = []
			if len(holeData) > 0:
				for holeIdx in range(len(holeData)):
					typeNames.append(holeData[holeIdx][0][0][2])

			self.filterPanel.prevSelected = self.RebuildComboBox(self.filterPanel.all, typeNames, hasSpliceData, hasLogData)
			self.optPanel.prevSelected = self.RebuildComboBox(self.optPanel.all, typeNames, hasSpliceData, hasLogData)


	def UpdateSECTION(self):
		self.Window.SectionData = []
		ret = py_correlator.getData(18)
		if ret != "" :
			self.ParseSectionSend(ret)

	def UpdateCORE(self):
		self.Window.HoleData = []
		ret = py_correlator.getData(0)
		if ret != "" :
			self.LOCK = 0
			self.PrevDataType = ""
			self.ParseData(ret, self.Window.HoleData)
			self.UpdateMinMax()
			self.LOCK = 1

			self.RefreshTypeComboBoxes()

	def UpdateSMOOTH_CORE(self):
		self.Window.SmoothData = []
		ret = py_correlator.getData(1)
		if ret != "" :
			self.filterPanel.OnLock()
			self.ParseData(ret, self.Window.SmoothData)
			self.filterPanel.OnRelease()


	def InitSPLICE(self):
		ret = py_correlator.getData(2)
		if ret != "" :
			self.ParseSpliceData(ret, False)


	def UpdateSPLICE(self, locked):
		self.Window.SpliceData = []
		ret = ""
		if locked == True : 
			ret = py_correlator.getData(15)
		else :
			ret = py_correlator.getData(3)
		if ret != "" :
			self.filterPanel.OnLock()
			self.ParseData(ret, self.Window.SpliceData)
			self.filterPanel.OnRelease()


	def UpdateSMOOTH_SPLICE(self, locked):
		self.Window.SpliceSmoothData = []
		ret =""
		if locked == True : 
			ret = py_correlator.getData(16)
		else :
			ret = py_correlator.getData(4)
		if ret != "" :
			self.filterPanel.OnLock()	
			self.ParseData(ret, self.Window.SpliceSmoothData)
			self.filterPanel.OnRelease()


	def UpdateLOGSPLICE(self, locked):
		self.Window.LogSpliceData = []
		if self.Window.isLogMode == 1 :
			ret =""
			if locked == True : 
				ret = py_correlator.getData(14)
			else :
				ret = py_correlator.getData(8)
			if ret != "" :
				self.filterPanel.OnLock()
				self.ParseData(ret, self.Window.LogSpliceData)
				self.filterPanel.OnRelease()


	def UpdateSMOOTH_LOGSPLICE(self, locked):
		#if self.Window.isLogMode == 1 and len(self.Window.SpliceData) > 0 :
		#	locked = True
		self.Window.LogSpliceSmoothData = []
		ret = ""
		if locked == True : 
			ret = py_correlator.getData(17)
		else :
			ret = py_correlator.getData(10)
		if ret != "" :
			self.filterPanel.OnLock()	
			self.ParseData(ret, self.Window.LogSpliceSmoothData)
			self.filterPanel.OnRelease()
		else :
			ret = py_correlator.getData(4)
			if ret != "" :
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
		#self.UpdateSMOOTH_SPLICE(False)
		self.UpdateShiftTie()

		# splice
		# UpdateStratData
		self.Window.UpdateDrawing()
		return

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

	def OnShowMessage(self, type, msg, numButton): 
		#dlg = dialog.MessageDialog(None, type, msg, numButton)
		dlg = dialog.MessageDialog(self.topMenu, type, msg, numButton)
		dlg.Centre(wx.CENTER_ON_SCREEN)
		ret = dlg.ShowModal()
		dlg.Destroy()
		return ret

	def AddTieInfo(self, info, depth):
		self.eldPanel.AddTieInfo(info, depth)

	def UpdateTieInfo(self, info, depth, tieNo):
		self.eldPanel.UpdateTieInfo(info, depth, tieNo)

	def ClearSaganTie(self, tieNo):
		if tieNo == -1 :
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
		if ret == wx.ID_OK :
			py_correlator.openAttributeFile(path, 0)
			s = "Affine Table: " + path + "\n\n"
			self.logFileptr.write(s)
			self.Window.AdjustDepthCore = []
			#if self.showReportPanel == 1 :
			#	self.OnUpdateReport() 
			self.UpdateData()

	def OnSaveAffineData(self, event):
		opendlg = wx.FileDialog(self, "Save AFFINE DATA file", self.Directory, "",wildcard = "Affine Table (*.affine.table)|*.affine.table|XML files(*.xml)|*.xml" , style =wx.SAVE)
		ret = opendlg.ShowModal()
		path = opendlg.GetPath()
		filterindex = opendlg.GetFilterIndex()
		if filterindex == 0 :
			index = path.find(".affine.table", 0)
			if index == -1 :
				path = path + ".affine.table"
		elif filterindex == 1 :
			index = path.find(".xml", 0)
			if index == -1 :
				path = path + ".xml"

		opendlg.Destroy()
		if ret == wx.ID_OK :
			py_correlator.saveAttributeFile(path, 1)

	def OnCONNECTION(self, event):
		if self.client is None :
			#HOST = '127.0.0.1'
			HOST = 'localhost'
			PORT = 17799
			for res in socket.getaddrinfo(HOST, PORT, socket.AF_INET, socket.SOCK_STREAM):
				af, socktype, proto, canonname, sa = res
				try :
					self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto)
				except socket.error, msg :
					self.client = None
					continue
				try : 
					self.client.connect(sa)
				except socket.error, msg :
					self.client.close()
					self.client = None
					continue
				break

			if self.client is None :
				#print "[DEBUG] Could not open socket to Corelyzer"
				self.OnShowMessage("Error", "Could not open socket to Corelyzer", 1)
				return False 
			else :
				#print "[DEBUG] Connected to Corelyzer"
				self.OnShowMessage("Information", "Connected to Corelyzer", 1)
				if self.Window.HoleData != [] :
					# TEST
					#self.client.send("load_section\t199\t1218\ta\t1\th\t1\t10\n")
					#self.client.send("load_section\t199\t1218\ta\t1\th\t2\t11\n")
					#self.client.send("load_section\t199\t1218\ta\t1\th\t3\t12\n")
					##########

					self.client.send("delete_all\n")

					# load_lims_table
					filename = self.dataFrame.OnGET_IMAGE_FILENAME()
					for name in filename :
						cmd = "load_lims_table\t" + name + "\n"
						self.client.send(cmd);
						#print "[DEBUG] send to Corelyzer : "  + str(cmd)

					# load_core JULIAN
					#ret = py_correlator.getData(18)
					#self.ParseSectionSend(ret)

					cmd = "affine_table\t" + self.CurrentDir + "tmp.affine.table\n" 
					#print "[DEBUG] send to Corelyzer : "  + str(cmd)
					self.client.send(cmd)

					#client.send("load_lims_table\t/Users/julian/Desktop/CRDownloader-data/1239/holeBC.dat\n");
					# self.client.send("show_depth_range\t"+str(self.Window.rulerStartDepth)+"\t"+str(self.Window.rulerEndDepth)+"\n")
					# self.client.send("jump_to_depth\t"+str(self.Window.rulerStartDepth)+"\n")
					#print "[DEBUG] " + str(self.Window.rulerStartDepth) + "\t" + str(self.Window.rulerEndDepth)
					_depth = (self.Window.rulerStartDepth + self.Window.rulerEndDepth) / 2.0
					self.client.send("show_depth_range\t" + str(_depth-0.7) + "\t" + str(_depth+0.7) + "\n")

				self.miConnection.SetText("Close Connection to Corelyzer");
				return True 
		else :
			if self.Window.HoleData != [] :
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
			self.miConnection.SetText("Connect to Corelyzer");
			print "[DEBUG] Close connection to Corelyzer"
			self.OnShowMessage("Information", "Close connection to Corelyzer", 1)
			return False 
			

	def OnPATH(self, event):
		opendlg = wx.DirDialog(self, "Select Directory", self.DBPath)
		ret = opendlg.ShowModal()
		path = opendlg.GetPath()
		opendlg.Destroy()
		if ret == wx.ID_OK :
  			path_len = len(path) -3
			dir_name = path[path_len:path_len+3]                      
			if sys.platform == 'win32' :
				if dir_name == "\\db" :
					path = path[0:path_len] 
			else :
				if dir_name == "/db" :
					path = path[0:path_len] 
			#print "[DEBUG]", path
			oldDBPath = self.DBPath 
			if platform_name[0] == "Windows" :
				self.DBPath = path  + "\\"
			else :
				self.DBPath = path  + "/"

			self.dataFrame.PathTxt.SetValue("Path : " + self.DBPath)
			prefile = self.DBPath + "db"
			if os.access(prefile, os.F_OK) == False :
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
			#print "[DEBUG] Data Repository path is changed : " + self.DBPath

			if os.access(path+"/tmp", os.F_OK) == False :
				os.mkdir(path + "/tmp")
				cmd = "cp ./tmp/*.* \"" + path + "/tmp\""
				if platform_name[0] == "Windows" :
					cmd = "copy tmp\\*.* \"" + path + "\\tmp\""
				os.system(cmd)
			else :
				if os.access(path+"/tmp/datatypelist.cfg", os.F_OK) == False :
					cmd = "cp ./tmp/*.* \"" + path + "/tmp\""
					if platform_name[0] == "Windows" :
						cmd = "copy tmp\\*.* \"" + path + "\\tmp\""
					os.system(cmd)
				
			#if os.access(path + "/log", os.F_OK) == False :
			if os.path.exists(path + "/log") == False :
				#os.mkdir(path + "/log")
				print "no log dir, trying to create..."
				os.makedirs(path + "/log")

			if self.logFileptr != None :
				self.logFileptr.close()
				self.logFileptr = open(path + "/" + global_logName, "a+")
				global_logFile = self.logFileptr

				global_logFile.write("Start of Session:\n")
				s = "BY " + getpass.getuser()  + "\n"
				global_logFile.write(s)
				s = str(datetime.today()) + "\n\n"
				global_logFile.write(s)
				global_logFile.write("Change Repository Directory Path : \n")
				global_logFile.write("from " + oldDBPath + " to " + path + "\n\n")

			self.dataFrame.OnLOADCONFIG()
				
	def UpdateLogData(self) :
		if len(self.Window.LogData) > 0 :	
			self.Window.LogData = []
			ret = py_correlator.getData(5)
			if ret != "" :
				self.filterPanel.OnLock()
				self.ParseData(ret, self.Window.LogData)
				self.Window.minRangeLog = self.min
				self.Window.maxRangeLog = self.max
				self.Window.coefRangeLog = self.Window.logHoleWidth / (self.max - self.min)
				#print "[DEBUG] Log data is updated"
				self.filterPanel.OnRelease()
				self.Window.UpdateDrawing()


	def UpdateSMOOTH_LogData(self) :
		if len(self.Window.LogData) > 0 :	
			self.Window.LogSMData = []
			ret = py_correlator.getData(19)
			if ret != "" :
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
		if ret != "" :
			self.filterPanel.OnLock()
			self.ParseData(ret, self.Window.LogData)
			self.filterPanel.OnRelease()
			self.Window.minRangeLog = self.min
			self.Window.maxRangeLog = self.max
			self.Window.coefRangeLog = self.Window.logHoleWidth / (self.max - self.min)
		self.Window.isLogShifted = flag 


	def UpdateStratData(self):
		ret = py_correlator.getData(7)
		if ret != "" : 
			self.Window.StratData = []
			start =0
			last =0
			last = ret.find(",", start)
			hole_number = int(ret[start:last])
			start = last +1

			loop_flag = True
			last = ret.find("#", start)
			if start == last :
				loop_flag = False 

			while loop_flag :
				last = ret.find(":", start)
				if start == last :
					start = last +1
					last = ret.find("#", start)
					if start == last :
						break
					last = ret.find(",", start)
					hole_number = int(ret[start:last])
					start = last +1
					if ret[start:start+1] == ':' :
						continue
					if ret[start+1:start+2] == '#' :
						break

				last = ret.find("#", start)
				if start == last :
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

				if self.Window.maxAgeRange < agevalue :
					self.Window.maxAgeRange = int(agevalue) + 2 
					#self.agePanel.maxAge.SetValue(str(self.Window.maxAgeRange))

				last = ret.find(":", start)
				if start == last :
					start = last +1
					last = ret.find("#", start)
					if start == last :
						break
					last = ret.find(",", start)
					hole_number = int(ret[start:last])
					start = last +1
					if ret[start:start+1] == ':' :
						continue
					if ret[start+1:start+2] == '#' :
						break

				last = ret.find("#", start)
				if start == last :
					break

	def OnNewData(self, event):
		if self.Window.HoleData != [] :
			#self.logFileptr.write("Closed All Files Loaded. \n\n")
			if event != None and self.client != None :
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
		#self.splicePanel.OnInitUI()
		self.spliceIntervalPanel.OnInitUI()
		self.eldPanel.OnInitUI()
		self.autoPanel.OnInitUI(True)
		self.agePanel.OnInitUI()
		self.filterPanel.OnInitUI()

		py_correlator.cleanData(1)
		self.OnClearData()
		self.OnDisableMenu(0, False)
		self.Window.UpdateDrawing()

	def OnClearAllData(self, event):
		self.OnClearData()

	def OnClearData(self):
		py_correlator.cleanData(2)
		self.Window.AdjustDepthCore = []
		self.Window.TieData = []
		self.Window.GuideCore = []
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

	def OnClearComposite(self, event):
		py_correlator.cleanData(3)
		self.Window.HoleData = []
		self.Window.AdjustDepthCore = []
		self.Window.TieData = []
		self.Window.GuideCore = []
		self.UpdateData()
		#self.Window.UpdateDrawing()

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
		if self.Window.hole_sagan != -1 :
			self.Window.OnUpdateHoleELD()
		self.eldPanel.OnInitUI()
		self.autoPanel.OnInitUI(False)
		self.Window.UpdateDrawing()
		if self.Window.ELDapplied == False and self.Window.LogData != [] :
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
		if ret == wx.ID_OK :
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
		if sys.platform == 'win32' :
			cmd = "copy "
		cmd += myPath + "/default.cfg " + myPath + "/tmp/.default.cfg" 
		os.system(cmd)
		
		f = open(myPath + '/default.cfg', 'w+')
		f.write("[applications] \n")
		
		self.WritePreferenceItem("fullscreen", self.fulls, f)

		winPT = self.GetPosition()
		if winPT[0] < 0 or winPT[1] < 0 :
			winPT = [0, 0]
		self.WritePreferenceItem("winx", winPT[0], f)

		if sys.platform != 'win32' :
			if winPT[0] < 800 and winPT[1] == 0 :
				self.WritePreferenceItem("winy", 100, f)
			else :
				self.WritePreferenceItem("winy", winPT[1], f)
		else :
			self.WritePreferenceItem("winy", winPT[1], f)

		width, height = self.GetClientSizeTuple()
		self.WritePreferenceItem("width", width, f)
		self.WritePreferenceItem("height", height, f)

		self.WritePreferenceItem("secondscroll", self.Window.isSecondScroll, f)

		if (width - self.Window.splicerX) < 10 :
			self.Window.splicerX = width / 2
		self.WritePreferenceItem("middlebarposition", self.Window.splicerX, f)

		self.WritePreferenceItem("startdepth", self.Window.rulerStartDepth, f)
		self.WritePreferenceItem("secondstartdepth", self.Window.SPrulerStartDepth, f)
		self.WritePreferenceItem("datawidth", self.optPanel.slider1.GetValue(), f)
		self.WritePreferenceItem("rulerunits", self.Window.GetRulerUnitsStr(), f)
		self.WritePreferenceItem("rulerscale", self.optPanel.slider2.GetValue(), f)

		rulerRangeStr = str(self.optPanel.min_depth.GetValue()) + " " + str(self.optPanel.max_depth.GetValue())
		self.WritePreferenceItem("rulerrange", rulerRangeStr, f)

		self.WritePreferenceItem("tiedotsize", self.Window.tieDotSize, f)
		self.WritePreferenceItem("tiewidth", self.Window.tieline_width, f)
		self.WritePreferenceItem("splicewindow", self.Window.spliceWindowOn, f)
		#self.WritePreferenceItem("fontsize", self.Window.font2.GetPointSize(), f) # see 11/2/2013 brg
		self.WritePreferenceItem("fontstartdepth", self.Window.startDepth, f)
		self.WritePreferenceItem("scrollsize", self.Window.ScrollSize, f)

		showlineInt = 1 if self.Window.showHoleGrid == True else 0
		self.WritePreferenceItem("showline", showlineInt, f)

		shiftclueInt = 1 if self.Window.ShiftClue == True else 0
		self.WritePreferenceItem("shiftclue", shiftclueInt, f)
		
		self.WritePreferenceItem("tab", self.Window.sideNote.GetSelection(), f)
		self.WritePreferenceItem("path", self.Directory, f)
		self.WritePreferenceItem("dbpath", self.DBPath, f)

		winPT = self.topMenu.GetPosition()
		self.WritePreferenceItem("toolbar", str(winPT[0]) + " " + str(winPT[1]), f)

		self.WritePreferenceItem("shiftrange", self.optPanel.tie_shift.GetValue(), f)
		self.WritePreferenceItem("leadlag", self.leadLag, f)
		self.WritePreferenceItem("winlength", self.winLength, f)

		colorStr = ""
		for i in range(18) : 
			colorItem = self.Window.colorList[i].Get()
			colorStr = colorStr + str(colorItem[0]) + " " + str(colorItem[1]) + " " + str(colorItem[2]) + " "
		self.WritePreferenceItem("colors", colorStr, f)

		overlapColorStr = ""
		for i in range(9) : 
			colorItem = self.Window.overlapcolorList[i].Get()
			overlapColorStr = overlapColorStr + str(colorItem[0]) + " " + str(colorItem[1]) + " " + str(colorItem[2]) + " "
		self.WritePreferenceItem("overlapcolors", overlapColorStr, f)

		f.close()


	def OnInitDataUpdate(self):
		self.UpdateCORE()
		self.UpdateSMOOTH_CORE()
		self.Window.UpdateDrawing()
		return

	def UndoSpliceSectionSend(self):
		if self.client == None :
			return

		# recover
		if self.spliceHoleA != None and self.spliceType != "first" :
			active = False
			for data in self.Window.SectionData :
				if self.spliceHoleA == data[0] and self.spliceCoreA == data[1] : 
					if active == False :
						start_depth = float(data[4])
						end_depth = float(data[5])
						if (self.spliceDepthA >= start_depth) and (self.spliceDepthA <= end_depth) :
							self.client.send("delete_section\t"+self.leg+"\t"+self.site+"\t"+data[0]+"\t"+data[1]+"\t"+data[2]+"\t"+data[3]+"\t"+ data[6] + "\t" + data[7] + "\n")
							self.client.send("cut_interval_to_new_track\t"+self.leg+"\t"+self.site+"\t"+data[0]+"\t"+data[1]+"\t"+data[2]+"\t"+data[3]+"\t"+ data[6]+ "\t" + data[7] + "\tspiliced\n")
							active = True
					elif active == True :
						self.client.send("delete_section\t"+self.leg+"\t"+self.site+"\t"+data[0]+"\t"+data[1]+"\t"+data[2]+"\t"+data[3]+"\t"+ data[6] + "\t" + data[7] + "\n")
						self.client.send("cut_interval_to_new_track\t"+self.leg+"\t"+self.site+"\t"+data[0]+"\t"+data[1]+"\t"+data[2]+"\t"+data[3]+"\t"+ data[6]+ "\t" + data[7] + "\tspiliced\n")
						active = True
				else :
					if active == True :
						break
		# delete
		if self.spliceHoleB != None :
			active = False
			for data in self.Window.SectionData :
				if self.spliceHoleB == data[0] and self.spliceCoreB == data[1] : 
					self.client.send("delete_section\t"+self.leg+"\t"+self.site+"\t"+data[0]+"\t"+data[1]+"\t"+data[2]+"\t"+data[3]+"\t"+ data[6] + "\t" + data[7] + "\n")
					active = True
				else :
					if active == True :
						break

		self.spliceHoleA = None 
		self.spliceHoleB = None 


	def NewDATA_SEND(self):
		if self.client != None and self.Window.HoleData != [] :
			self.client.send("delete_all\n")

			filenames = self.dataFrame.OnGET_IMAGE_FILENAME()
			for name in filenames :
				cmd = "load_lims_table\t" + name + "\n"
				#print "[DEBUG] send to Corelyzer : "  + str(cmd)
				self.client.send(cmd)

			py_correlator.saveAttributeFile(self.CurrentDir + 'tmp.affine.table'  , 1)
			cmd = "affine_table\t" + self.CurrentDir + "tmp.affine.table\n" 
			#print "[DEBUG] send to Corelyzer : "  + str(cmd)
			self.client.send(cmd)

			#ret = py_correlator.getData(18)
			#self.ParseSectionSend(ret)

	def UpdateSend(self):
		if self.client != None :
			cmd = "affine_table\t" + self.CurrentDir + "tmp.affine.table\n" 
			#print "[DEBUG] send to Corelyzer : "  + str(cmd)
			self.client.send(cmd)

	def SpliceSectionSend(self, hole, core, depth, type, tiedNo):
		if self.client != None and tiedNo <= 0:
			self.spliceType = type
			if type == "split" :
				self.spliceHoleA = hole
				self.spliceCoreA = core
				self.spliceDepthA = depth 
			else :
				self.spliceHoleB = hole
				self.spliceCoreB = core

			active = False
			for data in self.Window.SectionData :
				if hole == data[0] and core == data[1] : 
					if active == False and type != "first" :
						start_depth = float(data[4])
						end_depth = float(data[5])
						if (type == None) and (depth <= end_depth) :
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
						elif (type == "split") and (depth >= start_depth) and (depth <= end_depth) :
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
					else : 
						try:
							if type != "split" :
								self.client.send("cut_interval_to_new_track\t"+self.leg+"\t"+self.site+"\t"+data[0]+"\t"+data[1]+"\t"+data[2]+"\t"+data[3]+"\t"+ data[6] + "\t" + data[7] + "\tspiliced\n")
								active = True
							else :
								self.client.send("delete_section\t"+self.leg+"\t"+self.site+"\t"+data[0]+"\t"+data[1]+"\t"+data[2]+"\t"+data[3]+"\t"+ data[6] + "\t" + data[7] + "\n")
								active = True
						except Exception, E:
							#print "[DEBUG] Disconnect to the corelyzer"
							self.client.close()
							self.client = None
							return
				else :
					if active == True :
						return
		elif self.client != None :
			active = False
			for data in self.Window.SectionData :
				if hole == data[0] and core == data[1] : 
					if active == False :
						start_depth = float(data[4])
						end_depth = float(data[5])
						if (type == "split") and (self.spliceDepthA >= start_depth) and (self.spliceDepthA <= end_depth) :
							try :
								self.client.send("delete_section\t"+self.leg+"\t"+self.site+"\t"+data[0]+"\t"+data[1]+"\t"+data[2]+"\t"+data[3]+"\t"+ data[6] + "\t" + data[7] + "\n")

								self.client.send("cut_interval_to_new_track\t"+self.leg+"\t"+self.site+"\t"+data[0]+"\t"+data[1]+"\t"+data[2]+"\t"+data[3]+"\t"+ data[6] + "\t" + data[7] + "\tspiliced\n")

								active = True
							except Exception, E:
								#print "[DEBUG] Disconnect to the corelyzer"
								self.client.close()
								self.client = None
								return
						elif type == None : 
							if (self.spliceDepthB >= start_depth) and (self.spliceDepthB <= end_depth) :
								self.client.send("delete_section\t"+self.leg+"\t"+self.site+"\t"+data[0]+"\t"+data[1]+"\t"+data[2]+"\t"+data[3]+"\t"+ data[6] + "\t" + data[7] + "\n")

								self.client.send("cut_interval_to_new_track\t"+self.leg+"\t"+self.site+"\t"+data[0]+"\t"+data[1]+"\t"+data[2]+"\t"+data[3]+"\t"+ data[6] + "\t" + data[7] + "\tspiliced\n")
								#self.SpliceSectionSend(hole, core, depth, type, 1)
								return
							else :
								self.client.send("cut_interval_to_new_track\t"+self.leg+"\t"+self.site+"\t"+data[0]+"\t"+data[1]+"\t"+data[2]+"\t"+data[3]+"\t"+ data[6] + "\t" + data[7] + "\tspiliced\n")
					else : 
						try :
							if type == "split" :
								self.client.send("cut_interval_to_new_track\t"+self.leg+"\t"+self.site+"\t"+data[0]+"\t"+data[1]+"\t"+data[2]+"\t"+data[3]+"\t"+ data[6] + "\t" + data[7] + "\tspiliced\n")
								active = True
						except Exception, E:
							#print "[DEBUG] Disconnect to the corelyzer"
							self.client.close()
							self.client = None
							return
				else :
					if active == True :
						#if type == "split" :
						#	self.SpliceSectionSend(hole, core, depth, type, 1)
						break	


	def UndoShiftSectionSend(self):
		if self.shiftHole != None :
			self.ShiftSectionSend(self.shiftHole, self.shiftCore, self.shiftOffset, self.shiftType)
			self.shiftHole = None 

	def TieUpdateSend(self, leg, site, holeA, coreA, holeB, coreB, tie_depth, shift):
		if self.client != None :
			ret1 = self.GetSectionNoWithDepth(holeB, coreB, tie_depth)
			# ret1 = type, section_number
			cmd  = "tie_update\t" + str(leg) + "\t"+ str(site) + "\t" + str(holeA) + "\t" + str(coreA) + "\t" + str(leg) + "\t"+ str(site) + "\t" + str(holeB) + "\t" + str(coreB) + "\t" + str(ret1[1]) + "\t" + str(ret1[0]) + "\t" + str(tie_depth) + "\t" + str(shift) + "\n"
			#print "[DEBUG] send to Corelyzer : " + cmd
			try:
				self.client.send(cmd)
			except Exception, E:
				#print "[DEBUG] Disconnect to the corelyzer"
				self.client.close()
				self.client = None
			
	def clearSend(self) :
		#def clearSend(self, leg, site, holeA, coreA, holeB, coreB, tie_depth):
		if self.client != None :
			#ret1 = self.GetSectionNoWithDepth(holeB, coreB, tie_depth)
			#cmd  = "tie_update\t" + str(leg) + "\t"+ str(site) + "\t" + str(holeA) + "\t" + str(coreA) + "\t" + str(leg) + "\t"+ str(site) + "\t" + str(holeB) + "\t" + str(coreB) + "\t" + str(ret1[1]) + "\t" + str(ret1[0]) + "\t" + "0.0" + "\n"
			#print "[DEBUG] send to Corelyzer : " + cmd

			cmd = "affine_table\t" + self.CurrentDir + "tmp.affine.table\n" 
			#print "[DEBUG] send to Corelyzer : "  + str(cmd)
			try:
				self.client.send(cmd)
			except Exception, E:
				print "[DEBUG] Disconnect to the corelyzer"
				self.client.close()
				self.client = None

	def FineTuneSend(self, leg, site, holeA, coreA, holeB, coreB, tie_depth):
		if self.client != None :
			self.Window.selectedTie = -1
			self.Window.UpdateDrawing()
			tune_flag = self.OnShowMessage("About", "Do you want to process find tune?", 2)
			if tune_flag == wx.ID_OK :
				ret1 = self.GetSectionNo(holeA, coreA)
				ret2 = self.GetSectionNo(holeB, coreB)
				cmd  = "fine_tune\t" + str(leg) + "\t"+ str(site) + "\t" + str(holeA) + "\t" + str(coreA) + "\t" + str(ret1[1]) + "\t1\t" + str(ret1[0]) + "\t"  + str(leg) + "\t"+ str(site) + "\t" + str(holeB) + "\t" + str(coreB) + "\t" + str(ret2[1]) + "\t1\t" + str(ret2[0]) + "\t" + str(tie_depth) + "\n"
				#print "[DEBUG] send to Corelyzer : " + cmd
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
				if start > 0 :
					shift = float(recvdata[0:start])

				#print "[DEBUG] got data : " + str(recvdata) + " = " + str(shift)
				hold_dlg.Close()
				hold_dlg.Destroy()
				self.Window.SetFocusFromKbd()
				return shift

		return 0.0
		

	def ShowCoreSend(self, leg, site, hole, core):
		if self.client != None :
			core_Type = '-'
			start_section = '-' 
			end_section = '-' 
			shift = '-'
			for data in self.Window.SectionData :
				if hole == data[0] and core == data[1] : 
					core_Type = data[2] 
					if start_section == '-' :
						start_section = data[3]
					end_section = data[3]
					shift = data[8]
			msg = 'load_core\t' + leg + '\t' + site + '\t' + hole + '\t' + core + '\t' + core_Type + '\t'
			msg += start_section + '\t' + end_section + '\t' + shift + '\n'
			#print "[DEBUG-showCoreSend] send to Corelyzer : " + msg 

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
		for data in self.Window.SectionData :
			if hole == data[0] and core == data[1] : 
				flag = True 
				idx = data[3]
				type = data[2]
			elif flag == True :
				break
		return idx, type

	# JULIAN
	def GetSectionNoWithDepth(self, hole, core, depth):
		flag = False
		idx = 0
		type = '-'
		prev_depth = 0.0
		for data in self.Window.SectionData :
			if hole == data[0] and core == data[1] : 
				flag = True 
				if depth >= prev_depth and depth < data[4] :
					break

				idx = data[3]
				type = data[2]
				if depth >= data[4] and depth <= data[5] :
					break
				prev_depth = data[5] 
			elif flag == True :
				break
		return idx, type

	def GetSectionAtDepth(self, hole, core, type, depth):
		return py_correlator.getSectionAtDepth(hole, core, type, depth)


	def ShiftSectionSend(self, hole, core, offset, type):
		if self.client != None :
			"""
			self.shiftHole = hole
			self.shiftCore = core
			self.shiftOffset = -offset
			self.shiftType = type
			active = False
			for data in self.Window.SectionData :
				if hole == data[0] and core == data[1] : 
					try:
						cmd = "shift_section\t"+self.leg+"\t"+self.site+"\t"+data[0]+"\t"+data[1]+"\t"+data[2]+"\t"+data[3]+"\t"+ str(offset)+"\n"
						self.client.send(cmd)
						#print "[DEBUG] send to Corelyzer : " + cmd
						active = True
					except Exception, E:
						print "[DEBUG] Disconnect to the corelyzer"
						self.client.close()
						self.client = None
						return
				else :
					if active == True :
						if type == 2 :
							return
						else :
							if hole == data[0] :
								try:
									cmd = "shift_section\t"+self.leg+"\t"+self.site+"\t"+data[0]+"\t"+data[1]+"\t"+data[2]+"\t"+data[3]+"\t"+ str(offset)+"\n"
									self.client.send(cmd)
									#print "[DEBUG] send to Corelyzer : " + cmd
								except Exception, E:
									print "[DEBUG] Disconnect to the corelyzer"
									self.client.close()
									self.client = None
									return
							else :
								return
			"""

			cmd = "affine_table\t" + self.CurrentDir + "tmp.affine.table\n" 
			#print "[DEBUG] send to Corelyzer : "  + str(cmd)
			self.client.send(cmd)
							

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
			if start == last :
				start = last + 1
				last = data.find(",", start)
				shift = data[start:last] 
				start = last + 1

			last = data.find(":", start)
			if start == last :
				start = last + 1
				last = data.find("#", start)
				if start == last :
					break
				else :
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

			if hole != prevHole or core != prevCore :
				if startSecNo == "-" :
					startSecNo = secNo
				else :
					startSecNo = secNo
					secInfo_modified = (secInfo[0], secInfo[1], secInfo[2], secInfo[3], secInfo[4], secInfo[5], secInfo[6], secInfo[7], shift)
					self.Window.SectionData.append(secInfo_modified)
			else :
				if secInfo != None :
					self.Window.SectionData.append(secInfo)

			secInfo = (hole, core, type, secNo, depth_start, depth_end, top, bottom, '-')

			prevCore = core
			prevHole = hole
			prevType = type
			prevSecNo = secNo


		if startSecNo != "-" :
			if secInfo != None :
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
		if type == "GRA" :
			type = "Bulk Density(GRA)"

		# brg 11/18/2015: top and bottom are actually min/max section offset for the hole,
		# NOT min/max depths of hole. Those values are parsed out in ParseData() if needed...
		# top, bottom, min, max, 
		# 4 times
		temp =[]
		for i in range(4) :
			last = data.find(",", start)
			temp.append(float(data[start:last])) 
			start = last +1

		if self.min > temp[2] :
			self.min = temp[2]
		if self.max < temp[3] :
			self.max = temp[3]

		# hole-name
		last = data.find(",", start)
		holename = data[start:last] 

		# register Hole and Type
		if self.PrevDataType != type and self.LOCK == 0 : 
			self.filterPanel.OnRegisterHole("All " + type)
			#if self.noOfHoles != 0 and self.filterPanel.locked == False :
			#	self.noOfSameTypeHoles = self.noOfHoles - self.noOfSameTypeHoles
			#	for n in range(self.noOfSameTypeHoles) : 
			#		self.Window.OnChangeHoleRange(self.min, self.max)
			#	self.min = 999
			#	self.max = -999

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
		if start != last :
			for i in range(coreNum) :
				self.ParseCore(start, last, hole, data)
				start = self.CoreStart
				last = self.CoreLast 

			#holeinfo = site, leg, type, temp[0], temp[1], temp[2], temp[3], holename, self.CoreNo 
			holeinfo = site, leg, type, temp[0], temp[1], temp[2], temp[3], holename, coreNum 
			hole.insert(0, holeinfo)
			temp =[]
			temp.append(hole)
			output.append( temp )
		else :
			self.CoreStart = start
			self.CoreLast = last


	def ParseCore(self, start, last, hole, data) :
		# core-number, top, bottom, min, max, values, affine
		temp =[]
		last = data.find(",", start)
		temp.append(data[start:last])
		start = last +1

		last = data.find(":", start)
		if start == last :
			start = last + 1
			self.CoreStart = start
			self.CoreLast = last
			return

		for i in range(6) :
			last = data.find(",", start)
			temp.append(float(data[start:last])) 
			start = last +1
		corelist = [] 
		value = ()	

		last = data.find(",", start)
		annot = data[start:last] 
		start = last +1

		last = data.find(",", start)
		quality = data[start:last] 
		start = last +1

		# Get Section Information
		last = data.find(":", start)
		sections = []
		while start != last : 
			last = data.find(",", start)
			sec_depth = float(data[start:last])
			start = last +1
			sections.append(sec_depth)

			last = data.find(":", start)
		start = last +1

		# Get Data
		last = data.find(":", start)
		if start == last :
			start = last + 1
			self.CoreStart = start
			self.CoreLast = last
		else : 
			while True:
				last = data.find(",", start)
				v_value = float(data[start:last])
				start = last +1
				last = data.find(",", start)
				v_data = float(data[start:last])
				start = last +1
				corelist.append((v_value, v_data))
				last = data.find(":", start)
				if start == last :
					# Create a "core data" item, which looks like the following: 
					# (1-based core index in hole, top, bottom, mindata, maxdata, affine offset, stretch, annotated type,
					# core quality, sections (list of each sections' top depth), list of all cores's depth/data tuple-pairs
					# a list of all the core's depth/data pairs.
					coreinfo = temp[0], temp[1], temp[2], temp[3], temp[4], temp[5], temp[6], annot, quality, sections, corelist
					hole.append(coreinfo)
					start = last + 1
					self.CoreStart = start
					self.CoreLast = last
					self.CoreNo = self.CoreNo + 1
					break

	def ParseData(self, data, output):
		if data != "" :
			self.noOfSameTypeHoles = 0
			if self.filterPanel.locked == False :
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
				if self.filterPanel.locked == False :
					self.noOfHoles = self.noOfHoles + 1
				start = self.CoreStart
				last = self.CoreLast 
				last = data.find("#", start)
				if start == last :
					break

			#if self.LOCK == 0 :
			#	if self.noOfHoles != 0 and self.filterPanel.locked == False :
			#		self.noOfSameTypeHoles = self.noOfHoles - self.noOfSameTypeHoles
			#		for n in range(self.noOfSameTypeHoles) :
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
		if (self.max - self.min) != 0 :
			self.Window.coefRange = self.Window.holeWidth / (self.Window.maxRange - self.Window.minRange)

	def ParseSaganData(self, data):
		if data != "" :
			start =0
			last =0
			last = data.find("#", start)
			if start == last :
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
				if start == last :
					break
			self.Window.SetSaganFromFile(tie_list)


	def ParseTieData(self, data, data_list):
		if data != "" :
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
					if start == last :
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
				if start == last :
					break


	def ParseShiftTieData(self, data, data_list):
		if data != "" :
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
					if start == last :
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

				if hole_name != None :
					data_list.append( (hole_index, hole_name, l) )

				last = data.find("#", start)
				if start == last :
					break


	def ParseSpliceData(self, data, flag):
		if data != "" :
			self.Window.SpliceCore = []
			start =0
			last =0
			last = data.find("#", start)
			if start == last :
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
				if start != last :
					annotation = data[start:last]
				start = last +1
				if type == 30 :
					strtypeA = "GRA"
				elif type == 31 :
					strtypeA = "Pwave"
				elif type == 32 :
					strtypeA = "Susceptibility"
				elif type == 33 :
					strtypeA = "Natural Gamma"
				elif type == 34 :
					strtypeA = "Reflectance"
				elif type == 37 :
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
				if start != last :
					annotation = data[start:last]
				start = last +1
				if type == 30 :
					strtypeB = "GRA"
				elif type == 31 :
					strtypeB = "Pwave"
				elif type == 32 :
					strtypeB = "Susceptibility"
				elif type == 33 :
					strtypeB = "Natural Gamma"
				elif type == 34 :
					strtypeB = "Reflectance"
				elif type == 37 :
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
				if start == last :
					break
			self.Window.SetSpliceFromFile(tie_list, flag)

	def NewDrawing(self,cfgfile, new_flag):
		self.Window.DrawData = self.LoadPreferencesAndInitDrawData(cfgfile, new_flag)
		self.Window.UpdateDrawing()

	def ShowDataManager(self):
		if self.CHECK_CHANGES() == True :
			ret = self.OnShowMessage("About", "Do you want to save?", 0)
			if ret == wx.ID_YES:
				self.topMenu.OnSAVE(None) # dummy event
		if self.dataFrame.IsShown() == False :
			self.Window.Hide()
			self.dataFrame.Show(True)
			#self.midata.Check(True)
			self.topMenu.dbbtn.SetLabel("Go to Display")
		self.Layout()

	def ShowDisplay(self):
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
		if typeStr == "Bulk Density(GRA)" :
			type = 1 
		elif typeStr.lower() == "pwave": # expecting 'Pwave' or 'PWave'
			type = 2 
		elif typeStr == "Susceptibility" :
			type = 3 
		elif typeStr.replace(' ', '') == "NaturalGamma" : # expecting 'Natural Gamma' or 'NaturalGamma'
			type = 4 
		elif typeStr == "Reflectance" :
			type = 5 
		elif typeStr == "Other" :
			type = 6
		else:
			annot = typeStr
		return type, annot

	""" Convert data type string to output filename suffix. When Exporting data, the suffix
	is 'adj', in all other cases it's 'fix' """
	def TypeStrToFileSuffix(self, typeStr, useExportSuffix=False):
		suffix = "adj" if useExportSuffix else "fix"
		result = ""
		if typeStr == "Bulk Density(GRA)" :
			result = "gr" + suffix
		elif typeStr.lower() == "pwave" :
			result = "pw" + suffix
		elif typeStr == "Susceptibility" :
			suffix = "sus" + suffix
		elif typeStr.replace('  ', '') == "NaturalGamma" :
			result = "ng" + suffix
		elif typeStr == "Reflectance" :
			result = "refl" + suffix
		# 1/20/2014 brgtodo: May not be correct for export case...previous code
		# ignored the possibility of an Other type being passed in. However, this
		# does yield the correct suffix (type only, no adj/fix suffix) on Export.
		else:
			result = typeStr
		return result

	def LoadPreferencesAndInitDrawData(self, cfgfile, new_flag):
		self.positions= [ (77,32) , (203,32), (339,32),
						 (77,152) , (203,152), (339,152),
						 (77,270) , (203,270), (339,270),
						 (77,390) , (203,390), (339,390) ]

		DrawData = {}

		self.config = ConfigParser.ConfigParser()
		self.config.read(cfgfile)
		
		scroll_start = self.Window.startDepth * 0.7
		l = []

		#self.Width, self.Height = self.GetClientSizeTuple()
		if self.config.has_option("applications", "width"):
			str_temp =  self.config.get("applications", "width")
			if len(str_temp) > 0 :
				self.Width = int ( str_temp )
		if self.config.has_option("applications", "height"):
			str_temp =  self.config.get("applications", "height")
			if len(str_temp) > 0 :
				self.Height = int ( str_temp )
		if self.Width <= 0 :
			self.Width = 800
		if self.Height <= 0 :
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
			if len(str_temp) > 0 :
				win_x = int ( str_temp )
		if self.config.has_option("applications", "winy"):
			str_temp = self.config.get("applications", "winy")
			if len(str_temp) > 0 :
				win_y = int ( str_temp )
			#if win_y == 0 :
			#	win_y = 100

		if platform_name[0] != "Windows" and win_y == 0 :
			if win_x < 800 :
				win_y = 50

		#print "[DEBUG] Window Position :" + str(win_x) + " " + str(win_y)

		display_x, display_y = wx.DisplaySize()
		if (win_x > display_x) or (win_y > display_y) : 
			win_x = 0
			win_y = 23 

		self.SetPosition((win_x, win_y))

		win_width = self.Width
		win_height = self.Height
		#print "[DEBUG] Window Width = " + str(win_width) + " " + str(win_height)
		if sys.platform != 'win32' :
			win_height = self.Height + 40
		else :
			win_width = win_width + 8
			win_height = self.Height + 76
		
		# 4/10/2014 brg: init depends on self.DBPath among others...
		self.dataFrame = dbmanager.DataFrame(self)
		
		conf_str = ""
		conf_array = []

		#if self.config.has_option("applications", "middlebarposition"):
		#	str_temp =  self.config.get("applications", "middlebarposition")
		#	if len(str_temp) > 0 :
		#		conf_value = int ( str_temp ) 
		#		if conf_value > (display_x -340) :
		#			conf_value = display_x - 340
		#		self.Window.splicerX = conf_value
		#if self.Window.splicerX  < 150 :
		#	self.Window.splicerX = 180

		#if self.config.has_option("applications", "startdepth"):
		#	str_temp = self.config.get("applications", "startdepth")
		#	if len(str_temp) > 0 :
		#		conf_value = float ( str_temp )
		#		self.Window.rulerStartDepth = conf_value 

		if self.config.has_option("applications", "tiedotsize"):
			str_temp = self.config.get("applications", "tiedotsize")
			if len(str_temp) > 0 :
				conf_value = int ( str_temp )
				self.Window.tieDotSize = conf_value 

		if self.config.has_option("applications", "tiewidth"):
			str_temp = self.config.get("applications", "tiewidth")
			if len(str_temp) > 0 :
				conf_value = int ( str_temp )
				self.Window.tieline_width = conf_value 

		#if self.config.has_option("applications", "secondstartdepth"):
		#	str_temp = self.config.get("applications", "secondstartdepth")
		#	if len(str_temp) > 0 :
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
			if len(conf_str) > 0 :
				conf_array = conf_str.split()
				self.optPanel.min_depth.SetValue(conf_array[0])
				self.optPanel.max_depth.SetValue(conf_array[1])
				self.optPanel.OnDepthViewAdjust(None)

		if self.config.has_option("applications", "rulerscale"):
			str_temp = self.config.get("applications", "rulerscale")
			if len(str_temp) > 0 :
				conf_value = int ( str_temp )
				self.optPanel.slider2.SetValue(conf_value)
				self.optPanel.OnRulerOneScale(None)

		if self.config.has_option("applications", "shiftrange"):
			str_temp = self.config.get("applications", "shiftrange")
			if len(str_temp) > 0 :
				conf_value = float ( str_temp )
				self.optPanel.tie_shift.SetValue(str_temp)
				self.optPanel.OnTieShiftScale(None)

		if self.config.has_option("applications", "splicewindow"):
			str_temp = self.config.get("applications", "splicewindow")
			if len(str_temp) > 0 :
				conf_value = int ( str_temp )
			if conf_value == 0 :
				self.Window.spliceWindowOn = 1 
				self.OnActivateWindow(1)
				self.misecond.Check(False)
			else : 
				self.Window.spliceWindowOn = 0 
				self.OnActivateWindow(0)
				self.misecond.Check(True)
		
		conf_value = 0
		if self.config.has_option("applications", "secondscroll"):
			str_temp = self.config.get("applications", "secondscroll")
			if len(str_temp) > 0 :
				conf_value = int ( str_temp )
			if conf_value == 0:
				self.Window.isSecondScroll = 0 
				self.optPanel.opt2.SetValue(False)
			else :
				self.Window.isSecondScroll =1 
				self.optPanel.opt2.SetValue(True)

		if self.config.has_option("applications", "colors"):
			conf_str = self.config.get("applications", "colors") 
			if len(conf_str) > 0 :
				conf_array = conf_str.split()
				self.Window.colorList = []
				for i in range(18) :
					r = int(conf_array[i*3])
					g = int(conf_array[i*3+1]) 
					b = int(conf_array[i*3+2]) 
					self.Window.colorList.insert(i, wx.Colour(r, g, b))

		if self.config.has_option("applications", "overlapcolors"):
			conf_str = self.config.get("applications", "overlapcolors") 
			if len(conf_str) > 0 :
				conf_array = conf_str.split()
				self.Window.overlapcolorList = []
				for i in range(9) :
					r = int(conf_array[i*3])
					g = int(conf_array[i*3+1]) 
					b = int(conf_array[i*3+2]) 
					self.Window.overlapcolorList.insert(i, wx.Colour(r, g, b))

		# see 11/2/2013 brg
		#if self.config.has_option("applications", "fontsize"):
		#	str_temp = self.config.get("applications", "fontsize")
		#	if len(str_temp) > 0 :
		#		conf_value = int ( str_temp )
		#		self.Window.font2.SetPointSize(conf_value)
			
		if self.config.has_option("applications", "fontstartdepth"):
			str_temp = self.config.get("applications", "fontstartdepth")
			if len(str_temp) > 0 :
				conf_value = float ( str_temp )			
				self.Window.startDepth = conf_value
				self.Window.startAgeDepth = conf_value
		
		if self.config.has_option("applications", "showline"):
			str_temp = self.config.get("applications", "showline")
			if len(str_temp) > 0 :
				if str_temp == "1" :
					self.Window.showHoleGrid = True 
					self.optPanel.opt3.SetValue(True)
				else :
					self.Window.showHoleGrid = False 
					self.optPanel.opt3.SetValue(False)

		if self.config.has_option("applications", "shiftclue"):
			str_temp = self.config.get("applications", "shiftclue")
			if len(str_temp) > 0 :
				showArrows = True if str_temp == '1' else False
				self.Window.ShiftClue = showArrows 
				self.optPanel.showAffineShiftArrows.SetValue(showArrows)


		if self.config.has_option("applications", "scrollsize"):
			str_temp = self.config.get("applications", "scrollsize")
			if len(str_temp) > 0 :
				conf_value = int ( str_temp )
				self.Window.ScrollSize = conf_value

		if self.config.has_option("applications", "discreteplotmode"):
			str_temp = self.config.get("applications", "discreteplotmode")
			if len(str_temp) > 0 :
				conf_value = int ( str_temp )
				self.Window.DiscretePlotMode = conf_value
				if conf_value == 1 :
					self.miplot.Check(True)
			
		if self.config.has_option("applications", "toolbar"):
			conf_str = self.config.get("applications", "toolbar")
			if len(conf_str) > 0 :
				conf_array = conf_str.split()
				x = int(conf_array[0])
				y = int(conf_array[1])
				if x >= display_x :
					x = 300
				if y >= display_y :
					y = 200
				self.topMenu.SetPosition((x, y))
			
		#if self.config.has_option("applications", "startup"):
		#	conf_str = self.config.get("applications", "startup")
		#	if conf_str == "False" :
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
			if len(str_temp) > 0 :
				self.leadLag = float(str_temp)

		if self.config.has_option("applications", "middlebarposition"):
			str_temp =  self.config.get("applications", "middlebarposition")
			if len(str_temp) > 0 :
				conf_value = int ( str_temp ) 
				if conf_value > (display_x -340) :
					conf_value = display_x - 340
				self.Window.splicerX = conf_value
		if self.Window.splicerX  < 150 :
			self.Window.splicerX = 180

		if self.config.has_option("applications", "startdepth"):
			str_temp = self.config.get("applications", "startdepth")
			if len(str_temp) > 0 :
				conf_value = float ( str_temp )
				self.Window.rulerStartDepth = conf_value 

		if self.config.has_option("applications", "secondstartdepth"):
			str_temp = self.config.get("applications", "secondstartdepth")
			if len(str_temp) > 0 :
				conf_value = float ( str_temp )
				self.Window.SPrulerStartDepth = conf_value 

		if self.config.has_option("applications", "winlength"):
			str_temp = self.config.get("applications", "winLength")
			if len(str_temp) > 0 :
				self.winLength = float(str_temp)

		self.OnUpdateGraphSetup(1)
		self.OnUpdateGraphSetup(2)
		self.OnUpdateGraphSetup(3)

		if new_flag == False :
			if self.config.has_option("applications", "dbpath"):
				str_temp = self.config.get("applications", "dbpath")
				if len(str_temp) > 0 :
					if os.access(str_temp, os.F_OK) == True :
						str_len =  len(str_temp) -1
						self.DBPath = str_temp
						if platform_name[0] == "Windows" :
							if str_temp[str_len] != "\\" :
								self.DBPath = str_temp + "\\"
						else :
							if str_temp[str_len] != "/" :
								self.DBPath = str_temp + "/"
						self.dataFrame.PathTxt.SetValue("Path : " + self.DBPath)
					else :
						self.DBPath = myPath
						self.dataFrame.PathTxt.SetValue("Path : " + self.DBPath)
		else :
			self.DBPath = myPath
			self.dataFrame.PathTxt.SetValue("Path : " + self.DBPath)


		if self.DBPath == "-" :
			self.DBPath = User_Dir  + "/Documents/Correlator/" + vers.BaseVersion  + "/"
			if platform_name[0] == "Windows" :
				self.DBPath =  User_Dir  + "\\Correlator\\" + vers.BaseVersion + "\\"
			self.dataFrame.PathTxt.SetValue("Path : " + self.DBPath)
			
			if os.access(self.DBPath, os.F_OK) == False :
				os.mkdir(self.DBPath)
			prefile = self.DBPath + "db"
			if os.access(prefile, os.F_OK) == False :
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

		data_loaded = False
		if self.config.has_option("applications", "data"):
			conf_str = self.config.get("applications", "data")
			conf_array = conf_str.split()
			# HYEJUNG DB
			#if (self.dataFrame.listPanel.GetCellValue(0, 0) != '') and (len(conf_array) > 0) :
			#	if conf_array[0] != "-1" :
			#		for data in conf_array:
			#			self.dataFrame.listPanel.SelectRow(int(data), True)
			#		self.CurrentDataNo = int(conf_array[0]) 
			#		data_loaded = self.dataFrame.OnLOAD(1)
					
			#self.CurrentDataNo = conf_value
			#if conf_value >= 0 :
			#	self.dataFrame.listPanel.SelectRow(conf_value)
			#	data_loaded = self.dataFrame.OnLOAD(1)


		if self.config.has_option("applications", "path"):
			str_temp = self.config.get("applications", "path")
			if len(str_temp) > 0 :
				self.Directory = str_temp

		if self.config.has_option("applications", "datawidth"):
			str_temp = self.config.get("applications", "datawidth")
			if len(str_temp) > 0 :
				conf_value = int ( str_temp )
				self.optPanel.slider1.SetValue(conf_value)
				self.optPanel.OnChangeWidth(None)

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

		if self.ScrollMax != 0 :
			self.Window.UpdateScroll(1)
			self.Window.UpdateScroll(2)
			self.Window.ScrollUpdate = 1 

		return DrawData
	
	
# brgtodo 12/21/2015: still depends on MainFrame 
class SpliceController:
	def __init__(self, parent):
		self.parent = parent # MainFrame
		self.splice = splice.SpliceBuilder() # SpliceBuilder for current splice
		self.altSplice = splice.SpliceBuilder() # SpliceBuilder for alternate splice
		
		self.clear() # init selection, file state members
		
		self.selChangeListeners = []
		self.addIntervalListeners = []
		
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
			self.setDirty()
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

	def _onAdd(self, dirty=True):
		self._updateTies()
		if dirty:
			self.setDirty()
		for listener in self.addIntervalListeners:
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
			site = si.coreinfo.leg # ugh...mixed up? this site-exp shit is so dumb.
			hole = si.coreinfo.hole
			core = si.coreinfo.holeCore
			#print "Saving Interval {}: {}".format(index, si.coreinfo.getHoleCoreStr())
			
			offset = self.parent.Window.findCoreAffineOffset(hole, core)
			#print "   affine offset = {}".format(si.coreinfo.getHoleCoreStr(), offset)
			# section summary is always in CSF-A, remove CCSF-A/MCD offset for calculations
			mbsfTop = round(si.getTop(), 3) - offset
			topSection = secsumm.getSectionAtDepth(site, hole, core, mbsfTop)
			if topSection is not None:
				topDepth = secsumm.getSectionTop(site, hole, core, topSection)
				topOffset = round((mbsfTop - topDepth) * 100.0, 1) # section depth in cm
			else:
				print "Skipping, couldn't find top section at top CSF depth {}".format(mbsfTop)
				continue
			
			mbsfBot = round(si.getBot(), 3) - offset
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
			
			series = pandas.Series({'Exp':si.coreinfo.site, 'Site':site, 'Hole':hole, 'Core':core, 'CoreType':coreType, \
									'TopSection':topSection, 'TopOffset':topOffset, 'TopDepthCSF':mbsfTop, 'TopDepthCCSF':mbsfTop+offset, \
									'BottomSection':botSection, 'BottomOffset':botOffset, 'BottomDepthCSF':mbsfBot, 'BottomDepthCCSF':mbsfBot+offset, \
									'SpliceType':spliceType, 'DataUsed':si.coreinfo.type, 'Comment':si.comment})
			rows.append(series)			
		if len(rows) > 0:
			df = pandas.DataFrame(columns=tabularImport.SITFormat.req)
			df = df.append(rows, ignore_index=True)
			#print "{}".format(df)
			tabularImport.writeToFile(df, filepath)
			self.setDirty(False)
			
	def load(self, filepath, destSplice, datatype=None):
		df = tabularImport.readFile(filepath)
		previousSpliceType = None
		previousAffBot = None
		for index, row in df.iterrows(): # itertuples() is faster if needed
			#print "Loading row {}: {}".format(index, str(row))
			coreinfo, affineOffset, top, bot, fileTop, fileBot, appliedTop, appliedBot = self.getRowDepths(row)
			coremin, coremax = self.getCoreRange(coreinfo)
			coreinfo.minDepth = coremin
			coreinfo.maxDepth = coremax
			if datatype is not None: # override file datatype
				if datatype == "NaturalGamma":
					datatype = "Natural Gamma"
				coreinfo.type = datatype
				
			comment = "" if pandas.isnull(row.Comment) else str(row.Comment)
			intervalTop = previousAffBot if previousSpliceType == "TIE" and previousAffBot is not None else appliedTop
			previousSpliceType = row.SpliceType
			previousAffBot = appliedBot
			spliceInterval = splice.SpliceInterval(coreinfo, intervalTop, previousAffBot, comment)
			destSplice.addInterval(spliceInterval) # add to ints - should already be sorted properly
		
		self._onAdd(dirty=False) # notify listeners that intervals have been added

	def loadSplice(self, filepath):
		self.clear()
		self.load(filepath, self.splice)
	
	def loadAlternateSplice(self, filepath, datatype):
		self.altSplice.clear()
		self.load(filepath, self.altSplice, datatype)

	# given a Splice Interval Table row from pandas.DataFrame, return core info,
	# applied affine shift, unshifed depths and shifted depths (both with file and applied affine) 
	def getRowDepths(self, row):
		hole = row.Hole
		core = str(row.Core)
		datatype = row.DataUsed
		coreinfo = self.parent.Window.findCoreInfoByHoleCoreType(hole, core, datatype)
		if coreinfo is None:
			#print "Couldn't find hole {} core {} of type {}".format(hole, core, datatype)
			coreinfo = self.parent.Window.findCoreInfoByHoleCore(hole, core)
			if coreinfo is None:
				return
		
		# affine shift from currently-loaded affine table	
		affineOffset = self.parent.Window.findCoreAffineOffset(coreinfo.hole, coreinfo.holeCore)
		
		# file CSF and CCSF depths - ensure no sub-mm decimals
		top = round(row.TopDepthCSF, 3)
		bot = round(row.BottomDepthCSF, 3)
		fileTop = round(row.TopDepthCCSF, 3)
		fileBot = round(row.BottomDepthCCSF, 3)
		
		# CCSF depths with current affine applied
		appliedTop = round(top + affineOffset, 3)
		appliedBot = round(bot + affineOffset, 3)
		
		return coreinfo, affineOffset, top, bot, fileTop, fileBot, appliedTop, appliedBot
	
	# confirm applied affine shift matches file's CSF and CCSF difference
	def affineMatches(self, appliedVal, fileVal, coreinfo):
		matches = appliedVal == fileVal
		if not matches:
			msg = "Core {}: Applied affine shift ({}) does not match shift in Splice Table ({}), can't load splice.".format(coreinfo.getHoleCoreStr(), appliedVal.__repr__(), fileVal.__repr__())
			self._setErrorMsg(msg)
		return matches

	# do currently-applied affine shifts match corresponding Splice Interval file's shifts?
	def canApplyAffine(self, filepath):
		canApply = True
		df = tabularImport.readFile(filepath)
		for index, row in df.iterrows(): # itertuples() is faster if needed
			coreinfo, affineOffset, top, bot, fileTop, fileBot, appliedTop, appliedBot = self.getRowDepths(row)
			if not self.affineMatches(appliedTop, fileTop, coreinfo) or not self.affineMatches(appliedBot, fileBot, coreinfo):
				canApply = False
				break
		return canApply


class CorrelatorApp(wx.App):
	def __init__(self, new_version, cfg=myPath+"default.cfg"):
		self.cfgfile = cfg
		self.new = new_version
		wx.App.__init__(self,0)
		
	def OnInit(self):
		user = getpass.getuser()
		#if platform_name[0] != "Windows" :
		openframe = dialog.OpenFrame(None, -1, user, vers.ShortVersion)
		openframe.Centre()
		ret =  openframe.ShowModal()
		user = openframe.user
		openframe.Destroy()
		if ret == wx.ID_CANCEL :
			if global_logFile != None :
				global_logFile.close()
				if sys.platform == 'win32' :
					workingdir = os.getcwd()
					os.chdir(myPath)
					os.system('del ' + global_logName)
					os.chdir(workingdir)
				else :
					filename = myPath + global_logName
					os.system('rm \"'+ filename + '\"')
			return False

		winx = 460 
		winy = 600

		problemFlag = False 
		checklogFile = open(myTempPath + "success.txt", "r")
		line = checklogFile.readline()
		if len(line) == 0 : 
			problemFlag = True
		elif line[0:5] == "start" :
			problemFlag = True
		else :
			line = checklogFile.readline()
			winx = int(line)
			line = checklogFile.readline()
			winy = int(line)
			if (winx < 0) and (winy < 0) :
				winx = 460
				winy = 600 
		checklogFile.close()

		self.frame = MainFrame((winx, winy), user)
		self.SetTopWindow(self.frame)

		# This is for version difference
		#if self.new == True :
		#	self.frame.IMPORTRepository()

		if problemFlag == True :
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

		#if platform_name[0] != "Windows" : 
		#openframe.Hide()
		#openframe.Destroy()
		self.SetExitOnFrameDelete(False)

		return True


if __name__ == "__main__":

	new = False

	tempstamp = str(datetime.today())
	last = tempstamp.find(" ", 0)
	stamp = tempstamp[0:last] + "-"  

	if platform_name[0] == "Windows" :
		if os.access(User_Dir  + "\\Correlator\\", os.F_OK) == False :
			os.mkdir(User_Dir  + "\\Correlator\\")
			new = True
	else :
		if os.access(User_Dir  + "/Documents/Correlator/", os.F_OK) == False :
			os.mkdir(User_Dir  + "/Documents/Correlator/")
			new = True

	if os.access(myPath, os.F_OK) == False :
		os.mkdir(myPath)
		if new == True :
			new = False
		else : 
			new = True 

	if os.access(myPath+"tmp", os.F_OK) == False :
		os.mkdir(myPath + "tmp")
		cmd = "cp ./tmp/*.* " + myPath + "tmp"
		if platform_name[0] == "Windows" :
			cmd = "copy tmp\\*.* \"" + myTempPath + "\""
		os.system(cmd)
		cmd = "cp " + myTempPath + "/tmp/default.cfg " + myPath
		if platform_name[0] == "Windows" :
			cmd = "copy " + myTempPath + "\\tmp\\default.cfg \"" + myPath + "\""

		#print "[DEBUG] " + cmd
		os.system(cmd)

	if platform_name[0] == "Windows" :
		myTempPath = myPath + "tmp\\"
	else :
		myTempPath = myPath + "tmp/"
	
	if os.access(myTempPath+"success.txt", os.F_OK) == False :
		cmd = "cp ./tmp/*.* " + myTempPath
		if platform_name[0] == "Windows" :
			cmd = "copy tmp\\*.* \"" + myTempPath + "\""
		os.system(cmd)

	if os.access(myPath + '/log/', os.F_OK) == False :
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
	if platform_name[0] == "Windows" :
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
