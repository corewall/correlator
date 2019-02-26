# Logic related to smoothing filter

class SmoothParameters:
	def __init__(self, width, units, style):
		self.width = width # integer width of smoothing
		self.units = units # points (1) or cm (2)
		self.style = style # display style - original (0), smoothed (1), or both (2)

	@classmethod
	def createWithString(cls, smoothString):
		width = int(smoothString.split(' ')[0])
		units = 1 if smoothString.find("Points") != -1 else 2
		style = 0
		if smoothString.find("Smoothed Only") != -1:
			style = 1
		elif smoothString.find("Original & Smoothed") != -1:
			style = 2
		return cls(width, units, style)

	# Return integer smooth style string.
	def getStyleString(self):
		if self.style == 0:
			return "Original Only" # no smooth - should really define constant, named values
		elif self.style == 1:
			return "Smoothed Only"
		elif self.style == 2:
			return "Original & Smoothed"

	def getUnitsString(self):
		return "Points" if self.units == 1 else "Depth (cm)"

	def getWidthString(self):
		return str(self.width)

	def toString(self):
		return "{} {} {}".format(self.getWidthString(), self.getUnitsString(), self.getStyleString())
