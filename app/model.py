import wx

from importManager import py_correlator

import dialog

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

def MakeRangeString(min, max):
	return "Range: (" + min + ", " + max + ")"

def MakeDecimateString(dec):
	return "Decimate: " + str(dec)

""" Generate a range list - [name, min, max, range coefficient, smoothing type, continuous or discrete] -
from the provided HoleData or DownholeLogTable """
def MakeRangeList(data, name):
	if not isinstance(data, HoleData) and not isinstance(data, DownholeLogTable):
		print "MakeRangeList() expects HoleData or DownholeLogData"
		return []
	min = float(data.min)
	max = float(data.max)
	coef = max - min
	if isinstance(data, HoleData):
		continuous = data.holeSet.continuous
		smooth = data.holeSet.smooth
	else: # DownholeLogTable
		continuous = True
		smooth = data.smooth
	return [name, min, max, coef, smooth, continuous]

# FileMetadata a better name?
class TableData:
	def __init__(self):
		self.file = ''
		self.updatedTime = ''
		self.byWhom = ''
		self.enable = False
		self.origSource = ''

	def __repr__(self):
		return "%s %s %s %s %s" % (self.file, self.updatedTime, self.byWhom, str(self.enable), self.origSource)

	def FromTokens(self, tokens):
		self.file = tokens[1]
		self.updatedTime = tokens[2]
		self.byWhom = tokens[3]
		self.enable = ParseEnableToken(tokens[4])
		if len(tokens) > 5 and tokens[5] != '-':
			self.origSource = tokens[5]

	def GetEnableStr(self):
		return "Enable" if self.enable else "Disable"

	def IsEnabled(self):
		return self.enable

class HoleData(TableData):
	def __init__(self, name):
		TableData.__init__(self)
		self.name = name
		self.dataName = '[no dataName]'
		self.depth = '[no depth]'
		self.min = '[no min]'
		self.max = '[no max]'
		self.data = '[no data]'
		self.holeSet = None # parent HoleSet
		self.gui = None # HoleGUI

	def __repr__(self):
		return "Hole %s: %s %s %s %s %s %s %s %s %s %s" % (self.name, self.dataName, self.depth, self.min, self.max, self.data, str(self.enable), self.file, self.origSource, self.updatedTime, self.byWhom)

class HoleSet:
	def __init__(self, type):
		self.holes = {} # dict of HoleData objects
		self.cullTable = None # appears there can only be one of these per HoleSet
		self.type = type # built-in type string e.g. NaturalGamma, Pwave, or Other
		self.continuous = True # if False, discrete
		self.decimate = '[no decimate]' # numeric?
		self.smooth = '[no smooth]'
		self.min = '[no min]'
		self.max = '[no max]'
		self.site = None # parent SiteData
		self.gui = None # HoleSetGUI

	def __repr__(self):
		return "HoleSet %s: %s, %s %s %s %s %s" % (self.type, self.GetCullFile(), self.continuous, str(self.decimate), self.smooth, self.min, self.max)

	def dump(self):
		print self
		for hole in self.holes.values():
			print hole
		if self.HasCull():
			print self.cullTable
	
	def AddHole(self, hole):
		if isinstance(hole, HoleData) and hole.name not in self.holes:
			hole.holeSet = self
			self.holes[hole.name] = hole

	def HasCull(self):
		return self.cullTable != None

	def EnableCull(self, enable=True):
		if self.HasCull():
			self.cullTable.enable = enable

	def IsCullEnabled(self):
		result = False
		if self.HasCull():
			result = self.cullTable.IsEnabled()
		return result

	def GetCullFile(self):
		if self.HasCull():
			return self.cullTable.file
		else:
			return "[no cull table]"

	# return string for use in title of a hole set's CollapsiblePane
	def GetTitleStr(self):
		return self.type + " - Range: (" + self.min + ", " + self.max + "); " + self.continuous + "; " + "Decimate: " + str(self.decimate) + "; " + "Smoothing: " + self.smooth

class SiteData:
	def __init__(self, name):
		self.name = name
		self.holeSets = {}
		self.affineTables = []
		self.spliceTables = []
		self.eldTables = []
		self.logTables = []
		self.stratTables = []
		self.ageTables = []
		self.seriesTables = [] # timeseries
		self.imageTables = []
		self.affineGui = None
		self.spliceGui = None
		self.eldGui = None

	def __repr__(self):
		return "SiteData %s" % (self.name)

	def dump(self):
		print self
		for hs in self.holeSets.values():
			hs.dump()
		for at in self.affineTables:
			print at
		for st in self.spliceTables:
			print st
		for et in self.eldTables:
			print et
		for lt in self.logTables:
			print lt
		for st in self.stratTables:
			print st
		for at in self.ageTables:
			print at
		for st in self.seriesTables:
			print st
		for it in self.imageTables:
			print it

	def SyncToGui(self):
		for hs in self.holeSets.values():
			hs.gui.SyncToGui()
			for hole in hs.holes.values():
				hole.gui.SyncToGui()
		self.affineGui.SyncToGui()
		self.spliceGui.SyncToGui()
		self.eldGui.SyncToGui()
		for log in self.logTables:
			log.gui.SyncToGui()

	def SyncToData(self):
		for hs in self.holeSets.values():
			hs.gui.SyncToData()
			for hole in hs.holes.values():
				hole.gui.SyncToData()
		self.affineGui.SyncToData()
		self.spliceGui.SyncToData()
		self.eldGui.SyncToData()
		for log in self.logTables:
			log.gui.SyncToData()

	def AddHoleSet(self, type):
		if type not in self.holeSets:
			self.holeSets[type] = HoleSet(type)

	def AddHole(self, type, hole):
		if type in self.holeSets:
			self.holeSets[type].site = self
			self.holeSets[type].AddHole(hole)

	""" return currently enabled AffineTable if there is one """
	def GetAffine(self):
		return self.GetEnabledTable(self.affineTables)

	""" return currently enabled SpliceTable if there is one """
	def GetSplice(self):
		return self.GetEnabledTable(self.spliceTables)
	
	""" return currently enabled EldTable if there is one """
	def GetEld(self):
		return self.GetEnabledTable(self.eldTables)

	""" generic "find the enabled table" routine """
	def GetEnabledTable(self, tableList):
		result = None
		for tab in tableList:
			if tab.enable:
				result = tab
		return result

	def SetDecimate(self, type, decimate):
		if type in self.holeSets:
			self.holeSets[type].decimate = decimate
		else:
			print "Couldn't find type " + type + " in site " + self.name + " holeSets"

	def SetSmooth(self, type, smoothStr):
		if type in self.holeSets:
			self.holeSets[type].smooth = smoothStr
		else:
			print "Couldn't find type " + type + " in site " + self.name + " holeSets"

	def GetDir(self):
		return self.name + '/'

class AffineData(TableData):
	def __init__(self):
		TableData.__init__(self)
	def __repr__(self):
		return "AffineTable " + TableData.__repr__(self)
	def FromTokens(self, tokens):
		TableData.FromTokens(self, tokens)
	def GetName(self):
		return "Affine"

class SpliceData(TableData):
	def __init__(self):
		TableData.__init__(self)
	def __repr__(self):
		return "SpliceTable " + TableData.__repr__(self)
	def FromTokens(self, tokens):
		TableData.FromTokens(self, tokens)
	def GetName(self):
		return "Splice"

class EldData(TableData):
	def __init__(self):
		TableData.__init__(self)
	def __repr__(self):
		return "EldTable " + TableData.__repr__(self)
	def FromTokens(self, tokens):
		TableData.FromTokens(self, tokens)
	def GetName(self):
		return "ELD"

# "Universal" cull table i.e. applies to more than one HoleSet?
# Only available through Saved Tables tree item, and commented
# out, this may never have been implemented.
class UniCullTable(TableData):
	def __init__(self):
		TableData.__init__(self)
	def __repr__(self):
		return "UniCullTable " + TableData.__repr__(self)
	def FromTokens(self, tokens):
		TableData.FromTokens(self, tokens)
	def GetName(self):
		return "Univeral Cull Table"

# cull table that applies to a single HoleSet
class CullTable(TableData):
	def __init__(self):
		TableData.__init__(self)
	def __repr__(self):
		return "CullTable " + TableData.__repr__(self)
	def FromTokens(self, tokens):
		TableData.FromTokens(self, tokens)
	def GetName(self):
		return "Cull Table"

class StratTable(TableData):
	def __init__(self):
		TableData.__init__(self)
	def __repr__(self):
		return "StratTable " + TableData.__repr__(self)
	def FromTokens(self, tokens):
		TableData.FromTokens(self, tokens)
	def GetName(self):
		return "Stratigraphy" # brgtodo - correct

class AgeTable(TableData):
	def __init__(self):
		TableData.__init__(self)
	def __repr__(self):
		return "AgeTable " + TableData.__repr__(self)
	def FromTokens(self, tokens):
		TableData.FromTokens(self, tokens)
	def GetName(self):
		return "Age/Depth"

class SeriesTable(TableData):
	def __init__(self):
		TableData.__init__(self)
	def __repr__(self):
		return "SeriesTable " + TableData.__repr__(self)
	def FromTokens(self, tokens):
		TableData.FromTokens(self, tokens)
	def GetName(self):
		return "Age"

class ImageTable(TableData):
	def __init__(self):
		TableData.__init__(self)
	def __repr__(self):
		return "ImageTable " + TableData.__repr__(self)
	def FromTokens(self, tokens):
		TableData.FromTokens(self, tokens)
	def GetName(self):
		return "Image Table"

class DownholeLogTable(TableData):
	def __init__(self):
		TableData.__init__(self)
		self.dataIndex = '[no dataIndex]'
		self.dataType = '[no dataType]'
		self.min = '[no min]'
		self.max = '[no max]'
		self.decimate = '[no decimate]'
		self.smooth = '[no smooth]'
		self.gui = None # LogTableGUI

	def __repr__(self):
		return "DownholeLogTable " + "%s %s %s %s %s %s %s %s %s %s %s" % (self.file, self.updatedTime, self.byWhom, self.origSource, self.dataIndex, self.enable, self.dataType, self.min, self.max, str(self.decimate), self.smooth)

	def GetName(self):
		return self.dataType

	def FromTokens(self, tokens):
		self.file = tokens[1]
		self.updatedTime = tokens[2]
		self.byWhom = tokens[3]
		self.origSource = tokens[4]
		self.dataIndex = tokens[5]
		self.enable = ParseEnableToken(tokens[6])
		self.dataType = tokens[7]
		if len(tokens) >= 10:
			self.min = tokens[8]
			self.max = tokens[9]
		if len(tokens) >= 11:
			self.decimate = ParseDecimateToken(tokens[10])
		if len(tokens) >= 12:
			self.smooth = tokens[11]

class DBView:
	def __init__(self, parent, dataFrame, parentPanel, siteList):
		self.parent = parent # 1/6/2014 brg: Don't like this naming...app?
		self.dataFrame = dataFrame # old DB Manager DataFrame
		self.parentPanel = parentPanel # wx.Panel
		self.panes = [] # wx.CollapsiblePanes - retain to re-Layout() as needed
		self.menu = None # action menu

		self.InitUI(siteList)
		self.InitMenus()

		self.UpdateView(self.GetCurrentSite())

	def InitUI(self, siteList):
		self.sitePanel = wx.Panel(self.parentPanel, -1)
		self.sitePanel.SetSizer(wx.BoxSizer(wx.HORIZONTAL))
		siteLabel = wx.StaticText(self.sitePanel, -1, "Current Site: ", style=wx.BOLD)
		slFont = siteLabel.GetFont()
		slFont.SetWeight(wx.BOLD)
		siteLabel.SetFont(slFont)
		self.currentSite = wx.Choice(self.sitePanel, -1)
		self.loadButton = wx.Button(self.sitePanel, -1, "Load")

		self.sitePanel.GetSizer().Add(siteLabel, 0, border=5, flag=wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER_VERTICAL)
		self.sitePanel.GetSizer().Add(self.currentSite, 0, border=5, flag=wx.TOP|wx.BOTTOM|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL)
		self.sitePanel.GetSizer().Add(self.loadButton, 0, border=5, flag=wx.TOP|wx.BOTTOM|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL)
		self.parentPanel.GetSizer().Add(self.sitePanel, 0, border=10, flag=wx.BOTTOM | wx.LEFT)

		self.dataPanel = wx.Panel(self.parentPanel, -1)
		self.dataPanel.SetSizer(wx.BoxSizer(wx.VERTICAL))
		self.dataPanel.SetBackgroundColour('white')
		self.parentPanel.GetSizer().Add(self.dataPanel, 0, border=10, flag=wx.BOTTOM | wx.LEFT)

		self.UpdateSites(siteList)
		self.parentPanel.Bind(wx.EVT_CHOICE, self.SiteChanged, self.currentSite)
		self.parentPanel.Bind(wx.EVT_BUTTON, self.LoadPressed, self.loadButton)

	def InitMenus(self):
		# master dictionary of all menu items
		self.menuIds = {'Load': 1,
						'View': 2,
						'Export': 3,
						'Enable All': 101,
						'Disable All': 102}

		self.holeMenuItems = ['Load', 'View', 'Export']
		self.holeSetMenuItems = ['Load', 'Export', 'Enable All', 'Disable All']

	def BuildMenu(self, itemList):
		self.menu = wx.Menu()
		for key in itemList:
			self.menu.Append(self.menuIds[key], key)

	def NewPanel(self, toPanel):
		panel = wx.Panel(toPanel, -1)
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		panel.SetSizer(sizer)
		panel.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel) # forward all mousewheel events to parent
		return panel, sizer

	def AddHoleSetRow(self, toPanel, holeSet):
		panel, sizer = self.NewPanel(toPanel)

		holeSet.gui = HoleSetGUI(holeSet, panel)

		sizer.Add(wx.StaticText(panel, -1, "[All Holes]", size=(75,-1), style=wx.ALIGN_CENTRE), 0, border=10, flag=wx.RIGHT|wx.LEFT|wx.BOTTOM)
		#button = wx.Button(panel, -1, "Actions...")
		sizer.Add(holeSet.gui.actionButton, 0)
		sizer.AddSpacer((85,-1))
		#sizer.Add(wx.StaticText(panel, -1, "Range: (" + holeSet.min + ", " + holeSet.max + ")"), 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.Add(holeSet.gui.rangeText, 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.AddSpacer((5,-1))
		sizer.Add(holeSet.gui.continuousChoice, 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.AddSpacer((5,-1))
		sizer.Add(holeSet.gui.decimateText, 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		#sizer.Add(wx.StaticText(panel, -1, "Decimate: " + str(holeSet.decimate)), 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.AddSpacer((5,-1))
		sizer.Add(holeSet.gui.smoothText, 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		#sizer.Add(wx.StaticText(panel, -1, holeSet.smooth), 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.AddSpacer((5,-1))
		
		sizer.Add(holeSet.gui.cullEnabledCb, 0, border=5, flag=wx.LEFT|wx.BOTTOM)

		panel.Bind(wx.EVT_BUTTON, lambda event, args=holeSet: self.PopActionsMenu(event, args), holeSet.gui.actionButton)
		panel.Bind(wx.EVT_MENU, lambda event, args=holeSet: self.HandleHoleSetMenu(event, args))
		#panel.Bind(wx.EVT_MENU, lambda event, args=holeSet: self.HandleHoleSetMenu(event, args), self.loadItem)
		#panel.Bind(wx.EVT_MENU, lambda event, args=holeSet: self.HandleHoleSetMenu(event, args), self.viewItem)
		#panel.Bind(wx.EVT_MENU, lambda event, args=holeSet: self.HandleHoleSetMenu(event, args), self.enableAllItem)
		#panel.Bind(wx.EVT_MENU, lambda event, args=holeSet: self.HandleHoleSetMenu(event, args), self.disableAllItem)

		toPanel.GetSizer().Add(panel)

	def AddHoleRow(self, toPanel, hole):
		panel, sizer = self.NewPanel(toPanel)

		hole.gui = HoleGUI(hole, panel)

		sizer.Add(wx.StaticText(panel, -1, hole.name, size=(75,-1), style=wx.ALIGN_CENTRE), 0, border=10, flag=wx.RIGHT|wx.LEFT|wx.BOTTOM)
		button = wx.Button(panel, -1, "Actions...")
		sizer.Add(button, 0, border=5, flag=wx.BOTTOM)
		sizer.Add(hole.gui.enabledCb, 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.Add(wx.StaticText(panel, -1, "Range: (" + hole.min + ", " + hole.max + ")"), 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.Add(wx.StaticText(panel, -1, "File: " + hole.file), 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.Add(wx.StaticText(panel, -1, "Last updated: " + hole.updatedTime), 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.Add(wx.StaticText(panel, -1, "By: " + hole.byWhom), 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.Add(wx.StaticText(panel, -1, "Source: " + hole.origSource), 0, border=5, flag=wx.LEFT|wx.BOTTOM)

		panel.Bind(wx.EVT_BUTTON, lambda event, args=hole: self.PopActionsMenu(event, args), button)
		panel.Bind(wx.EVT_MENU, lambda event, args=hole: self.HandleHoleMenu(event, args))
		#panel.Bind(wx.EVT_MENU, lambda event, args=hole: self.HandleHoleMenu(event, args), self.loadItem)
		#panel.Bind(wx.EVT_MENU, lambda event, args=hole: self.HandleHoleMenu(event, args), self.viewItem)

		toPanel.GetSizer().Add(panel)

	def AddSavedTableRow(self, toPanel, site, name):
		panel, sizer = self.NewPanel(toPanel)
		
		gui = SavedTableGUI(site, name, panel)

		sizer.Add(wx.StaticText(panel, -1, name, size=(90,-1), style=wx.ALIGN_CENTRE), 0, border=10, flag=wx.RIGHT|wx.LEFT|wx.BOTTOM)
		button = wx.Button(panel, -1, "Actions...")
		sizer.Add(button, 0, border=5, flag=wx.BOTTOM|wx.LEFT)
		sizer.Add(gui.tableChoice, 0, border=5, flag=wx.BOTTOM|wx.LEFT)
		sizer.Add(gui.enabledCb, 0, border=5, flag=wx.BOTTOM|wx.LEFT)

		toPanel.GetSizer().Add(panel)

		return gui

	# for classes derived from TableData
	def AddTableRow(self, toPanel, table):
		panel, sizer = self.NewPanel(toPanel)
		
		sizer.Add(wx.StaticText(panel, -1, table.GetName(), size=(90,-1), style=wx.ALIGN_CENTRE), 0, border=10, flag=wx.RIGHT|wx.LEFT|wx.BOTTOM)
		button = wx.Button(panel, -1, "Actions...")
		sizer.Add(button, 0, border=5, flag=wx.BOTTOM)
		cb = wx.CheckBox(panel, -1, "Enabled", size=(80,-1))
		sizer.Add(cb, 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.Add(wx.StaticText(panel, -1, "File: " + table.file), 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.Add(wx.StaticText(panel, -1, "Last updated: " + table.updatedTime), 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.Add(wx.StaticText(panel, -1, "By: " + table.byWhom), 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.Add(wx.StaticText(panel, -1, "Source: " + table.origSource), 0, border=5, flag=wx.LEFT|wx.BOTTOM)

		toPanel.GetSizer().Add(panel)

	def AddLogTableRow(self, toPanel, table):
		panel, sizer = self.NewPanel(toPanel)

		table.gui = LogTableGUI(table, panel)

		sizer.Add(wx.StaticText(panel, -1, table.GetName(), size=(90,-1), style=wx.ALIGN_CENTRE), 0, border=10, flag=wx.RIGHT|wx.LEFT|wx.BOTTOM)
		button = wx.Button(panel, -1, "Actions...")
		sizer.Add(button, 0, border=5, flag=wx.BOTTOM)
		sizer.Add(table.gui.enabledCb, 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.Add(wx.StaticText(panel, -1, "File: " + table.file), 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.Add(wx.StaticText(panel, -1, "Last updated: " + table.updatedTime), 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.Add(wx.StaticText(panel, -1, "By: " + table.byWhom), 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.Add(wx.StaticText(panel, -1, "Source: " + table.origSource), 0, border=5, flag=wx.LEFT|wx.BOTTOM)

		panel.Bind(wx.EVT_CHECKBOX, self.LogCheckboxChanged, table.gui.enabledCb)

		toPanel.GetSizer().Add(panel)

	# 1/13/2014 brgtodo?: Retain GUI objects rather than rebuilding GUI whenever site changes?
	def UpdateView(self, site):
		self.panes = []
		self.dataPanel.GetSizer().Clear(True)

		if site == None:
			return
		
		# Add Holes
		for hsKey in sorted(site.holeSets.keys()): # sort by holeset type
			hs = site.holeSets[hsKey]
			hsPane = wx.CollapsiblePane(self.dataPanel, -1, hs.type, style=wx.CP_NO_TLW_RESIZE)
			hsPane.GetPane().SetSizer(wx.BoxSizer(wx.VERTICAL))
			self.dataPanel.GetSizer().Add(hsPane, 0, border=5, flag=wx.ALL)
			self.dataPanel.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.PaneChanged, hsPane)
			self.panes.append(hsPane)
			self.AddHoleSetRow(hsPane.GetPane(), hs)
			for holeKey in sorted(hs.holes.keys()):
				hole = hs.holes[holeKey]
				self.AddHoleRow(hsPane.GetPane(), hole)

		# Saved Tables (Affine, ELD, Splice)
		stPane = wx.CollapsiblePane(self.dataPanel, -1, "Saved Tables", style=wx.CP_NO_TLW_RESIZE)
		stPane.GetPane().SetSizer(wx.BoxSizer(wx.VERTICAL))
		self.dataPanel.GetSizer().Add(stPane, 0, border=5, flag=wx.ALL) # brgtodo: expand necessary?
		self.dataPanel.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.PaneChanged, stPane)
		self.panes.append(stPane)

		site.affineGui = self.AddSavedTableRow(stPane.GetPane(), site, "Affine")
		site.spliceGui = self.AddSavedTableRow(stPane.GetPane(), site, "Splice")
		site.eldGui = self.AddSavedTableRow(stPane.GetPane(), site, "ELD")

		ltPane = wx.CollapsiblePane(self.dataPanel, -1, "Downhole Logs", style=wx.CP_NO_TLW_RESIZE)
		ltPane.GetPane().SetSizer(wx.BoxSizer(wx.VERTICAL))
		self.dataPanel.GetSizer().Add(ltPane, 0, border=5, flag=wx.ALL) # brgtodo: expand necessary?
		self.dataPanel.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.PaneChanged, ltPane)
		self.panes.append(ltPane)
		for lt in site.logTables:
			self.AddLogTableRow(ltPane.GetPane(), lt)

		amPane = wx.CollapsiblePane(self.dataPanel, -1, "Age Models", style=wx.CP_NO_TLW_RESIZE)
		amPane.GetPane().SetSizer(wx.BoxSizer(wx.VERTICAL))
		self.dataPanel.GetSizer().Add(amPane, 0, border=5, flag=wx.ALL) # brgtodo: expand necessary?
		self.dataPanel.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.PaneChanged, amPane)
		self.panes.append(amPane)
		for at in site.ageTables:
			self.AddTableRow(amPane.GetPane(), at)
		for st in site.seriesTables:
			self.AddTableRow(amPane.GetPane(), st)

		# Forward mousewheel events to parent - seems like there ought to be an easier way...
		for pane in self.panes:
			pane.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel)
		self.dataPanel.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel)

		# refresh layout
		for pane in self.panes:
			if len(pane.GetPane().GetSizer().GetChildren()) > 0:
				pane.Expand()
		self.PaneChanged(evt=None) # force re-layout

	def OnMouseWheel(self, event):
		self.parentPanel.GetEventHandler().ProcessEvent(event)
		event.Skip()

	def UpdateSites(self, siteList):
		self.currentSite.Clear()
		for site in siteList:
			self.currentSite.Append(site.name, clientData=site)
		
		# brg 4/10/2014: Must explicitly set a current selection on Windows 
		if self.currentSite.GetCount() > 0:
			self.currentSite.SetSelection(0)

	def SiteChanged(self, evt):
		siteIndex = self.currentSite.GetSelection()
		curSite = self.currentSite.GetClientData(siteIndex)
		if curSite != None:
			self.UpdateView(curSite)

	""" Load all enabled holes """
	def LoadPressed(self, evt):
		siteIndex = self.currentSite.GetSelection()
		curSite = self.currentSite.GetClientData(siteIndex)
		curSite.SyncToGui()
		holesToLoad = []
		for holeSet in curSite.holeSets.values():
			for hole in holeSet.holes.values():
				if hole.enable:
					holesToLoad.append(hole)
		if len(holesToLoad) > 0:
			self.LoadHoles(holesToLoad)

	""" Ensure only one log Enabled checkbox is checked at a time """
	def LogCheckboxChanged(self, evt):
		siteIndex = self.currentSite.GetSelection()
		curSite = self.currentSite.GetClientData(siteIndex)
		changedCb = evt.GetEventObject()
		newState = changedCb.GetValue()
		for log in curSite.logTables:
			if log.gui.enabledCb != changedCb and newState == True:
				log.gui.enabledCb.SetValue(False)

	def PaneChanged(self, evt):
		self.parentPanel.Layout()
		self.dataPanel.Layout()
		for cp in self.panes:
			cp.GetPane().Layout()
		self.parentPanel.FitInside() # show/hide scrollbar if necessary

	def PopActionsMenu(self, evt, obj):
		if isinstance(obj, HoleData):
			self.BuildMenu(self.holeMenuItems)
		elif isinstance(obj, HoleSet):
			self.BuildMenu(self.holeSetMenuItems)
			
		evt.GetEventObject().PopupMenu(self.menu)

	def HandleHoleMenu(self, evt, hole):
		hole.holeSet.site.SyncToGui()
		if evt.GetId() == self.menuIds['Load']:
			holeList = [hole]
			self.LoadHoles(holeList)
		elif evt.GetId() == self.menuIds['View']:
			self.ViewFile(hole.file)
		elif evt.GetId() == self.menuIds['Export']:
			holeList = [hole]
			self.ExportHoles(holeList)

	def HandleHoleSetMenu(self, evt, holeSet):
		holeSet.site.SyncToGui()
		if evt.GetId() == self.menuIds['Load']:
			holeList = holeSet.holes.values()
			self.LoadHoles(holeList)
		if evt.GetId() == self.menuIds['Export']:
			holeList = holeSet.holes.values()
			self.ExportHoles(holeList)
		elif evt.GetId() == self.menuIds['Enable All'] or evt.GetId() == self.menuIds['Disable All']:
			for hole in holeSet.holes.values():
				hole.gui.enabledCb.SetValue(evt.GetId() == self.menuIds['Enable All'])

	def LoadHoles(self, holeList):
		# pre stuff
		self.parent.INIT_CHANGES()
		self.parent.OnNewData(None) # brgtodo

		self.parent.Window.range = []
		self.parent.Window.AltSpliceData = []
		self.parent.Window.selectedType = ""
		self.parent.TimeChange = False
		self.parent.Window.timeseries_flag = False

		site = holeList[0].holeSet.site # shorten some otherwise long statements
		sitePath = self.parent.DBPath + 'db/' + site.GetDir()

		# load holes (independent of enabled status, client can pass whatever list of holes they like)
		for hole in holeList:
			self.parent.CurrentDir = sitePath
			holefile = sitePath + hole.file
			self.parent.LOCK = 0
			type = hole.holeSet.type #GRA
			intType, annot = self.parent.TypeStrToInt(type)
			decimate = hole.holeSet.decimate
			#self.parent.filterPanel.decimate.SetValue(str(decimate))
			ret = py_correlator.openHoleFile(holefile, -1, intType, decimate, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, annot)
			if ret == 1:
				self.parent.LOCK = 1

			# set range
			holeRange = MakeRangeList(hole, type)
			self.parent.Window.range.append(holeRange)

		# load cull tables
		culledTypes = []
		for hole in holeList:
			if hole.holeSet.type not in culledTypes and hole.holeSet.IsCullEnabled():
				print "loading cull"
				coretype, annot = self.parent.TypeStrToInt(hole.holeSet.type)
				print "coretype = " + str(coretype) + ", annot = " + annot
				py_correlator.openCullTable(sitePath + hole.holeSet.cullTable.file, coretype, annot)
				culledTypes.append(hole.holeSet.type)

		# load log
		logLoaded = False
		for log in site.logTables:
			if log.enable:
				py_correlator.openLogFile(sitePath + log.file, int(log.dataIndex))
				# decimate
				# smooth
				ret = py_correlator.getData(5)
				if ret != "":
					if py_correlator.getMudline() != 0.0:
						self.parent.Window.isLogShifted = True
					self.parent.filterPanel.OnLock()
					self.parent.ParseData(ret, self.parent.Window.LogData)

					# set range
					logRange = MakeRangeList(log, 'log')
					self.parent.Window.range.append(logRange)

					self.parent.UpdateSMOOTH_LogData()

					self.parent.filterPanel.OnRelease()
					self.parent.Window.isLogMode = 1
					self.parent.Window.SpliceTieData = []
					self.parent.Window.CurrentSpliceCore = -1
					self.parent.autoPanel.OnButtonEnable(0, True)
					logLoaded = True
					break

		# load saved tables (OnLOAD_TABLE())
		tableLoaded = [False, False, False]
		for at in site.affineTables:
			if at.enable:
				py_correlator.openAttributeFile(sitePath + at.file, 0)
				tableLoaded[0] = True
				break
		for st in site.spliceTables:
			if st.enable:
				ret = py_correlator.openSpliceFile(sitePath + st.file)
				if ret == 'error':
					self.parent.OnShowMessage("Error", "Couldn't create splice record(s)", 1)
				else:
					tableLoaded[1] = True
				break
		for et in site.eldTables:
			if et.enable:
				py_correlator.openAttributeFile(sitePath + et.file, 1)
				tableLoaded[2] = True
				if self.parent.Window.LogData != [] :
					self.parent.eldPanel.SetFlag(True)
					if py_correlator.getMudline() != 0.0 :
						self.parent.OnUpdateLogData(True)
					retdata = py_correlator.getData(13)
					if retdata != "" :
						self.parent.ParseSaganData(retdata)
						self.parent.autoPanel.OnButtonEnable(0, False)
					retdata = "" 
				break

		# 1/21/2014 brgtodo: Try to consolidate all the parent.Window changes, GUI changes
		# and such into their own routines.
		self.parent.Window.LogselectedTie = -1
		self.parent.Window.activeSATie = -1
		self.parent.LOCK = 0

		if tableLoaded[1] == True :
			self.parent.OnInitDataUpdate()
			self.parent.InitSPLICE()
			self.parent.UpdateSPLICE(False)
			self.parent.autoPanel.SetCoreList(1, [])

			holeSet = holeList[0].holeSet
			hsMin = float(holeSet.min)
			hsMax = float(holeSet.max)
			newrange = 'splice', hsMin, hsMax, hsMax - hsMin, 0, holeSet.continuous
			self.parent.Window.range.append(newrange)
			self.parent.Window.selectedType = holeSet.type

		if tableLoaded[2] == True :
			self.parent.UpdateELD(True)

		if not tableLoaded[1] and not tableLoaded[2]:
			self.parent.UpdateCORE()
			self.parent.UpdateSMOOTH_CORE()
			self.parent.autoPanel.SetCoreList(0, self.parent.Window.HoleData)

		self.parent.Window.ShowLog = False

		self.parent.OnDisableMenu(1, True)
 		self.parent.LOCK = 1

		if self.parent.showReportPanel == 1:
			self.parent.OnUpdateReport()

		self.parent.ShowDisplay()
		self.parent.SetLoadedSite(site)

		# LOAD SECTION
		self.parent.OnUpdateDepthStep()

		self.parent.NewDATA_SEND()
		self.parent.Window.UpdateScroll(1)
		self.parent.Window.UpdateScroll(2)
		self.parent.Window.SetFocusFromKbd()
		self.parent.Window.UpdateDrawing()
		self.parent.compositePanel.OnUpdate() # make sure growth rate is updated

	def ViewFile(self, filename):
		holefile = self.parent.DBPath + "db/" + self.GetCurrentSite().GetDir() + filename
		self.dataFrame.fileText.Clear()
		self.dataFrame.fileText.LoadFile(holefile)
		self.dataFrame.sideNote.SetSelection(3) # File View tab

	def ExportHoles(self, holeList):
		exportDlg = dialog.ExportCoreDialog(self.dataFrame)
		exportDlg.Centre()
		if exportDlg.ShowModal() == wx.ID_OK:
			fileDlg = wx.FileDialog(self.dataFrame, "Select Directory for Export", self.parent.Directory, style=wx.SAVE)
			if fileDlg.ShowModal() == wx.ID_OK:
				self.parent.OnNewData(None)

				siteDir = holeList[0].holeSet.site.GetDir()
				path = self.parent.DBPath + 'db/' + siteDir

				# load holes (ignoring enabled state)
				for hole in holeList:
					intType, annot = self.parent.TypeStrToInt(hole.holeSet.type)
					holefile = path + hole.file
					ret = py_correlator.openHoleFile(holefile, -1, intType, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, annot)

				# apply cull, affine, splice
				applied = ""
# 				if exportDlg.cull.GetValue() == True and cull_item != None:
# 					py_correlator.openCullTable(path + self.tree.GetItemText(cull_item, 8), type, annot)
# 					applied = "cull"

				affine_item = holeList[0].holeSet.site.GetAffine()
 				if exportDlg.affine.GetValue() == True and affine_item != None:
 					py_correlator.openAttributeFile(path + affine_item.file, 0)
 					applied = "affine"

				splice_item = holeList[0].holeSet.site.GetSplice()
 				if exportDlg.splice.GetValue() == True and splice_item != None :
 					ret_splice = py_correlator.openSpliceFile(path + splice_item.file)
 					if ret_splice == "error" : 
 						self.parent.OnShowMessage("Error", "Could not Make Splice Records", 1)
					applied = "splice"
				elif exportDlg.splice.GetValue() == True and splice_item == None :
 					self.parent.OnShowMessage("Error", "Can't export, active splice table required.", 1)
 					self.parent.OnNewData(None)
 					exportDlg.Destroy()
 					return

				# apply eld, age model
# 				if exportDlg.eld.GetValue() == True and eld_item != None :
# 					if log_item != None :
# 						py_correlator.openLogFile(path+ self.tree.GetItemText(log_item, 8), int(self.tree.GetItemText(log_item, 11)))
# 						py_correlator.openAttributeFile(path + self.tree.GetItemText(eld_item, 8), 1)
# 						applied = "eld"
# 					else :
# 						self.parent.OnShowMessage("Error", "Need Log to Export ELD", 1)
# 						self.parent.OnNewData(None)
# 						dlg.Destroy()
# 						return
# 				if exportDlg.age.GetValue() == True and age_item != None :
# 					applied += "-age"
# 					agefilename = path+ self.tree.GetItemText(age_item, 8)
# 					if exportDlg.eld.GetValue() == True :
# 						if exportDlg.splice.GetValue() == True :
# 							count = py_correlator.saveAgeCoreData(agefilename, path + ".export.tmp", 2)
# 						else :
# 							count = py_correlator.saveAgeCoreData(agefilename, path + ".export.tmp", 0)
# 					else :
# 						if exportDlg.splice.GetValue() == True :
# 							count = py_correlator.saveAgeCoreData(agefilename, path + ".export.tmp", 1)
# 						else :
# 							count = py_correlator.saveAgeCoreData(agefilename, path + ".export.tmp", 0)
# 				elif exportDlg.eld.GetValue() == True :
# 					if exportDlg.splice.GetValue() == True :
# 						count = py_correlator.saveCoreData(path + ".export.tmp", 2)
# 					else :
# 						count = py_correlator.saveCoreData(path + ".export.tmp", 0)
# 				elif exportDlg.splice.GetValue() == True :
# 					count = py_correlator.saveCoreData(path + ".export.tmp", 1)
# 				else :
# 					count = py_correlator.saveCoreData(path + ".export.tmp", 0)
#
# 				self.parent.OnNewData(None)

				# just using splice/affine for now
				saveType = 1 if (exportDlg.splice.GetValue() == True) else 0
				savedCoreCount = py_correlator.saveCoreData(path + ".export.tmp", saveType)

 				self.parent.OnNewData(None)

				# 1/20/2014 brgtodo: I was initially horrified by the idea of assembling shell
				# commands to copy files, but it seems to be an accepted practice in the Python
				# world. Further, using a library (shlib is the most likely candidate) will lose
				# file metadata on POSIX systems like OS X, i.e. we'll lose group, owner and
				# resource forks (though, God willing, we don't have anything with a fork!).
				if exportDlg.format.GetValue() == True: # export non-XML
					outdir = fileDlg.GetDirectory()
					filename = fileDlg.GetFilename()
					#multiple = len(holeList) > 0
					count = 0
					for hole in holeList:
						filePrefix = filename + '-' + hole.holeSet.site.name + '-' + applied
						countStr = ""
						#if multiple:
						if savedCoreCount > 1:
							filePrefix = filePrefix + hole.name
							countStr = str(count)
							count = count + 1
							
						typeStr = self.parent.TypeStrToFileSuffix(hole.holeSet.type, True)
						fileSuffix = '.' + typeStr + '.dat'
						outfile = filePrefix + fileSuffix
						if sys.platform == 'win32':
							workingdir = os.getcwd()
							os.chdir(path)
							cmd = 'copy ' + '.export.tmp' + countStr + ' \"' + outdir + '/' + outfile + '\"'
							os.system(cmd)
							os.chdir(workingdir)
						else:
							cmd = 'cp \"' + path + '.export.tmp' + countStr + '\" \"' + outdir + '/' + outfile + '\"'
							os.system(cmd)
				else: # export as XML - 1/17/2014 brgtodo
					pass
				
				if savedCoreCount > 0:
					self.parent.OnShowMessage("Information", "Export successful", 1)
				else:
					self.parent.OnShowMessage("Error", "Export failed", 1)

			fileDlg.Destroy()
		exportDlg.Destroy()

	def GetCurrentSite(self):
		if self.currentSite.GetCount() > 0:
			siteIndex = self.currentSite.GetSelection()
			return self.currentSite.GetClientData(siteIndex)
		return None

class HoleGUI:
	def __init__(self, hole, panel):
		self.hole = hole
		self.enabledCb = wx.CheckBox(panel, -1, "Enabled", size=(80,-1))
		self.SyncToData()

	def SyncToData(self):
		self.enabledCb.SetValue(self.hole.IsEnabled())

	def SyncToGui(self):
		self.hole.enable = self.enabledCb.GetValue()

class HoleSetGUI:
	def __init__(self, holeSet, panel):
		self.holeSet = holeSet
		self.actionButton = wx.Button(panel, -1, "Actions...")
		self.rangeText = wx.StaticText(panel, -1, "")
		self.continuousChoice = wx.Choice(panel, -1, choices=['Continuous','Discrete'])
		self.decimateText = wx.StaticText(panel,  -1, "")
		self.smoothText = wx.StaticText(panel, -1, "")
		self.cullEnabledCb = wx.CheckBox(panel, -1, "Enable Cull")
		self.SyncToData()

	def SyncToData(self):
		self.continuousChoice.SetSelection(0 if self.holeSet.continuous else 1)
		self.rangeText.SetLabel(MakeRangeString(self.holeSet.min, self.holeSet.max))
		contIdx = 0 if self.holeSet.continuous else 1
		self.continuousChoice.SetSelection(contIdx)
		self.decimateText.SetLabel(MakeDecimateString(self.holeSet.decimate))
		self.smoothText.SetLabel(self.holeSet.smooth)
		self.cullEnabledCb.Enable(self.holeSet.HasCull())
		self.cullEnabledCb.SetValue(self.holeSet.IsCullEnabled())

	def SyncToGui(self):
		self.holeSet.continuous = (self.continuousChoice.GetSelection() == 0)
		self.holeSet.EnableCull(self.cullEnabledCb.GetValue())

class SavedTableGUI:
	def __init__(self, site, name, panel):
		self.site = site
		self.name = name # Affine, Splice or ELD
		self.tableChoice = wx.Choice(panel, -1, size=(200,-1))
		self.enabledCb = wx.CheckBox(panel, -1, "Enable")
		self.SyncToData()

	def SyncToData(self):
		self.tableChoice.Clear()

		enabledIdx = -1
		for t in self.GetTables():
			self.tableChoice.Append(t.file)
			if t.enable:
				enabledIdx = self.tableChoice.GetCount() - 1

		if self.tableChoice.GetCount() == 0:
			self.tableChoice.Append("[no " + self.name.lower() + " tables]")
			self.tableChoice.SetSelection(0)
			self.enabledCb.Enable(False)
		else:
			self.enabledCb.Enable(True)
			if enabledIdx != -1:
				self.tableChoice.SetSelection(enabledIdx)
				self.enabledCb.SetValue(True)
			else:
				self.tableChoice.SetSelection(0)
				self.enabledCb.SetValue(False)

	def SyncToGui(self):
		selStr = self.tableChoice.GetString(self.tableChoice.GetSelection())
		enable = self.enabledCb.GetValue()
		for t in self.GetTables():
			t.enable = (enable and (t.file == selStr))

	# pull correct list of tables based on self.name
	def GetTables(self):
		if self.name == "Affine":
			return self.site.affineTables
		elif self.name == "Splice":
			return self.site.spliceTables
		elif self.name == "ELD":
			return self.site.eldTables
		else:
			print "GetTables(): Unexpected saved table type: " + self.name
			return []

class LogTableGUI:
	def __init__(self, logTable, panel):
		self.logTable = logTable
		self.enabledCb = wx.CheckBox(panel, -1, "Enable")
		self.SyncToData()

	def SyncToData(self):
		self.enabledCb.SetValue(self.logTable.enable)

	def SyncToGui(self):
		self.logTable.enable = self.enabledCb.GetValue()
