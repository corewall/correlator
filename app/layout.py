# Logic to control order, grouping, and visibility of hole data columns in main view

from enum import Enum

from utils import HoleMetadata

# class LayoutProperties:
	# def __init__(self, x_origin, margin, plotWidth, imageWidth):

class ColumnType(Enum):
	Plot = 1
	Image = 2

	
class HoleColumn:
	def __init__(self, width, holeData, smoothData):
		self._width = width # hole column width in pixels
		self._columns = [] # one or more ColumnTypes
		self.rawHoleData = holeData
		self.holeData = holeData[0]
		self.smoothData = smoothData
		self.hmd = HoleMetadata(holeData)

	def addColumn(self, col):
		self._columns.append(col)

	def width(self):
		return self._width

	def holeName(self): # name of associated hole
		return self.hmd.holeName()

	def fullHoleName(self): # Exp-SiteHole
		hd = self.holeData[0]
		return "{}-{}{}".format(hd[1], hd[0], hd[7])

	def hasPlot(self):
		return ColumnType.Plot in self._columns

	def datatype(self): # datatype of associated hole
		if self._columns == [ColumnType.Image]:
			return "Image"
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


class LayoutManager:
	def __init__(self):
		self.holeColumns = []
		self.holePositions = []
		self.holesWithImages = []
		self.showCoreImages = False
		self.showImagesAsDatatype = False

	def _reset(self):
		self.holeColumns = []
		self.holePositions = []

	def layout(self, holeData, smoothData, holesWithImages, x, margin, plotWidth, imageWidth, showCoreImages, showImagesAsDatatype):
		self._reset()
		self.holesWithImages = holesWithImages # gross
		currentX = x

		if showCoreImages and showImagesAsDatatype:
			holesSeen = []
			for holeIndex, holeList in enumerate(holeData):
				hmd = HoleMetadata(holeList)
				if hmd.holeName() in holesSeen:
					continue # only one image column per hole if multiple datatypes are loaded
				if self._holeHasImages(hmd.holeName()):
					hole_col = HoleColumn(imageWidth + margin, holeList, smoothData[holeIndex][0])
					hole_col.addColumn(ColumnType.Image)
					self.holeColumns.append(hole_col)
					self.holePositions.append((currentX, hmd.holeName() + "Image"))
					currentX += hole_col.width()
					holesSeen.append(hmd.holeName())
		
		# even if we aren't drawing HoleData (unsmoothed), there will always be HoleData
		# corresponding to SmoothData, so it's safe to rely on self.HoleData here.  		
		for holeIndex, holeList in enumerate(holeData):
			hmd = HoleMetadata(holeList)
			imagesWithPlots = showCoreImages and not showImagesAsDatatype

			# if hole has imagery and images are being displayed, add self.coreImageWidth
			img_wid = imageWidth if (imagesWithPlots and self._holeHasImages(hmd.holeName())) else 0
			hole_wid = margin + plotWidth + img_wid

			hole_col = HoleColumn(hole_wid, holeList, smoothData[holeIndex][0])
			if imagesWithPlots and self._holeHasImages(hmd.holeName()):
				hole_col.addColumn(ColumnType.Image)
			hole_col.addColumn(ColumnType.Plot)
			self.holeColumns.append(hole_col)

			# store as a tuple - DrawStratCore() logic still uses index to access value
			holeKey = hmd.holeName() + hmd.datatype()
			self.holePositions.append((currentX, holeKey))
			currentX += hole_wid        

	def _holeHasImages(self, holeName):
		return holeName in self.holesWithImages