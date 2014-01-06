class HoleData:
	def __init__(self, name):
		self.name = name
		self.dataName = '[no dataName]'
		self.depth = '[no depth]'
		#self.decimate = '[no decimate]' #though decimate is stored at a hole level, it's holeset level in practice
		self.min = '[no min]'
		self.max = '[no max]'
		self.file = '[no file]'
		self.origSource = '[no origSource]'
		self.data = '[no data]'
		self.enable = '[no enable]'
		self.updatedTime = '[no updatedTime]'
		self.byWhom = '[no byWhom]'

	def __repr__(self):
		return "Hole %s: %s %s %s %s %s %s %s %s %s %s" % (self.name, self.dataName, self.depth, self.min, self.max, self.file, self.origSource, self.data, self.enable, self.updatedTime, self.byWhom)

class HoleSet:
	def __init__(self, type):
		self.holes = {} # dict of HoleData objects
		self.type = type # built-in type e.g. NaturalGamma, Pwave, or Other
		self.contOrDisc = '[no contOrDisc]' # discrete or continuous
		self.decimate = '[no decimate]'
		self.smooth = '[no smooth]'
		self.min = '[no min]'
		self.max = '[no max]'

	def __repr__(self):
		return "HoleSet %s: %s %s %s %s %s" % (self.type, self.contOrDisc, self.decimate, self.smooth, self.min, self.max)

	def dump(self):
		print self
		for hole in self.holes.values():
			print hole
	
	def AddHole(self, hole):
		if isinstance(hole, HoleData) and hole.name not in self.holes:
			self.holes[hole.name] = hole

	# return string for use in title of a hole set's CollapsiblePane
	def GetTitleStr(self):
		return self.type + " - Range: (" + self.min + ", " + self.max + "); " + self.contOrDisc + "; " + "Decimate: " + self.decimate + "; " + "Smoothing: " + self.smooth

class SiteData:
	def __init__(self, name):
		self.name = name
		self.holeSets = {}
		self.affineTables = []
		self.spliceTables = []
		self.eldTables = []
		self.cullTables = []
		self.logTables = []
		self.stratTables = []
		self.ageTables = []
		self.seriesTables = [] # timeseries
		self.imageTables = []

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
		for ct in self.cullTables:
			print ct
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

	def AddHole(self, type, hole):
		if type in self.holeSets:
			self.holeSets[type].AddHole(hole)

class TableData:
	def __init__(self):
		self.file = ''
		self.updatedTime = ''
		self.byWhom = ''
		self.enable = ''
		self.origSource = ''

	def __repr__(self):
		return "%s %s %s %s %s" % (self.file, self.updatedTime, self.byWhom, self.enable, self.origSource)

	def FromTokens(self, tokens):
		self.file = tokens[1]
		self.updatedTime = tokens[2]
		self.byWhom = tokens[3]
		self.enable = tokens[4]
		if len(tokens) > 5 and tokens[5] != '-':
			self.origSource = tokens[5]

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

class DownholeLogTable:
	def __init__(self):
		self.file = None
		self.updatedTime = None
		self.byWhom = None
		self.origSource = None
		self.dataIndex = None
		self.enable = None
		self.dataType = None
		self.min = None
		self.max = None
		self.decimate = None
		self.foo = None

	def __repr__(self):
		return "DownholeLogTable " + "%s %s %s %s %s %s %s %s %s %s %s" % (self.file, self.updatedTime, self.byWhom, self.origSource, self.dataIndex, self.enable, self.dataType, self.min, self.max, self.decimate, self.foo)

	def GetName(self):
		return self.dataType

	def FromTokens(self, tokens):
		self.file = tokens[1]
		self.updatedTime = tokens[2]
		self.byWhom = tokens[3]
		self.origSource = tokens[4]
		self.dataIndex = tokens[5]
		self.enable = tokens[6]
		self.dataType = tokens[7]
		if len(tokens) >= 10:
			self.min = tokens[8]
			self.max = tokens[9]
		if len(tokens) >= 11:
			self.decimate = tokens[10]
		if len(tokens) >= 12:
			self.foo = tokens[11] # unclear what this value means

class DBView:
	def __init__(self, parentPanel, siteList):
		self.parentPanel = parentPanel # wx.Panel
		self.panes = [] # wx.CollapsiblePanes - retain to re-Layout() as needed

		self.InitUI(siteList)
		self.InitMenus()

		self.UpdateView(self.GetCurrentSite())

	def InitUI(self, siteList):
		self.sitePanel = wx.Panel(self.parentPanel, -1)
		self.sitePanel.SetSizer(wx.BoxSizer(wx.HORIZONTAL))
		self.currentSite = wx.Choice(self.sitePanel, -1)
		siteLabel = wx.StaticText(self.sitePanel, -1, "Current Site: ", style=wx.BOLD)
		slFont = siteLabel.GetFont()
		slFont.SetWeight(wx.BOLD)
		siteLabel.SetFont(slFont)
		self.sitePanel.GetSizer().Add(siteLabel, 0, border=5, flag=wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER_VERTICAL)
		self.sitePanel.GetSizer().Add(self.currentSite, 0, border=5, flag=wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER_VERTICAL)
		self.parentPanel.GetSizer().Add(self.sitePanel, 0, border=10, flag=wx.BOTTOM | wx.LEFT)

		self.dataPanel = wx.Panel(self.parentPanel, -1)
		self.dataPanel.SetSizer(wx.BoxSizer(wx.VERTICAL))
		self.dataPanel.SetBackgroundColour('white')
		self.parentPanel.GetSizer().Add(self.dataPanel, 0, border=10, flag=wx.BOTTOM | wx.LEFT)

		self.UpdateSites(siteList)
		self.parentPanel.Bind(wx.EVT_CHOICE, self.SiteChanged, self.currentSite)

	def InitMenus(self):
		self.menu = wx.Menu()
		self.loadItem = self.menu.Append(1, "Load")
		self.viewItem = self.menu.Append(2, "View")

	def NewPanel(self, toPanel):
		panel = wx.Panel(toPanel, -1)
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		panel.SetSizer(sizer)
		return panel, sizer

	def AddHoleSetRow(self, toPanel, holeSet):
		panel, sizer = self.NewPanel(toPanel)

		sizer.Add(wx.StaticText(panel, -1, "[All Holes]", size=(75,-1), style=wx.ALIGN_CENTRE), 0, border=10, flag=wx.RIGHT|wx.LEFT|wx.BOTTOM)
		button = wx.Button(panel, -1, "Actions...")
		sizer.Add(button, 0)
		sizer.AddSpacer((85,-1))
		sizer.Add(wx.StaticText(panel, -1, "Range: (" + holeSet.min + ", " + holeSet.max + ")"), 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.AddSpacer((5,-1))
		sizer.Add(wx.StaticText(panel, -1, holeSet.contOrDisc), 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.AddSpacer((5,-1))
		sizer.Add(wx.StaticText(panel, -1, "Decimate: " + holeSet.decimate), 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.AddSpacer((5,-1))
		sizer.Add(wx.StaticText(panel, -1, holeSet.smooth), 0, border=5, flag=wx.LEFT|wx.BOTTOM)

		panel.Bind(wx.EVT_BUTTON, self.PopActionsMenu, button)
		panel.Bind(wx.EVT_MENU, lambda event, args=holeSet: self.HandleHoleSetMenu(event, args), self.loadItem)
		panel.Bind(wx.EVT_MENU, lambda event, args=holeSet: self.HandleHoleSetMenu(event, args), self.viewItem)

		toPanel.GetSizer().Add(panel)

	def AddHoleRow(self, toPanel, hole):
		panel, sizer = self.NewPanel(toPanel)

		sizer.Add(wx.StaticText(panel, -1, hole.name, size=(75,-1), style=wx.ALIGN_CENTRE), 0, border=10, flag=wx.RIGHT|wx.LEFT|wx.BOTTOM)
		button = wx.Button(panel, -1, "Actions...")
		sizer.Add(button, 0, border=5, flag=wx.BOTTOM)
		cb = wx.CheckBox(panel, -1, "Enabled", size=(80,-1))
		sizer.Add(cb, 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.Add(wx.StaticText(panel, -1, "Range: (" + hole.min + ", " + hole.max + ")"), 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.Add(wx.StaticText(panel, -1, "File: " + hole.file), 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.Add(wx.StaticText(panel, -1, "Last updated: " + hole.updatedTime), 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.Add(wx.StaticText(panel, -1, "By: " + hole.byWhom), 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.Add(wx.StaticText(panel, -1, "Source: " + hole.origSource), 0, border=5, flag=wx.LEFT|wx.BOTTOM)

		panel.Bind(wx.EVT_BUTTON, self.PopActionsMenu, button)
		panel.Bind(wx.EVT_MENU, lambda event, args=hole: self.HandleHoleMenu(event, args), self.loadItem)
		panel.Bind(wx.EVT_MENU, lambda event, args=hole: self.HandleHoleMenu(event, args), self.viewItem)
		panel.Bind(wx.EVT_CHECKBOX, lambda event, args=panel: self.HoleEnabled(event, args), cb)

		toPanel.GetSizer().Add(panel)

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

	def HoleEnabled(self, event, panel):
		cb = event.GetEventObject()
		if isinstance(cb, wx.CheckBox):
			if cb.GetValue() == True:
				panel.SetBackgroundColour('green')
			else:
				panel.SetBackgroundColour('pink')
			panel.Refresh()

	def UpdateView(self, site):
		self.panes = []
		self.dataPanel.GetSizer().Clear(True)

		# Add Holes
		for hs in site.holeSets.values():
			hsPane = wx.CollapsiblePane(self.dataPanel, -1, hs.type, style=wx.CP_NO_TLW_RESIZE)
			hsPane.GetPane().SetSizer(wx.BoxSizer(wx.VERTICAL))
			self.dataPanel.GetSizer().Add(hsPane, 0, border=5, flag=wx.ALL|wx.EXPAND)
			self.dataPanel.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.PaneChanged, hsPane)
			self.panes.append(hsPane)
			self.AddHoleSetRow(hsPane.GetPane(), hs)
			for holeKey in sorted(hs.holes.keys()):
				hole = hs.holes[holeKey]
				self.AddHoleRow(hsPane.GetPane(), hole)

		# Saved Tables (Affine, ELD, Splice)
		stPane = wx.CollapsiblePane(self.dataPanel, -1, "Saved Tables", style=wx.CP_NO_TLW_RESIZE)
		stPane.GetPane().SetSizer(wx.BoxSizer(wx.VERTICAL))
		self.dataPanel.GetSizer().Add(stPane, 0, border=5, flag=wx.ALL|wx.EXPAND) # brgtodo: expand necessary?
		self.dataPanel.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.PaneChanged, stPane)
		self.panes.append(stPane)
		for at in site.affineTables:
			self.AddTableRow(stPane.GetPane(), at)
		for st in site.spliceTables:
			self.AddTableRow(stPane.GetPane(), st)
		for et in site.eldTables:
			self.AddTableRow(stPane.GetPane(), et)

		amPane = wx.CollapsiblePane(self.dataPanel, -1, "Age Models", style=wx.CP_NO_TLW_RESIZE)
		amPane.GetPane().SetSizer(wx.BoxSizer(wx.VERTICAL))
		self.dataPanel.GetSizer().Add(amPane, 0, border=5, flag=wx.ALL|wx.EXPAND) # brgtodo: expand necessary?
		self.dataPanel.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.PaneChanged, amPane)
		self.panes.append(amPane)
		for at in site.ageTables:
			self.AddTableRow(amPane.GetPane(), at)
		for st in site.seriesTables:
			self.AddTableRow(amPane.GetPane(), st)

		ltPane = wx.CollapsiblePane(self.dataPanel, -1, "Downhole Logs", style=wx.CP_NO_TLW_RESIZE)
		ltPane.GetPane().SetSizer(wx.BoxSizer(wx.VERTICAL))
		self.dataPanel.GetSizer().Add(ltPane, 0, border=5, flag=wx.ALL|wx.EXPAND) # brgtodo: expand necessary?
		self.dataPanel.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.PaneChanged, ltPane)
		self.panes.append(ltPane)
		for lt in site.logTables:
			self.AddTableRow(ltPane.GetPane(), lt)

		# refresh layout
		for pane in self.panes:
			pane.Expand()
		self.PaneChanged(evt=None) # force re-layout

	def UpdateSites(self, siteList):
		self.currentSite.Clear()
		for site in siteList:
			self.currentSite.Append(site.name, clientData=site)

	def SiteChanged(self, evt):
		siteIndex = self.currentSite.GetSelection()
		curSite = self.currentSite.GetClientData(siteIndex)
		if curSite != None:
			self.UpdateView(curSite)

	def PaneChanged(self, evt):
		self.parentPanel.Layout()
		self.dataPanel.Layout()
		for cp in self.panes:
			cp.GetPane().Layout()
		self.parentPanel.FitInside() # show/hide scrollbar if necessary

	def PopActionsMenu(self, evt):
		evt.GetEventObject().PopupMenu(self.menu)

	def HandleHoleMenu(self, evt, hole):
		print "event id = " + str(evt.GetId())
		print "Hole = " + hole.name

	def HandleHoleSetMenu(self, evt, holeSet):
		print "event id = " + str(evt.GetId())
		print "HoleSet type = " + holeSet.type
	
	def GetCurrentSite(self):
		if self.currentSite.GetCount() > 0:
			id = self.currentSite.GetSelection()
			return self.currentSite.GetClientData(id)
		return None
