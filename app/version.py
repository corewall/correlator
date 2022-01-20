BaseVersion = "4.0"
VersionSuffix = "b1"
LongVersionSuffix = ""

def GetShortVersion():
	if VersionSuffix != "":
		return BaseVersion + "_" + VersionSuffix
	else:
		return BaseVersion

def GetLongVersion():
	if LongVersionSuffix != "":
		return BaseVersion + " " + LongVersionSuffix
	else:
		return BaseVersion

ShortVersion = GetShortVersion()
LongVersion = GetLongVersion()


if __name__ == "__main__":
	print "GetShortVersion() = " + GetShortVersion()
	print "GetLongVersion() = " + GetLongVersion()
