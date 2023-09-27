from builtins import object
import re

# Parse hole from full section name. Assumes IODP naming convention.
def getHoleName(iodpName):
	holePattern = "U[0-9]+([A-Z]+)" # TODO: make flexible for non-IODP section IDs
	hole = re.search(holePattern, iodpName)
	if hole and len(hole.groups()) == 1:
		return hole.groups()[0]
	return None

def hasJPEGExt(s):
	patt = re.compile("\.(jpg|jpeg|JPG|JPEG)")
	return bool(patt.search(s))

def trimJPEGExt(s):
	patt = re.compile("\.(jpg|jpeg|JPG|JPEG)")
	return patt.sub('',s)

def trimSectionType(s):
	patt = re.compile("(-A|-W|-WR)")
	return patt.sub('', s)

# Given an image filename '342-U1410A-1H-3-A.jpg', return string with
# JPEG extension and section type (-A, -W, -WR) removed.
def makeImageKey(filename):
	ik = trimJPEGExt(filename)
	return trimSectionType(ik)



# Convenience wrapper for DataCanvas.HoleData list elements with
# methods to access hole metadata.
class HoleMetadata(object):
	def __init__(self, holeData):
		self.holeData = holeData
		self.hmt = holeData[0][0] # hole metadata tuple
	
	def holeInfo(self):
		return self.hmt

	def siteName(self):
		return self.hmt[0]

	def expName(self):
		return self.hmt[1]

	def datatype(self):
		return self.hmt[2]

	def topDepth(self):
		return self.hmt[3]

	def botDepth(self):
		return self.hmt[4]

	def minData(self):
		return self.hmt[5]

	def maxData(self):
		return self.hmt[6]

	def holeName(self):
		return self.hmt[7]

	def coreCount(self):
		return self.hmt[8]


# Convenience wrapper for the core metadata tuples that comprise
# elements 1...N of each DataCanvas.HoleData element, listed below.
# 0: core name (number as string)
# 1: top depth
# 2: bottom depth
# 3: minimum data value
# 4: maximum data value
# 5: affine offset (meters)
# 6: stretch (related to log/ELD, unused)
# 7: datatype name
# 8: quality
# 9: list of section top depths (unreliable)
# 10: list of depth/data pairs for this core
class CoreMetadata(object):
	def __init__(self, core_metadata_tuple):
		self.cmt = core_metadata_tuple

	def coreName(self):
		return self.cmt[0]

	def topDepth(self):
		return self.cmt[10][0][0]

	def botDepth(self):
		return self.cmt[10][-1][0]

	def minData(self):
		return self.cmt[3]

	def maxData(self):
		return self.cmt[4]

	def affineOffset(self):
		return self.cmt[5]

	def depthDataPairs(self):
		return self.cmt[10]

	def pointCount(self):
		return len(self.cmt[10])
