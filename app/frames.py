#!/usr/bin/env python

## For Mac-OSX
#/usr/bin/env pythonw

#from wxPython.wx import *
import platform
platform_name = platform.uname()

import random, sys, os, re, time, ConfigParser, string
from datetime import datetime
import math

import numpy.oldnumeric as _Numeric
import numpy
import warnings
warnings.simplefilter('ignore', numpy.RankWarning) # stifle RankWarnings when computing growth rate

import wx 
import wx.grid
from wx.lib import plot

from importManager import py_correlator

import canvas
import dialog
import splice

def opj(path):
	"""Convert paths to the platform-specific separator"""
	return apply(os.path.join, tuple(path.split('/')))


class TopMenuFrame(wx.Frame):
	def __init__(self, parent):
		wx.Frame.__init__(self, parent, -1, "Tool Bar",
						 wx.Point(20,100),
						 style=wx.DEFAULT_DIALOG_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE | wx.FRAME_FLOAT_ON_PARENT | wx.FRAME_TOOL_WINDOW)

		self.parent = parent
		
		frameSizer = wx.BoxSizer(wx.VERTICAL)
		
		vbox = wx.FlexGridSizer(9, 1, vgap=5)
		self.dbbtn = wx.Button(self, -1, "Go to Display")
		self.Bind(wx.EVT_BUTTON, self.OnDB, self.dbbtn)
		vbox.Add(self.dbbtn, 0, wx.EXPAND)

		savebtn = wx.Button(self, -1, "Save")
		self.Bind(wx.EVT_BUTTON, self.OnSAVE, savebtn)
		vbox.Add(savebtn, 0, wx.EXPAND)

		self.cntbtn = wx.Button(self, -1, "Connect to Corelyzer")
		self.Bind(wx.EVT_BUTTON, self.OnCONNECT, self.cntbtn)
		vbox.Add(self.cntbtn, 0, wx.EXPAND)

		self.drawingbtn = wx.Button(self, -1, "Discrete Points")
		self.Bind(wx.EVT_BUTTON, self.OnDRAWMODE, self.drawingbtn)
		vbox.Add(self.drawingbtn, 0, wx.EXPAND)
		
		self.compositeBtn = wx.Button(self, -1, "Go to Composite")
		vbox.Add(self.compositeBtn, 0, wx.EXPAND)
		self.Bind(wx.EVT_BUTTON, self.OnComposite, self.compositeBtn)
		
		self.spliceBtn = wx.Button(self, -1, "Go to Splice")
		vbox.Add(self.spliceBtn, 0, wx.EXPAND)
		self.Bind(wx.EVT_BUTTON, self.OnSplice, self.spliceBtn)

		self.filterBtn = wx.Button(self, -1, "Go to Filters")
		vbox.Add(self.filterBtn, 0, wx.EXPAND)
		self.Bind(wx.EVT_BUTTON, self.OnFilter, self.filterBtn)
		
		self.prefsBtn = wx.Button(self, -1, "Go to Display Prefs")
		vbox.Add(self.prefsBtn, 0, wx.EXPAND)
		self.Bind(wx.EVT_BUTTON, self.OnPrefs, self.prefsBtn)

		exitbtn = wx.Button(self, -1, "Exit Correlator")
		self.Bind(wx.EVT_BUTTON, self.OnEXIT, exitbtn)
		vbox.Add(exitbtn, 0, wx.EXPAND)

		frameSizer.Add(vbox, 1, wx.EXPAND | wx.ALL, 2)
		self.SetSizerAndFit(frameSizer)

		self.SetBackgroundColour(wx.Colour(255, 255, 255))
		wx.EVT_CLOSE(self, self.OnHide)

	def OnHide(self, event):
		self.parent.optPanel.tool.SetValue(False)
		self.Show(False)
		self.parent.mitool.Check(False)
		self.parent.Window.SetFocusFromKbd()

	def OnNEW(self, event):
		if self.parent.CurrentDir != '' :
			if self.parent.CHECK_CHANGES() == True :
				ret = self.parent.OnShowMessage("About", "Do you want to save changes?", 2)		
				if ret == wx.ID_OK :
					self.OnSAVE(event)
		if self.parent.client != None and self.parent.Window.HoleData != [] :
			#ret = py_correlator.getData(18)
			#self.parent.ParseSectionSend(ret, "delete_section")
			self.parent.client.send("delete_all\n")

		self.parent.CurrentDir = ''

		self.parent.compositePanel.saveButton.Enable(False)
		self.parent.splicePanel.saveButton.Enable(False)
		self.parent.eldPanel.saveButton.Enable(False)
		self.parent.autoPanel.saveButton.Enable(False)
		self.parent.INIT_CHANGES()

		self.parent.OnNewData(None)
		self.parent.Window.SetFocusFromKbd()


	def OnDRAWMODE(self, event):
		if self.parent.Window.DiscretePlotMode == 0 :
			self.parent.Window.DiscretePlotMode = 1 
			self.drawingbtn.SetLabel("Continuous Points")
		else :
			self.parent.Window.DiscretePlotMode = 0
			self.drawingbtn.SetLabel("Discrete Points")
		if self.parent.dataFrame.IsShown() == False :
			self.parent.Window.UpdateDrawing()

	def OnCONNECT(self, event):
		ret = self.parent.OnCONNECTION(event)
		if ret == True :
			self.cntbtn.SetLabel("Close Connection")
		else :
			self.cntbtn.SetLabel("Connect to Corelyzer")

	def OnDB(self, event):
		if self.dbbtn.GetLabel() == "Go to Data Manager" :
			self.parent.ShowDataManager()
		else:
			self.parent.ShowDisplay()

	def OnSAVE(self, event):
		if self.parent.CurrentDir == '' : 
			self.parent.OnShowMessage("Error", "There is no data loaded", 1)
			return

		savedialog = dialog.SaveTableDialog(None, -1, self.parent.affineManager.isDirty(), self.parent.spliceManager.isDirty())
		savedialog.Centre()
		ret = savedialog.ShowModal()
		
		eld_flag = savedialog.eldCheck.GetValue()
		age_flag =  savedialog.ageCheck.GetValue()
		series_flag = savedialog.seriesCheck.GetValue()

		if ret == wx.ID_CANCEL :
			return
		
		# affine
		affine_filename = ""
		if savedialog.affineCheck.GetValue():
			affine_filename = self.parent.dataFrame.Add_TABLE("AFFINE" , "affine", savedialog.affineUpdate.GetValue(), False, "")
			self.parent.affineManager.save(affine_filename)
			#py_correlator.saveAttributeFile(affine_filename, 1)

			s = "Save Affine Table: " + affine_filename + "\n\n"
			self.parent.logFileptr.write(s)
			self.parent.AffineChange = False  
		# splice
		if savedialog.spliceCheck.GetValue():
			if self.parent.spliceManager.count() > 0:
				filename = self.parent.dataFrame.Add_TABLE("SPLICE" , "splice", savedialog.spliceUpdate.GetValue(), False, "")
				self.parent.spliceManager.save(filename)

				s = "Save Splice Table: " + filename + "\n\n"
				self.parent.logFileptr.write(s)
				self.parent.SpliceChange = False  

		if eld_flag == True :
			if self.parent.Window.LogData != [] :
				filename = self.parent.dataFrame.Add_TABLE("ELD" , "eld", savedialog.eldUpdate.GetValue(), False, "")
				py_correlator.saveAttributeFile(filename, 4)

				s = "Save ELD Table: " + filename + "\n\n"
				self.parent.logFileptr.write(s)
				self.parent.EldChange = False  

		if age_flag == True :
			filename = self.parent.dataFrame.OnSAVE_AGES(savedialog.ageUpdate.GetValue(), False)
			s = "Save Age/Depth: " + filename + "\n\n"
			self.parent.logFileptr.write(s)
			self.parent.AgeChange = False  

		if series_flag == True :
			if self.parent.Window.AgeDataList != [] :
				filename = self.parent.dataFrame.OnSAVE_SERIES(savedialog.seriesUpdate.GetValue(), False)
				s = "Save Age Model : " + filename + "\n\n"
				self.parent.logFileptr.write(s)
				self.parent.TimeChange = False  

		savedialog.Destroy()
		self.parent.OnShowMessage("Information", "Successfully Saved", 1)

		#self.parent.Window.SetFocusFromKbd()


	def OnSPLICE(self, event):
		if self.parent.Window.ShowSplice == True :
			self.parent.Window.ShowSplice = False
		else :
			self.parent.Window.ShowSplice = True 
		self.parent.Window.UpdateDrawing()
		self.parent.Window.SetFocusFromKbd()

	def OnLOG(self, event):
		if self.parent.Window.ShowLog == True :
			self.parent.Window.ShowLog = False
		else :
			self.parent.Window.ShowLog = True 
		self.parent.Window.UpdateDrawing()
		self.parent.Window.SetFocusFromKbd()

	def OnSTRAT(self, event):
		if self.parent.Window.ShowStrat == True :
			self.parent.Window.ShowStrat = False
		else :
			self.parent.Window.ShowStrat = True 
		self.parent.Window.UpdateDrawing()
		self.parent.Window.SetFocusFromKbd()

	def OnComposite(self, event):
		self.parent.Window.sideNote.SetSelection(1)
	
	def OnSplice(self, event):
		self.parent.Window.sideNote.SetSelection(2)

	def OnFilter(self, event):
		self.parent.Window.sideNote.SetSelection(5)
	
	def OnPrefs(self, event):
		self.parent.Window.sideNote.SetSelection(6)

	def OnEXIT(self, event):
		self.parent.OnExitButton(event)

class ProgressFrame(wx.Frame):
	def __init__(self, parent, max):
		wx.Frame.__init__(self, parent, -1, "Progress",
						 wx.Point(0,0),
						 size=(310,150),
						 style= wx.DEFAULT_DIALOG_STYLE |wx.NO_FULL_REPAINT_ON_RESIZE |wx.STAY_ON_TOP)

		self.parent = parent
		self.max = max
		self.interrupted = False 
		self.gauge = wx.Gauge(self, -1, max, (30, 30), size=(250, 50))
		self.btn = wx.Button(self, -1, "Done", (95, 70),size=(120,30))
		self.btn.Enable(False)
		self.parent.Enable(False)
		self.parent.Update()

		self.Centre()
		self.Show(True)
		self.Bind(wx.EVT_BUTTON, self.OnOk, self.btn)

	def SetProgress(self, value):
		self.gauge.SetValue(value)
		if value == self.max :
			self.btn.Enable(True)

	def OnOk(self, event):
		self.Show(False)
		self.parent.Enable(True)
		self.Destroy()

# 9/21/2013 brg: Extend wx.plot to exclude items with no legend text
# from the legend. This way we can add lines connecting offset
# points in Growth Rate graph without those lines ending up as random
# unlabeled entries in the legend. Pulled code straight from plot.py
# on the wxPython trunk.
class BetterLegendPlotCanvas(plot.PlotCanvas):
	def __init__(self, parent):
		plot.PlotCanvas.__init__(self, parent)
	
	def _drawLegend(self, dc, graphics, rhsW, topH, legendBoxWH, legendSymExt, legendTextExt):
		"""Draws legend symbols and text"""
		# top right hand corner of graph box is ref corner
		trhc= self.plotbox_origin+ (self.plotbox_size-[rhsW,topH])*[1,-1]
		legendLHS= .091* legendBoxWH[0] # border space between legend sym and graph box
		lineHeight= max(legendSymExt[1], legendTextExt[1]) * 1.1 #1.1 used as space between lines
		dc.SetFont(self._getFont(self._fontSizeLegend))
		legendItemsDrawn = 0 # brg added to remove space for undrawn legend items
		for i in range(len(graphics)):
			o = graphics[i]
			if o.getLegend() == '': # don't add items with no legend text to the legend!
				continue
			#s= i*lineHeight
			s = legendItemsDrawn * lineHeight
			if isinstance(o,plot.PolyMarker):
				# draw marker with legend
				pnt= (trhc[0]+legendLHS+legendSymExt[0]/2., trhc[1]+s+lineHeight/2.)
				o.draw(dc, self.printerScale, coord=_Numeric.array([pnt]))
			elif isinstance(o,plot.PolyLine):
				# draw line with legend
				pnt1= (trhc[0]+legendLHS, trhc[1]+s+lineHeight/2.)
				pnt2= (trhc[0]+legendLHS+legendSymExt[0], trhc[1]+s+lineHeight/2.)
				o.draw(dc, self.printerScale, coord=_Numeric.array([pnt1,pnt2]))
			else:
				raise TypeError, "object is neither PolyMarker or PolyLine instance"
			# draw legend txt
			pnt= (trhc[0]+legendLHS+legendSymExt[0]+5*self._pointSize[0], trhc[1]+s+lineHeight/2.-legendTextExt[1]/2)
			dc.DrawText(o.getLegend(),pnt[0],pnt[1])
			legendItemsDrawn += 1
		dc.SetFont(self._getFont(self._fontSizeAxis)) # reset

# convenience class to maintain data to display on mouseover of growth rate graph
# brgtodo 9/2/2014: What's the right way to do this? Passing around tuples is easy
# but indexing into them makes for hard-to-read code. Using a dictionary would get
# past that issue, but something about a class seems more "correct" to me, probably
# due to heavy OOP background.
class HoverData():
	def __init__(self, mbsf, mcd, hole, core, growthRate):
		self.mbsf = mbsf
		self.mcd = mcd
		self.hole = hole
		self.core = core
		self.growthRate = growthRate


class GrowthRatePlotCanvas(BetterLegendPlotCanvas):
	def __init__(self, parent, statusText):
		BetterLegendPlotCanvas.__init__(self, parent)
		
		self.growthPlotData = []
		self.growthRateLines = []
		self.hoverData = []
		self.minMcd = 99999.9
		self.maxMcd = -99999.9
		self.maxMbsf = -99999.9
		self.statusText = statusText
		
		self.plotMin = 99999.9

		self.SetEnablePointLabel(True)
		self.SetPointLabelFunc(self.MouseOverPoint)
		self.parent.Bind(wx.EVT_MOTION, self.OnMotion)

	def OnMotion(self, event):
		if self.GetEnablePointLabel() == True:
			dlst = self.GetClosestPoint( self._getXY(event), pointScaled = True)
			if dlst != []:
				curveNum, legend, pIndex, pointXY, scaledXY, distance = dlst
				mDataDict= {"pointXY":pointXY}
				self.UpdatePointLabel(mDataDict)
		event.Skip() #go to next handler
	
	def MouseOverPoint(self, dc, mDataDict):
		minDist = None
		closest = None
		nx = mDataDict["pointXY"][0]
		ny = mDataDict["pointXY"][1]
		for hd in self.hoverData:
			x = hd.mbsf
			y = hd.mcd
			dist = math.sqrt(math.pow(nx - x, 2) + math.pow(ny - y, 2))
			if minDist is None or dist < minDist:
				minDist = dist
				closest = hd
			
		growthRate = round(closest.growthRate[0], 3) if not math.isnan(closest.growthRate[0]) else "undefined"		
		self.statusText.SetLabel("{}{}: Growth rate {}".format(closest.hole, closest.core, growthRate))
	
	# scrollMax = max scrollable depth in GUI
	def UpdatePlot(self, holeData, startDepth, endDepth, scrollMax):
		self._updateData(holeData, startDepth, endDepth)
		if len(self.growthRateLines) == 0:
			return

		#tenPercentLine = plot.PolyLine([(0,0),(self.maxMbsfDepth, self.maxMbsfDepth * 1.1)], legend='10%', colour='black', width=2)
		# order matters: draw 10% line, then data lines, then data markers/points
		#self.growthPlotData = [tenPercentLine] + self.growthPlotData
		self.growthPlotData = self.growthRateLines + self.growthPlotData

		gc = plot.PlotGraphics(self.growthPlotData, 'Growth Rate', 'CSF', 'CCSF')
		
		xmin = self.plotMin
		xmax = min(endDepth, self.maxMbsf + 5)
		if xmax > scrollMax:
			xmax = scrollMax
		if xmin > xmax:
			xmin = 0
		xax = (xmin, xmax)

		yax = (round(self.minMcd, 0) - 5, round(self.maxMcd, 0) + 5)
		self.Draw(gc, xAxis = xax, yAxis = yax)
		self.growthPlotData = []

	def _updateData(self, holeData, startDepth, endDepth):
		minMcd = 10000.0
		maxMcd = -10000.0
		maxMbsf = -10000.0
		self.growthRateLines = []
		self.hoverData = []
		self.plotMin = 99999.9
		holeNum = 0
		holeSet = set([]) # avoid duplicate holes with different datatypes
		holeMarker = ['circle', 'square', 'triangle', 'plus', 'triangle_down']
		holeColor = ['red', 'blue', 'green', 'black', 'orange']
		for hole in holeData:
			holeName = hole[0][0][7]
			if holeName not in holeSet:
				holeSet.add(holeName)
				growthRatePoints = []
				mbsfVals = []
				mcdVals = []

				# brg 10/14/2013: hole[0][0][8] indicates the number of cores in the hole, but this isn't
				# always reliable - make sure we don't overrun the list of cores given such errant data
				numCores = min(hole[0][0][8], len(hole[0]) - 1)

				for core in range(numCores):
					#print "Core Info: {}".format(hole[0][core + 1])
					offset = hole[0][core + 1][5]
					topSectionMcd = hole[0][core + 1][9][0]
					mbsfDepth = topSectionMcd - offset
					
					# compute core length in horrible way: bottom data coord's depth - top data coord's depth
					coreLength = hole[0][core + 1][10][-1][0] - hole[0][core + 1][10][0][0]
					coreEnd = topSectionMcd + coreLength
					coreName = hole[0][core + 1][0]

					# determine ranges for plotting purposes
					if mbsfDepth > maxMbsf:
						maxMbsf = mbsfDepth
					
					inRange = False
					if mbsfDepth >= startDepth and mbsfDepth <= endDepth:
						inRange = True
						if topSectionMcd < minMcd:
							minMcd = topSectionMcd
						if topSectionMcd > maxMcd:
							maxMcd = topSectionMcd
					
					if not inRange and (coreEnd >= startDepth and coreEnd <= endDepth) or (mbsfDepth < startDepth and coreEnd >= endDepth):
						self.plotMin = min(self.plotMin, mbsfDepth)
						if topSectionMcd < minMcd:
							minMcd = topSectionMcd
						if topSectionMcd > maxMcd:
							maxMcd = topSectionMcd
					
					offsetMbsfPair = (mbsfDepth, topSectionMcd)
					growthRatePoints.append(offsetMbsfPair)
					mbsfVals.append(mbsfDepth)
					mcdVals.append(topSectionMcd)

					# track point data for use in point labeling on mouseover
					growthRate = numpy.polyfit(mbsfVals, mcdVals, 1)
					pointData = HoverData(mbsfDepth, topSectionMcd, holeName, coreName, growthRate)
					self.hoverData.append(pointData)

				self.growthPlotData.append(plot.PolyMarker(growthRatePoints, marker=holeMarker[holeNum],
														 legend=hole[0][0][7], colour=holeColor[holeNum], size=1.5))

				if len(growthRatePoints) == 1: # ensure we have at least two points
					growthRatePoints = [(0,0)] + growthRatePoints

				self.growthRateLines.append(plot.PolyLine(growthRatePoints, colour=holeColor[holeNum], width=1))
				holeNum = (holeNum + 1) % len(holeMarker) # make sure we don't overrun marker/color lists

		if minMcd > maxMcd:
			minMcd = startDepth
			maxMcd = endDepth
		self.minMcd = minMcd
		self.maxMcd = maxMcd
		self.maxMbsf = maxMbsf


class CompositePanel():
	def __init__(self, parent, mainPanel):
		self.mainPanel = mainPanel
		self.parent = parent
		self.polyline_list =[]
		self.growthPlotData = []
		self.addItemsInFrame()
		self.bestOffset = 0

	def addItemsInFrame(self):
		self.plotNote = wx.Notebook(self.mainPanel, -1, style=wx.NB_TOP | wx.NB_MULTILINE)

		# Correlation/Evaluation graph panel
		# brgtodo 9/6/2014: UI creation duplicated across Composite, Splice and ELD panels: consolidate
		self.crPanel = wx.Panel(self.plotNote, -1)
		self.crPanel.SetSizer(wx.BoxSizer(wx.VERTICAL))
		self.corrPlotCanvas = BetterLegendPlotCanvas(self.crPanel)

		self.corrPlotCanvas.SetEnableGrid(True)
		self.corrPlotCanvas.SetEnableTitle(False)
		self.corrPlotCanvas.SetBackgroundColour("White")
		self.corrPlotCanvas.Show(True)
		
		crSubPanel = wx.Panel(self.crPanel, -1)
		crSubPanel.SetSizer(wx.BoxSizer(wx.HORIZONTAL))
		bmp = wx.Bitmap("icons/sprocket.png")
		crSettingsBtn = wx.BitmapButton(crSubPanel, -1, bmp)
		self.crText = wx.StaticText(crSubPanel, -1, "Step: 0.135 | Window: 1.0 | Lead/Lag: 1.0")
		crFont = self.crText.GetFont()
		crFont.SetPointSize(10)
		self.crText.SetFont(crFont)
		crSubPanel.GetSizer().Add(self.crText, 1, wx.ALIGN_CENTER_VERTICAL)
		crSubPanel.GetSizer().Add(crSettingsBtn, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
		
		self.crPanel.GetSizer().Add(self.corrPlotCanvas, 1, wx.EXPAND)
		self.crPanel.GetSizer().Add(crSubPanel, 0, wx.EXPAND)
		
		self.crPanel.Bind(wx.EVT_BUTTON, self.OnEvalSettings, crSettingsBtn)

		# Growth Rate graph panel
		self.grPanel = wx.Panel(self.plotNote, -1)
		self.grPanel.SetSizer(wx.BoxSizer(wx.VERTICAL))

		grSubPanel = wx.Panel(self.grPanel, -1)
		gpSettingsBtn = wx.BitmapButton(grSubPanel, -1, bmp)
		self.grText = wx.StaticText(grSubPanel, -1, "[hover to see point data]")

		self.growthPlotCanvas = GrowthRatePlotCanvas(self.grPanel, self.grText)
		self.growthPlotCanvas.SetEnableGrid(True)
		self.growthPlotCanvas.SetEnableTitle(False)
		self.growthPlotCanvas.SetEnableLegend(True)
		self.growthPlotCanvas.SetFontSizeLegend(10)
		self.growthPlotCanvas.SetBackgroundColour('White')
		self.growthPlotCanvas.Show(True)

		self.grPanel.GetSizer().Add(self.growthPlotCanvas, 1, wx.EXPAND)

		grSubPanel.SetSizer(wx.BoxSizer(wx.HORIZONTAL))
		grSubPanel.GetSizer().Add(self.grText, 1, wx.ALIGN_CENTER_VERTICAL)
		grSubPanel.GetSizer().Add(gpSettingsBtn, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
		self.grPanel.GetSizer().Add(grSubPanel, 0, wx.EXPAND)
		
		# Affine Table panel
		atPanel = wx.Panel(self.plotNote, -1)
		atsz = wx.BoxSizer(wx.VERTICAL)
		self.table = wx.grid.Grid(atPanel, -1)
		self.table.SetRowLabelSize(0) # hide row headers
		self.table.DisableDragRowSize()
		self.table.EnableEditing(False)
		self.table.CreateGrid(numRows=0, numCols=3)
		for colidx, label in enumerate(["Core", "Shift", "Type"]):
			self.table.SetColLabelValue(colidx, label)
		self.table.SetSelectionMode(wx.grid.Grid.SelectRows)
		atsz.Add(self.table, 1, wx.EXPAND)
		atPanel.SetSizer(atsz)
		self.atPanel = atPanel		

		self.plotNote.AddPage(self.crPanel, "Evaluation")
		self.plotNote.AddPage(self.grPanel, "Growth Rate")
		self.plotNote.AddPage(self.atPanel, "Shifts")
		
		self.grPanel.Bind(wx.EVT_BUTTON, self.OnGrowthSettings, gpSettingsBtn)

		# add Notebook to main panel
		self.plotNote.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnSelectPlotNote)
		self.plotNote.SetSelection(1)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(self.plotNote, 3, wx.EXPAND | wx.ALL, 5)

		# update drawings
		xdata = [ (-self.parent.leadLag, 0), (self.parent.leadLag, 0) ]
		self.xaxes = plot.PolyLine(xdata, legend='', colour='black', width =2)
		ydata = [ (0, -1),( 0, 1) ]
		self.yaxes = plot.PolyLine(ydata, legend='', colour='black', width =2)
		
		self.OnUpdatePlots()

		# Panel 3
		panel3 = wx.Panel(self.mainPanel, -1)

		sizer31 = wx.StaticBoxSizer(wx.StaticBox(panel3, -1, 'TIE Shift Options'), orient=wx.VERTICAL)
		self.applyCore = wx.Choice(panel3, -1, choices=["This core and all related cores below", "This core only"])
		self.applyCore.SetSelection(0)
		sizer31.Add(self.applyCore, 0, wx.EXPAND | wx.BOTTOM, 5)
		
		# type depth panel
		tdpSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.actionType = wx.Choice(panel3, -1, choices=["To tie", "To best correlation", "By given amount (m):"])
		self.actionType.SetSelection(0)
		self.depthField = wx.TextCtrl(panel3, -1)
		tdpSizer.Add(self.actionType, 0, wx.RIGHT, 5)
		tdpSizer.Add(self.depthField)
		sizer31.Add(tdpSizer, 0, wx.EXPAND | wx.TOP, 5)
		
		self.mainPanel.Bind(wx.EVT_CHOICE, self.UpdateDepthField, self.actionType)
		
		commentSizer = wx.BoxSizer(wx.HORIZONTAL)
		commentSizer.Add(wx.StaticText(panel3, -1, "Comment:"), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)
		self.comment = dialog.CommentTextCtrl(panel3, -1)
		commentSizer.Add(self.comment, 1)
		sizer31.Add(commentSizer, 0, wx.EXPAND | wx.TOP, 10)
		
		btnSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.adjustButton = wx.Button(panel3, -1, "Apply Shift")
		self.clearButton = wx.Button(panel3, -1, "Clear Tie")
		btnSizer.Add(self.clearButton, 1, wx.RIGHT, 5)
		btnSizer.Add(self.adjustButton, 1, 5)
		sizer31.AddStretchSpacer()
		sizer31.Add(btnSizer, 0, wx.EXPAND | wx.TOP, 10)

		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnClearTie, self.clearButton)
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnAdjust, self.adjustButton)
		
		panel3.SetSizer(sizer31)
		vbox.Add(panel3, 0, wx.EXPAND)
		
		# Project... button
		projectPanel = wx.Panel(self.mainPanel, -1)
		setSizer = wx.StaticBoxSizer(wx.StaticBox(projectPanel, -1, "SET Dialog"), orient=wx.VERTICAL)
		self.projectButton = wx.Button(projectPanel, -1, "SET By Growth Rate or %...")
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnProject, self.projectButton)
		setSizer.Add(self.projectButton, 1, wx.EXPAND)
		projectPanel.SetSizer(setSizer)
		vbox.Add(projectPanel, 0, wx.EXPAND)

		# undo panel
		undoPanel = wx.Panel(self.mainPanel, -1)
		sizer32 = wx.StaticBoxSizer(wx.StaticBox(undoPanel, -1, 'Undo'), orient=wx.VERTICAL)
		self.undoButton = wx.Button(undoPanel, -1, "Undo Previous Shift")#, size=undoButtonSize)
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnUndoAffineShift, self.undoButton)
		self.undoButton.Enable(False)
		sizer32.Add(self.undoButton, 0, wx.EXPAND)

		undoPanel.SetSizer(sizer32)
		vbox.Add(undoPanel, 0, wx.EXPAND)

		buttonsize = 130
		if platform_name[0] == "Windows" :
			buttonsize = 145
			
		vbox.Add(wx.StaticText(self.mainPanel, -1, '* Right-click tie for context menu', (5, 5)), 0, wx.BOTTOM, 5)

		self.saveButton = wx.Button(self.mainPanel, -1, "Save Affine Table", size =(150, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnSAVE, self.saveButton)
		vbox.Add(self.saveButton, 0, wx.ALIGN_CENTER_VERTICAL)
		self.saveButton.Enable(False)

		self.mainPanel.SetSizer(vbox)
		
		self.UpdateDepthField()

	def OnInitUI(self):
		self.adjustButton.Enable(False)
		self.clearButton.Enable(False)
		self.undoButton.Enable(False)
		
	def UpdateDepthField(self, evt=None):
		enableDepth = (self.actionType.GetSelection() == 2) # "By given amount"
		self.depthField.Enable(enableDepth)

	def OnSAVE(self, event):
		dlg = dialog.Message3Button(self.parent, "Create new affine file?", yesLabel="Create New", okLabel="Update Existing", cancelLabel="Cancel")
		ret = dlg.ShowModal()
		dlg.Destroy()
		if ret == wx.ID_OK or ret == wx.ID_YES :
			updateExisting = ret == wx.ID_OK
			filename = self.parent.dataFrame.Add_TABLE("AFFINE", "affine", updateExisting, False, "")
			print "Save: updateExisting = {}, filename = {}".format(updateExisting, filename)
			self.parent.affineManager.save(filename)

	def OnButtonEnable(self, opt, enable):
		if opt == 0 : 
			self.adjustButton.Enable(enable)
			self.clearButton.Enable(enable)
			#self.aboveButton.Enable(enable)
		elif opt == 1:
			self.undoButton.Enable(enable)
		else :
			self.clearButton.Enable(enable)

	def OnDismiss(self, evt):
		self.Hide()

	def OnAdjust(self, evt):
		adjustCoreOnly = (self.applyCore.GetSelection() == 1) # 0 = this core and all below, 1 = this core only
		self.parent.OnAdjustCore(adjustCoreOnly, self.GetShiftType())

		self.parent.Window.activeTie = -1
		self.UpdateGrowthPlot()

	def OnClearTie(self, evt):
		self.parent.Window.OnClearTies(0)
		self.OnButtonEnable(0, False)
		self.parent.Window.activeTie = -1

	def OnUndoAffineShift(self, evt):
		self.parent.OnUndoAffineShift()

	def OnEvalSettings(self, evt):
		dlg = dialog.CorrParamsDialog(self.plotNote, self.parent.minDepthStep, self.parent.depthStep, self.parent.winLength, self.parent.leadLag)
		pos = self.crText.GetScreenPositionTuple()
		dlg.SetPosition(pos)
		if dlg.ShowModal() == wx.ID_OK:
			self.parent.OnEvalSetup(dlg.outDepthStep, dlg.outWinLength, dlg.outLeadLag)
			self.parent.OnUpdateGraphSetup(1)
			if len(self.parent.Window.TieData) > 0 :
				self.parent.Window.OnUpdateTie(1)
				
	def OnGrowthSettings(self, evt):
		min = self.parent.optPanel.min_depth.GetValue()
		max = self.parent.optPanel.max_depth.GetValue()
		dlg = dialog.DepthRangeDialog(self.plotNote, min, max)
		pos = self.grText.GetScreenPositionTuple()
		dlg.SetPosition(pos)
		if dlg.ShowModal() == wx.ID_OK:
			self.parent.optPanel.depthmax = dlg.outMax	# update mirrored prefs GUI (brgtodo 9/6/2014 gross)
			self.parent.optPanel.min_depth.SetValue(str(dlg.outMin))
			self.parent.optPanel.max_depth.SetValue(str(dlg.outMax))
			self.parent.optPanel.slider2.SetValue(1)
			self.parent.OnUpdateDepthRange(dlg.outMin, dlg.outMax)

	def OnProject(self, evt):
		dlg = dialog.ProjectDialog(self.parent)
		dlg.Centre(wx.CENTER_ON_SCREEN)
		result = dlg.ShowModal()
		if result == wx.ID_OK:
			if dlg.coreAndBelow.GetValue(): # SET current core and below
				isRate = dlg.outRate is not None
				value = dlg.outRate if isRate else dlg.outOffset
				coreList = dlg.outCoreList
				self.parent.affineManager.setAll(dlg.outHole, coreList, value, isRate, dlg.outType, dlg.outComment)
			else:
				self.parent.affineManager.set(dlg.outHole, dlg.outCore, dlg.outOffset, dlg.outType, dlg.outComment)

			self.parent.AffineChange = True
			#py_correlator.saveAttributeFile(self.parent.CurrentDir + 'tmp.affine.table', 1)

			# todo: notify Corelyzer of change
			#self.parent.ShiftSectionSend(ciA.hole, ciA.holeCore, shift, opId)

			if self.parent.showReportPanel == 1:
				self.parent.OnUpdateReport()

			self.parent.UpdateData()
			self.parent.UpdateStratData()
			
			if dlg.outCore == "All":
				self.parent.Window.UpdateShiftedSpliceIntervals(dlg.outHole, '1', True)
			else:
				self.parent.Window.UpdateShiftedSpliceIntervals(dlg.outHole, dlg.outCore, False)
			self.parent.Window.UpdateDrawing()

	def OnUpdateDepth(self, data):
		depth = int(10000.0 * float(data)) / 10000.0
		self.depthField.SetValue(str(depth))

	# brgtodo 9/4/2014: only called from this module, and always to set "empty" data:
	# merge f'ns and add default params?
	def OnUpdateData(self, data, bestdata, best):
		self.bestOffset = best 
		line = plot.PolyLine(data, legend='', colour='red', width =2) 
		self.polyline_list.append(line)
		if bestdata != [] :
			bestline = plot.PolyLine(bestdata, legend='', colour='blue', width =5) 
			self.polyline_list.append(bestline)

	# 9/18/2013 brg: Identical to OnUpdateData() above... and in SplicePanel
	def OnAddFirstData(self, data, bestdata, best):
		self.bestOffset = best 
		line = plot.PolyLine(data, legend='', colour='red', width =2) 
		self.polyline_list.append(line)
		if bestdata != [] : 
			bestline = plot.PolyLine(bestdata, legend='', colour='blue', width =5) 
			self.polyline_list.append(bestline)

	def OnAddData(self, data):
		line = plot.PolyLine(data, legend='', colour='grey', width =2) 
		self.polyline_list.append(line)

	def OnSelectPlotNote(self, event):
		self.crPanel.Hide()
		self.grPanel.Hide()	
		self.atPanel.Hide()
		if event.GetSelection() == 0:
			self.crPanel.Show()
		elif event.GetSelection() == 1:
			self.UpdateGrowthPlot()
			self.grPanel.Show()
		elif event.GetSelection() == 2:
			self.atPanel.Show()

	def OnUpdatePlots(self):
		self.UpdateEvalPlot()
		self.UpdateGrowthPlot()
		self.UpdateAffineTable()
	
	def UpdateGrowthPlot(self):
		# 9/18/2013 brg: Was unable to get Window attribute on init without adding this
		# hasattr call. Unclear why - its (Window is an instance of DataCanvas)
		# lone init() method, where Window is initialized, is called before this,
		# or so it would seem. Interestingly, other attributes declared beneath
		# Window in DataCanvas.init() were also unavailable. Funky.
		# 9/4/2014 brgtodo: init CompositePanel, etc after DataCanvas is complete - should solve this issue
		growthRateLines = []
		if hasattr(self.parent, 'Window'):
			win = self.parent.Window
			self.growthPlotCanvas.UpdatePlot(win.HoleData, win.rulerStartDepth, win.rulerEndDepth, self.parent.ScrollMax)
		else:
			return
		
	def UpdateEvalPlot(self):
		self.corrPlotCanvas.Clear()
		data = [(-self.parent.leadLag, 0), (0, 0), (self.parent.leadLag, 0)]
		self.OnUpdateData(data, [], 0)
		self.UpdateEvalStatus()
		self.OnUpdateDrawing()
		
	def UpdateAffineTable(self):
		affineRows = self.parent.affineManager.getAffineRows()
		
		if len(affineRows) > self.table.GetNumberRows():
			self.table.InsertRows(pos=0, numRows=len(affineRows))
		
		for rowIndex, ar in enumerate(affineRows):
			self.table.SetCellValue(rowIndex, 0, ar[0])
			self.table.SetCellValue(rowIndex, 1, ar[1])
			self.table.SetCellValue(rowIndex, 2, ar[2])
			
	def UpdateUndoButton(self):
		enable = self.parent.affineManager.canUndo()
		self.undoButton.Enable(enable)

	def UpdateEvalStatus(self):
		roundedDepthStep = int(10000.0 * float(self.parent.depthStep)) / 10000.0
		self.crText.SetLabel("Step: {} | Window: {} | Lead/Lag: {}".format(roundedDepthStep, self.parent.winLength, self.parent.leadLag))

	def OnUpdateDrawing(self):
		self.polyline_list.append(self.xaxes)
		self.polyline_list.append(self.yaxes)
		gc = plot.PlotGraphics(self.polyline_list, 'Evaluation Graph', 'depth Axis', 'coef Axis')
		self.corrPlotCanvas.Draw(gc, xAxis = (-self.parent.leadLag , self.parent.leadLag), yAxis = (-1, 1))
		self.polyline_list = []
		
	def GetDepthValue(self):
		return self.depthField.GetValue()
	
	def GetBestOffset(self):
		return self.bestOffset
	
	# shiftType values do not correspond to order in self.actionType list
	def GetShiftType(self):
		shiftType = 0 # To best correlation
		actionStr = self.actionType.GetStringSelection()
		if actionStr == "To tie":
			shiftType = 1
		elif actionStr == "By given amount (m):":
			shiftType = 2
		return shiftType
	
	def GetComment(self):
		return self.comment.GetValue()
		

class SplicePanel():
	def __init__(self, parent, mainPanel):
		self.mainPanel = mainPanel
		self.parent = parent
		self.leadLagValue = self.parent.leadLag
		self.appendflag = False
		self.appendall = 0
		self.polyline_list =[]
		self.addItemsInFrame()

	def addItemsInFrame(self):
		vbox_top = wx.BoxSizer(wx.VERTICAL)
		vbox = wx.BoxSizer(wx.VERTICAL)

		# Panel 2
		panel2 = wx.Panel(self.mainPanel, -1, style=wx.SIMPLE_BORDER)
		panel2.SetSizer(wx.BoxSizer(wx.VERTICAL))

		# Setup graph
		# parent, id, pos, size, style, name
		self.corrPlotCanvas = plot.PlotCanvas(panel2)

		self.corrPlotCanvas.SetEnableGrid( True )
		self.corrPlotCanvas.SetBackgroundColour("White")
		#self.corrPlotCanvas.Centre(wxBOTH)
		self.corrPlotCanvas.Show(True)
		
		crSubPanel = wx.Panel(panel2, -1)
		crSubPanel.SetSizer(wx.BoxSizer(wx.HORIZONTAL))
		bmp = wx.Bitmap("icons/sprocket.png")
		crSettingsBtn = wx.BitmapButton(crSubPanel, -1, bmp)
		self.crText = wx.StaticText(crSubPanel, -1, "Step: 0.135 | Window: 1.0 | Lead/Lag: 1.0")
		crFont = self.crText.GetFont()
		crFont.SetPointSize(10)
		self.crText.SetFont(crFont)
		crSubPanel.GetSizer().Add(self.crText, 1, wx.ALIGN_CENTER_VERTICAL)
		crSubPanel.GetSizer().Add(crSettingsBtn, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
		
		panel2.GetSizer().Add(self.corrPlotCanvas, 1, wx.EXPAND)
		panel2.GetSizer().Add(crSubPanel, 0, wx.EXPAND)
		
		panel2.Bind(wx.EVT_BUTTON, self.OnEvalSettings, crSettingsBtn)

		xdata = [ (-self.leadLagValue, 0),( 0, 0), (self.leadLagValue, 0) ]
		self.xaxes = plot.PolyLine(xdata, legend='', colour='black', width =2)
		ydata = [ (0, -1),( 0, 1) ]
		self.yaxes = plot.PolyLine(ydata, legend='', colour='black', width =2)

		data = [ (-self.leadLagValue, 0),( 0, 0), (self.leadLagValue, 0) ]
		self.OnUpdateData(data, [])
		self.OnUpdateDrawing()
		vbox.Add(panel2, 1, wx.TOP | wx.BOTTOM | wx.EXPAND, 5)

		# Panel 3
		panel3 = wx.Panel(self.mainPanel, -1)
		#hbox3 = wx.BoxSizer(wx.HORIZONTAL)

		hbox3 = wx.FlexGridSizer(3, 2)
		sizer34 = wx.StaticBoxSizer(wx.StaticBox(panel3, -1, 'Append mode'), orient=wx.VERTICAL)
		if platform_name[0] == "Windows" :		
			self.only = wx.RadioButton(panel3, -1, "Next core only        ", style=wx.RB_GROUP)
		else :
			self.only = wx.RadioButton(panel3, -1, "Next core only     ", style=wx.RB_GROUP)

		self.only.SetValue(True)
		sizer34.Add(self.only)
		self.all = wx.RadioButton(panel3, -1, "All below")
		sizer34.Add(self.all, 1, wx.TOP, 1)
		self.selected = wx.RadioButton(panel3, -1, "Selected core")
		sizer34.Add(self.selected, 1, wx.TOP, 1)

		#buttonsize = 110
		#if platform_name[0] == "Windows" :
		#	buttonsize = 125
		buttonsize = 120
		if platform_name[0] == "Windows" :
			buttonsize = 135

		self.appendButton = wx.Button(panel3, -1, "Append", size=(buttonsize, 20))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnAppend, self.appendButton)
		self.appendButton.Enable(False)
		sizer34.Add(self.appendButton, 1, wx.TOP, 5)
		hbox3.Add(sizer34, 1, wx.RIGHT, 10)

		sizer31_1 = wx.FlexGridSizer(3, 1)
		sizer31 = wx.StaticBoxSizer(wx.StaticBox(panel3, -1, 'Depth adjust (m)'), orient=wx.VERTICAL)
		self.depth = wx.TextCtrl(panel3, -1, "0.0", size=(buttonsize, 25), style=wx.SUNKEN_BORDER )
		self.depth.Enable(False)
		sizer31.Add(self.depth)
		sizer31_1.Add(sizer31)

		self.undoButton = wx.Button(panel3, -1, "Undo Last", size=(buttonsize, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnUndoSplice, self.undoButton)
		self.undoButton.Enable(False)
		sizer31_1.Add(self.undoButton, 1, wx.TOP, 3)
		self.clearButton = wx.Button(panel3, -1, "Clear Tie", size=(buttonsize, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnClearTie, self.clearButton)		
		self.clearButton.Enable(False)
		sizer31_1.Add(self.clearButton)
		hbox3.Add(sizer31_1)

		buttonsize = 120
		if platform_name[0] == "Windows" :
			buttonsize = 135
			
		sizer33 = wx.StaticBoxSizer(wx.StaticBox(panel3, -1, 'Splice mode'), orient=wx.VERTICAL)
		if platform_name[0] == "Windows" :		
			self.const = wx.RadioButton(panel3, -1, "Constrained		            ", style=wx.RB_GROUP)
		else :
			self.const = wx.RadioButton(panel3, -1, "Constrained		", style=wx.RB_GROUP)
						
		self.mainPanel.Bind(wx.EVT_RADIOBUTTON, self.OnChangeMode, self.const)
		self.const.SetValue(True)
		sizer33.Add(self.const)
		self.unconst = wx.RadioButton(panel3, -1, "Unconstrained")
		self.mainPanel.Bind(wx.EVT_RADIOBUTTON, self.OnChangeMode, self.unconst)
		sizer33.Add(self.unconst, 1, wx.TOP, 1)
		hbox3.Add(sizer33)

		sizer32 = wx.GridSizer(3, 1)
		self.spliceButton = wx.Button(panel3, -1, "Splice To Tie", size=(buttonsize, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnSplice, self.spliceButton)
		self.spliceButton.Enable(False)
		sizer32.Add(self.spliceButton)

		self.altButton = wx.Button(panel3, -1, "Alt. Splice", size =(buttonsize, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnCREATE_ALTSPLICE, self.altButton)
		self.altButton.Enable(False)
		sizer32.Add(self.altButton)

		self.newButton = wx.Button(panel3, -1, "New Splice", size =(buttonsize, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnNEWSPLICE, self.newButton)
		self.newButton.Enable(False)
		sizer32.Add(self.newButton)

		hbox3.Add(sizer32)

		panel3.SetSizer(hbox3)
		vbox.Add(panel3, 0, wx.TOP | wx.BOTTOM, 5)

		self.altClearBtn = wx.Button(self.mainPanel, -1, "Clear Alt. Splice", size =(150, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnCLEAR_ALTSPLICE, self.altClearBtn)
		vbox.Add(self.altClearBtn, 0, wx.BOTTOM, 5)
		self.altClearBtn.Enable(False)

		vbox.Add(wx.StaticText(self.mainPanel, -1, '*Sub menu for tie: On dot, right mouse button.', (5, 5)), 0, wx.BOTTOM, 9)

		self.saveButton = wx.Button(self.mainPanel, -1, "Save Splice Table", size =(150, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnSAVE, self.saveButton)
		vbox.Add(self.saveButton, 0, wx.ALIGN_CENTER_VERTICAL)
		self.saveButton.Enable(False)

		vbox_top.Add(vbox, 1, wx.LEFT, 5)
		self.mainPanel.SetSizer(vbox_top)

	def OnInitUI(self):
		self.spliceButton.Enable(False)
		self.clearButton.Enable(False)
		self.undoButton.Enable(False)
		self.appendButton.Enable(False)
		self.appendflag = False
		self.altClearBtn.Enable(False)
		self.appendall = 0

	def OnCLEAR_ALTSPLICE(self, event):
		self.altClearBtn.Enable(False)
		self.parent.Window.AltSpliceData = []
		for subr in self.parent.Window.range :
			if subr[0] == "altsplice" :
				self.parent.Window.range.remove(subr)
				break
		self.parent.Window.UpdateDrawing()


	def OnSAVE(self, event):
		#if self.parent.Window.SpliceData != [] :

		dlg = dialog.Message3Button(self.parent, "Do you want to create new splice file?")
		ret = dlg.ShowModal()
		dlg.Destroy()
		if ret == wx.ID_OK or ret == wx.ID_YES :
			flag = True
			if ret == wx.ID_YES :
				flag = False
			filename = self.parent.dataFrame.Add_TABLE("SPLICE" , "splice", flag, False, "")
			py_correlator.saveAttributeFile(filename, 2)

			s = "Save Splice Table: " + filename + "\n"
			self.parent.logFileptr.write(s)
			self.parent.autoPanel.SetCoreList(1, [])
			self.parent.OnShowMessage("Information", "Successfully Saved", 1)
			self.parent.SpliceChange = False 
		#else :
		#	self.parent.OnShowMessage("Error", "No data to save", 1)


	def OnNEWSPLICE(self, event):
		if self.parent.Window.SpliceData != [] :
			if self.parent.CHECK_CHANGES() == True :
				ret = self.parent.OnShowMessage("About", "Do you want to save?", 2)
				if ret == wx.ID_OK :
					self.OnSAVE(event)

			py_correlator.init_splice()

			ret = self.parent.OnShowMessage("About", "Do you want to keep the current splice?", 2)
			if ret == wx.ID_OK :
				type_range = None 
				alt_splice = None
				for subr in self.parent.Window.range :
					if subr[0] == "splice" :
						type_range = subr
					elif subr[0] == "altsplice" :
						alt_splice = subr

				newrange = "altsplice", type_range[1], type_range[2], type_range[3], 0, type_range[5]				
				if alt_splice != None :
					self.parent.Window.range.remove(alt_splice)
				self.parent.Window.range.append(newrange)

				self.parent.Window.AltSpliceData = []
				self.parent.Window.AltSpliceData = self.parent.Window.SpliceData
				self.altClearBtn.Enable(True)

			self.parent.Window.OnInit_SPLICE()
			self.parent.Window.UpdateDrawing()


	def OnCREATE_ALTSPLICE(self, event):
		dlg = dialog.AltSpliceDialog(self.parent)
		dlg.Centre()
		ret = dlg.ShowModal()
		selectedType =  dlg.selectedType
		selectedSplice = dlg.selectedSplice
		dlg.Destroy()
		if ret == wx.ID_OK :
			type_range = None 
			alt_splice = None
			for subr in self.parent.Window.range :
				if subr[0] == selectedType :
					type_range = subr
				elif subr[0] == "altsplice" :
					alt_splice = subr

			#newrange = "altsplice", type_range[1], type_range[2], type_range[3], 0, type_range[5]				
			#if alt_splice != None :
			#	self.parent.Window.range.remove(alt_splice)
			#self.parent.Window.range.append(newrange)

			path = self.parent.DBPath + 'db/' + self.parent.dataFrame.title  + '/'
			ret = py_correlator.loadAltSpliceFile(path + selectedSplice, selectedType)
			if ret == "" :
				self.parent.OnShowMessage("Error", "Could not create Splice Records", 1)
			else :
				newrange = "altsplice", type_range[1], type_range[2], type_range[3], 0, type_range[5]				
				self.parent.Window.altType = selectedType 
				if alt_splice != None :
					self.parent.Window.range.remove(alt_splice)
				self.parent.Window.range.append(newrange)

				self.parent.Window.AltSpliceData = []
				self.parent.ParseData(ret, self.parent.Window.AltSpliceData)
				self.altClearBtn.Enable(True)
				ret = ""
			self.parent.Window.UpdateDrawing()

			#print "[DEBUG] selected " + selectedSplice + " " + selectedType

	def OnButtonEnable(self, opt, enable):
		if opt == 0 : 
			self.spliceButton.Enable(enable)
			self.clearButton.Enable(enable)
		elif opt == 1 :
			self.undoButton.Enable(enable)
		elif opt == 2 :
			self.clearButton.Enable(enable)
		elif opt == 3 :
			self.spliceButton.Enable(enable)
		elif opt == 4 :
			self.appendButton.Enable(enable)

	def OnChangeMode(self, evt):
		if self.const.GetValue() == True :
			self.parent.Window.Constrained = 1 
			self.depth.SetValue("0.0")
		else :
			self.parent.Window.Constrained = 0 

	def OnClearTie(self, evt):
		self.parent.Window.activeSPTie = -1
		self.parent.Window.OnClearTies(1)
		self.OnButtonEnable(0, False)
		self.OnButtonEnable(1, True)

	def OnAppend(self, evt):
		if self.appendall == 1 and self.all.GetValue() == True:
			self.parent.OnShowMessage("Error", "Already appended all below", 1)
			return

		type = 0 
		self.appendall = 0 
		splice_count = len(self.parent.Window.SpliceCore)
		splice_data = "" 

		if self.selected.GetValue() == True :
			if splice_count <= 1:
				py_correlator.append_at_begin()

			l = self.parent.GetSpliceCore()
			if l != None : 
				hole = l[0]
				core = int(l[1])
				type = l[2]
				splice_data = py_correlator.append_selected(type, hole, core, self.parent.smoothDisplay)
		else : 
			if self.all.GetValue() == True :
				type = 1
				self.appendall = 1 

			if splice_count <= 1 :
				print "append....at begin", splice_count
				py_correlator.append_at_begin()

			self.undoButton.Enable(True)
			splice_data = py_correlator.append(type, self.parent.smoothDisplay)

		if splice_data[1] != "" :
			self.parent.Window.SpliceData = []
			ret = py_correlator.getData(2) # get splice tie info
			if ret != "" :
				self.parent.ParseSpliceData(ret, True)
				self.parent.Window.RealSpliceTie.append(canvas.DefaultSpliceTie())
				self.parent.Window.RealSpliceTie.append(canvas.DefaultSpliceTie())
				ret = "" 
			self.parent.filterPanel.OnLock()
			self.parent.ParseData(splice_data[1], self.parent.Window.SpliceData)
			self.parent.UpdateSMOOTH_SPLICE(False)
			self.parent.filterPanel.OnRelease()
			if self.all.GetValue() == True :
				self.appendflag =True 
		self.parent.Window.activeSPTie = -1
		self.parent.Window.UpdateDrawing()

	def OnSplice(self, evt):
		self.parent.Window.activeSPTie = -1
		self.parent.OnSplice()

	def OnUndoSplice(self, evt):
		# HYEJUNG
		self.parent.Window.activeSPTie = -1
		if self.appendall == 0 :
			self.parent.OnUndoSplice()
		else :
			self.appendall = 0
			splice_data = py_correlator.undoAppend(self.parent.smoothDisplay)
			if splice_data[1] != "" :
				self.parent.Window.RealSpliceTie.pop()
				self.parent.Window.RealSpliceTie.pop()

				self.parent.Window.SpliceData = []
				ret = py_correlator.getData(2)
				if ret != "" :
					self.parent.ParseSpliceData(ret, True)
					ret = "" 
				self.parent.filterPanel.OnLock()
				self.parent.ParseData(splice_data[1], self.parent.Window.SpliceData)
				self.parent.filterPanel.OnRelease()
				self.parent.Window.UpdateDrawing()

		for data in self.parent.Window.SpliceData :
			hole = data[0]
			info = hole[0]
			tie_max = info[8] 
			break

		if self.parent.Window.SpliceData == []:
			self.undoButton.Enable(False)
			self.appendButton.Enable(False)

	def OnEvalSettings(self, evt):
		pos = self.crText.GetScreenPositionTuple()
		dlg = dialog.CorrParamsDialog(self.mainPanel, self.parent.minDepthStep, self.parent.depthStep, self.parent.winLength, self.parent.leadLag)
		dlg.SetPosition(pos)
		if dlg.ShowModal() == wx.ID_OK:
			self.parent.OnEvalSetup(dlg.outDepthStep, dlg.outWinLength, dlg.outLeadLag)
			self.parent.OnUpdateGraphSetup(2)
			self.parent.Window.OnUpdateTie(2)

	def OnUpdate(self):
		self.corrPlotCanvas.Clear()
		data = [ (-self.parent.leadLag, 0),( 0, 0), (self.parent.leadLag, 0) ]
		self.OnUpdateData(data, [])
		self.OnUpdateDrawing()
		self.UpdateEvalStatus()
		self.mainPanel.Update()
		self.parent.Update()

	def OnUpdateDepth(self, data):
		depth_value = int(10000.0 * float(data)) / 10000.0
		self.depth.SetValue(str(depth_value))

	def UpdateEvalStatus(self):
		roundedDepthStep = int(10000.0 * float(self.parent.depthStep)) / 10000.0
		self.crText.SetLabel("Step: {} | Window: {} | Lead/Lag: {}".format(roundedDepthStep, self.parent.winLength, self.parent.leadLag))

	def OnUpdateData(self, data, bestdata):
		line = plot.PolyLine(data, legend='', colour='red', width =2) 
		self.polyline_list.append(line)
		if bestdata != [] : 
			bestline = plot.PolyLine(bestdata, legend='', colour='blue', width =5) 
			self.polyline_list.append(bestline)

	# brg 9/18/2013 duplication
	def OnAddFirstData(self, data, bestdata, best):
		line = plot.PolyLine(data, legend='', colour='red', width =2) 
		self.polyline_list.append(line)
		if bestdata != [] : 
			bestline = plot.PolyLine(bestdata, legend='', colour='blue', width =5) 
			self.polyline_list.append(bestline)

	def OnAddData(self, data):
		line = plot.PolyLine(data, legend='', colour='grey', width =2) 
		self.polyline_list.append(line)

	def OnUpdateDrawing(self):
		self.polyline_list.append(self.xaxes)
		self.polyline_list.append(self.yaxes)
		gc = plot.PlotGraphics(self.polyline_list, 'Evaluation Graph', 'depth Axis', 'coef Axis')
		self.corrPlotCanvas.Draw(gc, xAxis = (-self.leadLagValue , self.leadLagValue), yAxis = (-1, 1))	
		self.polyline_list = []


# Panel containing evaluation graph plot canvas and settings display/controls
class EvalPlotPanel(wx.Panel):
	def __init__(self, parent, uiParent, depthStep, winLength, leadLag):
		wx.Panel.__init__(self, uiParent, -1)
		self.parent = parent # correlator, so we can set global depthStep etc.
		self.depthStep = depthStep
		self.winLength = winLength
		self.leadLag = leadLag
		self.polylines = [] # data to be plotted
		self._debugDrawCount = 0
		
		self._setupUI()

	def _setupUI(self):
		# evaluation graph
		self.evalPlot = BetterLegendPlotCanvas(self)#evalPanel)
		self.evalPlot.SetEnableGrid(True)
		self.evalPlot.SetEnableTitle(False)
		self.evalPlot.SetBackgroundColour("White")
		self.evalPlot.Show(True)
		evsz = wx.BoxSizer(wx.VERTICAL)
		evsz.Add(self.evalPlot, 1, wx.EXPAND)
		
		paramPanel = wx.Panel(self, -1)
		psz = wx.BoxSizer(wx.HORIZONTAL)
		bmp = wx.Bitmap("icons/sprocket.png")
		settingsBtn = wx.BitmapButton(paramPanel, -1, bmp)
		self.crText = wx.StaticText(paramPanel, -1, "Step: 0.135 | Window: 1.0 | Lead/Lag: 1.0")
		crFont = self.crText.GetFont()
		crFont.SetPointSize(10)
		self.crText.SetFont(crFont)
		psz.Add(self.crText, 1, wx.ALIGN_CENTER_VERTICAL)
		psz.Add(settingsBtn, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
		paramPanel.SetSizer(psz)
		
		evsz.Add(paramPanel, 0, wx.EXPAND)
		self.SetSizer(evsz)
		
		paramPanel.Bind(wx.EVT_BUTTON, self.OnEvalSettings, settingsBtn)

		data = [ (-self.leadLag, 0), (0, 0), (self.leadLag, 0) ]
		self.OnUpdateData(data, [])
		self.OnUpdateDrawing()

	def OnEvalSettings(self, evt):
		pos = self.crText.GetScreenPositionTuple()
		dlg = dialog.CorrParamsDialog(self, self.parent.minDepthStep, self.depthStep, self.winLength, self.leadLag)
		dlg.SetPosition(pos)
		if dlg.ShowModal() == wx.ID_OK:
			self.depthStep = dlg.outDepthStep
			self.winLength = dlg.outWinLength
			self.leadLag = dlg.outLeadLag
			self.parent.OnEvalSetup(dlg.outDepthStep, dlg.outWinLength, dlg.outLeadLag)
			self.parent.OnUpdateGraphSetup(2)
	
	def OnUpdate(self):
		#self.evalPlot.Clear() # appears to be unnecessary on Mac...check Win and pull if possible
		data = [(-self.leadLag, 0), (0, 0), (self.leadLag, 0)]
		self.OnUpdateData(data, [])
		self.OnUpdateDrawing()
		#self.parent.Update() # appears to be unnecessary on Mac
		self.UpdateEvalStatus()

	def UpdateEvalStatus(self):
		roundedDepthStep = int(10000.0 * float(self.depthStep)) / 10000.0
		self.crText.SetLabel("Step: {} | Window: {} | Lead/Lag: {}".format(roundedDepthStep, self.winLength, self.leadLag))
		
	def OnUpdateData(self, data, bestdata):
		line = plot.PolyLine(data, legend='', colour='red', width =2) 
		self.polylines.append(line)
		if bestdata != [] : 
			bestline = plot.PolyLine(bestdata, legend='', colour='blue', width =5) 
			self.polylines.append(bestline)

	def OnAddFirstData(self, data, bestdata, best):
		line = plot.PolyLine(data, legend='', colour='red', width =2) 
		self.polylines.append(line)
		if bestdata != [] : 
			bestline = plot.PolyLine(bestdata, legend='', colour='blue', width =5) 
			self.polylines.append(bestline)

	def OnAddData(self, data):
		line = plot.PolyLine(data, legend='', colour='grey', width =2) 
		self.polylines.append(line)

	def OnUpdateDrawing(self): # called by client to redraw
		# update axes
		xdata = [ (-self.leadLag, 0), (0, 0), (self.leadLag, 0) ]
		self.xaxes = plot.PolyLine(xdata, legend='', colour='black', width =2)
		ydata = [ (0, -1),( 0, 1) ]
		self.yaxes = plot.PolyLine(ydata, legend='', colour='black', width =2)
		self.polylines.append(self.xaxes)
		self.polylines.append(self.yaxes)
		
		gc = plot.PlotGraphics(self.polylines, '', 'depth (m)', 'correlation coef (r)')
		self.evalPlot.Draw(gc, xAxis = (-self.leadLag , self.leadLag), yAxis = (-1, 1))
		self.polylines = []


class SpliceIntervalPanel():
	def __init__(self, parent, mainPanel):
		self.mainPanel = mainPanel
		self.parent = parent
		self.lastInterval = None # track last-selected row to save properly after selection change
		
		self._setupUI()
		
		self.parent.spliceManager.addSelChangeListener(self.OnSelectionChange)
		self.parent.spliceManager.addAddIntervalListener(self.OnAdd)
		self.parent.spliceManager.addDeleteIntervalListener(self.UpdateUI)
		
	def _setupUI(self):
		panel = wx.Panel(self.mainPanel, -1)
		psz = wx.BoxSizer(wx.VERTICAL)
		panel.SetSizer(psz)

		# interval table, evaluation graph tabs
		self.note = wx.Notebook(panel, -1)
		
		# interval table
		gridPanel = wx.Panel(self.note, -1)
		gpsz = wx.BoxSizer(wx.VERTICAL)
		self.table = wx.grid.Grid(gridPanel, -1)
		self.table.SetRowLabelSize(0) # hide row headers
		self.table.DisableDragRowSize()
		self.table.EnableEditing(False)
		self.table.CreateGrid(numRows=0, numCols=3)
		for colidx, label in enumerate(["Core", "Top (m)", "Bot (m)"]):
			self.table.SetColLabelValue(colidx, label)
		self.table.SetSelectionMode(wx.grid.Grid.SelectRows)
		gpsz.Add(self.table, 1, wx.EXPAND)
		gridPanel.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.OnSelectRow)
		gridPanel.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.OnSetDepth)
		gridPanel.SetSizer(gpsz)
		self.note.AddPage(gridPanel, "Splice Intervals")
		self.gridPanel = gridPanel
		
		# evaluation graph
		evalPlotPanel = EvalPlotPanel(self.parent, self.note, self.parent.depthStep, self.parent.winLength, self.parent.leadLag)
		self.note.AddPage(evalPlotPanel, "Evaluation Graph")
		self.evalPanel = evalPlotPanel
		
		psz.Add(self.note, 2, wx.EXPAND)
		self.note.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnSelectNote)
		self.note.SetSelection(0)
		
		# comments, delete button
		ctrlPanel = wx.Panel(panel, -1)
		cpsz = wx.BoxSizer(wx.VERTICAL)
		cbox = wx.StaticBoxSizer(wx.StaticBox(ctrlPanel, -1, "Interval Comments"))
		self.commentText = dialog.CommentTextCtrl(ctrlPanel, -1, "[interval comment]", style=wx.TE_MULTILINE)
		self.commentText.Bind(wx.EVT_KILL_FOCUS, self._saveComment)
		cbox.Add(self.commentText, 1, wx.EXPAND)
		cpsz.Add(cbox, 1, wx.EXPAND | wx.ALL, 5)

		self.delButton = wx.Button(ctrlPanel, -1, "Delete Interval")
		ctrlPanel.Bind(wx.EVT_BUTTON, self.OnDelete, self.delButton)
		cpsz.Add(self.delButton, 0, wx.EXPAND | wx.ALL, 5)
		ctrlPanel.SetSizer(cpsz)
		psz.Add(ctrlPanel, 1, wx.EXPAND)

		# tie option buttons (split/tie)
		tsbox = wx.StaticBoxSizer(wx.StaticBox(panel, -1, "Tie Options"), orient=wx.VERTICAL)	
		tieSplitPanel = wx.Panel(panel, -1)
		self.topTieButton = wx.Button(tieSplitPanel, -1, "Edit Top Tie")
		tieSplitPanel.Bind(wx.EVT_BUTTON, self.OnTopTieButton, self.topTieButton)
		self.botTieButton = wx.Button(tieSplitPanel, -1, "Edit Bottom Tie")
		tieSplitPanel.Bind(wx.EVT_BUTTON, self.OnBotTieButton, self.botTieButton)
		tspsz = wx.FlexGridSizer(rows=2, cols=2, vgap=10)
		tspsz.AddGrowableCol(1, proportion=1)
		tspsz.Add(wx.StaticText(tieSplitPanel, -1, "Top: "), 1, wx.ALIGN_CENTER_VERTICAL)
		tspsz.Add(self.topTieButton, 1, wx.EXPAND | wx.RIGHT, 10)
		tspsz.Add(wx.StaticText(tieSplitPanel, -1, "Bottom: "), 1, wx.ALIGN_CENTER_VERTICAL)
		tspsz.Add(self.botTieButton, 1, wx.EXPAND | wx.RIGHT, 10)
		tieSplitPanel.SetSizer(tspsz)
		tsbox.Add(tieSplitPanel, 1, wx.EXPAND)
		psz.Add(tsbox, 1, wx.EXPAND | wx.TOP, 10)
		
		self.altSpliceButton = wx.Button(panel, -1, "Select Alternate Splice...")
		self.altSpliceButton.Bind(wx.EVT_BUTTON, self.OnAltSplice)
		psz.Add(self.altSpliceButton, 0, wx.EXPAND | wx.ALL, 10)
		
		self.saveButton = wx.Button(panel, -1, "Save Splice...")
		self.saveButton.Bind(wx.EVT_BUTTON, self.OnSave)
		psz.Add(self.saveButton, 0, wx.EXPAND | wx.ALL, 10)
				
		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(panel, 1, wx.EXPAND)
		self.mainPanel.SetSizer(vbox)
		
	def OnAltSplice(self, event):
		asd = dialog.AltSpliceDialog(self.parent)
		if asd.ShowModal() == wx.ID_OK:
			selectedType =  asd.selectedType
			selectedSplice = asd.selectedSplice
			altSplicePath = self.parent.DBPath + "db/" + self.parent.dataFrame.GetSelectedSiteName() + '/' + selectedSplice
			if self.parent.spliceManager.canApplyAffine(altSplicePath):
				self.parent.spliceManager.loadAlternateSplice(altSplicePath, selectedType)
				self.parent.Window.UpdateDrawing()
			else:
				self.parent.OnShowMessage("Error", self.parent.spliceManager.getErrorMsg(), 1)
	
	def OnSelectNote(self, event):
		newSel = event.GetSelection()
		self.gridPanel.Hide()
		self.evalPanel.Hide() 
		if newSel == 0:
			self.gridPanel.Show()
			self.evalPanel.Hide()
		else:
			self.gridPanel.Hide()
			self.evalPanel.Show()
	
	def UpdateUI(self):
		self._updateTable()
		self._updateButtons()
		
	def OnInitUI(self): # to match other panels' interface
		self.UpdateUI()

	# add cells for SpliceInterval si at specified row
	def _makeTableRow(self, row, si):
		self.table.SetCellValue(row, 0, str(si.coreinfo.getHoleCoreStr()))
		self.table.SetCellValue(row, 1, str(round(si.getTop(), 3)))
		self.table.SetCellValue(row, 2, str(round(si.getBot(), 3)))
		
	# add/delete rows to match current interval count
	def _adjustTableRows(self, rows):
		currows = self.table.GetNumberRows()
		if currows > rows:
			delcount = currows - rows
			self.table.DeleteRows(pos=rows, numRows=delcount)
		elif currows < rows:
			addcount = rows - currows
			self.table.InsertRows(pos=0, numRows=addcount)

	# update all row data and selection
	def _updateTable(self):
		rows = self.parent.spliceManager.count()
		self._adjustTableRows(rows)
		for row, si in enumerate(self.parent.spliceManager.getIntervals()):
			self._makeTableRow(row, si)
		self._updateTableSelection()
			
	# update current selection
	def _updateTableSelection(self):
		cursel = self.parent.spliceManager.getSelectedIndex()
		if cursel == -1:
			self.table.ClearSelection()
			self.lastInterval = None
			self._updateComment("")
		else:
			self.table.SelectRow(cursel)
			self.table.MakeCellVisible(cursel, 0) # scroll to row if not visible
			self.lastInterval = self.parent.spliceManager.getSelected()
			self._updateComment(self.lastInterval.comment)
			
	# create label for tie/split buttons
	def _getButtonLabel(self, tie):
		label = "No Action"
		if tie.canTie():
			label = "Tie {}".format(tie.getButtonName())
		elif tie.isTied():
			label = "Split {}".format(tie.getButtonName())
		return label

	# update delete button, tie/split button label and enabled state
	def _updateButtons(self):
		hasSel = self.parent.spliceManager.hasSelection() 
		self.delButton.Enable(hasSel)
		self.saveButton.Enable(self.parent.spliceManager.count() > 0)
		if hasSel:
			self.delButton.SetLabel("Delete Interval {}".format(self.parent.spliceManager.getSelected().getHoleCoreStr()))
			
			topTie = self.parent.spliceManager.topTie
			enableTop = topTie.canTie() or topTie.isTied()
			self.topTieButton.Enable(enableTop)
			self.topTieButton.SetLabel(self._getButtonLabel(topTie))
			
			botTie = self.parent.spliceManager.botTie
			enableBot = botTie.canTie() or botTie.isTied()
			self.botTieButton.Enable(enableBot)
			self.botTieButton.SetLabel(self._getButtonLabel(botTie))
		else:
			self.delButton.SetLabel("Delete Interval")
			self.topTieButton.Enable(False)
			self.botTieButton.Enable(False)
	
	def _updateComment(self, comment):
		self.commentText.SetValue(comment)
	
	def _saveComment(self, event=None):
		if self.lastInterval is not None and self.lastInterval.comment != self.commentText.GetValue():
			self.lastInterval.comment = self.commentText.GetValue()
			
	def _prohibitCommas(self, evt):
		if chr(evt.GetKeyCode()) != ',':
			evt.Skip()

	# selected SpliceInterval changed through SpliceArea click, update GUI to reflect
	def OnSelectionChange(self):
		self._updateButtons()
		self._updateTableSelection()
		
	def OnAdd(self): # SpliceInterval added
		self.UpdateUI()
	
	def OnDelete(self, event): # handle Delete button
		self.parent.spliceManager.deleteSelected()
		self.UpdateUI()
		self.parent.Window.UpdateDrawing()
		
	def OnTopTieButton(self, event):
		topTie = self.parent.spliceManager.topTie
		self.OnTieButton(topTie)

	def OnBotTieButton(self, event):
		botTie = self.parent.spliceManager.botTie
		self.OnTieButton(botTie)
		
	def OnTieButton(self, tie):
		if tie.isTied():
			tie.split()
		else:
			tie.tie()
		self.UpdateUI()
		self.parent.Window.UpdateDrawing()
		
	def OnSave(self, event):
		dlg = dialog.Message3Button(self.parent, "Create new splice file?", yesLabel="Create New", okLabel="Update Existing", cancelLabel="Cancel")
		ret = dlg.ShowModal()
		dlg.Destroy()
		if ret == wx.ID_OK or ret == wx.ID_YES :
			updateExisting = ret == wx.ID_OK
			filename = self.parent.dataFrame.Add_TABLE("SPLICE" , "splice", updateExisting, False, "")
			print "Save: updateExisting = {}, filename = {}".format(updateExisting, filename)
			self.parent.spliceManager.save(filename)

			s = "Save Splice Table: " + filename + "\n"
			self.parent.logFileptr.write(s)
			self.parent.autoPanel.SetCoreList(1, [])
			self.parent.OnShowMessage("Information", "Successfully Saved", 1)
	
	def OnSelectRow(self, event):
		self.parent.spliceManager.selectByIndex(event.GetRow())
		self.lastInterval = self.parent.spliceManager.getIntervalAtIndex(event.GetRow())
		
		# adjust depth range to show selected interval if necessary
		visibleMin = self.parent.Window.rulerStartDepth
		visibleMax = self.parent.Window.rulerEndDepth - 2.0
		intervalTop = self.parent.spliceManager.getSelected()
		if not intervalTop.overlaps(splice.Interval(visibleMin, visibleMax)):
			self.parent.OnUpdateStartDepth(intervalTop.getTop()) # calls UpdateDrawing()
		else:
			self.parent.Window.UpdateDrawing()
			
	def OnSetDepth(self, event):
		if event.GetCol() == 0: # do nothing on double-click of ID column
			return
		
		curint = self.parent.spliceManager.getSelected()
		totalDepth = curint.getTop() if event.GetCol() == 1 else curint.getBot()
		totalDepth = round(totalDepth, 3)
		site = curint.coreinfo.leg # argh
		hole = curint.coreinfo.hole
		core = curint.coreinfo.holeCore
		mcdOffset = self.parent.Window.findCoreAffineOffset(hole, core)
		section = self.parent.sectionSummary.getSectionAtDepth(site, hole, core, totalDepth - mcdOffset)
		secDepth = round((totalDepth - (self.parent.sectionSummary.getSectionTop(site, hole, core, section) + mcdOffset)) * 100.0, 1)
		setDepthDialog = dialog.SetDepthDialog(self.parent, totalDepth, secDepth, section)
		setDepthDialog.SetPosition(event.GetEventObject().GetScreenPosition())
		result = setDepthDialog.ShowModal()
		if result == wx.ID_OK:
			tie = self.parent.spliceManager.topTie if event.GetCol() == 1 else self.parent.spliceManager.botTie
			if setDepthDialog.totalRadio.GetValue() == True: # total depth
				depth = float(setDepthDialog.totalDepth.GetValue())
			else: # section depth
				section = setDepthDialog.sectionNumber.GetValue()
				secDepth = float(setDepthDialog.sectionDepth.GetValue())
				# section summary depths are all MBSF/CSF-A, add MCD/CCSF-A offset for true depth
				depth = self.parent.sectionSummary.sectionDepthToTotal(site, hole, core, section, secDepth) + mcdOffset
			tie.move(depth)
			self.UpdateUI()
			self.parent.Window.UpdateDrawing()

	# wrappers for EvalPlotPanel
	def OnAddFirstData(self, data, bestdata, best):
		self.evalPanel.OnAddFirstData(data, bestdata, best)
	def OnAddData(self, data):
		self.evalPanel.OnAddData(data)
	def OnUpdate(self):
		self.evalPanel.OnUpdate()


############## end SpliceIntervalPanel #################################

class AutoPanel():
	def __init__(self, parent, mainPanel):
		self.mainPanel = mainPanel
		self.parent = parent
		self.AutoRateList = []
		self.sortDataList = []
		self.isCalculated = False
		self.spliceFlag = 0
		self.depthstart = -5.10
		self.squishend = 95.0
		self.depthinterval = 0.3
		self.squishinterval = 0.5
		self.leadLagValue = self.parent.leadLag
		self.selectedNo = -1
		self.ApplyFlag = -1 
		self.addItemsInFrame()

	def addItemsInFrame(self):
		#vbox_top = wx.BoxSizer(wx.VERTICAL)
		vbox = wx.BoxSizer(wx.VERTICAL)

		# Panel 1
		panel1 = wx.Panel(self.mainPanel, -1)
		sizer1 = wx.StaticBoxSizer(wx.StaticBox(panel1, -1, 'Core-Log Depth Matching Parameters'), orient=wx.VERTICAL)
		sizer1.Add(wx.StaticText(panel1, -1, 'Stretch/Compress core data between:', (5, 5)), 0, wx.ALIGN_CENTER_VERTICAL)

		grid1 = wx.FlexGridSizer(2, 4)
		self.valueA1 = wx.TextCtrl(panel1, -1, "85.0", size=(60, 25), style=wx.SUNKEN_BORDER )
		grid1.Add(self.valueA1)
		grid1.Add(wx.StaticText(panel1, -1, '%  and', (5, 5)), 0, wx.ALIGN_CENTER_VERTICAL)
		self.valueA2 = wx.TextCtrl(panel1, -1, "95.0", size=(60, 25), style=wx.SUNKEN_BORDER )
		grid1.Add(self.valueA2)
		if platform_name[0] == "Windows" :
			grid1.Add(wx.StaticText(panel1, -1, '%  at    ', (5, 5)), 0, wx.ALIGN_CENTER_VERTICAL)
		else :
			grid1.Add(wx.StaticText(panel1, -1, '%  at', (5, 5)), 0, wx.ALIGN_CENTER_VERTICAL)

		self.valueA3 = wx.TextCtrl(panel1, -1, "0.50", size =(60, 25), style=wx.SUNKEN_BORDER )
		grid1.Add(self.valueA3)
		grid1.Add(wx.StaticText(panel1, -1, '% intervals', (5, 5)), 0, wx.ALIGN_CENTER_VERTICAL)
		sizer1.Add(grid1, 0, wx.TOP, 5)

		sizer1.Add(wx.StaticText(panel1, -1, 'Slide Log up/down between:', (5, 5)), 0, wx.TOP | wx.ALIGN_CENTER_VERTICAL, 9)

		grid12 = wx.FlexGridSizer(2, 4)
		self.valueB1 = wx.TextCtrl(panel1, -1, "-5.1", size =(60, 25), style=wx.SUNKEN_BORDER )
		grid12.Add(self.valueB1)
		grid12.Add(wx.StaticText(panel1, -1, 'm  and', (5, 5)), 0, wx.ALIGN_CENTER_VERTICAL)
		self.valueB2 = wx.TextCtrl(panel1, -1, "5.1", size =(60, 25), style=wx.SUNKEN_BORDER )
		grid12.Add(self.valueB2)
		grid12.Add(wx.StaticText(panel1, -1, 'm  at', (5, 5)), 0, wx.ALIGN_CENTER_VERTICAL)
		self.valueB3 = wx.TextCtrl(panel1, -1, "0.3", size=(60, 25), style=wx.SUNKEN_BORDER )
		grid12.Add(self.valueB3)
		grid12.Add(wx.StaticText(panel1, -1, 'm intervals', (5, 5)), 0, wx.ALIGN_CENTER_VERTICAL)
		sizer1.Add(grid12, 0, wx.TOP, 5)

		grid13 = wx.FlexGridSizer(2, 3)
		grid13.Add(wx.StaticText(panel1, -1, 'Correlation depth step: ', (5, 5)), 0, wx.TOP | wx.ALIGN_CENTER_VERTICAL, 9)
		self.valueC = wx.TextCtrl(panel1, -1, "0.15", size =(60, 25), style=wx.SUNKEN_BORDER )
		if platform_name[0] == "Windows" :	
			grid13.Add(self.valueC, 0, wx.TOP | wx.LEFT, 9)
		else :
			grid13.Add(self.valueC, 0, wx.TOP, 9)
			
		grid13.Add(wx.StaticText(panel1, -1, 'm', (5, 5)), 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP, 9)
		grid13.Add(wx.StaticText(panel1, -1, 'Invert core variable:', (5, 5)), 0, wx.TOP | wx.ALIGN_CENTER_VERTICAL, 9)
		yesBtn = wx.RadioButton(panel1, -1, "Yes", style=wx.RB_GROUP)
		grid13.Add(yesBtn, 0, wx.TOP, 9)
		noBtn = wx.RadioButton(panel1, -1, "No")
		grid13.Add(noBtn, 0, wx.TOP, 9)
		yesBtn.Enable(False)
		noBtn.SetValue(True)

		sizer1.Add(grid13, 0, wx.TOP, 5)

		panel1.SetSizer(sizer1)
		vbox.Add(panel1, 0, wx.TOP, 9)

		vbox.Add(wx.StaticText(self.mainPanel, -1, 'Select Hole(s):', (5, 5)), 0, wx.ALIGN_CENTER_VERTICAL)
		
		buttonsize = 300
		if platform_name[0] == "Windows" :
			buttonsize = 285
			
		if self.parent.Height > 768 :
			self.fileList = wx.ListBox(self.mainPanel, -1, (0,0),(buttonsize,95), "", style=wx.LB_HSCROLL|wx.LB_NEEDED_SB|wx.LB_EXTENDED)
		else :
			self.fileList = wx.ListBox(self.mainPanel, -1, (0,0),(buttonsize,65), "", style=wx.LB_HSCROLL|wx.LB_NEEDED_SB|wx.LB_EXTENDED)

		vbox.Add(self.fileList, 0, wx.BOTTOM, 3)
		self.fileList.SetForegroundColour(wx.BLACK)

		buttonsize = 255
		#if platform_name[0] == "Windows" :
		#	buttonsize = 285
			
		self.calopBtn = wx.Button(self.mainPanel, -1, "Calculate Core-Log Depth Match", size=(buttonsize, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnCalcMatch, self.calopBtn)
		vbox.Add(self.calopBtn, 0, wx.TOP | wx.ALIGN_CENTER_HORIZONTAL, 5)
		self.calopBtn.Enable(False)

		# Panel 2
		panel2 = wx.Panel(self.mainPanel, -1)
		sizer2 = wx.StaticBoxSizer(wx.StaticBox(panel2, -1, 'LD Recommended Depth Matching'), orient=wx.VERTICAL)

		grid2 = wx.FlexGridSizer(3, 2)
		self.valueD1 = wx.TextCtrl(panel2, -1, "", size=(80, 25), style=wx.SUNKEN_BORDER )
		self.valueD1.SetEditable(False)
		grid2.Add(self.valueD1)
		if platform_name[0] == "Windows" :		
			grid2.Add(wx.StaticText(panel2, -1, ' %  stretch/compress                   ', (5, 5)), 0, wx.ALIGN_CENTER_VERTICAL)
		else :
			grid2.Add(wx.StaticText(panel2, -1, ' %  stretch/compress', (5, 5)), 0, wx.ALIGN_CENTER_VERTICAL)
		
		self.valueD2 = wx.TextCtrl(panel2, -1, "0.938", size =(80, 25), style=wx.SUNKEN_BORDER )
		self.valueD2.SetEditable(False)
		grid2.Add(self.valueD2)
		grid2.Add(wx.StaticText(panel2, -1, ' CSF / CCSF ratio', (5, 5)), 0, wx.ALIGN_CENTER_VERTICAL)
		self.valueD3 = wx.TextCtrl(panel2, -1, "", size =(80, 25), style=wx.SUNKEN_BORDER )
		self.valueD3.SetEditable(False)
		grid2.Add(self.valueD3)
		grid2.Add(wx.StaticText(panel2, -1, ' m log offset', (5, 5)), 0, wx.ALIGN_CENTER_VERTICAL)

		sizer2.Add(grid2, 0, wx.TOP, 5)
		panel2.SetSizer(sizer2)
		vbox.Add(panel2, 0, wx.TOP, 3)

		buttonsize = 300
		if platform_name[0] == "Windows" :
			buttonsize = 285
			
		if self.parent.Height > 768 :
			self.resultList = wx.ListBox(self.mainPanel, -1, (0,0),(buttonsize,130), "", style=wx.LB_NEEDED_SB)
		else :
			#self.resultList = wx.ListBox(self.mainPanel, -1, (0,0),(buttonsize,100), "", style=wx.LB_NEEDED_SB)
			self.resultList = wx.ListBox(self.mainPanel, -1, (0,0),(buttonsize,60), "", style=wx.LB_NEEDED_SB)

		self.mainPanel.Bind(wx.EVT_LISTBOX, self.OnSelectRate, self.resultList)
		vbox.Add(self.resultList, 0, wx.BOTTOM, 3)

		buttonsize = 95
		if platform_name[0] == "Windows" :
			buttonsize = 92
			
		# Panel 3
		panel3 = wx.Panel(self.mainPanel, -1)
		grid3 = wx.FlexGridSizer(1, 3)
		self.resetBtn = wx.Button(panel3, -1, "Reset", size=(buttonsize, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnDismiss, self.resetBtn)
		grid3.Add(self.resetBtn, 0)

		self.undoBtn = wx.Button(panel3, wx.ID_CANCEL, "Undo", size=(buttonsize, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnUndo, self.undoBtn)
		self.undoBtn.Enable(False)
		grid3.Add(self.undoBtn, 0, wx.LEFT, 5)

		self.ApplyFlag = -1
		self.applyBtn = wx.Button(panel3, -1, "Apply", size =(buttonsize, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnApply, self.applyBtn)
		self.applyBtn.Enable(False)
		grid3.Add(self.applyBtn, 0, wx.LEFT, 5)

		panel3.SetSizer(grid3)
		vbox.Add(panel3, 0, wx.TOP, 3)

		#vbox.Add(wx.StaticText(self.mainPanel, -1, '*Log data is required.', (5, 5)), 0, wx.BOTTOM, 9)
		self.saveButton = wx.Button(self.mainPanel, -1, "Save ELD Table", size =(150, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnSAVE, self.saveButton)
		vbox.Add(self.saveButton, 0, wx.ALIGN_CENTER_VERTICAL)
		self.saveButton.Enable(False)

		vbox.Add(wx.StaticText(self.mainPanel, -1, '* Auto Correlation will stretch/compress', (5, 5)), 0, wx.BOTTOM, 2)
		vbox.Add(wx.StaticText(self.mainPanel, -1, 'sections and log depth offset.', (5, 5)), 0, wx.BOTTOM, 7)

		#vbox_top.Add(vbox, 1, wx.LEFT, 5)
		self.mainPanel.SetSizer(vbox)

	def OnButtonEnable(self, opt, enable):
		self.mainPanel.Enable(enable)
		if opt == 0 :
			self.calopBtn.Enable(enable)
			

	def OnSAVE(self, event):
		if self.parent.Window.LogData != [] :
			dlg = dialog.Message3Button(self.parent, "Do you want to create new eld file?")
			ret = dlg.ShowModal()
			dlg.Destroy()
			if ret == wx.ID_OK or ret == wx.ID_YES :
				flag = True
				if ret == wx.ID_YES :
					flag = False
				filename = self.parent.dataFrame.Add_TABLE("ELD" , "eld", flag, False, "")
				py_correlator.saveAttributeFile(filename, 4)

				s = "Save ELD Table: " + filename + "\n"
				self.parent.logFileptr.write(s)
				self.parent.OnShowMessage("Information", "Successfully Saved", 1)
				self.parent.EldChange = False 
		else :
			self.parent.OnShowMessage("Error", "No data to save", 1)

	
	def SetCoreList(self, splice_flag, hole_data):
		self.fileList.Clear()
		if splice_flag == 1 :
			self.fileList.InsertItems(["Splice"], 0)
			self.spliceFlag = 1
		else :
			self.spliceFlag = 0 
			hole_name = ""
			hole_index =0
			for data in hole_data:
				for r in data:
					hole = r
					holeInfo = hole[0]
					hole_name = holeInfo[7] + " -" + holeInfo[1] + " " + holeInfo[0] + " : " + holeInfo[2]
					self.fileList.InsertItems([hole_name], hole_index)
					hole_index = hole_index + 1
		if self.fileList.GetCount() > 0 :
			self.fileList.Select(0)

	def OnCalcMatch(self, event):
		#if self.parent.Window.ELDapplied == True: 
		py_correlator.cleanData(8)
		#if self.parent.Window.coefRangeSplice == 0.0 :
		#	self.parent.Window.ResetSpliceCoef()
			
		squishstart = float(self.valueA1.GetValue()) 
		squishend = float(self.valueA2.GetValue()) 
		self.squishend = squishend
		if squishstart > squishend :
			temp = squishstart
			squishstart = squishend
			squishend = temp		
		depthstart = float(self.valueB1.GetValue()) 
		depthend = float(self.valueB2.GetValue()) 
		self.depthstart = depthstart
		if depthstart > depthend :
			temp = depthstart
			depthstart = depthend
			depthend = temp		
		self.squishinterval = float(self.valueA3.GetValue()) 
		self.depthinterval = float(self.valueB3.GetValue()) 
		depthrange = int((depthend - depthstart) / self.depthinterval)
		squishrange = int((squishend - squishstart) / self.squishinterval)

		if squishrange == 0 :
			squishrange = 1
		totalcount = squishrange * depthrange 
		progress = ProgressFrame(self.parent, totalcount)

		py_correlator.initCorrelate()

		self.parent.Window.autocoreNo = []
		depth_step = float(self.valueC.GetValue())
		for i in range(self.fileList.GetCount()) :
			if self.fileList.IsSelected(i) == True :
				str_list = self.fileList.GetString(i)
				if str_list == "Splice" :
					py_correlator.setCorrelate(str_list, "", squishstart, squishend, self.squishinterval, depthstart, depthend, self.depthinterval, depth_step)
					ratio = py_correlator.getRatio(str_list, str_list)
					ratio_str = int(1000.00 * float(ratio)) / 1000.00
					self.valueD2.SetValue(str(ratio_str))
				else :
					end = str_list.find(" ", 0)
					holename = str_list[0:end]
					start = str_list.find(":", 0) + 2 
					end = len(str_list)
					datatype = str_list[start:end]
					py_correlator.setCorrelate(holename, datatype, squishstart, squishend, self.squishinterval, depthstart, depthend, self.depthinterval, depth_step)
					ratio = py_correlator.getRatio(holename, datatype)
					ratio_str = int(1000.00 * float(ratio)) / 1000.00
					self.valueD2.SetValue(str(ratio_str))
				if self.spliceFlag == 0 : 
					self.parent.Window.autocoreNo.append(i)
					#print "[DEBUG] Auto Match : Selected Core No. =" + str(i)  

		self.AutoRateList = []
		squish = squishend
		offset = depthstart
		self.isCalculated = True

		xstart = 60
		self.sortDataList =[]
		guagecount = 0
		for i in range(squishrange) :
			for j in range(depthrange) :
				retdata = py_correlator.correlate(squish, offset)
				if retdata != None :
					if len(self.sortDataList) == 0 :
						self.sortDataList.append((retdata[0], retdata[1], i, j))	
					else :
						count = 0
						flag = 0
						for data in self.sortDataList :
							if data[0] < retdata[0] :
								self.sortDataList.insert(count, (retdata[0], retdata[1], i, j)) 
								flag = 1
								break
							count = count + 1
						if flag == 0 :
							self.sortDataList.append((retdata[0], retdata[1], i, j))	

					self.AutoRateList.append((retdata[0], retdata[1]))
				offset = offset + self.depthinterval
				guagecount = guagecount + 1
			progress.SetProgress(guagecount)
			progress.Update()
			squish = squish - self.squishinterval
			offset = depthstart

		self.resultList.Clear()
		index = 0 
		for data in self.sortDataList :
			rate, b, x, y = data
			rate = int(100.0 * float(rate)) / 100.0
			result_txt = "r = " + str(rate) + " n = " + str(b) + " (" + str(index+1) + ")"	 
			self.resultList.InsertItems([result_txt], index)	 
			index = index + 1

		self.selectedNo = -1 
		if len(self.sortDataList) > 0 :
			self.resultList.Select(0)
			self.selectedNo = 0 

			data = self.sortDataList[0]	
			squish = squishend - data[2] * self.squishinterval
			offset = depthstart + data[3] * self.depthinterval
			py_correlator.prevCorrelate(1, squish, offset)

			# get best match-squish,offset,coef,rate,b
			self.valueD1.SetValue(str(squish))
			self.valueD3.SetValue(str(offset))
			if self.spliceFlag == 0 : 
				#self.parent.UpdateData()
				self.parent.Window.OnUpdateHoleELD()
			else :
				self.parent.UpdateELD(False)

			self.parent.OnUpdateLogData(True)
			self.applyBtn.Enable(True)

			#self.parent.OnGetData(self.parent.smoothDisplay, True)
			# CHANGED FROM TRUE TO FALSE BY 2009
			self.ApplyFlag = 0 
			self.parent.Window.UpdateDrawing()


	def OnSelectRate(self, event):
		if self.applyBtn.IsEnabled() == False :
			self.parent.OnShowMessage("Information", "You can not change rate now", 1)
			if self.selectedNo != -1 :
				self.resultList.Select(self.selectedNo)
			return

		index =0
		for i in range(self.resultList.GetCount()) :
			if self.resultList.IsSelected(i) == True :
				index = i
				self.selectedNo = index
				break
		data = self.sortDataList[index]
		squish = self.squishend - data[2] * self.squishinterval
		offset = self.depthstart + data[3] * self.depthinterval
		self.valueD1.SetValue(str(squish))
		self.valueD3.SetValue(str(offset))

		py_correlator.prevCorrelate(1, squish, offset)
		if self.spliceFlag == 0 :
			#self.parent.UpdateData()
			self.parent.Window.OnUpdateHoleELD()
		else :
			# CHANGED FROM TRUE TO FALSE BY 2009
			self.parent.UpdateELD(False)
		self.parent.OnUpdateLogData(True)
		self.parent.Window.UpdateDrawing()

	def OnApply(self, event):
		index =0
		for i in range(self.resultList.GetCount()) :
			if self.resultList.IsSelected(i) == True :
				index = i
				self.selectedNo = index
				break

		data = self.sortDataList[index]	
		squish = self.squishend - data[2] * self.squishinterval
		offset = self.depthstart + data[3] * self.depthinterval

		py_correlator.applyCorrelate(1, squish, offset)
		if self.spliceFlag == 0 : 
			#self.parent.UpdateData()
			self.parent.Window.OnUpdateHoleELD()
		else :
			self.parent.UpdateELD(False)

		self.parent.OnUpdateLogData(True)
		s = "Apply Stretch/Compress : " + str(squish) + "\n"
		self.parent.logFileptr.write(s)
		s = "Apply mudline adjusted shift : " + str(offset) + "\n\n"
		self.parent.logFileptr.write(s)

		self.ApplyFlag = 1
		self.parent.EldChange = True
		self.undoBtn.Enable(True)
		self.resetBtn.Enable(False)
		self.applyBtn.Enable(False)
		self.calopBtn.Enable(False)

		self.parent.Window.UpdateDrawing()

	def OnInitUI(self, flag):
		if flag == True :
			self.fileList.Clear()
		self.resultList.Clear()
		self.undoBtn.Enable(False)
		self.resetBtn.Enable(True)
		self.applyBtn.Enable(False)
		self.calopBtn.Enable(False)
		self.selectedNo = -1
		self.ApplyFlag = -1 

	def OnUndo(self, event):
		if self.ApplyFlag == 1 :
			self.undoBtn.Enable(False)
			self.applyBtn.Enable(True)
			py_correlator.undoCorrelate(1)
			if self.spliceFlag == 0 : 
				#self.parent.UpdateData()
				self.parent.Window.OnUpdateHoleELD()
			else :
				self.parent.UpdateELD(False)

			self.parent.OnUpdateLogData(False)

			self.parent.logFileptr.write("Undo Stretch/Compress and mudline adjusted shift \n\n")
			self.ApplyFlag = 0 
			self.resetBtn.Enable(True)
			self.calopBtn.Enable(True)
			self.resultList.DeselectAll()
			self.selectedNo = -1 
			self.parent.Window.UpdateDrawing()

	def OnDismiss(self, event):
		self.selectedNo = -1 
		if self.ApplyFlag == 0 :
			py_correlator.undoCorrelate(0)
			if self.spliceFlag == 0 :
				#self.parent.UpdateData()
				self.parent.Window.OnUpdateHoleELD()
			else :
				self.parent.UpdateELD(False)

			self.parent.OnUpdateLogData(False)
			self.parent.Window.autocoreNo = []
			self.parent.Window.UpdateDrawing()


class ELDPanel():
	def __init__(self, parent, mainPanel):
		self.mainPanel = mainPanel
		self.parent = parent
		self.leadLagValue = self.parent.leadLag
		self.polyline_list =[]
		self.addItemsInFrame()

	def addItemsInFrame(self):
		vbox_top = wx.BoxSizer(wx.VERTICAL)
		vbox = wx.BoxSizer(wx.VERTICAL)

		# Panel 2
		panel2 = wx.Panel(self.mainPanel, -1, style=wx.BORDER_SIMPLE)
		panel2.SetSizer(wx.BoxSizer(wx.VERTICAL))
		self.corrPlotCanvas = plot.PlotCanvas(panel2)

		#self.corrPlotCanvas.SetEnableZoom( True )
		self.corrPlotCanvas.SetEnableGrid( True )
		self.corrPlotCanvas.SetBackgroundColour("White")
		#self.corrPlotCanvas.Centre(wxBOTH)
		self.corrPlotCanvas.Show(True)

		xdata = [ (-self.parent.leadLag, 0),( 0, 0), (self.parent.leadLag, 0) ]
		self.xaxes = plot.PolyLine(xdata, legend='', colour='black', width =2)
		ydata = [ (0, -1),( 0, 1) ]
		self.yaxes = plot.PolyLine(ydata, legend='', colour='black', width =2)

		data = [ (-self.parent.leadLag, 0),( 0, 0), (self.parent.leadLag, 0) ]
		self.OnUpdateData(data, [])
		self.OnUpdateDrawing()
		
		crSubPanel = wx.Panel(panel2, -1)
		crSubPanel.SetSizer(wx.BoxSizer(wx.HORIZONTAL))
		bmp = wx.Bitmap("icons/sprocket.png")
		crSettingsBtn = wx.BitmapButton(crSubPanel, -1, bmp)
		self.crText = wx.StaticText(crSubPanel, -1, "Step: 0.135 | Window: 1.0 | Lead/Lag: 1.0")
		crFont = self.crText.GetFont()
		crFont.SetPointSize(10)
		self.crText.SetFont(crFont)
		crSubPanel.GetSizer().Add(self.crText, 1, wx.ALIGN_CENTER_VERTICAL)
		crSubPanel.GetSizer().Add(crSettingsBtn, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
		
		panel2.GetSizer().Add(self.corrPlotCanvas, 1, wx.EXPAND)
		panel2.GetSizer().Add(crSubPanel, 0, wx.EXPAND)
		
		panel2.Bind(wx.EVT_BUTTON, self.OnEvalSettings, crSettingsBtn)
		
		vbox.Add(panel2, 1, wx.EXPAND | wx.BOTTOM, 10)

		buttonsize = 300
		if platform_name[0] == "Windows" :
			buttonsize = 285
		self.fileList = wx.ListBox(self.mainPanel, -1, (0,0),(buttonsize,105), "", style=wx.LB_HSCROLL|wx.LB_NEEDED_SB)
		self.mainPanel.Bind(wx.EVT_LISTBOX, self.OnSelectTie, self.fileList)
		vbox.Add(self.fileList, 0, wx.BOTTOM, 3)

		# Panel 3
		panel3 = wx.Panel(self.mainPanel, -1)
		#hbox3 = wx.BoxSizer(wx.HORIZONTAL)
		hbox3 = wx.FlexGridSizer(1, 2)
		hbox3.AddGrowableCol(0)
		sizer31 = wx.StaticBoxSizer(wx.StaticBox(panel3, -1, 'Apply Option'), orient=wx.VERTICAL)
		
		if platform_name[0] == "Windows" :
			self.coreOnly = wx.RadioButton(panel3, -1, "This core only", style=wx.RB_GROUP)
		else :
			self.coreOnly = wx.RadioButton(panel3, -1, "This core only	 ", style=wx.RB_GROUP)
			
		self.mainPanel.Bind(wx.EVT_RADIOBUTTON, self.SetFlag, self.coreOnly)
		sizer31.Add(self.coreOnly)
		if platform_name[0] == "Windows" :
			self.coreAll = wx.RadioButton(panel3, -1, "All overlapping cores")
		else :
			self.coreAll = wx.RadioButton(panel3, -1, "All overlapping	\ncores")
		self.mainPanel.Bind(wx.EVT_RADIOBUTTON, self.SetFlag, self.coreAll)
		#self.coreOnly.SetValue(True)
		self.coreAll.SetValue(True)
		#self.coreOnly.Enable(False)
		self.SetFlag(None)
		sizer31.Add(self.coreAll, wx.BOTTOM, 1)

		self.floating = wx.CheckBox(panel3, -1, 'Lock top of core')
		self.floating.SetValue(True)
		self.mainPanel.Bind(wx.EVT_CHECKBOX, self.SetFloating, self.floating)
		sizer31.Add(self.floating, 0, wx.TOP, 4)

		hbox3.Add(sizer31, 1, wx.RIGHT, 10)

		buttonsize = 100
		if platform_name[0] == "Windows" :
			buttonsize = 135
			
		sizer32 = wx.GridSizer(4, 1)
		clearBtn = wx.Button(panel3, -1, "Remove", size=(buttonsize, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnClear, clearBtn)
		sizer32.Add(clearBtn)
		clearTieBtn = wx.Button(panel3, -1, "Clear Tie", size=(buttonsize, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnClearTie, clearTieBtn)
		sizer32.Add(clearTieBtn)
		lineTieBtn = wx.Button(panel3, -1, "Straight Line", size=(buttonsize, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnStraightTie, lineTieBtn)
		sizer32.Add(lineTieBtn)
		applyBtn = wx.Button(panel3, -1, "Match To Tie", size=(buttonsize, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnApply, applyBtn)
		#applyBtn.Enable(False)
		sizer32.Add(applyBtn)
		hbox3.Add(sizer32, 1)

		panel3.SetSizer(hbox3)
		vbox.Add(panel3, 0, wx.BOTTOM, 5)

		vbox.Add(wx.StaticText(self.mainPanel, -1, '*Sub menu for tie: On dot, right mouse button.', (5, 5)), 0, wx.BOTTOM, 9)
		#vbox.Add(wx.StaticText(self.mainPanel, -1, '*Log data is required.', (5, 5)), 0, wx.BOTTOM, 9)

		self.saveButton = wx.Button(self.mainPanel, -1, "Save ELD Table", size =(150, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnSAVE, self.saveButton)
		vbox.Add(self.saveButton, 0, wx.ALIGN_CENTER_VERTICAL)
		self.saveButton.Enable(False)

		vbox_top.Add(vbox, 1, wx.LEFT, 5)
		self.mainPanel.SetSizer(vbox_top)


	def OnSelectTie(self, event):
		max_count = self.fileList.GetCount()
		for i in range(max_count) :
			if self.fileList.IsSelected(i) == True :
				self.parent.Window.Highlight_Tie = i
				self.parent.Window.UpdateDrawing()
				break

	def OnInitUI(self):
		self.fileList.Clear()
		self.SetFlag(False)
		#self.floating.SetValue(True)
		#self.SetFloating(None)

	def OnSAVE(self, event):
		if self.parent.Window.LogData != [] :
			dlg = dialog.Message3Button(self.parent, "Do you want to create new eld file?")
			ret = dlg.ShowModal()
			dlg.Destroy()
			if ret == wx.ID_OK or ret == wx.ID_YES :
				flag = True
				if ret == wx.ID_YES :
					flag = False
				filename = self.parent.dataFrame.Add_TABLE("ELD" , "eld", flag, False, "")
				py_correlator.saveAttributeFile(filename, 4)
				s = "Save ELD Table: " + filename + "\n"
				self.parent.logFileptr.write(s)
				self.parent.OnShowMessage("Information", "Successfully Saved", 1)
				self.parent.EldChange = False 
		else :
			self.parent.OnShowMessage("Error", "No data to save", 1)

	def SetFloating(self, event):
		flag = self.floating.IsChecked()
		if self.parent.Window.LogTieData != [] : 
			self.parent.OnShowMessage("Error", "Please clean all core-log tie", 1)
			self.floating.SetValue(not flag)

		else :	
			flag = not self.floating.IsChecked()
			self.parent.Window.Floating = flag
			if flag == True : 
				py_correlator.setSaganOption(1)
			else :
				py_correlator.setSaganOption(0)

	def UpdateTieInfo(self, info, depth, tieNo):
		i = tieNo / 2 
		self.fileList.Delete(i)
		self.AddTieInfo(info, depth)
		self.fileList.Select(i)

	def AddTieInfo(self, info, depth):
		regflag = False
		i = 0
		for i in range(self.fileList.GetCount()) :
			data = self.fileList.GetString(i)
			start =0
			last =0
			last = data.find(" ", start) # hole
			start = last +1
			last = data.find(" ", start) # core
			start = last +1
			last = data.find(" ", start) # depth 
			start = last +1
			last = data.find(" ", start) # [TieTo] 
			start = last +1
			last = data.find(" ", start) # [Log] 
			start = last +1
			last = data.find(" ", start) # log depth 
			regdepth = float(data[start:last])
			if depth < regdepth :
				self.fileList.InsertItems([info], i)
				i = i * 2 + 1 
				self.parent.Window.OnSortList(i)
				regflag = True 
				break
		if regflag == False :
			count = self.fileList.GetCount()
			self.fileList.InsertItems([info], count)

	def DeleteTie(self, i):
		self.fileList.Delete(i)
		self.fileList.Select(i-1)
		self.parent.Window.activeSATie = -1
		self.parent.Window.saganDepth = -1

	def OnClear(self, evt):
		self.parent.Window.activeSATie = -1
		self.parent.Window.saganDepth = -1
		for i in range(self.fileList.GetCount()) :
			if self.fileList.IsSelected(i) == True :
				self.parent.Window.LogselectedTie = i * 2 
				self.parent.Window.DeleteLogTie()
				self.fileList.Select(i-1)
				self.parent.Window.UpdateDrawing()
				break
		#self.parent.ClearSaganTie(-1)

	def OnStraightTie(self, evt):
		self.parent.Window.MakeStraightLine()

	def OnClearTie(self, evt):
		self.parent.Window.activeSATie = -1
		last = len(self.parent.Window.LogTieData)
		countTies = self.fileList.GetCount()
		countTies = countTies * 2
		#print "[DEBUG] clear tie : last = " + str(last) + " all list=" + str(countTies)
		if last > countTies :
			self.parent.Window.OnClearTies(2)

	def OnApply(self, evt):
		self.parent.Window.activeSATie = -1
		last = len(self.parent.Window.LogTieData)
		if last > 0 :
			self.parent.Window.LogselectedTie = last -1
			self.parent.Window.MatchLog()
			self.parent.Window.LogselectedTie = -1
			self.parent.Window.UpdateDrawing()

	def SetFlag(self, evt):
		flag = 0 
		if self.coreAll.GetValue() == True :
			flag = 1 
		py_correlator.setSagan(flag)

	def OnAutoCorrelate(self, evt):
		self.parent.Window.ShowAutoPanel = True
	
	def OnEvalSettings(self, evt):
		pos = self.crText.GetScreenPositionTuple()
		dlg = dialog.CorrParamsDialog(self.mainPanel, self.parent.minDepthStep, self.parent.depthStep, self.parent.winLength, self.parent.leadLag)
		dlg.SetPosition(pos)
		if dlg.ShowModal() == wx.ID_OK:
			self.parent.OnEvalSetup(dlg.outDepthStep, dlg.outWinLength, dlg.outLeadLag)
			self.parent.OnUpdateGraphSetup(3)
			self.parent.Window.OnUpdateTie(2)
	
	def OnUpdate(self):
		self.corrPlotCanvas.Clear()
		data = [ (-self.parent.leadLag, 0),( 0, 0), (self.parent.leadLag, 0) ]
		self.OnUpdateData(data, [])
		self.OnUpdateDrawing()
		self.UpdateEvalStatus()
		self.mainPanel.Update()
		self.parent.Update()

	def UpdateEvalStatus(self):
		roundedDepthStep = int(10000.0 * float(self.parent.depthStep)) / 10000.0
		self.crText.SetLabel("Step: {} | Window: {} | Lead/Lag: {}".format(roundedDepthStep, self.parent.winLength, self.parent.leadLag))
		
	def OnUpdateDepth(self, data):
		depthstep = int(10000.0 * float(data)) / 10000.0
		self.depth.SetValue(str(depthstep))

	def OnUpdateData(self, data, bestdata):
		line = plot.PolyLine(data, legend='', colour='red', width =2) 
		self.polyline_list.append(line)
		if bestdata != [] : 
			bestline = plot.PolyLine(bestdata, legend='', colour='blue', width =5) 
			self.polyline_list.append(bestline)

	# 9/18/2013 brg: duplication
	def OnAddFirstData(self, data, bestdata, best):
		line = plot.PolyLine(data, legend='', colour='red', width =2) 
		self.polyline_list.append(line)
		if bestdata != [] : 
			bestline = plot.PolyLine(bestdata, legend='', colour='blue', width =5) 
			self.polyline_list.append(bestline)

	def OnAddData(self, data):
		line = plot.PolyLine(data, legend='', colour='grey', width =2) 
		self.polyline_list.append(line)

	def OnUpdateDrawing(self):
		self.polyline_list.append(self.xaxes)
		self.polyline_list.append(self.yaxes)
		gc = plot.PlotGraphics(self.polyline_list, 'Evaluation Graph', 'depth Axis', 'coef Axis')
		self.corrPlotCanvas.Draw(gc, xAxis = (-self.parent.leadLag , self.parent.leadLag), yAxis = (-1, 1))	
		self.polyline_list = []


class AgeDepthPanel():
	def __init__(self, parent, mainPanel):
		self.mainPanel = mainPanel
		self.parent = parent
		self.leadLagValue = self.parent.leadLag
		self.X = -1 
		self.ageX = -1 
		self.selectedAge = False 
		self.addItemsInFrame()

	def addItemsInFrame(self):
		vbox_top = wx.BoxSizer(wx.VERTICAL)
		vbox = wx.BoxSizer(wx.VERTICAL)

		#vbox.Add(wx.StaticText(self.mainPanel, -1, 'Age Model', (5, 5)), 0, wx.TOP| wx.LEFT, 9)

		self.viewBtn = wx.ToggleButton(self.mainPanel, -1, "Age Model View", size = (140, 25))
		self.mainPanel.Bind(wx.EVT_TOGGLEBUTTON, self.SetChangeView, self.viewBtn)
		vbox.Add(self.viewBtn, 0, wx.TOP, 9)
		# brgtodo 9/6/2014: Use a spreadsheet instead
		vbox.Add(wx.StaticText(self.mainPanel, -1, '   CSF      CCSF       eld      Age(Ma)     Name', (5, 5)), 0, wx.TOP, 9)

		# Panel 1
		buttonsize = 300
		if platform_name[0] == "Windows" :
			buttonsize = 285
			
		if self.parent.Height > 768 :
			self.ageList = wx.ListBox(self.mainPanel, -1, (0, 0), (buttonsize,220), "", style=wx.LB_HSCROLL|wx.LB_NEEDED_SB|wx.LB_EXTENDED)	 
			font = self.ageList.GetFont()
			font.SetFamily(wx.FONTFAMILY_ROMAN)
			self.ageList.SetFont(font)
			#self.ageList = gizmos.TreeListCtrl(self.mainPanel, -1, (0,0), size=(buttonsize,220), style = wx.TR_DEFAULT_STYLE| wx.TR_FULL_ROW_HIGHLIGHT)

		else :
			#self.ageList = wx.ListBox(self.mainPanel, -1, (0, 0), (buttonsize,170), "", style=wx.LB_HSCROLL|wx.LB_NEEDED_SB|wx.LB_EXTENDED)	 
			self.ageList = wx.ListBox(self.mainPanel, -1, (0, 0), (buttonsize,120), "", style=wx.LB_HSCROLL|wx.LB_NEEDED_SB|wx.LB_EXTENDED)	 
			font = self.ageList.GetFont()
			font.SetFamily(wx.FONTFAMILY_ROMAN)
			self.ageList.SetFont(font)
			#self.ageList = gizmos.TreeListCtrl(self.mainPanel, -1, (0,0), size=(buttonsize,170), style = wx.TR_DEFAULT_STYLE| wx.TR_FULL_ROW_HIGHLIGHT)

		#self.ageList.SetString(0, "mbsf(m)")
		#self.ageList.SetString(1, "mcd(m)")
		#self.ageList.SetString(2, "eld(m)")
		#self.ageList.SetString(3, "age(Ma)")
		#self.ageList.SetString(4, "name")
		vbox.Add(self.ageList, 0, wx.BOTTOM | wx.TOP, 3)

		#self.mainPanel.Bind(wx.EVT_LISTBOX_DCLICK, self.OnAgeData, self.ageList)
		self.ageList.Bind(wx.EVT_LISTBOX, self.OnAgeData)

		self.ageList.SetForegroundColour(wx.BLACK)
		self.ageList.InsertItems(['00.00 \t00.00 \t00.00 \t00.00 \tX *handpick'], 0)
		#self.ageList.SetFirstItemStr('00.00')

		self.ageList.Select(0)

		# Panel 2
		panel2 = wx.Panel(self.mainPanel, -1)
		grid2 = wx.FlexGridSizer(1, 2)
		grid2.AddGrowableCol(1, 1)

		sizer21 = wx.StaticBoxSizer(wx.StaticBox(panel2, -1, 'User-defined Age'), orient=wx.VERTICAL)
		grid21 = wx.FlexGridSizer(4, 2)
	
		if platform_name[0] == "Windows" :					
			self.depth_label = wx.StaticText(panel2, -1, "CCSF(m)")
			grid21.Add(self.depth_label, 0, wx.TOP, 12)
			self.depth = wx.TextCtrl(panel2, -1, "0.0", size =(70, 25), style=wx.SUNKEN_BORDER )
			grid21.Add(self.depth, 0, wx.TOP| wx.RIGHT , 9)
			grid21.Add(wx.StaticText(panel2, -1, "Age(Ma)"), 0, wx.TOP, 12)
			self.age = wx.TextCtrl(panel2, -1, "0.0", size =(70, 25), style=wx.SUNKEN_BORDER )
			grid21.Add(self.age, 0, wx.TOP| wx.RIGHT, 9)
			grid21.Add(wx.StaticText(panel2, -1, "Label"), 0, wx.TOP, 12)
			self.nametxt = wx.TextCtrl(panel2, -1, "X", size =(70, 25), style=wx.SUNKEN_BORDER )
			grid21.Add(self.nametxt, 0, wx.TOP| wx.RIGHT | wx.BOTTOM, 9)
			grid21.Add(wx.StaticText(panel2, -1, "Comment"), 0, wx.TOP, 12)
			self.commenttxt = wx.TextCtrl(panel2, -1, "", size =(70, 25), style=wx.SUNKEN_BORDER )
			grid21.Add(self.commenttxt, 0, wx.TOP| wx.RIGHT | wx.BOTTOM, 9)
			sizer21.Add(grid21, 0, wx.LEFT | wx.RIGHT, 5)
		else :
			self.depth_label = wx.StaticText(panel2, -1, "CCSF(m)")
			grid21.Add(self.depth_label)
			self.depth = wx.TextCtrl(panel2, -1, "0.0", size =(70, 25), style=wx.SUNKEN_BORDER )
			grid21.Add(self.depth, 0, wx.LEFT, 9)
			grid21.Add(wx.StaticText(panel2, -1, "Age(Ma)"))
			self.age = wx.TextCtrl(panel2, -1, "0.0", size =(70, 25), style=wx.SUNKEN_BORDER )
			grid21.Add(self.age, 0, wx.LEFT, 9)
			grid21.Add(wx.StaticText(panel2, -1, "Label"))
			self.nametxt = wx.TextCtrl(panel2, -1, "X", size =(70, 25), style=wx.SUNKEN_BORDER )
			grid21.Add(self.nametxt, 0, wx.LEFT, 9)
			grid21.Add(wx.StaticText(panel2, -1, "Comment"))
			self.commenttxt = wx.TextCtrl(panel2, -1, "", size =(70, 25), style=wx.SUNKEN_BORDER )
			grid21.Add(self.commenttxt, 0, wx.LEFT, 9)
			sizer21.Add(grid21)			
		grid2.Add(sizer21)

		grid22 = wx.GridSizer(4, 1)
		removeBtn = wx.Button(panel2, -1, "Remove", size =(110, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnRemoveAge, removeBtn)
		grid22.Add(removeBtn, 0, wx.TOP, 1)

		clearBtn = wx.Button(panel2, -1, "Clear All", size =(110, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnClearList, clearBtn)
		grid22.Add(clearBtn, 0, wx.TOP, 1)

		#originBtn = wx.Button(panel2, -1, "Update Origin", size = (120, 30))
		#self.mainPanel.Bind(wx.EVT_BUTTON, self.SetORIGIN, originBtn)
		#grid22.Add(originBtn, 0, wx.TOP, 1)
		#originBtn.Enable(False)

		addBtn = wx.Button(panel2, -1, "Add Datum", size = (110, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnAddAge, addBtn)
		grid22.Add(addBtn, 0, wx.TOP, 1)
		addBtn = wx.Button(panel2, -1, "Update Datum", size = (110, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnUpdateDatum, addBtn)
		grid22.Add(addBtn, 0, wx.TOP, 1)

		if platform_name[0] == "Windows" :			
			grid2.Add(grid22, 0, wx.LEFT| wx.TOP, 11)
		else :
			grid2.Add(grid22, 0, wx.LEFT| wx.TOP, 9)

		panel2.SetSizer(grid2)
		vbox.Add(panel2, 0, wx.TOP, 9)

		# Panel 3
		panel3 = wx.Panel(self.mainPanel, -1)
		grid3 = wx.FlexGridSizer(1, 2)
		grid3.AddGrowableCol(1, 1)

		sizer31 = wx.StaticBoxSizer(wx.StaticBox(panel3, -1, 'Plot age versus'), orient=wx.VERTICAL)
		if platform_name[0] == "Windows" :	
			self.plotMbsfOpt = wx.RadioButton(panel3, -1, "CSF                ", style=wx.RB_GROUP)
		else :
			self.plotMbsfOpt = wx.RadioButton(panel3, -1, "CSF", style=wx.RB_GROUP)

		self.plotMbsfOpt.SetValue(False)	
		self.mainPanel.Bind(wx.EVT_RADIOBUTTON, self.SetChangePlot, self.plotMbsfOpt)
		sizer31.Add(self.plotMbsfOpt)
		self.plotMcdOpt = wx.RadioButton(panel3, -1, "CCSF")
		self.plotMcdOpt.SetValue(True)	
		self.mainPanel.Bind(wx.EVT_RADIOBUTTON, self.SetChangePlot, self.plotMcdOpt)
		sizer31.Add(self.plotMcdOpt)

		self.plotEldOpt = wx.RadioButton(panel3, -1, "eld")
		self.mainPanel.Bind(wx.EVT_RADIOBUTTON, self.SetChangePlot, self.plotEldOpt)
		self.plotEldOpt.Enable(False)
		sizer31.Add(self.plotEldOpt)
		grid3.Add(sizer31)

		grid32 = wx.GridSizer(2, 1)

		saveBtn = wx.Button(panel3, -1, "Save Age/Depth", size = (120, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnSAVE, saveBtn)
		grid32.Add(saveBtn, 0, wx.TOP | wx.EXPAND, 1)

		saveBtn = wx.Button(panel3, -1, "Save Age Model", size = (120, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnSAVETimeSeries, saveBtn)
		grid32.Add(saveBtn, 0, wx.TOP | wx.EXPAND, 1)

		grid3.Add(grid32, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 9)
		panel3.SetSizer(grid3)
		vbox.Add(panel3, 0, wx.TOP, 9)

		# Panel 31 
		#panel31 = wx.Panel(self.mainPanel, -1)
		#box31 = wx.BoxSizer(wx.HORIZONTAL)
		#self.enableBtn = wx.ToggleButton(panel3, -1, "Enable Drag", size = (buttonsize, 30))
		#self.mainPanel.Bind(wx.EVT_TOGGLEBUTTON, self.SetEnableDrag, self.enableBtn)
		#self.enableBtn.Enable(False)
		#box31.Add(self.enableBtn)
		#grid31.Add(self.enableBtn)

		#resetBtn = wx.Button(panel31, -1, "Reset", size =(120, 30))
		#self.mainPanel.Bind(wx.EVT_BUTTON, self.OnReset, resetBtn)
		#box31.Add(resetBtn, 0, wx.LEFT, 9)
		#resetBtn.Enable(False)

		#panel31.SetSizer(box31)
		#vbox.Add(panel31, 0, wx.TOP, 9)

		# Panel 4 
		panel4 = wx.Panel(self.mainPanel, -1)
		sizer4 = wx.StaticBoxSizer(wx.StaticBox(panel4, -1, 'Age Scale'), orient=wx.VERTICAL)
		self.slider1 = wx.Slider(panel4, -1, 1, 1, 5, size=(270, -1))
		self.slider1.SetValue(1)
		self.mainPanel.Bind(wx.EVT_COMMAND_SCROLL, self.OnAgeZoom, self.slider1)
		sizer4.Add(self.slider1, 0, flag=wx.EXPAND)

		grid42 = wx.FlexGridSizer(1, 5)
		grid42.Add(wx.StaticText(panel4, -1, 'min:', (5, 5)))
		self.min_age = wx.TextCtrl(panel4, -1, "0.0", size =(50, 25), style=wx.SUNKEN_BORDER | wx.TE_PROCESS_ENTER )
		grid42.Add(self.min_age)
		grid42.Add(wx.StaticText(panel4, -1, 'max:', (5, 5)), 0, wx.LEFT, 10)
		self.max_age = wx.TextCtrl(panel4, -1, "8.0", size =(50, 25), style=wx.SUNKEN_BORDER | wx.TE_PROCESS_ENTER )
		grid42.Add(self.max_age)
		testbtn = wx.Button(panel4, -1, "Apply", size=(60,25))
		grid42.Add(testbtn, 0, wx.LEFT, 10)
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnAgeViewAdjust, testbtn)

		sizer4.Add(grid42, 0, wx.TOP, 5)

		#sizer4.Add(self.slider1)
		panel4.SetSizer(sizer4)
		vbox.Add(panel4, 0, wx.TOP, 9)

		# Panel 5 
		panel5 = wx.Panel(self.mainPanel, -1)
		sizer5 = wx.StaticBoxSizer(wx.StaticBox(panel5, -1, 'Depth Scale'), orient=wx.VERTICAL)
		self.slider2 = wx.Slider(panel5, -1, 1, 1, 5, size=(270, -1))
		self.slider2.SetValue(1)
		self.mainPanel.Bind(wx.EVT_COMMAND_SCROLL, self.OnAgeDepthZoom, self.slider2)
		sizer5.Add(self.slider2, 0,wx.EXPAND)

		grid51 = wx.FlexGridSizer(1, 5)
		grid51.Add(wx.StaticText(panel5, -1, 'min:', (5, 5)))
		self.min_depth = wx.TextCtrl(panel5, -1, "0.0", size =(50, 25), style=wx.SUNKEN_BORDER | wx.TE_PROCESS_ENTER )
		grid51.Add(self.min_depth)
		grid51.Add(wx.StaticText(panel5, -1, 'max:', (5, 5)), 0, wx.LEFT, 10)
		self.max_depth = wx.TextCtrl(panel5, -1, "100.0", size =(50, 25), style=wx.SUNKEN_BORDER | wx.TE_PROCESS_ENTER )
		grid51.Add(self.max_depth)
		testbtn = wx.Button(panel5, -1, "Apply", size=(60,25))
		grid51.Add(testbtn, 0, wx.LEFT, 10)
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnDepthViewAdjust, testbtn)
		sizer5.Add(grid51, 0, wx.TOP, 5)

		panel5.SetSizer(sizer5)
		vbox.Add(panel5, 0, wx.TOP, 3)

		# Panel 6 
		panel6 = wx.Panel(self.mainPanel, -1)
		sizer6 = wx.StaticBoxSizer(wx.StaticBox(panel6, -1, 'Splice Depth Scale'), orient=wx.VERTICAL)
		self.slider3 = wx.Slider(panel6, -1, 10, 1, 40)#, size=(270, -1))
		self.slider3.SetValue(20)
		self.mainPanel.Bind(wx.EVT_COMMAND_SCROLL, self.OnSpliceDepthZoom, self.slider3)
		sizer6.Add(self.slider3, 0, wx.EXPAND)
		panel6.SetSizer(sizer6)
		vbox.Add(panel6, 0, wx.TOP | wx.EXPAND, 3)

		vbox_top.Add(vbox, 1, wx.LEFT, 5)
		self.mainPanel.SetSizer(vbox_top)

		self.startX = 40
		self.startY = 40
		self.AgeDataList = []
		self.max = 70.0 
		self.firstPntAge = 0.0, self.startX
		self.firstPntDepth = 0.0, self.startY

	def OnAgeData(self, evt):
                selected_item = "" 
                if platform_name[0] == "Windows" :
                        age_list = self.ageList.GetSelections()
                        for sel in age_list :
                                selected_item = self.ageList.GetString(sel)
                else :
                        selected_item = self.ageList.GetStringSelection()

		self.selectedAge = False 
		end = selected_item.find("*handpick", 0)
		if end > 0 :
			items = selected_item.split()
			if self.parent.Window.mbsfDepthPlot == 1 : # if mcd
				self.depth.SetValue(items[0])
			else :
				self.depth.SetValue(items[1])
			self.age.SetValue(items[3])
			self.nametxt.SetValue(items[4])
			self.selectedAge = True 
			

	def OnAgeViewAdjust(self, evt):
		min = float(self.min_age.GetValue()) 
		max = float(self.max_age.GetValue()) 
		self.parent.Window.minAgeRange = min
		x = (self.parent.Window.splicerX - 100 - self.parent.Window.compositeX - self.parent.Window.AgeShiftX)
		self.parent.Window.ageLength = x / (max - min) * 1.0
		self.parent.Window.maxAgeRange = int(max)
		#if max > self.parent.Window.maxAgeRange  :
		#	self.parent.Window.maxAgeRange = int(max)
		#	self.maxAge.SetValue(str(self.parent.Window.maxAgeRange))
		self.slider1.SetValue(1)
		self.parent.Window.UpdateDrawing()


	def OnDepthViewAdjust(self, evt):
		min = float(self.min_depth.GetValue()) 
		max = float(self.max_depth.GetValue()) 
		self.parent.Window.rulerStartAgeDepth = min
		self.max = max

		x = (self.parent.Window.Height - self.parent.Window.startAgeDepth - self.parent.Window.AgeShiftY) * self.parent.Window.ageGap
		self.parent.Window.ageYLength = x / (max - min) * 1.0
		self.slider2.SetValue(1)
		self.parent.Window.UpdateDrawing()


	def OnSAVE(self, evt):
		if len(self.parent.Window.UserdefStratData) == 0:
			self.parent.OnShowMessage("Error", "There is no userdefined age datum", 1)
			return

		dlg = dialog.Message3Button(self.parent, "Do you want to create new age/depth?")
		ret = dlg.ShowModal()
		dlg.Destroy()
		if ret == wx.ID_OK or ret == wx.ID_YES :
			flag = True
			if ret == wx.ID_YES :
				flag = False
			filename = self.parent.dataFrame.OnSAVE_AGES(flag, False)
			s = "Save Age Model: " + filename + "\n"
			self.parent.logFileptr.write(s)
			self.parent.OnShowMessage("Information", "Successfully Saved", 1)
			self.parent.AgeChange = False 


	def OnSAVETimeSeries(self, evt):
		dlg = dialog.Message3Button(self.parent, "Do you want to create new age model?")
		ret = dlg.ShowModal()
		dlg.Destroy()
		if ret == wx.ID_OK or ret == wx.ID_YES :
			flag = True
			if ret == wx.ID_YES :
				flag = False
			filename = self.parent.dataFrame.OnSAVE_SERIES(flag, False)
			s = "Save Time Series: " + filename + "\n"
			self.parent.logFileptr.write(s)
			self.parent.OnShowMessage("Information", "Successfully Saved", 1)
			self.parent.TimeChange = False 


	def OnMaxAgeEnter(self, evt):
		#self.parent.Window.maxAgeRange = int(self.maxAge.GetValue())
		#self.maxAge.SetValue(str(self.parent.Window.maxAgeRange))
		self.parent.Window.UpdateDrawing()

	def OnInitUI(self):
		self.OnNewStratList()
		self.OnClearList(1)
		self.parent.Window.UserdefStratData = []

	def OnAddAge(self, evt):
		pickname = self.nametxt.GetValue()
		pickdepth = float(self.depth.GetValue())
		pickmcd = pickdepth
		rate = py_correlator.getMcdRate(pickdepth)
		if self.parent.Window.mbsfDepthPlot == 0 : 
			pickdepth = (1.0 / rate) * pickmcd
			pickdepth = int(100.0 * pickdepth) / 100.0
		else :
			pickmcd = rate * pickdepth
			pickmcd = int(100.0 * pickmcd) / 100.0
                strItem = ""
		str_ba = str(pickdepth)
		max_ba = len(str_ba)
		start_ba = str_ba.find('.', 0)
		str_ba = str_ba[start_ba:max_ba]
		max_ba = len(str_ba)
		space_bar = ""
		if platform_name[0] == "Windows" :
                        space_bar = " "
                        
		if max_ba < 3 :
			strItem = str(pickdepth) + "0 \t"
		else :
			strItem = str(pickdepth) + space_bar + "\t"

		str_ba = str(pickmcd)
		max_ba = len(str_ba)
		start_ba = str_ba.find('.', 0)
		str_ba = str_ba[start_ba:max_ba]
		max_ba = len(str_ba)
		if max_ba < 3 :
			strItem += str(pickmcd) + "0 \t" + str(pickmcd) + "0 \t"
		else :
			strItem += str(pickmcd) + space_bar + "\t" + str(pickmcd) + space_bar + "\t"

		# NEED TO CHECK THERE IS SAME DEPTH ALREADY REGISTERED
		for i in range(self.ageList.GetCount()) :
			ageStrItem = self.ageList.GetString(i)
			ageItem = ageStrItem.split()
			depth = float(ageItem[0])
			if depth == pickdepth :
				self.parent.OnShowMessage("Error", "Same mbsf is already registered", 1)
				return

		pickage = float(self.age.GetValue())
		if self.parent.Window.maxAgeRange < pickage :
			self.parent.Window.maxAgeRange = int(pickage) + 2
			self.maxAge.SetValue(str(self.parent.Window.maxAgeRange))

		ba = int(1000.0 * float(pickage)) / 1000.0
		str_ba = str(ba)
		max_ba = len(str_ba)
		start_ba = str_ba.find('.', 0)
		str_ba = str_ba[start_ba:max_ba]
		max_ba = len(str_ba)
		if max_ba < 3 :
			strItem += str(ba) + "0 \t" + pickname + " *handpick"
		else :
			strItem += str(ba) + space_bar + "\t" + pickname + " *handpick"

		order = self.OnAddAgeToList(strItem)
		#self.parent.Window.AddUserdefAge(pickname, pickdepth, pickmcd, pickage, order)

		comment = self.commenttxt.GetValue()
		self.parent.Window.AddUserdefAge(pickname, pickdepth, pickmcd, pickage, comment)
		self.parent.Window.AddToAgeList(pickname, pickdepth, pickmcd, pickage, order, "handpick")
		self.parent.Window.UpdateDrawing()
		self.parent.AgeChange = True 


	def OnUpdateDatum(self, evt):
		if self.selectedAge == True :
			for i in range(self.ageList.GetCount()) :
				if self.ageList.IsSelected(i) == True :
					if i == 0 :
						self.SetORIGIN(evt)
						self.ageList.Select(0)
						break
					else :
						self.ageList.Delete(i)
						data = self.parent.Window.AgeDataList[i-1]
						if data[6] == -1 or data[6] == "handpick" :
							idx = 0
							for defdata in self.parent.Window.UserdefStratData :
								userdata = defdata[0]
								if data[5] == userdata[0] :
									self.parent.Window.UserdefStratData.pop(idx)
									break
								idx = idx + 1
						self.parent.Window.AgeDataList.remove(data)
						self.OnAddAge(evt)
						self.ageList.Select(i)
						break
			self.parent.TimeChange = True
			self.parent.Window.UpdateDrawing()
		else :
			self.parent.OnShowMessage("Error", "User defined datum can be modified", 1)


	def SetORIGIN(self, evt):
		pickdepth = float(self.depth.GetValue())
		pickdepth = int(100.0 * pickdepth) / 100.0
		str_ba = str(pickdepth)
		max_ba = len(str_ba)
		start_ba = str_ba.find('.', 0)
		str_ba = str_ba[start_ba:max_ba]
		max_ba = len(str_ba)
		space_bar = ""
		if platform_name[0] == "Windows" :
                        space_bar = " "
                        
		if max_ba < 3 :
			strItem = str(pickdepth) + "0 \t"  + str(pickdepth) + "0 \t" + str(pickdepth) + "0 \t"
		else :
			strItem = str(pickdepth) + space_bar + "\t"  + str(pickdepth) + space_bar + "\t" + str(pickdepth) + space_bar + "\t"

		pickage = float(self.age.GetValue())
		pickage = int(1000.0 * pickage) / 1000.0
		pickname = 'X'

		str_ba = str(pickage)
		max_ba = len(str_ba)
		start_ba = str_ba.find('.', 0)
		str_ba = str_ba[start_ba:max_ba]
		max_ba = len(str_ba)
		if max_ba < 3 :
			strItem += str(pickage) + "0 \t" + pickname + " *handpick"
		else :
			strItem += str(pickage) + space_bar + "\t" + pickname + " *handpick"

		self.ageList.Delete(0)
		self.ageList.InsertItems([strItem], 0)
		self.parent.Window.firstPntAge = pickage
		self.parent.Window.firstPntDepth = pickdepth
		self.parent.Window.UpdateDrawing()
		self.parent.TimeChange = True


	def OnReset(self, evt):
		self.parent.Window.AgeShiftX = 0
		self.parent.Window.AgeShiftY = 0
		self.parent.Window.UpdateDrawing()

	def OnAgeDepthZoom(self, evt):
		# 1 - 20
		# start -> 80 : 60 + (idx * 20) 
		idx = self.slider2.GetValue()
		#self.parent.Window.ageYLength = 60 + (idx * 20)
		min = self.parent.Window.rulerStartAgeDepth
		max = min + self.max 
		x = (self.parent.Window.Height - self.parent.Window.startAgeDepth - self.parent.Window.AgeShiftY) * self.parent.Window.ageGap
		self.parent.Window.ageYLength = idx * x / (max - min) * 1.0
		self.parent.Window.UpdateDrawing()

	def OnAgeZoom(self, evt):
		# 1- 20
		# start -> 95  : 90 + (idx * 5)
		idx = self.slider1.GetValue()  
		#self.parent.Window.ageLength = 90 + (idx * 5)
		min = self.parent.Window.minAgeRange 
		max = self.parent.Window.maxAgeRange 
		x = (self.parent.Window.splicerX - 100 - self.parent.Window.compositeX - self.parent.Window.AgeShiftX)
		self.parent.Window.ageLength = idx * x / (max - min) * 1.0
		self.parent.Window.UpdateDrawing()

	def OnSpliceDepthZoom(self, evt):
		idx = 21 - self.slider3.GetValue()
		self.parent.Window.spliceYLength = 60 - (idx * 2.3)
		self.parent.Window.UpdateDrawing()

	def SetChangeSplice(self, evt):
		if self.plotSpliceOpt.GetValue() == True :
			self.parent.Window.AgeSpliceHole = True
		else :
			self.parent.Window.AgeSpliceHole = False 
		self.parent.Window.UpdateDrawing()

	def SetChangePlot(self, evt):
		if self.plotMbsfOpt.GetValue() == True :
			self.parent.Window.mbsfDepthPlot = 1 
			self.depth_label.SetLabel("Mbsf(m)")
		elif self.plotMcdOpt.GetValue() == True :
			self.parent.Window.mbsfDepthPlot = 0 
			self.depth_label.SetLabel("Mcd(m)")
		elif self.plotEldOpt.GetValue() == True :
			self.parent.Window.mbsfDepthPlot = 2 
			self.depth_label.SetLabel("Eld(m)")
			
		self.parent.Window.UpdateDrawing()

	def OnAddAgeToListAt(self, strItem, order):
		# checking
		for i in range(self.ageList.GetCount()) :
			if i != 0 and self.ageList.GetString(i) == strItem :
				return 0

		count  = self.ageList.GetCount() -1
		if order < count :
			self.ageList.InsertItems([strItem], order + 1)
		else : 
			self.ageList.InsertItems([strItem], self.ageList.GetCount())
		return 1

	def OnAddAgeToList(self, strItem):
		# checking
		# check Age, add
		newAgeItem = strItem.split()
		newAge = float(newAgeItem[0])
		age = 0.0
		prevAge = 0.0
		order = 0
		for i in range(self.ageList.GetCount()) :
			ageStrItem = self.ageList.GetString(i)
			if i != 0 and self.ageList.GetString(i) == strItem :
				return -1 
			ageItem = ageStrItem.split()
			age = float(ageItem[0])
			if (prevAge < newAge) and (age > newAge) :
				break

			order = order + 1
			prevAge = age

		self.ageList.InsertItems([strItem], order)
		#self.ageList.Select(order)
		order = order -1

		return order 

	def OnNewStratList(self):
		#self.stratList.Clear()
		pass

	def OnAddStratToList(self):
		#typeList = [0, 0, 0, 0, 0]
		#self.stratList.Clear()
		#for data in self.parent.Window.StratData:
		#	for r in data:
		#		order, hole, name, label, start, stop, rawstart, rawstop, age, type = r
		#		if typeList[0] == 0 and type == 0 :  #DIATOMS - GOLD
		#			typeList[0] = 1
		#			self.stratList.InsertItems(['Diatoms'], 0)
		#		elif typeList[1] == 0 and type == 1 : #RADIOLARIA - PURPLE
		#			typeList[1] = 1
		#			self.stratList.InsertItems(['Radiolaria'], 0)
		#		elif typeList[2] == 0 and type == 2 : #FORAMINIFERA - GREEN
		#			typeList[2] = 1
		#			self.stratList.InsertItems(['Foraminifera'], 0)
		#		elif typeList[3] == 0 and type == 3 : #NANNOFOSSILS - PINK 
		#			typeList[3] = 1
		#			self.stratList.InsertItems(['Nannofossils'], 0)
		#		elif typeList[4] == 0 and type == 4 : #PALEOMAG - BLUE 
		#			typeList[4] = 1
		#			self.stratList.InsertItems(['Paleomag'], 0)
		pass

	def SetChangeView(self, evt):
		if self.viewBtn.GetValue() == True : 
			self.X = self.parent.Window.splicerX 
			if self.ageX == -1 :
				self.parent.Window.splicerX = int(self.parent.Window.Width * 0.6)
			else :
				self.parent.Window.splicerX = self.ageX
			self.parent.Window.MainViewMode = False
			self.parent.Window.DrawData["MouseInfo"] = []
			self.viewBtn.SetLabel("Main Core View")
			self.OnAgeViewAdjust(evt)
			self.OnDepthViewAdjust(evt)
		else :
			self.ageX = self.parent.Window.splicerX 
			self.parent.Window.splicerX = self.X
			self.parent.Window.MainViewMode = True 
			self.parent.Window.DrawData["MouseInfo"] = []
			self.viewBtn.SetLabel("Age Model View")
		self.parent.Window.UpdateDrawing()


	def SetEnableDrag(self, event):
		if self.parent.Window.AgeEnableDrag == 0 :
			self.parent.Window.AgeEnableDrag = 1 
			self.enableBtn.SetLabel("Disable Drag")
		else :
			self.parent.Window.AgeEnableDrag = 0 
			self.enableBtn.SetLabel("Enable Drag")


	def OnClearList(self, evt):
		#strItem = self.ageList.GetString(0)

		strItem = ""
		if self.parent.Window.firstPntDepth == 0 and self.parent.Window.firstPntAge == 0 : 
			strItem = "0.00 \t 0.00 \t 0.00 \t 0.00 \t X *handpick"
		else :
			strItem = str(self.parent.Window.firstPntDepth) +  " \t " +  str(self.parent.Window.firstPntDepth) + " \t " + str(self.parent.Window.firstPntDepth) + " \t " + str(self.parent.Window.firstPntAge) + " \t X *handpick"

		self.ageList.Clear()
		self.ageList.InsertItems([strItem], 0)
		#self.ageList.Select(0)
		self.AgeDataList = []
		self.firstPntAge = 0.0, self.startX
		self.firstPntDepth = 0.0, self.startY

		self.parent.Window.AgeDataList = []
		#self.parent.Window.UserdefStratData = []
		self.parent.TimeChange = True
		self.parent.Window.UpdateDrawing()


	def OnRemoveAge(self, evt):
		for i in range(self.ageList.GetCount()) :
			if i != 0 and self.ageList.IsSelected(i) == True :
				self.ageList.Delete(i)
				self.ageList.Select(i-1)
				data = self.parent.Window.AgeDataList[i-1]
				if data[6] == -1 or data[6] == 'handpick':
					idx = 0
					for defdata in self.parent.Window.UserdefStratData :
						userdata = defdata[0]
						#if (data[1] == userdata[1]) and (data[3] == userdata[3]) :
						if data[5] == userdata[0] :
							if (data[2] == userdata[2]) and (data[3] == userdata[3]) :
								#print "[DEBUG] datum " + data[5] + " at " + str(data[2]) + "-" + str(data[3]) + " is deleted" 
								self.parent.Window.UserdefStratData.pop(idx)
								break
						idx = idx + 1
				self.parent.Window.AgeDataList.remove(data)
				break
		if self.ageList.GetCount() == 1 :
			strItem = self.ageList.GetString(0)
			self.ageList.Clear()
			self.ageList.InsertItems([strItem], 0)
			self.ageList.Select(0)
			self.firstPntAge = 0.0, self.startX
			self.firstPntDepth = 0.0, self.startY
		self.parent.Window.UpdateDrawing()
		self.parent.TimeChange = True

class FilterPanel():
	def __init__(self, parent, mainPanel):
		self.mainPanel = mainPanel
		self.parent = parent
		self.locked = False
		self.prevSelected = 0
		self.addItemsInFrame()
		
	def addItemsInFrame(self):
		vbox_top = wx.BoxSizer(wx.VERTICAL)

		vbox_top.Add(wx.StaticText(self.mainPanel, -1, "Set Filter Range : "), 0, wx.LEFT | wx.TOP, 9)

		buttonsize = 290
		if platform_name[0] == "Windows" :
			buttonsize = 280
			
		self.all = wx.Choice(self.mainPanel, -1, (0,0), (buttonsize,-1))
		self.all.SetForegroundColour(wx.BLACK)
		vbox_top.Add(self.all, 0, wx.LEFT | wx.TOP, 9)
		self.mainPanel.Bind(wx.EVT_CHOICE, self.SetTYPE, self.all)

		panel1 = wx.Panel (self.mainPanel, -1)
		sizer1 = wx.StaticBoxSizer(wx.StaticBox(panel1, -1, 'Decimate'), orient=wx.HORIZONTAL)
		
		if platform_name[0] == "Windows" :		
			sizer1.Add(wx.StaticText(panel1, -1, "Use every      "), 0, wx.TOP | wx.LEFT | wx.RIGHT, 5)
			self.decimate = wx.TextCtrl(panel1, -1, "1", size=(80, 25), style=wx.SUNKEN_BORDER )
			sizer1.Add(self.decimate, 0, wx.RIGHT, 5)
			sizer1.Add(wx.StaticText(panel1, -1, " points              "), 0, wx.TOP | wx.RIGHT, 5)
		else :
			sizer1.Add(wx.StaticText(panel1, -1, "Use every      "), 0, wx.RIGHT, 5)
			self.decimate = wx.TextCtrl(panel1, -1, "1", size=(80, 25), style=wx.SUNKEN_BORDER )
			sizer1.Add(self.decimate, 0, wx.RIGHT, 5)
			sizer1.Add(wx.StaticText(panel1, -1, " points          "), 0, wx.RIGHT, 5)
		panel1.SetSizer(sizer1)
		vbox_top.Add(panel1, 0, wx.BOTTOM | wx.LEFT | wx.TOP, 9)

		gridApply1 = wx.GridSizer(1, 2)
		deciBtn = wx.Button(self.mainPanel, -1, "Apply", size=(120, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnDecimate, deciBtn)
		gridApply1.Add(deciBtn)

		self.deciUndo = [ "All Holes", "1" ]
		self.deciBackup = [ "All Holes", "1" ]
		self.deciundoBtn = wx.Button(self.mainPanel, -1, "Undo", size=(120, 30))
		self.deciundoBtn.Enable(False)
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnUNDODecimate, self.deciundoBtn)
		if platform_name[0] == "Windows" :	
			gridApply1.Add(self.deciundoBtn, 0, wx.LEFT, 20)
		else :
			gridApply1.Add(self.deciundoBtn, 0, wx.LEFT, 10)

		vbox_top.Add(gridApply1, 0, wx.LEFT, 10)


		panel2 = wx.Panel (self.mainPanel, -1)
		sizer2 = wx.StaticBoxSizer(wx.StaticBox(panel2, -1, 'Smooth'), orient=wx.VERTICAL)
		grid2 = wx.GridBagSizer(3, 3)
		
		if platform_name[0] == "Windows" :			
			grid2.Add(wx.StaticText(panel2, -1, "Type"), (0,0), flag=wx.LEFT | wx.RIGHT, border=5)
		else :
			grid2.Add(wx.StaticText(panel2, -1, "Type"), (0,0), flag=wx.RIGHT, border=5)
				
		self.smoothcmd = wx.Choice(panel2, -1, (0,0), (180, -1), ("None", "Gaussian"))
		self.smoothcmd.SetForegroundColour(wx.BLACK)
		if platform_name[0] == "Windows" :		
			grid2.Add(self.smoothcmd, (0,1), span=(1,2), flag=wx.RIGHT, border=5)
		else :
			grid2.Add(self.smoothcmd, (0,1), span=(1,2))
					
		if platform_name[0] == "Windows" :		
			grid2.Add(wx.StaticText(panel2, -1, "Width"), (1,0), flag=wx.LEFT | wx.RIGHT, border=5)
		else :
			grid2.Add(wx.StaticText(panel2, -1, "Width"), (1,0), flag=wx.RIGHT, border=5)
		
		self.width = wx.TextCtrl(panel2, -1, "9", size=(60, 25), style=wx.SUNKEN_BORDER)
		grid2.Add(self.width, (1,1), flag=wx.BOTTOM, border=3)

		self.unitscmd = wx.Choice(panel2, -1, choices=["Points", "Depth(cm)"])
		self.unitscmd.SetForegroundColour(wx.BLACK)
		self.mainPanel.Bind(wx.EVT_CHOICE, self.SetUNIT, self.unitscmd)
		grid2.Add(self.unitscmd, (1,2), flag=wx.ALIGN_CENTER_VERTICAL)

		if platform_name[0] == "Windows":
			grid2.Add(wx.StaticText(panel2, -1, "Display	         "), (2,0), flag=wx.RIGHT | wx.LEFT, border=5)
		else:
			grid2.Add(wx.StaticText(panel2, -1, "Display"), (2,0), flag=wx.RIGHT, border=5)
		self.plotcmd = wx.Choice(panel2, -1, (0,0), (180, -1), ("UnsmoothedOnly", "SmoothedOnly", "Smoothed&Unsmoothed"))
		self.plotcmd.SetForegroundColour(wx.BLACK)
		if platform_name[0] == "Windows":
			grid2.Add(self.plotcmd, (2,1), span=(1,2))
		else:
			grid2.Add(self.plotcmd, (2,1), span=(1,2))

		sizer2.Add(grid2)
		panel2.SetSizer(sizer2)
		vbox_top.Add(panel2, 0, wx.BOTTOM | wx.TOP | wx.LEFT | wx.EXPAND, 9)

		gridApply2 = wx.GridSizer(1, 2)
		smBtn = wx.Button(self.mainPanel, -1, "Apply", size=(120, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnSmooth, smBtn)
		gridApply2.Add(smBtn)

		self.smBackup = []
		self.smUndo = []

		self.smundoBtn = wx.Button(self.mainPanel, -1, "Undo", size=(120, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnUNDOSmooth, self.smundoBtn)
		#self.smundoBtn.Enable(False)
		if platform_name[0] == "Windows":
			gridApply2.Add(self.smundoBtn, 0, wx.LEFT, 20)
		else:
			gridApply2.Add(self.smundoBtn, 0, wx.LEFT, 10)
		vbox_top.Add(gridApply2, 0, wx.LEFT, 10)

		panel3 = wx.Panel(self.mainPanel, -1)
		sizer3 = wx.StaticBoxSizer(wx.StaticBox(panel3, -1, 'Cull'), orient=wx.VERTICAL)

		grid3 = wx.FlexGridSizer(2, 2)
		self.nocull = wx.RadioButton(panel3, -1, "No cull", style=wx.RB_GROUP)
		self.nocull.SetValue(True)
		grid3.Add(self.nocull)
		self.cull = wx.RadioButton(panel3, -1, "Use parameters ")
		self.cull.SetValue(False)
		grid3.Add(self.cull, 0, wx.BOTTOM, 15)

		self.valueD = wx.TextCtrl(panel3, -1, "5.0", size=(80, 25), style=wx.SUNKEN_BORDER )
		grid3.Add(self.valueD, 0, wx.RIGHT, 9)
		grid3.Add(wx.StaticText(panel3, -1, "cm from each core top "), 0, wx.BOTTOM, 9)
		if platform_name[0] == "Windows" :	
			sizer3.Add(grid3, 0, wx.BOTTOM | wx.LEFT, 9)
		else :
			sizer3.Add(grid3, 0, wx.BOTTOM, 9)


		grid31 = wx.FlexGridSizer(2, 4)
		grid31.Add(wx.StaticText(panel3, -1, ""), 0, wx.RIGHT, 3)
		self.cmd = wx.Choice(panel3, -1, (0,0), (50,-1), ("<", ">"))
		self.cmd.SetForegroundColour(wx.BLACK)

		grid31.Add(self.cmd, 0, wx.RIGHT, 9)
		self.valueA = wx.TextCtrl(panel3, -1, "9999.99", size=(80, 25), style=wx.SUNKEN_BORDER )
		grid31.Add(self.valueA, 0, wx.RIGHT, 9)

		self.onlyCheck = wx.CheckBox(panel3, -1, ' ')
		self.onlyCheck.SetValue(True)
		self.onlyCheck.Enable(False)
		grid31.Add(self.onlyCheck, 0, wx.BOTTOM, 9)

		grid31.Add(wx.StaticText(panel3, -1, "                     "), 0, wx.RIGHT, 3)
		self.signcmd = wx.Choice(panel3, -1, (0,0), (50,-1), ("<", ">")) 
		self.signcmd.SetForegroundColour(wx.BLACK)
		grid31.Add(self.signcmd, 0, wx.RIGHT, 9)
		self.valueB = wx.TextCtrl(panel3, -1, "-9999.99", size=(80, 25), style=wx.SUNKEN_BORDER )
		grid31.Add(self.valueB, 0, wx.RIGHT, 9)
		self.orCheck = wx.CheckBox(panel3, -1, ' ')
		grid31.Add(self.orCheck, 0, wx.BOTTOM, 15)

		wx.StaticText(panel3, -1, "data value", (20, 110))
		if platform_name[0] == "Windows" :	
			sizer3.Add(grid31, 0, wx.LEFT, 9)
		else :		
			sizer3.Add(grid31)

		buttonsize = 180
		if platform_name[0] == "Windows" :	
			buttonsize = 140
			
		grid32 = wx.FlexGridSizer(1, 2)
		self.optcmd = wx.Choice(panel3, -1, (0,0), (buttonsize, -1), ("Use all cores", "Use cores numbered <="))
		grid32.Add(self.optcmd, 0, wx.RIGHT, 5)
		self.valueE = wx.TextCtrl(panel3, -1, "999", size=(80, 25), style=wx.SUNKEN_BORDER )
		grid32.Add(self.valueE, 0, wx.BOTTOM, 9)
		if platform_name[0] == "Windows" :		
			sizer3.Add(grid32, 0, wx.LEFT, 9)
		else :
			sizer3.Add(grid32)

		panel3.SetSizer(sizer3)
		vbox_top.Add(panel3, 0, wx.BOTTOM | wx.TOP | wx.LEFT , 9)

		gridApply3 = wx.GridSizer(1, 2)
		cullBtn = wx.Button(self.mainPanel, -1, "Apply", size=(120, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnCull, cullBtn)
		gridApply3.Add(cullBtn)

		self.cullBackup = [ "All Holes", False, "5.0", ">", "9999.99", True, "<", "-9999.99", False, "Use all cores", "999" ]
		self.cullUndo = [ "All Holes", False, "5.0", ">", "9999.99", True, "<", "-9999.99", False, "Use all cores", "999" ]
		self.cullundoBtn = wx.Button(self.mainPanel, -1, "Undo", size=(120, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnUNDOCull, self.cullundoBtn)
		self.cullundoBtn.Enable(False)
		if platform_name[0] == "Windows" :	
			gridApply3.Add(self.cullundoBtn, 0, wx.LEFT, 20)	
		else :			
			gridApply3.Add(self.cullundoBtn, 0, wx.LEFT, 10)	
		vbox_top.Add(gridApply3, 0, wx.LEFT, 10)

		self.mainPanel.SetSizer(vbox_top)

	def OnInitUI(self):
		self.all.SetStringSelection("All Holes")
		self.decimate.SetValue("1")
		self.smoothcmd.SetStringSelection("Gaussian")
		self.unitscmd.SetStringSelection("Points")
		self.width.SetValue("9")
		self.plotcmd.SetStringSelection("Smoothed&Unsmoothed")
		self.nocull.SetValue(True)
		self.valueD.SetValue("5.0")
		self.cmd.SetStringSelection(">")
		self.valueA.SetValue("9999.99")
		self.onlyCheck.SetValue(True)
		self.signcmd.SetStringSelection("<")
		self.valueB.SetValue("-9999.99")
		self.orCheck.SetValue(False)
		self.optcmd.SetStringSelection("Use all cores")
		self.valueE.SetValue("999")
		self.deciBackup = [ "All Holes", "1"]
		self.smBackup = []
		self.cullBackup = [ "All Holes", False, "5.0", ">", "9999.99", True, "<", "-9999.99", False, "Use all cores", "999" ]
		self.deciUndo = [ "All Holes", "1"]
		self.smUndo = []
		self.cullUndo = [ "All Holes", False, "5.0", ">", "9999.99", True, "<", "-9999.99", False, "Use all cores", "999" ]
		self.smundoBtn.Enable(False)
		self.cullundoBtn.Enable(False)
		self.deciundoBtn.Enable(False)

	def SetUNIT(self, event):
	 	self.width.Clear()
		if self.unitscmd.GetStringSelection() == "Depth(cm)" :
			self.width.SetValue("40")
		else :
			self.width.SetValue("9")

	def OnLock(self):
		self.locked = True 

	def OnRelease(self):
		self.locked = False 

	def OnUPDATEDECIMATE(self, selection, deciValue) :
		n = self.all.GetCount()
		for i in range(n) :
			if self.all.GetString(i) == selection :
				self.all.SetSelection(i)
				self.decimate.SetValue(deciValue)
				self.OnDecimate(1)
				return


# 	def OnRegisterClear(self):
# 		if self.locked == False :
# 			self.prevSelected = self.all.GetCurrentSelection()
# 			if self.prevSelected == -1 :
# 				self.prevSelected = 0			
# 			self.all.Clear()
# 			self.all.Append("All Holes")
# 			self.all.SetSelection(0)
# 			#self.all.Append("Log")
			
# 			if platform_name[0] == "Windows":
# 				self.all.SetValue(self.all.GetString(self.prevSelected))			
# 			self.parent.optPanel.OnRegisterClear()


	def OnRegisterSplice(self):
		n = self.all.GetCount()
		for i in range(n) :
			if self.all.GetString(i) == "Spliced Records" :
				return False
		name = "Spliced Records"
		self.all.Append(name)
		self.parent.optPanel.OnRegisterHole(name)
		return True 

	def OnRegisterHole(self, holename):
		if self.locked == False :
			n = self.all.GetCount()
			for i in range(n) :
				if self.all.GetString(i) == holename :
					return

			self.all.Append(holename)
			self.parent.optPanel.OnRegisterHole(holename)

	def ParseSmoothString(self, smoothStr):
		tokens = smoothStr.split(' ')
		if len(tokens) != 3:
			return []
		return tokens

	def MakeSmoothString(self, width, units, smoothStyle):
		return width + " " + units + " " + smoothStyle

	def UpdateSmooth(self, smoothStr):
		smoothList = self.ParseSmoothString(smoothStr)
		if smoothList == []:
			return
		self.smoothcmd.SetStringSelection("Gaussian")
		self.width.SetValue(smoothList[0])
		self.unitscmd.SetStringSelection(smoothList[1])
		self.plotcmd.SetStringSelection(smoothList[2])

	# brg 1/29/2014: new-fangled SetTYPE()
	def TypeChoiceChanged(self, event):
		typeStr = self.all.GetValue()
		if typeStr == 'All Holes' or typeStr == 'Log' or typeStr == 'Spliced Records':
			return

# 		site = self.parent.GetLoadedSite()
# 		strippedType = typeStr[4:] # strip off 'All '
# 		if strippedType in site.holeSets:
# 			holeSet = site.holeSets[strippedType]
# 		else:
# 			print "Couldn't find type " + strippedType + " in site.holeSets, bailing"
# 			return

		self.decimate.SetValue(str(holeSet.decimate))
		self.UpdateSmooth(holeSet.smooth)


	def SetTYPE(self, event):
		type = self.all.GetStringSelection()
		if type == 'All Holes':
			return
		elif type == 'Log':
			return
		elif type == 'Spliced Records':
			return
		else:
			size = len(type)
			type = type[4:size] # strip off 'All '

		# Update decivalue & smooth
		if type == "Natural Gamma" :
			type = "NaturalGamma"
		data = self.parent.dataFrame.GetDECIMATE(type)
		
		if data != None :
			self.decimate.SetValue(data[0])
			if data[1] != "" :
				smooth_array = data[1].split(' ')
				self.smoothcmd.SetStringSelection("Gaussian")
				self.width.SetValue(smooth_array[0])
				self.unitscmd.SetStringSelection(smooth_array[1])
				self.plotcmd.SetStringSelection(smooth_array[2])
			else :
				self.smoothcmd.SetStringSelection("None")
		else :
			self.smoothcmd.SetStringSelection("None")
		self.smBackup = [ self.all.GetStringSelection(), self.smoothcmd.GetStringSelection(), self.width.GetValue(), self.unitscmd.GetStringSelection(), self.plotcmd.GetStringSelection()]

		# Update cull
		cullData = self.parent.dataFrame.GetCULL(type)
		if cullData == None and type == "NaturalGamma":
			type = "Natural Gamma"
			cullData = self.parent.dataFrame.GetCULL(type)

		self.nocull.SetValue(True)
		self.valueD.SetValue("5.0")
		self.cmd.SetStringSelection(">")
		self.valueA.SetValue("9999.99")
		self.onlyCheck.SetValue(True)
		self.signcmd.SetStringSelection("<")
		self.valueB.SetValue("-9999.99")
		self.orCheck.SetValue(False)
		self.optcmd.SetStringSelection("Use all cores")
		self.valueE.SetValue("999")

		if cullData != None :
			if cullData[1] == False :
				self.nocull.SetValue(True)
			else :
				self.cull.SetValue(True)

				max  = len(cullData)
				if max >= 3 :
					self.valueD.SetValue(cullData[2])
				#self.cmd.SetStringSelection(">")

				if max == 4 :
					self.orCheck.SetValue(False)
					self.optcmd.SetStringSelection("Use cores numbered <=")
					self.valueE.SetValue(cullData[3])
				elif max == 5 :
					self.valueA.SetValue(cullData[4])
					self.cmd.SetStringSelection(cullData[3])
					self.orCheck.SetValue(False)
					self.optcmd.SetStringSelection("Use all cores")
				elif max == 6 :
					self.valueA.SetValue(cullData[4])
					self.cmd.SetStringSelection(cullData[3])
					self.orCheck.SetValue(False)
					self.optcmd.SetStringSelection("Use cores numbered <=")
					self.valueE.SetValue(cullData[5])
				elif max == 7 :
					self.valueA.SetValue(cullData[4])
					self.cmd.SetStringSelection(cullData[3])
					self.orCheck.SetValue(True)
					self.valueB.SetValue(cullData[6])
					self.signcmd.SetStringSelection(cullData[5])
					self.optcmd.SetStringSelection("Use all cores")
				elif max == 8 :
					self.valueA.SetValue(cullData[4])
					self.cmd.SetStringSelection(cullData[3])
					self.orCheck.SetValue(True)
					self.valueB.SetValue(cullData[6])
					self.signcmd.SetStringSelection(cullData[5])
					self.optcmd.SetStringSelection("Use cores numbered <=")
					self.valueE.SetValue(cullData[7])


	# brg 1/29/2014: Ignore undo for now - seems pointless for decimate
	def OnUNDODecimate(self, event):
		opt = self.deciUndo[0]
		deci = self.deciUndo[1]
		self.deciUndo = [ self.all.GetStringSelection(), self.decimate.GetValue() ]

		self.decimate.SetValue(deci)
		self.all.SetStringSelection(opt)
		self.OnDecimate(event)
		

	# brg 1/29/2014: Ignore undo for now - seems pointless for decimate
	def OnDecimate(self, event):
		type = self.all.GetStringSelection()
		if type == 'Spliced Records' :
			self.parent.OnShowMessage("Error", "Splice Records can not be decimated", 1)
			return

		self.deciUndo = self.deciBackup
		self.deciundoBtn.Enable(True)

		deciValue = int(self.decimate.GetValue())

		site = self.parent.GetLoadedSite()
		if type == "All Holes" :
			for index in range(1, self.all.GetCount()):
				allType = self.all.GetString(index)
				if allType == 'Spliced Records' :
					continue
				py_correlator.decimate(allType, deciValue)
				#site.SetDecimate(allType[4:], deciValue)
		else :
			py_correlator.decimate(type, deciValue)
			#site.SetDecimate(type[4:], deciValue)

		self.deciBackup = [ self.all.GetStringSelection(), self.decimate.GetValue() ]

		if type != "Log" :
			self.parent.LOCK = 0 
			self.parent.UpdateCORE()
			self.parent.UpdateSMOOTH_CORE()
			self.parent.LOCK = 1 
		else :
			self.parent.UpdateLogData()

		#if type == "All Natural Gamma" :
		#	type = "All NaturalGamma"
		#self.parent.dataFrame.OnUPDATEDECIMATE(type, deciValue)

		#site.SyncToData()
		self.parent.Window.UpdateDrawing()

	""" Return integer smooth style (unsmoothed, smoothed, or combo) based on current smooth combobox selection """
	def GetSmoothStyle(self):
		smoothStyle = 0 # no smooth - should really define constant, named values
		if self.plotcmd.GetStringSelection() == "SmoothedOnly":
			smoothStyle = 1
		elif self.plotcmd.GetStringSelection() == "Smoothed&Unsmoothed":
			smoothStyle = 2
		return smoothStyle

	""" Return integer width or -1 if "None" smooth type is selected """
	def GetSmoothWidth(self):
		smoothWidth = -1
		if self.smoothcmd.GetStringSelection() == "Gaussian":
			smoothWidth = int(self.width.GetValue())
		return smoothWidth

	""" Return current smooth unit """
	def GetSmoothUnit(self):
		smoothUnit = 2 if self.unitscmd.GetStringSelection() == "Depth(cm)" else 1
		return smoothUnit

	""" Return True if smooth is enabled ("Gaussian" type is selected) else False """
	def GetSmoothEnable(self):
		return False if self.smoothcmd.GetStringSelection() == "None" else True

	def OnUNDOSmooth(self, event):
		if self.smUndo == [] :
			self.smundoBtn.Enable(False)
			return

		opt = self.smUndo[0]
		filter = self.smUndo[1]
		value = self.smUndo[2]
		unit = self.smUndo[3]
		plotting = self.smUndo[4]
		#self.smUndo = [ self.all.GetValue(), self.smoothcmd.GetValue(), self.width.GetValue(), self.plotcmd.GetValue()]

		self.all.SetStringSelection(opt)
		self.smoothcmd.SetStringSelection(filter)
		self.width.SetValue(value)
		self.unitscmd.SetStringSelection(unit)
		self.plotcmd.SetStringSelection(plotting)
		self.OnSmooth(event)
		self.smundoBtn.Enable(False)


	def OnSmooth(self, event):
		self.smundoBtn.Enable(True)
		self.smUndo = self.smBackup

		smoothEnable = self.GetSmoothEnable()
		smoothWidth = self.GetSmoothWidth()
		smoothUnit = self.GetSmoothUnit()
		smoothUnitStr = self.unitscmd.GetStringSelection()
		smoothStyle = self.GetSmoothStyle()
		smoothStyleStr = self.plotcmd.GetStringSelection()

		site = self.parent.GetLoadedSite()
		type = self.all.GetStringSelection()

		# 1/29/2014 brg: Looks like this takes effect when only smoothStyle has changed.
		if self.smBackup != [] : 
			if type == self.smBackup[0] and self.smoothcmd.GetStringSelection() == self.smBackup[1] and self.width.GetValue() == self.smBackup[2] and self.unitscmd.GetStringSelection() == self.smBackup[3] :
				if type  != 'All Holes' and type != 'Log' and type != 'Spliced Records' :
					size = len(type)
					type = type[4:size]
				if type == "Natural Gamma" :
					type = "NaturalGamma"

				if type == 'Spliced Records' :
					self.parent.Window.UpdateSMOOTH('splice', smoothStyle)
				elif type == 'Log' :
					self.parent.Window.UpdateSMOOTH('log', smoothStyle)
				else :
					self.parent.dataFrame.OnUPDATE_SMOOTH(type, self.smoothcmd.GetStringSelection(), str(self.width.GetValue()), self.unitscmd.GetStringSelection(), self.plotcmd.GetStringSelection() )
					if type == 'All Holes' :
						self.parent.Window.UpdateSMOOTH('splice', smoothStyle)
						
				self.parent.Window.UpdateDrawing()
				#print "[DEBUG] Display is updated : " + self.plotcmd.GetValue()
				return

		if not smoothEnable:
			smoothUnit = -1

		# brgtodo 1/29/2014: ??? If type is spliced records, why are we doing everything
		# *but* modifying spliced records???
#  		if type == 'Spliced Records' : 
#  			max = self.all.GetCount()
#  			start = 1
#  			#if self.parent.Window.LogData == [] :
#  			#	start = 2
#  			for i in range(start, max) :
#  				all_type = self.all.GetString(i)
#  				if all_type == 'Spliced Records' :
#  					continue
#  				start = all_type.find("All", 0)
#  				if start >= 0 : 
#  					py_correlator.smooth(all_type, smoothWidth, smoothUnit)

		# brgtodo 1/29/2014: Pretty sure this does exactly the same thing as above block
		if type == 'All Holes' : 
			for i in range(1, self.all.GetCount()) :
				all_type = self.all.GetString(i)
				if all_type == 'Spliced Records' :
					continue
				start = all_type.find("All", 0)
				if start >= 0 or all_type == 'Log':
					py_correlator.smooth(all_type, smoothWidth, smoothUnit)
					#site.SetSmooth(all_type[4:], self.MakeSmoothString(str(smoothWidth), smoothUnitStr, smoothStyleStr))
				#elif all_type == 'Log' :
					#py_correlator.smooth(all_type, smoothWidth, smoothUnit)
		else :
			py_correlator.smooth(type, smoothWidth, smoothUnit)
			#site.SetSmooth(type[4:], self.MakeSmoothString(str(smoothWidth), smoothUnitStr, smoothStyleStr))

		#site.SyncToData()

		#HYEJUNG CHANGING NOW
		if type == 'Spliced Records' :
			self.parent.UpdateSMOOTH_SPLICE(False)
			if self.parent.Window.LogData != [] and self.parent.Window.SpliceData != [] :
				self.parent.UpdateSMOOTH_LOGSPLICE(True)
			self.parent.Window.UpdateSMOOTH('splice', smoothStyle)
		elif type == 'Log' :
			#self.parent.UpdateLogData()
			self.parent.UpdateSMOOTH_LogData()
			self.parent.Window.UpdateSMOOTH('log', smoothStyle)
		else :
			self.parent.UpdateSMOOTH_CORE()
			if type == 'All Holes' :
				self.parent.UpdateSMOOTH_SPLICE(False)
				self.parent.Window.UpdateSMOOTH('splice', smoothStyle)
		###

		self.smBackup = [ self.all.GetStringSelection(), self.smoothcmd.GetStringSelection(), self.width.GetValue(), self.unitscmd.GetStringSelection(), self.plotcmd.GetStringSelection()]

		if type  != 'All Holes' and type != 'Log' and type != 'Spliced Records' :
			size = len(type)
			type = type[4:size]

		if type == "Natural Gamma" :
			type = "NaturalGamma"

		self.parent.dataFrame.OnUPDATE_SMOOTH(type, self.smoothcmd.GetStringSelection(), str(self.width.GetValue()), self.unitscmd.GetStringSelection(), self.plotcmd.GetStringSelection())

		self.parent.Window.UpdateDrawing()


	def OnUNDOCull(self, event):
		opt = self.cullUndo[0]
		cull = self.cullUndo[1]
		top = self.cullUndo[2]
		sign1 = self.cullUndo[3]
		value1 = self.cullUndo[4]
		flag1 = self.cullUndo[5]
		sign2 = self.cullUndo[6]
		value2 = self.cullUndo[7]
		flag2 = self.cullUndo[8]
		type = self.cullUndo[9]
		coreno = self.cullUndo[10]

		# [ "All Holes", "False", "5.0", ">", "999.99", True, "<", "-999.99", False, "Use all cores", "999" ]
		self.cullUndo = [ self.all.GetStringSelection(), self.nocull.GetValue(), self.valueD.GetValue(), self.cmd.GetStringSelection(), self.valueA.GetValue(), self.onlyCheck.GetValue(), self.signcmd.GetValue(), self.valueB.GetValue(), self.orCheck.GetValue(), self.optcmd.GetStringSelection(), self.valueE.GetValue()]

		self.all.SetStringSelection(opt)
		self.nocull.SetValue(cull)
		self.cull.SetValue(True)
		if cull == True : 
			self.cull.SetValue(False)
			self.nocull.SetValue(True)
		self.valueD.SetValue(top)
		self.cmd.SetStringSelection(sign1)
		self.valueA.SetValue(value1)
		self.onlyCheck.SetValue(flag1)
		self.signcmd.SetStringSelection(sign2)
		self.valueB.SetValue(value2)
		self.orCheck.SetValue(flag2)
		self.optcmd.SetStringSelection(type)
		self.valueE.SetValue(coreno)

		self.OnCull(event)


	def OnCull(self, event):
		type = self.all.GetStringSelection()
		if type == 'Spliced Records' :
			self.parent.OnShowMessage("Error", "Splice Records can not be culled", 1)
			return

		self.cullundoBtn.Enable(True)

		self.cullUndo = self.cullBackup

		cullValue = 0.0
		if self.valueD.GetValue() != "" :
			cullValue = float(self.valueD.GetValue())
		else :
			self.valueD.SetValue("0.0")

		bcull = 0
		if self.cull.GetValue() == True :
			bcull = 1

		value1 = 999.99 
		value2 = -999.99 
		if self.valueA.GetValue() != "" :
			value1 = float(self.valueA.GetValue())
		else :
			self.valueA.SetValue("999.99")

		if self.valueB.GetValue() != "" :
			value2 = float(self.valueB.GetValue())
		else :
			self.valueB.SetValue("-999.99")

		sign1 = 1
		if self.cmd.GetStringSelection() == "<" :
			sign1 = 2
		sign2 = 1
		if self.signcmd.GetStringSelection() == "<" :
			sign2 = 2

		join = 1
		if self.orCheck.GetValue() == True :
			join = 2

		cullNumber = -1
		if self.optcmd.GetStringSelection() != "Use all cores" :
			if self.valueE.GetValue() != "" :
				cullNumber = int(self.valueE.GetValue())
			else :
				self.valueE.SetValue("999")

		#cullStrength = float(self.valueC.GetValue())
		cullStrength = 167.0

		# HYEJUNG
		if type == 'All Holes' : 
			max = self.all.GetCount()
			start = 1
			#if self.parent.Window.LogData == [] :
			#	start = 2
			for i in range(start, max) :
				all_type = self.all.GetString(i)
				if all_type == 'Spliced Records' : 
					continue
				start = all_type.find("All", 0)
				if start >= 0 or all_type == 'Log' : 
					self.parent.dataFrame.UpdateCULL(all_type, bcull, cullValue, cullNumber, value1, value2, sign1, sign2, join)

					py_correlator.cull(all_type, bcull, cullValue, cullNumber, cullStrength, value1, value2, sign1, sign2, join)

		else :
			self.parent.dataFrame.UpdateCULL(type, bcull, cullValue, cullNumber, value1, value2, sign1, sign2, join)
			py_correlator.cull(type, bcull, cullValue, cullNumber, cullStrength, value1, value2, sign1, sign2, join)

		if type != "Log" :
			self.parent.LOCK = 0 
			self.parent.UpdateCORE()
			self.parent.UpdateSMOOTH_CORE()
			self.parent.LOCK = 1 
		else :
			self.parent.UpdateLogData()

		self.cullBackup = [ self.all.GetStringSelection(), self.nocull.GetValue(), self.valueD.GetValue(), self.cmd.GetStringSelection(), self.valueA.GetValue(), self.onlyCheck.GetValue(), self.signcmd.GetStringSelection(), self.valueB.GetValue(), self.orCheck.GetValue(), self.optcmd.GetStringSelection(), self.valueE.GetValue()]


		if type  != 'All Holes' and type != 'Log' and type != 'Spliced Records' :
			size = len(type)
			type = type[4:size]

		if type == "Natural Gamma" :
			type = "NaturalGamma"

		if type != "Log" :
			self.parent.dataFrame.OnUPDATE_CULLTABLE(type)

		self.parent.Window.UpdateDrawing()


class PreferencesPanel():
	def __init__(self, parent, mainPanel):
		self.mainPanel = mainPanel
		self.parent = parent
		self.addItemsInFrame()
		self.prevSelected = 0
		self.depthmax = 20.0

	def OnRegisterHole(self, holename):
		self.all.Append(holename)
		self.all.SetSelection(self.prevSelected)

	def OnToolbarWindow(self, event):
		if self.tool.IsChecked() == True : 
			self.parent.topMenu.Show(True)
			self.parent.mitool.Check(True)
		else :
			self.parent.topMenu.Show(False)
			self.parent.mitool.Check(False)
		
	def OnActivateWindow(self, event):
		if self.opt1.IsChecked() == True : 
			self.parent.OnActivateWindow(1)
			self.parent.misecond.Check(True)
		else :
			self.parent.OnActivateWindow(0)
			self.parent.misecond.Check(False)

	def OnActivateScroll(self, event):
		if self.opt2.IsChecked() == True : 
			self.parent.SetSecondScroll(1)
			self.parent.miscroll.Check(True)
		else :
			self.parent.SetSecondScroll(0)
			self.parent.miscroll.Check(False)

	def OnUndoMinMax(self, event):
		pass

	def OnUPDATEMinMax(self, selection, min, max):
		n = self.all.GetCount()
		for i in range(n) :
			if self.all.GetString(i) == selection :
				self.all.SetSelection(i)
				self.min.SetValue(min)
				self.max.SetValue(max)
				self.OnChangeMinMax(1)
				return


	def OnUPDATEWidth(self):
		type = self.all.GetStringSelection()
		idx = self.slider1.GetValue() - 10
		holeWidth = 300 + (idx * 10)
		self.parent.Window.holeWidth = holeWidth 
		self.parent.Window.spliceHoleWidth = holeWidth
		self.parent.Window.logHoleWidth = holeWidth 


	def SetTYPE(self, event):
		type = self.all.GetStringSelection()

		if type  == 'All Holes' :
			print "[DEBUG] SET All Holes"
		elif type == 'Log' :
			type = "log"
		elif type == 'Spliced Records' :
			type = "splice"
		else :
			size = len(type)
			type = type[4:size]

			if type == "Natural Gamma" :
				type = "NaturalGamma"

		ret = self.parent.Window.GetMINMAX(type)
		if ret != None :
			self.min.SetValue(str(ret[0]))
			self.max.SetValue(str(ret[1]))

	# convert self.all string ("All Susceptibility") to type string ("Susceptibility")
	def _FixListTypeStr(self, type):
		if type.find("All ") == 0:
			type = type[4:]
			if type == "Natural Gamma":
				type = "NaturalGamma"
		elif type == "Spliced Records":
			type = "splice"
		elif type == "Log":
			type = "log"
		return type
	
	# get all hole types in self.all - no splice or log
	def _GetHoleTypes(self):
		result = []
		for str in self.all.GetStrings():
			print str
			if str.find("All ") != -1 and str != "All Holes":
				result.append(self._FixListTypeStr(str))
		return result
	
	# return list of types to apply min/max range change to - builds
	# list if All Holes is selected, otherwise selected non-Log/Splice type
	def _GetApplyList(self, allowSpliceAndLog=False):
		result = []
		curType = self.all.GetStringSelection()
		if curType == "All Holes":
			result = self._GetHoleTypes()
		elif (curType != "Log" and curType != "Spliced Records") or allowSpliceAndLog:
			result.append(self._FixListTypeStr(curType))
		return result
	
	def OnChangeMinMax(self, event):
		type = self.all.GetStringSelection()
		minRange = float(self.min.GetValue())
		maxRange = float(self.max.GetValue())

		if type == 'Log' :
			self.parent.Window.UpdateRANGE("log", minRange, maxRange)
		elif type == 'Spliced Records' :
			self.parent.Window.UpdateRANGE("splice", minRange, maxRange)
		else: # holes
			for applyType in self._GetApplyList():
				self.parent.dataFrame.UpdateMINMAX(applyType, minRange, maxRange)

		self.parent.Window.UpdateDrawing()

	def OnChangeWidth(self, event):
		idx = self.slider1.GetValue() - 10
		holeWidth = 300 + (idx * 10)

		self.parent.Window.holeWidth = holeWidth
		self.parent.Window.spliceHoleWidth = holeWidth
		self.parent.Window.logHoleWidth = holeWidth
		if event == None :
			return
		self.parent.Window.UpdateDrawing()

	def OnChangeRulerUnits(self, evt):
		self.parent.Window.rulerUnits = self.unitsPopup.GetStringSelection()
		self.parent.Window.UpdateDrawing()

	# 9/12/2012 brgtodo: rename slider2 to something meaningful,
	# update tie edit fields when slider moves  
	def OnRulerOneScale(self, event):
		# 1 --> 400 
		# start -> 62 : 60 + (idx * 2) 
		#idx = self.slider2.GetValue() - 10
		idx = self.slider2.GetValue()

		#self.parent.Window.length = 60 + (idx * 2)
		min = self.parent.Window.rulerStartDepth
		max = min + self.depthmax 
		if event == None : 
			max = min + self.depthmax
		x = (self.parent.Window.Height - self.parent.Window.startDepth) * self.parent.Window.gap
		self.parent.Window.length = idx * x / (max - min) * 1.0
		if event == None :
			return
		self.parent.Window.UpdateDrawing()


	def OnTieShiftScale(self, event):
		self.parent.Window.shift_range = float(self.tie_shift.GetValue())

	def OnChangeColor(self, event):
		dlg = dialog.ColorTableDialog(self.parent)
		dlg.Centre()
		ret = dlg.ShowModal()
		dlg.Destroy()

	def OnShowLine(self, event):
		self.parent.Window.showHoleGrid = self.opt3.GetValue()
		self.parent.Window.UpdateDrawing()

	def OnDepthViewAdjust(self, event):
		min = float(self.min_depth.GetValue())
		max = float(self.max_depth.GetValue())
		if min >= max :
			return
		self.depthmax = max
		self.slider2.SetValue(1)
		
		updateScroll = event is not None
		self.parent.OnUpdateDepthRange(min, max, updateScroll)
		
	def OnShowSectionDepths(self, event):
		self.parent.Window.showSectionDepths = self.showSectionDepths.IsChecked()
		self.parent.Window.UpdateDrawing()

	def OnShowAffineShiftInfo(self, event):
		self.parent.Window.showAffineShiftInfo = self.showAffineShiftInfo.IsChecked()
		self.parent.Window.UpdateDrawing()
		
	def OnShowAffineTieArrows(self, event):
		self.parent.Window.showAffineTieArrows = self.showAffineTieArrows.IsChecked()
		self.parent.Window.UpdateDrawing()
		
	def OnShowLogShiftArrows(self, event):
		self.parent.Window.LogClue = self.showLogShiftArrows.IsChecked()
		self.parent.Window.UpdateDrawing()
	
	def addItemsInFrame(self):
		vbox_top = wx.BoxSizer(wx.VERTICAL)
	
		unitsPanel = wx.Panel(self.mainPanel, -1)
		unitsSizer = wx.FlexGridSizer(1, 2)
		self.unitsPopup = wx.Choice(unitsPanel, -1, choices=('m','cm','mm'), size=(-1,24))
		self.unitsPopup.SetSelection(0)
		self.mainPanel.Bind(wx.EVT_CHOICE, self.OnChangeRulerUnits, self.unitsPopup)
		unitsSizer.Add(wx.StaticText(unitsPanel, -1, "Depth units: "), flag=wx.ALIGN_CENTER_VERTICAL)
		unitsSizer.Add(self.unitsPopup, flag=wx.ALIGN_CENTER_VERTICAL)
		unitsPanel.SetSizer(unitsSizer)
		vbox_top.Add(unitsPanel, 0, wx.LEFT | wx.BOTTOM | wx.TOP, 9)

		grid1 = wx.FlexGridSizer(1, 2)
		self.opt1 = wx.CheckBox(self.mainPanel, -1, 'Splice/Log window', (10, 10))
		self.mainPanel.Bind(wx.EVT_CHECKBOX, self.OnActivateWindow, self.opt1)
		grid1.Add(self.opt1)

		self.tool = wx.CheckBox(self.mainPanel, -1, 'Toolbar window', (10, 10))
		self.tool.SetValue(True)
		self.mainPanel.Bind(wx.EVT_CHECKBOX, self.OnToolbarWindow, self.tool)
		grid1.Add(self.tool, 0, wx.LEFT, 5)
		vbox_top.Add(grid1, 0, wx.LEFT, 9)

		buttonsize = 300
		if platform_name[0] == "Windows" :
			buttonsize = 285
			
		vbox_top.Add(wx.StaticLine(self.mainPanel, -1, size=(buttonsize,1)), 0, wx.TOP | wx.LEFT, 9)

		grid2 = wx.FlexGridSizer(1, 2)
		self.opt2 = wx.CheckBox(self.mainPanel, -1, 'Second scroll', (10, 10))
		self.mainPanel.Bind(wx.EVT_CHECKBOX, self.OnActivateScroll, self.opt2)
		grid2.Add(self.opt2)
		self.opt2.SetValue(False)

		self.opt3 = wx.CheckBox(self.mainPanel, -1, 'Show Line', (10, 10))
		self.mainPanel.Bind(wx.EVT_CHECKBOX, self.OnShowLine, self.opt3)
		self.opt3.SetValue(True)
		if platform_name[0] == "Windows" :
			grid2.Add(self.opt3, 0, wx.LEFT, 35)
		else :		
			grid2.Add(self.opt3, 0, wx.LEFT, 15)

		#self.opt3 = wx.CheckBox(self.mainPanel, -1, 'Text on Tie', (10, 10))
		#self.mainPanel.Bind(wx.EVT_CHECKBOX, self.OnActivateText, self.opt3)
		#self.opt3.SetValue(True)
		#if platform_name[0] == "Windows" :
		#	grid2.Add(self.opt3, 0, wx.LEFT, 35)
		#else :		
		#	grid2.Add(self.opt3, 0, wx.LEFT, 15)

		vbox_top.Add(grid2, 0, wx.TOP | wx.LEFT, 9)
		vbox_top.Add(wx.StaticLine(self.mainPanel, -1, size=(buttonsize,1)), 0, wx.TOP | wx.LEFT, 9)

		self.showSectionDepths = wx.CheckBox(self.mainPanel, -1, "Show sections' depths and numbers")
		self.mainPanel.Bind(wx.EVT_CHECKBOX, self.OnShowSectionDepths, self.showSectionDepths)
		vbox_top.Add(self.showSectionDepths, 0, wx.ALL, 5)

		self.showAffineShiftInfo = wx.CheckBox(self.mainPanel, -1, "Show affine shift direction and distance")
		self.mainPanel.Bind(wx.EVT_CHECKBOX, self.OnShowAffineShiftInfo, self.showAffineShiftInfo)
		vbox_top.Add(self.showAffineShiftInfo, 0, wx.ALL, 5)
		
		self.showAffineTieArrows = wx.CheckBox(self.mainPanel, -1, "Show affine tie arrows")
		self.mainPanel.Bind(wx.EVT_CHECKBOX, self.OnShowAffineTieArrows, self.showAffineTieArrows)
		vbox_top.Add(self.showAffineTieArrows, 0, wx.ALL, 5)		

		self.showLogShiftArrows = wx.CheckBox(self.mainPanel, -1, "Show log shift arrows")
		self.mainPanel.Bind(wx.EVT_CHECKBOX, self.OnShowLogShiftArrows, self.showLogShiftArrows)
		vbox_top.Add(self.showLogShiftArrows, 0, wx.ALL, 5)

		panel1 = wx.Panel(self.mainPanel, -1)
		sizer1 = wx.StaticBoxSizer(wx.StaticBox(panel1, -1, 'Display Range'), orient=wx.VERTICAL)

		self.all = wx.Choice(panel1, -1, (0,0), (270,-1), (""))
		panel1.Bind(wx.EVT_CHOICE, self.SetTYPE, self.all)

		self.all.SetForegroundColour(wx.BLACK)
		sizer1.Add(self.all, 0, wx.TOP, 5)

		grid1range = wx.FlexGridSizer(4, 2)
		grid1range.Add(wx.StaticText(panel1, -1, "Variable minimum: "), 0, wx.TOP, 5)
		self.min = wx.TextCtrl(panel1, -1, "0", size=(80, 25), style=wx.SUNKEN_BORDER)
		grid1range.Add(self.min, 0, wx.LEFT | wx.TOP, 5)

		grid1range.Add(wx.StaticText(panel1, -1, "Variable maximum: "), 0, wx.TOP, 5)
		self.max = wx.TextCtrl(panel1, -1, "20", size=(80, 25), style=wx.SUNKEN_BORDER)
		grid1range.Add(self.max, 0, wx.LEFT | wx.TOP, 5)
		widthBtn = wx.Button(panel1, -1, "Apply", size=(110, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnChangeMinMax, widthBtn)
		grid1range.Add(widthBtn, 0, wx.TOP, 9)
		widthundoBtn = wx.Button(panel1, -1, "Undo", size=(110, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnUndoMinMax, widthundoBtn)
		grid1range.Add(widthundoBtn, 0, wx.TOP | wx.LEFT, 9)
		widthundoBtn.Enable(False)

		if platform_name[0] == "Windows" :
			grid1range.Add(wx.StaticText(panel1, -1, "Axis width: "), 0, wx.TOP, 10)
			grid1range.Add(wx.StaticText(panel1, -1, ""), 0, wx.BOTTOM, 25)

			self.slider1 = wx.Slider(panel1, -1, 10, 1, 20, (90, 165), (150, -1))
			self.mainPanel.Bind(wx.EVT_COMMAND_SCROLL, self.OnChangeWidth, self.slider1)
			sizer1.Add(grid1range, 0, wx.LEFT | wx.TOP, 5)
		else :
			grid1range.Add(wx.StaticText(panel1, -1, "Axis width: "), 0, wx.TOP, 8)
			grid1range.Add(wx.StaticText(panel1, -1, ""), 0, wx.TOP, 10)

			self.slider1 = wx.Slider(panel1, -1, 10, 1, 20, (100, 165), (150, -1))
			self.mainPanel.Bind(wx.EVT_COMMAND_SCROLL, self.OnChangeWidth, self.slider1)
			sizer1.Add(grid1range, 0, wx.LEFT | wx.TOP, 5)

		panel1.SetSizer(sizer1)
		vbox_top.Add(panel1, 0, wx.TOP | wx.LEFT | wx.BOTTOM, 9)
		
		panel2 = wx.Panel(self.mainPanel, -1)
		sizer2 = wx.StaticBoxSizer(wx.StaticBox(panel2, -1, 'Ruler Depth Scale'), orient=wx.VERTICAL)
		self.slider2 = wx.Slider(panel2, -1, 1, 1, 10, size=(270, -1))
		self.mainPanel.Bind(wx.EVT_COMMAND_SCROLL, self.OnRulerOneScale, self.slider2)
		sizer2.Add(self.slider2, 0, flag=wx.EXPAND)
		grid21 = wx.FlexGridSizer(1, 5)
		grid21.Add(wx.StaticText(panel2, -1, 'min:'))
		self.min_depth = wx.TextCtrl(panel2, -1, "0.0", size =(50, 25), style=wx.SUNKEN_BORDER | wx.TE_PROCESS_ENTER)
		grid21.Add(self.min_depth, 0, wx.LEFT, 5)
		grid21.Add(wx.StaticText(panel2, -1, 'max:'), 0, wx.LEFT, 5)
		self.max_depth = wx.TextCtrl(panel2, -1, "20.0", size =(50, 25), style=wx.SUNKEN_BORDER | wx.TE_PROCESS_ENTER)
		grid21.Add(self.max_depth, 0, wx.LEFT, 5)
		sizer2.Add(grid21)
		testbtn = wx.Button(panel2, -1, "Apply", size=(60,25))
		grid21.Add(testbtn, 0, wx.LEFT, 10)
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnDepthViewAdjust, testbtn)

		panel2.SetSizer(sizer2)
		#vbox_top.Add(panel2, 0, wx.TOP | wx.LEFT, 9)
		vbox_top.Add(panel2, 0, wx.LEFT, 9)
		
		panel6 = wx.Panel(self.mainPanel, -1)
		sizer6 = wx.StaticBoxSizer(wx.StaticBox(panel6, -1, 'Keyboard Tie Shift Depth Scale'), orient=wx.VERTICAL)
		grid61 = wx.FlexGridSizer(1, 3)
		grid61.Add(wx.StaticText(panel6, -1, 'In meters'), 0, wx.RIGHT, 9)
		self.tie_shift = wx.TextCtrl(panel6, -1, "0.0", size =(100, 25), style=wx.SUNKEN_BORDER | wx.TE_PROCESS_ENTER)
		grid61.Add(self.tie_shift)

		testbtn = wx.Button(panel6, -1, "Apply", size=(60,25))
		grid61.Add(testbtn, 0, wx.LEFT, 12)
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnTieShiftScale, testbtn)
		sizer6.Add(grid61)
		panel6.SetSizer(sizer6)
		vbox_top.Add(panel6, 0, wx.LEFT | wx.TOP, 9)


		testbtn = wx.Button(self.mainPanel, -1, "Change Color Set", size=(290,25))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnChangeColor, testbtn)
		vbox_top.Add(testbtn, 0, wx.LEFT | wx.TOP, 9)

		self.mainPanel.SetSizer(vbox_top)

