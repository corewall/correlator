from __future__ import print_function
BaseVersion = "4.5.9"
VersionSuffix = ""
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
    print("GetShortVersion() = " + GetShortVersion())
    print("GetLongVersion() = " + GetLongVersion())
