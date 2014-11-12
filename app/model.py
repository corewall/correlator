import wx
from datetime import datetime

from importManager import py_correlator

import constants as const
import dbutils as dbu
import dialog
import globals as glb
import xml_handler as xml


def MakeRangeString(min, max):
	return "Range: (" + min + ", " + max + ")"

def MakeDecimateString(dec):
	return "Decimate: " + str(dec)

""" Generate a range list - [name, min, max, range coefficient, smoothing type, continuous or discrete] -
from the provided HoleData or DownholeLogTable """
def MakeRangeList(data, name):
	if isinstance(data, HoleData):
		smoothStyle = data.holeSet.smooth.style
		continuous = data.holeSet.continuous
	elif isinstance(data, DownholeLogTable):
		smoothStyle = data.smooth.style
		continuous = True
	else:
		print "MakeRangeList() expects HoleData or DownholeLogData"
		return []
	min = float(data.min)
	max = float(data.max)
	coef = max - min

	return [name, min, max, coef, smoothStyle, continuous]

""" Convert "Natural Gamma" to "NaturalGamma" """
def FixType(typeStr):
	if typeStr == "Natural Gamma":
		typeStr = "NaturalGamma"
	return typeStr


# FileMetadata a better name?
class TableData:
	def __init__(self, file="", origSource=""):
		self.file = file
		self.updatedTime = glb.GetTimestamp()
		self.byWhom = glb.User
		self.enable = False
		self.origSource = origSource

	def __repr__(self):
		return "%s %s %s %s %s" % (self.file, self.updatedTime, self.byWhom, str(self.enable), self.origSource)

	def GetEnableStr(self):
		return "Enable" if self.enable else "Disable"

	def IsEnabled(self):
		return self.enable

	def UpdateTimestamp(self):
		self.updatedTime = glb.GetTimestamp()
		
	def GetTooltipStr(self):
		return "File: {}\nLast Updated: {}\nBy Whom: {}\nOriginal Source: {}".format(self.file, self.updatedTime, self.byWhom, self.origSource)

class HoleData(TableData):
	def __init__(self, name):
		TableData.__init__(self)
		self.name = name
		self.dataName = 'Undefined'
		self.depth = '[no depth]' # brgtodo unused?
		self.min = '-9999.0'
		self.max = '9999.0'
		self.data = '[no data]' # weird 6 7 8 9 string
		self.holeSet = None # parent HoleSet
		self.gui = None # HoleGUI

	def __repr__(self):
		return "Hole %s: %s %s %s %s %s %s %s %s %s %s" % (self.name, self.dataName, self.depth, self.min, self.max, self.data, str(self.enable), self.file, self.origSource, self.updatedTime, self.byWhom)

class SmoothData:
	def __init__(self, width=-1, unit=-1, style=-1):
		self.width = width
		self.unit = unit
		self.style = style
	
	def __repr__(self):
		if self.IsValid():
			return "{} {} {}".format(self.width, self.GetUnitStr(), self.GetStyleStr())
		else:
			return ""

	def IsValid(self):
		return self.width != -1 and self.unit != -1 and self.style != -1

	def GetUnitStr(self):
		if self.unit == const.POINTS:
			return "Points"
		else:
			return "Depth(cm)"

	def GetStyleStr(self):
		if self.style == const.SMOOTHED:
			return "SmoothedOnly"
		elif self.style == const.UNSMOOTHED:
			return "UnsmoothedOnly"
		else:
			return "Smoothed&Unsmoothed"

	def MakeToken(self):
		return str(self)

class HoleSet:
	def __init__(self, type):
		self.holes = {} # dict of HoleData objects
		self.cullTable = None # appears there can only be one of these per HoleSet
		self.type = type # built-in type string e.g. NaturalGamma, Pwave, or Other
		self.continuous = True # if False, discrete
		self.decimate = 1
		self.smooth = SmoothData()
		self.min = '-9999.0' # brgtodo numeric?
		self.max = '9999.0' # numeric?
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
			
	def HasHoles(self):
		return len(self.holes) > 0
	
	def AddHole(self, hole):
		if isinstance(hole, HoleData) and hole.name not in self.holes:
			hole.holeSet = self
			self.holes[hole.name] = hole
		self.UpdateRange()

	def UpdateRange(self):
		setMax = -9999.0
		setMin = 9999.0
		for hole in self.holes.values():
			holeMin = float(hole.min)
			holeMax = float(hole.max)
			if holeMin < setMin:
				setMin = holeMin
			if holeMax > setMax:
				setMax = holeMax
		self.min = str(setMin)
		self.max = str(setMax)

	def HasCull(self):
		return self.cullTable is not None

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

	def GetSmoothStr(self):
		return str(self.smooth)

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
		for at in self.ageTables:
			at.gui.SyncToData()

	def AddHoleSet(self, type):
		if type not in self.holeSets:
			self.holeSets[type] = HoleSet(type)

	def AddHole(self, type, hole):
		#print "AddHole: type = {}, hole = {}".format(type, hole)
		if type not in self.holeSets:
			self.AddHoleSet(type)
		self.holeSets[type].site = self
		self.holeSets[type].AddHole(hole)
		
	def AddLog(self, logTable):
		self.logTables.append(logTable)

	# copy existing table file to site dir, add to siteDict
	# tableFile.file is full path to source file
	def AddTableFile(self, tableFile, type):
		srcPath = tableFile.file
		tableList = self.GetTableList(type)
		tableFile.file = dbu.MakeTableFilename(self.name, dbu.GetNewTableNum(tableList), const.SAVED_TABLE_STRS[type])
		destPath = dbu.GetSiteFilePath(self.name, tableFile.file)
		tableList.append(tableFile)
		dbu.MoveFile(srcPath, destPath) # copy table to site dir
	
	def CreateTableFile(self, type, enable=True):
		tableList = self.GetTableList(type)
		tab = self.CreateTable(type)
		tableNum = dbu.GetNewTableNum(tableList)
		tab.file = dbu.MakeTableFilename(self.name, tableNum, const.SAVED_TABLE_STRS[type])
		tab.enable = enable
		tableList.append(tab)
		if enable:
			self.SetEnabledTable(tab.file, tableList)
		return dbu.GetSiteFilePath(self.name, tab.file)
	
	def SaveTable(self, type, createNew):
		filePath = ""
		tableList = self.GetTableList(type)
		if createNew or self.GetEnabledTable(tableList) is None:
			filePath = self.CreateTableFile(type)
		else: # update current table
			curTab = self.GetTableByType(type)
			filePath = dbu.GetSiteFilePath(self.name, curTab.file)
		return filePath
	
	""" remove item from site based on filename, which is unique per site """
	def DeleteTable(self, filename):
		for hskey, hs in self.holeSets.items():
			for holekey, hole in hs.holes.items():
				if hole.file == filename:
					del hs.holes[holekey]
					if not hs.HasHoles():
						del self.holeSets[hskey]
					return
		for at in self.affineTables:
			if at.file == filename:
				self.affineTables.remove(at)
				return
		for st in self.spliceTables:
			if st.file == filename:
				self.spliceTables.remove(st)
				return
		for et in self.eldTables:
			if et.file == filename:
				self.eldTables.remove(et)
				return
		for lt in self.logTables:
			if lt.file == filename:
				self.logTables.remove(lt)
				return
		for at in self.ageTables:
			if at.file == filename:
				self.ageTables.remove(at)
				return
		for st in self.seriesTables:
			if st.file == filename:
				self.seriesTables.remove(st)
				return
		for it in self.imageTables:
			if it.file == filename:
				self.imageTables.remove(it)
				return 

	""" return currently enabled table of specified type, if one exists """
	def GetTableByType(self, type):
		if type == const.AFFINE:
			return self.GetAffine()
		elif type == const.SPLICE:
			return self.GetSplice()
		elif type == const.ELD:
			return self.GetEld()
		else:
			return None
		
	def CreateTable(self, type):
		if type == const.AFFINE:
			return AffineData()
		elif type == const.SPLICE:
			return SpliceData()
		elif type == const.ELD:
			return EldData()
		else:
			return None
	
	def GetTableList(self, type):
		if type == const.AFFINE:
			return self.affineTables
		elif type == const.SPLICE:
			return self.spliceTables
		elif type == const.ELD:
			return self.eldTables
		else:
			return None
	
	""" return currently enabled AffineTable if there is one """
	def GetAffine(self):
		return self.GetEnabledTable(self.affineTables)

	""" return currently enabled SpliceTable if there is one """
	def GetSplice(self):
		return self.GetEnabledTable(self.spliceTables)
	
	""" return currently enabled EldTable if there is one """
	def GetEld(self):
		return self.GetEnabledTable(self.eldTables)

	def SetEnabledTable(self, enabledFile, tableList):
		for tab in tableList:
			tab.enable = (tab.file == enabledFile)
	
	""" generic "find the enabled table" routine """
	def GetEnabledTable(self, tableList):
		result = None
		for tab in tableList:
			if tab.enable:
				result = tab
		return result

	def FindHoleSet(self, type):
		type = FixType(type)
		if type in self.holeSets:
			return self.holeSets[type]
		else:
			print "Couldn't find type " + type + " in site " + self.name + " holeSets"
			return None
		
	def FindHole(self, type, hole):
		type = FixType(type)
		if type in self.holeSets:
			if hole in self.holeSets[type].holes:
				return self.holeSets[type].holes[hole]
		return None
	
	def HasHoleSet(self, type):
		return self.FindHoleSet(type) is not None
	
	def HasHole(self, type, hole):
		return self.FindHole(type, hole) is not None

	def SetDecimate(self, type, decimate):
		hs = self.FindHoleSet(type)
		if hs is not None:
			self.holeSets[type].decimate = decimate

	def SetSmooth(self, type, smooth):
		hs = self.FindHoleSet(type)
		if hs is not None:
			self.holeSets[type].smooth = smooth
			
	def SetLogSmooth(self, smooth):
		enabledLog = self.GetEnabledTable(self.logTables)
		if enabledLog is not None:
			enabledLog.smooth = smooth

	def GetCull(self, type):
		hs = self.FindHoleSet(type)
		if hs is not None:
			return hs.cullTable

	def SetCull(self, type, curUser):
		print "SetCull for type {}".format(type)
		hs = self.FindHoleSet(type)
		if hs is not None:
			if hs.cullTable is None:
				hs.cullTable = CullTable()
				hs.cullTable.file = glb.MakeFileName(type, self.name, 'cull')
				hs.cullTable.enable = True
				print "no cull file exists, creating new {}".format(hs.cullTable.file)
			else:
				print "cull file exists, updating user and timestamp"

			# always update whether or not we created a new cull table file
			hs.cullTable.UpdateTimestamp()
			hs.cullTable.byWhom = curUser

	def GetDir(self):
		return self.name + '/'

	def GetPath(self, prefix):
		return prefix + self.GetDir()
	
	def GetLegAndSite(self):
		return self.GetLeg(), self.GetSite()
	
	def GetLeg(self):
		splitName = self.name.split('-')
		return splitName[0]
	
	def GetSite(self):
		splitName = self.name.split('-')
		return splitName[1]

class AffineData(TableData):
	def __init__(self, file="", origSource=""):
		TableData.__init__(self, file, origSource)
	def __repr__(self):
		return "AffineTable " + TableData.__repr__(self)
	def GetName(self):
		return "Affine"

class SpliceData(TableData):
	def __init__(self, file="", origSource=""):
		TableData.__init__(self, file, origSource)
	def __repr__(self):
		return "SpliceTable " + TableData.__repr__(self)
	def GetName(self):
		return "Splice"

class EldData(TableData):
	def __init__(self, file="", origSource=""):
		TableData.__init__(self, file, origSource)
	def __repr__(self):
		return "EldTable " + TableData.__repr__(self)
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
	def GetName(self):
		return "Universal Cull Table"

# cull table that applies to a single HoleSet
class CullTable(TableData):
	def __init__(self, file="", origSource=""):
		TableData.__init__(self, file, origSource)
	def __repr__(self):
		return "CullTable " + TableData.__repr__(self)
	def GetName(self):
		return "Cull Table"

class StratTable(TableData):
	def __init__(self):
		TableData.__init__(self)
	def __repr__(self):
		return "StratTable " + TableData.__repr__(self)
	def GetName(self):
		return "Stratigraphy" # brgtodo - correct

class AgeTable(TableData):
	def __init__(self, file="", origSource=""):
		TableData.__init__(self, file, origSource)
		self.gui = None
	def __repr__(self):
		return "AgeTable " + TableData.__repr__(self)
	def GetName(self):
		return "Age/Depth"

class SeriesTable(TableData):
	def __init__(self, file="", origSource=""):
		TableData.__init__(self, file, origSource)
		self.gui = None
	def __repr__(self):
		return "SeriesTable " + TableData.__repr__(self)
	def GetName(self):
		return "Age"

class ImageTable(TableData):
	def __init__(self, file="", origSource=""):
		TableData.__init__(self, file, origSource)
	def __repr__(self):
		return "ImageTable " + TableData.__repr__(self)
	def GetName(self):
		return "Image"

class DownholeLogTable(TableData):
	def __init__(self, file="", origSource=""):
		TableData.__init__(self, file, origSource)
		self.dataIndex = '[no dataIndex]'
		self.dataType = '[no dataType]'
		self.min = '[no min]'
		self.max = '[no max]'
		self.decimate = 1
		self.smooth = SmoothData()
		self.gui = None # LogTableGUI

	def __repr__(self):
		return "DownholeLogTable " + "%s %s %s %s %s %s %s %s %s %s %s" % (self.file, self.updatedTime, self.byWhom, self.origSource, self.dataIndex, self.enable, self.dataType, self.min, self.max, str(self.decimate), self.smooth)

	def GetName(self):
		return self.dataType

class DBController:
	def __init__(self):
		self.parent = None
		self.parentPanel = None
		self.view = None
		self.siteDict = None
		
	# 10/14/2014 brgtodo: still have to init this stuff late due to
	# family-sized platter of spaghetti initialization, ugh.
	def InitView(self, parent, dataFrame, parentPanel, siteDict):
		self.parent = parent
		self.parentPanel= parentPanel
		self.siteDict = siteDict
		self.view = DBView(parent, dataFrame, parentPanel, siteDict)
	
	def ImportHoleData(self, event):
		self.view.DoImportHoleData()
	
	# import affine, splice, or ELD data
	def ImportSavedTable(self, type):
		curSite = self.view.GetCurrentSite()
		leg, site = curSite.GetLegAndSite()
		if type == const.AFFINE:
			importTable = dbu.ImportAffineTable(self.parentPanel, leg, site)
		elif type == const.SPLICE:
			importTable = dbu.ImportSpliceTable(self.parentPanel, leg, site)
		elif type == const.ELD:
			importTable = dbu.ImportELDTable(self.parentPanel, leg, site)

		if importTable is not None:
			curSite.AddTableFile(importTable, type)
			curSite.SyncToData()
		
	def ImportAffineTable(self, event):
		self.ImportSavedTable(const.AFFINE)
		
	def ImportSpliceTable(self, event):
		self.ImportSavedTable(const.SPLICE)
		
	def ImportELDTable(self, event):
		self.ImportSavedTable(const.ELD)
		
	def ImportDownholeLog(self, event):
		curSite = self.view.GetCurrentSite()
		if dbu.ImportDownholeLog(self.parentPanel, curSite):
			self.view.UpdateView(curSite)
			
	def ImportStratFile(self, event):
		curSite = self.view.GetCurrentSite()
		dbu.ImportStratFile(self.parentPanel, curSite.GetLeg(), curSite.GetSite())
		
	def ImportAgeDepthTable(self, event):
		curSite = self.view.GetCurrentSite()
		adTable = dbu.ImportAgeDepthTable(self.parentPanel, curSite)
		if adTable is not None:
			curSite.ageTables.append(adTable)
			self.view.UpdateView(curSite)
	
	def ImportTimeSeriesTable(self, event):
		curSite = self.view.GetCurrentSite()
		tsTable = dbu.ImportTimeSeriesTable(self.parentPanel, curSite)
		if tsTable is not None:
			curSite.seriesTables.append(tsTable)
			self.view.UpdateView(curSite)
	
	def ImportImageTable(self, event):
		curSite = self.view.GetCurrentSite()
		imTable = dbu.ImportImageTable(self.parentPanel, curSite)
		if imTable is not None:
			curSite.imageTables.append(imTable)
			self.view.UpdateView(curSite)


class DBView:
	def __init__(self, parent, dataFrame, parentPanel, siteDict):
		self.parent = parent # 1/6/2014 brg: Don't like this naming...app?
		self.dataFrame = dataFrame # old DB Manager DataFrame
		self.parentPanel = parentPanel # wx.Panel
		self.panes = [] # wx.CollapsiblePanes - retain to re-Layout() as needed
		self.menu = None # action menu
		self.siteDict = siteDict # dictionary of sites keyed on site name
		
		# 10/15/2014 brg: Basis of a kludgy method to update GUI after an item
		# has been deleted. Was getting segfaults when trying to call SiteChanged()
		# from an event handler because SiteChanged() clears the GUI and rebuilds it.
		# wx.CallAfter() didn't help, so I resorted to starting this timer in the
		# offending event handler. Seems to work! I'll take it.
		self.refreshTimer = wx.Timer(self.parentPanel)
		self.parentPanel.Bind(wx.EVT_TIMER, self.SiteChanged, self.refreshTimer)

		self.InitUI()
		self.InitMenus()

		self.UpdateView(self.GetCurrentSite())

	def InitUI(self):
		self.sitePanel = wx.Panel(self.parentPanel, -1)
		self.sitePanel.SetSizer(wx.BoxSizer(wx.HORIZONTAL))
		siteLabel = wx.StaticText(self.sitePanel, -1, "Current Site: ", style=wx.BOLD)
		slFont = siteLabel.GetFont()
		slFont.SetWeight(wx.BOLD)
		siteLabel.SetFont(slFont)
		self.currentSite = wx.Choice(self.sitePanel, -1)
		self.loadButton = wx.Button(self.sitePanel, -1, "Load")
		self.deleteButton = wx.Button(self.sitePanel, -1, "Delete")
		self.writeButton = wx.Button(self.sitePanel, -1, "Write DB")

		self.sitePanel.GetSizer().Add(siteLabel, 0, border=5, flag=wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER_VERTICAL)
		self.sitePanel.GetSizer().Add(self.currentSite, 0, border=5, flag=wx.TOP|wx.BOTTOM|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL)
		self.sitePanel.GetSizer().Add(self.loadButton, 0, border=5, flag=wx.TOP|wx.BOTTOM|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL)
		self.sitePanel.GetSizer().Add(self.deleteButton, 0, border=5, flag=wx.TOP|wx.BOTTOM|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL)
		self.sitePanel.GetSizer().Add(self.writeButton, 0, border=5, flag=wx.TOP|wx.BOTTOM|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL)
		self.parentPanel.GetSizer().Add(self.sitePanel, 0, border=10, flag=wx.BOTTOM | wx.LEFT)

		self.dataPanel = wx.Panel(self.parentPanel, -1)
		self.dataPanel.SetSizer(wx.BoxSizer(wx.VERTICAL))
		self.dataPanel.SetBackgroundColour('white')
		self.parentPanel.GetSizer().Add(self.dataPanel, 0, border=10, flag=wx.BOTTOM | wx.LEFT)

		self.UpdateSites()
		self.parentPanel.Bind(wx.EVT_CHOICE, self.SiteChanged, self.currentSite)
		self.parentPanel.Bind(wx.EVT_BUTTON, self.LoadPressed, self.loadButton)
		self.parentPanel.Bind(wx.EVT_BUTTON, self.DeletePressed, self.deleteButton)
		self.parentPanel.Bind(wx.EVT_BUTTON, self.WritePressed, self.writeButton)

	def WritePressed(self, event):
		site = self.GetCurrentSite()
		site.SyncToGui()
		dbu.SaveSite(site)
	
	def InitMenus(self):
		# master dictionary of all menu items
		self.menuIds = {'Load': 1,
						'View': 2,
						'Export': 3,
						'Delete': 4,
						'Import Cull Table': 10,
						'Enable All': 101,
						'Disable All': 102}

		self.holeMenuItems = ['Load', 'View', 'Export', 'Delete']
		self.holeSetMenuItems = ['Load', 'Export', 'Enable All', 'Disable All', 'Import Cull Table']
		self.savedTableMenuItems = ['View', 'Export', 'Delete']
		self.logTableMenuItems = ['View', 'Delete']
		self.tableMenuItems = ['View', 'Delete']

	def BuildMenu(self, itemList):
		self.menu = wx.Menu()
		for key in itemList:
			self.menu.Append(self.menuIds[key], key)

	def MakeActionsButton(self, buttonParent):
		#sprocketImage = wx.Bitmap("icons/sprocket.png")
		return wx.Button(buttonParent, -1, "Actions...")
	
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
		button = self.MakeActionsButton(panel)
		sizer.Add(button, 0)
		#sizer.Add(holeSet.gui.actionButton, 0)
		sizer.AddSpacer((85,-1))
		sizer.Add(holeSet.gui.rangeText, 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.AddSpacer((5,-1))
		sizer.Add(holeSet.gui.continuousChoice, 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.AddSpacer((5,-1))
		sizer.Add(holeSet.gui.decimateText, 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.AddSpacer((5,-1))
		sizer.Add(holeSet.gui.smoothText, 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.AddSpacer((5,-1))
		
		sizer.Add(holeSet.gui.cullEnabledCb, 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.Add(holeSet.gui.cullInfo, 0, border=5, flag=wx.LEFT|wx.BOTTOM)

		panel.Bind(wx.EVT_BUTTON, lambda event, args=holeSet: self.PopActionsMenu(event, args), button)#holeSet.gui.actionButton)
		panel.Bind(wx.EVT_MENU, lambda event, args=holeSet: self.HandleHoleSetMenu(event, args))

		toPanel.GetSizer().Add(panel)

	# brg 10/30/2014: On OSX, setting tooltip at panel creation time (e.g. in AddHoleRow())
	# stops working as soon as the interface changes in any way. Changing the current Note's page,
	# changing sites, even minimizing a CollapsiblePane causes tooltips to stop appearing.
	# Setting tooltip on mouseover works consistently. 
	def ShowTooltip(self, event, hole):
		panel = event.GetEventObject()
		panel.SetToolTip(wx.ToolTip(hole.GetTooltipStr()))
	
	def AddHoleRow(self, toPanel, hole):
		panel, sizer = self.NewPanel(toPanel)

		hole.gui = HoleGUI(hole, panel)
		
		#print "AddHoleRow: tooltip = {}".format(hole.GetTooltipStr())
		#panel.SetToolTip(wx.ToolTip(hole.GetTooltipStr()))

		sizer.Add(wx.StaticText(panel, -1, hole.name, size=(75,-1), style=wx.ALIGN_CENTRE), 0, border=10, flag=wx.RIGHT|wx.LEFT|wx.BOTTOM)
		#button = wx.Button(panel, -1, "Actions...")
		button = self.MakeActionsButton(panel)
		sizer.Add(button, 0, border=5, flag=wx.BOTTOM)
		sizer.Add(hole.gui.enabledCb, 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.Add(wx.StaticText(panel, -1, "Range: (" + hole.min + ", " + hole.max + ")"), 0, border=5, flag=wx.LEFT|wx.BOTTOM)
#		sizer.Add(wx.StaticText(panel, -1, "File: " + hole.file), 0, border=5, flag=wx.LEFT|wx.BOTTOM)
#		sizer.Add(wx.StaticText(panel, -1, "Last updated: " + hole.updatedTime), 0, border=5, flag=wx.LEFT|wx.BOTTOM)
#		sizer.Add(wx.StaticText(panel, -1, "By: " + hole.byWhom), 0, border=5, flag=wx.LEFT|wx.BOTTOM)
#		sizer.Add(wx.StaticText(panel, -1, "Source: " + hole.origSource), 0, border=5, flag=wx.LEFT|wx.BOTTOM)

		panel.Bind(wx.EVT_BUTTON, lambda event, args=hole: self.PopActionsMenu(event, args), button)
		panel.Bind(wx.EVT_MENU, lambda event, args=hole: self.HandleHoleMenu(event, args))
		panel.Bind(wx.EVT_ENTER_WINDOW, lambda event, args=hole: self.ShowTooltip(event, args))

		toPanel.GetSizer().Add(panel)

	def AddSavedTableRow(self, toPanel, site, name):
		panel, sizer = self.NewPanel(toPanel)
		
		gui = SavedTableGUI(site, name, panel)

		sizer.Add(wx.StaticText(panel, -1, name, size=(90,-1), style=wx.ALIGN_CENTRE), 0, border=10, flag=wx.RIGHT|wx.LEFT|wx.BOTTOM)
		button = self.MakeActionsButton(panel)#wx.Button(panel, -1, "Actions...")
		sizer.Add(button, 0, border=5, flag=wx.BOTTOM|wx.LEFT)
		sizer.Add(gui.tableChoice, 0, border=5, flag=wx.BOTTOM|wx.LEFT)
		sizer.Add(gui.enabledCb, 0, border=5, flag=wx.BOTTOM|wx.LEFT)
		
		panel.Bind(wx.EVT_BUTTON, lambda event, args=gui: self.PopActionsMenu(event, args), button)
		panel.Bind(wx.EVT_MENU, lambda event, args=gui: self.HandleSavedTableMenu(event, args))

		toPanel.GetSizer().Add(panel)

		return gui

	# for classes derived from TableData
	def AddTableRow(self, toPanel, site, table):
		panel, sizer = self.NewPanel(toPanel)
		
		table.gui = TableGUI(site, table, panel)
		
		sizer.Add(wx.StaticText(panel, -1, table.GetName(), size=(90,-1), style=wx.ALIGN_CENTRE), 0, border=10, flag=wx.RIGHT|wx.LEFT|wx.BOTTOM)
		button = self.MakeActionsButton(panel) #wx.Button(panel, -1, "Actions...")
		sizer.Add(button, 0, border=5, flag=wx.BOTTOM)
		sizer.Add(table.gui.enabledCb, 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.Add(wx.StaticText(panel, -1, "File: " + table.file), 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.Add(wx.StaticText(panel, -1, "Last updated: " + table.updatedTime), 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.Add(wx.StaticText(panel, -1, "By: " + table.byWhom), 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.Add(wx.StaticText(panel, -1, "Source: " + table.origSource), 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		
		panel.Bind(wx.EVT_BUTTON, lambda event, args=table.gui: self.PopActionsMenu(event, args), button)
		panel.Bind(wx.EVT_MENU, lambda event, args=table.gui: self.HandleTableMenu(event, args))

		toPanel.GetSizer().Add(panel)

	def AddLogTableRow(self, toPanel, site, table):
		panel, sizer = self.NewPanel(toPanel)

		table.gui = LogTableGUI(site, table, panel)

		sizer.Add(wx.StaticText(panel, -1, table.GetName(), size=(90,-1), style=wx.ALIGN_CENTRE), 0, border=10, flag=wx.RIGHT|wx.LEFT|wx.BOTTOM)
		button = self.MakeActionsButton(panel) #wx.Button(panel, -1, "Actions...")
		sizer.Add(button, 0, border=5, flag=wx.BOTTOM)
		sizer.Add(table.gui.enabledCb, 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.Add(wx.StaticText(panel, -1, "File: " + table.file), 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.Add(wx.StaticText(panel, -1, "Last updated: " + table.updatedTime), 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.Add(wx.StaticText(panel, -1, "By: " + table.byWhom), 0, border=5, flag=wx.LEFT|wx.BOTTOM)
		sizer.Add(wx.StaticText(panel, -1, "Source: " + table.origSource), 0, border=5, flag=wx.LEFT|wx.BOTTOM)

		panel.Bind(wx.EVT_CHECKBOX, self.LogCheckboxChanged, table.gui.enabledCb)
		panel.Bind(wx.EVT_BUTTON, lambda event, args=table.gui: self.PopActionsMenu(event, args), button)
		panel.Bind(wx.EVT_MENU, lambda event, args=table.gui: self.HandleLogTableMenu(event, args))

		toPanel.GetSizer().Add(panel)

	# 1/13/2014 brgtodo?: Retain GUI objects rather than rebuilding GUI whenever site changes?
	def UpdateView(self, site):
		self.panes = []
		self.dataPanel.GetSizer().Clear(True)

		if site is None:
			msg = "No sites found. Use the Import > Hole Data... menu item to import hole data and create a site."
			self.dataPanel.GetSizer().Add(wx.StaticText(self.dataPanel, -1, msg))
			return
		
		# Add Holes
		for hsKey in sorted(site.holeSets.keys()): # sort by holeset type
			hs = site.holeSets[hsKey]
			#print "holeset type = {}".format(hs.type)
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
		self.dataPanel.GetSizer().Add(stPane, 0, border=5, flag=wx.ALL)
		self.dataPanel.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.PaneChanged, stPane)
		self.panes.append(stPane)

		site.affineGui = self.AddSavedTableRow(stPane.GetPane(), site, "Affine")
		site.spliceGui = self.AddSavedTableRow(stPane.GetPane(), site, "Splice")
		site.eldGui = self.AddSavedTableRow(stPane.GetPane(), site, "ELD")

		ltPane = wx.CollapsiblePane(self.dataPanel, -1, "Downhole Logs", style=wx.CP_NO_TLW_RESIZE)
		ltPane.GetPane().SetSizer(wx.BoxSizer(wx.VERTICAL))
		self.dataPanel.GetSizer().Add(ltPane, 0, border=5, flag=wx.ALL)
		self.dataPanel.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.PaneChanged, ltPane)
		self.panes.append(ltPane)
		for lt in site.logTables:
			self.AddLogTableRow(ltPane.GetPane(), site, lt)

		amPane = wx.CollapsiblePane(self.dataPanel, -1, "Age Models", style=wx.CP_NO_TLW_RESIZE)
		amPane.GetPane().SetSizer(wx.BoxSizer(wx.VERTICAL))
		self.dataPanel.GetSizer().Add(amPane, 0, border=5, flag=wx.ALL)
		self.dataPanel.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.PaneChanged, amPane)
		self.panes.append(amPane)
		for at in site.ageTables:
			self.AddTableRow(amPane.GetPane(), site, at)
		for st in site.seriesTables:
			self.AddTableRow(amPane.GetPane(), site, st)
			
		imPane = wx.CollapsiblePane(self.dataPanel, -1, "Image Data", style=wx.CP_NO_TLW_RESIZE)
		imPane.GetPane().SetSizer(wx.BoxSizer(wx.VERTICAL))
		self.dataPanel.GetSizer().Add(imPane, 0, border=5, flag=wx.ALL)
		self.dataPanel.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.PaneChanged, imPane)
		self.panes.append(imPane)
		for it in site.imageTables:
			self.AddTableRow(imPane.GetPane(), site, it)

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

	def UpdateSites(self, selectSite=None):
		self.currentSite.Clear()
		for siteKey in sorted(self.siteDict):
			site = self.siteDict[siteKey]
			self.currentSite.Append(site.name, clientData=site)
		if self.currentSite.GetCount() > 0:
			if selectSite is not None:
				self.currentSite.SetStringSelection(selectSite)
			else:
				self.currentSite.SetSelection(0)
			self.SiteChanged()
		else: # no sites
			self.UpdateView(None) # clear deleted site's GUI if present

	def SiteChanged(self, evt=None):
		if self.refreshTimer.IsRunning():
			self.refreshTimer.Stop()
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
			
	""" Delete current site """
	def DeletePressed(self, evt):
		site = self.GetCurrentSite()
		result = glb.OnShowMessage("About", "Are you sure you want to delete {}, including all data and saved tables?".format(site.name), 2)
		if result == wx.ID_OK:
			dbu.DeleteSite(site)
			del self.siteDict[site.name]
			self.UpdateSites()

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
		elif isinstance(obj, SavedTableGUI):
			self.BuildMenu(self.savedTableMenuItems)
		elif isinstance(obj, LogTableGUI):
			self.BuildMenu(self.logTableMenuItems)
		elif isinstance(obj, TableGUI):
			self.BuildMenu(self.tableMenuItems)
			
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
		elif evt.GetId() == self.menuIds['Delete']:
			site = self.GetCurrentSite()
			self.DeleteFile(hole.file)
			site.SyncToData()
			self.refreshTimer.Start(200)

	def HandleHoleSetMenu(self, evt, holeSet):
		holeSet.site.SyncToGui()
		if evt.GetId() == self.menuIds['Load']:
			holeList = holeSet.holes.values()
			self.LoadHoles(holeList)
		elif evt.GetId() == self.menuIds['Export']:
			holeList = holeSet.holes.values()
			self.ExportHoles(holeList)
		elif evt.GetId() == self.menuIds['Enable All'] or evt.GetId() == self.menuIds['Disable All']:
			for hole in holeSet.holes.values():
				hole.gui.enabledCb.SetValue(evt.GetId() == self.menuIds['Enable All'])
		elif evt.GetId() == self.menuIds['Import Cull Table']:
			newCullTable = dbu.ImportCullTable(self.parent, holeSet)
			if newCullTable is not None:
				holeSet.cullTable = newCullTable
				holeSet.site.SyncToData()
				
	def HandleSavedTableMenu(self, evt, gui):
		gui.site.SyncToGui()
		if evt.GetId() == self.menuIds['View']:
			curTable = gui.GetCurrentTable()
			self.ViewFile(curTable.file)
		if evt.GetId() == self.menuIds['Delete']:
			curTable = gui.GetCurrentTable()
			self.DeleteFile(curTable.file)
			gui.site.SyncToData()
			
	def HandleLogTableMenu(self, evt, gui):
		gui.site.SyncToGui()
		if evt.GetId() == self.menuIds['View']:
			self.ViewFile(gui.logTable.file)
		elif evt.GetId() == self.menuIds['Delete']:
			self.DeleteFile(gui.logTable.file)
			gui.site.SyncToData()
			self.refreshTimer.Start(200)

	def HandleTableMenu(self, evt, gui):
		gui.SyncToGui()
		if evt.GetId() == self.menuIds['View']:
			self.ViewFile(gui.table.file)
		elif evt.GetId() == self.menuIds['Delete']:
			self.DeleteFile(gui.table.file)
			gui.site.SyncToData()
			self.refreshTimer.Start(200)
	
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
		sitePath = glb.DBPath + 'db/' + site.GetDir()

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

			# set type's range if necessary
			typeRangeFound = False
			for range in self.parent.Window.range:
				if range[0] == type:
					typeRangeFound = True
					break

			if not typeRangeFound:
				holeRange = MakeRangeList(hole, type)
				self.parent.Window.range.append(holeRange)

		# load cull tables
		culledTypes = []
		for hole in holeList:
			if hole.holeSet.type not in culledTypes and hole.holeSet.IsCullEnabled():
				coretype, annot = self.parent.TypeStrToInt(hole.holeSet.type)
				py_correlator.openCullTable(sitePath + hole.holeSet.cullTable.file, coretype, annot)
				culledTypes.append(hole.holeSet.type)

		# smoothing occurs at HoleSet level
		smoothedTypes = []
		for hole in holeList:
			if hole.holeSet.type not in smoothedTypes and hole.holeSet.smooth is not None:
				sm = hole.holeSet.smooth
				py_correlator.smooth(hole.holeSet.type, sm.width, sm.unit)
				smoothedTypes.append(hole.holeSet.type)

		# load log
		logLoaded = False
		for log in site.logTables:
			if log.enable:
				py_correlator.openLogFile(sitePath + log.file, int(log.dataIndex))
				if log.decimate > 1:
					py_correlator.decimate('Log', log.decimate)
				if log.smooth.IsValid():
					py_correlator.smooth('Log', log.smooth.width, log.smooth.unit)
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
		self.parent.OnInitDataUpdate()
		tableLoaded = [False, False, False]
		for at in site.affineTables:
			if at.enable:
				py_correlator.openAttributeFile(sitePath + at.file, 0)
				tableLoaded[0] = True
				break
		for st in site.spliceTables:
			if st.enable:
				ret = py_correlator.openSpliceFile(sitePath + st.file)
				print "trying to load splice: {}".format(sitePath + st.file)
				if ret == 'error':
					glb.OnShowMessage("Error", "Couldn't create splice record(s)", 1)
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
			self.parent.filterPanel.OnRegisterHole("Spliced Records")

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
		if logLoaded:
			self.parent.Window.ShowLog = True
			self.parent.filterPanel.OnRegisterHole("Log")

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
		
		self.parent.compositePanel.saveButton.Enable(True)
		if self.parent.Window.LogData == [] :
			self.parent.splicePanel.saveButton.Enable(True)
			self.parent.splicePanel.altButton.Enable(True)
			self.parent.splicePanel.newButton.Enable(True)
		else :
			self.parent.eldPanel.saveButton.Enable(True)
			self.parent.autoPanel.saveButton.Enable(True)
			self.parent.splicePanel.altButton.Enable(False)
			self.parent.splicePanel.newButton.Enable(False)

	def GetFileHeader(self, path):
		if path.find(".xml", 0) >= 0:
			path = xml.ConvertFromXML(path, glb.LastDir)

		header = ""
		with open(path, 'r+') as f:
			line = f.readline().rstrip()
			c1 = line[0].capitalize()
			if c1 == 'L' or c1 == "#": # "Leg", or comment brgtodo check "Exp[edition]"?
				header = line

		return header

	def DoImportHoleData(self):
		opendlg = wx.FileDialog(self.parent, "Select core data files", glb.LastDir, "", "*.*", style=wx.MULTIPLE)
		if opendlg.ShowModal() == wx.ID_OK:
			glb.LastDir = opendlg.GetDirectory()
			paths = opendlg.GetPaths()
			headerSet = set([self.GetFileHeader(path) for path in paths])
			if len(headerSet) == 1: # do all header lines match?
				self.ImportHoleData(paths, headerSet.pop()) # pop lone header string
			else:
				glb.OnShowMessage("Error", "Unmatched headers found, only one datatype can be imported at a time", 1)
		opendlg.Destroy()

	def ImportHoleData(self, paths, header):
		dlg = dialog.ImportHoleDataDialog(self.dataFrame, -1, paths, header, self.siteDict)
		if dlg.ShowModal() == wx.ID_OK:
			curSite = self.GetCurrentSite()
			if curSite is not None and dlg.importedSite == curSite.name:
				self.UpdateView(curSite) # update to show just-imported data
			elif dlg.importedSite not in self.currentSite.GetStrings():
				self.UpdateSites(dlg.importedSite) # add new site to "Current Site" Choice
				
	def DeleteFile(self, filename):
		if glb.OnShowMessage("About", "Are you sure you want to delete {}?".format(filename), 2) != wx.ID_OK:
			return
		curSite = self.GetCurrentSite()
		filepath = dbu.GetSiteFilePath(curSite.name, filename)
		dbu.DeleteFile(filepath)
		curSite.DeleteTable(filename)
		
	def ViewFile(self, filename):
		holefile = glb.DBPath + "db/" + self.GetCurrentSite().GetDir() + filename
		self.dataFrame.fileText.Clear()
		self.dataFrame.fileText.LoadFile(holefile)
		self.dataFrame.sideNote.SetSelection(3) # File View tab

	def ExportHoles(self, holeList):
		exportDlg = dialog.ExportCoreDialog(self.dataFrame)
		exportDlg.Centre()
		if exportDlg.ShowModal() == wx.ID_OK:
			fileDlg = wx.FileDialog(self.dataFrame, "Select Directory for Export", glb.LastDir, style=wx.SAVE)
			if fileDlg.ShowModal() == wx.ID_OK:
				self.parent.OnNewData(None)

				siteDir = holeList[0].holeSet.site.GetDir()
				path = glb.DBPath + 'db/' + siteDir

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
 						glb.OnShowMessage("Error", "Could not Make Splice Records", 1)
					applied = "splice"
				elif exportDlg.splice.GetValue() == True and splice_item == None :
 					glb.OnShowMessage("Error", "Can't export, active splice table required.", 1)
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
# 						glb.OnShowMessage("Error", "Need Log to Export ELD", 1)
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
					glb.OnShowMessage("Information", "Export successful", 1)
				else:
					glb.OnShowMessage("Error", "Export failed", 1)

			fileDlg.Destroy()
		exportDlg.Destroy()

	def GetCurrentSite(self):
		if self.currentSite.GetCount() > 0:
			siteIndex = self.currentSite.GetSelection()
			return self.currentSite.GetClientData(siteIndex)
		return None

class TableGUI:
	def __init__(self, site, table, panel):
		self.site = site
		self.table = table
		self.enabledCb = wx.CheckBox(panel, -1, "Enable", size=(80,-1))
		self.SyncToData()
		
	def SyncToData(self):
		self.enabledCb.SetValue(self.table.IsEnabled())
		
	def SyncToGui(self):
		self.table.enable = self.enabledCb.GetValue()

class HoleGUI:
	def __init__(self, hole, panel):
		self.hole = hole
		self.enabledCb = wx.CheckBox(panel, -1, "Enable", size=(80,-1))
		self.SyncToData()

	def SyncToData(self):
		self.enabledCb.SetValue(self.hole.IsEnabled())

	def SyncToGui(self):
		self.hole.enable = self.enabledCb.GetValue()

class HoleSetGUI:
	def __init__(self, holeSet, panel):
		self.holeSet = holeSet
		self.rangeText = wx.StaticText(panel, -1, "")
		self.continuousChoice = wx.Choice(panel, -1, choices=['Continuous','Discrete'])
		self.decimateText = wx.StaticText(panel,  -1, "")
		self.smoothText = wx.StaticText(panel, -1, "")
		self.cullEnabledCb = wx.CheckBox(panel, -1, "Enable Cull")
		self.cullInfo = wx.StaticText(panel, -1, "")
		self.SyncToData()

	def SyncToData(self):
		self.continuousChoice.SetSelection(0 if self.holeSet.continuous else 1)
		self.rangeText.SetLabel(MakeRangeString(self.holeSet.min, self.holeSet.max))
		contIdx = 0 if self.holeSet.continuous else 1
		self.continuousChoice.SetSelection(contIdx)
		self.decimateText.SetLabel(MakeDecimateString(self.holeSet.decimate))
		self.smoothText.SetLabel(self.holeSet.GetSmoothStr())
		self.cullEnabledCb.Enable(self.holeSet.HasCull())
		self.cullEnabledCb.SetValue(self.holeSet.IsCullEnabled())
		if self.holeSet.HasCull():
			cullPath = dbu.GetSiteFilePath(self.holeSet.site.name, self.holeSet.cullTable.file)
			cullInfoStr = dbu.ReadCullInfo(cullPath)
			self.cullInfo.SetLabel('[' + cullInfoStr + ']')

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
		
	def GetCurrentTable(self):
		result = None
		tableList = self.GetTables()
		curTableName = self.tableChoice.GetStringSelection()
		for tab in tableList:
			if tab.file == curTableName:
				result = tab
				break
		return result

class LogTableGUI:
	def __init__(self, site, logTable, panel):
		self.site = site
		self.logTable = logTable
		self.enabledCb = wx.CheckBox(panel, -1, "Enable")
		self.SyncToData()

	def SyncToData(self):
		self.enabledCb.SetValue(self.logTable.enable)

	def SyncToGui(self):
		self.logTable.enable = self.enabledCb.GetValue()
