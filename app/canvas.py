from __future__ import print_function
from __future__ import division
#_!/usr/bin/env python

## For Mac-OSX
#/usr/bin/env pythonw
from builtins import chr
from builtins import str
from builtins import range
from past.utils import old_div
from builtins import object
import platform
platform_name = platform.uname()

import re
import timeit
from enum import Enum

import wx 
import wx.lib.sheet as sheet
from wx.lib import plot, scrolledpanel

import numpy

from datetime import datetime
import random, sys, os, re, time, string, traceback

import py_correlator

from affine import TieShiftMethod
import frames
import splice
from layout import LayoutManager, ColumnType, ImageDatatypeStr
from utils import CoreMetadata, HoleMetadata, getHoleName, makeImageKey


# brg 4/9/2014: Why are we defining our own wxBufferedWindow when
# wx.BufferedWindow already exists (same interface 'n all) in wx?
# brg 6/30/2020: Don't see a wx.BufferedWindow, was I crazy?
class wxBufferedWindow(wx.Window):

    """

    A Buffered window class.

    To use it, subclass it and define a Draw(DC) method that takes a DC
    to draw to. In that method, put the code needed to draw the picture
    you want. The window will automatically be double buffered, and the
    screen will be automatically updated when a Paint event is received.

    When the drawing needs to change, you app needs to call the
    UpdateDrawing() method.

    """
    def __init__(self, parent, id,
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 style=wx.NO_FULL_REPAINT_ON_RESIZE):
        wx.Window.__init__(self, parent, id, pos, size, style)
        #wx.SplitterWindow.__init__(self, parent, id, pos, size, style)

        self.sideTabSize = 340 
        self.CLOSEFLAG = 0

        self.WindowUpdate = 0
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)

        # OnSize called to make sure the buffer is initialized.
        # This might result in OnSize getting called twice on some
        # platforms at initialization, but little harm done.
        self.OnSize(None)

    def Draw(self, dc):
        ## just here as a place holder.
        ## This method should be over-ridden when sub-classed
        pass

    def OnPaint(self, event):
        # brg 1/17/2022: Adjust canvas size to reflect resized main window if needed. Otherwise,
        # canvas doesn't always draw to the full available width, particularly on first launch
        # when the window size is adjusted before the data canvas is displayed.
        # This isn't an ideal way to fix this, but triggering wxBufferedWindow.OnSize()
        # from an EVT_SIZE in correlator.py throws errors about self._Buffer not existing.
        tup = self.GetClientSize()
        tabWidth = self.sideTabSize if self.CLOSEFLAG == 0 else 45
        if (self.Width + tabWidth, self.Height) != tup:
            self.OnSize(None)
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self._Buffer, 0, 0)

    def OnSize(self, event):
        # The Buffer init is done here, to make sure the buffer is always
        # the same size as the Window
        self.Width, self.Height = self.GetClientSize()
                
        if self.CLOSEFLAG == 1:
            self.Width = self.Width - 45 
        else:
            self.Width = self.Width - self.sideTabSize
        self.WindowUpdate = 1

        # Make new off screen bitmap: this bitmap will always have the
        # current drawing in it, so it can be used to save the image to
        # a file, or whatever.
        if self.Width > 0 and self.Height > 0:
            self._Buffer = wx.Bitmap(self.Width, self.Height)
            self.UpdateDrawing()

    def UpdateDrawing(self):
        """
        This would get called if the drawing needed to change, for whatever reason.

        The idea here is that the drawing is based on some data generated
        elsewhere in the system. IF that data changes, the drawing needs to
        be updated.

        """
        # update the buffer
        dc = wx.MemoryDC()
        dc.SelectObject(self._Buffer)
        
        self.Draw(dc)
        # update the screen
        wx.ClientDC(self).Blit(0, 0, self.Width, self.Height, dc, 0, 0)


class CompositeTie(object):
    def __init__(self, hole, core, screenX, screenY, fixed, depth):
        self.hole = hole # hole index in currently loaded set of holes
        self.core = core # core index in currently loaded set of holes
        self.screenX = screenX # tied hole's x-coord
        self.screenY = screenY # tie mouse click y-coord
        self.fixed = fixed # is tie movable?
        self.depth = depth # actual depth of tie

    def __repr__(self):
        return str((self.hole, self.core, self.screenX, self.screenY, self.fixed, self.depth))

class SpliceTie(object):
    def __init__(self, x, y, core, fixed, minData, depth, tie, constrained):
        self.x = x
        self.y = y
        self.core = core
        self.fixed = fixed
        self.minData = minData
        self.depth = depth
        self.tie = tie # index/number of tie (within SpliceTieData?)
        self.constrained = constrained

    def __repr__(self):
        return str((self.x, self.y, self.core, self.fixed, self.minData, self.depth,
                    self.tie, self.constrained))

def DefaultSpliceTie():
    return SpliceTie(-1, -1, -1, -1, -1, -1, -1, -1)

class CoreInfo(object):
    def __init__(self, core, leg, site, hole, holeCore, minData, maxData, minDepth, maxDepth,
                 stretch, type, quality, holeCount, coredata):
        self.core = core # core index in currently loaded set of holes
        self.leg = leg # parent hole leg
        self.site = site # parent hole site
        self.hole = hole # parent hole name
        self.holeCore = holeCore # core index in parent hole's data
        self.minData = minData
        self.maxData = maxData
        self.minDepth = minDepth
        self.maxDepth = maxDepth
        self.stretch = stretch # expansion/compression in this core, expressed as a %
        self.type = type # hole data type
        self.quality = quality # core quality
        self.holeCount = holeCount # hole's index in currently loaded set of holes
        self.coredata = coredata # list of core's (depth,data) pairs

    def __repr__(self):
        return str((self.core, self.leg, self.site, self.hole, self.holeCore, self.minData, self.maxData,
                    self.minDepth, self.maxDepth, self.stretch, self.type, self.quality, self.holeCount))
        
    def getName(self):
        return "{}-{}-{}-{} {} Range: {}-{}".format(self.site, self.leg, self.hole, self.holeCore, self.type, self.minDepth, self.maxDepth)
    
    def getHoleCoreStr(self):
        return "{}{}".format(self.hole, self.holeCore)


# Contains metadata about the core currently being dragged
class DragCoreData(object):
    def __init__(self, mouseX, origMouseY, deltaY=0):
        self.x = mouseX # x-offset of dragged core
        self.origMouseY = origMouseY # y-coordinate at start of drag action
        self.y = deltaY # y-offset of dragged core (offset of current mouse y from origMouseY)

    def update(self, curMouseX, curMouseY):
        self.x = curMouseX
        self.y = curMouseY - self.origMouseY


# Report changes in the number of affine tie points, at most
# two if fixed and movable ties have been created.
class AffineTiePointEventBroadcaster(object):
    def __init__(self):
        self.listeners = []

    # Listener l is a function with a single integer parameter
    # indicating the current affine tie point count.
    def addListener(self, l):
        if l not in self.listeners:
            self.listeners.append(l)

    def removeListener(self, l):
        if l in self.listeners:
            self.listeners.remove(l)

    def updateAffineTiePointCount(self, count):
        for l in self.listeners:
            l(count)


# HoleData definition:
# Each element of HoleData is a list containing a list (yes, redundant) containing elements
# describing all hole and core data for a single hole+type.
#
# The first element is a tuple of hole metadata:
# 0: site name
# 1: expedition/leg name
# 2: data type
# 3: top depth
# 4: bottom depth
# 5: minimum data value
# 6: maximum data value
# 7: hole name
# 8: number of cores in hole
# 
# Subsequent elements are tuples of each core's metadata + all depth/data pairs:
#    (core name (number as string), top, bottom, mindata, maxdata, affine offset, stretch, annotated type,
#     core quality, list of sections' top depths, list of core's depth/data tuples)
#
# Note: top and bottom don't seem to reflect the actual core top and bottom at all. In some cases the core's
# depths fall outside of this interval, so take it with a large grain of salt. May be (almost) unused.


# Correlator frequently uses tuples to aggregate data, particularly for drawing.
# While tuples are convenient, lack of element names can make them hard to
# understand. Descriptions of the most commonly used DrawData tuples follow.
#
# CoreArea
# Contains metadata about core plots that were drawn in the
# most recent DrawMainView() loop. CoreArea tuples have 3 elements:
# - associated CoreInfo object
# - wx.Rect with the bounds of the drawn core
# - hole index
#
# MouseInfo
# Contains metadata about mouse position and core if the mouse cursor is
# over a core. MouseInfo tuples have 5 elements:
# - core index
# - x-coord of mouse
# - y-coord of mouse
# - x-coord of the left of the HoleColumn's Plot column if mouse is currently
#   over it. Otherwise, x-coord of the left of the HoleColumn.
# - boolean indicating whether the mouse is currently over a Plot column
#
# MovableSkin
# Splice scrollbar thumb - bmp, x, y
#
# MovableInterface
# Splice vertical scrollbar? - bmp, x, y, mystery flag
# 
# Skin
# Composite vertical scrollbar thumb - bmp, x, y, mystery flag
# 
# Interface
# 
# HScroll
# Horizontal scrollbar thumb - bmp, x, y, mystery flag
# 
# CoreImage?
#
# DragCore - converted to class DragCoreData, see above
# CoreInfo - converted to class CoreInfo, see above
#
# Other things that are not easily understood...
# 
# self.range is a list of 'range' tuples, each corresponding to a loaded datatype.
# A range has six elements:
# 0: datatype name
# 1: minimum data value for type
# 2: maximum data value for type
# 3: scaling coefficient used to map the min-max range to a pixel width
# 4: smoothing: -1 = no smoothing is applied, 0, 1, 2 mean smoothing is applied
#    0 = draw only original (unsmoothed), 1 = draw only smoothed, 2 = draw both
# 5: 'continue flag' boolean: This is related to the "Continuous" item for each hole
# 	in the Data Manager. That could be toggled to "Discrete" via a context menu item
#	that has been removed. AFAICT, the only thing "Discrete" did was draw the plot
#	in gray instead of yellow...confusingly it did not draw the plot as discrete points.
#	At this point, safe to assume continue flag is always True i.e. "Continuous"
#	except for data from old versions of Correlator.

# Adding an enum for smoothing types in the hope that they'll
# actually be used someday! brg 9/28/2020
class SmoothingType(Enum):
    NoSmoothing = -1
    Unsmoothed = 0
    Smoothed = 1
    SmoothedAndUnsmoothed = 2

# Display styles for core imagery
class ImageDisplayStyle(Enum):
    FullWidth = 0
    MiddleThird = 1
    AspectRatio = 2


class DataCanvas(wxBufferedWindow):
    def __init__(self, parent, id= -1):
        ## Any data the Draw() function needs must be initialized before
        ## calling wxBufferedWindow.__init__, as it will call the Draw
        ## function.
        self.drawCount = 0

        stdFontSize = 9 if platform_name[0] == "Windows" else 12 # 12 point too large on Windows, just right on Mac
        self.stdFont = wx.Font(stdFontSize, wx.SWISS, wx.NORMAL, wx.BOLD)
        self.ageFont = wx.Font(9, wx.SWISS, wx.NORMAL, wx.BOLD) # used only for drawing label in age depth model points
        
        self.headerY = 5 # vertical position for first line of a header
        headerFontSize = 8 if platform_name[0] == "Windows" else 11
        self.headerFont = wx.Font(headerFontSize, wx.SWISS, wx.NORMAL, wx.BOLD) # used for info above each hole plot
        self.headerLineSpacing = 13
                    
        self.parent = parent
        self.DrawData = {}
        self.Highlight_Tie = -1
        self.SpliceTieFromFile = 0

        self.affineBroadcaster = AffineTiePointEventBroadcaster()

        # brgtodo 6/26/2014: ShiftTieList is populated with new composite shifts only,
        # but shift arrows still draw correctly without this, even for a new shift. Remove?
        self.ShiftTieList = []
        self.showAffineShiftInfo = True  # brgtodo 6/25/2014 grab state from checkbox in frames and dump this var
        self.showAffineTies = True
        self.showAffineTieArrows = True # if False, show lines
        self.showSectionDepths = True
        self.showCoreInfo = False # show hole, core, min/max, quality, stretch on mouseover - see DrawGraphInfo()
        self.showOutOfRangeData = False # if True, clip data plots to the width of the hole's plot area
        self.showAffineShiftStrips = True # show color strips to left of plot indicating affine shift type
        self.showColorLegend = True # draw color legend for affine shift strips
        self.showDepthLine = False # draw line at mouse depth; click to lock/unlock position
        self.depthLinePos = None
        self.showPlotOverlays = False # overlay all plots of the same datatype on the first hole in alphabetical order
        self.drawSpliceInHoleColors = True # draw splice intervals in the color of their core's parent hole
        
        # debug options
        self.showBounds = False
        self.showFPS = False
        
        self.LogTieList = []
        self.LogClue = True    # brgtodo ditto

        self.Floating = False
        self.hole_sagan = -1
        self.sagan_type = ""
        self.fg = wx.Colour(255, 255, 255)
        # 1 = Composite, 2 = Splice, 3 = Sagan
        self.mode = 1 
        self.statusStr = ""
        self.ShowSplice = True
        self.currentHole = -1
        self.showMenu = False
        self.showGrid = False
        self.showHoleGrid = True
        self.ShowStrat = True
        self.ShowLog = False 
        self.WidthsControl = []
        self.HoleColumns = [] # list of HoleColumn objects to potentially draw
        self.minScrollRange = 0
        self.minSpliceScrollRange = 0
        self.smooth_id = 0
        self.selectedType = ""
        self.ScrollSize = 15
        self.AgeSpliceHole = True
        self.maxAgeRange = 8.0 
        # range_start, range_stop, rate, offset
        self.PreviewLog = [-1, -1, 1.0, 0, -1, -1, 1.0]
        self.PreviewOffset = 0
        self.PreviewB = 0
        self.PreviewBOffset = 0
        self.PreviewNumTies = 0
        self.PreviewFirstNo = 0
        self.prevNoteId = -1
        self.DiscretePlotMode = 0 
        self.DiscreteSize = 1 
        self.altType = ""
        self.altMultipleType = False

        # 0 , 1 - Composite, 2 - Splice
        self.Process = 0 
        self.Constrained = 1 
        self.independentScroll = False # scroll composite and splice windows separately
        self.ScrollUpdate = 0
        self.isLogMode = 0 
        self.closeFlag = True 
        #self.note_id = 0
        self.LogAutoMode = 1
        self.isAppend = False 
        self.SPSelectedCore = -1 
        self.mbsfDepthPlot = 0 
        self.firstPntAge = 0.0
        self.firstPntDepth = 0.0
        self.SelectedAge = -1
        self.AgeDataList = []
        self.AgeYRates = []
        self.AgeEnableDrag = 0
        self.AgeShiftX = 0
        self.AgeShiftY = 0
        self.AgeUnit = 0.1
        self.AgeOffset = 0.0
        self.AdjustAgeDepth = 0.0
        self.prevDepth = 0.0
        self.AgeSpliceGap = 2.0
        self.lastLogTie = -1 
        self.LDselectedTie = -1
        self.SaganDots = []
        self.ShowAutoPanel = False
        self.ELDapplied = False 
        self.MousePos = None # tuple (x,y) TODO? change to wx.Point?
        self.LastMousePos = None

        # Use dictionary so we can name colors - also need a list of names since dictionary is unordered
        
        self.colorDictKeys = ['background', 'foreground', 'imageOverlay',  'mbsf', \
            'ccsfTie', 'ccsfSet', 'ccsfRel', 'corrWindow', 'splice', 'spliceSel', 'spliceTrace', 'holeA', 'holeB', \
            'holeC', 'holeD', 'holeE', 'holeF', 'smoothA', 'smoothB', 'smoothC', \
            'smoothD', 'smoothE', 'smoothF']
        self.colorDict = {'background':wx.Colour(0,0,0), 'foreground':wx.Colour(255,255,255), 'imageOverlay':wx.Colour(238,238,0), \
            'mbsf':wx.Colour(238,238,0), 'ccsfTie':wx.Colour(0,139,0), 'ccsfSet':wx.Colour(0,102,255), 'ccsfRel':wx.Colour(255,153,0), \
            'corrWindow':wx.Colour(178,34,34), 'splice':wx.Colour(30,144,255), 'spliceSel':wx.GREEN, 'spliceTrace':wx.Colour(178,34,34), \
            'holeA':wx.Colour(234,153,153), 'holeB':wx.Colour(128,215,168), 'holeC':wx.Colour(158,196,247), 'holeD':wx.Colour(255,229,153), \
            'holeE':wx.Colour(213,166,189), 'holeF':wx.Colour(180,167,214), 'smoothA':wx.Colour(206,40,36), 'smoothB':wx.Colour(0,158,15), \
            'smoothC':wx.Colour(43,120,228), 'smoothD':wx.Colour(255,157,11), 'smoothE':wx.Colour(255,0,255), 'smoothF':wx.Colour(153,0,255)
        }
        self.defaultColorDict = dict(self.colorDict)
        assert len(self.colorDictKeys) == len(self.colorDict)

        self.compositeX = 35 # start of plotting area (first 35px are ruler)
        self.splicerX = 695 # start of splice plotting area (after ruler)
        self.splicerBackX = 695
        self.tieline_width = 2

        # obsolete vars, but with refs in obsolete code, leaving to be
        # removed in a dedicated obsolete code cleanup
        self.holeWidth = 300
        self.spliceHoleWidth = 300
        self.logHoleWidth = 210
        
        self.coreImageStyle = ImageDisplayStyle.FullWidth
        self.coreImageResolution = 3003 # pixels per meter TODO: Hard-coded for test image set

        self.Height = 0 # pixel height of client area
        self.Width = 0 # pixel width of client area

        # y-coordinate where the first depth ruler tick is drawn.
        # this value - 20 is the top of the plot area i.e. the bottom of hole headers
        self.startDepthPix = 60

        self.rulerHeight = 0 
        self.rulerStartDepth = 0.0 
        self.rulerEndDepth = 0.0
        self.rulerTickRate = 0.0 
        self.rulerUnits = 'cm' # one of 'm','cm','mm'
        self.tieDotSize = 10 

        self.ageXGap = 1.0
        self.ageLength = 90.0
        self.startAgeDepth = 60.0
        self.rulerStartAgeDepth = 0.0 
        self.rulerEndAgeDepth = 0.0
        self.ageRulerTickRate = 0.0 

        self.coefRange = 0.0
        self.coefRangeSplice = 0.0
        self.datascale = 0
        self.bothscale = 0
        self.isLogShifted = False
        #self.lastSpliceX = -1
        #self.lastSpliceY = -1

        self.decimateEnable = 0
        self.smoothEnable = 0
        self.cullEnable = 0
        self.autocoreNo = [] 

        # type, min, max, coef, smooth_mode, continous_type[True/False]
        self.range = [] 
        self.continue_flag = True 
        self.timeseries_flag = False 

        self.minRange = -1
        self.minAgeRange = 0.0 
        self.minRangeSplice = -1
        self.maxRange = -1
        self.SPrulerHeight = 0 
        self.SPrulerStartDepth = 0.0 
        self.SPrulerEndDepth = 0.0 
        self.SPrulerStartAgeDepth = 0.0 

        # current resolution, as computed by
        # (self.Height - self.rulerStartPix) / [length of visible interval in Display Prefs edit fields]
        self.pixPerMeter = 60

        # brg 6/11/2020 self._gap is the physical distance between labeled ticks on a ruler.
        # Dividing by its corresponding length (number of pixels in the gap) yields
        # pixels per meter. Somehow these two vars became the basis of all scaling in
        # the composite area ie any translation between pixels and depth required a
        # length/gap factor in the computation. This was bonkers and has been
        # removed for composite drawing. If age f'nality is ever resurrected, that behavior
        # should be fixed for ageGap/ageYLength as well!
        self._gap = 2 # obsolete - leaving around for Age drawing that depends on it
        self.ageGap = 10 
        self.ageYLength = 60
        self.spliceYLength = 60

        self.HoleCount = 0
        self.selectScroll = 0
        self.dragCore = -1
        self.SPgrabCore = -1
        self.spliceTie = -1
        self.lastSiTie = None # track last-selected SpliceInterval tie
        self.logTie = -1
        self.splice_smooth_flag = 0 

        self.squishValue = 100
        self.squishCoreId = -1 

        # Each element of HoleData is a list containing a list (yes, redundant) containing elements
        # describing all hole and core data for a single hole+type.
        #
        # The first element is a tuple of hole metadata:
        #    (site, leg, data type, hole's min depth, hole's max depth,
        #     hole's mindata, hole's maxdata, hole name, number of cores in hole)
        # 
        # Subsequent elements are tuples of each core's metadata + all depth/data pairs:
        #    (core name (number as string), top, bottom, mindata, maxdata, affine offset, stretch, annotated type,
        #     core quality, list of sections' top depths, list of core's depth/data tuples)
        #
        # Note: top and bottom don't seem to reflect the actual core top and bottom at all. In some cases the core's
        # depths fall outside of this interval, so take it with a large grain of salt. May be (almost) unused.
        self.HoleData = []

        self.SectionData = []
        self.SmoothData = [] 
        self.TieData = [] # composite ties
        self.StratData = []
        self.UserdefStratData = []
        self.GuideCore = []
        self.GuideCoreDatatype = None
        self.SpliceSmoothData = []
        self.Images = {}
        self.HolesWithImages = []

        self.layoutManager = LayoutManager()

        self.LogData = [] 
        self.LogSMData = [] 

        self.FirstDepth = -999.99
        self.SpliceCoreId = -1 
        self.SpliceTieData = [] # splice tie
        self.RealSpliceTie = []	 # splice tie
        self.SPGuideCore = []	# splice guide 
        self.SpliceCore = []	 # indexes of cores in splice
        self.SpliceData = []
        self.AltSpliceData = []
        self.LogSpliceData = []
        self.LogSpliceSmoothData = []
        self.LogTieData = [] # splice tie
        self.CurrentSpliceCore = -1 # index of core to be spliced onto splice

        self.drag = 0
        
        # brg 3/12/2022: index of core mouse cursor is currently over, but also
        # used when affine TIE fixed/shift lines are active. Commenting
        # out the three lines where this var is set in affine logic seemed to have
        # no detrimental effects, but it's way too late in the 4.0 cycle to tinker
        # with the affine interface and risk introducing bugs. The relevant affine logic
        # lines are commented with 'SelectedCoreAffine?'. TODO: Revisit post-4.0.
        self.mouseoverCore = -1

        # When a core is selected, it's drawn with a distinct background for easy
        # visual identification. Purely visual, no additional function.
        # Set to the tuple (hole name str, core name str).
        self.selectedCore = None

        self.LogselectedCore = -1 
        # brgtodo do we need both selectedTie and activeTie? 
        self.selectedTie = -1 
        self.activeTie = -1
        self.activeSPTie = -1 
        self.activeSATie = -1 
        self.activeCore = -1 
        self.shift_range = 0.1 

        self.compositeDepth = -1
        self.spliceDepth = -1
        self.saganDepth = -1
        self.selectedLastTie = -1 
        self.SPselectedTie = -1 
        self.SPselectedLastTie = -1 
        self.LogselectedTie = -1 
        self.mouseX = 0 
        self.mouseY = 0 
        self.newHoleX = 30.0
        self.guideCore = -1
        self.guideSPCore = -1
        self.minData = -1
        self.coreCount = 0 
        self.pressedkeyShift = 0
        self.pressedkeyS = 0
        self.pressedkeyD = 0
        self.selectedHoleType = "" 
        self.selectedStartX = 0 
        self.selectedCount = 0
        self.hideTie = 0
        self.currentStartX = 0
        self.grabScrollA = 0 
        self.grabScrollB = 0 
        self.dragCompositeScroll = False
        self.dragSpliceScroll = False
        self.Lock = False
        self.draw_count = 0

        self.spliceWindowOn = 1
        wxBufferedWindow.__init__(self, parent, id)

        self.sidePanel = wx.Panel(self, -1)
        self.sidePanel.SetBackgroundColour(wx.Colour(255, 255, 255))

        self.sideNote = wx.Notebook(self.sidePanel, -1, style=wx.NB_RIGHT | wx.NB_MULTILINE)
        self.sideNote.SetBackgroundColour(wx.Colour(255, 255, 255))

        # Sep 3 2024: Without a sizer for the parent Panel, Notebook tabs are
        # partially cut off on the right side on Macs in wxPython 4.
        sidePanelSizer = wx.BoxSizer()
        self.sidePanel.SetSizer(sidePanelSizer)
        sidePanelSizer.Add(self.sideNote, 0, wx.EXPAND)

        self.closePanel = wx.Panel(self.sideNote, -1, (0, 50), (45, 500), style=wx.NO_BORDER)

        self.compPanel = wx.Panel(self.sideNote, -1, (0, 50), (300, 500), style=wx.NO_BORDER)
        self.parent.compositePanel = frames.CompositePanel(self.parent, self.compPanel)
        self.compPanel.Hide()

        self.splicePanel = wx.Panel(self.sideNote, -1, (0, 50), (300, 500), style=wx.NO_BORDER)
        self.parent.splicePanel = frames.SplicePanel(self.parent, self.splicePanel)
        self.splicePanel.Hide()
        
        self.spliceIntervalPanel = wx.Panel(self.sideNote, -1, (0, 50), (300, 500), style=wx.NO_BORDER)
        self.parent.spliceIntervalPanel = frames.SpliceIntervalPanel(self.parent, self.spliceIntervalPanel)
        self.spliceIntervalPanel.Hide()

        start_pos = 50
        if platform_name[0] == "Windows":
            start_pos = 0

        self.eldPanel = wx.Panel(self.sideNote, -1, (0, start_pos), (300, 500), style=wx.NO_BORDER)
        self.eldPanel.SetBackgroundColour(wx.Colour(255, 255, 255))

        self.subSideNote = wx.Notebook(self.eldPanel, -1, style=wx.NB_TOP | wx.NB_MULTILINE)
        self.subSideNote.SetBackgroundColour(wx.Colour(255, 255, 255))

        self.manualPanel = wx.Panel(self.subSideNote, -1, (0, 50), (300, 500), style=wx.NO_BORDER)
        self.parent.eldPanel = frames.ELDPanel(self.parent, self.manualPanel)
        self.manualPanel.Hide()

        self.autoPanel = wx.Panel(self.subSideNote, -1, (0, 50), (300, 500), style=wx.NO_BORDER)
        self.parent.autoPanel = frames.AutoPanel(self.parent, self.autoPanel)
        self.autoPanel.Hide()

        self.subSideNote.AddPage(self.autoPanel, 'Auto Correlation')
        self.subSideNote.AddPage(self.manualPanel, 'Manual Correlation')
        self.subSideNote.SetSelection(0)
        self.subSideNote.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnSelectELDNote)

        self.filterPanel = wx.Panel(self.sideNote, -1, (0, 50), (300, 500), style=wx.NO_BORDER)
        self.parent.filterPanel = frames.FilterPanel(self.parent, self.filterPanel)
        self.filterPanel.Hide()

        self.optPanel = scrolledpanel.ScrolledPanel(self.sideNote, -1, (0, 50), (300, 500), style=wx.NO_BORDER | wx.VSCROLL)
        self.optPanel.SetupScrolling()
        self.parent.optPanel = frames.PreferencesPanel(self.parent, self.optPanel)
        self.optPanel.Hide()

        #self.helpPanel = wx.Panel(self.sideNote, -1, (0, 50), (300, 500), style=wx.NO_BORDER )

        #self.logPanel = wx.Panel(self.sideNote, -1, (0, 50), (300, 500), style=wx.NO_BORDER)

        self.agePanel = wx.Panel(self.sideNote, -1, (0, 50), (300, 500), style=wx.NO_BORDER)
        self.parent.agePanel = frames.AgeDepthPanel(self.parent, self.agePanel)
        #self.agePanel.Enable(False)

        #help = "About Correlator ...\n "
        #self.helpText = wx.TextCtrl(self.helpPanel, -1, help, (0, 0), (300, 500), style=wx.TE_MULTILINE|wx.TE_READONLY|wx.VSCROLL|wx.TE_AUTO_URL|wx.TE_WORDWRAP)
        #self.helpText.SetEditable(False)

        #report = "Report ..."
        #self.reportText = wx.TextCtrl(self.logPanel, -1, report, (0, 0), (300, 500), style=wx.TE_MULTILINE | wx.SUNKEN_BORDER | wx.ALWAYS_SHOW_SB )
        #self.reportText.SetEditable(False)

        self.sideNote.AddPage(self.closePanel, 'Close')
        self.sideNote.AddPage(self.compPanel, 'Shift Cores')
        #self.sideNote.AddPage(self.splicePanel, 'Splice')
        self.sideNote.AddPage(self.spliceIntervalPanel, "Splice Cores")
        # self.sideNote.AddPage(self.eldPanel, 'Core-Log Integration')
        #self.sideNote.AddPage(self.eldPanel, 'Correlation')

        #self.sideNote.AddPage(self.autoPanel, 'Auto Correlation')
        # self.sideNote.AddPage(self.agePanel, 'Age Depth Model')

        self.sideNote.AddPage(self.filterPanel, 'Data Filters')
        self.sideNote.AddPage(self.optPanel, 'Display Preferences')
        #self.sideNote.AddPage(self.logPanel, 'Report')

        #self.sideNote.AddPage(self.helpPanel, 'Help')
        
        self.sideNote.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnSelectNote)
        self.sideNote.SetSelection(1)
        
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLMouse)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleLeftClick)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRMouse)
        self.Bind(wx.EVT_LEFT_UP, self.OnMouseUp)
        self.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel)

        self.Bind(wx.EVT_KEY_DOWN, self.OnChar)
        self.sidePanel.Bind(wx.EVT_KEY_DOWN, self.OnChar)
        self.Bind(wx.EVT_KEY_UP, self.OnCharUp)
        self.sidePanel.Bind(wx.EVT_KEY_UP, self.OnCharUp)

    # 5/9/2014 brgtodo: Duplication in this routine and __init__ above
    def OnInit(self):
        self.GuideCore = []
        self.Highlight_Tie = -1
        self.saganDepth = -1
        self.ShiftTieList = []
        self.minScrollRange = 0
        self.minSpliceScrollRange = 0
        self.selectedHoleType = "" 
        self.selectedStartX = 0 
        self.selectedCount = 0
        self.SpliceTieFromFile = 0
        self.hole_sagan = -1 
        self.sagan_type = "" 
        self.LogTieList = []
        self.PreviewLog = [-1, -1, 1.0, 0, -1, -1, 1.0]
        self.showMenu = False
        self.splice_smooth_flag = 0
        self.autocoreNo = []
        self.HoleData = []
        self.SmoothData = []
        self.LogData = []
        self.LogSMData = []
        self.LogselectedTie = -1
        self.LDselectedTie = -1
        self.LogTieData = [] 
        self.SpliceData = []
        self.SpliceSmoothData = []
        self.Images = {} # todo? imageDB?
        self.imageCullPct = None # if images are culled, a float with cull percentage e.g. 22.5
        self.HolesWithImages = []
        self.LogSpliceData = []
        self.LogSpliceSmoothData = []
        self.firstPntAge = 0.0
        self.firstPntDepth = 0.0
        self.isLogMode = 0 
        self.StratData = []
        self.noOfHoles = 0
        self.logTie = -1
        self.SpliceTieData = []
        self.RealSpliceTie = []
        self.TieData = []
        self.SpliceCore = []
        self.UserdefStratData = []
        self.CurrentSpliceCore = -1
        self.mouseoverCore = -1
        self.LogselectedCore = -1
        self.selectedTie = -1
        self.selectedLastTie = -1
        self.guideCore = -1 # index of core on which to draw affine guide core...not the guide core itself!
        self.guideSPCore = -1
        self.selectedType = "" 
        self.multipleType = False 
        self.activeTie = -1 
        self.activeSPTie = -1 
        self.activeSATie = -1 
        self.activeCore = -1 


    def OnInit_SPLICE(self):
        self.altType = self.selectedType
        self.SpliceData = []
        self.SpliceSmoothData = []
        self.SpliceTieData = []
        self.RealSpliceTie = []
        self.SpliceCore = []
        self.CurrentSpliceCore = -1
        self.selectedTie = -1
        self.selectedLastTie = -1
        self.guideSPCore = -1
        self.selectedType = "" 
        self.altMultipleType = self.multipleType
        self.multipleType = False 
        self.SPgrabCore = -1
        self.spliceTie = -1
        self.SpliceCoreId = -1
        self.SPGuideCore = []
        self.SPselectedTie = -1
        self.SPselectedLastTie = -1
        self.splice_smooth_flag = 0

    def UpdateRANGE(self, type, min, max):
        for r in self.range:
            if r[0] == type:
                coef = max - min
                newrange = type, min, max, coef, r[4], r[5]
                self.range.remove(r)
                self.range.append(newrange)
                break


    def UpdateSMOOTH(self, type, smooth):
        for r in self.range:
            if r[0] == type:
                newrange = type, r[1], r[2], r[3], smooth, r[5] 
                self.range.remove(r)
                self.range.append(newrange)
                break

        if self.hole_sagan != -1 and type == self.sagan_type:
            for r in self.range:
                if r[0] == "splice":
                    newrange = r[0], r[1], r[2], r[3], smooth, r[5] 
                    self.range.remove(r)
                    self.range.append(newrange)
                    break

    def UpdateDATATYPE(self, type, continue_flag):
        for r in self.range:
            if r[0] == type:
                newrange = type, r[1], r[2], r[3], r[4], continue_flag 
                self.range.remove(r)
                self.range.append(newrange)
                break


    def _updateImageWidth(self):
        if self.coreImageStyle in [ImageDisplayStyle.FullWidth, ImageDisplayStyle.MiddleThird]:
            # restore old image width
            self.parent.optPanel.OnChangeImageWidth(None)
        elif self.coreImageStyle == ImageDisplayStyle.AspectRatio: # overrides layoutManager.imageWidth to maintain aspect ratio
            if len(self.Images) == 0:
                return
            img, _ = self.Images[list(self.Images.keys())[0]]
            h_px = img.GetHeight()
            h_phys = h_px / float(self.coreImageResolution)
            draw_height_px = h_phys * self.pixPerMeter
            scale = float(draw_height_px) / h_px
            self.layoutManager.imageWidth = int(round(img.GetWidth() * scale))
            # print("Image is {}px high = {}m at {}px/m; width {} scales to {}".format(h_px, h_phys, self.coreImageResolution, img.GetWidth(), self.layoutManager.imageWidth))

    def InvalidateImages(self):
        invalidatedImages = {}
        for k, v in list(self.Images.items()):
            invalidatedImages[k] = (v[0], None)
        self.Images = invalidatedImages
        self._updateImageWidth()

    def LoadImages(self, img_files):
        self.HolesWithImages = []
        for f in img_files:
            img = wx.Image(f)
            img_key = makeImageKey(os.path.basename(f))
            self.Images[img_key] = (img, None) # wx.Image, wx.Bitmap
            hole_name = getHoleName(img_key)
            assert hole_name is not None
            if hole_name not in self.HolesWithImages:
                self.HolesWithImages.append(hole_name)
        # print("Loaded images: {}".format(self.Images))
        # print("Holes with images: {}".format(self.HolesWithImages))

    def CountImages(self):
        return len(self.Images)

    def GetImageBitmap(self, sectionName, displayHeight):
        if sectionName not in self.Images:
            return None
        img, bmp = self.Images[sectionName]
        if bmp is None: # recreate bitmap if it was invalidated
            if self.imageCullPct is not None:
                cull_wid = img.GetWidth() * (self.imageCullPct / 100.0) # total pixels to cull
                vis_wid = img.GetWidth() - cull_wid # resulting image width
                culled_img_rect = wx.Rect(cull_wid/2.0, 0, vis_wid, img.GetHeight())
                bmp = img.GetSubImage(culled_img_rect).Scale(self.layoutManager.imageWidth, displayHeight).ConvertToBitmap()
            else:
                bmp = img.Scale(self.layoutManager.imageWidth, displayHeight).ConvertToBitmap()
            self.Images[sectionName] = (img, bmp)
        return bmp

    # Used only for core images in the splice area, which still draws using
    # old crude approach (vs. the core/composite area, which uses the layout.py
    # module logic to draw) and thus needs to explicitly ask self.layoutManager
    # whether images are visible at all.
    def GetSpliceAreaImageWidth(self):
        if (len(self.HolesWithImages) > 0 and self.layoutManager.getShowImages()):
            return self.layoutManager.imageWidth
        return 0

    # hole: hole name string
    def HoleHasImages(self, hole):
        return hole in self.HolesWithImages
        
    # CoreInfo finding routines
    def findCoreInfoByIndex(self, coreIndex):
        result = None
        for ci in self.DrawData["CoreInfo"]:
            if ci.core == coreIndex:
                result = ci
                break
        if result == None:
            print("Can't find matching coreinfo for index " + str(coreIndex))
        return result

    def findCoreInfoByHoleCore(self, hole, core):
        result = None
        for ci in self.DrawData["CoreInfo"]:
            if ci.hole == hole and ci.holeCore == core:
                result = ci
                break
        if result == None:
            print("Can't find matching coreinfo for hole " + str(hole) + ", core (hole index) " + str(core))
        return result

    def findCoreInfoByHoleCoreType(self, hole, core, datatype):
        if datatype == "NaturalGamma":
            datatype = "Natural Gamma"
        result = None
        for ci in self.DrawData["CoreInfo"]:
            #print "DrawData = {}".format(ci)
            if ci.hole == hole and ci.holeCore == core and ci.type == datatype:
                result = ci
                break
        if result == None:
            print("Can't find matching coreinfo for hole " + str(hole) + ", core (hole index) " + str(core) + ", type " + str(datatype))
        return result

    def findCoreInfoByHoleCount(self, holeCount):
        result = None
        for ci in self.DrawData["CoreInfo"]:
            if ci.holeCount == holeCount:
                result = ci
                break
        if result == None:
            print("Can't find matching coreinfo for holeCount " + str(holeCount))
        return result
    
    def getCorePointData(self, hole, core, datatype, forceUnsmooth=False):
        smoothType = self.GetSmoothType(datatype)
        searchData = self.SmoothData if (smoothType > 0 and not forceUnsmooth) else self.HoleData
        return self._findCorePointData(searchData, hole, core, datatype)
    
    # find and return (depth, data) tuples for specified hole/core/datatype
    # from self.HoleData or self.SmoothData
    def _findCorePointData(self, holedata, hole, core, datatype):
        result = []
        for h in holedata:
            curhole = h[0]
            if curhole[0][7] == hole and curhole[0][2] == datatype:
                for curcore in curhole[1:]:
                    if curcore[0] == core:
                        result = curcore[10]
                        break
        return result
    
    def findCoreAffineOffset(self, hole, core):
        result = None
        for h in self.HoleData:
            curhole = h[0] # needless list
            #print "curhole = {}".format(curhole)
            if curhole[0][7] == hole:
                for c in curhole[1:]:
                    #print "c = {}".format(c)
                    if c[0] == core:
                        result = c[5] # affine offset
        return result
    
    # Create a CoreInfo object from the matching self.HoleData element.
    # Used in cases where self.DrawData["CoreInfo"] is empty and thus
    # findCoreInfoByHoleCoreType() will return None.
    def createCoreInfoForHoleCoreType(self, hole, core, datatype):
        result = None
        for h in self.HoleData:
            curHole = h[0] # needless list
            if curHole[0][7] == hole and curHole[0][2] == datatype:
                for curCore in curHole[1:]:
                    if curCore[0] == core:
                        result = CoreInfo(0, curHole[0][0], curHole[0][1], curHole[0][7], curCore[0], curCore[3], curCore[4], curCore[10][0][0], curCore[10][-1][0], curCore[6], datatype, curCore[8], 0, curCore[10])
                        break
        if result == None:
            print("V2: Can't find matching CoreInfo for hole " + str(hole) + ", core (hole index) " + str(core))
        return result

    # Given DataCanvas.HoleData list, return dict with elements of form
    # key: datatype (string)
    # value: list of hole names (strings) with that datatype
    def getDatatypeHoleDict(self):
        holeMetadataList = [HoleMetadata(hd) for hd in self.HoleData]
        typeHolePairs = [(hmd.datatype(), hmd.holeName()) for hmd in holeMetadataList]
        typeHolePairs += [(ImageDatatypeStr, h) for h in self.HolesWithImages]
        dhDict = {}
        for dt in list(set([datatype for datatype, _ in typeHolePairs])):
            holeNames = sorted([name for datatype, name in typeHolePairs if datatype == dt])
            dhDict[dt] = holeNames
        return dhDict

    # return sorted list of currently-loaded hole names
    def getLoadedHoles(self):
        return sorted(list(set([HoleMetadata(hd).holeName() for hd in self.HoleData])))

    # convert y coordinate to depth - for composite area
    def getDepth(self, ycoord):
        return old_div((ycoord - self.startDepthPix), self.pixPerMeter) + self.rulerStartDepth

    # convert depth to y coordinate - for composite area
    def getCoord(self, depth):
        return self.startDepthPix + (depth - self.rulerStartDepth) * self.pixPerMeter
    
    # convert depth to y coordinate in splice area
    def getSpliceDepth(self, ycoord):
        return old_div((ycoord - self.startDepthPix), self.pixPerMeter) + self.SPrulerStartDepth
    
    # convert y-coordinate to depth in splice area
    def getSpliceCoord(self, depth):
        return self.startDepthPix + (depth - self.SPrulerStartDepth) * self.pixPerMeter

    def GetMINMAX(self, type):
        for r in self.range:
            if r[0] == type:
                return (r[1], r[2])
        return None
    
    def GetSmoothType(self, datatype):
        if datatype == "Natural Gamma":
            datatype = "NaturalGamma"
        smoothType = None
        for r in self.range:
            if r[0] == datatype:
                smoothType = r[4]
        return smoothType

    def GetRulerUnitsStr(self):
        return self.rulerUnits

    def GetRulerUnitsIndex(self):
        unitToIndexMap = {'m':0, 'cm':1, 'mm':2}
        return unitToIndexMap[self.rulerUnits]

    def GetRulerUnitsFactor(self):
        unitToFactorMap = {'m':1.0, 'cm':100.0, 'mm':1000.0}
        return unitToFactorMap[self.rulerUnits]

    # only affine for now
    def GetCompositeTieCount(self):
        return len(self.TieData)

    def OnSelectELDNote(self, event):
        note_id = event.GetSelection()
        if self.prevNoteId == note_id:
            self.prevNoteId = -1
            return

        self.manualPanel.Hide()
        self.autoPanel.Hide()

        if note_id == 0:
            self.mode = 3
            self.autoPanel.Show()
            self.parent.showSplicePanel = 0 
            self.parent.showCompositePanel = 0 
            self.parent.showELDPanel = 0 
        else:
            #if self.ShowAutoPanel == False:
            self.manualPanel.Show()
            self.parent.showELDPanel = 1
            self.mode = 3
            if self.spliceWindowOn == 0: 
                self.parent.OnActivateWindow(1)
            self.parent.showSplicePanel = 0 
            self.parent.showCompositePanel = 0 
            self.parent.eldPanel.OnUpdate()
        self.prevNoteId = note_id
        self.subSideNote.SetSelection(note_id)
        #event.Skip()

    def OnSelectNote(self, event):
        note_id = event.GetSelection()

        #self.closeFlag = False 
        #self.sideNote.SetSize((self.sideTabSize,self.Height))
        #self.sidePanel.SetSize((self.sideTabSize,self.Height))
        #x, y = self.GetCorrelatorWindowSize()
        #self.SetSashPosition(x - self.sideTabSize, False)

        self.compPanel.Hide()
        self.splicePanel.Hide()
        self.spliceIntervalPanel.Hide()
        self.eldPanel.Hide()
        self.filterPanel.Hide()
        self.agePanel.Hide()
        #self.autoPanel.Hide()
        self.optPanel.Hide()
        #self.logPanel.Hide()
        #self.helpPanel.Hide()

        originalWidth = self.Width
        if note_id == 0:
            if self.CLOSEFLAG == 0:
                self.parent.showCompositePanel = 0 
                self.parent.showSplicePanel = 0 
                self.parent.showELDPanel = 0 
                self.Width, self.Height = self.parent.GetCorrelatorWindowSize()
                self.Width = self.Width - 45 
                self.sideNote.SetSize((45, self.Height))
                self.sidePanel.SetPosition((self.Width, 0))
                self.sidePanel.SetSize((45, self.Height))
                self.UpdateDrawing()
                self.CLOSEFLAG = 1
                self._Buffer = wx.Bitmap(self.Width, self.Height)
                if self.spliceWindowOn == 0:
                    self.splicerX = self.Width + 45
                self.UpdateSpliceScrollThumb(self.splicerX, originalWidth)
                self.UpdateDrawing()
        else:
            if self.CLOSEFLAG == 1:
                self.Width, self.Height = self.parent.GetCorrelatorWindowSize()
                self.Width = self.Width - self.sideTabSize
                self.sidePanel.SetPosition((self.Width, 0))
                self.sidePanel.SetSize((self.sideTabSize, self.Height))
                self.sideNote.SetSize((self.sideTabSize, self.Height))
                self.CLOSEFLAG = 0 
                self._Buffer = wx.Bitmap(self.Width, self.Height)
                if self.spliceWindowOn == 0:
                    self.splicerX = self.Width + 45
                self.UpdateSpliceScrollThumb(self.splicerX, originalWidth)
                self.UpdateDrawing()

        if note_id == 1:
            self.compPanel.Show()
            self.parent.showCompositePanel = 1
            self.mode = 1
            #if self.spliceWindowOn == 1: 
            #	self.parent.OnActivateWindow(1)
            self.parent.showSplicePanel = 0 
            self.parent.showELDPanel = 0 
        elif note_id == 2:
            self.spliceIntervalPanel.Show()
            self.parent.showSplicePanel = 1
            self.parent.showCompositePanel = 0 
            self.parent.showELDPanel = 0
        # elif note_id == 3:
        # 	self.mode = 3
        # 	#if self.ShowAutoPanel == False:
        # 	self.eldPanel.Show()
        # 	self.parent.showELDPanel = 1
        # 	self.mode = 3
        # 	if self.spliceWindowOn == 0: 
        # 		self.parent.OnActivateWindow(1)
        # 	self.parent.showSplicePanel = 0 
        # 	self.parent.showCompositePanel = 0 

        # 	if self.parent.showELDPanel == 1:
        # 		self.parent.eldPanel.OnUpdate()

        # 	# -------- HJ
        # 	#self.mode = 3
        # 	#self.autoPanel.Show()
        # 	#self.parent.showSplicePanel = 0 
        # 	#self.parent.showCompositePanel = 0 
        # 	#self.parent.showELDPanel = 0 
        # 	# --------
        # elif note_id == 4:
        # 	self.mode = 4
        # 	self.agePanel.Show()
        # 	self.parent.showSplicePanel = 0 
        # 	self.parent.showCompositePanel = 0 
        # 	self.parent.showELDPanel = 0 
        elif note_id == 3:#5:
            self.filterPanel.Show()
            self.parent.showSplicePanel = 0 
            self.parent.showCompositePanel = 0 
            self.parent.showELDPanel = 0 
        elif note_id == 4:#6:
            self.optPanel.Show()
            #self.parent.optPanel.updateItem()
            self.parent.showSplicePanel = 0 
            self.parent.showCompositePanel = 0 
            self.parent.showELDPanel = 0

        event.Skip()

    def DrawAgeModelRuler(self, dc):
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.SetPen(wx.Pen(self.colorDict['foreground'], 1))
        dc.SetTextBackground(self.colorDict['background'])
        dc.SetTextForeground(self.colorDict['foreground'])
        dc.SetFont(self.stdFont)

        self.rulerHeight = self.Height - self.startAgeDepth

        # Draw ruler on age model space
        depth = self.startAgeDepth 
        pos = self.rulerStartAgeDepth 
        dc.DrawLines(((self.compositeX, 0), (self.compositeX, self.Height)))

        rulerUnitsStr = " (" + self.GetRulerUnitsStr() + ")"
        dc.DrawText("Depth", self.compositeX - 35, self.startAgeDepth - 45)
        dc.DrawText(rulerUnitsStr, self.compositeX - 35, self.startAgeDepth - 35)
        
        # Draw depth scale ticks
        rulerRange = (old_div(self.rulerHeight, (old_div(self.ageYLength, self.ageGap))))
        self.ageRulerTickRate = self.CalcTickRate(rulerRange)

        unitAdjFactor = self.GetRulerUnitsFactor()
        while True:
            adjPos = pos * unitAdjFactor
            dc.DrawLines(((self.compositeX - 10, depth), (self.compositeX, depth)))
            wid, hit = dc.GetTextExtent(str(adjPos))
            dc.DrawRotatedText(str(adjPos), self.compositeX - 5 - hit * 2, depth + old_div(wid,2), 90.0)
            depth = depth + (old_div(self.ageRulerTickRate * self.ageYLength, self.ageGap))
            dc.DrawLines(((self.compositeX - 5, depth), (self.compositeX, depth)))
            depth = depth + (old_div(self.ageRulerTickRate * self.ageYLength, self.ageGap)) 
            pos = pos + self.ageRulerTickRate * 2
            if depth > self.Height:
                break

        self.rulerEndAgeDepth = pos
        dc.DrawLines(((self.compositeX, self.startAgeDepth), (self.splicerX - 50, self.startAgeDepth)))
        dc.DrawText("Age(Ma)", self.compositeX + 5, self.startAgeDepth - 45)
        y1 = self.startDepthPix - 7
        y2 = self.startDepthPix
        y3 = self.startDepthPix - 20 
        pos = 1.0 
        #width = ((0.5 - self.minAgeRange) * self.ageLength) 
        x = self.compositeX + ((pos - self.minAgeRange) * self.ageLength)
        #x = self.compositeX + width 

        maxsize = self.splicerX - 50
        for i in range(self.maxAgeRange):
            if x > self.compositeX and x < maxsize:
                dc.DrawLines(((x, y1), (x, y2)))
                dc.DrawText(str(pos), x - 10, y3)
            pos = pos + self.ageXGap
            x = self.compositeX + ((pos - self.minAgeRange) * self.ageLength)

        # Draw ruler on splicer space
        if self.spliceWindowOn == 1:
            depth = self.startDepthPix 
            pos = self.SPrulerStartDepth 

            dc.DrawLines(((self.splicerX, 0), (self.splicerX, self.Height)))

            self.SPrulerHeight = self.Height - self.startDepthPix

            temppos = self.SPrulerStartDepth % (old_div(self._gap, 2))
            dc.DrawLines(((self.splicerX - 10, depth), (self.splicerX, depth)))
            if temppos > 0: 
                dc.DrawText(str(pos), self.splicerX - 35, depth - 5)

                # brg 6/11/2020 - not fixing since age f'n is disabled, but if you
                # have to work with this, change the two instances of "self.pixPerMeter / 2"
                # to "self.pixPerMeter" to get correct depths. self.pixPerMeter used to mean
                # "pixels per 2 meters" but now means "pixels per meter" as it should.
                depth = depth + (old_div(self.pixPerMeter, 2)) * (1 - temppos) 
                dc.DrawLines(((self.splicerX - 5, depth), (self.splicerX, depth)))
                depth = depth + old_div(self.pixPerMeter, 2) 
                pos = pos - temppos + self._gap

            dc.DrawText("Ma", self.splicerX - 35, 20)
            agedepth = 0.0 
            if self.SPrulerStartAgeDepth <= 0.0:
                dc.DrawText(str(agedepth), self.splicerX - 35, self.startAgeDepth - 5)
            count = 1
            agedepth = self.AgeUnit
            agey = count * self.AgeSpliceGap
            if self.spliceYLength > 40: # this will always be the case as spliceYLength is init'd to 60 and never changed.
                while True:
                    y = self.startAgeDepth + (agey - self.SPrulerStartAgeDepth) * (old_div(self.spliceYLength, self._gap))
                    dc.DrawLines(((self.splicerX - 10, y), (self.splicerX, y)))
                    dc.DrawText(str(agedepth), self.splicerX - 35, y - 5)
                    if y > self.Height: 
                        break
                    count = count + 1
                    agedepth = count * self.AgeUnit
                    agey = count * self.AgeSpliceGap
            elif self.spliceYLength > 20: # never hit, see above
                while True:
                    y = self.startAgeDepth + (agey - self.SPrulerStartAgeDepth) * (old_div(self.spliceYLength, self._gap))
                    if count % 2 == 0:
                        dc.DrawLines(((self.splicerX - 10, y), (self.splicerX, y)))
                        dc.DrawText(str(agedepth), self.splicerX - 35, y - 5)
                    else:
                        dc.DrawLines(((self.splicerX - 5, y), (self.splicerX, y)))

                    if y > self.Height: 
                        break
                    count = count + 1
                    agedepth = count * self.AgeUnit
                    agey = count * self.AgeSpliceGap
            else: # never hit, see above
                while True:
                    y = self.startAgeDepth + (agey - self.SPrulerStartAgeDepth) * (old_div(self.spliceYLength, self._gap))
                    if count % 5 == 0:
                        dc.DrawLines(((self.splicerX - 10, y), (self.splicerX, y)))
                        dc.DrawText(str(agedepth), self.splicerX - 35, y - 5)
                    else:
                        dc.DrawLines(((self.splicerX - 5, y), (self.splicerX, y)))

                    if y > self.Height: 
                        break
                    count = count + 1
                    agedepth = count * self.AgeUnit
                    agey = count * self.AgeSpliceGap

            depth = self.startAgeDepth - 20
            dc.DrawLines(((self.splicerX, depth), (self.Width, depth)))


    # Given rulerRange (in meters), return a suitable rate of depth scale tick marks (in meters).
    def CalcTickRate(self, rulerRange):
        result = 1.0
        exp = 5
        while True:
            bigTens = pow(10, exp)
            halfBigTens = bigTens / 2.0
            smallTens = pow(10, exp - 1)
            if rulerRange <= pow(10, exp) and rulerRange > pow(10, exp - 1):
                # found the proper range, now determine which of 10^exp, (10^exp)/2, 10^(exp-1)
                # it's nearest. That number/10 will be our tick rate.
                diffList = [bigTens - rulerRange, rulerRange - smallTens, abs(bigTens / 2.0 - rulerRange)]
                result = min(diffList)
                resultIndex = diffList.index(result)
                if resultIndex == 0:
                    result = bigTens / 10.0
                elif resultIndex == 1:
                    result = smallTens / 10.0
                elif resultIndex == 2:
                    result = halfBigTens / 10.0
                break
            exp = exp - 1
        
        return result

    def DrawRuler(self, dc):
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.SetPen(wx.Pen(self.colorDict['foreground'], 1))
        dc.SetTextBackground(self.colorDict['background'])
        dc.SetTextForeground(self.colorDict['foreground'])
        dc.SetFont(self.headerFont)

        rulerUnitsStr = " (" + self.GetRulerUnitsStr() + ")"
        if self.timeseries_flag == False:
            dc.DrawText("Depth", self.compositeX - 35, self.startDepthPix - 45)
            dc.DrawText(rulerUnitsStr, self.compositeX - 35, self.startDepthPix - 35)
        else:
            dc.DrawText("Age", self.compositeX - 35, self.startDepthPix - 45)
            dc.DrawText("(Ma)", self.compositeX - 35, self.startDepthPix - 35)

        # Draw ruler on composite space
        depth = self.startDepthPix # depth in pixels
        pos = self.rulerStartDepth # depth in meters for tick labels
        dc.DrawLines(((self.compositeX, 0), (self.compositeX, self.Height))) # depth axis

        # Draw depth scale ticks
        self.rulerHeight = self.Height - self.startDepthPix
        rulerRange = (old_div(self.rulerHeight, self.pixPerMeter))
        self.rulerTickRate = self.CalcTickRate(rulerRange) # shouldn't need to do this every draw!
        # print("rulerRange = {}, tickRate = {}".format(rulerRange, self.rulerTickRate))

        dc.SetFont(self.stdFont) # draw numbers in standard font

        unitAdjFactor = self.GetRulerUnitsFactor()
        while True:
            adjPos = round(pos * unitAdjFactor, 3) # pos in meters, adjust *100 if displaying cm, *1000 if mm

            dc.DrawLines(((self.compositeX - 10, depth), (self.compositeX, depth))) # depth-labeled ticks
            wid, hit = dc.GetTextExtent(str(adjPos))
            dc.DrawRotatedText(str(adjPos), self.compositeX - 5 - hit * 2, depth + old_div(wid,2), 90.0)
            depth = depth + (self.rulerTickRate * self.pixPerMeter)

            dc.DrawLines(((self.compositeX - 5, depth), (self.compositeX, depth))) # unlabeled ticks
            depth = depth + (self.rulerTickRate * self.pixPerMeter)

            pos = pos + self.rulerTickRate * 2 # jump to next labeled tick position
            if depth > self.Height:
                break

        self.rulerEndDepth = pos + 2.0
        self.parent.compositePanel.UpdateGrowthPlot() # shouldn't need to do this every draw!

        # Draw ruler on splicer space
        if self.spliceWindowOn == 1:
            depth = self.startDepthPix 
            pos = self.SPrulerStartDepth 

            if self.timeseries_flag == False:
                dc.DrawText("Depth", self.splicerX - 35, self.startDepthPix - 45)
                dc.DrawText(rulerUnitsStr, self.splicerX - 35, self.startDepthPix - 35)
            else:
                dc.DrawText("Age", self.splicerX - 35, self.startDepthPix - 45)
                dc.DrawText("(Ma)", self.splicerX - 35, self.startDepthPix - 35)

            dc.DrawLines(((self.splicerX, 0), (self.splicerX, self.Height))) # depth axis
            self.SPrulerHeight = self.Height - self.startDepthPix
            
            while True:
                adjPos = round(pos * unitAdjFactor, 3)
                dc.DrawLines(((self.splicerX - 10, depth), (self.splicerX, depth)))
                wid, hit = dc.GetTextExtent(str(adjPos))
                dc.DrawRotatedText(str(adjPos), self.splicerX - 5 - hit * 2, depth + old_div(wid,2), 90.0)
                depth = depth + (self.rulerTickRate * self.pixPerMeter)
                dc.DrawLines(((self.splicerX - 5, depth), (self.splicerX, depth)))
                depth = depth + (self.rulerTickRate * self.pixPerMeter)
                pos = pos + self.rulerTickRate * 2
                if depth > self.Height:
                    break

            self.SPrulerEndDepth = pos + 2.0 
            depth = self.startDepthPix - 20
            dc.DrawLines(((self.splicerX, depth), (self.Width, depth)))

        depth = self.startDepthPix - 20
        if self.spliceWindowOn == 1:
            dc.DrawLines(((self.compositeX, depth), (self.splicerX - 50, depth)))
        else:
            dc.DrawLines(((self.compositeX, depth), (self.Width, depth)))


    def DrawDebugBounds(self, dc, startX, rangeMax):
        # bounds of each hole's plot rectangle
        dc.SetPen(wx.Pen(wx.RED, 1))
        dc.DrawLine(startX, self.startDepthPix - 20, startX, self.Height) # left edge of hole plot
        dc.SetPen(wx.Pen(wx.GREEN, 1))
        dc.DrawLine(rangeMax, self.startDepthPix - 20, rangeMax, self.Height) # right edge of hole plot
        # right edge of next hole plot's info area (core number, affine shift type and distance)
        dc.SetPen(wx.Pen(wx.YELLOW, 1))
        dc.DrawLine(rangeMax + self.layoutManager.plotLeftMargin - 1, self.startDepthPix - 20, rangeMax + self.layoutManager.plotLeftMargin - 1, self.Height)
        dc.SetPen(wx.Pen(wx.BLUE, 1))
        dc.DrawLine(startX, self.startDepthPix - 20, rangeMax + self.layoutManager.plotLeftMargin, self.startDepthPix - 20) # top of hole plot
        dc.DrawLine(startX, self.Height, rangeMax + self.layoutManager.plotLeftMargin, self.Height) # bottom of hole plot...obscured by horz scrollbar

        # Draw some debugging lines indicating bounds of Composite Area
        dc.SetPen(wx.Pen(wx.RED))
        dc.DrawLines(((self.compositeX, 0), (self.compositeX, self.Height))) # depth axis - left edge of composite area
        # dc.SetPen(wx.Pen(wx.YELLOW, 3))
        # dc.DrawLines(((self.splicerX - 63, 0), (self.splicerX - 63, self.Height))) # right edge of composite area...splicerX - 60
        dc.SetPen(wx.Pen(wx.RED))
        dc.DrawLines(((self.compositeX, self.Height-self.ScrollSize), (self.Width, self.Height-self.ScrollSize))) # bottom of composite area (directly above horz scrollbar)
        dc.DrawLines(((self.splicerX, 0), (self.splicerX, self.Height))) # bottom of composite area (directly above horz scrollbar)
        dc.DrawLines(((self.Width - self.ScrollSize - 1, 0),(self.Width - self.ScrollSize - 1, self.Height))) # right edge of draw area, whether or not splice is enabled
        if self.spliceWindowOn == 1: # left edge of splice area (directly to right of scrollbar)
            dc.SetPen(wx.Pen(wx.RED, 1))
            dc.DrawLines(((self.splicerX - 59 + self.ScrollSize, 0),(self.splicerX - 59 + self.ScrollSize, self.Height)))

        dc.SetPen(wx.Pen(self.colorDict['foreground'], 1)) # restore pen

    # Draw hole info above image/plot area. Three lines: hole ID, hole datatype, and hole data range.
    # Uses self.headerFont, which is slightly smaller than self.stdFont to accommodate three lines
    # in available space.
    def DrawHoleHeader(self, dc, headerX, holeColumn, clipRegion):
        dc.SetFont(self.headerFont)
        clip = wx.DCClipper(dc, clipRegion)
        dc.DrawText(holeColumn.fullHoleName(), headerX, self.headerY)
        dc.DrawText(holeColumn.datatype(), headerX, self.headerY + self.headerLineSpacing) # hole datatype
        if holeColumn.hasPlot():
            rangeStr = "Range: {} : {}".format(str(holeColumn.minData()), str(holeColumn.maxData()))
            dc.DrawText(rangeStr, headerX, self.headerY +  self.headerLineSpacing * 2) # range
        dc.SetFont(self.stdFont) # reset to standard font

    def DrawHoleColumn(self, dc, holeColumn):
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.SetPen(wx.Pen(self.colorDict['foreground'], 1))
        dc.SetTextBackground(self.colorDict['background'])
        dc.SetTextForeground(self.colorDict['foreground'])
        dc.SetFont(self.stdFont)

        # TODO: skip draw if entire column will be outside viewport

        holeType = holeColumn.datatype()
        holeName = holeColumn.holeName()
        startX = self.GetHoleStartX(holeName, holeType)

        spliceScrollbarLeft = self.splicerX - 50
        headerBottom = self.startDepthPix - 20
        headerClipRegion = wx.Region(0, 0, spliceScrollbarLeft, headerBottom)
        self.DrawHoleHeader(dc, startX, holeColumn, headerClipRegion)

        rangeMax = startX + holeColumn.width()
        if self.showBounds:
            self.DrawDebugBounds(dc, startX, rangeMax)

        # draw vertical dotted line at left edge of hole column
        if self.showHoleGrid and startX < spliceScrollbarLeft:
            dc.SetPen(wx.Pen(self.colorDict['foreground'], 1, style=wx.DOT))
            dc.DrawLines(((startX, headerBottom), (startX, self.Height)))

        if holeType == "Natural Gamma": # TODO: fix this abomination
            holeType = "NaturalGamma"

        # apply range for current datatype
        smoothType = SmoothingType.NoSmoothing
        for r in self.range:
            if r[0] == holeType:
                # print("Getting range for {}".format(holeType))
                self.minRange = r[1]
                self.maxRange = r[2]
                if r[3] != 0.0:
                    self.coefRange = old_div(self.layoutManager.plotWidth, r[3])
                else:
                    self.coefRange = 0 
                smoothType = SmoothingType(r[4])
                self.continue_flag = r[5] 
                break

        # print("Hole {} Type {}, smooth_id = {}, continue_flag = {}".format(holeName, holeType, smooth_id, self.continue_flag))

        visibleTopDepth = self.rulerStartDepth - (old_div(20, self.pixPerMeter)) # todo: save this value as a member instead of computing everywhere

        # for each core in hole
        drawBoundariesFunc = self.DrawSectionBoundaries if self.pressedkeyS == 1 or self.showSectionDepths else self.DrawCoreBoundaries
        for coreIndex, cmd in enumerate([CoreMetadata(c) for c in holeColumn.cores()]):
            coreTop, coreBot = cmd.topDepth(), cmd.botDepth()

            # only draw columns for cores within visible depth range, but
            # create CoreInfo for all cores
            if not self.depthIntervalVisible(coreTop, coreBot, visibleTopDepth, self.rulerEndDepth):
                self.CreateCoreInfo(holeColumn, cmd.cmt, coreTop, coreBot, self.coreCount)
                self.coreCount += 1
                continue 

            colStartX = startX
            for columnType, width in holeColumn.columns():
                if columnType == ColumnType.Image:
                    if self.parent.sectionSummary:
                        self.DrawSectionImages(dc, colStartX, holeColumn.holeName(), cmd.coreName(), cmd.affineOffset())
                        if not holeColumn.hasPlot():
                            drawBoundariesFunc(dc, colStartX, width, holeColumn.holeName(), cmd.coreName(), cmd.affineOffset(), self.colorDict['imageOverlay'])
                elif columnType == ColumnType.Plot:
                    plotStartX = colStartX
                    if smoothType in [SmoothingType.NoSmoothing, SmoothingType.Unsmoothed]:
                        coresToPlot = [cmd]
                    else: # smoothType in [SmoothingType.Smoothed, SmoothingType.SmoothedAndUnsmoothed]
                        smooth_core = CoreMetadata(holeColumn.smoothCores()[coreIndex])
                        coresToPlot = [smooth_core] if smoothType == SmoothingType.Smoothed else [cmd, smooth_core]
                    # print("Core {}: smooth_id = {}, coresToPlot len = {}".format(cmd.coreName(), smooth_id, len(coresToPlot)))

                    for idx, ctp in enumerate(coresToPlot):
                        useSmoothColor = (smoothType == SmoothingType.Smoothed) or (smoothType == SmoothingType.SmoothedAndUnsmoothed and idx > 0)
                        plotColor = self.getHoleColor(holeColumn.holeName(), useSmoothColor)
                        self.DrawCorePlot(dc, colStartX, holeColumn.holeName(), ctp, plotColor)

                    # for now we'll continue to draw section boundaries only on the plot area
                    if self.parent.sectionSummary and self.showSectionDepths:
                        drawBoundariesFunc(dc, colStartX, width, holeColumn.holeName(), cmd.coreName(), cmd.affineOffset())
                else:
                    assert False, f"Unexpected column type {columnType}"

                colStartX += width

            coreInfo = self.CreateCoreInfo(holeColumn, cmd.cmt, coreTop, coreBot, self.coreCount)

            topPoint = self.getCoord(coreTop)
            botPoint = self.getCoord(coreBot)
            self.CreateCoreArea(coreInfo, startX, holeColumn.contentWidth(), topPoint, botPoint)
            self.coreCount += 1

            if self.showAffineShiftStrips:
                self.DrawAffineShiftStrip(dc, startX, topPoint, botPoint, holeColumn.holeName(), cmd.coreName())

            if cmd.affineOffset() != 0:
                clippingRegion = wx.Region(0, headerBottom, spliceScrollbarLeft, self.Height - headerBottom)
                self.DrawAffineShiftInfo(dc, startX, coreTop, coreBot, holeColumn, cmd, clippingRegion)
                if self.showAffineTies:
                    arrowStartX = plotStartX if holeColumn.hasPlot() else startX
                    self.PrepareTieShiftArrow(dc, arrowStartX, coreTop, coreBot, holeColumn, cmd)

    # Show affine shift direction, distance, and type to left of core, centered on core depth interval
    def DrawAffineShiftInfo(self, dc, startX, coreTopY, coreBotY, hole, core, clippingRegion):
        if self.showAffineShiftInfo:
            clip = wx.DCClipper(dc, clippingRegion)
            shiftInfoY = coreTopY + old_div((coreBotY - coreTopY), 2) # midpoint of core's depth interval
            y = self.startDepthPix + (shiftInfoY - self.rulerStartDepth) * self.pixPerMeter # depth to pix

            # prepare triangle indicating shift direction
            arrowheadAdjust = 8 if core.affineOffset() > 0 else -8
            arrowY = y + 4
            tribase1 = wx.Point(startX - 4, arrowY)
            tribase2 = wx.Point(startX + 4, arrowY)
            tribase3 = wx.Point(startX, arrowY + arrowheadAdjust)
            dc.SetPen(wx.Pen(self.colorDict['foreground'], 1))
            dc.SetBrush(wx.Brush(self.colorDict['foreground']))

            # draw triangle, observing right-hand rule
            if core.affineOffset() > 0:
                dc.DrawPolygon((tribase3, tribase2, tribase1))
            else:
                dc.DrawPolygon((tribase3, tribase1, tribase2))

            # draw shift distance and type
            dc.SetTextForeground(self.colorDict['foreground'])
            dc.DrawText(str(core.affineOffset()), startX - 40, y)
            shiftTypeStr = self.parent.affineManager.getShiftTypeStr(hole.holeName(), core.coreName())
            dc.DrawText(shiftTypeStr, startX - 32, y - 12)

    # draw color strip indicating affine shift type
    def DrawAffineShiftStrip(self, dc, startX, coreTopY, coreBotY, holeName, coreName):
        stripWidth = 3
        clip = self.ClipPlot(dc, startX - (stripWidth+1))
        stripColor = self.parent.affineManager.getShiftColor(holeName, coreName)
        dc.SetPen(wx.Pen(stripColor, 1))
        dc.SetBrush(wx.Brush(stripColor))
        dc.DrawRectangle(startX-stripWidth, coreTopY, stripWidth, coreBotY-coreTopY)

    # Draw arrow or line indicating a TIE between cores
    # brg 3/14/2022: Blatantly co-opting TIE arrow code to handle TIE lines because
    # it's quick and easy. The lines are a temporary v4 workaround for mixed-datatype
    # TIEs, which aren't preserved in the affine table. We agreed it's too late in v4
    # cycle to modify the affine table format to track mixed TIEs. We plan to do so in
    # v5, at which point this hack will be removed.
    # TODO: Assumes arrows are drawn plot to plot and image to image.
    # If we allow mixed TIEs between images and data, this will break.
    def PrepareTieShiftArrow(self, dc, startX, coreTopY, coreBotY, hole, core):
        shiftTypeStr = self.parent.affineManager.getShiftTypeStr(hole.holeName(), core.coreName())
        if shiftTypeStr == "TIE":
            tieDepth, parentCore = self.parent.affineManager.getTieDepthAndParent(hole.holeName(), core.coreName())
            holeType = hole.datatype()
            if not self.layoutManager.isHoleVisible(parentCore.hole, holeType):
                return
            if holeType == ImageDatatypeStr:
                parentStartX = self.GetHoleStartX(parentCore.hole, holeType)
                if parentStartX < startX:
                    parentStartX += self.layoutManager.imageWidth
                else:
                    startX += self.layoutManager.imageWidth
                arrowRect, drawData = self._createTieShiftArrowDrawData(parentStartX, startX, self.getCoord(tieDepth))
                self.AffineTieArrows.append((hole.holeName() + core.coreName(), arrowRect, drawData))
            else:
                parentCoreData = self.GetCoreData(parentCore.hole, holeType, parentCore.core)
                if parentCoreData is not None:
                    nearDepth, nearDatum = self.interpolateDataPoint(core.depthDataPairs(), tieDepth)
                    parentCoreData = self.GetCoreData(parentCore.hole, holeType, parentCore.core)
                    if parentCoreData is not None:
                        parentNearDepth, parentNearDatum = self.interpolateDataPoint(parentCoreData, tieDepth)
                    tieY = self.getCoord(nearDepth)
                    tieX = nearDatum - self.minRange
                    tieX = (tieX * self.coefRange) + startX
                    parentTieX = (parentNearDatum - self.minRange) * self.coefRange + self.GetHoleStartX(parentCore.hole, holeType)
                    arrowRect, drawData = self._createTieShiftArrowDrawData(parentTieX, tieX, tieY)
                    self.AffineTieArrows.append((hole.holeName() + core.coreName(), arrowRect, drawData))

    def _createTieShiftArrowDrawData(self, parentX, childX, y):
        rx = parentX if parentX < childX else childX
        arrowDir = 5 if parentX > childX else -5
        drawData = {}
        if self.showAffineTieArrows:
            drawData['arrow'] = ((parentX, y), (childX, y), (childX, y), (childX+arrowDir, y+5), (childX, y), (childX+arrowDir, y-5))
            drawData['circle'] = (parentX, y)
            arrowRect = wx.Rect(rx, y - 5, abs(childX - parentX), 10)
        else: # lines
            drawData['arrow'] = ((0, y), (self.splicerX - 60, y))
            arrowRect = wx.Rect(0, y, self.splicerX - 60, 5)
        return arrowRect, drawData

    def DrawTieShiftArrow(self, dc, arrowRect, drawData):
        if self.MousePos and arrowRect.Contains(wx.Point(self.MousePos[0], self.MousePos[1])):
            dc.SetPen(wx.Pen(wx.GREEN)) # highlight TIE arrow in green on mouseover
        else:
            dc.SetPen(wx.Pen(self.colorDict['foreground'], 1))

        if self.showAffineTieArrows: # circle on parent core, arrow to shifted core
            circle_x, circle_y = drawData['circle']
            dc.DrawCircle(circle_x, circle_y, 3) # radius 3
            dc.DrawLines(drawData['arrow'])
        else: # line across entire composite area
            dc.DrawLines(drawData['arrow'])

    def DrawTieShiftArrows(self, dc):
        clip = wx.DCClipper(dc, wx.Region(0, self.startDepthPix - 20, self.splicerX - 60, self.Height - (self.startDepthPix - 20)))
        for _, arrowRect, drawData in self.AffineTieArrows:
            self.DrawTieShiftArrow(dc, arrowRect, drawData)

    def PrintHoleSummary(self):
        print("{} holes in self.HoleData".format(len(self.HoleData)))
        for h in self.HoleData:
            hole = h[0] # hole data is added to a silly list where it's the only member, pull it out now
            # brg 11/18/2015: 
            # holeinfo: site, exp, type, ??minSecDepth, ??maxSecDepth, dataMin, dataMax, hole name (e.g. 'A'), core count
            # min/maxSecDepth appear to be the minimum and maximum top/bottom offset in the hole: not sure why we'd
            # want to track this in the context of a hole. May be a bug, but I don't think that data is used much if at all.
            # True hole min/max depths are available in the data returned from C++ side.
            hi = hole[0]
            print("hole: {}-{} {} type = {}, contains {} cores".format(hi[1], hi[0], hi[7], hi[2], hi[8]))
            for core in hole[1:]:
                ci = self.findCoreInfoByHoleCoreType(hi[7], core[0], hi[2])
                print(ci)
                print(core[:10])
                
                if self.parent.sectionSummary is not None:
                    if self.parent.sectionSummary.containsCore(hi[0], hi[7], core[0]):
                        print("Found in section summary")
                    else:
                        print("Did NOT find in section summary")
                                
            print("##########################################\n\n")
            
    def GetHoleSite(self, hole):
        site = None
        for h in self.HoleData:
            holeInnerList = h[0]
            holeInfo = holeInnerList[0]
            if holeInfo[7] == hole:
                site = holeInfo[0]
                break
        return site
    
    def GetHoleCores(self, hole):
        cores = []
        for h in self.HoleData:
            holeInnerList = h[0]
            holeInfo = holeInnerList[0]
            if holeInfo[7] == hole:
                for core in holeInnerList[1:]:
                    cores.append(core[0])
        return cores
    
    def GetCoreData(self, searchHole, holeType, searchCore):
        for h in self.HoleData:
            holeInnerList = h[0]
            holeInfo = holeInnerList[0]
            if holeInfo[7] == searchHole and holeInfo[2] == holeType:
                for coreInfo in holeInnerList[1:]:
                    if coreInfo[0] == searchCore:
                        return coreInfo[10]
        return None
    
    # wrapper to remove affine shifts before handing off to py_correlator.evalcoef(), which
    # has no knowledge of any affine shifts since they're now managed on the Python side 
    def EvaluateCorrelation(self, typeA, holeA, coreA, depthA, typeB, holeB, coreB, depthB):
        unshiftedDepthA = depthA - self.parent.affineManager.getShiftDistance(holeA, coreA)
        unshiftedDepthB = depthB - self.parent.affineManager.getShiftDistance(holeB, coreB)
        evalCoefs = py_correlator.evalcoef(typeA, holeA, int(coreA), unshiftedDepthA, typeB, holeB, int(coreB), unshiftedDepthB)
        return evalCoefs

    def _SetSpliceRangeCoef(self, smoothed):
        modifiedType = "splice"
        if smoothed == 7:
            modifiedType = "altsplice"
        for r in self.range:
            if r[0] == modifiedType:
                self.minRange = r[1]
                self.maxRange = r[2]
                if r[3] != 0.0:
                    self.coefRangeSplice = old_div(self.layoutManager.plotWidth, r[3])
                else:
                    self.coefRangeSplice = 0
                self.smooth_id = r[4]
                break
            
    def _GetSpliceRangeCoef(self, datamin, datamax):
        # return self.spliceHoleWidth / (datamax - datamin)
        return old_div(self.layoutManager.plotWidth, (datamax - datamin))
            
    def _UpdateSpliceRange(self, datamin, datamax):
        for r in self.range:
            if r[0] == "splice":
                self.range.remove(r)
                break
        self.range.append(("splice", datamin, datamax, datamax - datamin, 0, False))
        
    def _GetSpliceRange(self, datatype=None):
        rangemin, rangemax = None, None
        datatypes = [datatype] if datatype is not None else self.parent.spliceManager.getDataTypes() 
        for dt in datatypes:
            if dt == "Natural Gamma":
                dt = "NaturalGamma"
            datamin, datamax = self.GetMINMAX(dt)
            if rangemin is None or datamin < rangemin:
                rangemin = datamin
            if rangemax is None or datamax > rangemax:
                rangemax = datamax
        return rangemin, rangemax
        
    def DrawIntervalEdgeAndName(self, dc, interval, drawing_start, startX, drawDatatype=True):
        liney = self.startDepthPix + (interval.getBot() - self.SPrulerStartDepth) * self.pixPerMeter
        if liney < self.startDepthPix - 20:
            return # don't bother drawing if line is above top of plot area

        dc.SetPen(wx.Pen(self.colorDict['foreground'], 2))
        dc.DrawLine(startX - 20, liney, startX, liney)
        
        dc.SetTextForeground(self.colorDict['foreground'])
        coreName = f"{interval.coreinfo.hole}{interval.coreinfo.holeCore}"
        dc.DrawText(coreName, startX - (dc.GetTextExtent(coreName)[0] + 2), liney - (dc.GetCharHeight() + 2))
        if drawDatatype:
            datatype = interval.coreinfo.type[:5]
            dc.DrawText(datatype, startX - (dc.GetTextExtent(datatype)[0] + 2), liney - (dc.GetCharHeight() + 2) - self.headerLineSpacing)
        
    def DrawSpliceIntervalTie(self, dc, tie):
        fgPen = wx.Pen(self.colorDict['foreground'], 1, style=wx.DOT)
        fgBrush = wx.Brush(self.colorDict['foreground'])
        dc.SetPen(fgPen)
        dc.SetBrush(fgBrush)
        img_wid = self.GetSpliceAreaImageWidth()
        startx = self.splicerX + self.layoutManager.plotLeftMargin + img_wid - self.minSpliceScrollRange # beginning of splice plot area
        endx = startx + (self.layoutManager.plotWidth * 2) + len(self._getSpliceDatatypesToDraw()) * self.layoutManager.plotWidth + self.layoutManager.plotLeftMargin
        ycoord = self.getSpliceCoord(tie.depth())
        circlex = startx + (old_div(self.layoutManager.plotWidth, 2))
        namestr = tie.getName()
        namex = circlex - (old_div(dc.GetTextExtent(namestr)[0], 2))
        
        # message indicating why handle movement was restricted, draw handle/line in red
        if len(tie.clampMessage) > 0:
            dc.SetTextForeground(wx.RED)
            dc.SetPen(wx.Pen(wx.RED, 1))
            dc.SetBrush(wx.Brush(wx.BLACK))

            msgWidth, msgHeight = dc.GetTextExtent(tie.clampMessage)
            msgx = circlex - old_div(msgWidth, 2)
            msgy = ycoord - (tie.TIE_CIRCLE_RADIUS + 12 + 5 + msgHeight)
            dc.DrawRectangle(msgx - 1,  msgy - 1, msgWidth + 2, msgHeight + 2)
            dc.DrawText(tie.clampMessage, msgx, msgy)
            dc.SetBrush(wx.Brush(wx.RED))
            dc.DrawLine(startx, ycoord, endx, ycoord)
            dc.DrawCircle(circlex, ycoord, tie.TIE_CIRCLE_RADIUS)
            dc.SetTextForeground(self.colorDict['foreground'])
            dc.SetPen(fgPen)
            dc.SetBrush(fgBrush)
        else:
            dc.DrawLine(startx, ycoord, endx, ycoord)
            dc.DrawCircle(circlex, ycoord, tie.TIE_CIRCLE_RADIUS)
        
        dc.DrawText(namestr, namex, ycoord - (tie.TIE_CIRCLE_RADIUS + 12))
        
    def DrawSpliceInterval(self, dc, interval, drawing_start, startX, smoothed):
        interval.coreinfo.coredata = self.getCorePointData(interval.coreinfo.hole, interval.coreinfo.holeCore, interval.coreinfo.type)
        if len(interval.coreinfo.coredata) == 0: # data isn't enabled+loaded
            ypos = self.getSpliceCoord(interval.getTop() + (interval.getBot() - interval.getTop())/2.0) # draw at middle of interval
            dc.DrawText("[{}{} {} unavailable]".format(interval.coreinfo.hole, interval.coreinfo.holeCore, interval.coreinfo.type), startX + 5, ypos)
            self.DrawIntervalEdgeAndName(dc, interval, drawing_start, startX)
            return
        
        # set range for interval datatype so plot is drawn within expected bounds
        datatype = interval.coreinfo.type
        if datatype == "Natural Gamma":
            datatype = "NaturalGamma"
        rangemin, rangemax = self.GetMINMAX(datatype)
        self._UpdateSpliceRange(rangemin, rangemax)
        self._SetSpliceRangeCoef(smoothed)

        # gather datapoints within interval range for plotting
        intdata = [pt for pt in interval.coreinfo.coredata if pt[0] >= interval.getTop() and pt[0] <= interval.getBot()]
        screenPoints = self.GetScreenPointsBuffer(intdata, drawing_start, startX)
        usScreenPoints = [] # unsmoothed screenpoints
        smoothType = self.GetSmoothType(datatype)
        drawUnsmoothed = smoothType == 2 # 2 == draw both Smooth & Unsmooth data
        if drawUnsmoothed:
            smoothdata = self.getCorePointData(interval.coreinfo.hole, interval.coreinfo.holeCore, interval.coreinfo.type, forceUnsmooth=True)
            smoothdata = [pt for pt in smoothdata if pt[0] >= interval.getTop() and pt[0] <= interval.getBot()] # trim to interval
            usScreenPoints = self.GetScreenPointsBuffer(smoothdata, drawing_start, startX)

        self.DrawSpliceIntervalPlot(dc, interval, startX, screenPoints, smoothType,usScreenPoints, drawUnsmoothed, isMainSplice=True)

        if self.parent.sectionSummary and self.layoutManager.getShowImages():
            self.DrawSpliceIntervalImages(dc, interval, startX)

        if self.parent.spliceManager.isSelectedInterval(interval):
            for tie in self.parent.spliceManager.getTies():
                self.DrawSpliceIntervalTie(dc, tie)

        img_wid = self.GetSpliceAreaImageWidth()
        self.DrawIntervalEdgeAndName(dc, interval, drawing_start, startX - img_wid)

    # TODO: Mostly duplicative of DrawSpliceInterval()
    def DrawSpliceIntervalWithDatatype(self, dc, interval, datatype, drawing_start, startX, smoothed):
        interval.coreinfo.coredata = self.getCorePointData(interval.coreinfo.hole, interval.coreinfo.holeCore, datatype)
        if len(interval.coreinfo.coredata) == 0: # data isn't enabled+loaded
            ypos = self.getSpliceCoord(interval.getTop() + (interval.getBot() - interval.getTop())/2.0) # draw at middle of interval
            dc.DrawText("[{}{} {} unavailable]".format(interval.coreinfo.hole, interval.coreinfo.holeCore, datatype), startX + 5, ypos)
            self.DrawIntervalEdgeAndName(dc, interval, drawing_start, startX)
            return
        
        rangemin, rangemax = self.GetMINMAX("NaturalGamma" if datatype == "Natural Gamma" else datatype)
        self._UpdateSpliceRange(rangemin, rangemax)
        self._SetSpliceRangeCoef(smoothed)

        # gather datapoints within interval range for plotting
        intdata = [pt for pt in interval.coreinfo.coredata if pt[0] >= interval.getTop() and pt[0] <= interval.getBot()]
        screenPoints = self.GetScreenPointsBuffer(intdata, drawing_start, startX)
        usScreenPoints = [] # unsmoothed screenpoints 
        smoothType = self.GetSmoothType(datatype)
        drawUnsmoothed = smoothType == 2 # 2 == draw both Smooth & Unsmooth data
        if drawUnsmoothed:
            smoothdata = self.getCorePointData(interval.coreinfo.hole, interval.coreinfo.holeCore, datatype, forceUnsmooth=True)
            smoothdata = [pt for pt in smoothdata if pt[0] >= interval.getTop() and pt[0] <= interval.getBot()] # trim to interval
            usScreenPoints = self.GetScreenPointsBuffer(smoothdata, drawing_start, startX)

        self.DrawSpliceIntervalPlot(dc, interval, startX, screenPoints, smoothType, usScreenPoints, drawUnsmoothed, isMainSplice=False)
        self.DrawIntervalEdgeAndName(dc, interval, drawing_start, startX, drawDatatype=False)

    def DrawSpliceIntervalPlot(self, dc, interval, startX, screenPoints, smoothType, usScreenPoints, drawUnsmoothed, isMainSplice=True):
        clip_width = self.Width - startX if self.showOutOfRangeData else self.layoutManager.plotWidth
        clip = wx.DCClipper(dc, wx.Rect(startX, self.startDepthPix - 20, clip_width, self.Height - (self.startDepthPix - 20)))

        color = self.getHoleColor(interval.coreinfo.hole, smoothType in [1,2])
        unsmoothedColor = self.getHoleColor(interval.coreinfo.hole, False)
        lineWidth = 1
        if isMainSplice:
            if self.parent.spliceManager.isSelectedInterval(interval):
                lineWidth = 2
                if not self.drawSpliceInHoleColors:
                    color = self.colorDict['spliceSel']
                    unsmoothedColor = color
            else:
                if not self.drawSpliceInHoleColors:
                    color = self.colorDict['splice']
                    unsmoothedColor = color
        else:
            if not self.drawSpliceInHoleColors:
                color = self.colorDict['foreground']
                unsmoothedColor = color

        if len(screenPoints) >= 2:
            dc.SetPen(wx.Pen(color, lineWidth))
            if len(screenPoints) >= 4:
                dc.DrawLinesFromBuffer(screenPoints)
            elif len(screenPoints) >= 2:
                dc.SetBrush(wx.Brush(color))
                dc.DrawCircle(screenPoints[0], screenPoints[1], radius=2)
            else:
                pass # nothing to draw
        else:
            print("Can't draw {}, it contains 0 points".format(interval.coreinfo.getName()))
            
        if drawUnsmoothed:
            if len(usScreenPoints) >= 2:
                dc.SetPen(wx.Pen(unsmoothedColor, 1))
                if len(usScreenPoints) >= 4:
                    dc.DrawLinesFromBuffer(usScreenPoints)
                else:
                    dc.SetBrush(wx.Brush(color))
                    dc.DrawCircle(usScreenPoints[0], usScreenPoints[1], radius=2)
            else:
                print("Can't draw unsmoothed {} data over smoothed, it contains 0 points".format(interval.coreinfo.getName()))

    def DrawSpliceIntervalImages(self, dc, interval, startX):
        interval_top_y = self.startDepthPix + (interval.getTop() - self.rulerStartDepth) * self.pixPerMeter
        interval_bot_y = self.startDepthPix + (interval.getBot() - self.rulerStartDepth) * self.pixPerMeter
        drawing_start_y = self.startDepthPix - 20
        if interval_bot_y < drawing_start_y:
            return # don't bother drawing if interval bottom is above top of plot area

        img_clip_top_y = max(drawing_start_y, interval_top_y)

        # wx.DCClipper-based clipping region is destroyed when it goes out of scope (i.e. at function end)
        rect = wx.Rect(startX - self.layoutManager.imageWidth, img_clip_top_y, self.layoutManager.imageWidth, interval_bot_y - img_clip_top_y)
        clip = wx.DCClipper(dc, rect)

        secrows = self.parent.sectionSummary.getSectionRows(interval.coreinfo.hole, interval.coreinfo.holeCore)
        affine_shift = self.findCoreAffineOffset(interval.coreinfo.hole, interval.coreinfo.holeCore)
        for secIndex, row in enumerate(secrows):
            top = row.topDepth + affine_shift
            bot = row.bottomDepth + affine_shift
            topPx = self.startDepthPix + (top - self.rulerStartDepth) * self.pixPerMeter
            botPx = self.startDepthPix + (bot - self.rulerStartDepth) * self.pixPerMeter
            secName = row.fullIdentity()
            bmp = self.GetImageBitmap(secName, botPx - topPx)
            if bmp is not None:
                dc.DrawBitmap(bmp, startX - self.layoutManager.imageWidth, topPx)


    def GetScreenPoints(self, dataPoints, drawingStart, startX):
        screenpoints = []
        for pt in dataPoints:
            if pt[0] >= drawingStart and pt[0] <= self.SPrulerEndDepth:
                y = self.startDepthPix + (pt[0] - self.SPrulerStartDepth) * self.pixPerMeter
                x = (pt[1] - self.minRange) * self.coefRangeSplice + startX
                screenpoints.append((x,y))
        return screenpoints
    
    def GetScreenPointsBuffer(self, dataPoints, drawingStart, startX):
        screenpoints = []
        for pt in dataPoints:
            if pt[0] >= drawingStart and pt[0] <= self.SPrulerEndDepth:
                y = numpy.intc(self.startDepthPix + (pt[0] - self.SPrulerStartDepth) * self.pixPerMeter)
                x = numpy.intc((pt[1] - self.minRange) * self.coefRangeSplice + startX)
                screenpoints.append(x)
                screenpoints.append(y)
        return numpy.array(screenpoints)
    
    # draw info header above splice hole column
    def DrawSpliceHeader(self, dc):
        dc.SetFont(self.headerFont)
        firstint = self.parent.spliceManager.getIntervalAtIndex(0)
        rangeMax = self.splicerX + self.layoutManager.plotLeftMargin - self.minSpliceScrollRange
        dc.SetPen(wx.Pen(self.colorDict['foreground'], 1, style=wx.DOT))
        dc.DrawLines(((rangeMax, self.startDepthPix - 20), (rangeMax, self.Height)))
        dc.DrawText(f"{firstint.coreinfo.site}-{firstint.coreinfo.leg} Splice", rangeMax, self.headerY)
        dc.DrawText("Datatypes used:", rangeMax, self.headerY + self.headerLineSpacing)
        dc.DrawText(','.join(self.parent.spliceManager.getDataTypes()), rangeMax, self.headerY + self.headerLineSpacing * 2)
        dc.SetFont(self.stdFont) # restore standard font

    def DrawSplice(self, dc, hole, smoothed): # TODO: hole and smoothed are always NONE, why pass them at all?
        clip = wx.DCClipper(dc, wx.Region(self.splicerX, 0, self.Width - self.splicerX, self.Height))
        
        if self.parent.spliceManager.count() > 0:
            # vertical dotted line separating splice from splice guide area
            img_wid = self.GetSpliceAreaImageWidth()
            spliceholewidth = self.splicerX + img_wid + self.layoutManager.plotWidth + self.layoutManager.plotLeftMargin - self.minSpliceScrollRange
            dc.SetPen(wx.Pen(self.colorDict['foreground'], 1, style=wx.DOT))
            dc.DrawLines(((spliceholewidth, self.startDepthPix - 20), (spliceholewidth, self.Height)))

            rangemin, rangemax = self._GetSpliceRange()
            self._UpdateSpliceRange(rangemin, rangemax)
            self._SetSpliceRangeCoef(smoothed)
            self.DrawSpliceHeader(dc)
            
            drawing_start = self.SPrulerStartDepth - 5.0
            startX = self.splicerX + self.layoutManager.plotLeftMargin + img_wid - self.minSpliceScrollRange
            clip_y = self.startDepthPix - 20
            clip_height = self.Height - clip_y
            for si in self.parent.spliceManager.getIntervalsInRange(drawing_start, self.SPrulerEndDepth):
                self.DrawSpliceInterval(dc, si, drawing_start, startX, smoothed)
            if self.parent.spliceManager.hasSelection():
                selected_x = startX + self.layoutManager.plotWidth
                # draw debug guides for left and right bounds of selected core plot, immediately to right of splice
                # dc.SetPen(wx.Pen(wx.RED, 1))
                # dc.DrawLine(selected_x, clip_y, selected_x, clip_y + clip_height)
                # dc.DrawLine(selected_x + self.layoutManager.plotWidth, clip_y, selected_x + self.layoutManager.plotWidth, clip_y + clip_height)
                guide_clip_rect = wx.Rect(x=selected_x, y=clip_y, width=self.layoutManager.plotWidth, height=clip_height)
                self.DrawSelectedSpliceGuide(dc, self.parent.spliceManager.getSelectedInterval(), drawing_start, startX, guide_clip_rect)

            spliceAreaWidth = img_wid + ((self.layoutManager.plotWidth + self.layoutManager.plotLeftMargin) * 2)
            spliceAreaWidth += len(self._getSpliceDatatypesToDraw()) * self.layoutManager.plotWidth
            self.parent.SpliceScrollMax = spliceAreaWidth
        else: # draw help text
            ypos = self.getSpliceCoord(self.SPrulerStartDepth)
            dc.DrawText("Drag a core from the left to start a splice.", self.splicerX + 20, ypos + 20)
        
    def DrawAlternateSpliceHeader(self, dc, altSpliceX, datatype):
        dc.SetFont(self.headerFont)
        dc.SetPen(wx.Pen(self.colorDict['foreground'], 1, style=wx.DOT))
        dc.DrawLines(((altSpliceX, self.startDepthPix - 20), (altSpliceX, self.Height)))
        dc.DrawText("Splice", altSpliceX, self.headerY)
        dc.DrawText(datatype, altSpliceX, self.headerY + self.headerLineSpacing)
        dc.SetFont(self.stdFont) # restore standard font

    def _getSpliceDatatypesToDraw(self):
        altDatatypesToDraw = []
        for datatype in self.layoutManager.datatypeOrder:
            if datatype != ImageDatatypeStr and self.layoutManager.isDatatypeVisible(datatype):
                altDatatypesToDraw.append(datatype)
        return altDatatypesToDraw

    def DrawAlternateSplices(self, dc, hole, smoothed):
        if self.parent.spliceManager.count() == 0:
            return

        clip = wx.DCClipper(dc, wx.Region(self.splicerX, 0, self.Width - self.splicerX, self.Height))
        img_wid = self.GetSpliceAreaImageWidth()
        altSpliceX = self.splicerX + img_wid + ((self.layoutManager.plotWidth + self.layoutManager.plotLeftMargin) * 2) - self.minSpliceScrollRange

        for datatype in self._getSpliceDatatypesToDraw():
            # vertical dotted line separating splice from next splice hole (or core to be spliced)
            dc.SetPen(wx.Pen(self.colorDict['foreground'], 1, style=wx.DOT))
            dc.DrawLines(((altSpliceX, self.startDepthPix - 20), (altSpliceX, self.Height)))

            rangemin, rangemax = self._GetSpliceRange()
            self._UpdateSpliceRange(rangemin, rangemax)
            self._SetSpliceRangeCoef(smoothed)
            drawing_start = self.SPrulerStartDepth - 5.0
            for si in self.parent.spliceManager.splice.getIntervalsInRange(drawing_start, self.SPrulerEndDepth):
                self.DrawSpliceIntervalWithDatatype(dc, si, datatype, drawing_start, altSpliceX, smoothed)
            self.DrawAlternateSpliceHeader(dc, altSpliceX, datatype)

            altSpliceX += self.layoutManager.plotWidth
            
    # draw current interval's core in its entirety to the right of the splice
    def DrawSelectedSpliceGuide(self, dc, interval, drawing_start, startX, guide_clip_rect):
        img_wid = self.GetSpliceAreaImageWidth()
        screenpoints = []

        # set range for interval datatype so plot is drawn within expected bounds
        datatype = interval.coreinfo.type
        if datatype == "Natural Gamma":
            datatype = "NaturalGamma"
        rangemin, rangemax = self.GetMINMAX(datatype)
        self._UpdateSpliceRange(rangemin, rangemax)
        self._SetSpliceRangeCoef(None)
        
        # for pt in interval.coreinfo.coredata:
        for pt in self.getCorePointData(interval.coreinfo.hole, interval.coreinfo.holeCore, interval.coreinfo.type):
            if pt[0] >= drawing_start and pt[0] <= self.SPrulerEndDepth:
                y = self.startDepthPix + (pt[0] - self.SPrulerStartDepth) * self.pixPerMeter
                spliceholewidth = self.splicerX + self.layoutManager.plotLeftMargin + img_wid + self.layoutManager.plotWidth - self.minSpliceScrollRange
                x = (pt[1] - self.minRange) * self.coefRangeSplice + spliceholewidth
                screenpoints.append(numpy.intc(x))
                screenpoints.append(numpy.intc(y))
        screenpoints = numpy.array(screenpoints)
        if len(screenpoints) >= 2:
            if not self.showOutOfRangeData:
                clip = wx.DCClipper(dc, guide_clip_rect)
            dc.SetPen(wx.Pen(self.colorDict['spliceTrace'], 1))
            if len(screenpoints) >= 4:
                dc.DrawLinesFromBuffer(screenpoints)
            else:
                dc.SetBrush(wx.Brush(self.colorDict['spliceTrace']))
                dc.DrawCircle(screenpoints[0], screenpoints[1], radius=2)

    # find nearest point in coredata with depth less than searchDepth
    def nearestDataPointAbove(self, coredata, searchDepth):
        ptsabove = [pt for pt in coredata if pt[0] <= searchDepth]
        if len(ptsabove) == 0:
            print("Couldn't find point above in coredata")
            return coredata[0]
        return max(ptsabove, key=lambda pt:pt[0])
    
    # find nearest point in coredata with depth greater than searchDepth
    def nearestDataPointBelow(self, coredata, searchDepth):
        ptsbelow = [pt for pt in coredata if pt[0] >= searchDepth]
        if len(ptsbelow) == 0:
            print("Couldn't find point below in coredata")
            return coredata[-1]
        return min(ptsbelow, key=lambda pt:pt[0])
    
    # return point interpolated from nearest point above and below
    def interpolateDataPoint(self, coredata, searchDepth):
        above = self.nearestDataPointAbove(coredata, searchDepth)
        below = self.nearestDataPointBelow(coredata, searchDepth)
        interpDatum = numpy.interp(searchDepth, [above[0], below[0]], [above[1], below[1]])
        return (searchDepth, interpDatum)
    
    # Is given depth (point) in visible range? All args in meters.
    def depthVisible(self, depth, rangetop, rangebot):
        return depth >= rangetop and depth <= rangebot

    # Is given depth interval in visible range? All args in meters.
    def depthIntervalVisible(self, top, bot, rangetop, rangebot):
        return self.depthVisible(top, rangetop, rangebot) or self.depthVisible(bot, rangetop, rangebot) or (top <= rangetop and bot >= rangebot)

    # Colors are defined for holes A-F. Reuse colors in the unlikely event of holes beyond F.
    def getHoleColor(self, holeName, smooth=False):
        prefix = 'smooth' if smooth else 'hole'
        if 'A' <= holeName <= 'F':
            return self.colorDict[prefix + holeName]
        else: # use hole A color for hole G, B for H, C for I, etc.
            assert len(holeName) == 1 and holeName > 'F', "Unexpected hole name {}, must be a single capital letter A-Z".format(holeName)
            wrappedHoleCode = ord('A') + (ord(holeName) - ord('A')) % 6
            return self.colorDict[prefix + chr(wrappedHoleCode)]

    def DrawCorePlot(self, dc, plotStartX, holeName, core, plotColor):
        pointList = []
        for y, x in core.depthDataPairs():
            if y <= self.rulerEndDepth:
                y = self.startDepthPix + (y - self.rulerStartDepth) * self.pixPerMeter
                x = (x - self.minRange) * self.coefRange + plotStartX
                pointList.append(numpy.intc(x))
                pointList.append(numpy.intc(y))
            else: # y > self.rulerEndDepth:
                break
        
        # dc.DrawLinesFromBuffer() is significantly faster than dc.DrawLines(),
        # and requires a numpy array as input.
        points = numpy.array(pointList)
        
        # clip to avoid draw in splice area
        clip = self.ClipPlot(dc, plotStartX)

        # higlight background of selected core
        if self.selectedCore is not None and len(points) > 0:
             if self.selectedCore[0] == holeName and self.selectedCore[1] == core.coreName():
                highlightColor = wx.Colour(0, 0, 128, 64) # 75% transparent medium blue
                dc.SetPen(wx.Pen(highlightColor, 1))
                dc.SetBrush(wx.Brush(highlightColor))
                dc.DrawRectangle(plotStartX, points[1], self.layoutManager.plotWidth, points[-1] - points[1])
    
        # plot points
        dc.SetPen(wx.Pen(plotColor, 1))
        if self.DiscretePlotMode == 0 and len(points) >= 4:
            dc.DrawLinesFromBuffer(points)
        else:
            for pt in list(zip(points[0::2], points[1::2])): # create (x,y) tuples from list of form [x0, y0, x1, y1....]
                dc.DrawCircle(pt[0], pt[1], self.DiscreteSize)

        if len(points) > 0:
            self.DrawHighlight(dc, plotStartX, points[1], points[-1], len(points))

        if self.guideCore == self.coreCount:
            self.DrawGuideCore(dc, plotStartX)

    def ClipPlot(self, dc, plotStartX):
        if self.showOutOfRangeData: # clip only to prevent draw into splice area
            clip_x = 0
            clip_width = (self.splicerX - 60)
        else: # clip to plot area
            clip_x = plotStartX
            clip_width = min(self.layoutManager.plotWidth + 2, (self.splicerX - 60) - plotStartX)
            if clip_width < 0:
                clip_width = 0
        # wx.DCClipper-based clipping region is destroyed when it goes out of scope
        return wx.DCClipper(dc, wx.Region(x=clip_x, y=self.startDepthPix - 20, width=clip_width, height=self.Height-(self.startDepthPix-20)))

    # Add core's CoreArea metadata to DrawData
    def CreateCoreArea(self, coreInfo, x, width, top_y, bot_y):
        coreDrawData = (coreInfo, wx.Rect(x, top_y, width + 1, bot_y - top_y), self.HoleCount)
        self.DrawData["CoreArea"].append(coreDrawData)

    def CreateCoreInfo(self, holeColumn, coreMetadataTuple, coreTop, coreBot, coreCount):
        holeInfo = holeColumn.holeData[0]
        coreInfo = coreMetadataTuple
        coreInfoObj = CoreInfo(coreCount, holeInfo[0], holeInfo[1], holeInfo[7], coreInfo[0], coreInfo[3], coreInfo[4], coreTop, coreBot, coreInfo[6], holeInfo[2], coreInfo[8], self.HoleCount, coreInfo[10])
        self.DrawData["CoreInfo"].append(coreInfoObj)
        return coreInfoObj

    # Draw guide core (movable core data superimposed on fixed core for comparison)
    def DrawGuideCore(self, dc, plotStartX):
        # save current datatype range
        save_range = (self.minRange, self.maxRange, self.coefRange, self.continue_flag)
        self._getPlotRange(self.GuideCoreDatatype)

        lead = self.compositeDepth - self.parent.winLength
        lag = self.compositeDepth + self.parent.winLength
        lead_coords = []
        corr_window_coords = []
        lag_coords = []
        for y,x in self.GuideCore:
            dest = corr_window_coords
            if y < lead:
                dest = lead_coords
            elif y > lag:
                dest = lag_coords

            y = self.startDepthPix + (y - self.rulerStartDepth) * self.pixPerMeter
            x = ((x - self.minRange) * self.coefRange) + plotStartX
            dest.append(numpy.intc(x))
            dest.append(numpy.intc(y))

        if len(corr_window_coords) >= 2:
            dc.SetPen(wx.Pen(self.colorDict['foreground']))
            if len(lead_coords) >= 2:
                # connect last lead point to first corr_window point
                lead_coords.append(corr_window_coords[0])
                lead_coords.append(corr_window_coords[1])
                dc.DrawLinesFromBuffer(numpy.array(lead_coords))
            if len(lag_coords) >= 2:
                # connect last corr_window point to first lag point
                lag_coords = [corr_window_coords[-2], corr_window_coords[-1]] + lag_coords
                dc.DrawLinesFromBuffer(numpy.array(lag_coords))
            if len(corr_window_coords) >= 4: # need four coordinates to draw a line
                dc.SetPen(wx.Pen(self.colorDict['corrWindow']))
                dc.DrawLinesFromBuffer(numpy.array(corr_window_coords))

        # restore saved datatype range
        self.minRange, self.maxRange, self.coefRange, self.continue_flag = save_range

    # Highlight core on mouseover
    # TODO: Should be able to use self.mouseoverCore instead of rect.Contains()
    def DrawHighlight(self, dc, x, top_y, bot_y, pointCount):
        if self.MousePos and not self.HasDragCore() and not self.coreWasHighlighted and pointCount > 1:
            wid = self.layoutManager.plotWidth + 1
            if wx.Rect(x, top_y, wid, bot_y - top_y).Contains(self.MousePos):
                curPen = dc.GetPen()
                self.DrawHighlightRect(dc, x, top_y, wid, bot_y - top_y)
                dc.SetPen(curPen)
                self.coreWasHighlighted = True # ensure we only highlight a single core per draw cycle

    # Draw dashed rectangle around given bounds
    def DrawHighlightRect(self, dc, x, y, wid, hit):
        dc.SetPen(wx.Pen(self.colorDict['foreground'], 1, wx.DOT))
        dc.DrawLines(((x, y), (x + wid, y), (x + wid, y + hit), (x, y + hit), (x, y)))
        # dc.DrawLines(((x - 2, y - 2), (x + wid + 2, y - 2), (x + wid + 2, y + hit + 2), (x - 2, y + hit + 2), (x - 2, y - 2)))

    # for each section of a core, draw number, top, and bottom boundaries
    def DrawSectionBoundaries(self, dc, x, width, hole, coreno, affine_shift, color=None):
        clip = wx.DCClipper(dc, wx.Region(x-1, self.startDepthPix - 20, (self.splicerX - 60) - x, self.Height - (self.startDepthPix - 20)))
        penColor = self.colorDict['foreground'] if color is None else color
        dc.SetPen(wx.Pen(penColor, 1, style=wx.DOT))
        dc.SetTextForeground(penColor)
        secrows = self.parent.sectionSummary.getSectionRows(hole, coreno)
        # print("startDepth = {}, rulerStartDepth = {}, rulerEndDepth = {}".format(self.startDepthPix, self.rulerStartDepth, self.rulerEndDepth))
        for secIndex, row in enumerate(secrows):
            top = row.topDepth + affine_shift
            bot = row.bottomDepth + affine_shift
            y = self.startDepthPix + (top - self.rulerStartDepth) * self.pixPerMeter
            dc.DrawLines(((x, y), (x + width, y)))
            coreSectionStr = "{}-{}".format(coreno, row.section)
            dc.DrawText(coreSectionStr, x + 2, y)
            
            if secIndex == len(secrows) - 1: # draw bottom of last section
                ybot = self.startDepthPix + (bot - self.rulerStartDepth) * self.pixPerMeter
                dc.DrawLines(((x, ybot), (x + width, ybot)))

    # draw core number, top, and bottom boundaries
    def DrawCoreBoundaries(self, dc, x, width, hole, coreno, affine_shift, color=None):
        clip = wx.DCClipper(dc, wx.Region(x, self.startDepthPix - 20, (self.splicerX - 60) - x, self.Height - (self.startDepthPix - 20)))
        penColor = self.colorDict['foreground'] if color is None else color
        dc.SetPen(wx.Pen(penColor, 1, style=wx.DOT))
        dc.SetTextForeground(penColor)
        secrows = self.parent.sectionSummary.getSectionRows(hole, coreno)
        # print("startDepth = {}, rulerStartDepth = {}, rulerEndDepth = {}".format(self.startDepthPix, self.rulerStartDepth, self.rulerEndDepth))
        row = secrows[0]
        top = row.topDepth + affine_shift
        y = self.startDepthPix + (top - self.rulerStartDepth) * self.pixPerMeter
        dc.DrawLines(((x, y), (x + width, y)))
        coreSectionStr = "{}".format(coreno)
        dc.DrawText(coreSectionStr, x + 2, y)

        row = secrows[-1] # draw bottom of core
        bot = row.bottomDepth + affine_shift
        ybot = self.startDepthPix + (bot - self.rulerStartDepth) * self.pixPerMeter
        dc.DrawLines(((x, ybot), (x + width, ybot)))


    def DrawSectionImages(self, dc, startX, hole, coreno, affine_shift):
        clip = wx.DCClipper(dc, wx.Region(startX, self.startDepthPix - 20, (self.splicerX - 60) - startX, self.Height - (self.startDepthPix - 20)))
        secrows = self.parent.sectionSummary.getSectionRows(hole, coreno)
        for secIndex, row in enumerate(secrows):
            top = row.topDepth + affine_shift
            bot = row.bottomDepth + affine_shift
            topPx = self.startDepthPix + (top - self.rulerStartDepth) * self.pixPerMeter
            botPx = self.startDepthPix + (bot - self.rulerStartDepth) * self.pixPerMeter
            secName = row.fullIdentity()
            bmp = self.GetImageBitmap(secName, botPx - topPx)
            if bmp is not None:
                dc.DrawBitmap(bmp, startX, topPx)

    def DrawGraphInfo(self, dc, coreInfo):
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.SetPen(wx.Pen(self.colorDict['foreground'], 1))
        dc.SetTextBackground(self.colorDict['background'])
        dc.SetTextForeground(self.colorDict['foreground'])
        dc.SetFont(self.stdFont)
        dc.SetPen(wx.Pen(wx.Colour(0, 255, 0), 1))

        x = self.splicerX - 270
        # if flag == 2:
        # 	x = self.Width - 220

        dc.DrawText("Hole: " + coreInfo.hole + " Core: " + coreInfo.holeCore, x, self.startDepthPix)
        dc.DrawText("Min: " + str(coreInfo.minData) + " Max: " + str(coreInfo.maxData), x, self.startDepthPix + 20)

        return (coreInfo.type, coreInfo.hole)
    
    def DrawMouseInfo(self, dc, coreInfo, x, y, startx, overPlot, datatype):
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.SetPen(wx.Pen(self.colorDict['foreground'], 1))
        dc.SetTextBackground(self.colorDict['background'])
        dc.SetTextForeground(self.colorDict['foreground'])
        dc.SetFont(self.stdFont)

        ycoord = self.getDepth(y) if x < self.splicerX else self.getSpliceDepth(y)
        unroundedYcoord = ycoord
        ycoord = round(ycoord, 3)

        # draw data value of current mouse x position for hole's datatype
        data_str = None
        if overPlot:
            if datatype == "Natural Gamma":
                datatype = "NaturalGamma"
            for r in self.range:
                if r[0] == datatype:
                    minData = r[1]
                    if r[3] != 0.0:
                        self.coefRange = old_div(self.layoutManager.plotWidth, r[3])
                    else:
                        self.coefRange = 0
                    data_at_x = old_div((x - startx), self.coefRange) + minData
                    data_str = str(round(data_at_x, 3))
                    if self.drag == 0:
                        dc.DrawText(data_str, x, self.startDepthPix - 15)
                        # print("Mouse over datatype {}, x-pos = {}, data value = {}, startx = {}, mindata = {}".format(datatype, x, data_str, startx, minData))
                    break

        section, offset = self.parent.GetSectionAtDepth(coreInfo.leg, coreInfo.hole, coreInfo.holeCore, datatype, ycoord)
        self.statusStr = "Hole: " + coreInfo.hole + " Core: " + coreInfo.holeCore
        self.statusStr += " Section: " + str(section) + " Section offset: " + str(offset) + "cm"

        # Status bar: display depth at current mouse y position and data at x if available
        yUnitAdjusted = round(unroundedYcoord * self.GetRulerUnitsFactor(), 3)
        self.statusStr += " Depth: " + str(yUnitAdjusted)
        if data_str is not None:
            self.statusStr += " Data: " + data_str

    def DrawAnnotation(self, dc, info, line):
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.SetPen(wx.Pen(self.colorDict['foreground'], 1))
        dc.SetTextBackground(self.colorDict['background'])
        dc.SetTextForeground(self.colorDict['foreground'])
        dc.SetFont(self.stdFont)
        dc.SetPen(wx.Pen(wx.Colour(0, 255, 0), 1))
        y = 0
        if line == 1:
            y = self.Height - 90
        elif line == 2:
            y = self.Height - 70
        elif line == 3:
            y = self.Height - 50
        dc.DrawText(info, self.splicerX - 250, y)
    
    # baseX - x coordinate of rightmost point of legend: the last item's right edge will be at this coordinate
    # itemList - list of tuples of form (user-facing item name (e.g. "CCSF"), self.colorDict key ("mbsf"))
    def _drawColorLegend(self, dc, baseX, y, itemList):
        totalWidth = 0
        rightPadding = 5
        for elt in itemList:
            totalWidth += dc.GetTextExtent(elt[0])[0] + rightPadding
        startX = baseX - totalWidth
        
        for uiName, colorKey in itemList:
            dc.SetPen(wx.Pen(self.colorDict[colorKey], 1))
            dc.SetBrush(wx.Brush(self.colorDict[colorKey]))
            width = dc.GetTextExtent(uiName)[0] + rightPadding
            dc.DrawRectangle(startX, y, width, self.ScrollSize)
            dc.DrawText(uiName, startX, y)
            startX += width
        
    def DrawColorLegend(self, dc):
        if self.showAffineShiftStrips and self.showColorLegend:
            paintgap = 50 
            start = self.Width
            if self.spliceWindowOn == 1:
                start = self.splicerX - 60
            else:
                start = self.Width - self.ScrollSize

            y = self.Height - (self.ScrollSize * 2)
            itemList = [('CSF-A','mbsf'), ('CCSF TIE','ccsfTie'), ('CCSF SET','ccsfSet'), ('CCSF REL','ccsfRel')]
            self._drawColorLegend(dc, start, y, itemList)

    def Draw(self, dc):
        beginDrawTime = time.perf_counter()

        dc.SetBackground(wx.Brush(self.colorDict['background']))
        dc.Clear() # make sure you clear the bitmap!

        # 7/11/2020: Double-draw is because OnMainMotion() is called even
        # when the mouse has moved so little that the cursor position doesn't
        # change. Skipping draw when position is unchanged solves this
        # so things always draw fast.
        # 3/18/2019: Attempt to debug double-drawing issue after initial Load
        # of data, which seems to be fixed by clicking anywhere on the right-hand
        # panels, resulting in noticeably faster response. Looks like OnMainMotion()
        # is being called twice but thus far can't figure out why.
        # print("Draw() {}".format(self.drawCount))
        # self.drawCount += 1
        # stk = traceback.format_stack()
        # for thing in stk[len(stk) - 5:]:
        # 	print("{}".format(thing.strip()))
        # print("------\n")

        if self.WindowUpdate == 1: 
            self.Width, self.Height = self.parent.GetCorrelatorWindowSize()
            self.SetSize((self.Width, self.Height))
                
            self.parent.UpdateSize(self.Width, self.Height)

            if self.CLOSEFLAG == 1:
                self.Width = self.Width - 45 
                self.sidePanel.SetPosition((self.Width, 0))
                self.sidePanel.SetSize((45, self.Height))
                self.sideNote.SetSize((45, self.Height))
            else:
                self.Width = self.Width - self.sideTabSize
                self.sidePanel.SetPosition((self.Width, 0))
                self.sidePanel.SetSize((self.sideTabSize, self.Height))
                self.sideNote.SetSize((self.sideTabSize, self.Height))

            #self.eldPanel.SetPosition((self.Width, 50))
            self.subSideNote.SetSize((self.sideTabSize - 20, self.Height))

            if self.spliceWindowOn == 1:
                if self.splicerX <= self.compositeX:
                    self.splicerX = old_div(self.Width * 8, 10) + self.compositeX
                if self.splicerX > (self.Width - 100):
                    # splicerX gets set to 20 here on first launch...see
                    # 3/12/2022 DRAWHELL comment
                    self.splicerX = self.Width - 100
            else:
                self.splicerX = self.Width + 45
            self.WindowUpdate = 0

        self.DrawMainView(dc)

        ### Draw Scrollbars
        dc.SetBrush(wx.Brush(wx.Colour(205, 201, 201)))
        dc.SetPen(wx.Pen(wx.Colour(205, 201, 201), 1))

        # Scrollbar background rectangles
        if self.spliceWindowOn == 1:
            dc.DrawRectangle(self.compositeX, self.Height - self.ScrollSize, self.splicerX - 60 - self.compositeX, self.ScrollSize)
            dc.DrawRectangle(self.Width - self.ScrollSize - 1, 0, self.ScrollSize, self.Height)
            dc.DrawRectangle(self.splicerX, self.Height - self.ScrollSize, self.Width - self.splicerX, self.ScrollSize)
            dc.DrawRectangle(self.splicerX - self.ScrollSize - 45, 0, self.ScrollSize, self.Height)
        else:
            dc.DrawRectangle(self.compositeX, self.Height - self.ScrollSize, self.Width - 10 - self.compositeX, self.ScrollSize)
            dc.DrawRectangle(self.Width - self.ScrollSize - 1, 0, self.ScrollSize, self.Height)

        # Scrollbar thumbs
        for key, data in list(self.DrawData.items()):
            if key == "Skin": # draw composite area scrollbar thumb
                bmp, x, y = data
                dc.DrawBitmap(bmp, self.Width + x - 1, y, 1)
            elif key == "CompositeScroll": # draw horizontal scrollbar thumb
                bmp, x, y = data
                dc.DrawBitmap(bmp, x, self.Height + y, 1)
            elif key == "SpliceScroll" and self.spliceWindowOn: # draw splice scrollbar thumb
                bmp, x, y = data
                dc.DrawBitmap(bmp, x, self.Height + y, 1)
            elif key == "CoreImage":
                bmp, x, y = data
                dc.DrawBitmap(bmp, x, y, 1)

        if self.spliceWindowOn == 1 and "MovableSkin" in self.DrawData: # splice scrollbar thumb
            bmp, x, y = self.DrawData["MovableSkin"]
            x = x + self.splicerX - 40
            dc.DrawBitmap(bmp, x, y, 1)

        dc.SetTextForeground(wx.BLACK)
        self.DrawColorLegend(dc)

        self.statusStr = ""

        # determine which hole + datatype mouse cursor is over
        holeName = ""
        holeType = ""
        for key, data in list(self.DrawData.items()):
            if key == "MouseInfo":
                for r in data:
                    coreInfo, x, y, startx, overPlot = r
                    if coreInfo is not None and self.findCoreInfoByHoleCore(coreInfo.hole, coreInfo.holeCore) is not None:
                        if self.showCoreInfo:
                            self.DrawGraphInfo(dc, coreInfo)
                        holeType, holeName = coreInfo.type, coreInfo.hole
                        self.minData = coreInfo.minData
                        self.selectedHoleType = holeType
                        self.DrawMouseInfo(dc, coreInfo, x, y, startx, overPlot, holeType)
            if holeType != "":
                break
        # TODO: Need this ridiculous check because we insist on drawing
        # during init, before this wx.StaticText is created.
        if self.parent.statusBarText is not None:
            self.parent.statusBarText.SetLabel(self.statusStr)

        self.selectedHoleType = holeType

        # draw depth at mouse y-position
        if self.MousePos is not None:
            dc.SetBrush(wx.TRANSPARENT_BRUSH)
            dc.SetPen(wx.Pen(self.colorDict['foreground'], 1))
            dc.SetTextBackground(self.colorDict['background'])
            dc.SetTextForeground(self.colorDict['foreground'])
            #dc.SetFont(self.stdFont)
            ycoord = self.MousePos[1]
            ycoord = self.getDepth(ycoord) if self.MousePos[0] < self.splicerX else self.getSpliceDepth(ycoord)
            ycoord = ycoord * self.GetRulerUnitsFactor()
            ycoord = round(ycoord, 3)
            depthStrY = self.MousePos[1] - 12 # draw depth text just above horizontal depth line
            best_x = self.layoutManager.getClosestColumnRightEdge(self.MousePos[0])
            if self.MousePos[0] < self.splicerX:
                # Draw current depth in right margin of mouseover hole plot
                dc.DrawText(str(ycoord), best_x + 3, depthStrY)
                if self.showGrid:
                    dc.SetPen(wx.Pen(self.colorDict['foreground'], 1, style=wx.DOT))
                    dc.DrawLines(((self.compositeX, depthStrY), (self.splicerX - 50, depthStrY)))
            elif self.MousePos[0] <= self.Width: # 1/29/2014 brg: Don't draw depth info if we're over options tab
                dc.DrawText(str(ycoord), self.splicerX + 3, depthStrY)
                if self.showGrid:
                    dc.SetPen(wx.Pen(self.colorDict['foreground'], 1, style=wx.DOT))
                    dc.DrawLines(((self.splicerX, depthStrY), (self.Width, depthStrY)))

            # draw horizontal line indicating mouse depth
            if self.showDepthLine:
                if self.depthLinePos is None:
                    depthLinePos = self.getDepth(self.MousePos[1])
                else:
                    depthLinePos = self.depthLinePos
                    dc.DrawText(str(round(depthLinePos, 3)), best_x + 3, self.getCoord(depthLinePos) -12)
                dc.SetPen(wx.Pen(self.colorDict['foreground'], 1, style=wx.SOLID))
                dc.DrawLines(((self.compositeX, self.getCoord(depthLinePos)), (self.Width, self.getCoord(depthLinePos))))

        endDrawTime = time.perf_counter()
        if self.showFPS:
            crudeFPS = round(1.0 / (endDrawTime - beginDrawTime), 1)
            dc.DrawText(str(crudeFPS) + "fps", 0, 0)

    def LayoutHoleColumns(self):
        columnSpaceX = self.compositeX - self.minScrollRange + self.layoutManager.plotLeftMargin
        self.layoutManager.layout(self.HoleData, self.SmoothData, self.HolesWithImages, columnSpaceX, self.layoutManager.plotLeftMargin)
        self.HoleColumns = self.layoutManager.holeColumns
        self.WidthsControl = self.layoutManager.holePositions
        self.parent.CompositeScrollMax = self.layoutManager.getLayoutWidth()

    # Disable controls in CompositePanel and FilterPanel that require loaded data to
    # function and aren't otherwise en/disabled by their respective panel's logic (e.g.
    # if data is loaded, the Create/Edit buttons in FilterPanel will always be enabled).
    def DisableDisplayControls(self):
        self.parent.compositePanel.EnableSETButton(False)
        self.parent.filterPanel.DisableAllControls()

    # unused, sad!
    def _getPlotRange(self, datatype):
        if datatype == "Natural Gamma":
            datatype = "NaturalGamma"
        for r in self.range:
            if r[0] == datatype: 
                self.minRange = r[1]
                self.maxRange = r[2]
                if r[3] != 0.0:
                    self.coefRange = old_div(self.layoutManager.plotWidth, r[3])
                else:
                    self.coefRange = 0 
                smooth_id = r[4]
                self.continue_flag = r[5] 
                return (r[1], r[2], self.coefRange)
        
    def DrawMainView(self, dc):
        # print("{} DrawMainView()".format(self.draw_count))
        # self.draw_count += 1
        self.DrawData["CoreArea"] = [] 
        self.DrawData["CoreInfo"] = []
        self.AffineTieArrows = [] # (hole+core, bounding rect) for each TIE arrow
        self.coreWasHighlighted = False # has a core already been highlighted in this draw cycle?

        if self.ScrollUpdate == 1: 
            self.UpdateScroll(1)
            self.ScrollUpdate = 0 

        self.smooth_id = -1
        self.ELDapplied = False 
        self.HoleCount = 0
        self.coreCount = 0 
        self.newHoleX = 30.0
        holeType = ""

        self.LayoutHoleColumns()

        for holeColumn in self.HoleColumns:
            self.DrawHoleColumn(dc, holeColumn)
            self.HoleCount += 1

        if self.showPlotOverlays:
            datatypes = list(set([hc.datatype() for hc in self.HoleColumns if hc.datatype() != ImageDatatypeStr]))
            for dt in datatypes:
                dtHoles = sorted([hc for hc in self.HoleColumns if hc.datatype() == dt], key=lambda hc:hc.holeName())
                targetHole = dtHoles[0] # draw overlays on first hole alphabetically
                self.DrawPlotOverlay(dc, targetHole, dtHoles[1:])

        # Draw TIE shift arrows. Doing so here ensures they'll always
        # draw over hole plots and images.
        self.DrawTieShiftArrows(dc)

        self.HoleCount = 0
        self.coreCount = 0 
        self.newHoleX = 30.0
        # smooth_flag = 3 
        # holeType = ""
        # if len(self.HoleData) == 0:
            # smooth_flag = 1 
            
        self.HoleCount = -2 # hoo boy
        self.DrawRuler(dc)

         # If no data is loaded, show help text.
        if len(self.HoleData) == 0 and len(self.SmoothData) == 0:
            msg = "No Data has been loaded. In Data Manager, right-click on a Site and select Load."
            dc.DrawText(msg, self.compositeX + 10, self.getCoord(self.rulerStartDepth))

        if self.spliceWindowOn == 1:

            if self.ShowSplice == True:
                self.DrawSplice(dc, None, None)
                self.DrawAlternateSplices(dc, None, None)

        if self.HasDragCore():
            self.DrawDragCore(dc)

        # UI debugging helpers
# 		dc.SetPen(wx.Pen(wx.RED))
# 		dc.DrawLine(0, self.startDepthPix, 1000, self.startDepthPix)
# 		dc.SetPen(wx.Pen(wx.GREEN))
# 		dc.DrawLine(self.compositeX, 0, self.compositeX, 900)
# 		dc.DrawLine(self.splicerX, 0, self.splicerX, 900)

        self.DrawActiveAffineTies(dc)

    def DrawActiveAffineTies(self, dc):
        radius = old_div(self.tieDotSize, 2)
        fixedTieDepth = 0
        for compTie in self.TieData: # draw in-progress composite ties (not established TIE arrows)
            if compTie.fixed == 1:
                dc.SetBrush(wx.Brush(wx.RED))
                dc.SetPen(wx.Pen(wx.RED, 1))
            else:
                dc.SetBrush(wx.Brush(wx.GREEN))
                dc.SetPen(wx.Pen(wx.GREEN, 1))

            y = self.startDepthPix + (compTie.depth - self.rulerStartDepth) * self.pixPerMeter
            tempx = round(compTie.depth, 3)

            holeColumn = self.HoleColumns[compTie.hole]
            x = self.GetHoleStartX(holeColumn.holeName(), holeColumn.datatype())
            width = holeColumn.contentWidth()
            if compTie.depth >= self.rulerStartDepth and compTie.depth <= self.rulerEndDepth:
                if x < self.splicerX - 65: # splicerX - 65 is roughly left of splice area scrollbar...todo FUDGE
                    # don't draw tie line or end rectangle in Splice Area
                    x_end = min(x + width, self.splicerX - 65)
                    dc.DrawCircle(x, y, radius)
                    if compTie.fixed == 1: 
                        dc.SetPen(wx.Pen(wx.RED, self.tieline_width, style=wx.DOT))
                    else:
                        rect_x = x + width - radius
                        if rect_x < self.splicerX - 65:
                            dc.DrawRectangle(x + width - radius, y - radius, self.tieDotSize, self.tieDotSize)
                        dc.SetPen(wx.Pen(wx.GREEN, self.tieline_width, style=wx.DOT))

                    dc.DrawLine(x, y, x_end, y)
                    
                    posStr = str(tempx)
                    if compTie.fixed == 1: # store fixed depth for shift calc on next go-around
                        fixedTieDepth = round(compTie.depth, 3)
                    else: # movable tie, add shift distance to info str
                        shiftDist =  round(fixedTieDepth - compTie.depth, 3)
                        signChar = '+' if shiftDist > 0 else '' 
                        posStr += ' (' + signChar + str(shiftDist) + ')'
                    dc.DrawText(posStr, x + 10, y + 10)

    def DrawPlotOverlay(self, dc, targetHole, overlayHoles):
        # print("Overlay: targetHole = {}, overlayCores = {}".format(targetHole.columnKey(), len(overlayHoles)))
        holeType = targetHole.datatype()
        holeName = targetHole.holeName()
        startX = self.GetHoleStartX(holeName, holeType)
        if not targetHole.hasPlot():
            return
        
        overlayX = startX + targetHole.getColumnOffset(ColumnType.Plot)

        if holeType == "Natural Gamma": # TODO: fix this abomination
            holeType = "NaturalGamma"

        # apply range for current datatype
        smoothType = SmoothingType.NoSmoothing
        for r in self.range:
            if r[0] == holeType:
                # print("Getting range for {}".format(holeType))
                self.minRange = r[1]
                self.maxRange = r[2]
                if r[3] != 0.0:
                    self.coefRange = old_div(self.layoutManager.plotWidth, r[3])
                else:
                    self.coefRange = 0 
                smoothType = SmoothingType(r[4])
                self.continue_flag = r[5] 
                break

        # print("Hole {} Type {}, smooth_id = {}, continue_flag = {}".format(holeName, holeType, smooth_id, self.continue_flag))

        visibleTopDepth = self.rulerStartDepth - (old_div(20, self.pixPerMeter)) # todo: save this value as a member instead of computing everywhere

        # draw each overlay
        for overlayHole in overlayHoles:
            overlayColor = self.getHoleColor(overlayHole.holeName())
            for overlayIndex, cmd in enumerate([CoreMetadata(c) for c in overlayHole.cores()]):
                coreTop, coreBot = cmd.topDepth(), cmd.botDepth()
                # only draw overlay cores within visible depth range
                if not self.depthIntervalVisible(coreTop, coreBot, visibleTopDepth, self.rulerEndDepth):
                    continue 
                if smoothType in [SmoothingType.NoSmoothing, SmoothingType.Unsmoothed]:
                    coresToPlot = [cmd]
                else: # smoothType in [SmoothingType.Smoothed, SmoothingType.SmoothedAndUnsmoothed]
                    smooth_core = CoreMetadata(overlayHole.smoothCores()[overlayIndex])
                    coresToPlot = [smooth_core] if smoothType == SmoothingType.Smoothed else [cmd, smooth_core]
                # print("Core {}: smooth_id = {}, coresToPlot len = {}".format(cmd.coreName(), smooth_id, len(coresToPlot)))

                for idx, ctp in enumerate(coresToPlot):
                    self.DrawCorePlot(dc, overlayX, overlayHole.holeName(), ctp, overlayColor)

    def SetSaganFromFile(self, tie_list):
        self.LogTieData = []
        for tie_data in tie_list: 
            id, holeB, coreB, holeA, coreA, depth, depthB = tie_data 
            coreInfo = self.findCoreInfoByHoleCore(holeA, str(coreA))

            x = 100 + self.splicerX + self.holeWidth
            y = self.startDepthPix + (depthB - self.SPrulerStartDepth) * self.pixPerMeter
            l = []
            l.append((x, y, coreInfo.core, 1, -1, -1, depth, self.splicerX, id, depth))
            self.LogTieData.append(l)

            l = []
            x = x + self.holeWidth 
            y = self.startDepthPix + (depth - self.SPrulerStartDepth) * self.pixPerMeter
            l.append((x, y, coreInfo.core, 0, -1, -1, depth, self.splicerX, id, depth))
            self.LogTieData.append(l)

            rey1 = int(100.0 * float(depth)) / 100.0
            rey2 = int(100.0 * float(depthB)) / 100.0
            info = holeA + " " + str(coreA) + " " + str(rey2) + "\t [TieTo] Log " + str(rey1)
            self.parent.AddTieInfo(info, rey2)

        if len(self.LogTieData) > 0: 
            self.PreviewFirstNo = 1
            self.PreviewNumTies = 1


    def SetSpliceFromFile(self, tie_list, flag):
        # clean splice core
        self.SpliceCore = []
        if flag == False:
            self.SpliceTieData = []
            self.RealSpliceTie = []

        index = 0
        prevCoreIndex = -1 
        prevDepth = 0.0

        id = -1
        prevId = -1 
        strtypeA = ""
        strtypeB = ""
        for tie_data in tie_list: 
            id, typeB, holeB, coreB, typeA, holeA, coreA, depthA, depthB = tie_data 
            if typeA == 'GRA':
                typeA = 'Bulk Density(GRA)'
            if typeB == 'GRA':
                typeB = 'Bulk Density(GRA)'

            if flag == False: # create dummy splice ties
                self.RealSpliceTie.append(DefaultSpliceTie())
                self.RealSpliceTie.append(DefaultSpliceTie())

            if prevId != -1 and id == -1:
                self.SpliceCore.append(coreB)

            prevId = id

            coreInfoA = self.findCoreInfoByHoleCoreType(holeA, str(coreA), typeA)
            coreInfoB = self.findCoreInfoByHoleCoreType(holeB, str(coreB), typeB)

            if prevCoreIndex != coreInfoA.core:
                self.SpliceCore.append(coreInfoA.core)
            prevCoreIndex = coreInfoA.core

        if id != -1:
            self.SpliceCore.append(coreInfoB.core)

        prevCoreIndex = coreInfoA.core
        prevDepth = depthB

        self.SpliceTieFromFile = len(self.RealSpliceTie)


    def OnSetQTCb(self, event):
        opId = event.GetId() 
        if opId == 3: # show this core on Corelyzer
            for mouse in self.DrawData["MouseInfo"]:
                coreInfo = self.findCoreInfoByIndex(mouse[0])
                self.parent.ShowCoreSend(coreInfo.leg, coreInfo.site, coreInfo.hole, coreInfo.holeCore)
        # brgtodo 5/1/2014 unclear what we're doing here...search then return nothing on a match, set no globals, etc. ???
        elif opId == 4:
            for mouse in self.DrawData["MouseInfo"]:
                coreInfo = self.findCoreInfoByIndex(mouse[0])
                if coreInfo != None:
                    return

    def OnScaleSelectionCb(self, event):
        opId = event.GetId() 
        if opId == 1: # scale up
            if self.bothscale == 0:
                self.bothscale = 1 
            else:
                self.bothscale = 0 
        elif opId == 2: # data scale down
            if self.datascale == 0:
                self.datascale = 1 
            else:
                self.datascale = 0 
        self.UpdateDrawing()

    def OnLogTieSelectionCb(self, event):
        opId = event.GetId() 
        self.activeSATie = -1
        self.showMenu = False
        if opId == 1:
            self.DeleteLogTie()
            self.PreviewLog[0] = -1
            self.PreviewLog[1] = -1
            self.PreviewLog[2] = 1.0 
            self.PreviewLog[3] = 0
            self.PreviewLog[4] = -1
            self.PreviewLog[5] = -1
            self.PreviewLog[6] = 1.0 
            self.saganDepth = -1
        elif opId == 2:
            self.MatchLog()

        self.LogselectedTie = -1
        self.drag = 0 
        self.UpdateDrawing()

    def DeleteLogTie(self):
        if self.LogselectedTie >= 0:
            tieNo = -1
            data = self.LogTieData[self.LogselectedTie]
            fixed = 0
            for r in data:
                fixed = r[3]
                tieNo = r[8]

            if tieNo > 0:
                ret = py_correlator.delete_sagan(tieNo)
                if ret == 0:
                    self.LogselectedTie = -1
                    return

                if fixed == 0: # move tie
                    #self.LogTieData.remove(data)
                    #data = self.LogTieData[self.LogselectedTie-1]
                    #self.LogTieData.remove(data)
                    self.LogTieData.pop(self.LogselectedTie)
                    self.LogTieData.pop(self.LogselectedTie - 1)
                else:		 # fixed tie 
                    length = len(self.LogTieData)
                    if (self.SPselectedTie + 1) < length:
                        #data = self.LogTieData[self.LogselectedTie+1]
                        #self.LogTieData.remove(data)
                        self.LogTieData.pop(self.LogselectedTie + 1)
                    #data = self.LogTieData[self.LogselectedTie]
                    #self.LogTieData.remove(data)
                    self.LogTieData.pop(self.LogselectedTie)
                #self.HoleData = []
                #self.parent.OnGetData(self.parent.smoothDisplay, True)

                if self.hole_sagan == -1:
                    self.parent.UpdateELD(True)
                else: 
                    self.OnUpdateHoleELD()
                self.parent.EldChange = True


                s = "Log/Core Match undo: " + str(datetime.today()) + "\n\n"
                self.parent.logFileptr.write(s)
                if self.parent.showReportPanel == 1:
                    self.parent.OnUpdateReport()

                i = -1 
                if fixed == 1:
                    i = old_div((self.LogselectedTie + 1), 2)
                else:
                    i = old_div(self.LogselectedTie, 2)
                self.parent.eldPanel.DeleteTie(i)

            else:
                self.OnClearTies(2)

            self.LogselectedTie = -1
            if self.parent.eldPanel.fileList.GetCount() == 0:
                self.LogAutoMode = 1
                self.parent.autoPanel.OnButtonEnable(0, True)

    def MatchLog(self):
        if self.lastLogTie != -1:
            self.LogselectedTie = self.lastLogTie
            self.lastLogTie = -1

        if self.LogselectedTie >= 0:
            tieNo = -1 
            data = self.LogTieData[self.LogselectedTie]
            coreidA = 0
            coreidB = 0
            depth = 0
            corexB = 0
            y1 = 0
            y2 = 0
            x1 = 0
            x2 = 0
            for r in data:
                coreidB = r[2]
                #y1 = (r[1] - self.startDepthPix) / ( self.pixPerMeter / self._gap ) + self.SPrulerStartDepth
                y1 = r[6]
                x1 = r[4]

            data = self.LogTieData[self.LogselectedTie - 1]
            for r in data:
                coreidA = r[2]
                depth = r[6]
                #y2 = (r[1] - self.startDepthPix) / ( self.pixPerMeter / self._gap ) + self.SPrulerStartDepth
                y2 = r[6]
                tieNo = r[8]
                x2 = r[4]

            reversed = False
            if x1 < x2:
                reversed = True

            coreInfoA = self.findCoreInfoByIndex(coreidA)
            coreInfoB = self.findCoreInfoByIndex(coreidB)

            if coreInfoA != None and coreInfoB != None:
                preTieNo = tieNo
                annot_str = ""
                rd = -999
                if reversed == False:
                    tieNo, annot_str, rd = py_correlator.sagan(coreInfoB.hole, int(coreInfoB.holeCore), y1, coreInfoA.hole, int(coreInfoA.holeCore), y2, tieNo)
                else:
                    tieNo, annot_str, rd = py_correlator.sagan(coreInfoA.hole, int(coreInfoA.holeCore), y2, coreInfoB.hole, int(coreInfoB.holeCore), y1, tieNo)
                    temp = y2
                    y2 = y1
                    y1 = temp

                self.parent.EldChange = True
                if tieNo == 0:
                    self.LogselectedTie = -1
                    self.drag = 0
                    #print "[DEBUG] tieNo is Zero -- then error"
                    self.parent.OnShowMessage("Error", "Could not make tie", 1)
                    return

                if self.PreviewNumTies == 0:
                    self.PreviewNumTies = 1

                self.saganDepth = -1
                self.PreviewLog[0] = -1 
                self.PreviewLog[1] = -1 
                self.PreviewLog[2] = 1.0 
                self.PreviewLog[3] = 0
                self.PreviewLog[4] = -1 
                self.PreviewLog[5] = -1 
                self.PreviewLog[6] = 1.0 
                if self.LogAutoMode == 1:
                    self.LogAutoMode = 0
                    self.parent.autoPanel.OnButtonEnable(0, False)
        
                rey1 = int(100.0 * float(y1)) / 100.0
                rey2 = int(100.0 * float(y2)) / 100.0
                #info = str(holeA) + " " + str(coreA) + " " +str(rey2) + "\t [TieTo] Log " +str(rey1)
                info = annot_str + " " + str(rey2) + "\t [TieTo] Log " + str(rey1)
                if preTieNo != tieNo:
                    self.parent.AddTieInfo(info, rey1)
                else:
                    self.parent.UpdateTieInfo(info, rey1, self.LogselectedTie)

                s = "Log/Core Match: hole " + coreInfoA.hole + " core " + coreInfoA.holeCore + ": " + str(datetime.today()) + "\n"
                self.parent.logFileptr.write(s)
                s = coreInfoA.hole + " " + coreInfoA.holeCore + " " + str(y2) + " tied to " + coreInfoB.hole + " " + coreInfoB.holeCore + " " + str(y1) + "\n\n"
                self.parent.logFileptr.write(s)

                #self.SpliceData = []
                #self.HoleData = []
                #self.parent.OnGetData(self.parent.smoothDisplay, True)
                if self.hole_sagan == -1:
                    self.parent.UpdateELD(True)
                else: 
                    self.OnUpdateHoleELD()

                if len(self.LogTieData) >= 2:
                    if reversed == False:
                        data = self.LogTieData[self.LogselectedTie]
                    else:
                        data = self.LogTieData[self.LogselectedTie - 1]
                    prevy = 0 
                    prevd = 0 
                    for r in data:
                        x, y, n, f, startx, m, d, s, t, raw = r
                        y = self.startDepthPix + (rd - self.SPrulerStartDepth) * self.pixPerMeter
                        d = rd 

                        prevy = y 
                        prevd = d 
                        newtag = (x, y, n, f, startx, m, d, s, tieNo, raw)
                        data.remove(r)
                        data.insert(0, newtag)

                    if reversed == False:
                        data = self.LogTieData[self.LogselectedTie - 1]
                    else:
                        data = self.LogTieData[self.LogselectedTie]
                    for r in data:
                        x, y, n, f, startx, m, d, s, t, raw = r
                        newtag = (x, prevy, n, f, startx, m, prevd, s, tieNo, raw)
                        data.remove(r)
                        data.insert(0, newtag)

                    self.LogselectedTie = -1

    def OnUpdateHoleELD(self):
        self.parent.UpdateCORE()
        self.parent.UpdateSMOOTH_CORE()
        self.parent.UpdateSaganTie()
        self.LogSpliceData = []
        icount = 0
        for data in self.HoleData:
            for r in data:
                if icount == self.hole_sagan:
                    hole = r 
                    l = []
                    l.append(hole)
                    self.LogSpliceData.append(l)
                    break
            if self.LogSpliceData != []:
                break
            icount += 1 
        icount = 0
        self.LogSpliceSmoothData = []
        for data in self.SmoothData:
            for r in data:
                if icount == self.hole_sagan:
                    hole = r 
                    l = []
                    l.append(hole)
                    self.LogSpliceSmoothData.append(l)
                    break
            if self.LogSpliceSmoothData != []:
                break
            icount += 1 

    def OnSortList(self, index):
        data = self.LogTieData[self.LogselectedTie]
        data1 = self.LogTieData[self.LogselectedTie - 1]
        self.LogTieData.remove(data)
        self.LogTieData.remove(data1)
        self.LogTieData.insert(index - 1, data)
        self.LogTieData.insert(index - 1, data1)
        self.LogselectedTie = index 

    def ApplySplice(self, tieIndex):
        if tieIndex < 0:
            print("ApplySplice: invalid tie index {}".format(tieIndex))
            return

        spliceTieA = self.SpliceTieData[tieIndex] # tie on core being added to splice
        spliceTieB = self.SpliceTieData[tieIndex - 1] # tie on current splice core

        coreA = self.findCoreInfoByIndex(spliceTieA.core)
        coreB = self.findCoreInfoByIndex(spliceTieB.core)
        if coreA == None or coreB == None:
            return

        #print "Core A: " + str(ciA)
        #print "Core B: " + str(ciB)

        if self.GetTypeID(coreA.type) != self.GetTypeID(coreB.type):
            self.multipleType = True
        
        y1 = spliceTieA.depth
        y2 = spliceTieB.depth
        splice_data = py_correlator.splice(coreA.type, coreA.hole, int(coreA.holeCore), y1,
                                           coreB.type, coreB.hole, int(coreB.holeCore), y2,
                                           spliceTieA.tie, self.parent.smoothDisplay, 0)
        
        # splice_data array looks like this:
        # 0: C++ side tie ID
        # 1: hole data followed by coredata for each core
        # 2: tie depth

        self.parent.SpliceChange = True
        py_correlator.saveAttributeFile(self.parent.CurrentDir + 'tmp.splice.table', 2)

        if spliceTieA.tie <= 0 and splice_data[0] > 0:
            self.RealSpliceTie.append(spliceTieB)
            self.RealSpliceTie.append(spliceTieA)
            self.SpliceCore.append(spliceTieA.core)
        if splice_data[0] == -1:
            self.parent.OnShowMessage("Error", "It can not find value point.", 1)
            self.parent.splicePanel.OnButtonEnable(0, True)
            self.parent.splicePanel.OnButtonEnable(1, False)
            return

        prevTie = spliceTieA.tie
        spliceTieA.tie = splice_data[0]
        spliceTieB.tie = splice_data[0]
        if spliceTieA.constrained == 1:
            spliceTieA.depth = splice_data[2]
        if spliceTieB.constrained == 1:
            spliceTieB.depth = splice_data[2]

        if splice_data[1] != "":
            self.SpliceData = []
            self.parent.filterPanel.OnLock()
            self.parent.ParseData(splice_data[1], self.SpliceData)
            self.parent.filterPanel.OnRelease()
            self.parent.UpdateSMOOTH_SPLICE(False)

            # brgtodo 5/15/2014: This logic in button splice but not right-click splice.
            self.parent.splicePanel.OnButtonEnable(0, False)
            self.parent.splicePanel.OnButtonEnable(1, True)

            s = "Constrained Splice: "	
            if self.Constrained == 0:
                s = "Unconstrained Splice: "	

            s = s + "hole " + coreA.hole + " core " + coreA.holeCore + ": " + str(datetime.today()) + "\n"
            self.parent.logFileptr.write(s)
            s = coreB.hole + " " + coreB.holeCore + " " + str(y1) + " tied to " + coreA.hole + " " + coreA.holeCore + " " + str(y2) + "\n\n"
            self.parent.logFileptr.write(s)

            self.parent.SpliceSectionSend(coreB.hole, coreB.holeCore, y1, "split", prevTie)
            self.parent.SpliceSectionSend(coreA.hole, coreA.holeCore, y2, None, prevTie)
            if prevTie > 0:
                self.parent.SpliceSectionSend(coreB.hole, coreB.holeCore, y1, "split", -1)
                self.parent.SpliceSectionSend(coreA.hole, coreA.holeCore, y2, None, -1)

            self.SpliceTieData = []
            self.SpliceTieData.append(spliceTieB)
            self.SpliceTieData.append(spliceTieA)

        self.SPselectedTie = -1
        self.SPGuideCore = []
        self.drag = 0 
        self.UpdateDrawing()


    def OnSpliceTieSelectionCb(self, event):
        opId = event.GetId() 
        self.activeSPTie = -1
        self.showMenu = False
        if opId == 1:
            if len(self.SpliceTieData) > 2:
                if self.SPselectedTie < 2:
                    self.OnUndoSplice()
                else:
                    self.OnClearTies(1)
            else:
                if self.SpliceTieFromFile != len(self.RealSpliceTie):
                    #print "self.SpliceTieFromFile != len(self.RealSpliceTie), undo"
                    self.OnUndoSplice()
                else:
                    #print "self.SpliceTieFromFile == len(self.RealSpliceTie), clear ties"
                    self.OnClearTies(1)
            self.SPselectedTie = -1
            self.SPGuideCore = []
            self.drag = 0 
            self.UpdateDrawing()
        elif opId == 2:
            self.ApplySplice(self.SPselectedTie)

    def OnClearTies(self, mode):
        if mode == 0: # composite
            self.ClearCompositeTies()
        elif mode == 1: # splice
            realties = len(self.RealSpliceTie)
            curties = len(self.SpliceTieData)
            if realties == 0 and curties <= 2:
                self.SpliceTieData = []
            if realties >= 2 and curties <= 4:
                self.SpliceTieData = []
                data = self.RealSpliceTie[realties - 2]
                self.SpliceTieData.append(data)
                data = self.RealSpliceTie[realties - 1]
                self.SpliceTieData.append(data)

            self.SPGuideCore = []
            self.SPselectedTie = -1
        elif mode == 2: # log
            last = self.LogselectedTie + 1
            length = last % 2
            if length == 0 and last != 0:
                self.LogTieData.pop(last - 1)	
                self.LogTieData.pop(last - 2)	
            elif length == 1 and len(self.LogTieData) != 0: 
                self.LogTieData.pop(last - 1)	

            self.PreviewLog[0] = -1
            self.PreviewLog[1] = -1
            self.PreviewLog[2] = 1.0 
            self.PreviewLog[3] = 0
            self.PreviewLog[4] = -1
            self.PreviewLog[5] = -1
            self.PreviewLog[6] = 1.0 
            self.saganDepth = -1
            self.LogselectedTie = -1
            self.LDselectedTie = -1

        self.drag = 0 
        self.UpdateDrawing()

    def MakeStraightLine(self):
        last = len(self.LogTieData) 
        length = last % 2
        if length == 0 and last != 0:
            data = self.LogTieData[last - 2]	
            prevy = 0
            prevd = 0
            for r in data:
                x, y, n, f, startx, m, d, s, t, raw = r
                prevy = y
                prevd = d
            data = self.LogTieData[last - 1]	
            for r in data:
                x, y, n, f, startx, m, d, s, t, raw = r
                newtag = (x, prevy, n, f, startx, m, prevd, s, t, raw)
                data.remove(r)
                data.insert(0, newtag)

            self.UpdateDrawing()

    def ClearCompositeTies(self):
        self.TieData = []
        self.GuideCore = []
        self.activeTie = -1
        self.selectedTie = -1
        self.parent.clearSend()
        self.UpdateAffineTieCount(0)

    def UpdateAffineTieCount(self, count):
        self.affineBroadcaster.updateAffineTiePointCount(count)
        
    def UndoLastShift(self):
        py_correlator.undo(1, "X", 0)
        self.parent.AffineChange = True
        py_correlator.saveAttributeFile(self.parent.CurrentDir + 'tmp.affine.table'  , 1)

        s = "Composite undo previous offset: " + str(datetime.today()) + "\n\n"
        self.parent.logFileptr.write(s)
        if self.parent.showReportPanel == 1:
            self.parent.OnUpdateReport()

        self.parent.UpdateSend()
        #self.parent.UndoShiftSectionSend()
        self.parent.UpdateData()
        self.parent.UpdateStratData()

    def OnTieSelectionCb(self, event):
        opId = event.GetId()
        self.activeTie = -1
        self.showMenu = False
        if opId == 1: # Clear Tie
            self.ClearCompositeTies()
            self.selectedTie = -1
            self.drag = 0
            self.UpdateDrawing()
        elif opId in [2,3,4]:
            if opId == 2:
                shiftMethod = TieShiftMethod.TiedAndDeeperInHoles
            elif opId == 3:
                shiftMethod = TieShiftMethod.TiedAndDeeperInChain
            elif opId == 4:
                shiftMethod = TieShiftMethod.CoreOrChain
            self.OnAdjustCore(shiftMethod)

    def OnAdjustCore(self, shiftMethod, actionType=1): # tie by default
        if self.selectedLastTie < 0:
            self.selectedLastTie = len(self.TieData) - 1

        if self.selectedLastTie >= 0:
            movableTie = self.TieData[self.selectedLastTie]
            fixedTie = self.TieData[self.selectedLastTie - 1]
            y1 = movableTie.depth
            y2 = fixedTie.depth
            shift = fixedTie.depth - movableTie.depth
            #print "fixed tie depth = {}, movable tie depth = {}, shift = {}".format()

            if shift == 0:
                self.parent.OnShowMessage("Error", "Tie points cannot be at the same depth.", 1)
                self.selectedTie = -1
                return

            if actionType == 0: # adjust to reflect best offset
                offset = self.parent.compositePanel.GetBestOffset()
                y1 = y1 + offset
                shift = shift + offset

            ciA = self.findCoreInfoByIndex(movableTie.core)
            ciB = self.findCoreInfoByIndex(fixedTie.core)
            if ciA is not None and ciB is not None:
                comment = self.parent.compositePanel.GetComment()
                proceed = self.parent.affineManager.tie(shiftMethod, ciB.hole, ciB.holeCore, round(y2, 3), ciA.hole, ciA.holeCore, round(y1, 3), ciA.type, comment)
                if proceed:
                    self.OnDataChange(movableTie.core, shift) # apply shift to self.HoleData
                    self.parent.AffineChange = True

                    if shiftMethod == TieShiftMethod.CoreOnly:
                        s = "Affine shift (core only): hole " + ciA.hole + " core " + ciA.holeCore + ": " + str(datetime.today()) + "\n"
                        self.parent.logFileptr.write(s)
                    elif shiftMethod == TieShiftMethod.CoreAndRelatedBelow:
                        s = "Affine shift (core and related below): hole " + ciA.hole + " core " + ciA.holeCore + ": " + str(datetime.today()) + "\n"
                        self.parent.logFileptr.write(s)
                    else:
                        s = "Affine shift (core and all below): hole " + ciA.hole + " core " + ciA.holeCore + ": " + str(datetime.today()) + "\n"
                        self.parent.logFileptr.write(s)

                    s = ciA.hole + " " + ciA.holeCore + " " + str(y1) + " tied to " + ciB.hole + " " + ciB.holeCore + " " + str(y2) + "\n\n"
                    self.parent.logFileptr.write(s)

                    #py_correlator.saveAttributeFile(self.parent.CurrentDir + 'tmp.affine.table', 1)
                    self.parent.ShiftSectionSend()

                    if self.parent.showReportPanel == 1:
                        self.parent.OnUpdateReport()

                    self.parent.UpdateData()
                    self.parent.UpdateStratData()

            if actionType == 0: # update graph to reflect best correlation
                corr = self.EvaluateCorrelation(ciA.type, ciA.hole, int(ciA.holeCore), fixedTie.depth, ciB.type, ciB.hole, int(ciB.holeCore), y1)
                if corr != "":
                    self.parent.OnAddFirstGraph(corr, fixedTie.depth, y1)
                    self.parent.OnUpdateGraph()

            self.ClearCompositeTies()
            self.drag = 0 
            self.UpdateDrawing()

    def GetTypeID(self, typeA):
        type = -1
        if typeA == "Susceptibility":
            type = 32
        elif typeA == "Natural Gamma":
            type = 33
        elif typeA == "Reflectance":
            type = 34
        elif typeA == "Other Type":
            type = 35
        elif typeA == "ODP Other1":
            type = 7 
        elif typeA == "ODP Other2":
            type = 8 
        elif typeA == "ODP Other3":
            type = 9 
        elif typeA == "ODP Other4":
            type = 10 
        elif typeA == "ODP Other5":
            type = 11
        elif typeA == "Bulk Density(GRA)":
            type = 30
        elif typeA == "Pwave":
            type = 31
        return type
        
    def GetSpliceCore(self):
        result = None
        coreInfo = self.findCoreInfoByIndex(self.CurrentSpliceCore)
        if coreInfo != None:
            result = coreInfo.hole, coreInfo.holeCore, coreInfo.type
        return result

    def OnSpliceCore(self):
        self.parent.splicePanel.OnButtonEnable(0, False)
        self.parent.splicePanel.OnButtonEnable(1, True)
        lastTie = len(self.SpliceTieData) - 1
        # print "[DEBUG] length of Splice Ties " + str(len(self.SpliceTieData)) 
        self.ApplySplice(lastTie)

    def OnUndoSplice(self):
        lastTie = len(self.RealSpliceTie) - 1
    
        if lastTie >= 0:
            spliceTie = self.RealSpliceTie[lastTie]

            self.RealSpliceTie.pop()
            self.RealSpliceTie.pop()

            tieNo = 0 if spliceTie.tie == -1 else spliceTie.tie

            # delete splice tie
            if tieNo >= 0:
                self.SpliceCore.pop()
                splice_data = py_correlator.delete_splice(tieNo, self.parent.smoothDisplay)
                py_correlator.saveAttributeFile(self.parent.CurrentDir + 'tmp.splice.table'  , 2)
                self.parent.SpliceChange = True
                if splice_data != "":
                    self.SpliceData = []
                    self.parent.filterPanel.OnLock()
                    self.parent.ParseData(splice_data, self.SpliceData)

                    self.parent.filterPanel.OnRelease()
                    self.parent.UpdateSMOOTH_SPLICE(False)
                    if self.SpliceData == []: 
                        self.parent.splicePanel.OnButtonEnable(4, False)

                    self.parent.UndoSpliceSectionSend()

                s = "Splice undo last spliced tie: " + str(datetime.today()) + "\n\n"
                self.parent.logFileptr.write(s)
                if self.parent.showReportPanel == 1:
                     self.parent.OnUpdateReport()

                self.SPGuideCore = []
                self.SPselectedTie = -1
                
        if len(self.RealSpliceTie) == 0:
            self.parent.splicePanel.OnButtonEnable(1, False)
            self.CurrentSpliceCore = -1 

        self.SpliceTieData = []
        if len(self.RealSpliceTie) >= 2:
            realties = len(self.RealSpliceTie) - 2
            prevSpliceTie = self.RealSpliceTie[realties]
            if prevSpliceTie.core >= 0: 
                self.SpliceTieData.append(prevSpliceTie)
                curSpliceTie = self.RealSpliceTie[realties + 1]
                self.CurrentSpliceCore = curSpliceTie.core
                self.SpliceTieData.append(curSpliceTie)
            else:
                self.CurrentSpliceCore = -1

        ret = py_correlator.getData(2)
        if ret != "":
            self.parent.ParseSpliceData(ret, True)
            ret = "" 
        else:
            print("No py_correlator splice data")

        self.UpdateDrawing()

    def OnMouseWheel(self, event):
        rot = event.GetWheelRotation() 
        pos = event.GetPosition().Get()

        if pos[0] <= self.splicerX or not self.independentScroll:
            if self.parent.ScrollMax > 0:
                if rot < 0:
                    self.rulerStartDepth += self.rulerTickRate
                    if not self.independentScroll:
                        self.SPrulerStartDepth = self.rulerStartDepth 
                else: 
                    self.rulerStartDepth -= self.rulerTickRate
                    if self.rulerStartDepth < 0:
                        self.rulerStartDepth = 0.0
                    if not self.independentScroll:
                        self.SPrulerStartDepth = self.rulerStartDepth 
                self.UpdateScroll(1)
        else:
            if self.independentScroll and self.parent.ScrollMax > 0: 
                if rot < 0:
                    self.SPrulerStartDepth += self.rulerTickRate
                else: 
                    self.SPrulerStartDepth -= self.rulerTickRate
                    if self.SPrulerStartDepth < 0:
                        self.SPrulerStartDepth = 0.0
            self.UpdateScroll(2)

        self.UpdateDrawing()
        #event.Skip()


    def UpdateScroll(self, scroll_flag):
        if scroll_flag == 1:
            rate = old_div(self.rulerStartDepth, self.parent.ScrollMax) 
        elif scroll_flag == 2:
            rate = old_div(self.SPrulerStartDepth, self.parent.ScrollMax) 

        scroll_start = self.startDepthPix * 0.7	 
        scroll_width = self.Height - (self.startDepthPix * 1.6)
        scroll_width = scroll_width - scroll_start
        scroll_y = rate * scroll_width 
        scroll_width += scroll_start
        scroll_y += scroll_start
        if scroll_y < scroll_start:
            scroll_y = scroll_start
        if scroll_y > scroll_width:
            scroll_y = scroll_width 

        if scroll_flag == 1:
            for key, data in list(self.DrawData.items()):
                if key == "MovableInterface":
                    bmp, x, y = data
                    self.DrawData["MovableInterface"] = (bmp, x, scroll_y)

            if self.spliceWindowOn == 1:
                bmp, x, y = self.DrawData["MovableSkin"]
                self.DrawData["MovableSkin"] = (bmp, x, scroll_y)

            if self.parent.client != None:
#				# self.parent.client.send("show_depth_range\t"+str(self.rulerStartDepth)+"\t"+str(self.rulerEndDepth)+"\n") # JULIAN
                _depth = (self.rulerStartDepth + self.rulerEndDepth) / 2.0
                self.parent.client.send("jump_to_depth\t" + str(_depth) + "\n")

        if not self.independentScroll: # if composite/splice windows scroll together, scroll splice too
            scroll_flag = 2

        # brgtodo 4/23/2014: MovableInterface/Skin and Interface/Skin appear to be duplicating
        # most of their behavior/logic. Refactor into a common object.
        if scroll_flag == 2:
            bmp, x, y = self.DrawData["Interface"]
            self.DrawData["Interface"] = (bmp, x, scroll_y)

            bmp, x, y = self.DrawData["Skin"]
            self.DrawData["Skin"] = (bmp, x, scroll_y)

    def OnCharUp(self, event):
        keyid = event.GetKeyCode()

        if keyid == wx.WXK_ALT:
            self.showGrid = False 
            self.UpdateDrawing()
        elif keyid == wx.WXK_SHIFT:
            self.pressedkeyShift = 0 
            self.UpdateDrawing()
        elif keyid == ord("D"):
            self.pressedkeyD = 0 
            self.UpdateDrawing()
        elif keyid == ord("S"):
            self.pressedkeyS = 0 
            self.UpdateDrawing()

    def OnChar(self, event):
        eventCaught = True
        keyid = event.GetKeyCode()
        if keyid == 127:
            self.ClearCompositeTies()
        elif keyid == 72: # show/hide active affine ties...unused
            if self.hideTie == 1:
                self.hideTie = 0
            else: 
                self.hideTie = 1
        elif keyid == ord("D"):
            self.pressedkeyD = 1 
        elif keyid == ord("S"):
            self.pressedkeyS = 1 
        elif keyid == wx.WXK_ALT:
            self.showGrid = True
        elif keyid == wx.WXK_SHIFT:
            self.pressedkeyShift = 1 
        elif keyid == wx.WXK_DOWN and self.parent.ScrollMax > 0:
            if self.activeTie == -1 and self.activeSPTie == -1 and self.activeSATie == -1:
                if not self.independentScroll:
                    self.rulerStartDepth += self.rulerTickRate
                    if self.rulerStartDepth > self.parent.ScrollMax:
                        self.rulerStartDepth = self.parent.ScrollMax
                    self.SPrulerStartDepth = self.rulerStartDepth 
                elif event.GetModifiers() & wx.MOD_SHIFT: # arrow + shift moves splice only
                    self.SPrulerStartDepth += self.rulerTickRate
                else:
                    self.rulerStartDepth += self.rulerTickRate
                    if self.rulerStartDepth > self.parent.ScrollMax:
                        self.rulerStartDepth = self.parent.ScrollMax

                self.UpdateScroll(1)
            else:
                self.UPDATE_TIE(False)
        elif keyid == wx.WXK_UP and self.parent.ScrollMax > 0:
            if self.activeTie == -1 and self.activeSPTie == -1 and self.activeSATie == -1:
                if not self.independentScroll:
                    self.rulerStartDepth -= self.rulerTickRate
                    if self.rulerStartDepth < 0:
                        self.rulerStartDepth = 0.0
                    self.SPrulerStartDepth = self.rulerStartDepth
                elif event.GetModifiers() & wx.MOD_SHIFT: # arrow + shift moves splice only
                    self.SPrulerStartDepth -= self.rulerTickRate
                else:
                    self.rulerStartDepth -= self.rulerTickRate
                    if self.rulerStartDepth < 0:
                        self.rulerStartDepth = 0
                self.UpdateScroll(1)
            else:
                self.UPDATE_TIE(True)
        elif keyid == wx.WXK_LEFT:
            self.minScrollRange = self.minScrollRange - 15 
            if self.minScrollRange < 0:
                self.minScrollRange = 0
        elif keyid == wx.WXK_RIGHT:
            self.minScrollRange = self.minScrollRange + 15 
            if self.minScrollRange > self.parent.CompositeScrollMax:
                self.minScrollRange = self.parent.CompositeScrollMax 
        else:
            eventCaught = False
            event.Skip()
            
        if eventCaught:
            self.UpdateDrawing()


    # called on up/down arrow keyup only (mouse drag handled elsewhere)
    def UPDATE_TIE(self, upflag):
        shift_delta = self.shift_range 
        if upflag == True:
            shift_delta *= -1 

        data = []
        if self.activeTie != -1: # update composite tie
            if len(self.TieData) < self.activeTie:
                self.activeTie = -1
                return

            movableTie = self.TieData[self.activeTie]
            movableTie.depth += shift_delta
            movableTie.screenY = self.startDepthPix + (movableTie.depth - self.rulerStartDepth) * self.pixPerMeter

            fixedTie = self.TieData[self.activeTie - 1]
            depth = movableTie.depth
            depth2 = fixedTie.depth

            ciA = self.findCoreInfoByIndex(fixedTie.core)
            ciB = self.findCoreInfoByIndex(movableTie.core)
    
            shift = fixedTie.depth - movableTie.depth
            shiftx = fixedTie.hole - movableTie.hole
            self.OnUpdateGuideData(self.activeCore, shiftx, shift)
            self.parent.OnUpdateDepth(shift)
            self.parent.TieUpdateSend(ciA.leg, ciA.site, ciA.hole, int(ciA.holeCore), ciB.hole, int(ciB.holeCore), depth, shift)

            flag = self.parent.showELDPanel | self.parent.showCompositePanel | self.parent.showSplicePanel
            if flag == 1:
                testret = self.EvaluateCorrelation(ciA.type, ciA.hole, int(ciA.holeCore), depth2, ciB.type, ciB.hole, int(ciB.holeCore), depth)
                if testret != "":
                    self.parent.OnAddFirstGraph(testret, depth2, depth)

                typeA = ciA.type # needed since we don't want to modify ciA's type
                for data_item in self.range:
                    if data_item[0] == "Natural Gamma" and ciA.type == "NaturalGamma":
                        typeA = "Natural Gamma"
                    elif data_item[0] == "NaturalGamma" and ciA.type == "Natural Gamma":
                        typeA = "NaturalGamma"
                    if data_item[0] != typeA and data_item[0] != "splice" and data_item[0] != "log":
                        testret = self.EvaluateCorrelation(data_item[0], ciA.hole, int(ciA.holeCore), depth2, data_item[0], ciB.hole, int(ciB.holeCore), depth)
                        if testret != "":
                            self.parent.OnAddGraph(testret, depth2, depth)

                self.parent.OnUpdateGraph()


        elif self.activeSPTie != -1: # update splice tie
            if len(self.SpliceTieData) < self.activeSPTie:
                self.activeSPTie = -1
                return

            curSpliceTie = self.SpliceTieData[self.activeSPTie]
            newDepth = curSpliceTie.depth + shift_delta
            curSpliceTie.depth = newDepth
            curSpliceTie.y = self.startDepthPix + (newDepth - self.SPrulerStartDepth) * self.pixPerMeter # brgtodo 5/13/2014: splice getDepth/getCoord
            prevSpliceTie = self.SpliceTieData[self.activeSPTie - 1]
            if self.Constrained == 1:
                prevSpliceTie.y = curSpliceTie.y
                prevSpliceTie.depth = curSpliceTie.depth

            ciA = self.findCoreInfoByIndex(prevSpliceTie.core)
            ciB = self.findCoreInfoByIndex(curSpliceTie.core)

            shift = prevSpliceTie.depth - curSpliceTie.depth
            self.OnUpdateSPGuideData(self.activeCore, curSpliceTie.depth, shift)
            if self.Constrained == 0:
                self.parent.splicePanel.OnUpdateDepth(shift)

            self.parent.splicePanel.OnButtonEnable(0, True)
            flag = self.parent.showELDPanel | self.parent.showCompositePanel | self.parent.showSplicePanel
            if flag == 1:
                testret = py_correlator.evalcoef_splice(ciB.type, ciB.hole, int(ciB.holeCore), 
                                                        curSpliceTie.depth, prevSpliceTie.depth)
                if testret != "":
                    self.parent.OnAddFirstGraph(testret, prevSpliceTie.depth, curSpliceTie.depth)

                typeA = ciA.type # needed since we don't want to modify ciA's type
                for data_item in self.range:
                    if data_item[0] == "Natural Gamma" and typeA == "NaturalGamma":
                        typeA = "Natural Gamma"
                    elif data_item[0] == "NaturalGamma" and typeA == "Natural Gamma":
                        typeA = "NaturalGamma"
                    if data_item[0] != typeA and data_item[0] != "splice" and data_item[0] != "log":
                        testret = py_correlator.evalcoef_splice(data_item[0], ciB.hole, int(ciB.holeCore),
                                                                curSpliceTie.depth, prevSpliceTie.depth)
                        if testret != "":
                            self.parent.OnAddGraph(testret, prevSpliceTie.depth, curSpliceTie.depth)
                self.parent.OnUpdateGraph()

        else: # update log tie
            if len(self.LogTieData) < self.activeSATie:
                self.activeSATie = -1
                return

            data = self.LogTieData[self.activeSATie]
            x1 = 0
            x2 = 0
            y1 = 0
            y2 = 0
            n2 = -1 
            currentY = 0
            for r in data:
                x, y, n, f, startx, m, d, splicex, i, raw = r
                n1 = n
                x1 = x
                y1 = d + shift_delta
                y = self.startDepthPix + (y1 - self.SPrulerStartDepth) * self.pixPerMeter
                newtag = (x, y, n, f, startx, m, y1, splicex, i, raw)
                data.remove(r)
                data.insert(0, newtag)

            self.saganDepth = y1

            data = self.LogTieData[self.activeSATie - 1]
            for r in data:
                x2 = r[0]
                y2 = r[6]
                n2 = r[2] 

            coreInfo = self.findCoreInfoByIndex(n2)
            count = 0
            if len(self.SpliceCore) == 1:
                self.PreviewNumTies = 0
                for i in range(self.parent.eldPanel.fileList.GetCount()):
                    start = 0
                    last = 0
                    data = self.parent.eldPanel.fileList.GetString(i)
                    last = data.find(" ", start) # hole
                    temp_hole = data[start:last]
                    start = last + 1
                    last = data.find(" ", start) # core
                    temp_core = data[start:last]
                    if temp_hole == coreInfo.hole and temp_core == coreInfo.holeCore:
                        self.PreviewFirstNo = count * 2 + 1
                        self.PreviewNumTies = 1
                        break
                    count = count + 1

            self.PreviewLog = [-1, -1, 1.0, 0, -1, -1, 1.0]
            if len(self.LogTieData) == 2 or self.PreviewNumTies == 0:
                self.PreviewFirstNo = self.activeSATie
                self.PreviewLog[3] = y1 - y2
                if self.Floating == False:
                    self.PreviewLog[0] = self.FirstDepth 
                    self.PreviewLog[1] = y2
                    self.PreviewLog[2] = old_div((y1 - self.FirstDepth), (y2 - self.FirstDepth))
                    self.PreviewLog[3] = y1 - y2

                    if (self.activeSATie + 2) < len(self.LogTieData):
                        data = self.LogTieData[self.activeSATie + 1]
                        for r in data:
                            y3 = r[6]
                        self.PreviewLog[4] = y2
                        self.PreviewLog[5] = y3
                        self.PreviewLog[6] = old_div((y3 - y1), (y3 - y2))
            else:
                y3 = 0
                data = self.LogTieData[self.activeSATie - 2]
                for r in data:
                    y3 = r[6]
                self.PreviewLog[2] = old_div((y1 - y3), (y2 - y3))
                self.PreviewLog[0] = y3
                self.PreviewLog[1] = y2
                if (self.activeSATie + 2) < len(self.LogTieData):
                    data = self.LogTieData[self.activeSATie + 1]
                    for r in data:
                        y3 = r[6]
                    self.PreviewLog[4] = y2
                    self.PreviewLog[5] = y3
                    self.PreviewLog[6] = old_div((y3 - y1), (y3 - y2))

            flag = self.parent.showELDPanel | self.parent.showCompositePanel | self.parent.showSplicePanel
            if coreInfo.hole != 'x' and flag == 1:
                testret = py_correlator.evalcoefLog(coreInfo.hole, int(coreInfo.holeCore), y2, y1)
                if testret != "":
                    self.parent.OnAddFirstGraph(testret, y2, y1)
                    self.parent.OnUpdateGraph()

    def OnBreakTie(self, event, holecore):
        self.parent.affineManager.breakTie(holecore)

    def OnRMouse(self, event):
        pos = event.GetPosition().Get()
        self.selectedTie = -1 

        dotsize_y = self.tieDotSize + 10
        half = old_div(dotsize_y, 2)

        count = 0
        for tie in self.TieData: # handle context-click on in-progress tie points
            holeColumn = self.HoleColumns[tie.hole]
            x = self.GetHoleStartX(holeColumn.holeName(), holeColumn.datatype())
            y = self.startDepthPix + (tie.depth - self.rulerStartDepth) * self.pixPerMeter
            width = holeColumn.contentWidth()
            dotsize_x = self.tieDotSize + width + 10
            reg = wx.Rect(x - half, y - half, dotsize_x, dotsize_y)
            if reg.Contains(wx.Point(pos[0], pos[1])):
                self.selectedTie = count
                self.showMenu = True
                popupMenu = wx.Menu()
                popupMenu.Append(1, "&Clear tie point(s)")
                if tie.fixed == 0: # movable tie
                    popupMenu.Append(2, "&Shift this core or chain, all deeper chains and deeper cores in all holes")
                    popupMenu.Append(3, "&Shift this core or chain and all cores below this core or chain")
                    popupMenu.Append(4, "&Shift this core or chain only")

                # brg 11/29/2023: A bit odd to bind to the menu itself, but it works, seems
                # harmless, and self.parent.Bind(...) breaks the main window's menu handling.
                popupMenu.Bind(wx.EVT_MENU, self.OnTieSelectionCb)
                self.parent.PopupMenu(popupMenu, event.GetPosition().Get())
                return
            count = count + 1

        # handle right-click on an existing tie arrow
        for holecore, rect, _ in self.AffineTieArrows:
            if rect.Contains(wx.Point(pos[0], pos[1])):
                popupMenu = wx.Menu()
                popupMenu.Append(2, "Break TIE to {}".format(holecore))
                wx.EVT_MENU(popupMenu, 2, lambda evt, hc=holecore: self.OnBreakTie(evt, hc))
                self.parent.PopupMenu(popupMenu, pos)
                break

        count = 0
        for spliceTie in self.SpliceTieData:
            y = self.startDepthPix + (spliceTie.depth - self.SPrulerStartDepth) * self.pixPerMeter
            x = self.splicerX + 50
            reg = None
            if (count % 2) == 1:
                x += self.holeWidth + 50
            reg = wx.Rect(x - half, y - half, dotsize_x, dotsize_y)

            if reg.Contains(wx.Point(pos[0], pos[1])):
                self.SPselectedTie = count
                popupMenu = wx.Menu()
                self.showMenu = True
                # create Menu
                popupMenu.Append(1, "&Clear")
                wx.EVT_MENU(popupMenu, 1, self.OnSpliceTieSelectionCb)
                if spliceTie.fixed == 0: # move tie
                    popupMenu.Append(2, "&Set")
                    wx.EVT_MENU(popupMenu, 2, self.OnSpliceTieSelectionCb)
                self.parent.PopupMenu(popupMenu, event.GetPosition().Get())
                return
            count = count + 1

        count = 0
        for data in self.LogTieData:
            for r in data:
                x = self.splicerX + self.holeWidth + 100
                y = self.startDepthPix + (r[6] - self.SPrulerStartDepth) * self.pixPerMeter
                reg = None
                if (count % 2) == 1:
                    x += self.holeWidth + 50
                reg = wx.Rect(x - half, y - half, dotsize_x, dotsize_y)

                if reg.Contains(wx.Point(pos[0], pos[1])):
                    self.LogselectedTie = count
                    self.showMenu = True
                    popupMenu = wx.Menu()
                    # create Menu
                    popupMenu.Append(1, "&Clear")
                    wx.EVT_MENU(popupMenu, 1, self.OnLogTieSelectionCb)
                    if r[3] == 0: # move tie	
                        popupMenu.Append(2, "&Set")
                        wx.EVT_MENU(popupMenu, 2, self.OnLogTieSelectionCb)
                    self.parent.PopupMenu(popupMenu, event.GetPosition().Get())
                    return
            count = count + 1

        if pos[0] <= self.splicerX:
            for mouse in self.DrawData["MouseInfo"]:
                if self.findCoreInfoByIndex(mouse[0]) != None:
                    popupMenu = wx.Menu()
                    #popupMenu.Append(4, "&Undo last shift")
                    #wx.EVT_MENU(popupMenu, 4, self.OnTieSelectionCb)
                    if self.parent.client != None:
                        popupMenu.Append(3, "&Show it on Corelyzer")
                        wx.EVT_MENU(popupMenu, 3, self.OnSetQTCb)
                    self.parent.PopupMenu(popupMenu, event.GetPosition().Get())
                    return
                break # brgtodo 5/1/2014: needed? probably only have one MouseInfo at a time...

    def OnLMouse(self, event):
        pos = event.GetPosition().Get()
        for key, data in list(self.DrawData.items()):
            if key == "Interface": # dragging composite area vertical scroll thumb? Or moving comp/splice separating scrollbar?
                bmp, x, y = data
                x = self.Width + x
                w, h = bmp.GetWidth(), bmp.GetHeight()
                reg = wx.Rect(x, y, w, h)
                if reg.Contains(wx.Point(pos[0], pos[1])):				 
                    if self.independentScroll and self.spliceWindowOn == 1:
                        self.grabScrollB = 1
                        print("grab scroll B")
                    elif not self.independentScroll:# or self.spliceWindowOn == 0:
                        self.grabScrollA = 1
                        # print("grab scroll A")
                    self.UpdateDrawing()
            elif key == "MovableInterface": # dragging splice area vertical scroll thumb?
                bmp, x, y = data
                x = x + self.splicerX - 40
                w, h = bmp.GetWidth(), bmp.GetHeight()
                reg = wx.Rect(x, y, w, h)
                if reg.Contains(wx.Point(pos[0], pos[1])):
                    # print("grab scroll A MovableInterface")
                    self.grabScrollA = 1	
                    self.UpdateDrawing()
            elif key == "MovableSkin" and self.spliceWindowOn == 1: # dragging comp/splice separating scrollbar
                bmp, x, y = data
                x = x + self.splicerX - 40
                w, h = bmp.GetWidth(), bmp.GetHeight()
                w = self.ScrollSize
                reg = wx.Rect(x, pos[1], w, h)
                if reg.Contains(wx.Point(pos[0], pos[1])):
                    self.selectScroll = 1
            elif key == "CompositeScroll":
                bmp, x, y = data
                y = self.Height + y
                w, h = bmp.GetWidth(), bmp.GetHeight()
                reg = wx.Rect(x, y, w, h)
                if reg.Contains(wx.Point(pos[0], pos[1])):
                    self.dragCompositeScroll = True
            elif key == "SpliceScroll":
                bmp, x, y = data
                y = self.Height + y
                w, h = bmp.GetWidth(), bmp.GetHeight()
                reg = wx.Rect(x, y, w, h)
                if reg.Contains(wx.Point(pos[0], pos[1])):
                    self.dragSpliceScroll = True

        self.OnMainLMouse(event)

    def _clickInSpliceIntervalArea(self, clickPos):
        horzRangeMax = self.splicerX + self.GetSpliceAreaImageWidth() + (self.layoutManager.plotLeftMargin * 2) + self.layoutManager.plotWidth
        inHorzRange = clickPos[0] >= self.splicerX and clickPos[0] < horzRangeMax
        inVertRange = clickPos[1] >= self.startDepthPix and clickPos[1] < self.Height - self.ScrollSize
        return inHorzRange and inVertRange

    def OnMainLMouse(self, event):
        # check left or right
        pos = event.GetPosition().Get()
        self.selectedTie = -1 
        self.activeTie = -1
        self.activeSPTie = -1
        self.activeSATie = -1

        # move active affine tie
        dotsize_y = self.tieDotSize + 10
        half = old_div(dotsize_y, 2)
        for tie_idx, tie in enumerate(self.TieData):
            holeColumn = self.HoleColumns[tie.hole]
            width = holeColumn.contentWidth()
            x = self.GetHoleStartX(holeColumn.holeName(), holeColumn.datatype())
            y = self.startDepthPix + (tie.depth - self.rulerStartDepth) * self.pixPerMeter
            dotsize_x = self.tieDotSize + width + 10 # should extend all the way to right square handle
            reg = wx.Rect(x - half, y - half, dotsize_x, dotsize_y)
            if reg.Contains(wx.Point(pos[0], pos[1])):
                if tie.fixed == 0:
                    self.selectedTie = tie_idx
                    if tie_idx == 1:
                        self.activeTie = tie_idx
                    return

        # check for click on SpliceIntervalTie - is user starting to drag?
        img_wid = self.GetSpliceAreaImageWidth()
        for siTie in self.parent.spliceManager.getTies():
            basex = self.splicerX + self.layoutManager.plotLeftMargin + img_wid + (old_div(self.layoutManager.plotWidth, 2)) - self.minSpliceScrollRange
            basey = self.getSpliceCoord(siTie.depth())
            rect = wx.Rect(basex - 8, basey - 8, 16, 16)
            if rect.Contains(wx.Point(pos[0], pos[1])):
                self.parent.spliceManager.selectTie(siTie)
                self.UpdateSpliceEvalPlot()
                return
        
        # select SpliceInterval at click depth
        if self._clickInSpliceIntervalArea(pos):
            depth = self.getSpliceDepth(pos[1])
            if not self.parent.spliceManager.select(depth):
                self.parent.OnShowMessage("Error", self.parent.spliceManager.getErrorMsg(), 1)
            return

        # Detect shift-click on core to prepare for affine tie creation
        if self.pressedkeyShift == 1:
            if self.drag == 0:
                for area in self.DrawData["CoreArea"]:
                    coreInfo, rect, hole_idx = area
                    if rect.Contains(wx.Point(pos[0], pos[1])):
                        self.mouseoverCore = coreInfo.core # TODO: SelectedCoreAffine?
                        self.mouseX = pos[0] 
                        self.mouseY = pos[1] 
                        self.currentStartX = rect.GetX()
                        self.currentHole = hole_idx 
                        return

        # Drag core from composite to splice area to add to splice.
        # Disable while scrolling or when there are active composite ties.
        if len(self.TieData) == 0 and self.selectScroll == 0 and self.grabScrollA == 0 and not self.dragCompositeScroll:
            if pos[0] <= self.splicerX:
                for area in self.DrawData["CoreArea"]:
                    coreInfo, rect, hole_idx = area
                    if rect.Contains(wx.Point(pos[0], pos[1])):
                        self.dragCore = coreInfo.core

        # Toggle between fixed depth line and following mouse cursor
        if self.showDepthLine and self.selectScroll == 0 and self.grabScrollA == 0 and not self.dragCompositeScroll:
            if self.depthLinePos is None:
                self.depthLinePos = self.getDepth(pos[1])
            else:
                self.depthLinePos = None

    # select double-clicked core
    def OnDoubleLeftClick(self, event):
        pos = event.GetPosition().Get()
        for area in self.DrawData["CoreArea"]:
            coreInfo, rect, _ = area
            if rect.Contains(wx.Point(pos[0], pos[1])):
                self.selectedCore = coreInfo.hole, str(coreInfo.holeCore)
                return
        self.selectedCore = None

    def OnDataChange(self, core, shift):
        coreInfo = self.findCoreInfoByIndex(core)
        for data in self.HoleData:
            for record in data:
                holeInfo = record[0]
                if holeInfo[7] == coreInfo.hole:
                    count = 0
                    for coredata in record:
                        if coredata[0] == coreInfo.holeCore and count != 0:
                            valuelist = coredata[10]
                            count = 0
                            for v in valuelist:
                                x, y = v
                                x = x + shift
                                news = (x, y)
                                valuelist.remove(v)
                                valuelist.insert(count, news)
                                count = count + 1
                            return
                        count = 1


    # shiftx unused
    def OnUpdateGuideData(self, core, shiftx, shifty):
        self.GuideCore = []
        coreInfo = self.findCoreInfoByIndex(core)

        # determine smoothing type
        temp_type = coreInfo.type
        if temp_type == "Natural Gamma":
            temp_type = "NaturalGamma"
        smooth_id = -1
        for r in self.range:
            if r[0] == temp_type:
                smooth_id = r[4]
                break

        # create guide core's draw data from smoothed/unsmoothed
        dataSource = self.SmoothData if smooth_id == 1 else self.HoleData
        for data in dataSource:
            for record in data:
                holeInfo = record[0]
                if holeInfo[7] == coreInfo.hole and holeInfo[2] == coreInfo.type:
                    count = 0
                    self.GuideCoreDatatype = coreInfo.type
                    for coredata in record: 
                        if coredata[0] == coreInfo.holeCore and count != 0:
                            valuelist = coredata[10]
                            for v in valuelist:
                                x, y = v
                                x = x + shifty
                                self.GuideCore.append((x,y))
                            return
                        count = 1


    def OnUpdateSPGuideData(self, core, cut, shift):
        self.SPGuideCore = []
        coreInfo = self.findCoreInfoByIndex(core)

        # create guide core's draw data from smoothed/unsmoothed
        dataSource = self.SmoothData if self.splice_smooth_flag == 1 else self.HoleData
        for data in dataSource:
            for record in data:
                holeInfo = record[0]
                if holeInfo[7] == coreInfo.hole and holeInfo[2] == coreInfo.type:
                    count = 0
                    for coredata in record:
                        if coredata[0] == coreInfo.holeCore and count != 0:
                            valuelist = coredata[10]
                            for v in valuelist:
                                x, y = v
                                x = x + shift
                                if self.Constrained == 0 or (self.Constrained == 1 and x >= cut):
                                    l = []
                                    l.append((x, y))
                                    self.SPGuideCore.append(l) 
                            return
                        count = 1 

    # get leftmost coordinate for given hole name and datatype
    def GetHoleStartX(self, holeName, holeType):
        holeStartX = [x[0] for x in self.WidthsControl if x[1] == holeName + holeType]
        assert len(holeStartX) == 1
        return holeStartX[0]
    
    def DrawDragCore(self, dc):
        if self.DrawData["DragCore"] != []:
            xoffset = self.DrawData["DragCore"].x
            yoffset = self.DrawData["DragCore"].y
            dc.SetPen(wx.Pen(wx.RED, 1))

            # build list of core graph lines
            dragCoreLines = []
            coreInfo = self.findCoreInfoByIndex(self.dragCore)
            if coreInfo is None:
                print("DrawDragCore: can't get coreInfo for dragCore {}".format(self.dragCore))
                return
            
            holeData = None
            holeInfo = None
            smoothHoleData = None
            smoothHoleInfo = None
            for hole in self.HoleData:
                curHoleInfo = hole[0][0]
                if curHoleInfo[7] == coreInfo.hole and curHoleInfo[2] == coreInfo.type:
                    holeInfo = curHoleInfo
                    holeData = hole[0]
            for hole in self.SmoothData:
                curHoleInfo = hole[0][0]
                if curHoleInfo[7] == coreInfo.hole and curHoleInfo[2] == coreInfo.type:
                    smoothHoleInfo = curHoleInfo
                    smoothHoleData = hole[0]
            
            drawSmooth = False
            for r in self.range:
                # find matching type (account for space mismatch in "Natural Gamma" types)
                if r[0] == holeInfo[2] or r[0] == holeInfo[2].replace(' ', ''):
                    typeMin = r[1]
                    typeMax = r[2]
                    if r[3] != 0.0:
                        typeCoefRange = old_div(self.layoutManager.plotWidth, r[3])
                    else:
                        self.coefRange = 0
                    drawSmooth = (r[4] > 0) # type 0 = Unsmoothed, 1 = SmoothedOnly 2 = Smoothed&Unsmoothed
                    break
                
            holeData = smoothHoleData if drawSmooth else holeData
            for coredata in holeData[1:]: # every item after index 0 is a core in that hole
                if coredata[0] == coreInfo.holeCore:
                    valuelist = coredata[10]
                    for v in valuelist:
                        depth, datum = v
                        screenx = (datum - typeMin) * typeCoefRange
                        x = screenx + xoffset - (old_div(self.layoutManager.plotWidth, 2))
                        screeny = self.getCoord(depth)
                        y = screeny + yoffset
                        dragCoreLines.append((x, y))

            # now draw the lines
            dclen = len(dragCoreLines)
            idx = 0
            for pt in dragCoreLines:
                dc.DrawLines((dragCoreLines[idx], dragCoreLines[idx+1]))
                idx += 1
                if idx >= (dclen - 1):
                    break

    def OnDrawGuide(self):
        if self.selectedTie < 0:
            return
        else:
            fixedTie = self.TieData[self.selectedTie - 1]
            self.guideCore = fixedTie.core

            movableTie = self.TieData[self.selectedTie]

            shift = fixedTie.depth - movableTie.depth
            shiftx = fixedTie.hole - movableTie.hole
            self.compositeDepth = fixedTie.depth

            self.activeCore = self.mouseoverCore
            self.OnUpdateGuideData(self.mouseoverCore, shiftx, shift)

    def GetDataInfo(self, coreindex):
        coreInfo = self.findCoreInfoByIndex(coreindex)
        return (coreInfo.hole, int(coreInfo.holeCore), coreInfo.type, coreInfo.quality, coreInfo.holeCount)

    def GetFixedCompositeTie(self):
        if len(self.TieData) >= 1:
            return self.TieData[0]
        
    def GetFixedCompositeTieCore(self):
        if len(self.TieData) >= 1:
            return self.findCoreInfoByIndex(self.TieData[0].core)

    def CanSpliceCore(self, prevCore, coreToSplice):
        result = False
        #print "CanSpliceCore: prevCore = {}, toSplice = {}".format(prevCore, coreToSplice)
        ciA = self.findCoreInfoByIndex(prevCore)
        ciB = self.findCoreInfoByIndex(coreToSplice)
        if ciA != None and ciB != None and ciA.hole != ciB.hole:
            result = True
        return result

    def HasDragCore(self):
        return self.dragCore != -1

    def UpdateAgeModel(self):
        space_bar = ""
        if platform_name[0] == "Windows":
            space_bar = " "

        # 9/23/2013 brgtodo duplication
        for data in self.StratData:
            for r in data:
                order, hole, name, label, start, stop, rawstart, rawstop, age, type = r 
                strItem = ""
                bm0 = int(100.0 * float(rawstart)) / 100.0
                str_ba = str(bm0)
                max_ba = len(str_ba)
                start_ba = str_ba.find('.', 0)
                str_ba = str_ba[start_ba:max_ba]
                max_ba = len(str_ba)
                if max_ba < 3:
                    strItem = strItem + str(bm0) + "0 \t"
                else:
                    strItem = strItem + str(bm0) + space_bar + "\t"

                bm = int(100.0 * float(start)) / 100.0
                str_ba = str(bm)
                max_ba = len(str_ba)
                start_ba = str_ba.find('.', 0)
                str_ba = str_ba[start_ba:max_ba]
                max_ba = len(str_ba)
                if max_ba < 3:
                    strItem += str(bm) + "0 \t" + str(bm) + "0 \t"
                else:
                    strItem += str(bm) + space_bar + "\t" + str(bm) + space_bar + " \t"

                ba = int(1000.0 * float(age)) / 1000.0
                str_ba = str(ba)
                max_ba = len(str_ba)
                start_ba = str_ba.find('.', 0)
                str_ba = str_ba[start_ba:max_ba]
                max_ba = len(str_ba)
                if max_ba < 3:
                    strItem += str(ba) + "0 \t" + label 
                else:
                    strItem += str(ba) + space_bar + "\t" + label 
                ret = self.parent.agePanel.OnAddAgeToListAt(strItem, int(order))
                if ret >= 0:
                    self.AgeDataList.insert(int(order), ((self.SelectedAge, start, rawstart, age, name, label, type, 0.0)))

    def OnMouseUp(self, event):
        self.SetFocusFromKbd()
        pos = event.GetPosition().Get()

        if self.showMenu == True:
            self.selectedTie = -1
            self.activeTie = -1
            self.showMenu = False
            self.mouseoverCore = -1
            self.spliceTie = -1
            self.logTie = -1
            self.drag = 0
            self.mouseX = 0
            self.mouseY = 0
            return

        self.selectScroll = 0
        if self.grabScrollA == 1: # scroll A is composite *and* splice scrollbar if visible
            self.UpdateScrollA(pos)

            self.grabScrollA = 0
            self.selectScroll = 0 
            self.UpdateDrawing()
            return

        # scrollB is unused - was related to the now-removed ability to independently
        # scroll composite and splice areas
        if self.grabScrollB == 1:
            scroll_start = self.startDepthPix * 0.7
            scroll_y = pos[1] - scroll_start
            if scroll_y < scroll_start:
                scroll_y = scroll_start
            scroll_width = self.Height - (self.startDepthPix * 1.6)
            if scroll_y > scroll_width:
                scroll_y = scroll_width

            bmp, x, y = self.DrawData["Interface"]
            self.DrawData["Interface"] = (bmp, x, scroll_y)

            bmp, x, y = self.DrawData["Skin"]
            self.DrawData["Skin"] = (bmp, x, scroll_y)

            scroll_width = scroll_width - scroll_start 
            rate = old_div((scroll_y - scroll_start), (scroll_width * 1.0))
            self.SPrulerStartDepth = int(self.parent.ScrollMax * rate * 100.0) / 100.0

            self.grabScrollB = 0
            self.UpdateDrawing()
            return 

        # scrollC is the horizontal scrollbar at the bottom of the composite area
        if self.dragCompositeScroll:
            self.UpdateCompositeScroll(pos[0])
            self.dragCompositeScroll = False
            self.UpdateDrawing()
            return

        if self.dragSpliceScroll:
            self.UpdateSpliceScroll(pos[0])
            self.dragSpliceScroll = False
            self.UpdateDrawing()
            return

        if pos[0] >= self.splicerX:
            if self.HasDragCore(): # dragged core was dropped in splice area, add to splice
                if self.parent.sectionSummary is not None:
                    coreinfo = self.findCoreInfoByIndex(self.dragCore)
                    self.parent.AddSpliceCore(coreinfo)
                else:
                    self.parent.OnShowMessage("Error", "Section Summary is required to create a splice", 1)

                self.dragCore = -1
                self.UpdateDrawing()
                return
        else:
            self.dragCore = -1

        if self.selectScroll == 1:
            self.selectScroll = 0 
            return

        currentY = pos[1]
        if self.selectedTie >= 0: 
            tie = self.TieData[self.selectedTie]
            if self.mouseoverCore != tie.core:
                return

            tie.screenY = pos[1]
            tie.depth = self.getDepth(pos[1])
                
            self.mouseoverCore = tie.core # TODO: SelectedCoreAffine?
            self.selectedLastTie = self.selectedTie 
            self.GuideCore = []	
            # draw guide 
            self.OnDrawGuide()
            self.selectedTie = -1 

        selectedIntervalTie = self.parent.spliceManager.getSelectedTie()
        if selectedIntervalTie is not None:
            newdepth = self.getSpliceDepth(currentY)
            selectedIntervalTie.move(newdepth)
            selectedIntervalTie._setClampMessage("")
            self.parent.spliceManager.selectTie(None)
            self.parent.spliceManager.setDirty()
            self.parent.spliceIntervalPanel.UpdateUI()

        if pos[0] == self.mouseX and pos[1] == self.mouseY: # why this test?
            if len(self.TieData) >= 2: # max two ties
                return
            fixed = 1 if len(self.TieData) == 0 else 0
            print("Creating {} TieData for hole {}, core {}".format("fixed" if fixed == 1 else "movable", self.currentHole, self.mouseoverCore))
            newTie = CompositeTie(self.currentHole, self.mouseoverCore, self.currentStartX, pos[1], fixed, self.getDepth(pos[1]))
            self.TieData.append(newTie)

            if len(self.TieData) == 1:
                self.UpdateAffineTieCount(1)
            else: # we now have two ties, set up guide core, eval graph, etc
                self.activeTie = 1
                length = len(self.TieData) 
                fixedTie = self.TieData[length - 2]
                fixedY = self.getDepth(fixedTie.screenY)
                fixedX = fixedTie.hole
                self.guideCore = fixedTie.core

                movableTie = self.TieData[length - 1]
                shift = fixedTie.depth - movableTie.depth
                shiftx = (fixedTie.hole - movableTie.hole) * (self.holeWidth + 50) # shiftx is unused in OnUpdateGuideData...don't care about this self.holeWidth
                self.compositeDepth = fixedTie.depth
                y2 = fixedTie.depth
                y1 = movableTie.depth

                ciA = self.findCoreInfoByIndex(self.guideCore)
                ciB = self.findCoreInfoByIndex(movableTie.core)
                if ciA is not None and ciA.hole == ciB.hole:
                    self.parent.OnShowMessage("Error", "Composite ties cannot be made in the same hole.", 1)
                    self.ClearCompositeTies()
                elif not self.parent.affineManager.isLegalTie(ciB, ciA):
                    self.parent.OnShowMessage("Error", "Core {}{} is upstream in the tie chain.".format(ciB.hole, ciB.holeCore), 1)
                    self.ClearCompositeTies()
                else:
                    self.activeCore = self.mouseoverCore
                    self.OnUpdateGuideData(self.mouseoverCore, shiftx, shift)
                    self.parent.OnUpdateDepth(shift)
                    self.parent.TieUpdateSend(ciA.leg, ciA.site, ciA.hole, int(ciA.holeCore), ciB.hole, int(ciB.holeCore), y1, shift)
                    testret = self.EvaluateCorrelation(ciA.type, ciA.hole, int(ciA.holeCore), y2, ciB.type, ciB.hole, int(ciB.holeCore), y1)
                    if testret != "":
                        self.parent.OnAddFirstGraph(testret, y2, y1)
                    for data_item in self.range:
                        typeA = ciA.type
                        if data_item[0] == "Natural Gamma" and typeA == "NaturalGamma":
                            typeA = "Natural Gamma"
                        elif data_item[0] == "NaturalGamma" and typeA == "Natural Gamma":
                            typeA = "NaturalGamma"
                        if data_item[0] != typeA and data_item[0] != "splice" and data_item[0] != "log":
                            testret = self.EvaluateCorrelation(data_item[0], ciA.hole, int(ciA.holeCore), y2, data_item[0], ciB.hole, int(ciB.holeCore), y1)
                            if testret != "":
                                self.parent.OnAddGraph(testret, y2, y1)
                    self.parent.OnUpdateGraph()
                    self.UpdateAffineTieCount(len(self.TieData))

        self.mouseoverCore = -1
        self.spliceTie = -1
        self.logTie = -1
        self.drag = 0
        self.mouseX = 0
        self.mouseY = 0
        self.grabScrollA = 0
        self.grabScrollB = 0
        self.dragCompositeScroll = False
        self.dragSpliceScroll = False
        self.UpdateDrawing()

    # scrollA = vertical scrolling of the CoreArea (leftmost) region *and* the splice
    # region if enabled. 
    def UpdateScrollA(self, mousePos):
        scroll_start = self.startDepthPix * 0.7
        scroll_y = mousePos[1] - scroll_start
        scroll_width = self.Height - (self.startDepthPix * 1.6)
        if scroll_y < scroll_start:		 
            scroll_y = scroll_start
        if scroll_y > scroll_width:
            scroll_y = scroll_width

        for key, data in list(self.DrawData.items()):
            if key == "MovableInterface":
                bmp, x, y = data
                self.DrawData["MovableInterface"] = (bmp, x, scroll_y)

        if self.spliceWindowOn == 1:
            bmp, x, y = self.DrawData["MovableSkin"]
            self.DrawData["MovableSkin"] = (bmp, x, scroll_y)

        scroll_width = scroll_width - scroll_start
        rate = old_div((scroll_y - scroll_start), (scroll_width * 1.0))
        self.rulerStartDepth = int( self.parent.ScrollMax * rate * 100.0 ) / 100.0
        if self.parent.client != None:
            _depth = (self.rulerStartDepth + self.rulerEndDepth) / 2.0
            self.parent.client.send("jump_to_depth\t" + str(_depth) + "\n")

        if not self.independentScroll or self.spliceWindowOn == 0:
            # 3/10/2019 TODO? "Interface" seems to be redundant, we never actually draw
            # its bitmap (search on dc.DrawBitmap()) as we do for "Skin". Leaving for
            # now since it's harmless.
            bmp, x, y = self.DrawData["Interface"]
            self.DrawData["Interface"] = (bmp, x, scroll_y)

            bmp, x, y = self.DrawData["Skin"]
            self.DrawData["Skin"] = (bmp, x, scroll_y)

            self.SPrulerStartDepth = int(self.parent.ScrollMax * rate * 100.0) / 100.0

    def UpdateCompositeScroll(self, mousePosX):
        scroll_start = self.compositeX
        scroll_x = mousePosX
        if scroll_x < scroll_start:
            scroll_x = scroll_start

        # brg 9/28/2024:
        # After some experimentation, I have a better guess as to what's happening here.
        #
        # TL;DR: self.startDepthPix * 2.3 = 149.5. It seems to be an approximation of the horizontal
        # distance (in pixels) from the left edge of the horizontal scroll thumb to the start of the splice
        # plot area, when the thumb is at its rightmost limit in the scrollbar.
        #
        # startDepthPix was related to font size back in the day, but we've removed
        # the ability to adjust font size so startDepthPix will always be 65.0.
        # It is the vertical distance from the top of the client area to depth 0m in the plot area
        # if scrollbar A (depth scrolling) is at its upper limit. Because it's related to font size,
        # it sort of makes sense that startDepthPix also has horizontal meaning, as growing fonts would
        # also make the interface (e.g. depth scale ruler) wider. I remain utterly mystified by the 2.3
        # fudge factor's origin, but it works well enough.
        scroll_width = self.splicerX - (self.startDepthPix * 2.3) 
        if scroll_x > scroll_width:
            scroll_x = scroll_width

        bmp, x, y = self.DrawData["CompositeScroll"]
        self.DrawData["CompositeScroll"] = (bmp, scroll_x, y)

        scroll_width = scroll_width - scroll_start
        rate = old_div((scroll_x - scroll_start), (scroll_width * 1.0))
        self.minScrollRange = int(self.parent.CompositeScrollMax * rate)

    def UpdateSpliceScroll(self, mousePosX):
        # clamp splice scroll position to left edge of splice area
        splice_scroll_start = self.splicerX
        splice_scroll_x = splice_scroll_start if mousePosX < splice_scroll_start else mousePosX

        bmp, x, y = self.DrawData["SpliceScroll"]

        splice_scroll_width = self.Width - bmp.GetWidth()
        if splice_scroll_x > splice_scroll_width:
            splice_scroll_x = splice_scroll_width

        self.DrawData["SpliceScroll"] = (bmp, splice_scroll_x, y)

        splice_scroll_width -= splice_scroll_start
        splice_scroll_rate = old_div((splice_scroll_x - splice_scroll_start), splice_scroll_width * 1.0)
        self.minSpliceScrollRange = int(self.parent.SpliceScrollMax * splice_scroll_rate)

    def InitSpliceScrollThumbPosition(self):
        if "SpliceScroll" not in self.DrawData:
            return
        bmp, x, y = self.DrawData["SpliceScroll"]
        if x > self.splicerX:
            x = self.splicerX
            self.DrawData["SpliceScroll"] = (bmp, x, y)

    def UpdateSpliceScrollThumb(self, originalSplicerX, originalWidth):
        # Due to Correlator's horrific spaghetti initialization process, this method
        # can sometimes be called before DrawData is init'd, guard against errors.
        if "SpliceScroll" not in self.DrawData:
            return
        bmp, x, y = self.DrawData["SpliceScroll"]
        original_splice_width = originalWidth - bmp.GetWidth() - originalSplicerX
        new_splice_width = self.Width - bmp.GetWidth() - self.splicerX
        relative_thumb_pos = (x - originalSplicerX) / original_splice_width
        new_thumb_pos = int(relative_thumb_pos * new_splice_width)
        splice_scroll_x = self.splicerX + new_thumb_pos
        self.DrawData["SpliceScroll"] = (bmp, splice_scroll_x, y)

    def OnUpdateTie(self, tieType):
        tieData = None
        if tieType == 1: # composite
            rulerStart = self.rulerStartDepth
            tieData = self.TieData
        else: 
            rulerStart = self.SPrulerStartDepth
            tieData = self.SpliceTieData

        max = len(tieData)
        if tieType == 1 and max == 2: # composite tie
            y2 = self.getDepth(tieData[0].screenY)
            n1 = tieData[0].core
            y1 = self.getDepth(tieData[1].screenY)
            n2 = tieData[1].core
        elif max != 0 and max % 2 == 0: # splice tie
            length = len(tieData)
            y2 = tieData[length - 2].depth #(tieData[length - 2].y - self.startDepthPix) / self.pixPerMeter + rulerStart
            n1 = tieData[length - 2].core
            y1 = tieData[length - 1].depth #(tieData[length - 1].y - self.startDepthPix) / self.pixPerMeter + rulerStart
            n2 = tieData[length - 2].core
        else: # no tie to update, bail
            return

        ciA = self.findCoreInfoByIndex(n1)
        ciB = self.findCoreInfoByIndex(n2)

        if tieType == 1: # composite
            shift = y2 - y1
            self.parent.TieUpdateSend(ciA.leg, ciA.site, ciA.hole, int(ciA.holeCore), ciB.hole, int(ciB.holeCore), y1, shift)

        flag = self.parent.showELDPanel | self.parent.showCompositePanel | self.parent.showSplicePanel
        if ciA != None and ciB != None and flag == 1:
            if tieType == 1: # composite
                testret = self.EvaluateCorrelation(ciA.type, ciA.hole, int(ciA.holeCore), y2, ciB.type, ciB.hole, int(ciB.holeCore), y1)
            else:
                testret = py_correlator.evalcoef_splice(ciB.type, ciB.hole, int(ciB.holeCore), y1, y2)
            if testret != "":
                self.parent.OnAddFirstGraph(testret, y2, y1)
            for data_item in self.range:
                typeA = ciA.type
                if data_item[0] == "Natural Gamma" and typeA == "NaturalGamma":
                    typeA = "Natural Gamma"
                elif data_item[0] == "NaturalGamma" and typeA == "Natural Gamma":
                    typeA = "NaturalGamma"
                if data_item[0] != typeA and data_item[0] != "splice" and data_item[0] != "log":
                    if tieType == 1: # composite
                        testret = self.EvaluateCorrelation(data_item[0], ciA.hole, int(ciA.holeCore), y2, data_item[0], ciB.hole, int(ciB.holeCore), y1)
                    else:
                        testret = py_correlator.evalcoef_splice(data_item[0], ciB.hole, int(ciB.holeCore), y1, y2)
                    if testret != "":
                        self.parent.OnAddGraph(testret, y2, y1)
            self.parent.OnUpdateGraph()


    # 9/20/2012 brgtodo: duplication
    def OnMotion(self, event):
        pos = event.GetPosition().Get()

        if self.grabScrollA == 1:
            self.UpdateScrollA(pos)
            self.UpdateDrawing()
            return 

        if self.grabScrollB == 1:
            scroll_start = self.startDepthPix * 0.7
            scroll_y = pos[1] - scroll_start
            if scroll_y < scroll_start:
                scroll_y = scroll_start
            scroll_width = self.Height - (self.startDepthPix * 1.6)
            if scroll_y > scroll_width:
                scroll_y = scroll_width

            bmp, x, y = self.DrawData["Interface"]
            self.DrawData["Interface"] = (bmp, x, scroll_y)

            bmp, x, y = self.DrawData["Skin"]
            self.DrawData["Skin"] = (bmp, x, scroll_y)

            scroll_width = scroll_width - scroll_start
            rate = old_div((scroll_y - scroll_start), (scroll_width * 1.0))
            self.SPrulerStartDepth = int(self.parent.ScrollMax * rate * 100.0) / 100.0
            self.UpdateDrawing()
            return 

        if self.dragCompositeScroll:
            self.UpdateCompositeScroll(pos[0])
            self.UpdateDrawing()
            return
        
        if self.dragSpliceScroll:
            self.UpdateSpliceScroll(pos[0])
            self.UpdateDrawing()
            return

        self.OnMainMotion(event)

    def OnMainMotion(self, event):
        if self.showMenu == True:
            return

        if self.MousePos is not None:
            self.LastMousePos = self.MousePos

        pos = event.GetPosition().Get()
        self.MousePos = pos 
        # if cursor position hasn't actually changed, avoid a needless redraw
        if self.LastMousePos is not None:
            x, y = self.MousePos
            lx, ly = self.LastMousePos
            if lx - x == 0 and ly - y == 0:
                return

        got = 0
        # brg 1/29/2014: if mouse is over options panel, don't bother proceeding - the draw
        # commands change nothing and cause GUI elements to respond sluggishly
        if self.MousePos[0] > self.Width:
            return

        # draw info for current mouseover core
        if "CoreArea" in self.DrawData and self.MousePos[0] < self.splicerX:
            for area in self.DrawData["CoreArea"]:
                coreInfo, rect, hole_idx = area
                if rect.Contains(wx.Point(pos[0], pos[1])):
                    got = 1
                    self.mouseoverCore = coreInfo.core

                    hc = self.layoutManager.getColumnAtPos(pos[0])
                    overPlot = hc.getColumnTypeAtPos(pos[0]) == ColumnType.Plot
                    plotOffset = hc.getColumnOffset(ColumnType.Plot) if overPlot else 0
                    # print("Over column {}, subcolumn {}".format(hc.columnKey(), hc.getColumnTypeAtPos(pos[0])))

                    mouseInfo = [(coreInfo, pos[0], pos[1], rect.GetX() + plotOffset, overPlot)]
                    self.DrawData["MouseInfo"] = mouseInfo
                    break

        # draw info for mouseover splice core
        if self.MousePos[0] > self.splicerX:
            ydepth = self.getSpliceDepth(pos[1])
            interval = self.parent.spliceManager.getIntervalAtDepth(ydepth)
            if interval is not None:
                splicemin, splicemax = self._GetSpliceRange(interval.coreinfo.type)
                spliceCoef = self._GetSpliceRangeCoef(splicemin, splicemax)
                img_wid = self.GetSpliceAreaImageWidth()
                plotLeftX = self.splicerX + self.layoutManager.plotLeftMargin + img_wid
                miTuple = (interval.coreinfo, pos[0], pos[1], plotLeftX, pos[0] >= plotLeftX)
                self.DrawData["MouseInfo"] = [miTuple]
                got = 1 # must set or DrawData["MouseInfo"] will be cleared

        if self.drag == 1:
            got = 1 
            
        # adjust SpliceIntervalTie's depth if one is selected
        siTie = self.parent.spliceManager.getSelectedTie()
        if siTie is not None:
            depth = self.getSpliceDepth(pos[1])
            siTie.move(depth)
            self.UpdateSpliceEvalPlot()
            self.UpdateDrawing()
            return

        # dragging to adjust movable affine tie
        if self.selectedTie >= 0:
            movableTie = self.TieData[self.selectedTie]
            if self.mouseoverCore != movableTie.core:
                return

            fixedTie = self.TieData[self.selectedTie - 1]
            y1 = self.getDepth(pos[1])
            y2 = fixedTie.depth
            shift = y2 - y1

            ciA = self.findCoreInfoByIndex(movableTie.core)
            ciB = self.findCoreInfoByIndex(fixedTie.core)

            if self.parent.showCompositePanel == 0:
                data = self.TieData[self.selectedTie]
                data.screenY = pos[1]
                data.depth = y1
            
            # Notify Corelyzer of modified tie point
            self.parent.TieUpdateSend(ciA.leg, ciA.site, ciB.hole, int(ciB.holeCore), ciA.hole, int(ciA.holeCore), y1, shift)

            # Update evaluation graph
            flag = self.parent.showELDPanel | self.parent.showCompositePanel | self.parent.showSplicePanel
            if ciA.hole != None and ciB.hole != None and flag == 1:
                testret = self.EvaluateCorrelation(ciB.type, ciB.hole, int(ciB.holeCore), y2, ciA.type, ciA.hole, int(ciA.holeCore), y1)
                if testret != "":
                    data = self.TieData[self.selectedTie]
                    data.screenY = pos[1]
                    data.depth = y1
                    self.parent.OnUpdateDepth(shift)
                    self.parent.OnAddFirstGraph(testret, y2, y1)

                # update evaluation plot for datatypes other than the type being shifted
                for data_item in self.range:
                    typeA = ciA.type
                    if data_item[0] == "Natural Gamma" and typeA == "NaturalGamma":
                        typeA = "Natural Gamma"
                    elif data_item[0] == "NaturalGamma" and typeA == "Natural Gamma":
                        typeA = "NaturalGamma"
                    if data_item[0] != typeA and data_item[0] != "splice" and data_item[0] != "log":
                        testret = self.EvaluateCorrelation(data_item[0], ciB.hole, int(ciB.holeCore), y2, data_item[0], ciA.hole, int(ciA.holeCore), y1)
                        if testret != "":
                            self.parent.OnAddGraph(testret, y2, y1)
                self.parent.OnUpdateGraph()

            self.mouseoverCore = movableTie.core # TODO: SelectedCoreAffine?
            self.GuideCore = []
            # draw guide
            self.OnDrawGuide()
            got = 1

        # Dragging composite/splice area divider scrollbar?
        if self.selectScroll == 1 and self.grabScrollA == 0 and not self.dragCompositeScroll:
            if pos[0] >= 180 and pos[0] <= (self.Width - 100):
                scroll_widthA = self.splicerX - (self.startDepthPix * 2.3) - self.compositeX 
                originalSplicerX = self.splicerX
                self.splicerX = pos[0]

                # update position of scrollbar thumbs to reflect changing scroll area widths
                bmp, x, y = self.DrawData["CompositeScroll"]
                scroll_rate = old_div((x - self.compositeX), (scroll_widthA * 1.0))
                scroll_widthA = self.splicerX - (self.startDepthPix * 2.3) - self.compositeX 
                scroll_x = scroll_widthA * scroll_rate
                scroll_x += self.compositeX
                self.DrawData["CompositeScroll"] = (bmp, scroll_x, y)

                self.UpdateSpliceScrollThumb(originalSplicerX, self.Width)

        # store data needed to draw "ghost" of core being dragged:
        # x is the current mouse x, y is the offset between current and original mouse y
        if self.HasDragCore():
            if self.DrawData["DragCore"] == []:
                self.DrawData["DragCore"] = DragCoreData(pos[0], pos[1])
            else:
                self.DrawData["DragCore"].update(pos[0], pos[1])
        else:
            self.DrawData["DragCore"] = []

        if got == 0:
            self.DrawData["MouseInfo"] = []
            self.mouseoverCore = -1 

        self.UpdateDrawing()

    # Update splice eval plot for current splice tie - if none is currently selected,
    # draw from last-selected tie.
    def UpdateSpliceEvalPlot(self):
        siTie = self.parent.spliceManager.getSelectedTie()
        if siTie is None:
            siTie = self.lastSiTie

        if siTie is not None and siTie.isTied():
            self.lastSiTie = siTie
            sortedInts = sorted([siTie.interval, siTie.adjInterval], key=lambda i:i.getTop())
            topInterval = sortedInts[0]
            botInterval = sortedInts[1]
            h1, c1, t1 = topInterval.triad()
            h2, c2, t2 = botInterval.triad()
            depth = siTie.depth()
            evalResult = self.EvaluateCorrelation(t1, h1, int(c1), depth, t2, h2, int(c2), depth)
            try: # attempt to parse evalResult into datapoints for eval graph
                self.parent.OnAddFirstGraph(evalResult, depth, depth)
            except ValueError:
                print("Error parsing evalcoef() results, do cores have data at depth {}?".format(depth))
                return
            
            if t1 != t2: # if intervals' datatypes differ, plot eval for second type
                try:
                    evalResult = self.EvaluateCorrelation(t2, h1, int(c1), depth, t2, h2, int(c2), depth)
                    self.parent.OnAddGraph(evalResult, depth, depth)
                except ValueError:
                    print("Error parsing evalcoef() results for mixed datatypes, do cores have data at depth {}?".format(depth))
                    return
            
            self.parent.OnUpdateGraph()