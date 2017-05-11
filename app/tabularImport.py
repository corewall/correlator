'''
Routines and classes for loading of tabular data and conversion to target formats
'''

import os
import sys

import pandas
import wx
import wx.grid

import dialog

class SectionSummary:
    def __init__(self, name, dataframe):
        self.name = name
        self.dataframe = dataframe
        
    @classmethod
    def createWithFile(cls, filepath):
        dataframe = readFile(filepath)
        stringColumns = ['Core', 'Section']
        forceStringDatatype(stringColumns, dataframe)
        return cls(os.path.basename(filepath), dataframe)
    
    def containsCore(self, site, hole, core):
        cores = self._findCores(site, hole, core)
        return not cores.empty
    
    def containsSection(self, site, hole, core, section):
        sections = self._findSection(site, hole, core, section)
        return not sections.empty
    
    # return depth of top of top section, bottom of bottom section
    def getCoreRange(self, site, hole, core):
        cores = self._findCores(site, hole, core)
        cores = cores[(cores.Section != "CC")] # omit CC section for time being
        if not cores.empty:
            coremin = cores['TopDepth'].min()
            coremax = cores['BottomDepth'].max()
            return coremin, coremax
        return None
    
    # return type of core
    def getCoreType(self, site, hole, core):
        cores = self._findCores(site, hole, core)
        cores = cores[(cores.Section != "CC")] # omit CC section for time being
        if not cores.empty:
            return cores.iloc[0]['CoreType']
        return None    
    
    def getSites(self):
        return set(self.dataframe['Site'])
    
    def getHoles(self):
        return set(self.dataframe['Hole'])
    
    def getCores(self, hole):
        return set(self.dataframe[self.dataframe['Hole'] == hole]['Core'])
        
    def getSectionTop(self, site, hole, core, section):
        return self._getSectionValue(site, hole, core, section, 'TopDepth')
    
    def getSectionBot(self, site, hole, core, section):
        return self._getSectionValue(site, hole, core, section, 'BottomDepth')
    
    def getSectionCoreType(self, site, hole, core, section):
        return self._getSectionValue(site, hole, core, section, 'CoreType')
    
    def getSectionAtDepth(self, site, hole, core, depth):
        sec = self._findSectionAtDepth(site, hole, core, depth)
        return sec
    
    def sectionDepthToTotal(self, site, hole, core, section, secDepth):
        top = self.getSectionTop(site, hole, core, section)
        result = top + secDepth / 100.0 # cm to m
        #print "section depth {} in section {} = {} overall".format(secDepth, section, result)        
        return result
    
    def checkStrType(self, argList):
        for arg in argList:
            if not isinstance(arg, str):
                print "SectionSummary ERROR: encountered non-str query element {}".format(arg)
    
    def _findCores(self, site, hole, core):
        # omitting core here and below since it's an integer at present
        self.checkStrType([site, hole])
        df = self.dataframe
        cores = df[(df.Site == site) & (df.Hole == hole) & (df.Core == core)]
        if cores.empty:
            print "SectionSummary: Could not find core {}-{}{}".format(site, hole, core)
        return cores

    def _findSection(self, site, hole, core, section):
        self.checkStrType([site, hole, section])
        df = self.dataframe
        section = df[(df.Site == site) & (df.Hole == hole) & (df.Core == core) & (df.Section == section)]
        if section.empty:
            print "SectionSummary: Could not find {}-{}{}-{}".format(site, hole, core, section)
        return section
    
    def _findSectionAtDepth(self, site, hole, core, depth):
        self.checkStrType([site, hole])
        df = self.dataframe
        section = df[(df.Site == site) & (df.Hole == hole) & (df.Core == core) & (depth >= df.TopDepth) & (depth <= df.BottomDepth)]
        if not section.empty:
            return section.iloc[0]['Section']
        return None    
    
    def _getSectionValue(self, site, hole, core, section, columnName):
        self.checkStrType([site, hole, section])
        section = self._findSection(site, hole, core, section)
        return section.iloc[0][columnName]
    
class AffineTable:
    def __init__(self, name, dataframe):
        self.name = name
        self.dataframe = dataframe

class SpliceIntervalTable:
    def __init__(self, name, dataframe):
        self.name = name
        self.dataframe = dataframe

""" bridge between imported tabular columns and destination format """ 
class TabularFormat:
    req = [] # list of required column names
    def __init__(self, name, req):
        self.name = name
        self.req = req

MeasurementFormat = TabularFormat("Measurement Data",
                                  ['Exp', 'Site', 'Hole', 'Core', 'CoreType', 'Section', 'TopOffset', 'BottomOffset', 'Depth'])
SectionSummaryFormat = TabularFormat("Section Summary", 
                                     ['Exp', 'Site', 'Hole', 'Core', 'CoreType', 'Section', 'TopDepth', 'BottomDepth'])

AffineFormat = TabularFormat("Affine Table",
                             ['Site', 'Hole', 'Core', 'Core Type', 'Depth CSF (m)', 'Depth CCSF (m)', \
                              'Cumulative Offset (m)', 'Differential Offset (m)', 'Growth Rate', 'Shift Type', \
                              'Data Used', 'Quality Comment'])

AffineFormatNew = TabularFormat("Affine Table New-Fangled",
                             ['Site', 'Hole', 'Core', 'Core Type', 'Depth CSF (m)', 'Depth CCSF (m)', \
                              'Cumulative Offset (m)', 'Differential Offset (m)', 'Growth Rate', 'Shift Type', \
                              'Fixed Core', 'Fixed Tie CSF', 'Shifted Tie CSF', 'Data Used', 'Quality Comment'])

# Splice Interval Table headers: 2.0.2 b8 and earlier
# brg 1/18/2016: keeping for now, may want to convert from this format
SITFormat_202_b8 = TabularFormat("Splice Interval Table 2.0.2 b8 and earlier",
                          ['Exp', 'Site', 'Hole', 'Core', 'CoreType', 'TopSection', 'TopOffset', \
                           'TopDepthCSF', 'TopDepthCCSF', 'BottomSection', 'BottomOffset', 'BottomDepthCSF', \
                           'BottomDepthCCSF', 'SpliceType', 'DataUsed', 'Comment'])

SITFormat = TabularFormat("Splice Interval Table",
                          ['Site', 'Hole', 'Core', 'Core Type', 'Top Section', 'Top Offset', \
                           'Top Depth CSF-A', 'Top Depth CCSF-A', 'Bottom Section', 'Bottom Offset', 'Bottom Depth CSF-A', \
                           'Bottom Depth CCSF-A', 'Splice Type', 'Data Used', 'Comment'])


# Format for exported core data...may not need RunNo, RawDepth or Offset any longer?
CoreExportFormat = TabularFormat("Exported Core Data",
                                 ['Exp', 'Site', 'Hole', 'Core', 'CoreType',
                                  'Section', 'TopOffset', 'BottomOffset', 'Depth',
                                  'Data', 'RunNo', 'RawDepth', 'Offset'])

class ImportDialog(wx.Dialog):
    def __init__(self, parent, id, path, dataframe, goalFormat, allowEmptyCells=True):
        wx.Dialog.__init__(self, parent, id, size=(800,600), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        self.path = path # source file path
        self.dataframe = dataframe # pandas DataFrame read from self.path
        self.goalFormat = goalFormat
        self.allowEmptyCells = allowEmptyCells
        self.reqColMap = None # populated when all required columns have been identified
        self.lastCol = None # index of last column label selected...can't easily pass in event handlers
        self.NA = "N/A"
        
        self._createUI()
        self._populateTable()
        self._updateFileLabel()
        self._updateFormatLabel()
    
    def _populateTable(self):
        # init: adjust table's column count to match dataframe, column/row labels
        rowcount = min(len(self.dataframe), 100) + 1 # extra row for source file headers
        self.table.CreateGrid(rowcount, len(self.dataframe.columns.tolist()))
        for col in range(len(self.dataframe.columns.tolist())):
            self.table.SetColLabelValue(col, self.NA)
        self.table.SetRowLabelValue(0, "Headers")

        # populate required headers based on matches
        goalCols = findFormatColumns(self.dataframe, self.goalFormat)
        for name, col in goalCols.iteritems():
            if col is not None:
                self.table.SetColLabelValue(col, name)
        
        # read source file headers into row 1
        font = self.table.GetCellFont(0, 0)
        for col, name in enumerate(self.dataframe.columns.tolist()):
            self.table.SetCellValue(0, col, name)
            self.table.SetCellBackgroundColour(0, col, wx.Colour(192, 192, 192))
            self.table.SetCellFont(0, col, font)
        
        # fill table
        for c in range(len(self.dataframe.columns)):
            col = self.dataframe.icol(c)
            for r in range(1, rowcount):
                self.table.SetCellValue(r, c, str(col[r - 1]))
                self.table.SetReadOnly(r, c)
                self.table.SetRowLabelValue(r, str(r))
                
        self.table.AutoSize()
        
        self._createReqMenu()
        self._checkReq()

    def _createReqMenu(self):
        # setup required column menu
        self.reqMenu = wx.Menu()
        menuItems = self.goalFormat.req + [self.NA]
        for index, mi in enumerate(menuItems):
            menuIndex = index + 1 # start from 1, no zero menu index on Mac
            self.reqMenu.Append(menuIndex, mi)
            wx.EVT_MENU(self.reqMenu, menuIndex, self.OnReqMenu)
    
    def _updateFileLabel(self):
        self.fileLabel.SetLabel("File: {}".format(self.path))
        
    def _updateFormatLabel(self):
        self.formatLabel.SetLabel("Required columns for {}: {}".format(self.goalFormat.name, ', '.join(self.goalFormat.req)))
        
    def _updateHelpLabel(self, helptext):
        self.helpText.SetLabel(helptext)
        
    def _updateWarnLabel(self, warntext):
        self.warnText.SetLabel(warntext)
    
    def _createUI(self):
        self.SetTitle("Import {}".format(self.goalFormat.name))
        
        sz = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sz)
        
        self.fileLabel = wx.StaticText(self, -1, "File: {}".format(self.NA))
        sz.Add(self.fileLabel, 0, wx.EXPAND | wx.ALL, 10)
        
        self.table = wx.grid.Grid(self, -1)
        self.table.DisableDragRowSize()
        sz.Add(self.table, 1, wx.EXPAND)

        panel = wx.Panel(self, -1)
        
        # required columns + help/warn text subpanel
        textpanel = wx.Panel(panel, -1)
        tpsz = wx.BoxSizer(wx.VERTICAL)
        self.formatLabel = wx.StaticText(textpanel, -1, "[Format]: {}".format(self.NA))
        tpsz.Add(self.formatLabel, 0, wx.EXPAND | wx.BOTTOM, 10)
        self.helpText = wx.StaticText(textpanel, -1, "I am some helpful text.")
        self.warnText = wx.StaticText(textpanel, -1, "I am warning text")
        self.warnText.SetForegroundColour(wx.RED)
        tpsz.Add(self.helpText, 0, wx.EXPAND)
        tpsz.Add(self.warnText, 0, wx.EXPAND)
        textpanel.SetSizer(tpsz)

        # bottom text/button panel        
        bpsz = wx.BoxSizer(wx.HORIZONTAL)
        self.importButton = wx.Button(panel, -1, "Import")
        self.importButton.Enable(False)
        self.Bind(wx.EVT_BUTTON, self.OnImport, self.importButton)
        self.cancelButton = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        bpsz.Add(textpanel, 1, wx.EXPAND)
        bpsz.Add(self.importButton, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        bpsz.Add(self.cancelButton, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        panel.SetSizer(bpsz)
        
        sz.Add(panel, 0, wx.EXPAND | wx.ALL | wx.ALIGN_RIGHT, 10)
        
        self.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.OnSelectLabel, self.table)
        
    def _checkReq(self):
        # get current column names
        curNames = []
        for col in range(self.table.GetNumberCols()):
            curNames.append(self.table.GetColLabelValue(col))
        
        # for each required column, if we have a match in column names, add to "good" list
        missing = []
        colmap = {}
        for reqCol in self.goalFormat.req:
            if reqCol not in curNames:
                missing.append(reqCol)
            else:
                colmap[reqCol] = curNames.index(reqCol)
                
        if len(missing) == 0:
            self.importButton.Enable(True)
            self._updateHelpLabel("All required columns identified, click Import!")
            self.reqColMap = colmap
        else:
            self.importButton.Enable(False)
            self._updateHelpLabel("Click column labels to identify required columns: {}".format(', '.join(missing)))
            self.reqColMap = None
            
        # warnings
        nonNANames = [n for n in curNames if n != self.NA]
        if len(set(nonNANames)) < len(nonNANames):
            mulsels = list(set([n for n in nonNANames if nonNANames.count(n) > 1]))
            msstr = ', '.join(mulsels)
            self._updateWarnLabel("Warning: Multiple columns selected for {}".format(msstr))
        else:
            self._updateWarnLabel("")

    # check user-selected columns for empty cells
    def _hasEmptyCells(self):
        goaldf = reorderColumns(self.dataframe, self.reqColMap, self.goalFormat)
        empty = False
        for col in goaldf.columns.tolist():
            if goaldf[col].isnull().sum() > 0: # count NaN cells
                empty = True
                break
        return empty

    def OnImport(self, event):
        if not self.allowEmptyCells and self._hasEmptyCells():
            errbox(self, "One or more columns selected for import contain empty cells")
        else:
            self.EndModal(wx.ID_OK)
        
    def OnSelectLabel(self, event):
        selCol = event.GetCol()
        if selCol >= 0: # row label column index = -1
            self.lastCol = selCol
            self.PopupMenu(self.reqMenu, event.GetPosition())
            
    def OnReqMenu(self, event):
        mi = self.reqMenu.FindItemById(event.GetId())
        self.table.SetColLabelValue(self.lastCol, mi.GetText())
        #print "Source column: {}, item {}".format(self.lastCol, event.GetId())
        self._checkReq()
        
# with GUI, select and import a file, returning a SectionSummary (to be generalized)
def doImport(parent, goalFormat, path=None, allowEmptyCells=True):
    secSumm = None
    if path is None:
        path = selectFile(parent, goalFormat)
    if path is not None:
        dataframe = parseFile(parent, path, goalFormat, checkcols=True)
        if dataframe is not None:
            dlg = ImportDialog(parent, -1, path, dataframe, goalFormat, allowEmptyCells)
            if dlg.ShowModal() == wx.ID_OK:
                dataframe = reorderColumns(dlg.dataframe, dlg.reqColMap, goalFormat)
                name = os.path.basename(dlg.path)
                secSumm = SectionSummary(name, dataframe)
    return secSumm, path

def _columnHeadersMatch(chLists):
    columnsMatch = True
    if len(chLists) > 1:
        ch1 = chLists[0]
        for ch in chLists[1:]:
            if ch != ch1:
                columnsMatch = False
                break
    return columnsMatch

def doMultiImport(parent, goalFormat, allowEmptyCells=True):
    secSummMap = {}
    paths = selectFiles(parent, goalFormat)
    if len(paths) > 0:
        # confirm all files have same column headers
        chLists = []
        for p in paths:
            df = parseFile(parent, p, goalFormat, checkcols=True)
            chLists.append(list(df.columns.values))
        print "column sets:\n{}".format(chLists)
        if not _columnHeadersMatch(chLists):
            errbox(parent, "For multiple file import, all files must have identical column headers in name and order.")
            return
        else:
            print "1 set found for {}".format(len(chLists))
            
        importPath = paths[0]
        importDataframe = parseFile(parent, importPath, goalFormat, checkcols=True)
        dlg = ImportDialog(parent, -1, importPath, importDataframe, goalFormat, allowEmptyCells)
        if dlg.ShowModal() == wx.ID_OK:
            for p in paths:
                df = parseFile(parent, p, goalFormat, checkcols=True)
                reorderedDf = reorderColumns(df, dlg.reqColMap, goalFormat)
                name = os.path.basename(p)
                secSummMap[p] = SectionSummary(name, reorderedDf)

    return secSummMap


# brgtodo: generalize Import methods, they're all the same except for the
# object they create!
def doAffineImport(parent, goalFormat, path=None):
    sit = None
    if path is None:
        path = selectFile(parent, goalFormat)
    if path is not None:
        dataframe = parseFile(parent, path, goalFormat, checkcols=True)
        if dataframe is not None:
            dlg = ImportDialog(parent, -1, path, dataframe, goalFormat)
            if dlg.ShowModal() == wx.ID_OK:
                dataframe = reorderColumns(dlg.dataframe, dlg.reqColMap, goalFormat)

                # 1/12/2016 brg: Importing legacy tab+space delimited files into Excel, then exporting
                # as CSV to import into Correlator can result in cells with whitespace following text,
                # which confuses e.g. site and hole name-matching. Strip all whitespace in cells.
                stripCells(dataframe)
                
                name = os.path.basename(dlg.path)
                sit = AffineTable(name, dataframe)
    return sit

def doSITImport(parent, goalFormat, path=None):
    sit = None
    if path is None:
        path = selectFile(parent, goalFormat)
    if path is not None:
        dataframe = parseFile(parent, path, goalFormat, checkcols=True)
        if dataframe is not None:
            dlg = ImportDialog(parent, -1, path, dataframe, goalFormat)
            if dlg.ShowModal() == wx.ID_OK:
                dataframe = reorderColumns(dlg.dataframe, dlg.reqColMap, goalFormat)
                name = os.path.basename(dlg.path)
                sit = SpliceIntervalTable(name, dataframe)
    return sit


def readFile(filepath):
    srcfile = open(filepath, 'rU')
    dataframe = pandas.read_csv(srcfile, sep=None, skipinitialspace=True, engine='python')
    srcfile.close()
    return dataframe

def writeToFile(dataframe, filepath):
    dataframe.to_csv(filepath, index=False)

""" find column names in dataframe matching those required by format """
def findFormatColumns(dataframe, format):
    colmap = dict().fromkeys(format.req)
    for key in colmap.keys():
        if key in dataframe.dtypes.keys():
            colmap[key] = dataframe.columns.get_loc(key)
    return colmap

""" returns new dataframe with columns in order specified by colmap """
def reorderColumns(dataframe, colmap, format):
    newmap = {}
    for colName in colmap.keys():
        index = colmap[colName]
        if index is not None:
            newmap[colName] = dataframe.icol(index)
    df = pandas.DataFrame(newmap, columns=format.req)
    return df

""" strip whitespace from dataframe cells """ 
def stripCells(dataframe):
    for c in dataframe.columns:
        try:
            dataframe[c] = dataframe[c].str.strip()
        except:
            pass

def errbox(parent, msg):
    md = dialog.MessageDialog(parent, "Error", msg, 1)
    md.ShowModal()

def selectFile(parent, goalFormat):
    path = None
    dlg = wx.FileDialog(parent, "Select {} File".format(goalFormat.name), wildcard="CSV Files (*.csv)|*.csv", style=wx.OPEN)
    if dlg.ShowModal() == wx.ID_OK:
        path = dlg.GetPath()
    return path

def selectFiles(parent, goalFormat):
    paths = []
    dlg = wx.FileDialog(parent, "Select {} Files".format(goalFormat.name), wildcard="CSV Files (*.csv)|*.csv", style=wx.OPEN|wx.MULTIPLE)
    if dlg.ShowModal() == wx.ID_OK:
        paths = dlg.GetPaths()
    return paths

def parseFile(parent, path, goalFormat, checkcols=False):
    dataframe = None
    try:
        dataframe = readFile(path)
    except:
        errbox(parent, "Error reading file: {}".format(sys.exc_info()[1]))
        return None

    if dataframe is None:
        errbox(parent, "Couldn't import file, unknown error")
    elif checkcols:
        fileColCount = len(dataframe.columns.tolist())
        formatColCount = len(goalFormat.req) 
        if fileColCount < formatColCount: 
            errbox(parent, "File contains fewer columns ({}) than the {} format requires ({})".format(fileColCount, goalFormat.name, formatColCount))
            return None

    return dataframe

# force pandas column dtype and convert values to object (string)
def forceStringDatatype(cols, dataframe):
    for col in cols:
        dataframe[col] = dataframe[col].astype(object)
        dataframe[col] = dataframe[col].apply(lambda x: str(x)) # todo: if x != NaN? to avoid line below?
        
        # forced string conversion forces all NaN values to the string "nan" - remove these
        dataframe[col] = dataframe[col].apply(lambda x: "" if x == "nan" else x)


class FooApp(wx.App):
    def __init__(self):
        wx.App.__init__(self, 0)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        app = FooApp()
        doImport(None, SectionSummaryFormat, sys.argv[1])
    else:
        print "specify a CSV file to load"