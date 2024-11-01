# Logic to control order, grouping, and visibility of hole data columns in main view

from builtins import object
from enum import Enum

from utils import HoleMetadata


class ColumnType(Enum):
    Plot = 1
    Image = 2

ImageDatatypeStr = "Image"
    
class HoleColumn(object):
    def __init__(self, leftX, margin, holeData, smoothData):
        self.leftX = leftX # x coordinate of left of column
        self.margin = margin # width of leftmost space where core number and shift type+distance are displayed
        self._columns = [] # tuples of (ColumnType, column width in pixels)
        self.rawHoleData = holeData # raw input data (DataCanvas.HoleData)
        self.holeData = holeData[0] # input data without seemingly-useless enclosing list
        self.smoothData = smoothData # raw input smooth data (DataCanvas.SmoothData)
        self.hmd = HoleMetadata(holeData) # convenience wrapper

    def addColumn(self, columnType, width):
        self._columns.append((columnType, width))

    def width(self):
        return sum(self.columnWidths()) + self.margin

    def contentWidth(self):
        return sum(self.columnWidths())

    def holeName(self): # name of associated hole
        return self.hmd.holeName()

    def fullHoleName(self): # Exp-SiteHole
        hd = self.holeData[0]
        return "{}-{}{}".format(hd[1], hd[0], hd[7])

    def hasPlot(self):
        return ColumnType.Plot in self.columnTypes()

    def hasImage(self):
        return ColumnType.Image in self.columnTypes()

    def getColumnOffset(self, columnType):
        offset = 0
        for ct, wid in self._columns:
            if ct == columnType:
                return offset
            else:
                offset += wid
        assert False, "HoleColumn has no {} column." .format(columnType)

    def datatype(self): # datatype of associated hole
        if self.columnTypes() == [ColumnType.Image]:
            return ImageDatatypeStr
        else:
            return self.hmd.datatype()

    def columnKey(self): # hole name + datatype string to be used as a dict key
        return self.holeName() + self.datatype()

    def getColumnTypeAtPos(self, x):
        offset = 0
        for ct, wid in self._columns:
            if x >= self.leftX + offset and x <= self.leftX + offset + wid:
                return ct
            offset += wid
        return None

    def topDepth(self):
        return self.hmd.topDepth()

    def botDepth(self):
        return self.hmd.botDepth()

    def minData(self):
        return self.hmd.minData()

    def maxData(self):
        return self.hmd.maxData()

    def holeInfo(self):
        return self.hmd.holeInfo()

    def cores(self):
        return self.holeData[1:]

    def smoothCores(self):
        return self.smoothData[1:]

    def columns(self):
        return self._columns

    def columnTypes(self):
        return [ct for ct, wid in self._columns]

    def columnWidths(self):
        return [wid for ct, wid in self._columns]


class LayoutManager(object):
    def __init__(self):
        self.groupByDatatype = True # if True group HoleColumns by datatype, else group by hole
        self.plotWidth = 250
        self.imageWidth = 50
        self.plotLeftMargin = 50

        self.holeColumns = [] # HoleColumns in current layout
        self.holeColumnDict = {} # HoleColumns in current layout keyed on hole+datatype str
        self.holePositions = [] # list of (xpos, HoleColumn) tuples
        self.holesWithImages = [] # holes with imagery
        self.datatypeOrder = [] # display order of datatypes
        self.visibleHoles = {} # hole (str):visible (bool)
        self.visibleDatatypes = {} # datatype (str):visible (bool)

    def _reset(self):
        self.holeColumns = []
        self.holeColumnDict = {}
        self.holePositions = []

    # If new elts (holes or datatypes) aren't found in visDict, add them
    # with default visibility True.
    def _updateVisibility(self, elts, visDict):
        for e in elts:
            if e not in visDict:
                visDict[e] = True

    def updateVisibleHoles(self, vh):
        for hole in list(vh.keys()):
            self.visibleHoles[hole] = vh[hole]

    def updateVisibleDatatypes(self, vd):
        for datatype in list(vd.keys()):
            self.visibleDatatypes[datatype] = vd[datatype]

    def layout(self, holeData, smoothData, holesWithImages, x, margin):
        self._reset()
        self.holesWithImages = holesWithImages # gross

        # update datatypeOrder if needed
        datatypes = list(set([HoleMetadata(hd).datatype() for hd in holeData]))
        if len(self.holesWithImages) > 0:
            datatypes = [ImageDatatypeStr] + datatypes

        if self.datatypeOrder == [] or len(self.datatypeOrder) != len(datatypes) or set(self.datatypeOrder) != set(datatypes):
            self.datatypeOrder = datatypes

        # update hole/datatype visibility tracking, adding newly-loaded holes/types
        holes = list(set([HoleMetadata(hd).holeName() for hd in holeData]))
        self._updateVisibility(holes, self.visibleHoles)
        self._updateVisibility(self.datatypeOrder, self.visibleDatatypes)

        # create HoleColumns in datatypeOrder, grouping by datatype or by hole
        currentX = x
        if self.groupByDatatype:
            for dt in self.datatypeOrder:
                if dt == ImageDatatypeStr:
                    currentX = self._layoutImageColumns(currentX, holeData, smoothData)
                else:
                    currentX = self._layoutPlotColumns(currentX, holeData, smoothData, dt)
        else: # group by hole
            holeMetadataList = [HoleMetadata(hd) for hd in holeData]
            holes = list(set([h.holeName() for h in holeMetadataList]))
            # find holeData corresponding to each hole+datatype pair and create a HoleColumn for it
            for h in sorted(holes): # TODO: this won't sort correctly if there are 27+ holes (27th hole 'AA' should come after 26th hole 'Z')
                for dt in self.datatypeOrder:
                    if not self.visibleHoles[h] or not self.visibleDatatypes[dt]:
                        continue
                    for idx, hmd in enumerate(holeMetadataList):
                        if hmd.holeName() == h and dt == ImageDatatypeStr and self._holeHasImages(h):
                            currentX += self._createImageColumn(holeData[idx], smoothData[idx][0], currentX, hmd.holeName() + ImageDatatypeStr)
                            break
                        elif hmd.holeName() == h and hmd.datatype() == dt:
                            currentX += self._createPlotColumn(holeData[idx], smoothData[idx][0], currentX, hmd)
                            break
        self.holeColumnDict = {hc.columnKey(): hc for hc in self.holeColumns}

    def getDatatypeOrder(self):
        return self.datatypeOrder

    def setDatatypeOrder(self, datatypeOrder):
        self.datatypeOrder = datatypeOrder

    def setGroupByDatatype(self, groupByDatatype):
        self.groupByDatatype = groupByDatatype

    def isHoleVisible(self, holeName, datatype):
        for hc in self.holeColumns:
            if hc.holeName() == holeName and hc.datatype() == datatype:
                return True
        return False
    
    def isDatatypeVisible(self, datatype):
        return self.visibleDatatypes[datatype]

    def getColumnAtPos(self, x):
        for cur_x, key in self.holePositions:
            hc = self.holeColumnDict[key]
            if x >= cur_x and x <= cur_x + hc.contentWidth():
                return hc
        return None

    def getClosestColumnRightEdge(self, x):
        right_edge = 0
        for cur_x, key in self.holePositions:
            hc = self.holeColumnDict[key]
            right_edge = cur_x + hc.contentWidth() # include margin
            if x >= cur_x and x <= right_edge + hc.margin:
                return right_edge
        return right_edge if x > right_edge else 0

    def getShowImages(self):
        if ImageDatatypeStr not in self.visibleDatatypes:
            return False
        else:
            return self.visibleDatatypes[ImageDatatypeStr]
        
    def getLayoutWidth(self):
        return sum([hc.width() for hc in self.holeColumns])

    def _holeHasImages(self, holeName):
        return holeName in self.holesWithImages

    # create a HoleColumn with nothing but an ImageColumn
    def _createImageColumn(self, holeData, smoothData, currentX, holeKey):
        holeCol = HoleColumn(currentX, self.plotLeftMargin, holeData, smoothData)
        holeCol.addColumn(ColumnType.Image, self.imageWidth)
        self.holeColumns.append(holeCol)
        self.holePositions.append((currentX, holeKey))
        return holeCol.width()

    # create a HoleColumn with a PlotColumn and possibly an ImageColumn
    def _createPlotColumn(self, holeData, smoothData, currentX, hmd):
        holeCol = HoleColumn(currentX, self.plotLeftMargin, holeData, smoothData)
        holeCol.addColumn(ColumnType.Plot, self.plotWidth)
        self.holeColumns.append(holeCol)
        self.holePositions.append((currentX, hmd.holeName() + hmd.datatype()))
        return holeCol.width()

    # for HoleColumns with a PlotColumn and possibly an ImageColumn
    def _layoutPlotColumns(self, currentX, holeData, smoothData, datatype):
        for holeIndex, holeList in enumerate(holeData):
            hmd = HoleMetadata(holeList)
            if hmd.datatype() != datatype or not self.visibleHoles[hmd.holeName()] or not self.visibleDatatypes[datatype]:
                continue
            currentX += self._createPlotColumn(holeList, smoothData[holeIndex][0], currentX, hmd)
        return currentX

    # for HoleColumns with nothing but an ImageColumn
    def _layoutImageColumns(self, currentX, holeData, smoothData):
        holesSeen = []
        for holeIndex, holeList in enumerate(holeData):
            hmd = HoleMetadata(holeList)
            if hmd.holeName() in holesSeen or not self.visibleHoles[hmd.holeName()] or not self.visibleDatatypes[ImageDatatypeStr]:
                continue # only one image column per hole if multiple datatypes are loaded
            if self._holeHasImages(hmd.holeName()):
                currentX += self._createImageColumn(holeList, smoothData[holeIndex][0], currentX, hmd.holeName() + ImageDatatypeStr)
                holesSeen.append(hmd.holeName())
        return currentX