#!/usr/bin/env python

## For Mac-OSX
#/usr/bin/env pythonw

from __future__ import print_function
from __future__ import division
from builtins import chr
from builtins import str
from builtins import range
from builtins import object
from past.utils import old_div
import platform
platform_name = platform.uname()

import os
import math

import numpy
import warnings
warnings.simplefilter('ignore', numpy.RankWarning) # stifle RankWarnings when computing growth rate

import wx 
import wx.grid
from wx.lib import plot

import py_correlator
from layout import ImageDatatypeStr

from affine import TieShiftMethod
import canvas
from colordlg import ColorsDialog
import dialog
from smooth import SmoothParameters
import splice
from utils import load_bmp_resource


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
                o.draw(dc, self.printerScale, coord=numpy.array([pnt]))
            elif isinstance(o,plot.PolyLine):
                # draw line with legend
                pnt1= (trhc[0]+legendLHS, trhc[1]+s+lineHeight/2.)
                pnt2= (trhc[0]+legendLHS+legendSymExt[0], trhc[1]+s+lineHeight/2.)
                o.draw(dc, self.printerScale, coord=numpy.array([pnt1, pnt2]))
            else:
                raise TypeError("object is neither PolyMarker or PolyLine instance")
            # draw legend txt
            pnt= (trhc[0]+legendLHS+legendSymExt[0]+5*self._pointSize[0], trhc[1]+s+lineHeight/2.-old_div(legendTextExt[1],2))
            dc.DrawText(o.getLegend(),pnt[0],pnt[1])
            legendItemsDrawn += 1
        dc.SetFont(self._getFont(self._fontSizeAxis)) # reset

# convenience class to maintain data to display on mouseover of growth rate graph
# brgtodo 9/2/2014: What's the right way to do this? Passing around tuples is easy
# but indexing into them makes for hard-to-read code. Using a dictionary would get
# past that issue, but something about a class seems more "correct" to me, probably
# due to heavy OOP background.
class HoverData(object):
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

        self.enablePointLabel = True
        self.pointLabelFunc = self.MouseOverPoint
        self.parent.Bind(wx.EVT_MOTION, self.OnMotion)

    def OnMotion(self, event):
        if self.enablePointLabel:
            dlst = self.GetClosestPoint( self._getXY(event), pointScaled = True)
            if dlst != []:
                curveNum, legend, pIndex, pointXY, scaledXY, distance = dlst
                mDataDict= {"pointXY":pointXY}
                self.UpdatePointLabel(mDataDict)
        event.Skip() #go to next handler
    
    # find closest growth rate point and display its info
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
        if closest:
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
                    if len(mbsfVals) == 1 and mbsfVals[0] == 0.0:
                        growthRate = [1.0, 0.0]
                    else:
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


class CompositePanel(object):
    def __init__(self, parent, mainPanel):
        self.mainPanel = mainPanel
        self.parent = parent
        self.polyline_list = []
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

        self.corrPlotCanvas.enableGrid = True
        self.corrPlotCanvas.enableTitle = False
        self.corrPlotCanvas.SetBackgroundColour("White")
        self.corrPlotCanvas.Show(True)
        
        crSubPanel = wx.Panel(self.crPanel, -1)
        crSubPanel.SetSizer(wx.BoxSizer(wx.HORIZONTAL))
        bmp = load_bmp_resource("icons/sprocket.png")
        crSettingsBtn = wx.BitmapButton(crSubPanel, -1, bmp)
        self.crText = wx.StaticText(crSubPanel, -1, "Step: 0.135 | Window: 1.0 | Lead/Lag: 1.0")
        crFont = self.crText.GetFont()
        crFont.SetPointSize(10)
        self.crText.SetFont(crFont)
        crSubPanel.GetSizer().Add(self.crText, 1, wx.ALIGN_CENTER_VERTICAL)
        crSubPanel.GetSizer().Add(crSettingsBtn, 0, wx.ALIGN_CENTER_VERTICAL)
        
        self.crPanel.GetSizer().Add(self.corrPlotCanvas, 1, wx.EXPAND)
        self.crPanel.GetSizer().Add(crSubPanel, 0, wx.EXPAND)
        
        self.crPanel.Bind(wx.EVT_BUTTON, self.OnEvalSettings, crSettingsBtn)

        # Growth Rate graph panel
        self.grPanel = wx.Panel(self.plotNote, -1)
        self.grPanel.SetSizer(wx.BoxSizer(wx.VERTICAL))

        self.grText = wx.StaticText(self.grPanel, -1, "Mouse over a point to show data.")
        self.growthPlotCanvas = GrowthRatePlotCanvas(self.grPanel, self.grText)
        self.growthPlotCanvas.enableGrid = True
        self.growthPlotCanvas.enableTitle = False
        self.growthPlotCanvas.enableLegend = True
        self.growthPlotCanvas.fontSizeLegend = 10
        self.growthPlotCanvas.SetBackgroundColour('White')
        self.growthPlotCanvas.Show(True)

        self.grPanel.GetSizer().Add(self.growthPlotCanvas, 1, wx.EXPAND)
        self.grPanel.GetSizer().Add(self.grText, 0, wx.EXPAND)
        
        # Affine Table panel
        atPanel = wx.Panel(self.plotNote, -1)
        atsz = wx.BoxSizer(wx.VERTICAL)
        self.table = wx.grid.Grid(atPanel, -1)
        self.table.SetRowLabelSize(0) # hide row headers
        self.table.DisableDragRowSize()
        self.table.EnableEditing(False)
        self.table.CreateGrid(numRows=0, numCols=3)
        for colidx, label in enumerate(["Core", "Offset", "Type"]):
            self.table.SetColLabelValue(colidx, label)
        self.table.SetSelectionMode(wx.grid.Grid.SelectRows)
        self.breakTieButton = wx.Button(atPanel, -1, "Break TIE")
        self.breakTieButton.Enable(False)
        atsz.Add(self.table, 1, wx.EXPAND)
        atsz.Add(self.breakTieButton, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        atPanel.SetSizer(atsz)
        self.atPanel = atPanel		

        self.plotNote.AddPage(self.crPanel, "Evaluation")
        self.plotNote.AddPage(self.grPanel, "Growth Rate")
        self.plotNote.AddPage(self.atPanel, "Shifts")
        
        # event handling
        self.atPanel.Bind(wx.EVT_BUTTON, self.OnBreakTie, self.breakTieButton)
        self.atPanel.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.OnShiftsTableSelection, self.table)

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

        # affected cores and action type panel
        panel3 = wx.Panel(self.mainPanel, -1)

        sizer31 = wx.StaticBoxSizer(wx.StaticBox(panel3, -1, 'TIE Shift Options'), orient=wx.VERTICAL)
        tieShiftScopes = [
            "This core or chain, all deeper chains and deeper cores in all holes",
            "This core or chain and cores below this core or chain",
            "This core or chain only"
        ]
        self.applyCore = wx.Choice(panel3, -1, choices=tieShiftScopes)
        self.applyCore.SetSelection(0)
        sizer31.Add(self.applyCore, 0, wx.EXPAND | wx.BOTTOM, 5)
        
        tdpSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.actionType = wx.Choice(panel3, -1, choices=["To tie", "To best correlation"])
        self.actionType.SetSelection(0)
        # hardcode width to prevent 'm' label being pushed too far right
        self.depthField = wx.TextCtrl(panel3, -1, size=(80,-1))
        self.depthField.Enable(False)
        tdpSizer.Add(self.actionType, 0, wx.RIGHT, 5)
        tdpSizer.Add(self.depthField)
        tdpSizer.Add(wx.StaticText(panel3, -1, 'm'))
        sizer31.Add(tdpSizer, 0, wx.EXPAND | wx.TOP, 5)
        
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
        self.setButton = wx.Button(projectPanel, -1, "SET...")
        self.mainPanel.Bind(wx.EVT_BUTTON, self.OnSETButton, self.setButton)
        setSizer.Add(self.setButton, 1, wx.EXPAND)
        projectPanel.SetSizer(setSizer)
        vbox.Add(projectPanel, 0, wx.EXPAND)

        self.saveButton = wx.Button(self.mainPanel, -1, "Save Affine (and Splice if one exists)...")
        self.mainPanel.Bind(wx.EVT_BUTTON, self.OnSAVE, self.saveButton)
        vbox.Add(self.saveButton, 0, wx.EXPAND | wx.BOTTOM, 2)
        self.saveButton.Enable(False)

        self.mainPanel.SetSizer(vbox)

    def OnInitUI(self):
        self.adjustButton.Enable(False)
        self.clearButton.Enable(False)

    def EnableSETButton(self, enable):
        self.setButton.Enable(enable)
        
    def OnSAVE(self, event):
        self.parent.OnSAVE(event=None)

    def OnAdjust(self, evt):
        sel = self.applyCore.GetSelection()
        if sel == 0:
            shiftMethod = TieShiftMethod.TiedAndDeeperInHoles
        elif sel == 1:
            shiftMethod = TieShiftMethod.TiedAndDeeperInChain
        elif sel == 2:
            shiftMethod = TieShiftMethod.CoreOrChain
        self.parent.OnAdjustCore(shiftMethod, self.GetActionType())

        self.parent.Window.activeTie = -1
        self.UpdateGrowthPlot()

    # AffineTiePointChangeListener - update controls' state depending on
    # new number of active affine tie points
    def TiePointCountChanged(self, count):
        if count == 0:
            self.applyCore.Enable(False)
            self.actionType.Enable(False)
            self.adjustButton.Enable(False)
            self.clearButton.Enable(False)
            self.comment.Enable(False)
        elif count == 1:
            self.clearButton.Enable(True)
        elif count == 2:
            self.applyCore.Enable(True)
            self.actionType.Enable(True)
            self.adjustButton.Enable(True)
            self.comment.Enable(True)

    def OnClearTie(self, evt):
        self.parent.Window.ClearCompositeTies()
        self.parent.Window.UpdateDrawing() # or tie graphics won't clear until mouseover

    def OnEvalSettings(self, evt):
        dlg = dialog.CorrParamsDialog(self.plotNote, self.parent.minDepthStep, self.parent.depthStep, self.parent.winLength, self.parent.leadLag)
        pos = self.crText.GetScreenPosition()
        dlg.SetPosition(pos)
        if dlg.ShowModal() == wx.ID_OK:
            self.parent.OnEvalSetup(dlg.outDepthStep, dlg.outWinLength, dlg.outLeadLag)
            self.parent.OnUpdateGraphSetup(1)
            if len(self.parent.Window.TieData) > 0 :
                self.parent.Window.OnUpdateTie(1)
                
    def OnBreakTie(self, evt):
        row = self.table.GetSelectedRows()[0] # only one row can be selected
        corestr = str(self.table.GetCellValue(row, 0)) # str() to convert from Unicode, col 0 is core
        self.parent.affineManager.breakTie(corestr)
        self.breakTieButton.Enable(False)

    def OnShiftsTableSelection(self, evt):
        shiftType = self.table.GetCellValue(evt.GetRow(), 2) # col 2 is shift type
        self.breakTieButton.Enable("TIE" in shiftType)

    def OnSETButton(self, evt):
        dlg = dialog.SetDialog(self.parent)
        dlg.Centre(wx.BOTH)
        result = dlg.ShowModal()
        if result == wx.ID_OK:
            isRate = dlg.percentRadio.GetValue()
            value = dlg.outRate if isRate else dlg.outOffset
            if dlg.deeperAndChainsInHoles.GetValue():
                self.parent.affineManager.setDeeperAndChainsInHoles(dlg.outHole, dlg.outCore, value, isRate, dlg.outType, dlg.outComment)
            elif dlg.deeperAndChainsInThisHole.GetValue():
                self.parent.affineManager.setDeeperAndChainsInThisHole(dlg.outHole, dlg.outCore, value, isRate, dlg.outType, dlg.outComment)
            elif dlg.coreOrChain.GetValue():
                self.parent.affineManager.setCoreOrChain(dlg.outHole, dlg.outCore, value, isRate, dlg.outType, dlg.outComment)
            elif dlg.coreAndBelow.GetValue(): # SET current core and below
                coreList = dlg.outCoreList
                self.parent.affineManager.setAll(dlg.outHole, coreList, value, isRate, dlg.outType, dlg.outComment)
            elif dlg.coreAndChain.GetValue(): # entire chain
                self.parent.affineManager.setChainRoot(dlg.outHole, dlg.outCore, dlg.outOffset, dlg.outType, dlg.outComment)
            else: # current core only
                self.parent.affineManager.SET(dlg.outHole, dlg.outCore, value, isRate, dlg.outType, dlg.outComment)

            self.parent.AffineChange = True
            #py_correlator.saveAttributeFile(self.parent.CurrentDir + 'tmp.affine.table', 1)

            # todo: notify Corelyzer of change
            #self.parent.ShiftSectionSend(ciA.hole, ciA.holeCore, shift, opId)

            if self.parent.showReportPanel == 1:
                self.parent.OnUpdateReport()

            self.parent.UpdateData()
            self.parent.UpdateStratData()
            self.parent.Window.UpdateDrawing()

    def OnUpdateDepth(self, data):
        depth = int(10000.0 * float(data)) / 10000.0
        self.depthField.SetValue(str(depth))

    # brgtodo 9/4/2014: only called from this module, and always to set "empty" data:
    # merge f'ns and add default params?
    def OnUpdateData(self, data, bestdata, best):
        self.polyline_list = []
        self.bestOffset = best 
        line = plot.PolyLine(data, legend='', colour='red', width =2) 
        self.polyline_list.append(line)
        if bestdata != [] :
            bestline = plot.PolyLine(bestdata, legend='', colour='blue', width =5) 
            self.polyline_list.append(bestline)

    # 9/18/2013 brg: Identical to OnUpdateData() above... and in SplicePanel
    # plot correlation for datatype with which tie is being made
    def OnAddFirstData(self, data, bestdata, best):
        self.polyline_list = []
        self.bestOffset = best
        line = plot.PolyLine(data, legend='', colour='red', width =2) 
        self.polyline_list.append(line)
        if bestdata != [] : 
            bestline = plot.PolyLine(bestdata, legend='', colour='blue', width =5) 
            self.polyline_list.append(bestline)

    # plot correlation for datatypes with which tie is *not* being made
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
        # self.corrPlotCanvas.Clear() - causes flicker on Mac
        data = [(-self.parent.leadLag, 0), (0, 0), (self.parent.leadLag, 0)]
        self.OnUpdateData(data, [], 0)
        self.UpdateEvalStatus()
        self.OnUpdateDrawing()
        
    def UpdateAffineTable(self):
        affineRows = self.parent.affineManager.getAffineRowsForUI()
        tableRowCount = self.table.GetNumberRows()

        if len(affineRows) > tableRowCount:
            self.table.InsertRows(pos=0, numRows=len(affineRows))
        elif len(affineRows) < tableRowCount:
            self.table.DeleteRows(pos=0, numRows=tableRowCount - len(affineRows))
        
        for rowIndex, ar in enumerate(affineRows):
            self.table.SetCellValue(rowIndex, 0, ar[0])
            self.table.SetCellValue(rowIndex, 1, ar[1])
            self.table.SetCellValue(rowIndex, 2, ar[2])

    def ClearAffineTable(self):
        if self.table.GetNumberRows() > 0:
            self.table.ClearGrid()
            self.table.DeleteRows(pos=0, numRows=self.table.GetNumberRows())

    def UpdateEvalStatus(self):
        roundedDepthStep = int(10000.0 * float(self.parent.depthStep)) / 10000.0
        self.crText.SetLabel("Step: {} | Window: {} | Lead/Lag: {}".format(roundedDepthStep, self.parent.winLength, self.parent.leadLag))

    def OnUpdateDrawing(self):
        self.polyline_list.append(self.xaxes)
        self.polyline_list.append(self.yaxes)
        gc = plot.PlotGraphics(self.polyline_list, xLabel='depth (m)', yLabel='correlation coefficient (r)')
        self.corrPlotCanvas.Draw(gc, xAxis = (-self.parent.leadLag , self.parent.leadLag), yAxis = (-1, 1))
        
    def GetDepthValue(self):
        return self.depthField.GetValue()
    
    def GetBestOffset(self):
        return self.bestOffset
    
    def GetActionType(self):
        actionType = 0 # To best correlation
        actionStr = self.actionType.GetStringSelection()
        if actionStr == "To tie":
            actionType = 1
        return actionType
    
    def GetComment(self):
        return self.comment.GetValue()
        
# Obsolete, replaced by SpliceIntervalPanel but left as-is for now
# to avoid issues with its tendrils in MainFrame. TODO 3/10/2019
class SplicePanel(object):
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

        self.corrPlotCanvas.enableGrid = True
        self.corrPlotCanvas.SetBackgroundColour("White")
        #self.corrPlotCanvas.Centre(wxBOTH)
        self.corrPlotCanvas.Show(True)
        
        crSubPanel = wx.Panel(panel2, -1)
        crSubPanel.SetSizer(wx.BoxSizer(wx.HORIZONTAL))
        bmp = load_bmp_resource("icons/sprocket.png")
        crSettingsBtn = wx.BitmapButton(crSubPanel, -1, bmp)
        self.crText = wx.StaticText(crSubPanel, -1, "Step: 0.135 | Window: 1.0 | Lead/Lag: 1.0")
        crFont = self.crText.GetFont()
        crFont.SetPointSize(10)
        self.crText.SetFont(crFont)
        crSubPanel.GetSizer().Add(self.crText, 1, wx.ALIGN_CENTER_VERTICAL)
        crSubPanel.GetSizer().Add(crSettingsBtn, 0, wx.ALIGN_CENTER_VERTICAL)
        
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

        hbox3 = wx.FlexGridSizer(3, 2, gap=(0,0))
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

        sizer31_1 = wx.FlexGridSizer(3, 1, gap=(0,0))
        sizer31 = wx.StaticBoxSizer(wx.StaticBox(panel3, -1, 'Depth adjust (m)'), orient=wx.VERTICAL)
        self.depth = wx.TextCtrl(panel3, -1, "0.0", size=(buttonsize, 25), style=wx.SUNKEN_BORDER )
        self.depth.Enable(False)
        sizer31.Add(self.depth)
        sizer31_1.Add(sizer31)

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

        sizer32 = wx.GridSizer(3, 1, gap=(0,0))
        self.spliceButton = wx.Button(panel3, -1, "Splice To Tie", size=(buttonsize, 30))
        self.mainPanel.Bind(wx.EVT_BUTTON, self.OnSplice, self.spliceButton)
        self.spliceButton.Enable(False)
        sizer32.Add(self.spliceButton)
        
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
        vbox.Add(self.saveButton, 0)
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
            if self.parent.UnsavedChanges() == True :
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
                print("append....at begin", splice_count)
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
        pos = self.crText.GetScreenPosition()
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
        self.evalPlot = BetterLegendPlotCanvas(self)
        self.evalPlot.enableGrid = True
        self.evalPlot.enableTitle = False
        self.evalPlot.SetBackgroundColour("White")
        self.evalPlot.Show(True)
        evsz = wx.BoxSizer(wx.VERTICAL)
        evsz.Add(self.evalPlot, 1, wx.EXPAND)
        
        paramPanel = wx.Panel(self, -1)
        psz = wx.BoxSizer(wx.HORIZONTAL)
        bmp = load_bmp_resource("icons/sprocket.png")
        settingsBtn = wx.BitmapButton(paramPanel, -1, bmp)
        self.crText = wx.StaticText(paramPanel, -1, "Step: 0.135 | Window: 1.0 | Lead/Lag: 1.0")
        crFont = self.crText.GetFont()
        crFont.SetPointSize(10)
        self.crText.SetFont(crFont)
        psz.Add(self.crText, 1, wx.ALIGN_CENTER_VERTICAL)
        psz.Add(settingsBtn, 0, wx.ALIGN_CENTER_VERTICAL)
        paramPanel.SetSizer(psz)
        
        evsz.Add(paramPanel, 0, wx.EXPAND)
        self.SetSizer(evsz)
        
        paramPanel.Bind(wx.EVT_BUTTON, self.OnEvalSettings, settingsBtn)

        data = [ (-self.leadLag, 0), (0, 0), (self.leadLag, 0) ]
        self.OnUpdateData(data, [])
        self.OnUpdateDrawing()

    def OnEvalSettings(self, evt):
        pos = self.crText.GetScreenPosition()
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
        line = plot.PolyLine(data, legend='', colour='red', width=2)
        self.polylines.append(line)
        if bestdata != [] : 
            bestline = plot.PolyLine(bestdata, legend='', colour='blue', width=5)
            self.polylines.append(bestline)

    def OnAddFirstData(self, data, bestdata, best):
        line = plot.PolyLine(data, legend='', colour='red', width=2)
        self.polylines.append(line)
        if bestdata != [] : 
            bestline = plot.PolyLine(bestdata, legend='', colour='blue', width=5)
            self.polylines.append(bestline)

    def OnAddData(self, data):
        line = plot.PolyLine(data, legend='', colour='grey', width=2)
        self.polylines.append(line)

    def OnUpdateDrawing(self): # called by client to redraw
        # update axes
        xdata = [ (-self.leadLag, 0), (0, 0), (self.leadLag, 0) ]
        self.xaxes = plot.PolyLine(xdata, legend='', colour='black', width=2)
        ydata = [ (0, -1),(0, 1) ]
        self.yaxes = plot.PolyLine(ydata, legend='', colour='black', width=2)
        self.polylines.append(self.xaxes)
        self.polylines.append(self.yaxes)
        
        gc = plot.PlotGraphics(self.polylines, '', 'depth (m)', 'correlation coef (r)')
        self.evalPlot.Draw(gc, xAxis=(-self.leadLag , self.leadLag), yAxis=(-1, 1))
        self.polylines = []


class SpliceIntervalPanel(object):
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

        self.spliceHoleColors = wx.CheckBox(panel, -1, "Splice interval colors by hole")
        self.mainPanel.Bind(wx.EVT_CHECKBOX, self.OnSpliceHoleColor, self.spliceHoleColors)
        psz.Add(self.spliceHoleColors, 0, wx.ALL, 10)

        # interval table, evaluation graph tabs
        self.note = wx.Notebook(panel, -1)
        
        # interval table
        gridPanel = wx.Panel(self.note, -1)
        gpsz = wx.BoxSizer(wx.VERTICAL)
        self.intervalTable = wx.grid.Grid(gridPanel, -1)
        self.intervalTable.SetRowLabelSize(0) # hide row headers
        self.intervalTable.DisableDragRowSize()
        self.intervalTable.EnableEditing(False)
        self.intervalTable.CreateGrid(numRows=0, numCols=3)
        for colidx, label in enumerate(["Core", "Top (m)", "Bottom (m)"]):
            self.intervalTable.SetColLabelValue(colidx, label)
        self.intervalTable.SetSelectionMode(wx.grid.Grid.SelectRows)
        gpsz.Add(self.intervalTable, 1, wx.EXPAND)
        self.intervalTable.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.OnSelectRow)
        self.intervalTable.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.OnSetDepth)
        gridPanel.SetSizer(gpsz)
        self.note.AddPage(gridPanel, "Intervals")
        self.gridPanel = gridPanel
        
        # gaps table
        gapsPanel = wx.Panel(self.note, -1)
        gapSizer = wx.BoxSizer(wx.VERTICAL)
        self.gapsTable = wx.grid.Grid(gapsPanel, -1)
        self.gapsTable.SetRowLabelSize(0) # hide row headers
        self.gapsTable.DisableDragRowSize()
        self.gapsTable.EnableEditing(False)
        self.gapsTable.CreateGrid(numRows=0, numCols=2)
        for colidx, label in enumerate(["Top (m)", "Bottom (m)"]):
            self.gapsTable.SetColLabelValue(colidx, label)
        self.gapsTable.SetSelectionMode(wx.grid.Grid.SelectRows)
        gapSizer.Add(self.gapsTable, 1, wx.EXPAND)
        self.gapsTable.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.OnDClickGapRow)
        gapsPanel.SetSizer(gapSizer)
        self.note.AddPage(gapsPanel, "Gaps")
        self.gapsPanel = gapsPanel
        
        # evaluation graph
        evalPlotPanel = EvalPlotPanel(self.parent, self.note, self.parent.depthStep, self.parent.winLength, self.parent.leadLag)
        self.note.AddPage(evalPlotPanel, "Evaluation Graph")
        self.evalPanel = evalPlotPanel

        psz.Add(self.note, 3, wx.EXPAND)
        self.note.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnSelectNote)
        self.note.SetSelection(0)
        
        # comments, delete button
        ctrlPanel = wx.Panel(panel, -1)
        cpsz = wx.BoxSizer(wx.VERTICAL)
        cbox = wx.StaticBoxSizer(wx.StaticBox(ctrlPanel, -1, "Interval Comments"))
        self.commentText = dialog.CommentTextCtrl(ctrlPanel, -1, "[interval comment]", style=wx.TE_MULTILINE, size=(-1, 100))
        self.commentText.Bind(wx.EVT_KILL_FOCUS, self._saveComment)
        cbox.Add(self.commentText, 1)
        cpsz.Add(cbox, 0, wx.EXPAND | wx.ALL, 5)

        self.delButton = wx.Button(ctrlPanel, -1, "Delete Interval")
        ctrlPanel.Bind(wx.EVT_BUTTON, self.OnDelete, self.delButton)
        cpsz.Add(self.delButton, 0, wx.EXPAND | wx.ALL, 5)
        ctrlPanel.SetSizer(cpsz)
        psz.Add(ctrlPanel, 0, wx.EXPAND)

        # tie option buttons (split/tie)
        tsbox = wx.StaticBoxSizer(wx.StaticBox(panel, -1, "Tie Options"), orient=wx.VERTICAL)	
        tieSplitPanel = wx.Panel(panel, -1)
        self.topTieButton = wx.Button(tieSplitPanel, -1, "Edit Top Tie")
        tieSplitPanel.Bind(wx.EVT_BUTTON, self.OnTopTieButton, self.topTieButton)
        self.botTieButton = wx.Button(tieSplitPanel, -1, "Edit Bottom Tie")
        tieSplitPanel.Bind(wx.EVT_BUTTON, self.OnBotTieButton, self.botTieButton)
        tspsz = wx.FlexGridSizer(rows=2, cols=2, gap=(0,10))
        tspsz.AddGrowableCol(1, proportion=1)
        tspsz.Add(wx.StaticText(tieSplitPanel, -1, "Top: "), 1, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        tspsz.Add(self.topTieButton, 1, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        tspsz.Add(wx.StaticText(tieSplitPanel, -1, "Bottom: "), 1, wx.ALIGN_CENTER_VERTICAL)
        tspsz.Add(self.botTieButton, 1, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM, 1)
        tieSplitPanel.SetSizer(tspsz)
        tsbox.Add(tieSplitPanel, 1, wx.EXPAND)
        psz.Add(tsbox, 0, wx.EXPAND | wx.TOP, 10)
        
        self.saveButton = wx.Button(panel, -1, "Save Splice and Affine...")
        self.saveButton.Bind(wx.EVT_BUTTON, self.OnSave)
        psz.Add(self.saveButton, 0, wx.EXPAND | wx.ALL, 10)
                
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(panel, 1, wx.EXPAND)
        self.mainPanel.SetSizer(vbox)
        
    def UpdateGapsTable(self, gaps):
        rowCount = len(gaps)
        self._adjustTableRows(self.gapsTable, rowCount)
        for row, g in enumerate(gaps):
            self.gapsTable.SetCellValue(row, 0, str(round(g.top, 3)))
            self.gapsTable.SetCellValue(row, 1, str(round(g.bot, 3)))

    # update all row data and selection
    def _updateIntervalTable(self):
        rows = self.parent.spliceManager.count()
        self._adjustTableRows(self.intervalTable, rows)
        for row, si in enumerate(self.parent.spliceManager.getIntervals()):
            self._makeIntervalTableRow(row, si)
        self._updateIntervalTableSelection()
    
    def OnSelectNote(self, event):
        newSel = event.GetSelection()
        self.gridPanel.Hide()
        self.gapsPanel.Hide()
        self.evalPanel.Hide()
        if newSel == 0:
            self.gridPanel.Show()
            self.gapsPanel.Hide()
            self.evalPanel.Hide()
        elif newSel == 1:
            self.gridPanel.Hide()
            self.gapsPanel.Show()
            self.evalPanel.Hide()
        elif newSel == 2:
            self.gridPanel.Hide()
            self.gapsPanel.Hide()
            self.evalPanel.Show()
    
    def UpdateUI(self):
        self._updateIntervalTable()
        self._updateButtons()
        if self.parent.spliceManager is not None:
            self.parent.spliceManager.findGaps()
        
    def OnInitUI(self): # to match other panels' interface
        self.UpdateUI()

    # add cells for SpliceInterval si at specified row
    def _makeIntervalTableRow(self, row, si):
        self.intervalTable.SetCellValue(row, 0, str(si.coreinfo.getHoleCoreStr()))
        self.intervalTable.SetCellValue(row, 1, str(round(si.getTop(), 3)))
        self.intervalTable.SetCellValue(row, 2, str(round(si.getBot(), 3)))
        
    # add/delete rows in wx.Grid table to match int rows
    def _adjustTableRows(self, table, rows):
        currows = table.GetNumberRows()
        if currows > rows:
            delcount = currows - rows
            table.DeleteRows(pos=rows, numRows=delcount)
        elif currows < rows:
            addcount = rows - currows
            table.InsertRows(pos=0, numRows=addcount)

    # update all row data and selection
    def _updateIntervalTable(self):
        rows = self.parent.spliceManager.count()
        self._adjustTableRows(self.intervalTable, rows)
        for row, si in enumerate(self.parent.spliceManager.getIntervals()):
            self._makeIntervalTableRow(row, si)
        self._updateIntervalTableSelection()
            
    # update current selection
    def _updateIntervalTableSelection(self):
        cursel = self.parent.spliceManager.getSelectedIndex()
        if cursel == -1:
            self.intervalTable.ClearSelection()
            self.lastInterval = None
            self._updateComment("")
        else:
            self.intervalTable.SelectRow(cursel)
            self.intervalTable.MakeCellVisible(cursel, 0) # scroll to row if not visible
            self.lastInterval = self.parent.spliceManager.getSelectedInterval()
            self._updateComment(self.lastInterval.comment)
            
    # create label for tie/split buttons
    def _getButtonLabel(self, tie):
        label = "No Action"
        if tie.canTie():
            label = "Tie {}".format(tie.getButtonName())
        elif tie.isTied():
            label = "Split {}".format(tie.getButtonName())
        return label

    # Enable/disable buttons and update button text to reflect splice state
    def _updateButtons(self):
        hasSel = self.parent.spliceManager.hasSelection() 
        self.delButton.Enable(hasSel)
        hasIntervals = self.parent.spliceManager.count() > 0
        self.saveButton.Enable(hasIntervals)
        if hasSel:
            self.delButton.SetLabel("Delete Interval {}".format(self.parent.spliceManager.getSelectedInterval().getHoleCoreStr()))
            
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

    # selected SpliceInterval changed through click, update GUI to reflect
    def OnSelectionChange(self):
        self._updateButtons()
        self._updateIntervalTableSelection()
        
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
        self.parent.spliceManager.pushState()
        if tie.isTied():
            tie.split()
        else:
            tie.tie()
        self.UpdateUI()
        self.parent.Window.UpdateDrawing()

    def OnSave(self, event):
        self.parent.OnSAVE(event=None)

    def OnDClickGapRow(self, event):
        visibleMin = self.parent.Window.rulerStartDepth
        visibleMax = self.parent.Window.rulerEndDepth - 2.0
        selRow = self.gapsTable.GetSelectedRows()[0]
        gapTop = float(self.gapsTable.GetCellValue(selRow, 0))
        gapBot = float(self.gapsTable.GetCellValue(selRow, 1))
        if not splice.Interval(gapTop, gapBot).overlaps(splice.Interval(visibleMin, visibleMax)):
            self.parent.OnUpdateStartDepth(gapTop)
    
    def OnSelectRow(self, event):
        self.parent.spliceManager.selectByIndex(event.GetRow())
        self.lastInterval = self.parent.spliceManager.getIntervalAtIndex(event.GetRow())
        self.parent.Window.UpdateDrawing()	
            
    def OnSetDepth(self, event):
        if event.GetCol() == 0: # jump to interval depth on double-click of ID column
            visibleMin = self.parent.Window.rulerStartDepth
            visibleMax = self.parent.Window.rulerEndDepth - 2.0
            intervalTop = self.parent.spliceManager.getSelectedInterval()
            if not intervalTop.overlaps(splice.Interval(visibleMin, visibleMax)):
                self.parent.OnUpdateStartDepth(intervalTop.getTop())
            return
        
        # Top or Bot depth cell was double-clicked, open SetDepthDialog
        # for manual editing of selected interval's top or bottom depth.
        curint = self.parent.spliceManager.getSelectedInterval()
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
            self.parent.spliceManager.pushState()
            tie.move(depth)
            self.UpdateUI()
            self.parent.Window.UpdateDrawing()

    def OnSpliceHoleColor(self, event):
        checked = self.spliceHoleColors.IsChecked()
        self.parent.Window.drawSpliceInHoleColors = checked
        self.parent.optPanel.spliceHoleColors.SetValue(checked)
        self.parent.Window.UpdateDrawing()

    # wrappers for EvalPlotPanel
    def OnAddFirstData(self, data, bestdata, best):
        self.evalPanel.OnAddFirstData(data, bestdata, best)
    def OnAddData(self, data):
        self.evalPanel.OnAddData(data)
    def OnUpdate(self):
        self.evalPanel.OnUpdate()


############## end SpliceIntervalPanel #################################

class AutoPanel(object):
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
        sizer1.Add(wx.StaticText(panel1, -1, 'Stretch/Compress core data between:', (5, 5)), 0)

        grid1 = wx.FlexGridSizer(2, 4, gap=(0,0))
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

        sizer1.Add(wx.StaticText(panel1, -1, 'Slide Log up/down between:', (5, 5)), 0, wx.TOP, 9)

        grid12 = wx.FlexGridSizer(2, 4, gap=(0,0))
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

        grid13 = wx.FlexGridSizer(2, 3, gap=(0,0))
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

        vbox.Add(wx.StaticText(self.mainPanel, -1, 'Select Hole(s):', (5, 5)), 0)
        
        buttonsize = 300
        if platform_name[0] == "Windows" :
            buttonsize = 285
            
        if self.parent.Height > 768 :
            self.fileList = wx.ListBox(self.mainPanel, -1, (0,0),(buttonsize,95), style=wx.LB_HSCROLL|wx.LB_NEEDED_SB|wx.LB_EXTENDED)
        else :
            self.fileList = wx.ListBox(self.mainPanel, -1, (0,0),(buttonsize,65), style=wx.LB_HSCROLL|wx.LB_NEEDED_SB|wx.LB_EXTENDED)

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

        grid2 = wx.FlexGridSizer(3, 2, gap=(0,0))
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
            self.resultList = wx.ListBox(self.mainPanel, -1, (0,0),(buttonsize,130), style=wx.LB_NEEDED_SB)
        else :
            #self.resultList = wx.ListBox(self.mainPanel, -1, (0,0),(buttonsize,100), "", style=wx.LB_NEEDED_SB)
            self.resultList = wx.ListBox(self.mainPanel, -1, (0,0),(buttonsize,60), style=wx.LB_NEEDED_SB)

        self.mainPanel.Bind(wx.EVT_LISTBOX, self.OnSelectRate, self.resultList)
        vbox.Add(self.resultList, 0, wx.BOTTOM, 3)

        buttonsize = 95
        if platform_name[0] == "Windows" :
            buttonsize = 92
            
        # Panel 3
        panel3 = wx.Panel(self.mainPanel, -1)
        grid3 = wx.FlexGridSizer(1, 3, gap=(0,0))
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
        vbox.Add(self.saveButton, 0)
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
        depthrange = int(old_div((depthend - depthstart), self.depthinterval))
        squishrange = int(old_div((squishend - squishstart), self.squishinterval))

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


class ELDPanel(object):
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

        self.corrPlotCanvas.enableGrid = True
        self.corrPlotCanvas.SetBackgroundColour("White")
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
        bmp = load_bmp_resource("icons/sprocket.png")
        crSettingsBtn = wx.BitmapButton(crSubPanel, -1, bmp)
        self.crText = wx.StaticText(crSubPanel, -1, "Step: 0.135 | Window: 1.0 | Lead/Lag: 1.0")
        crFont = self.crText.GetFont()
        crFont.SetPointSize(10)
        self.crText.SetFont(crFont)
        crSubPanel.GetSizer().Add(self.crText, 1, wx.ALIGN_CENTER_VERTICAL)
        crSubPanel.GetSizer().Add(crSettingsBtn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        
        panel2.GetSizer().Add(self.corrPlotCanvas, 1, wx.EXPAND)
        panel2.GetSizer().Add(crSubPanel, 0, wx.EXPAND)
        
        panel2.Bind(wx.EVT_BUTTON, self.OnEvalSettings, crSettingsBtn)
        
        vbox.Add(panel2, 1, wx.EXPAND | wx.BOTTOM, 10)

        buttonsize = 300
        if platform_name[0] == "Windows" :
            buttonsize = 285
        self.fileList = wx.ListBox(self.mainPanel, -1, (0,0),(buttonsize,105), style=wx.LB_HSCROLL|wx.LB_NEEDED_SB)
        self.mainPanel.Bind(wx.EVT_LISTBOX, self.OnSelectTie, self.fileList)
        vbox.Add(self.fileList, 0, wx.BOTTOM, 3)

        # Panel 3
        panel3 = wx.Panel(self.mainPanel, -1)
        #hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        hbox3 = wx.FlexGridSizer(1, 2, gap=(5,5))
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
            
        sizer32 = wx.GridSizer(4, 1, gap=(0,0))
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
        vbox.Add(self.saveButton, 0)
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
        i = old_div(tieNo, 2) 
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
        pos = self.crText.GetScreenPosition()
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


class AgeDepthPanel(object):
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
            self.ageList = wx.ListBox(self.mainPanel, -1, (0, 0), (buttonsize,220), style=wx.LB_HSCROLL|wx.LB_NEEDED_SB|wx.LB_EXTENDED)	 
            font = self.ageList.GetFont()
            font.SetFamily(wx.FONTFAMILY_ROMAN)
            self.ageList.SetFont(font)
            #self.ageList = gizmos.TreeListCtrl(self.mainPanel, -1, (0,0), size=(buttonsize,220), style = wx.TR_DEFAULT_STYLE| wx.TR_FULL_ROW_HIGHLIGHT)

        else :
            #self.ageList = wx.ListBox(self.mainPanel, -1, (0, 0), (buttonsize,170), "", style=wx.LB_HSCROLL|wx.LB_NEEDED_SB|wx.LB_EXTENDED)	 
            self.ageList = wx.ListBox(self.mainPanel, -1, (0, 0), (buttonsize,120), style=wx.LB_HSCROLL|wx.LB_NEEDED_SB|wx.LB_EXTENDED)	 
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
        grid2 = wx.FlexGridSizer(1, 2, gap=(0,0))
        grid2.AddGrowableCol(1, 1)

        sizer21 = wx.StaticBoxSizer(wx.StaticBox(panel2, -1, 'User-defined Age'), orient=wx.VERTICAL)
        grid21 = wx.FlexGridSizer(4, 2, gap=(0,0))
    
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

        grid22 = wx.GridSizer(4, 1, gap=(0,0))
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
        grid3 = wx.FlexGridSizer(1, 2, gap=(0,0))
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

        grid32 = wx.GridSizer(2, 1, gap=(0,0))

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

        grid42 = wx.FlexGridSizer(1, 5, gap=(0,0))
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

        grid51 = wx.FlexGridSizer(1, 5, gap=(0,0))
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
        if platform_name[0] == "Windows":
            age_list = self.ageList.GetSelections()
            for sel in age_list:
                selected_item = self.ageList.GetString(sel)
        else:
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
        self.parent.Window.ageLength = old_div(x, (max - min)) * 1.0
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
        self.parent.Window.ageYLength = old_div(x, (max - min)) * 1.0
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
        if platform_name[0] == "Windows":
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
        if platform_name[0] == "Windows":
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
        self.parent.Window.ageYLength = old_div(idx * x, (max - min)) * 1.0
        self.parent.Window.UpdateDrawing()

    def OnAgeZoom(self, evt):
        # 1- 20
        # start -> 95  : 90 + (idx * 5)
        idx = self.slider1.GetValue()  
        #self.parent.Window.ageLength = 90 + (idx * 5)
        min = self.parent.Window.minAgeRange 
        max = self.parent.Window.maxAgeRange 
        x = (self.parent.Window.splicerX - 100 - self.parent.Window.compositeX - self.parent.Window.AgeShiftX)
        self.parent.Window.ageLength = old_div(idx * x, (max - min)) * 1.0
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
            # self.parent.Window.MainViewMode = False
            self.parent.Window.DrawData["MouseInfo"] = []
            self.viewBtn.SetLabel("Main Core View")
            self.OnAgeViewAdjust(evt)
            self.OnDepthViewAdjust(evt)
        else :
            self.ageX = self.parent.Window.splicerX 
            self.parent.Window.splicerX = self.X
            # self.parent.Window.MainViewMode = True 
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

class FilterPanel(object):
    def __init__(self, parent, mainPanel):
        self.mainPanel = mainPanel
        self.decPanel = None
        self.smoothPanel = None
        self.cullPanel = None
        self.imgPanel = None
        self.parent = parent
        self.locked = False
        self.prevSelected = 0
        self.addItemsInFrame()

        # init undo members
        self.deciUndo = [ "All Holes", "1" ]
        self.deciBackup = [ "All Holes", "1" ]
        self.smBackup = []
        self.smUndo = []
        self.cullBackup = [ "All Holes", False, "5.0", ">", "9999.99", True, "<", "-9999.99", False, "Use all cores", "999" ]
        self.cullUndo = [ "All Holes", False, "5.0", ">", "9999.99", True, "<", "-9999.99", False, "Use all cores", "999" ]

    def addItemsInFrame(self):
        vbox_top = wx.BoxSizer(wx.VERTICAL)

        # Filter Range
        vbox_top.Add(wx.StaticText(self.mainPanel, -1, "Apply Filters to Data Type: "), 0, wx.LEFT | wx.TOP, 9)
        buttonsize = 290
        self.all = wx.Choice(self.mainPanel, -1, (0,0), (buttonsize,-1))
        self.all.SetForegroundColour(wx.BLACK)
        vbox_top.Add(self.all, 0, wx.ALL, 5)
        self.mainPanel.Bind(wx.EVT_CHOICE, self.SetTYPE, self.all)

        ### Decimate
        decPanel = wx.Panel(self.mainPanel, -1)
        decSizer = wx.StaticBoxSizer(wx.StaticBox(decPanel, -1, 'Decimate'), orient=wx.VERTICAL)
        self.deciState = wx.StaticText(decPanel, -1, "None (show every point)")
        decBtnPanel = wx.Panel(decPanel, -1)
        decBtnSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.deciCreate = wx.Button(decBtnPanel, -1, "Create", size=(120, 30))
        decPanel.Bind(wx.EVT_BUTTON, self.OnCreateDecimate, self.deciCreate)

        self.deciDelete = wx.Button(decBtnPanel, -1, "Delete", size=(120, 30))
        self.deciDelete.Enable(False)
        decPanel.Bind(wx.EVT_BUTTON, self.OnClearDecimate, self.deciDelete)

        decBtnSizer.Add(self.deciCreate, 0)
        decBtnSizer.Add(self.deciDelete, 0)
        decBtnPanel.SetSizer(decBtnSizer)

        decSizer.Add(self.deciState, 1, wx.BOTTOM, 10)
        decSizer.Add(decBtnPanel, 1, wx.EXPAND)
        decPanel.SetSizer(decSizer)
        vbox_top.Add(decPanel, 0, wx.TOP | wx.EXPAND, 5)
        self.decPanel = decPanel

        ### Smoothing
        smoothPanel = wx.Panel(self.mainPanel, -1)
        smoothSizer = wx.StaticBoxSizer(wx.StaticBox(smoothPanel, -1, 'Gaussian Smoothing'), orient=wx.VERTICAL)
        self.smoothState1 = wx.StaticText(smoothPanel, -1, "[Current smoothing state]")
        self.smoothState2 = wx.StaticText(smoothPanel, -1, "[Smoothing style]")
        smoothSizer.Add(self.smoothState1, 0, wx.BOTTOM)
        smoothSizer.Add(self.smoothState2, 1, wx.BOTTOM, 10)

        smoothBtnPanel = wx.Panel(smoothPanel, -1)
        smoothBtnSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.smCreate = wx.Button(smoothBtnPanel, -1, "Create", size=(120, 30))
        self.mainPanel.Bind(wx.EVT_BUTTON, self.OnCreateSmooth, self.smCreate)
        self.smDelete = wx.Button(smoothBtnPanel, -1, "Delete", size=(120, 30))
        self.smDelete.Enable(False)
        self.mainPanel.Bind(wx.EVT_BUTTON, self.OnClearSmooth, self.smDelete)
        smoothBtnSizer.Add(self.smCreate)
        smoothBtnSizer.Add(self.smDelete)
        smoothBtnPanel.SetSizer(smoothBtnSizer)
        smoothSizer.Add(smoothBtnPanel)

        smoothPanel.SetSizer(smoothSizer)
        vbox_top.Add(smoothPanel, 0, wx.TOP | wx.EXPAND, 5)
        self.smoothPanel = smoothPanel

        ### Culling
        cullPanel = wx.Panel(self.mainPanel, -1)
        cullSizer = wx.StaticBoxSizer(wx.StaticBox(cullPanel, -1, 'Cull'), orient=wx.VERTICAL)

        self.cullState1 = wx.StaticText(cullPanel, -1, "[Cull from section tops]")
        self.cullState2 = wx.StaticText(cullPanel, -1, "[Cull data values > X]")
        self.cullState3 = wx.StaticText(cullPanel, -1, "[Cull data values < X]")
        cullSizer.Add(self.cullState1)
        cullSizer.Add(self.cullState2)
        cullSizer.Add(self.cullState3, 1, wx.BOTTOM, 10)
        cullPanel.SetSizer(cullSizer)

        cullBtnPanel = wx.Panel(cullPanel, -1)
        self.cullCreate = wx.Button(cullBtnPanel, -1, "Create", size=(120, 30))
        self.mainPanel.Bind(wx.EVT_BUTTON, self.OnCreateCull, self.cullCreate)
        self.cullDelete = wx.Button(cullBtnPanel, -1, "Delete", size=(120, 30))
        self.mainPanel.Bind(wx.EVT_BUTTON, self.OnClearCull, self.cullDelete)
        self.cullDelete.Enable(False)

        cullBtnSizer = wx.BoxSizer(wx.HORIZONTAL)
        cullBtnSizer.Add(self.cullCreate)
        cullBtnSizer.Add(self.cullDelete)
        cullBtnPanel.SetSizer(cullBtnSizer)
        cullSizer.Add(cullBtnPanel)

        vbox_top.Add(cullPanel, 0, wx.TOP | wx.EXPAND, 5)
        self.cullPanel = cullPanel

        # Image lateral culling
        imgPanel = wx.Panel(self.mainPanel, -1)
        imgSizer = wx.StaticBoxSizer(wx.StaticBox(imgPanel, -1, 'Image culling'), orient=wx.VERTICAL)
        self.imgState = wx.StaticText(imgPanel, -1, "None")
        imgBtnPanel = wx.Panel(imgPanel, -1)
        imgBtnSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.imgCreate = wx.Button(imgBtnPanel, -1, "Create", size=(120, 30))
        imgPanel.Bind(wx.EVT_BUTTON, self.OnCreateImageCull, self.imgCreate)

        self.imgDelete = wx.Button(imgBtnPanel, -1, "Delete", size=(120, 30))
        self.imgDelete.Enable(False)
        imgPanel.Bind(wx.EVT_BUTTON, self.OnClearImageCull, self.imgDelete)

        imgBtnSizer.Add(self.imgCreate, 0)
        imgBtnSizer.Add(self.imgDelete, 0)
        imgBtnPanel.SetSizer(imgBtnSizer)

        imgSizer.Add(self.imgState, 1, wx.BOTTOM, 10)
        imgSizer.Add(imgBtnPanel, 1, wx.EXPAND)
        imgPanel.SetSizer(imgSizer)
        vbox_top.Add(imgPanel, 0, wx.TOP | wx.EXPAND, 5)

        self.mainPanel.SetSizer(vbox_top)
        self.imgPanel = imgPanel

    # Disable all controls and re-init status text. Used when no data is loaded.
    def DisableAllControls(self):
        self.all.Enable(False)
        self.all.Clear()
        self.deciCreate.Enable(False)
        self.deciDelete.Enable(False)
        self.ClearDecimateStateText()
        self.smCreate.Enable(False)
        self.smDelete.Enable(False)
        self.ClearSmoothStateText()
        self.cullCreate.Enable(False)
        self.cullDelete.Enable(False)
        self.ClearCullStateText()

    def OnLock(self):
        self.locked = True 

    def OnRelease(self):
        self.locked = False 

    def ClearCullStateText(self):
        self.cullState1.SetLabel("No cull applied.")
        self.cullState2.SetLabel("")
        self.cullState3.SetLabel("")

    def OnClearCull(self, event):
        datatype = self._curType()
        self.ApplyCull(datatype) # clear cull

    def OnCreateCull(self, event):
        dlg = dialog.CullDialog(self.parent, self._curCull())
        pos = self.cullCreate.GetScreenPosition()
        dlg.SetPosition(pos)
        if dlg.ShowModal() != wx.ID_OK:
            return
        self.ApplyCull(self._curType(), True, dlg.outCullTops, dlg.outCullValue1, dlg.outCullValue2, dlg.outSign1, dlg.outSign2, dlg.outJoin)

    # bcull = 0 no cull, 1 apply cull
    # cullValue: amount to trim from top
    # cullNumber: -1 to use all cores, other to use cores numbered [number and less]: always set to -1
    # cullStrength, always 167.0 for some reason
    # value1 = > cull value, 9999.99 or -9999.99 indicates dummy, no actual culling
    # value2 = < cull value
    # sign1 = 1 for greater than, 2 for less than
    # sign2 = same as sign1
    # join = 1 if only sign1 + value1 is used, 2 if both are used
    def ApplyCull(self, datatype, bcull=False, cullValue=0.0, value1=9999.99, value2=-9999.99, sign1=1, sign2=2, join=1):
        cullStrength = 167.0 # always use this magic number
        cullNumber = -1 # always show all cores
        self.parent.dataFrame.UpdateCULL(datatype, bcull, cullValue, cullNumber, value1, value2, sign1, sign2, join)
        py_correlator.cull(datatype, bcull, cullValue, cullNumber, cullStrength, value1, value2, sign1, sign2, join)

        self.parent.LOCK = 0
        self.parent.UpdateCORE()
        self.parent.UpdateSMOOTH_CORE()
        self.parent.LOCK = 1

        if datatype == "Natural Gamma":
            datatype = "NaturalGamma"

        # Delete cull file if it's been cleared. We no longer have an enable/disable mechanism
        # for cull tables. If a cull file exists, it's "enabled" and we always apply it.
        deleteTable = not bcull
        self.parent.dataFrame.OnUPDATE_CULLTABLE(datatype, deleteTable)
        self.UpdateCullState(self._curCull())
        self.parent.Window.UpdateDrawing()

    def UpdateCullState(self, cullData):
        hasCull = cullData is not None and cullData[1] == True
        if hasCull:
            print("cullData = {}".format(cullData))
            statuses = self.GetCullStatusStrings(cullData)
            # fill cullStateX text with applied culling parameters, maximum 3.
            for index, cullState in enumerate([self.cullState1, self.cullState2, self.cullState3]):
                if index < len(statuses):
                    cullState.SetLabel(statuses[index])
                else:
                    cullState.SetLabel("")
        else:
            self.ClearCullStateText()
        self.cullCreate.Enable(True)
        self.cullCreate.SetLabel("Edit" if hasCull else "Create")
        self.cullDelete.Enable(hasCull)

    # Return true if the cull sign and value aren't the '9999.9' or '-9999.9' dummy values
    # passed to py_correlator.cull() to indicate no cull depending on associated sign (<, >).
    def _nonDummyValue(self, cullSign, cullValue):
        return (cullSign == '>' and float(cullValue) < 9999.0) or (cullSign == '<' and float(cullValue) > -9999.0)

    # Create cull status strings for display based on variable-length cullData list.
    def GetCullStatusStrings(self, cullData):
        strs = []
        datalen = len(cullData)
        if datalen >= 3:
            strs.append("Culling {} cm from core tops".format(cullData[2]))
        if datalen == 5 or datalen == 6:
            if self._nonDummyValue(cullData[3], cullData[4]):
                strs.append("Culling data values {} {}".format(cullData[3], cullData[4]))
        elif datalen == 7 or datalen == 8:
            if self._nonDummyValue(cullData[3], cullData[4]):
                strs.append("Culling data values {} {}".format(cullData[3], cullData[4]))
            if self._nonDummyValue(cullData[5], cullData[6]):
                strs.append("Culling data values {} {}".format(cullData[5], cullData[6]))
        return strs

    # Update filter panels to reflect change in selected filter data type.
    def SetTYPE(self, event):
        self.all.Enable(True) # ensure dropdown is enabled
        type = self._curType() # get self.all type, correcting for "Natural Gamma" spacing

        # update filter UI based on selected type
        self._updateVisibleFilters(type)
        
        if type == ImageDatatypeStr:
            icp = self.parent.Window.imageCullPct
            self.UpdateImageCullState(icp)
        else:
            data = self.parent.dataFrame.GetDECIMATE(type) # returns tuple of decimate, smooth data
            self.UpdateDecimateState(data[0])
            if data[1] != "":
                smoothParams = SmoothParameters.createWithString(data[1])
                self.UpdateSmoothState(smoothParams)
            else:
                self.UpdateSmoothState(None)

            cullData = self.parent.dataFrame.GetCULL(type)
            if cullData == None and type == "NaturalGamma":
                type = "Natural Gamma"
                cullData = self.parent.dataFrame.GetCULL(type)
            self.UpdateCullState(cullData)

    # show appropriate filters for data types vs Image
    def _updateVisibleFilters(self, selectedType):
        showDataFilters = selectedType != ImageDatatypeStr
        self.decPanel.Show(showDataFilters)
        self.smoothPanel.Show(showDataFilters)
        self.cullPanel.Show(showDataFilters)
        self.imgPanel.Show(not showDataFilters)
        self.mainPanel.GetSizer().Layout()
        
    # Apply decimate value to given datatype.
    # datatype: data type string
    # deciValue: integer decimate value
    def ApplyDecimate(self, datatype, deciValue):
        py_correlator.decimate(datatype, deciValue)
        self.parent.LOCK = 0
        self.parent.UpdateCORE()
        self.parent.UpdateSMOOTH_CORE()
        self.parent.LOCK = 1
        self.parent.dataFrame.OnUPDATEDECIMATE(datatype, deciValue)
        self.UpdateDecimateState(deciValue)
        self.parent.Window.UpdateDrawing()

    # Pop DecimateDialog to Create/Edit decimate filter.
    def OnCreateDecimate(self, event):
        datatype = self._curType()
        curdec = self._curDecimate()
        decdlg = dialog.DecimateDialog(self.parent, curdec)
        pos = self.deciCreate.GetScreenPosition()
        decdlg.SetPosition(pos)
        if decdlg.ShowModal() != wx.ID_OK:
            return
        deciValue = decdlg.deciValue
        self.ApplyDecimate(datatype, deciValue)

    def ClearDecimateStateText(self):
        self.deciState.SetLabel("None (show all points).")

    # Reset decimate filter to 1.
    def OnClearDecimate(self, evt):
        self.ApplyDecimate(self._curType(), 1)

    # Update GUI to reflect current type's decimate filter.
    # deciStr: string representing decimate value for current type
    def UpdateDecimateState(self, deciStr):
        decimate = int(deciStr) > 1
        if decimate:
            self.deciState.SetLabel("Show every {} points".format(deciStr))
        else:
            self.ClearDecimateStateText()
            self.deciCreate.SetLabel("Create")
        self.deciCreate.Enable(True)
        self.deciCreate.SetLabel("Edit" if decimate else "Create")
        self.deciDelete.Enable(decimate)

    def UpdateImageCullState(self, icp):
        cullExists = icp is not None
        if cullExists:
            self.imgState.SetLabel("Trim {}% from left and right of images".format(icp))
        else:
            self.imgState.SetLabel("None.")
        self.imgCreate.Enable(True)
        self.imgCreate.SetLabel("Edit" if cullExists else "Create")
        self.imgDelete.Enable(cullExists)

    def OnCreateImageCull(self, event):
        icdlg = dialog.ImageCullDialog(self.parent, self.parent.Window.imageCullPct)
        pos = self.imgCreate.GetScreenPosition()
        icdlg.SetPosition(pos)
        if icdlg.ShowModal() != wx.ID_OK:
            return
        self.parent.Window.imageCullPct = icdlg.icpValue
        self.UpdateImageCullState(icdlg.icpValue)
        self.parent.Window.InvalidateImages()
        self.parent.Window.UpdateDrawing()

    def OnClearImageCull(self, event):
        self.parent.Window.imageCullPct = None
        self.UpdateImageCullState(self.parent.Window.imageCullPct)
        self.parent.Window.InvalidateImages()
        self.parent.Window.UpdateDrawing()

    def _curType(self):
        datatype = self.all.GetStringSelection()
        if datatype == "Natural Gamma":
            datatype = "NaturalGamma"
        return datatype

    def _curDecimate(self):
        datatype = self._curType()
        decimate, _ = self.parent.dataFrame.GetDECIMATE(datatype) # _ = smooth dummy
        return decimate

    def _curSmooth(self):
        datatype = self._curType()
        _, smooth = self.parent.dataFrame.GetDECIMATE(datatype) # _ = decimate dummy
        if smooth != "":
            return SmoothParameters.createWithString(smooth)
        else:
            return None

    def _curCull(self):
        datatype = self._curType()
        cullData = self.parent.dataFrame.GetCULL(datatype)
        if cullData == None and datatype == "NaturalGamma":
            datatype = "Natural Gamma"
            cullData = self.parent.dataFrame.GetCULL(datatype)
        return cullData

    def UpdateSmoothState(self, smoothData):
        if smoothData is not None:
            self.smoothState1.SetLabel("Width: {} {}".format(smoothData.getWidthString(), smoothData.getUnitsString()))
            self.smoothState2.SetLabel("Display: {}".format(smoothData.getStyleString().replace('&', '&&')))
        else:
            self.ClearSmoothStateText()
        self.smCreate.Enable(True)
        self.smCreate.SetLabel("Create" if smoothData is None else "Edit")
        self.smDelete.Enable(smoothData is not None)

    def ClearSmoothStateText(self):
        self.smoothState1.SetLabel("No smoothing applied.")
        self.smoothState2.SetLabel("")

    def OnClearSmooth(self, event):
        datatype = self._curType()
        self.ApplySmooth(datatype, params=None)

    def OnCreateSmooth(self, event):
        curSmooth = self._curSmooth()
        if curSmooth is None:
            smdlg = dialog.SmoothDialog(self.parent)
        else:
            smdlg = dialog.SmoothDialog(self.parent, curSmooth.width, curSmooth.units, curSmooth.style)
        pos = self.smCreate.GetScreenPosition()
        smdlg.SetPosition(pos)
        if smdlg.ShowModal() == wx.ID_OK:
            datatype = self._curType()
            self.ApplySmooth(datatype, smdlg.outSmoothParams)

    def ApplySmooth(self, datatype, params):
        if params:
            py_correlator.smooth(datatype, params.width, params.units)
        else: # remove smoothing
            py_correlator.smooth(datatype, -1, -1)
        self.parent.UpdateSMOOTH_CORE()
        self.parent.dataFrame.OnUPDATE_SMOOTH(datatype, params)
        self.UpdateSmoothState(self._curSmooth())
        self.parent.Window.UpdateDrawing()


class PreferencesPanel(object):
    def __init__(self, parent, mainPanel):
        self.mainPanel = mainPanel
        self.parent = parent
        self.addItemsInFrame()
        self.prevSelected = 0
        self.visibleDepthInterval = 20.0

    def OnActivateWindow(self, event):
        if self.showSpliceWindow.IsChecked(): 
            self.parent.OnActivateWindow(1)
            self.parent.misecond.Check(True)
        else:
            self.parent.OnActivateWindow(0)
            self.parent.misecond.Check(False)

    # def OnActivateScroll(self, event):
    # 	self.parent.SetIndependentScroll(self.indSpliceScroll.IsChecked())

    def OnUndoMinMax(self, event):
        pass

    def OnUPDATEMinMax(self, selection, min, max):
        n = self.variableChoice.GetCount()
        for i in range(n) :
            if self.variableChoice.GetString(i) == selection :
                self.variableChoice.SetSelection(i)
                self.varMin.SetValue(min)
                self.varMax.SetValue(max)
                self.OnChangeMinMax(1)
                return

    def SetTYPE(self, event):
        datatype = self.variableChoice.GetStringSelection()
        if datatype == "Natural Gamma":
            datatype = "NaturalGamma"
        ret = self.parent.Window.GetMINMAX(datatype)
        if ret is not None:
            self.varMin.SetValue(str(ret[0]))
            self.varMax.SetValue(str(ret[1]))

    # convert self.variableChoice string ("All Susceptibility") to type string ("Susceptibility")
    def _FixListTypeStr(self, type):
        if type == "Natural Gamma":
            type = "NaturalGamma"
        return type

    def OnChangeMinMax(self, event):
        datatype = self.variableChoice.GetStringSelection()
        minRange = float(self.varMin.GetValue())
        maxRange = float(self.varMax.GetValue())
        applyType = self._FixListTypeStr(datatype)
        self.parent.dataFrame.UpdateMINMAX(applyType, minRange, maxRange)
        self.parent.Window.UpdateDrawing()

    # def OnChangeHoleWidth(self, event):
    # 	idx = self.holeWidthSlider.GetValue() - 10
    # 	holeWidth = 200 + (idx * 10) - 50 # leave 50 for image
    # 	self.parent.Window.holeWidth = holeWidth
    # 	self.parent.Window.spliceHoleWidth = holeWidth
    # 	self.parent.Window.logHoleWidth = holeWidth
    # 	if event == None :
    # 		return
    # 	self.parent.Window.UpdateDrawing()

    def OnChangePlotWidth(self, event):
        idx = self.plotWidthSlider.GetValue()
        plotWidth = 100 + (idx * 2) # width range: 100-300px
        self.parent.Window.layoutManager.plotWidth = plotWidth
        if event is None:
            return
        self.parent.Window.UpdateDrawing()
        
    def OnChangeImageWidth(self, event):
        idx = self.imageWidthSlider.GetValue()
        imageWidth = 30 + (idx * 2) # width range: 30-230px
        self.parent.Window.layoutManager.imageWidth = imageWidth
        if event is None:
            return
        self.parent.Window.InvalidateImages() # wx.Images must be recreated at appropriate width
        self.parent.Window.UpdateDrawing()

    def OnChangeRulerUnits(self, evt):
        self.parent.Window.rulerUnits = self.unitsPopup.GetStringSelection()
        self.parent.Window.UpdateDrawing()

    def OnTieShiftScale(self, event):
        self.parent.Window.shift_range = float(self.tie_shift.GetValue())

    def OnChangeColor(self, event):
        dlg = ColorsDialog(self.parent, self.parent.Window.colorDict, self.parent.Window.defaultColorDict)
        dlg.Centre()
        dlg.ShowModal()
        dlg.Destroy()

    def OnShowLine(self, event):
        self.parent.Window.showHoleGrid = self.showPlotLines.GetValue()
        self.parent.Window.UpdateDrawing()

    def OnDepthViewAdjust(self, event):
        try:
            interval = float(self.depthRangeText.GetValue())
        except ValueError:
            if event is not None: # 'Apply' button was clicked
                self.parent.OnShowMessage("Error", "{} is not a valid depth.".format(self.depthRangeText.GetValue()), 1)
                return
            else:
                print("WARNING: Invalid depth interval {} in displayRangeText, defaulting to 10m.".format(self.depthRangeText.GetValue()))
                interval = 10.0 # default to 10m
                self.depthRangeText.SetValue(str(interval))
        self.visibleDepthInterval = interval
        self.parent.OnUpdateDisplayInterval(interval, updateScroll=event is not None)

    def OnZoomIn(self, event):
        interval = float(self.depthRangeText.GetValue())
        self.depthRangeText.SetValue(str(interval / 2.0))
        self.OnDepthViewAdjust(event)

    def OnZoomOut(self, event):
        interval = float(self.depthRangeText.GetValue())
        self.depthRangeText.SetValue(str(interval * 2.0))
        self.OnDepthViewAdjust(event)
        
    def OnShowSectionDepths(self, event):
        self.parent.Window.showSectionDepths = self.showSectionDepths.IsChecked()
        self.parent.Window.UpdateDrawing()

    def OnShowAffineShiftInfo(self, event):
        self.parent.Window.showAffineShiftInfo = self.showAffineShiftInfo.IsChecked()
        self.parent.Window.UpdateDrawing()
        
    def OnShowAffineTies(self, event):
        self.parent.Window.showAffineTies = self.showAffineTies.IsChecked()
        self.UpdateAffineTieStyle()
        self.parent.Window.UpdateDrawing()

    def OnAffineTieStyle(self, event):
        sel = self.affineTieStyle.GetSelection()
        self.parent.Window.showAffineTieArrows = (sel == 0)
        self.parent.Window.UpdateDrawing()

    def UpdateAffineTieStyle(self):
        self.affineTieStyle.Enable(self.showAffineTies.IsChecked())

    def OnShowCoreInfo(self, event):
        self.parent.Window.showCoreInfo = self.showCoreInfo.IsChecked()
        self.parent.Window.UpdateDrawing()

    def OnShowOutOfRangeData(self, event):
        self.parent.Window.showOutOfRangeData = self.showOutOfRangeData.IsChecked()
        self.parent.Window.UpdateDrawing()

    def OnShowAffineShiftStrips(self, event):
        self.parent.Window.showAffineShiftStrips = self.showAffineShiftStrips.IsChecked()
        self.UpdateShowColorLegendCheckbox()
        self.parent.Window.UpdateDrawing()

    def OnShowColorLegend(self, event):
        self.parent.Window.showColorLegend = self.showColorLegend.IsChecked()
        self.parent.Window.UpdateDrawing()

    def OnSpliceHoleColor(self, event):
        checked = self.spliceHoleColors.IsChecked()
        self.parent.Window.drawSpliceInHoleColors = checked
        self.parent.spliceIntervalPanel.spliceHoleColors.SetValue(checked)
        self.parent.Window.UpdateDrawing()

    # Enable color legend checkbox based on affine shift strips state.
    # Legend is only drawn when shift strips are drawn.
    def UpdateShowColorLegendCheckbox(self):
        self.showColorLegend.Enable(self.showAffineShiftStrips.IsChecked())

    def OnShowDepthLine(self, event):
        self.parent.Window.showDepthLine = self.showDepthLine.IsChecked()
        if self.parent.Window.showDepthLine:
            self.parent.Window.depthLinePos = None # forget last fixed line position, follow cursor
        self.parent.Window.UpdateDrawing()

    def OnShowPlotOverlays(self, event):
        self.parent.Window.showPlotOverlays = self.showPlotOverlays.IsChecked()
        self.parent.Window.UpdateDrawing()

    def OnHoleVisibilityButton(self, event):
        # Only show loaded holes in dialog. (layoutManager visible holes dict preserves
        # last-known visibility state for previously-loaded holes that may not currently
        # be loaded.)
        lmVisDict = self.parent.Window.layoutManager.visibleHoles
        holeVisDict = {h:lmVisDict[h] for h in self.parent.Window.getLoadedHoles()}
        dlg = dialog.HoleVisibilityDialog(self.parent, holeVisDict)
        pos = self.holeVisibilityButton.GetScreenPosition()
        dlg.SetPosition(pos)
        dlg.ShowModal()

    def OnDatatypeVisibilityAndOrderButton(self, event):
        datatypeOrder = list(self.parent.Window.layoutManager.getDatatypeOrder()) # copy
        lmVisDict = self.parent.Window.layoutManager.visibleDatatypes
        typeVisDict = {dt:lmVisDict[dt] for dt in datatypeOrder}
        dlg = dialog.DatatypeVisibilityAndOrderDialog(self.parent, datatypeOrder, typeVisDict)
        pos = self.displayOrderButton.GetScreenPosition()
        dlg.SetPosition(pos)
        dlg.ShowModal()

    def OnGroupByDatatype(self, event):
        self.parent.Window.layoutManager.setGroupByDatatype(self.dtRadio.GetValue())
        self.parent.Window.UpdateDrawing()

    def addItemsInFrame(self):
        vbox_top = wx.BoxSizer(wx.VERTICAL)

        self.showSpliceWindow = wx.CheckBox(self.mainPanel, -1, 'Show splice window partition')
        self.mainPanel.Bind(wx.EVT_CHECKBOX, self.OnActivateWindow, self.showSpliceWindow)
        vbox_top.Add(self.showSpliceWindow, 0, wx.ALL, 10)

        ### Data selections and arrangements panel
        layoutPanel = wx.Panel(self.mainPanel, -1)
        layoutSizer = wx.StaticBoxSizer(wx.StaticBox(layoutPanel, -1, "Data selections and arrangements"), orient=wx.VERTICAL)

        self.displayOrderButton = wx.Button(layoutPanel, -1, "Show/arrange data types...")
        self.mainPanel.Bind(wx.EVT_BUTTON, self.OnDatatypeVisibilityAndOrderButton, self.displayOrderButton)
        self.holeVisibilityButton = wx.Button(layoutPanel, -1, "Show holes...")
        self.mainPanel.Bind(wx.EVT_BUTTON, self.OnHoleVisibilityButton, self.holeVisibilityButton)

        groupBySizer = wx.BoxSizer(wx.HORIZONTAL)
        groupBySizer.Add(wx.StaticText(layoutPanel, -1, "Group by"), 0, wx.RIGHT, 10)
        self.dtRadio = wx.RadioButton(layoutPanel, -1, "Data type", style=wx.RB_GROUP)
        self.holeRadio = wx.RadioButton(layoutPanel, -1, "Hole")
        self.dtRadio.SetValue(True)
        self.mainPanel.Bind(wx.EVT_RADIOBUTTON, self.OnGroupByDatatype, self.dtRadio)
        self.mainPanel.Bind(wx.EVT_RADIOBUTTON, self.OnGroupByDatatype, self.holeRadio)
        groupBySizer.Add(self.dtRadio, 1)
        groupBySizer.Add(self.holeRadio, 1)

        self.showPlotOverlays = wx.CheckBox(layoutPanel, -1, "Overlay plots by data type")
        self.mainPanel.Bind(wx.EVT_CHECKBOX, self.OnShowPlotOverlays, self.showPlotOverlays)

        layoutSizer.Add(self.displayOrderButton, 0, wx.BOTTOM | wx.EXPAND, 10)
        layoutSizer.Add(self.holeVisibilityButton, 0, wx.BOTTOM | wx.EXPAND, 10)
        layoutSizer.Add(groupBySizer, 0, wx.BOTTOM | wx.EXPAND, 10)
        layoutSizer.Add(self.showPlotOverlays)
        layoutPanel.SetSizer(layoutSizer)

        vbox_top.Add(layoutPanel, 0, wx.EXPAND)

        ### Data range panel
        depthScalePanel = wx.Panel(self.mainPanel, -1)
        depthScaleSizer = wx.StaticBoxSizer(wx.StaticBox(depthScalePanel, -1, 'Depth range'), orient=wx.VERTICAL)

        unitsPanel = wx.Panel(depthScalePanel, -1)
        unitsSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.unitsPopup = wx.Choice(unitsPanel, -1, choices=('m','cm','mm'), size=(-1,24))
        self.unitsPopup.SetSelection(0)
        self.mainPanel.Bind(wx.EVT_CHOICE, self.OnChangeRulerUnits, self.unitsPopup)
        unitsSizer.Add(wx.StaticText(unitsPanel, -1, "Units"), flag=wx.ALIGN_CENTER_VERTICAL)
        unitsSizer.Add(self.unitsPopup, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 10)
        unitsPanel.SetSizer(unitsSizer)
        depthScaleSizer.Add(unitsPanel, 0, wx.BOTTOM, 10)

        depthRangePanel = wx.Panel(depthScalePanel, -1)
        depthRangeSizer = wx.BoxSizer(wx.HORIZONTAL)
        depthRangeSizer.Add(wx.StaticText(depthRangePanel, -1, "Display interval"), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10)
        self.depthRangeText = wx.TextCtrl(depthRangePanel, -1, "10", size=(55,-1))
        depthRangeSizer.Add(self.depthRangeText, 0, wx.LEFT, 5)
        depthRangeSizer.Add(wx.StaticText(depthRangePanel, -1, 'm'), 2, wx.LEFT | wx.ALIGN_CENTER_VERTICAL)

        depthRangePanel.SetSizer(depthRangeSizer)
        depthScaleSizer.Add(depthRangePanel, 0, wx.BOTTOM, 10)

        depthScaleApply = wx.Button(depthRangePanel, -1, "Apply")
        depthRangeSizer.Add(depthScaleApply, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 10)
        self.mainPanel.Bind(wx.EVT_BUTTON, self.OnDepthViewAdjust, depthScaleApply)

        depthZoomPanel = wx.Panel(depthScalePanel, -1)
        depthZoomSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.zoomInBtn = wx.Button(depthZoomPanel, -1, "Zoom in")
        self.mainPanel.Bind(wx.EVT_BUTTON, self.OnZoomIn, self.zoomInBtn)
        self.zoomOutBtn = wx.Button(depthZoomPanel, -1, "Zoom out")
        self.mainPanel.Bind(wx.EVT_BUTTON, self.OnZoomOut, self.zoomOutBtn)
        depthZoomSizer.Add(self.zoomInBtn, 1, wx.BOTTOM | wx.EXPAND, 5)
        depthZoomSizer.Add(self.zoomOutBtn, 1, wx.LEFT | wx.BOTTOM | wx.EXPAND, 5)
        depthZoomPanel.SetSizer(depthZoomSizer)
        depthScaleSizer.Add(depthZoomPanel, 0, wx.BOTTOM | wx.EXPAND, 10)

        # Keyboard up/down arrow shift distance
        kbsSizer = wx.BoxSizer(wx.HORIZONTAL)
        kbsSizer.Add(wx.StaticText(depthScalePanel, -1, "Up/down toggle"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.tie_shift = wx.TextCtrl(depthScalePanel, -1, "0.0", size=(50,-1))
        kbsSizer.Add(self.tie_shift)
        kbsSizer.Add(wx.StaticText(depthScalePanel, -1, "m"), 0, wx.ALIGN_CENTER_VERTICAL)

        kbsApply = wx.Button(depthScalePanel, -1, "Apply")
        kbsSizer.Add(kbsApply, 0, wx.LEFT, 12)
        self.mainPanel.Bind(wx.EVT_BUTTON, self.OnTieShiftScale, kbsApply)
        depthScaleSizer.Add(kbsSizer, 0)

        depthScalePanel.SetSizer(depthScaleSizer)
        vbox_top.Add(depthScalePanel, 0, wx.BOTTOM | wx.EXPAND, 10)

        ### Data range panel
        varScalePanel = wx.Panel(self.mainPanel, -1)
        varScaleSizer = wx.StaticBoxSizer(wx.StaticBox(varScalePanel, -1, 'Data range'), orient=wx.VERTICAL)

        self.variableChoice = wx.Choice(varScalePanel, -1, (0,0), (-1,-1))
        varScalePanel.Bind(wx.EVT_CHOICE, self.SetTYPE, self.variableChoice)

        varSizer = wx.BoxSizer(wx.HORIZONTAL)
        varSizer.Add(wx.StaticText(varScalePanel, -1, "Range for"))
        varSizer.Add(self.variableChoice, 1, wx.LEFT, 5)
        varScaleSizer.Add(varSizer, 0, wx.EXPAND | wx.BOTTOM, 10)

        varRangeSizer = wx.BoxSizer(wx.HORIZONTAL)
        minRangeSizer = wx.BoxSizer(wx.VERTICAL)
        minRangeSizer.Add(wx.StaticText(varScalePanel, -1, "min"))
        self.varMin = wx.TextCtrl(varScalePanel, -1, "0", size=(50,-1))
        minRangeSizer.Add(self.varMin)

        maxRangeSizer = wx.BoxSizer(wx.VERTICAL)
        maxRangeSizer.Add(wx.StaticText(varScalePanel, -1, "max"))
        self.varMax = wx.TextCtrl(varScalePanel, -1, "20", size=(50,-1))
        maxRangeSizer.Add(self.varMax)
        varRangeSizer.Add(minRangeSizer, 0, wx.RIGHT, 10)
        varRangeSizer.Add(maxRangeSizer, 0, wx.RIGHT, 10)

        varApply = wx.Button(varScalePanel, -1, "Apply Range")
        varRangeSizer.Add(varApply, 0, wx.ALIGN_BOTTOM | wx.BOTTOM, 10)
        self.mainPanel.Bind(wx.EVT_BUTTON, self.OnChangeMinMax, varApply)
        varScalePanel.SetSizer(varScaleSizer)

        varScaleSizer.Add(varRangeSizer, 0, wx.BOTTOM | wx.ALIGN_RIGHT, 15)

        self.showOutOfRangeData = wx.CheckBox(varScalePanel, -1, "Show data outside track")
        self.mainPanel.Bind(wx.EVT_CHECKBOX, self.OnShowOutOfRangeData, self.showOutOfRangeData)
        varScaleSizer.Add(self.showOutOfRangeData, 0, wx.BOTTOM, 10)

        # Plot Width Slider
        self.plotWidthSlider = wx.Slider(varScalePanel, -1, value=0, minValue=0, maxValue=100)
        self.mainPanel.Bind(wx.EVT_COMMAND_SCROLL, self.OnChangePlotWidth, self.plotWidthSlider)
        plotWidthSliderSizer = wx.BoxSizer(wx.HORIZONTAL)
        plotWidthSliderSizer.Add(wx.StaticText(varScalePanel, -1, "Track width"))
        plotWidthSliderSizer.Add(self.plotWidthSlider, 1, wx.EXPAND)
        varScaleSizer.Add(plotWidthSliderSizer, 0, wx.EXPAND | wx.BOTTOM, 10)

        # Image Width Slider
        self.imageWidthSlider = wx.Slider(varScalePanel, -1, value=0, minValue=0, maxValue=100)
        self.mainPanel.Bind(wx.EVT_COMMAND_SCROLL, self.OnChangeImageWidth, self.imageWidthSlider)
        imageWidthSliderSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.iwsLabel = wx.StaticText(varScalePanel, -1, "Image width")
        imageWidthSliderSizer.Add(self.iwsLabel)
        imageWidthSliderSizer.Add(self.imageWidthSlider, 1, wx.EXPAND)
        varScaleSizer.Add(imageWidthSliderSizer, 0, wx.EXPAND)

        vbox_top.Add(varScalePanel, 0, wx.EXPAND | wx.BOTTOM, 10)

        # TODO: staticboxsizer for image options?
        # Image Display Style - all (stretch/squeeze), middle third, preserve aspect ratio
        # imageStyleSizer = wx.BoxSizer(wx.HORIZONTAL)
        # self.imageStyleChoice = wx.Choice(self.mainPanel, -1, choices=["Full Width", "Middle Third", "Preserve Aspect Ratio"])
        # self.mainPanel.Bind(wx.EVT_CHOICE, self.OnChangeImageStyle, self.imageStyleChoice)
        # imageStyleSizer.Add(wx.StaticText(self.mainPanel, -1, "Image Style"))
        # imageStyleSizer.Add(self.imageStyleChoice)
        # vbox_top.Add(imageStyleSizer, 0, wx.BOTTOM, 10)

        ### Lines, arrows, appearance panel
        viewPanel = wx.Panel(self.mainPanel, -1)
        viewSizer = wx.StaticBoxSizer(wx.StaticBox(viewPanel, -1, "Lines, arrows, appearance"), orient=wx.VERTICAL)

        self.showPlotLines = wx.CheckBox(viewPanel, -1, 'Show lines between plot tracks')
        self.mainPanel.Bind(wx.EVT_CHECKBOX, self.OnShowLine, self.showPlotLines)
        self.showPlotLines.SetValue(True)
        self.showSectionDepths = wx.CheckBox(viewPanel, -1, "Show section boundaries and numbers")
        self.mainPanel.Bind(wx.EVT_CHECKBOX, self.OnShowSectionDepths, self.showSectionDepths)
        self.showAffineShiftInfo = wx.CheckBox(viewPanel, -1, "Show core shift direction and distance")
        self.mainPanel.Bind(wx.EVT_CHECKBOX, self.OnShowAffineShiftInfo, self.showAffineShiftInfo)

        tiesSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.showAffineTies = wx.CheckBox(viewPanel, -1, "Show core tie")
        self.mainPanel.Bind(wx.EVT_CHECKBOX, self.OnShowAffineTies, self.showAffineTies)
        self.affineTieStyle = wx.Choice(viewPanel, -1, choices=["arrows", "lines"])
        self.mainPanel.Bind(wx.EVT_CHOICE, self.OnAffineTieStyle, self.affineTieStyle)
        tiesSizer.Add(self.showAffineTies, 0, wx.ALIGN_CENTER_VERTICAL)
        tiesSizer.Add(self.affineTieStyle, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 2)

        self.showCoreInfo = wx.CheckBox(viewPanel, -1, "Show core info on mouseover")
        self.mainPanel.Bind(wx.EVT_CHECKBOX, self.OnShowCoreInfo, self.showCoreInfo)
        self.showDepthLine = wx.CheckBox(viewPanel, -1, "Show line at current depth")
        self.mainPanel.Bind(wx.EVT_CHECKBOX, self.OnShowDepthLine, self.showDepthLine)
        self.showAffineShiftStrips = wx.CheckBox(viewPanel, -1, "Show shift type color strips")
        self.mainPanel.Bind(wx.EVT_CHECKBOX, self.OnShowAffineShiftStrips, self.showAffineShiftStrips)
        self.showColorLegend = wx.CheckBox(viewPanel, -1, "Show shift type color legend")
        self.mainPanel.Bind(wx.EVT_CHECKBOX, self.OnShowColorLegend, self.showColorLegend)
        self.spliceHoleColors = wx.CheckBox(viewPanel, -1, "Splice interval colors by hole")
        self.mainPanel.Bind(wx.EVT_CHECKBOX, self.OnSpliceHoleColor, self.spliceHoleColors)

        viewSizer.Add(self.showAffineShiftInfo, 0, wx.BOTTOM, 5)
        viewSizer.Add(tiesSizer, 0, wx.BOTTOM, 5)
        viewSizer.Add(self.showSectionDepths, 0, wx.BOTTOM, 5)
        viewSizer.Add(self.showCoreInfo, 0, wx.BOTTOM, 5)
        viewSizer.Add(self.showPlotLines, 0, wx.BOTTOM, 5)
        viewSizer.Add(self.showDepthLine, 0, wx.BOTTOM, 5)
        viewSizer.Add(self.showAffineShiftStrips, 0, wx.BOTTOM, 5)
        viewSizer.Add(self.showColorLegend, 0, wx.BOTTOM, 5)
        viewSizer.Add(self.spliceHoleColors, 0, wx.BOTTOM, 10)

        # Color Set
        colorButton = wx.Button(viewPanel, -1, "Set colors...")
        self.mainPanel.Bind(wx.EVT_BUTTON, self.OnChangeColor, colorButton)
        viewSizer.Add(colorButton, 1, wx.EXPAND)

        viewPanel.SetSizer(viewSizer)
        vbox_top.Add(viewPanel, 0, wx.BOTTOM | wx.EXPAND, 10)

        self.mainPanel.SetSizer(vbox_top)

