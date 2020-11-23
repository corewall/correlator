# Logic to control order, grouping, and visibility of hole data columns in main view

from enum import Enum

from utils import HoleMetadata

# class LayoutProperties:
	# def __init__(self, x_origin, margin, plotWidth, imageWidth):

class ColumnType(Enum):
	Plot = 1
	Image = 2

ImageDatatypeStr = "Image"
	
class HoleColumn:
	def __init__(self, holeData, smoothData):
		self.margin = 50 # hard-coded...should match DataCanvas.plotLeftMargin
		self._columns = [] # tuples of (ColumnType, column width in pixels)
		self.rawHoleData = holeData
		self.holeData = holeData[0]
		self.smoothData = smoothData
		self.hmd = HoleMetadata(holeData)

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

	def datatype(self): # datatype of associated hole
		if self.columnTypes() == [ColumnType.Image]:
			return ImageDatatypeStr
		else:
			return self.hmd.datatype()

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


class LayoutManager:
	def __init__(self):
		self.holeColumns = []
		self.holePositions = []
		self.holesWithImages = []
		self.showCoreImages = False
		self.showImagesAsDatatype = False
		self.groupByDatatype = True
		self.datatypeOrder = []
		self.hiddenHoles = [] # hole name + datatype strings

	def _reset(self):
		self.holeColumns = []
		self.holePositions = []

	def layout(self, holeData, smoothData, holesWithImages, x, margin, plotWidth, imageWidth, showCoreImages, showImagesAsDatatype):
		self._reset()
		self.holesWithImages = holesWithImages # gross

		# update datatypeOrder if needed
		datatypes = list(set([HoleMetadata(hd).datatype() for hd in holeData]))
		if showCoreImages and showImagesAsDatatype:
			datatypes = [ImageDatatypeStr] + datatypes
		if self.datatypeOrder == [] or len(self.datatypeOrder) != len(datatypes) or set(self.datatypeOrder) != set(datatypes):
			self.datatypeOrder = datatypes

		# create HoleColumns in datatypeOrder, grouping by datatype or by hole
		currentX = x
		if self.groupByDatatype:
			for dt in self.datatypeOrder:
				if dt == ImageDatatypeStr and showCoreImages and showImagesAsDatatype:
					currentX = self._layoutImageColumns(currentX, holeData, smoothData, imageWidth)
				else:
					currentX = self._layoutPlotColumns(currentX, holeData, smoothData, dt, plotWidth, imageWidth, showCoreImages, showImagesAsDatatype)
		else: # group by hole
			holeMetadataList = [HoleMetadata(hd) for hd in holeData]
			holes = list(set([h.holeName() for h in holeMetadataList]))
			# find holeData corresponding to each hole+datatype pair and create a HoleColumn for it
			for h in sorted(holes): # TODO: this won't sort correctly if there are 27+ holes (27th hole 'AA' should come after 26th hole 'Z')
				for dt in self.datatypeOrder:
					if h + dt in self.hiddenHoles:
						continue
					for idx, hmd in enumerate(holeMetadataList):
						if showCoreImages and showImagesAsDatatype and hmd.holeName() == h and dt == ImageDatatypeStr and self._holeHasImages(h):
							currentX += self._createImageColumn(holeData[idx], smoothData[idx][0], imageWidth, currentX, hmd.holeName() + ImageDatatypeStr)
							break
						elif hmd.holeName() == h and hmd.datatype() == dt:
							currentX += self._createPlotColumn(holeData[idx], smoothData[idx][0], plotWidth, imageWidth, currentX, hmd, showCoreImages, showImagesAsDatatype)
							break

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
		
	def _holeHasImages(self, holeName):
		return holeName in self.holesWithImages

	# create a HoleColumn with nothing but an ImageColumn
	def _createImageColumn(self, holeData, smoothData, imageWidth, currentX, holeKey):
		holeCol = HoleColumn(holeData, smoothData)
		holeCol.addColumn(ColumnType.Image, imageWidth)
		self.holeColumns.append(holeCol)
		self.holePositions.append((currentX, holeKey))
		return holeCol.width()

	# create a HoleColumn with a PlotColumn and possibly an ImageColumn
	def _createPlotColumn(self, holeData, smoothData, plotWidth, imageWidth, currentX, hmd, showCoreImages, showImagesAsDatatype):
		holeCol = HoleColumn(holeData, smoothData)
		if self._holeHasImages(hmd.holeName()) and showCoreImages and not showImagesAsDatatype:
			holeCol.addColumn(ColumnType.Image, imageWidth)
		holeCol.addColumn(ColumnType.Plot, plotWidth)
		self.holeColumns.append(holeCol)
		self.holePositions.append((currentX, hmd.holeName() + hmd.datatype()))
		return holeCol.width()

	# for HoleColumns with a PlotColumn and possibly an ImageColumn
	def _layoutPlotColumns(self, currentX, holeData, smoothData, datatype, plotWidth, imageWidth, showCoreImages, showImagesAsDatatype):
		for holeIndex, holeList in enumerate(holeData):
			hmd = HoleMetadata(holeList)
			if hmd.datatype() != datatype or (hmd.holeName() + hmd.datatype() in self.hiddenHoles):
				continue
			currentX += self._createPlotColumn(holeList, smoothData[holeIndex][0], plotWidth, imageWidth, currentX, hmd, showCoreImages, showImagesAsDatatype)
		return currentX

	# for HoleColumns with nothing but an ImageColumn
	def _layoutImageColumns(self, currentX, holeData, smoothData, imageWidth):
		holesSeen = []
		for holeIndex, holeList in enumerate(holeData):
			hmd = HoleMetadata(holeList)
			if hmd.holeName() in holesSeen or (hmd.holeName() + ImageDatatypeStr in self.hiddenHoles):
				continue # only one image column per hole if multiple datatypes are loaded
			if self._holeHasImages(hmd.holeName()):
				currentX += self._createImageColumn(holeList, smoothData[holeIndex][0], imageWidth, currentX, hmd.holeName() + ImageDatatypeStr)
				holesSeen.append(hmd.holeName())
		return currentX