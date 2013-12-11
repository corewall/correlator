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
		self.seriesTables = [] # timeseries?
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

class SpliceData(TableData):
	def __init__(self):
		TableData.__init__(self)
	def __repr__(self):
		return "SpliceTable " + TableData.__repr__(self)
	def FromTokens(self, tokens):
		TableData.FromTokens(self, tokens)

class EldData(TableData):
	def __init__(self):
		TableData.__init__(self)
	def __repr__(self):
		return "EldTable " + TableData.__repr__(self)
	def FromTokens(self, tokens):
		TableData.FromTokens(self, tokens)

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

# cull table that applies to a single HoleSet
class CullTable(TableData):
	def __init__(self):
		TableData.__init__(self)
	def __repr__(self):
		return "CullTable " + TableData.__repr__(self)
	def FromTokens(self, tokens):
		TableData.FromTokens(self, tokens)

class StratTable(TableData):
	def __init__(self):
		TableData.__init__(self)
	def __repr__(self):
		return "StratTable " + TableData.__repr__(self)
	def FromTokens(self, tokens):
		TableData.FromTokens(self, tokens)

class AgeTable(TableData):
	def __init__(self):
		TableData.__init__(self)
	def __repr__(self):
		return "AgeTable " + TableData.__repr__(self)
	def FromTokens(self, tokens):
		TableData.FromTokens(self, tokens)

class SeriesTable(TableData):
	def __init__(self):
		TableData.__init__(self)
	def __repr__(self):
		return "SeriesTable " + TableData.__repr__(self)
	def FromTokens(self, tokens):
		TableData.FromTokens(self, tokens)

class ImageTable(TableData):
	def __init__(self):
		TableData.__init__(self)
	def __repr__(self):
		return "ImageTable " + TableData.__repr__(self)
	def FromTokens(self, tokens):
		TableData.FromTokens(self, tokens)

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
			self.declimate = tokens[10]
		if len(tokens) >= 12:
			self.foo = tokens[11] # unclear what this value means

