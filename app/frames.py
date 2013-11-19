#!/usr/bin/env python

## For Mac-OSX
#/usr/bin/env pythonw

#from wxPython.wx import *
import platform
platform_name = platform.uname()

import wx 
from wx.lib import plot
import random, sys, os, re, time, ConfigParser, string
from datetime import datetime

import numpy.oldnumeric as _Numeric

from importManager import py_correlator

from dialog import *
from dbmanager import *

def opj(path):
	"""Convert paths to the platform-specific separator"""
	return apply(os.path.join, tuple(path.split('/')))


class TopMenuFrame(wx.Frame):
	def __init__(self, parent):
		#topsize = (320, 60)
		topsize = (180, 245)
		if platform_name[0] == "Windows" :
			topsize = (185, 260)
		wx.Frame.__init__(self, None, -1, "Tool Bar",
						 wx.Point(20,100),
						 topsize,
						 style= wx.DEFAULT_DIALOG_STYLE |wx.NO_FULL_REPAINT_ON_RESIZE |wx.STAY_ON_TOP)

		self.parent = parent
		vbox = wx.BoxSizer(wx.VERTICAL)
		##newbtn = wx.BitmapButton(self, -1, wx.Bitmap('icons/New-32x32.png'))
		#newbtn = wx.Button(self, -1, "New", size=(180,25))
		#self.Bind(wx.EVT_BUTTON, self.OnNEW, newbtn)
		##newbtn.SetToolTip(wx.ToolTip('New') ) 
		#vbox.Add(newbtn)

		#dbbtn = wx.BitmapButton(self, -1, wx.Bitmap('icons/DB-32x32.png'))
		#self.dbbtn = wx.Button(self, -1, "Go to Data Manager", size=(180,25))
		self.dbbtn = wx.Button(self, -1, "Go to Display", size=(180,25))
		self.Bind(wx.EVT_BUTTON, self.OnDB, self.dbbtn)
		#dbbtn.SetToolTip(wx.ToolTip('Go to data manager') ) 
		vbox.Add(self.dbbtn)

		#savebtn = wx.BitmapButton(self, -1, wx.Bitmap('icons/save-32x32.png'))
		savebtn = wx.Button(self, -1, "Save", size=(180,25))
		self.Bind(wx.EVT_BUTTON, self.OnSAVE, savebtn)
		#savebtn.SetToolTip(wx.ToolTip('Save current changes to data manager') ) 
		vbox.Add(savebtn)

		self.cntbtn = wx.Button(self, -1, "Connect to Corelyzer", size=(180,25))
		self.Bind(wx.EVT_BUTTON, self.OnCONNECT, self.cntbtn)
		#self.cntbtn.Enable(False)
		vbox.Add(self.cntbtn)

		self.drawingbtn = wx.Button(self, -1, "Discrete Points", size=(180,25))
		self.Bind(wx.EVT_BUTTON, self.OnDRAWMODE, self.drawingbtn)
		vbox.Add(self.drawingbtn)

		#clearbtn = wx.BitmapButton(self, -1, wx.Bitmap('icons/Clear-32x32.png'))
		clearbtn = wx.Button(self, -1, "Clear All Ties", size=(180,25))
		self.Bind(wx.EVT_BUTTON, self.OnCLEAR, clearbtn)
		#clearbtn.SetToolTip(wx.ToolTip('Clear all shifts') ) 
		vbox.Add(clearbtn)

		#clearCPbtn = wx.BitmapButton(self, -1, wx.Bitmap('icons/Clear-32x32.png'))
		clearCPbtn = wx.Button(self, -1, "Clear All Shifts", size=(180,25))
		self.Bind(wx.EVT_BUTTON, self.OnCLEARCOMPOSITE, clearCPbtn)
		#clearCPbtn.SetToolTip(wx.ToolTip('Clear all composite shifts') ) 
		vbox.Add(clearCPbtn)

		#clearSPbtn = wx.BitmapButton(self, -1, wx.Bitmap('icons/Clear-32x32.png'))
		clearSPbtn = wx.Button(self, -1, "Clear All Splice Ties", size=(180,25))
		self.Bind(wx.EVT_BUTTON, self.OnCLEARSPLICE, clearSPbtn)
		#clearSPbtn.SetToolTip(wx.ToolTip('Clear all splice ties') ) 
		vbox.Add(clearSPbtn)

		#clearSAbtn = wx.BitmapButton(self, -1, wx.Bitmap('icons/Clear-32x32.png'))
		clearSAbtn = wx.Button(self, -1, "Clear All Core-Log Ties", size=(180,25))
		self.Bind(wx.EVT_BUTTON, self.OnCLEARSAGAN, clearSAbtn)
		#clearSAbtn.SetToolTip(wx.ToolTip('Clear all correlate ties') ) 
		vbox.Add(clearSAbtn)

		#splicebtn = wx.BitmapButton(self, -1, wx.Bitmap('icons/Splice-32x32.png'))
		#self.Bind(wx.EVT_BUTTON, self.OnSPLICE, splicebtn)
		#splicebtn.SetToolTip(wx.ToolTip('Splice data on/off') ) 
		#vbox.Add(splicebtn)

		#logbtn = wx.BitmapButton(self, -1, wx.Bitmap('icons/Log-32x32.png'))
		#self.Bind(wx.EVT_BUTTON, self.OnLOG, logbtn)
		#logbtn.SetToolTip(wx.ToolTip('Log data on/off') ) 
		#vbox.Add(logbtn)

		#stratbtn = wx.BitmapButton(self, -1, wx.Bitmap('icons/Strat-32x32.png'))
		#self.Bind(wx.EVT_BUTTON, self.OnSTRAT, stratbtn)
		#stratbtn.SetToolTip(wx.ToolTip('Strat data on/off') ) 
		#vbox.Add(stratbtn)

		#clearbtn = wx.BitmapButton(self, -1, wx.Bitmap('icons/Clear-32x32.png'))
		#self.Bind(wx.EVT_BUTTON, self.OnCLEAR, clearbtn)
		#clearbtn.SetToolTip(wx.ToolTip('Clear all shifts') ) 
		#vbox_bottom.Add(clearbtn)

		#exitbtn = wx.BitmapButton(self, -1, wx.Bitmap('icons/ErrorCircle-32x32.png'))
		exitbtn = wx.Button(self, -1, "Exit", size=(180,25))
		self.Bind(wx.EVT_BUTTON, self.OnEXIT, exitbtn)
		#exitbtn.SetToolTip(wx.ToolTip('Exit') ) 
		vbox.Add(exitbtn)

		self.SetSizer(vbox)

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
			#self.OnNEW(event)
			if self.parent.CHECK_CHANGES() == True :
				ret = self.parent.OnShowMessage("About", "Do you want to save?", 0)
				if ret == wx.ID_OK :
					self.OnSAVE(event)

			if self.parent.dataFrame.IsShown() == False :
				self.parent.dataFrame.Show(True)
				self.parent.midata.Check(True)
			else :
				self.parent.dataFrame.Raise()

			self.dbbtn.SetLabel("Go to Display")
		else :
			self.parent.dataFrame.propertyIdx = None
			
			self.parent.dataFrame.Show(False)
			self.parent.midata.Check(False)
			self.parent.Show(True)
			self.dbbtn.SetLabel("Go to Data Manager")


	def OnSAVE(self, event):
		if self.parent.CurrentDir == '' : 
			self.parent.OnShowMessage("Error", "There is no data loaded", 1)
			return

		splice_flag = self.parent.SpliceChange
		if self.parent.DoesFineTune() == True :
			splice_flag = True
			self.parent.OnShowMessage("Information", "You need to save splice table too.", 1)

		savedialog = SaveTableDialog(self, -1, self.parent.AffineChange, splice_flag)
		savedialog.Centre()
		ret = savedialog.ShowModal()
		affine_flag = savedialog.affineCheck.GetValue()
		splice_flag = savedialog.spliceCheck.GetValue()
		eld_flag = savedialog.eldCheck.GetValue()
		age_flag =  savedialog.ageCheck.GetValue()
		series_flag = savedialog.seriesCheck.GetValue()

		if ret == wx.ID_CANCEL :
			return
		
		# affine
		affine_filename = "";
		if affine_flag == True :
			affine_filename = self.parent.dataFrame.Add_TABLE("AFFINE" , "affine", savedialog.affineUpdate.GetValue(), False, "")
			py_correlator.saveAttributeFile(affine_filename, 1)

			s = "Save Affine Table: " + affine_filename + "\n\n"
			self.parent.logFileptr.write(s)
			self.parent.AffineChange = False  
		# splice
		if splice_flag == True :
			if self.parent.Window.SpliceData != [] :
				filename = self.parent.dataFrame.Add_TABLE("SPLICE" , "splice", savedialog.spliceUpdate.GetValue(), False, "")
				#py_correlator.saveAttributeFile(filename, 2, affine_filename)
				py_correlator.saveSpliceFile(filename, affine_filename)

				self.parent.autoPanel.SetCoreList(1, [])

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

	def OnCLEAR(self, event):
		self.parent.OnClearAllData(event)
		self.parent.Window.SetFocusFromKbd()

	def OnCLEARCOMPOSITE(self, event):
		self.parent.OnClearComposite(event)
		self.parent.Window.SetFocusFromKbd()

	def OnCLEARSPLICE(self, event):
		self.parent.OnClearSpliceTie(event)
		self.parent.Window.SetFocusFromKbd()

	def OnCLEARSAGAN(self, event):
		self.parent.OnClearSAGANTie(event)

	def OnEXIT(self, event):
		#if self.parent.dataFrame.IsShown() == True :
		#	self.parent.dataFrame.Show(False)
		#	self.parent.midata.Check(False)
		#else :
		#if self.parent.CurrentDir != '' and self.parent.changeFlag == True :
		#	ret = self.parent.OnShowMessage("About", "Do you want to save changes?", 2)		
		#	if ret == wx.ID_OK :
		#		self.OnSAVE(event)
		#self.Close(True)
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

class CompositePanel():
	def __init__(self, parent, mainPanel):
		self.mainPanel = mainPanel
		self.parent = parent
		self.leadLagValue = self.parent.leadLag
		self.polyline_list =[]
		self.growthPlotData = []
		self.addItemsInFrame()
		self.bestOffset = 0

	def addItemsInFrame(self):
		vbox_top = wx.BoxSizer(wx.VERTICAL)

		vbox = wx.BoxSizer(wx.VERTICAL)

		buttonsize = 85
		if platform_name[0] == "Windows" :
			buttonsize = 100
			
		# Panel 1
		panel1 = wx.Panel(self.mainPanel, -1)
		grid1 = wx.GridSizer(4, 2)
		grid1.Add(wx.StaticText(panel1, -1, 'Interpolated depth step(meter) : '), 0, wx.ALIGN_CENTER_VERTICAL)
		self.depthstep = wx.TextCtrl(panel1, -1, "0.11", size = (buttonsize, 25), style=wx.SUNKEN_BORDER )
		#self.depthstep.Enable(False)
		grid1.Add(self.depthstep, 0, wx.ALIGN_RIGHT)
		grid1.Add(wx.StaticText(panel1, -1, 'Correlation window length : ', (5, 5)), 0, wx.ALIGN_CENTER_VERTICAL)
		self.winlength = wx.TextCtrl(panel1, -1, str(self.parent.winLength), size =(buttonsize, 25), style=wx.SUNKEN_BORDER )
		grid1.Add(self.winlength, 0, wx.ALIGN_RIGHT)
		grid1.Add(wx.StaticText(panel1, -1, 'Correlation lead/lag : ', (5, 5)), 0, wx.ALIGN_CENTER_VERTICAL)
		self.leadlag = wx.TextCtrl(panel1, -1, str(self.leadLagValue), size = (buttonsize, 25), style=wx.SUNKEN_BORDER )
		grid1.Add(self.leadlag, 0, wx.ALIGN_RIGHT)

		buttonsize = 90
		if platform_name[0] == "Windows" :
			buttonsize = 100
			
		grid1.Add(wx.StaticText(panel1, -1, ' ', (5, 5)), 0, wx.ALIGN_CENTER_VERTICAL)

		addButton = wx.Button(panel1, -1, "Recorrelate", size =(buttonsize, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnCorrelate, addButton)
		grid1.Add(addButton, 0, wx.ALIGN_RIGHT)

		panel1.SetSizer(grid1)
		vbox.Add(panel1, 0, wx.TOP, 9)

		self.plotNote = wx.Notebook(self.mainPanel, -1, style=wx.NB_TOP | wx.NB_MULTILINE)

		# Correlation/Evaluation graph panel
		self.corrPlotCanvas = BetterLegendPlotCanvas(self.plotNote)

		if self.parent.Height > 768 :
			self.corrPlotCanvas.SetSize((300,300))
		else :
			self.corrPlotCanvas.SetSize((300,250))

		self.corrPlotCanvas.SetEnableGrid(True)
		self.corrPlotCanvas.SetEnableTitle(False)
		self.corrPlotCanvas.SetBackgroundColour("White")
		self.corrPlotCanvas.Show(True)

		# Growth Rate graph panel
		self.growthPlotCanvas = BetterLegendPlotCanvas(self.plotNote)
		self.growthPlotCanvas.SetEnableGrid(True)
		self.growthPlotCanvas.SetEnableTitle(False)
		self.growthPlotCanvas.SetEnableLegend(True)
		self.growthPlotCanvas.SetFontSizeLegend(10)
		self.growthPlotCanvas.SetBackgroundColour('White')
		self.growthPlotCanvas.Show(True)

		self.plotNote.AddPage(self.corrPlotCanvas, 'Evaluation')
		self.plotNote.AddPage(self.growthPlotCanvas, 'Growth Rate')

		# add Notebook to main panel
		self.plotNote.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnSelectPlotNote)
		self.plotNote.SetSelection(1)
		vbox.Add(self.plotNote, 1, wx.EXPAND | wx.ALL, 5)

		# update drawings
		xdata = [ (-self.leadLagValue, 0), (self.leadLagValue, 0) ]
		self.xaxes = plot.PolyLine(xdata, legend='', colour='black', width =2)
		ydata = [ (0, -1),( 0, 1) ]
		self.yaxes = plot.PolyLine(ydata, legend='', colour='black', width =2)
		data = [ (-self.leadLagValue, 0),( 0, 0), (self.leadLagValue, 0) ]
		self.OnUpdateData(data, [], 0)
		self.OnUpdateDrawing()

		self.UpdateGrowthPlot()

		# Panel 3
		panel3 = wx.Panel(self.mainPanel, -1)
		hbox3 = wx.BoxSizer(wx.HORIZONTAL)

		sizer31 = wx.StaticBoxSizer(wx.StaticBox(panel3, -1, 'Depth option'), orient=wx.VERTICAL)
		self.coreOnly = wx.RadioButton(panel3, -1, "This core only", style=wx.RB_GROUP)
		sizer31.Add(self.coreOnly)
		self.coreBelow = wx.RadioButton(panel3, -1, "This core and \nall below")
		self.coreBelow.SetValue(True)
		
		buttonsize = 110
		#if platform_name[0] == "Windows" :
		#	buttonsize = 145
		
		sizer31.Add(self.coreBelow, wx.BOTTOM, 0)
		self.actionType = wx.ComboBox(panel3, -1, "To tie", (0,0),(buttonsize,-1), ("To best correlation", "To tie", "To given"), wx.CB_DROPDOWN)
		self.actionType.SetForegroundColour(wx.BLACK)
		self.actionType.SetEditable(False)
		sizer31.Add(self.actionType, 0, wx.TOP, 0)
		hbox3.Add(sizer31, 1, wx.RIGHT, 0)

		sizer32 = wx.StaticBoxSizer(wx.StaticBox(panel3, -1, 'Undo option'), orient=wx.VERTICAL)
		sizer32.Add(wx.StaticText(panel3, -1, 'Previous offset:', (5, 5)), 0, wx.ALIGN_CENTER_VERTICAL)
		#sizer32 = wx.StaticBoxSizer(wx.StaticBox(panel3, -1, 'Undo option'), orient=wx.VERTICAL)
		#self.corePrev = wx.RadioButton(panel3, -1, "Previous offset", style=wx.RB_GROUP)
		#self.corePrev.SetValue(True)
		#sizer32.Add(self.corePrev)

		if platform_name[0] == "Windows" :
			self.undoButton = wx.Button(panel3, -1, "Undo To", size=(135, 30))
			self.mainPanel.Bind(wx.EVT_BUTTON, self.OnUndoCore, self.undoButton)
			self.undoButton.Enable(False)
			sizer32.Add(self.undoButton)
		else :	
			self.undoButton = wx.Button(panel3, -1, "Undo To", size=(120, 30))
			self.mainPanel.Bind(wx.EVT_BUTTON, self.OnUndoCore, self.undoButton)
			self.undoButton.Enable(False)
			sizer32.Add(self.undoButton)


		#self.coreAbove = wx.RadioButton(panel3, -1, "Offset of core \nabove")
		## rBotton.Bind(wx.EVT_RADIOBUTTON, self.monActv)
		#sizer32.Add(self.coreAbove)
		#self.coreAbove.Enable(False)
		#if platform_name[0] == "Windows" :
		#	self.undoButton = wx.Button(panel3, -1, "Undo To", (165, 60), (135, 30))
		#else :	
		#	self.undoButton = wx.Button(panel3, -1, "Undo To", (165, 95), (120, 30))
		#self.mainPanel.Bind(wx.EVT_BUTTON, self.OnUndoCore, self.undoButton)
		#self.undoButton.Enable(False)

		sizer32.Add(wx.StaticText(panel3, -1, 'Offset of core\nabove:', (5, 5)), 0, wx.ALIGN_CENTER_VERTICAL)
		self.aboveButton = wx.Button(panel3, -1, "Undo To", size=(120, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnUndoCoreAbove, self.aboveButton)
		self.aboveButton.Enable(False)
		sizer32.Add(self.aboveButton)

		hbox3.Add(sizer32, 1)
		panel3.SetSizer(hbox3)
		vbox.Add(panel3, 0, wx.BOTTOM, 9)

		buttonsize = 130
		if platform_name[0] == "Windows" :
			buttonsize = 145
			
		# Panel 4
		panel4 = wx.Panel(self.mainPanel, -1)
		hbox4 = wx.BoxSizer(wx.HORIZONTAL)
		sizer41 = wx.StaticBoxSizer(wx.StaticBox(panel4, -1, 'Depth adjust (meter)'), orient=wx.VERTICAL)
		self.depth = wx.TextCtrl(panel4, -1, " ", size=(buttonsize, 25), style=wx.SUNKEN_BORDER )
		sizer41.Add(self.depth)
		hbox4.Add(sizer41, 1, wx.RIGHT, 10)

		buttonsize = 120
		if platform_name[0] == "Windows" :
			buttonsize = 135
			
		sizer42 = wx.GridSizer(2, 1)
		self.clearButton = wx.Button(panel4, -1, "Clear Tie", size=(buttonsize, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnClearTie, self.clearButton)
		self.clearButton.Enable(False)
		sizer42.Add(self.clearButton, 0, wx.TOP, 5)

		self.adjustButton = wx.Button(panel4, -1, "Adjust Depth", size=(buttonsize, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnAdjust, self.adjustButton)
		self.adjustButton.Enable(False)
		sizer42.Add(self.adjustButton)
		hbox4.Add(sizer42, 1)

		panel4.SetSizer(hbox4)
		vbox.Add(panel4, 0, wx.BOTTOM, 2)

		self.showClue = wx.CheckBox(self.mainPanel, -1, 'Show depth adjust clue')
		#self.showClue.SetValue(False)
		self.showClue.SetValue(True)
		self.mainPanel.Bind(wx.EVT_CHECKBOX, self.OnShowClue, self.showClue)
		vbox.Add(self.showClue, 0, wx.BOTTOM, 5)

		vbox.Add(wx.StaticText(self.mainPanel, -1, '*Sub menu for tie: On dot, right mouse button.', (5, 5)), 0, wx.BOTTOM, 5)

		self.saveButton = wx.Button(self.mainPanel, -1, "Save Affine Table", size =(150, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnSAVE, self.saveButton)
		vbox.Add(self.saveButton, 0, wx.ALIGN_CENTER_VERTICAL)
		self.saveButton.Enable(False)

		vbox_top.Add(vbox, 1, wx.LEFT, 5)
		self.mainPanel.SetSizer(vbox_top)

	def OnInitUI(self):
		self.adjustButton.Enable(False)
		self.clearButton.Enable(False)
		self.undoButton.Enable(False)

	def OnSAVE(self, event):
		dlg = Message3Button(self.parent, "Do you want to create new affine file?")
		ret = dlg.ShowModal()
		dlg.Destroy()
		if ret == wx.ID_OK or ret == wx.ID_YES :
			flag = True 
			if ret == wx.ID_YES :
				flag = False
			filename = self.parent.dataFrame.Add_TABLE("AFFINE" , "affine", flag, False, "")
			py_correlator.saveAttributeFile(filename, 1)

			s = "Save Affine Table: " + filename + "\n"
			self.parent.logFileptr.write(s)
			self.parent.OnShowMessage("Information", "Successfully Saved", 1)
			self.parent.AffineChange = False 

	def OnButtonEnable(self, opt, enable):
		if opt == 0 : 
			self.adjustButton.Enable(enable)
			self.clearButton.Enable(enable)
			self.aboveButton.Enable(enable)
		elif opt == 1:
			self.undoButton.Enable(enable)
		else :
			self.clearButton.Enable(enable)

	def OnShowClue(self, event):
		self.parent.Window.ShiftClue = self.showClue.IsChecked()
		self.parent.Window.UpdateDrawing()

	def OnDismiss(self, evt):
		self.Hide()

	def OnAdjust(self, evt):
		offset = self.depth.GetValue()

		type = 0 # To best correlation
		if self.actionType.GetValue() == "To best correlation" :
			offset = str(self.bestOffset)
		elif self.actionType.GetValue() == "To tie" :
			type = 1 
		elif self.actionType.GetValue() == "To given" :
			type = 2 

		if self.coreBelow.GetValue() == True : 
			self.parent.OnAdjustCore(1, type, offset)
		if self.coreOnly.GetValue() == True :
			self.parent.OnAdjustCore(0, type, offset)

		self.parent.Window.activeTie = -1

		self.UpdateGrowthPlot()

	def OnClearTie(self, evt):
		self.parent.Window.OnClearTies(0)
		self.OnButtonEnable(0, False)
		self.parent.Window.activeTie = -1

	def OnUndoCore(self, evt):
		self.parent.OnUndoCore(0)

	def OnUndoCoreAbove(self, evt):
		self.parent.OnUndoCore(1)

	def OnCorrelate(self, evt):
		self.parent.depthStep = float(self.depthstep.GetValue())
		self.parent.winLength = float(self.winlength.GetValue())
		self.parent.leadLag = float(self.leadlag.GetValue())

		self.parent.OnEvalSetup()
		self.parent.OnUpdateGraphSetup(1)
		if len(self.parent.Window.TieData) > 0 :
			self.parent.Window.OnUpdateTie(1)

	def OnUpdate(self):
		self.leadLagValue = float(self.leadlag.GetValue())
		self.corrPlotCanvas.Clear()
		data = [ (-self.leadLagValue, 0),( 0, 0), (self.leadLagValue, 0) ]
		self.OnUpdateData(data, [], 0)
		self.OnUpdateDrawing()
		self.UpdateGrowthPlot()
		
	def OnUpdateDepth(self, data):
		depth = int(10000.0 * float(data)) / 10000.0;
		self.depth.SetValue(str(depth))

	def OnUpdateDepthStep(self, depthstep):
		depthstep = int(10000.0 * float(depthstep)) / 10000.0;
		self.depthstep.SetValue(str(depthstep))

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
		#self.corrPlotPanel.Hide()
		self.corrPlotCanvas.Hide()
		#self.growthPlotPanel.Hide()
		self.growthPlotCanvas.Hide()
		if event.GetSelection() == 0:
			#self.corrPlotPanel.Show()
			self.corrPlotCanvas.Show()
		elif event.GetSelection() == 1:
			self.UpdateGrowthPlot()
			self.growthPlotCanvas.Show()

	def UpdateGrowthPlotData(self):
		maxMbsfDepth = 0.0
		growthRateLines = []
		holeNum = 0
		holeSet = set([]) # avoid duplicate holes with different datatypes
		holeMarker = ['circle', 'square', 'triangle', 'plus', 'triangle_down']
		holeColor = ['red', 'blue', 'green', 'black', 'orange']
		for hole in self.parent.Window.HoleData:
			holeName = hole[0][0][7]
			if holeName not in holeSet:
				holeSet.add(holeName)
				growthRatePoints = []

				# brg 10/14/2013: hole[0][0][8] indicates the number of cores in the hole, but this isn't
				# always reliable - make sure we don't overrun the list of cores given such errant data
				numCores = min(hole[0][0][8], len(hole[0]) - 1)

				for core in range(numCores):
					offset = hole[0][core + 1][5]
					topSectionMcd = hole[0][core + 1][9][0]
					mbsfDepth = topSectionMcd - offset
					if mbsfDepth > maxMbsfDepth:
						maxMbsfDepth = mbsfDepth
					offsetMbsfPair = (mbsfDepth, topSectionMcd)
					growthRatePoints.append(offsetMbsfPair)

				self.growthPlotData.append(plot.PolyMarker(growthRatePoints, marker=holeMarker[holeNum], legend=hole[0][0][7], colour=holeColor[holeNum], size=0.8))

				if len(growthRatePoints) == 1: # ensure we have at least two points
					growthRatePoints = [(0,0)] + growthRatePoints

				growthRateLines.append(plot.PolyLine(growthRatePoints, colour='black', width=1))
				holeNum = (holeNum + 1) % len(holeMarker) # make sure we don't overrun marker/color lists

		return growthRateLines, maxMbsfDepth

	def UpdateGrowthPlot(self):
		# 9/18/2013 brg: Was unable to get Window attribute on init without adding this
		# hasattr call. Unclear why - its (Window is an instance of DataCanvas)
		# lone init() method, where Window is initialized, is called before this,
		# or so it would seem. Interestingly, other attributes declared beneath
		# Window in DataCanvas.init() were also unavailable. Funky.
		growthRateLines = []
		if hasattr(self.parent, 'Window'):
			growthRateLines, maxMbsfDepth = self.UpdateGrowthPlotData()
		else:
			return
		
		tenPercentLine = plot.PolyLine([(0,0),(maxMbsfDepth, maxMbsfDepth * 1.1)], legend='10%', colour='black', width=2)
		# order matters: draw 10% line, then data lines, then data markers/points
		self.growthPlotData = [tenPercentLine] + self.growthPlotData
		self.growthPlotData = growthRateLines + self.growthPlotData

		gc = plot.PlotGraphics(self.growthPlotData, 'Growth Rate', 'mbsf', 'mcd')
		self.growthPlotCanvas.Draw(gc, xAxis = (0, maxMbsfDepth), yAxis = (0, maxMbsfDepth * 1.1))
		self.growthPlotData = []

	def OnUpdateDrawing(self):
		self.polyline_list.append(self.xaxes)
		self.polyline_list.append(self.yaxes)
		gc = plot.PlotGraphics(self.polyline_list, 'Evaluation Graph', 'depth Axis', 'coef Axis')
		self.corrPlotCanvas.Draw(gc, xAxis = (-self.leadLagValue , self.leadLagValue), yAxis = (-1, 1))	
		self.polyline_list = []

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

		# Panel 1
		panel1 = wx.Panel(self.mainPanel, -1)
		grid1 = wx.GridSizer(4, 2)

		buttonsize = 85
		if platform_name[0] == "Windows" :
			buttonsize = 100
			
		grid1.Add(wx.StaticText(panel1, -1, 'Interpolated depth step(meter) : ', (5, 5)), 0, wx.ALIGN_CENTER_VERTICAL)
		self.depthstep = wx.TextCtrl(panel1, -1, "0.11", size = (buttonsize, 25), style=wx.SUNKEN_BORDER )
		#self.depthstep.Enable(False)
		grid1.Add(self.depthstep, 0, wx.ALIGN_RIGHT)
		grid1.Add(wx.StaticText(panel1, -1, 'Correlation window length : ', (5, 5)), 0, wx.ALIGN_CENTER_VERTICAL)
		self.winlength = wx.TextCtrl(panel1, -1, str(self.parent.winLength), size =(buttonsize, 25), style=wx.SUNKEN_BORDER )
		grid1.Add(self.winlength, 0, wx.ALIGN_RIGHT)
		grid1.Add(wx.StaticText(panel1, -1, 'Correlation lead/lag : ', (5, 5)), 0, wx.ALIGN_CENTER_VERTICAL)
		self.leadlag = wx.TextCtrl(panel1, -1, str(self.leadLagValue), size = (buttonsize, 25), style=wx.SUNKEN_BORDER )
		grid1.Add(self.leadlag, 0, wx.ALIGN_RIGHT)

		buttonsize = 90 
		if platform_name[0] == "Windows" :
			buttonsize = 100
		grid1.Add(wx.StaticText(panel1, -1, ' ', (5, 5)), 0, wx.ALIGN_CENTER_VERTICAL)
		addButton = wx.Button(panel1, -1, "Recorrelate", size =(buttonsize, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnCorrelate, addButton)
		grid1.Add(addButton, 0, wx.ALIGN_RIGHT)

		panel1.SetSizer(grid1)
		vbox.Add(panel1, 0, wx.TOP, 9)

		# Panel 2
		panel2 = wx.Panel(self.mainPanel, -1)
		# Setup graph
		# parent, id, pos, size, style, name
		self.corrPlotCanvas = plot.PlotCanvas(panel2)
		if self.parent.Height > 768 :
			self.corrPlotCanvas.SetSize((300,300))
		else :
			self.corrPlotCanvas.SetSize((300,250))

		#self.corrPlotCanvas.SetEnableZoom( True )
		self.corrPlotCanvas.SetEnableGrid( True )
		self.corrPlotCanvas.SetBackgroundColour("White")
		#self.corrPlotCanvas.Centre(wxBOTH)
		self.corrPlotCanvas.Show(True)

		xdata = [ (-self.leadLagValue, 0),( 0, 0), (self.leadLagValue, 0) ]
		self.xaxes = plot.PolyLine(xdata, legend='', colour='black', width =2)
		ydata = [ (0, -1),( 0, 1) ]
		self.yaxes = plot.PolyLine(ydata, legend='', colour='black', width =2)

		data = [ (-self.leadLagValue, 0),( 0, 0), (self.leadLagValue, 0) ]
		self.OnUpdateData(data, [])
		self.OnUpdateDrawing()
		vbox.Add(panel2, 0, wx.TOP, 5)

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
		sizer31 = wx.StaticBoxSizer(wx.StaticBox(panel3, -1, 'Depth adjust (meter)'), orient=wx.VERTICAL)
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
		vbox.Add(panel3, 0, wx.BOTTOM, 3)

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

		dlg = Message3Button(self.parent, "Do you want to create new splice file?")
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

			ret = self.parent.OnShowMessage("About", "Do you want to keep current splice?", 2)
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
		dlg = AltSpliceDialog(self.parent)
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

	def OnUpdateDepth(self, data):
		depth_value = int(10000.0 * float(data)) / 10000.0;
		self.depth.SetValue(str(depth_value))

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
			if splice_count <= 2 :
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
			ret = py_correlator.getData(2)
			if ret != "" :
				self.parent.ParseSpliceData(ret, True)
				l = []
				l.append((-1, -1, -1, -1, -1, -1, -1, -1, -1))
				self.parent.Window.RealSpliceTie.append(l)
				self.parent.Window.RealSpliceTie.append(l)
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
				#lastTie = len(self.parent.Window.RealSpliceTie) -1
				#data = self.parent.Window.RealSpliceTie[lastTie]
				#self.parent.Window.RealSpliceTie.remove(data)
				#data = self.parent.Window.RealSpliceTie[lastTie-1]
				#self.parent.Window.RealSpliceTie.remove(data)
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

		#if self.parent.Window.maxSPcore >= tie_max :
		#	self.undoButton.Enable(False)
		#	self.appendButton.Enable(False)

		if self.parent.Window.SpliceData == []:
			self.undoButton.Enable(False)
			self.appendButton.Enable(False)


	def OnCorrelate(self, evt):
		self.parent.depthStep = float(self.depthstep.GetValue())
		self.parent.winLength = float(self.winlength.GetValue())
		self.parent.leadLag = float(self.leadlag.GetValue())

		self.parent.OnEvalSetup()
		self.parent.OnUpdateGraphSetup(2) 
		self.parent.Window.OnUpdateTie(2)


	def OnUpdate(self):
		self.leadLagValue = float(self.leadlag.GetValue())
		self.corrPlotCanvas.Clear()
		data = [ (-self.leadLagValue, 0),( 0, 0), (self.leadLagValue, 0) ]
		self.OnUpdateData(data, [])
		self.OnUpdateDrawing()
		self.mainPanel.Update()
		self.parent.Update()


	def OnUpdateDepth(self, data):
		depth_value = int(10000.0 * float(data)) / 10000.0;
		self.depth.SetValue(str(depth_value))

	def OnUpdateDepthStep(self, depthstep):
		depthstep = int(10000.0 * float(depthstep)) / 10000.0;
		self.depthstep.SetValue(str(depthstep))

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
		grid2.Add(wx.StaticText(panel2, -1, ' mbsf / mcd ratio', (5, 5)), 0, wx.ALIGN_CENTER_VERTICAL)
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
			dlg = Message3Button(self.parent, "Do you want to create new eld file?")
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
					ratio_str = int(1000.00 * float(ratio)) / 1000.00;
					self.valueD2.SetValue(str(ratio_str))
				else :
					end = str_list.find(" ", 0)
					holename = str_list[0:end]
					start = str_list.find(":", 0) + 2 
					end = len(str_list)
					datatype = str_list[start:end]
					py_correlator.setCorrelate(holename, datatype, squishstart, squishend, self.squishinterval, depthstart, depthend, self.depthinterval, depth_step)
					ratio = py_correlator.getRatio(holename, datatype)
					ratio_str = int(1000.00 * float(ratio)) / 1000.00;
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
			rate = int(100.0 * float(rate)) / 100.0;
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


		# Panel 1
		panel1 = wx.Panel(self.mainPanel, -1)
		grid1 = wx.FlexGridSizer(4, 2)
		grid1.AddGrowableCol(1, 1)

		buttonsize = 40
		if platform_name[0] == "Windows" :
			buttonsize = 60
			
		grid1.Add(wx.StaticText(panel1, -1, 'Interpolated depth step (m):', (5, 5)), 0, wx.ALIGN_CENTER_VERTICAL)
		self.depthstep = wx.TextCtrl(panel1, -1, "0.11", size = (buttonsize, 25), style=wx.SUNKEN_BORDER )
		#self.depthstep.Enable(False)
		grid1.Add(self.depthstep, 0, flag=wx.LEFT | wx.EXPAND, border=5)
		grid1.Add(wx.StaticText(panel1, -1, 'Correlation window length:', (5, 5)), 0, wx.ALIGN_CENTER_VERTICAL)
		self.winlength = wx.TextCtrl(panel1, -1, str(self.parent.winLength), size =(buttonsize, 25), style=wx.SUNKEN_BORDER )
		grid1.Add(self.winlength, 0, flag=wx.LEFT | wx.EXPAND, border=5)
		grid1.Add(wx.StaticText(panel1, -1, 'Correlation lead/lag:', (5, 5)), 0, wx.ALIGN_CENTER_VERTICAL)
		self.leadlag = wx.TextCtrl(panel1, -1, str(self.leadLagValue), size = (buttonsize, 25), style=wx.SUNKEN_BORDER )
		grid1.Add(self.leadlag, 0, flag=wx.LEFT | wx.EXPAND, border=5)

		buttonsize = 90 
		if platform_name[0] == "Windows" :
			buttonsize = 100
		grid1.Add(wx.StaticText(panel1, -1, ' ', (5, 5)), 0, wx.ALIGN_CENTER_VERTICAL)
		#autoButton = wx.Button(panel1, -1, "Auto Core-Log Integration", size =(190, 30))
		#self.mainPanel.Bind(wx.EVT_BUTTON, self.OnAutoCorrelate, autoButton)
		#grid1.Add(autoButton)

		addButton = wx.Button(panel1, -1, "Recorrelate", size =(buttonsize, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnCorrelate, addButton)
		grid1.Add(addButton, 0, wx.ALIGN_CENTER)

		panel1.SetSizer(grid1)
		vbox.Add(panel1, 0, wx.TOP, 2)

		# Panel 2
		panel2 = wx.Panel(self.mainPanel, -1)
		# Setup graph
		# parent, id, pos, size, style, name
		self.corrPlotCanvas = plot.PlotCanvas(panel2)
		if self.parent.Height > 768 :
			self.corrPlotCanvas.SetSize((300,300))
		else :
			#self.corrPlotCanvas.SetSize((300,250))
			self.corrPlotCanvas.SetSize((300,230))

		#self.corrPlotCanvas.SetEnableZoom( True )
		self.corrPlotCanvas.SetEnableGrid( True )
		self.corrPlotCanvas.SetBackgroundColour("White")
		#self.corrPlotCanvas.Centre(wxBOTH)
		self.corrPlotCanvas.Show(True)

		xdata = [ (-self.leadLagValue, 0),( 0, 0), (self.leadLagValue, 0) ]
		self.xaxes = plot.PolyLine(xdata, legend='', colour='black', width =2)
		ydata = [ (0, -1),( 0, 1) ]
		self.yaxes = plot.PolyLine(ydata, legend='', colour='black', width =2)

		data = [ (-self.leadLagValue, 0),( 0, 0), (self.leadLagValue, 0) ]
		self.OnUpdateData(data, [])
		self.OnUpdateDrawing()
		vbox.Add(panel2, 0, wx.TOP, 5)

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

		self.showClue = wx.CheckBox(self.mainPanel, -1, 'Show depth adjust clue')
		self.showClue.SetValue(True)
		self.mainPanel.Bind(wx.EVT_CHECKBOX, self.OnShowClue, self.showClue)
		vbox.Add(self.showClue, 0, wx.BOTTOM, 5)

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
			dlg = Message3Button(self.parent, "Do you want to create new eld file?")
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

	def OnShowClue(self, event):
		self.parent.Window.LogClue = self.showClue.IsChecked()
		self.parent.Window.UpdateDrawing()

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
		self.parent.Window.MakeStraightLie()

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
	
	def OnCorrelate(self, evt):
		self.parent.depthStep = float(self.depthstep.GetValue())
		self.parent.winLength = float(self.winlength.GetValue())
		self.parent.leadLag = float(self.leadlag.GetValue())

		self.parent.OnEvalSetup()
		self.parent.OnUpdateGraphSetup(3)
		self.parent.Window.OnUpdateTie(2)

	def OnUpdate(self):
		self.leadLagValue = float(self.leadlag.GetValue())
		self.corrPlotCanvas.Clear()
		data = [ (-self.leadLagValue, 0),( 0, 0), (self.leadLagValue, 0) ]
		self.OnUpdateData(data, [])
		self.OnUpdateDrawing()
		self.mainPanel.Update()
		self.parent.Update()

		
	def OnUpdateDepth(self, data):
		depthstep = int(10000.0 * float(data)) / 10000.0;
		self.depth.SetValue(str(depthstep))

	def OnUpdateDepthStep(self, depthstep):
		depthstep = int(10000.0 * float(depthstep)) / 10000.0;
		self.depthstep.SetValue(str(depthstep))

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
		self.corrPlotCanvas.Draw(gc, xAxis = (-self.leadLagValue , self.leadLagValue), yAxis = (-1, 1))	
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
		vbox.Add(wx.StaticText(self.mainPanel, -1, '    mbsf      mcd       eld      Age(Ma)     Name', (5, 5)), 0, wx.TOP, 9)

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
			self.depth_label = wx.StaticText(panel2, -1, "Mcd(m)")
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
			self.depth_label = wx.StaticText(panel2, -1, "Mcd(m)")
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
			self.plotMbsfOpt = wx.RadioButton(panel3, -1, "mbsf                ", style=wx.RB_GROUP)
		else :
			self.plotMbsfOpt = wx.RadioButton(panel3, -1, "mbsf", style=wx.RB_GROUP)

		self.plotMbsfOpt.SetValue(False)	
		self.mainPanel.Bind(wx.EVT_RADIOBUTTON, self.SetChangePlot, self.plotMbsfOpt)
		sizer31.Add(self.plotMbsfOpt)
		self.plotMcdOpt = wx.RadioButton(panel3, -1, "mcd")
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

		dlg = Message3Button(self.parent, "Do you want to create new age/depth?")
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
		dlg = Message3Button(self.parent, "Do you want to create new age model?")
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
			pickdepth = int(100.0 * pickdepth) / 100.0;
		else :
			pickmcd = rate * pickdepth
			pickmcd = int(100.0 * pickmcd) / 100.0;
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

		ba = int(1000.0 * float(pickage)) / 1000.0;
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
		pickdepth = int(100.0 * pickdepth) / 100.0;
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
		pickage = int(1000.0 * pickage) / 1000.0;
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
			
		self.all = wx.ComboBox(self.mainPanel, -1, "", (0,0), (buttonsize,-1), (""), wx.CB_DROPDOWN)

		self.all.SetForegroundColour(wx.BLACK)
		self.all.SetEditable(False)
		vbox_top.Add(self.all, 0, wx.LEFT | wx.TOP, 9)
		self.mainPanel.Bind(wx.EVT_COMBOBOX, self.SetTYPE, self.all)

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
		grid2 = wx.FlexGridSizer(4, 2)
		
		if platform_name[0] == "Windows" :			
			grid2.Add(wx.StaticText(panel2, -1, "Type            "), 0, wx.LEFT | wx.RIGHT, 5)
		else :
			grid2.Add(wx.StaticText(panel2, -1, "Type            "), 0, wx.RIGHT, 5)
				
		self.smoothcmd = wx.ComboBox(panel2, -1, "Gaussian", (0,0), (180, -1), \
				("None", "Gaussian"), wx.CB_DROPDOWN)
		self.smoothcmd.SetForegroundColour(wx.BLACK)
		self.smoothcmd.SetEditable(False)
		if platform_name[0] == "Windows" :		
			grid2.Add(self.smoothcmd, 0, wx.RIGHT, 5)
		else :
			grid2.Add(self.smoothcmd)		
		if platform_name[0] == "Windows" :		
			grid2.Add(wx.StaticText(panel2, -1, "Width	    "), 0, wx.LEFT | wx.RIGHT, 5)
		else :
			grid2.Add(wx.StaticText(panel2, -1, "Width	 "), 0, wx.RIGHT, 5)
		
		self.width = wx.TextCtrl(panel2, -1, "9", size=(60, 25), style=wx.SUNKEN_BORDER )
		grid2.Add(self.width, 0, wx.BOTTOM, 3)

		if platform_name[0] == "Windows" :
			self.unitscmd = wx.ComboBox(panel2, -1, "Points", (167, 50), (110, -1), \
					("Points", "Depth(cm)"), wx.CB_DROPDOWN)
		else :
			self.unitscmd = wx.ComboBox(panel2, -1, "Points", (167, 55), (110, -1), \
					("Points", "Depth(cm)"), wx.CB_DROPDOWN)
				
		self.unitscmd.SetForegroundColour(wx.BLACK)
		self.unitscmd.SetEditable(False)
		self.mainPanel.Bind(wx.EVT_COMBOBOX, self.SetUNIT, self.unitscmd)
		#grid2.Add(self.unitscmd)

		if platform_name[0] == "Windows" :	
			grid2.Add(wx.StaticText(panel2, -1, "Display	         "), 0, wx.RIGHT | wx.LEFT, 5)
		else :
			grid2.Add(wx.StaticText(panel2, -1, "Display	      "), 0, wx.RIGHT, 5)
		self.plotcmd = wx.ComboBox(panel2, -1, "Smoothed&Unsmoothed", (0,0), (180, -1), \
				("UnsmoothedOnly", "SmoothedOnly", "Smoothed&Unsmoothed"), wx.CB_DROPDOWN)
		self.plotcmd.SetForegroundColour(wx.BLACK)
		self.plotcmd.SetEditable(False)
		if platform_name[0] == "Windows" :			
			grid2.Add(self.plotcmd, 0, wx.RIGHT, 10)
		else :
			grid2.Add(self.plotcmd)

		sizer2.Add(grid2)
		panel2.SetSizer(sizer2)
		vbox_top.Add(panel2, 0, wx.BOTTOM | wx.TOP | wx.LEFT, 9)

		gridApply2 = wx.GridSizer(1, 2)
		smBtn = wx.Button(self.mainPanel, -1, "Apply", size=(120, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnSmooth, smBtn)
		gridApply2.Add(smBtn)

		self.smBackup = []
		self.smUndo = []

		self.smundoBtn = wx.Button(self.mainPanel, -1, "Undo", size=(120, 30))
		self.mainPanel.Bind(wx.EVT_BUTTON, self.OnUNDOSmooth, self.smundoBtn)
		#self.smundoBtn.Enable(False)
		if platform_name[0] == "Windows" :	
			gridApply2.Add(self.smundoBtn, 0, wx.LEFT, 20)
		else :
			gridApply2.Add(self.smundoBtn, 0, wx.LEFT, 10)		
		vbox_top.Add(gridApply2, 0, wx.LEFT, 10)

		panel3 = wx.Panel (self.mainPanel, -1)
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
		self.cmd = wx.ComboBox(panel3, -1, ">", (0,0), (50,-1), ("<", ">"), wx.CB_DROPDOWN)
		self.cmd.SetForegroundColour(wx.BLACK)
		self.cmd.SetEditable(False)

		grid31.Add(self.cmd, 0, wx.RIGHT, 9)
		self.valueA = wx.TextCtrl(panel3, -1, "9999.99", size=(80, 25), style=wx.SUNKEN_BORDER )
		grid31.Add(self.valueA, 0, wx.RIGHT, 9)

		self.onlyCheck = wx.CheckBox(panel3, -1, ' ')
		self.onlyCheck.SetValue(True)
		self.onlyCheck.Enable(False)
		grid31.Add(self.onlyCheck, 0, wx.BOTTOM, 9)

		grid31.Add(wx.StaticText(panel3, -1, "                     "), 0, wx.RIGHT, 3)
		self.signcmd = wx.ComboBox(panel3, -1, "<", (0,0), (50,-1), ("<", ">"), wx.CB_DROPDOWN) 
		self.signcmd.SetForegroundColour(wx.BLACK)
		self.signcmd.SetEditable(False)
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
		self.optcmd = wx.ComboBox(panel3, -1, "Use all cores", (0,0), (buttonsize, -1), \
				("Use all cores", "Use cores numbered <="), wx.CB_DROPDOWN)
		self.optcmd.SetEditable(False)	
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
		if self.unitscmd.GetValue() == "Depth(cm)" :
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
# 			self.prevSelected = self.all.GetCurrentSelection();
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


	def SetTYPE(self, event):
		type = self.all.GetValue()
		if type  == 'All Holes' :
			return
		elif type == 'Log' :
			return
		elif type == 'Spliced Records' :
			return
		else :
			size = len(type)
			type = type[4:size]

		# Update decivalue & smooth
		if type == "Natural Gamma" :
			type = "NaturalGamma"
		data = self.parent.dataFrame.GetDECIMATE(type)
		if data == None and type == "Natural Gamma" :
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
		self.smBackup = [ self.all.GetValue(), self.smoothcmd.GetValue(), self.width.GetValue(), self.unitscmd.GetValue(), self.plotcmd.GetValue()]

		# Update cull
		cullData = self.parent.dataFrame.GetCULL(type)
		if cullData == None :
			if type == "Natural Gamma" :
				type = "NaturalGamma"
				cullData = self.parent.dataFrame.GetCULL(type)
			elif type == "NaturalGamma" :
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


	def OnUNDODecimate(self, event):
		opt = self.deciUndo[0]
		deci = self.deciUndo[1]
		self.deciUndo = [ self.all.GetValue(), self.decimate.GetValue() ]

		self.decimate.SetValue(deci)
		self.all.SetStringSelection(opt)
		self.OnDecimate(event)
		

	def OnDecimate(self, event):

		type = self.all.GetValue()
		if type == 'Spliced Records' :
			self.parent.OnShowMessage("Error", "Splice Records can not be decimated", 1)
			return

		self.deciUndo = self.deciBackup
		self.deciundoBtn.Enable(True)

		deciValue = int(self.decimate.GetValue())

		if type == "All Holes" :
			max = self.all.GetCount()
			start = 1
			#if self.parent.Window.LogData == [] :
			#	start = 2 
			for i in range(start, max) :
				all_type = self.all.GetString(i)
				if all_type == 'Spliced Records' :
					continue
				py_correlator.decimate(all_type, deciValue)
		else :
			py_correlator.decimate(type, deciValue)

		self.deciBackup = [ self.all.GetValue(), self.decimate.GetValue() ]

		if type != "Log" :
			self.parent.LOCK = 0 
			self.parent.UpdateCORE()
			self.parent.UpdateSMOOTH_CORE()
			self.parent.LOCK = 1 
		else :
			self.parent.UpdateLogData()

		if type == "All Natural Gamma" :
			type = "All NaturalGamma"

		self.parent.dataFrame.OnUPDATEDECIMATE(type, deciValue)
		self.parent.Window.UpdateDrawing()


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

		smoothEnable = 1 

		self.smUndo = self.smBackup

		if self.smoothcmd.GetValue() == "None" : 
			smoothEnable = 0 

		smoothWidth = -1
		if self.smoothcmd.GetValue() == "Gaussian" :
			smoothWidth = int(self.width.GetValue())

		smoothUnit = 1
		if self.unitscmd.GetValue() == "Depth(cm)" :
			smoothUnit = 2

		plot = 1
		if self.plotcmd.GetValue() == "SmoothedOnly" :
			plot = 2
		elif self.plotcmd.GetValue() == "Smoothed&Unsmoothed" :
			plot = 3

		type = self.all.GetValue()

		if self.smBackup != [] : 
			if type == self.smBackup[0] and self.smoothcmd.GetValue() == self.smBackup[1] and self.width.GetValue() == self.smBackup[2] and self.unitscmd.GetValue() == self.smBackup[3] :
				if type  != 'All Holes' and type != 'Log' and type != 'Spliced Records' :
					size = len(type)
					type = type[4:size]
				if type == "Natural Gamma" :
					type = "NaturalGamma"

				if type == 'Spliced Records' :
					self.parent.Window.UpdateSMOOTH('splice', plot-1)
				elif type == 'Log' :
					self.parent.Window.UpdateSMOOTH('log', plot-1)
				else :
					self.parent.dataFrame.OnUPDATE_SMOOTH(type, self.smoothcmd.GetValue(), str(self.width.GetValue()), self.unitscmd.GetValue(), self.plotcmd.GetValue() )
					if type == 'All Holes' :
						self.parent.Window.UpdateSMOOTH('splice', plot-1)
						
				self.parent.Window.UpdateDrawing()
				#print "[DEBUG] Display is updated : " + self.plotcmd.GetValue()
				return


		if smoothEnable == 0 : 
			smoothUnit = -1

		if type == 'Spliced Records' : 
			max = self.all.GetCount()
			start = 1
			#if self.parent.Window.LogData == [] :
			#	start = 2
			for i in range(start, max) :
				all_type = self.all.GetString(i)
				if all_type == 'Spliced Records' :
					continue
				start = all_type.find("All", 0)
				if start >= 0 : 
					py_correlator.smooth(all_type, smoothWidth, smoothUnit)

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
					py_correlator.smooth(all_type, smoothWidth, smoothUnit)
		else :
			py_correlator.smooth(type, smoothWidth, smoothUnit)

		#HYEJUNG CHANGING NOW
		if type == 'Spliced Records' :
			self.parent.UpdateSMOOTH_SPLICE(False)
			if self.parent.Window.LogData != [] and self.parent.Window.SpliceData != [] :
				self.parent.UpdateSMOOTH_LOGSPLICE(True)
			self.parent.Window.UpdateSMOOTH('splice', plot-1)
		elif type == 'Log' :
			#self.parent.UpdateLogData()
			self.parent.UpdateSMOOTH_LogData()
			self.parent.Window.UpdateSMOOTH('log', plot-1)
		else :
			self.parent.UpdateSMOOTH_CORE()
			if type == 'All Holes' :
				self.parent.UpdateSMOOTH_SPLICE(False)
				self.parent.Window.UpdateSMOOTH('splice', plot-1)
		###

		self.smBackup = [ self.all.GetValue(), self.smoothcmd.GetValue(), self.width.GetValue(), self.unitscmd.GetValue(), self.plotcmd.GetValue()]

		if type  != 'All Holes' and type != 'Log' and type != 'Spliced Records' :
			size = len(type)
			type = type[4:size]

		if type == "Natural Gamma" :
			type = "NaturalGamma"

		self.parent.dataFrame.OnUPDATE_SMOOTH(type, self.smoothcmd.GetValue(), str(self.width.GetValue()), self.unitscmd.GetValue(), self.plotcmd.GetValue() )

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
		self.cullUndo = [ self.all.GetValue(), self.nocull.GetValue(), self.valueD.GetValue(), self.cmd.GetValue(), self.valueA.GetValue(), self.onlyCheck.GetValue(), self.signcmd.GetValue(), self.valueB.GetValue(), self.orCheck.GetValue(), self.optcmd.GetValue(), self.valueE.GetValue()]

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
		type = self.all.GetValue()
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
		if self.cmd.GetValue() == "<" :
			sign1 = 2
		sign2 = 1
		if self.signcmd.GetValue() == "<" :
			sign2 = 2

		join = 1
		if self.orCheck.GetValue() == True :
			join = 2

		cullNumber = -1
		if self.optcmd.GetValue() != "Use all cores" :
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

		self.cullBackup = [ self.all.GetValue(), self.nocull.GetValue(), self.valueD.GetValue(), self.cmd.GetValue(), self.valueA.GetValue(), self.onlyCheck.GetValue(), self.signcmd.GetValue(), self.valueB.GetValue(), self.orCheck.GetValue(), self.optcmd.GetValue(), self.valueE.GetValue()]


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
		if platform_name[0] == "Windows"  :
			self.all.SetValue(self.all.GetString(self.prevSelected))	

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
		type = self.all.GetValue()
		idx = self.slider1.GetValue() - 10
		holeWidth = 300 + (idx * 10)
		self.parent.Window.holeWidth = holeWidth 
		self.parent.Window.spliceHoleWidth = holeWidth
		self.parent.Window.logHoleWidth = holeWidth 


	def SetTYPE(self, event):
		type = self.all.GetValue()

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


	def OnChangeMinMax(self, event):
		type = self.all.GetValue()
		minRange = float(self.min.GetValue())
		maxRange = float(self.max.GetValue())

		if type  == 'All Holes' :
			print "[DEBUG] Set All Holes"
		elif type == 'Log' :
			#print "[DEBUG] Set Log"
			self.parent.Window.UpdateRANGE("log", minRange, maxRange)
			self.parent.Window.UpdateDrawing()
		elif type == 'Spliced Records' :
			#print "[DEBUG] Spliced records"
			self.parent.Window.UpdateRANGE("splice", minRange, maxRange)
			self.parent.Window.UpdateDrawing()
		else :
			size = len(type)
			type = type[4:size]

			if type == "Natural Gamma" :
				type = "NaturalGamma"

		self.parent.dataFrame.UpdateMINMAX(type, minRange, maxRange)
		self.parent.Window.UpdateDrawing()

	def OnChangeWidth(self, event):
		#type = self.all.GetValue()
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
		dlg = ColorTableDialog(self.parent)
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
		self.parent.Window.rulerStartDepth = min
		self.parent.Window.SPrulerStartDepth = min
		self.depthmax = max
		x = (self.parent.Window.Height - self.parent.Window.startDepth) * self.parent.Window.gap
		self.parent.Window.length = x / (max - min) * 1.0

		if event != None :
			self.parent.Window.UpdateScroll(1)
			# set..... 
			self.parent.Window.UpdateScroll(2)

		self.slider2.SetValue(1)
		self.parent.Window.UpdateDrawing()
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


		panel1 = wx.Panel(self.mainPanel, -1)
		sizer1 = wx.StaticBoxSizer(wx.StaticBox(panel1, -1, 'Display Range'), orient=wx.VERTICAL)

		self.all = wx.ComboBox(panel1, -1, "", (0,0), (270,-1), (""), wx.CB_DROPDOWN)
		panel1.Bind(wx.EVT_COMBOBOX, self.SetTYPE, self.all)

		self.all.SetForegroundColour(wx.BLACK)
		self.all.SetEditable(False)
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

