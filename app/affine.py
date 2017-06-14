'''
Created on Feb 22, 2017

@author: bgrivna

Support for the creation and editing of Affine Shifts and resulting tables.
'''

import re # to parse combined hole/core strings
import unittest
import numpy

import tabularImport
import sectionSummary

class AffineError(Exception):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message

class AffineShift:
    def __init__(self, core, distance, dataUsed="", comment=""):
        self.core = core # CoreInfo (or AffineCoreInfo) for the shifted core
        self.distance = distance # shift distance (can be 0)
        self.dataUsed = dataUsed # data type used to create shift
        self.comment = comment # user comment
        
    # adjust current shift by deltaDistance
    def adjust(self, deltaDistance):
        self.distance += deltaDistance

    def typeStr(self):
        return "NO TYPE - implement typeStr() in child"

# An affine shift resulting from the shift of another core that "pushes" or "pulls"
# all cores below and/or related cores to maintain spacing of cores. Because the user
# didn't explicitly shift this core, it isn't a TIE or a SET, but a "convenience" shift
# that maintains relative positions between cores in a hole. Ultimately, such
# shifts will usually be replaced with a TIE or SET as they're integrated into
# the CCSF-A/MCD depth scale.
class ImplicitShift(AffineShift):
    def __init__(self, core, distance, dataUsed="", comment=""):
        AffineShift.__init__(self, core, distance, dataUsed, comment)
    
    def __repr__(self):
        commentStr = " ({})".format(self.comment) if self.comment != "" else ""
        return "Implicit shift of {} by {}m{}".format(self.core, self.distance, commentStr)
    
    def typeStr(self):
        return "REL"
    

class TieShift(AffineShift):
    def __init__(self, fromCore, fromDepth, core, depth, distance, dataUsed="", comment=""):
        AffineShift.__init__(self, core, distance, dataUsed, comment)
        self.fromCore = fromCore # CoreInfo for core to which self.core was tied
        self.fromDepth = fromDepth # MBSF depth of "from" core's TIE point
        self.depth = depth # MBSF depth of shifted core's TIE point

    def __repr__(self):
        fmtStr = "TIE from {}@{}mbsf to {}@{}mbsf ({}mcd), shifted {}m{}" 
        commentStr = " ({})".format(self.comment) if self.comment != "" else ""
        return fmtStr.format(self.fromCore, self.fromDepth, self.core, self.depth, self.depth + self.distance, self.distance, commentStr)
    
    def typeStr(self):
        return "TIE"


class SetShift(AffineShift):
    def __init__(self, core, distance, dataUsed="", comment=""):
        AffineShift.__init__(self, core, distance, dataUsed, comment)

    def __repr__(self):
        commentStr = " ({})".format(self.comment) if self.comment != "" else ""
        return "SET: {} shifted {}m{}".format(self.core, self.distance, commentStr)
    
    def typeStr(self):
        return "SET"
    
def isTie(shift):
    return isinstance(shift, TieShift)

def isSet(shift):
    return isinstance(shift, SetShift)

def isImplicit(shift):
    return isinstance(shift, ImplicitShift)

class UnknownCoreError(AffineError):
    def __init__(self, expression, message):
        AffineError.__init__(self, expression, message)
        
        
        
# Maintains a collection of AffineShifts, ensuring exactly one shift per AffineCoreId.
# No enforcement or updating of TIE relationships. 
class AffineTable:
    def __init__(self):
        self.shifts = [] # list of AffineShifts representing the current affine state
        
    @classmethod
    def createWithCores(cls, cores):
        #print "core type = {}, hole type = {}".format(type(cores[0].core), type(cores[0].hole))
        affine = cls()
        for c in cores:
            affine.addShift(ImplicitShift(c, 0.0))
        return affine
    
    @classmethod
    def createWithShifts(cls, shifts):
        affine = cls()
        for s in shifts:
            affine.addShift(s)
        return affine

    def __repr__(self):
        superstr = "AffineTable: {} shifts\n".format(len(self.shifts))
        for index, shift in enumerate(self.shifts):
            superstr += "  {}: {}\n".format(index, shift)
        return superstr
        
    def clear(self):
        self.shifts = []
        
    # return all shifts to zero-distance ImplicitShifts
    def reset(self):
        resetShifts = [ImplicitShift(shift.core, 0.0) for shift in self.shifts]
        self.shifts = resetShifts
        
    # client needn't know whether this core already has a shift - add if not, otherwise replace
    def addShift(self, newShift):
        shift = self.getShift(newShift.core)
        if shift is None:
            self._add(newShift)
        else:
            self._replace(shift, newShift)
    
    def _add(self, shift):
        #print "adding {}".format(shift)
        assert shift not in self.shifts
        self.shifts.append(shift)
    
    def _delete(self, shift):
        assert shift in self.shifts
        #print "deleting {}".format(shift)
        self.shifts.remove(shift)
        
    def _replace(self, oldShift, newShift):
        #print "replacing {} with {}".format(oldShift, newShift)
        self._delete(oldShift)
        self._add(newShift)
        
    # modify existing shift by deltaDistance
    def adjust(self, core, deltaDistance):
        self.getShift(core).adjust(deltaDistance)
        
    # change TieShift or SetShift to ImplicitShift, leaving shift distance unchanged
    def makeImplicit(self, core):
        shift = self.getShift(core)
        self._replace(shift, ImplicitShift(core, shift.distance, shift.dataUsed, shift.comment))
    
    def getShift(self, core):
        shifts = [s for s in self.shifts if s.core == core]
        assert len(shifts) <= 1
        return shifts[0] if len(shifts) == 1 else None
    
    def hasShift(self, core):
        return self.getShift(core) is not None
    
    def getShiftDistance(self, core):
        shift = self.getShift(core)
        assert shift is not None
        return shift.distance

    # returns True if core is the top of a chain or chains
    def isChainTop(self, core):
        tiedChainTop = self.countChildren(core) > 1 and isTie(self.getShift(core))
        return tiedChainTop or (self.countChildren(core) > 0 and not isTie(self.getShift(core)))
        
    # is core part of a TIE chain?
    def inChain(self, core):
        shift = self.getShift(core)
        return isTie(shift) or self.isChainTop(core)
    
    # is searchCore the fromCore for anything upstream?
    def isUpstream(self, searchCore, curCore):
        curShift = self.getShift(curCore)
        if not isTie(curShift):
            return False
        elif curShift.fromCore == searchCore:
            return True
        else:
            return self.isUpstream(searchCore, curShift.fromCore)
    
    # get immediate descendants of core
    def getChildren(self, core):
        return [shift for shift in self.shifts if isTie(shift) and shift.fromCore == core]
    
    # count immediate descendants of core
    def countChildren(self, core):
        return len(self.getChildren(core))
    
    # return list of all AffineCoreIds that are part of core's TIE chain (if any), including core itself
    def getChainCores(self, core):
        chainCores = []
        if self.inChain(core):
            root = self.getRoot(core)
            self._walkChain([root], chainCores)
        return chainCores
    
    def _walkChain(self, nodes, chainCores):
        for n in nodes:
            self._walkChain(self.getChildren(n.core), chainCores)
            chainCores.append(n.core)
            
    # if there's a chain of ties from core to any member of searchCores that doesn't
    # involve a core in excluded, return True.
    # core: AffineCoreInfo of core for which connection is sought
    # searchCores: list of AffineCoreInfos of cores for which connection with core is sought
    # excluded: cores that cannot be included in the chain
    # visited: already-seen cores
    def isConnected(self, core, searchCores, excluded, visited):
        if core in excluded:
            return False
        if core in searchCores:
            return True
        visited.append(core)
        for childShift in self.getChildren(core):
            if childShift.core not in visited and self.isConnected(childShift.core, searchCores, excluded, visited):
                return True
        parentShift = self.getParent(core)
        if parentShift is not None and parentShift.core not in visited and self.isConnected(parentShift.core, searchCores, excluded, visited):
            return True
        return False
            
    # get immediate parent of core
    def getParent(self, core):
        shift = None
        if isTie(self.getShift(core)):
            shift = self.getShift(core)
            shift = self.getShift(shift.fromCore)
        return shift
    
    # get root shift of TIE chain containing core - if core is the root, return its shift
    def getRoot(self, core):
        shift = self.getShift(core)
        while isTie(shift):
            shift = self.getShift(shift.fromCore)
        assert self.isChainTop(shift.core) # catch client passing non-chain core argument
        return shift


class AffineBuilder:
    def __init__(self):
        self.affine = AffineTable() # AffineTable representing the current affine state
        self.sectionSummary = None
        self.site = None # Yuck. Maintaining so we can query sectionSummary
        
    @classmethod
    def createWithSectionSummary(cls, secsumm):
        affineBuilder = cls()
        cores = []
        for hole in secsumm.getHoles():
            for core in secsumm.getCores(hole):
                cores.append(aci(hole, str(core)))
        affineBuilder.affine = AffineTable.createWithCores(cores)
        affineBuilder.sectionSummary = secsumm
        affineBuilder.site = list(secsumm.getSites())[0] # assume a single site!
        return affineBuilder
    
    @classmethod
    def createWithAffineFile(cls, affineFile, secsumm):
        affineBuilder = cls()
        affineShifts = []
        df = tabularImport.readFile(affineFile)
        tabularImport.forceStringDatatype(['Core'], df)
        shiftedCores = []
        for index, row in df.iterrows():
            hole, core, offset, shiftType, fixedCore, fixedCsf, shiftedCsf, dataUsed, comment = affineBuilder._parseAffineRow(row)
            shiftedCore = aci(hole, core)
            if shiftType == "TIE":
                fromCore = acistr(fixedCore)
                shift = TieShift(fromCore, fixedCsf, shiftedCore, shiftedCsf, offset, dataUsed, comment)
            elif shiftType == "SET":
                shift = SetShift(shiftedCore, offset, dataUsed, comment)
            elif shiftType == "REL" or shiftType == "ANCHOR":
                shift = ImplicitShift(shiftedCore, offset, dataUsed, comment)
            else:
                raise Exception("Unknown affine shift type {}".format(shiftType))
            shiftedCores.append(shiftedCore)
            affineShifts.append(shift)
            
        # for cores in the section summary but not in the affineFile, add affine shifts
        # for each, using same shift as nearest core above in affine
        ssCores = []
        for h in secsumm.getHoles():
            cores = [aci(h,c) for c in secsumm.getCores(h)]
            ssCores.extend(cores)
        shiftlessCores = [c for c in ssCores if c not in shiftedCores]
        tmpAffine = AffineTable.createWithShifts(affineShifts)
        for c in shiftlessCores:
            coreAbove = findCoreAbove(c, shiftedCores)
            if coreAbove is not None:
                distance = tmpAffine.getShiftDistance(coreAbove)
                seededShift = ImplicitShift(c, distance, dataUsed="", comment="seeded with section summary")
                affineShifts.append(seededShift)
                print "Seeded missing affine shift for {} using core above {}".format(c, coreAbove)
            else:
                affineShifts.append(ImplicitShift(c, 0.0, dataUsed="", comment="seeded: no core above, no shift"))
                print "No core above found to seed affine shift for {}, no shift".format(c)
        
        affineBuilder.affine = AffineTable.createWithShifts(affineShifts)
        affineBuilder.sectionSummary = secsumm
        affineBuilder.site = list(secsumm.getSites())[0] # assume a single site!
        return affineBuilder

    def _parseAffineRow(self, row):
        hole = row['Hole']
        core = row['Core']
        offset = row['Cumulative Offset (m)']
        shiftType = row['Shift Type']
        dataUsed = row['Data Used']
        comment = row['Quality Comment']
        
        fixedCore = fixedCsf = shiftedCsf = ""
        if shiftType == 'TIE':
            if 'Fixed Core' in row: # new-style affine table
                fixedCore = row['Fixed Core']
                fixedCsf = row['Fixed Tie CSF']
                shiftedCsf = row['Shifted Tie CSF']
            else: # older affine with no TIE chain information
                pass
        
        return hole, core, offset, shiftType, fixedCore, fixedCsf, shiftedCsf, dataUsed, comment
        
    def __repr__(self):
        return str(self.affine)
        
    def clear(self):
        self.affine.clear()
        
    def reset(self):
        self.affine.reset()
        
    # modify existing shift by deltaDistance
    def adjust(self, core, deltaDistance):
        self.affine.getShift(core).adjust(deltaDistance)
     
    # shift core(s) by a given distance (SET) 
    def set(self, coreOnly, core, distance, dataUsed="", comment=""):
        bogusFromCore = AffineCoreInfo.createBogus() # SET has no fromCore, use bogus to ensure no matches
        breaks = []
        if coreOnly:
            breaks = self.findBreaks(core, bogusFromCore)
            deltaDistance = distance - self.affine.getShift(core).distance
            self.affine.addShift(SetShift(core, distance, dataUsed, comment))
        else: # consider related cores
            shift = self.affine.getShift(core)
            deltaDistance = distance - shift.distance
            relatedCores = self.gatherRelatedCores(bogusFromCore, core, setAllOperation=True)
            breaks = self.findBreaks(core, bogusFromCore, relatedCores)
            self.affine.addShift(SetShift(core, distance, dataUsed, comment))
            for ci in relatedCores:
                if ci != core:
                    self.affine.adjust(ci, deltaDistance)

        for b in breaks:
            childCore = b[1]
            if childCore != core:
                self.affine.makeImplicit(childCore)

    # shift core(s) based on a tie between two cores
    # coreOnly - if True, shift core only, else shift core and all related
    # mcdShiftDistance - distance between tie points in MCD space
    # fromCore, fromDepth - core and MBSF depth of tie on fixed core
    # core, depth - core and MBSF depth of tie on core to be shifted
    # comment - user comment/annotation of shift
    def tie(self, coreOnly, mcdShiftDistance, fromCore, fromDepth, core, depth, dataUsed="", comment=""):
        breaks = []
        totalShiftDistance = self.affine.getShiftDistance(core) + mcdShiftDistance
        if coreOnly:
            breaks = self.findBreaks(core, fromCore)
            self.affine.addShift(TieShift(fromCore, fromDepth, core, depth, totalShiftDistance, dataUsed, comment))
        else:
            relatedCores = self.gatherRelatedCores(fromCore, core)
            breaks = self.findBreaks(core, fromCore, relatedCores)
            self.affine.addShift(TieShift(fromCore, fromDepth, core, depth, totalShiftDistance, dataUsed, comment))
            for ci in relatedCores:
                self.affine.adjust(ci, mcdShiftDistance)
                
        # change shift type of cores with just-broken ties to ImplicitShift
        for b in breaks:
            childCore = b[1]
            if childCore != core: # original tie for core was broken by new tie - don't make implicit!
                self.affine.makeImplicit(childCore)
    
    # given list of cores to move, determine where ties will be broken and return
    # list of tuples of form (fromCore, childCore) indicating break locations
    def findBreaks(self, shiftCore, fromCore, _movingCores=[]):
        # use local copy of _movingCores to avoid adding shiftCore to client list
        movingCores = _movingCores + [shiftCore]
        breaks = []
        for core in movingCores:
            shift = self.getShift(core)
            if isTie(shift) and shift.fromCore not in movingCores and \
                (core != shiftCore or fromCore != shift.fromCore): # re-tie with same fromCore isn't a break
                breaks.append((shift.fromCore, core))
            if self.affine.getChildren(core) > 0:
                for child in self.affine.getChildren(core):
                    if child.core not in movingCores:
                        breaks.append((core, child.core))
        return breaks
    
    def getOffHoleFromCores(self, cores, shiftHole):
        shiftHoleCores = [c for c in cores if c.hole == shiftHole]
        offHoleFromCores = []
        for c in [c for c in cores if c.hole != shiftHole]:
            kids = self.affine.getChildren(c)
            for k in kids:
                if k.core in shiftHoleCores:
                    offHoleFromCores.append(c)
                    break
        return offHoleFromCores
        #return [c for c in cores if c not in offHoleFromCores]
    
    # gather all cores that will be shifted by "Shift by [shiftCore] and related cores below" action
    # note: result excludes shiftCore itself!
    def gatherRelatedCores(self, fromCore, shiftCore, setAllOperation=False):
        excludeCores = [fromCore]
        shift = self.getShift(shiftCore)
        if isTie(shift) and shift.fromCore != fromCore:
            excludeCores.append(shift.fromCore)
            
        # shiftCore and all cores below in shiftCore.hole are going to shift: find all
        # chain cores related to those cores.
        chainCores = self._gatherHoleChainCores(shiftCore, excludeCores, knownChainCores=[])
        
        # now find all other chain cores affected by shiftCore's shift by gathering
        # chain cores related to topmost core in chainCores for each hole != shiftCore.hole
        done = False
        nonShiftHoles = [h for h in self.sectionSummary.getHoles() if h != shiftCore.hole]
        while not done:
            newChainCores = []
            for hole in nonShiftHoles:
                # topmost chainCore in hole is going to shift - find any chain cores
                # related to it or any core below it in hole
                topChainCore = self._topCoreInHole(hole, chainCores)
                if topChainCore is not None:
                    newChainCores.extend(self._gatherHoleChainCores(topChainCore, excludeCores, knownChainCores=chainCores))
            if len(newChainCores) == 0: # no new chain cores were found, we're done!
                done = True
            else: # found new chain cores, add them and repeat the process
                chainCores.extend(newChainCores)
        
        # if this is a SET and related below operation, any TIEs in hole below shiftCore should be
        # broken before considering related cores
        if setAllOperation:
            offHoleFromCores = self.getOffHoleFromCores(chainCores, shiftCore.hole)
            chainCores = [c for c in chainCores if c not in offHoleFromCores]
        
        # cull any cores above shiftCore
        shiftCoreTop = self._getCoreTop(shiftCore) + self.getShift(shiftCore).distance
        chainCores = [c for c in chainCores if self._getCoreTop(c) + self.getShift(c).distance >= shiftCoreTop]
        
        # cull any cores above fromCore - fromCore can't move, so nothing above it can move
        if fromCore != AffineCoreInfo.createBogus():
            fromCoreTop = self._getCoreTop(fromCore) + self.getShift(fromCore).distance
            coresAboveFrom = [c for c in chainCores if c.hole == fromCore.hole and self._getCoreTop(c) + self.getShift(c).distance < fromCoreTop]
            for core in coresAboveFrom:
                chainCores.remove(core)        
        
        for hole in nonShiftHoles:
            topChainCore = self._topCoreInHole(hole, chainCores)
            if topChainCore is not None:
                coreAndBelow = [topChainCore] + self.getCoresBelow(topChainCore)
                chainCores.extend(coreAndBelow)
            
        chainCores.extend(self.getCoresBelow(shiftCore))
        if shiftCore in chainCores: # remove shiftCore from relatedCores
            chainCores.remove(shiftCore)
        relatedCores = list(set(chainCores))
        
        return relatedCores
    
    # return list of cores in chains related to core and below in core.hole
    # core - gather chain cores for this core and all cores below in its hole
    # excludeCores - cores to be excluded from the list
    # knownChainCores - chain cores that have already been discovered, to be excluded from list
    def _gatherHoleChainCores(self, core, excludeCores, knownChainCores):
        foundCores = []
        for c in [core] + self.getCoresBelow(core):
            if c not in knownChainCores and self.affine.inChain(c):
                newChainCores = [nc for nc in self.affine.getChainCores(c) if nc not in excludeCores]
                foundCores.extend(newChainCores)
        
        return list(set(foundCores))    
        
    # return topmost core in coreList found in hole, otherwise None
    def _topCoreInHole(self, hole, coreList):
        foundCoresInHole = [c for c in coreList if c.hole == hole]
        if len(foundCoresInHole) > 0:
            theCore = min(foundCoresInHole, key=lambda c: int(c.core))
            return theCore
        else:
            return None
        
    def _getCoreTop(self, ci):
        return self.sectionSummary.getCoreTop(self.site, ci.hole, ci.core)
    
    # get all cores in hole below core by name - not actual position!
    # todo: abstract concept of "below"?
    # todo: this really shouldn't be part of AffineBuilder, should be done
    # through SectionSummary so we can deal with holes/cores directly instead
    # of cracking open Shifts to get at hole/core names. Or at least at
    # AffineController level where there's a notion of SectionSummary.
    # But for now...and therefore forever...
    def getCoresBelow(self, ci):
        cb = [core for core in self.getCoresInHole(ci.hole) if int(core.core) > int(ci.core)]
        return cb
    
    def getCoresInHole(self, hole):
        return [shift.core for shift in self.affine.shifts if shift.core.hole == hole]
    
    def isLegalTie(self, fromCore, core):
        return not self.affine.isUpstream(fromCore, core)
        
    def hasShift(self, core):
        return self.affine.hasShift(core)
    
    def getShift(self, core):
        #print "core type = {}, hole type = {}".format(type(core.core), type(core.hole))
        return self.affine.getShift(core)
    
    # return list of shifts, sorted first by hole, then core
    def getSortedShifts(self):
        return sorted(self.affine.shifts, key=lambda x:x.core)
    
    # return sorted list of holes represented in affine table
    def getSortedHoles(self):
        holeSet = set([x.core.hole for x in self.affine.shifts])
        return sorted(list(holeSet))
    
    def isTie(self, core):
        return isTie(self.getShift(core))
    
    # if core is "below" compareCore, return True, else False
    def coreIsBelow(self, coreInfo, compareCoreInfo):
        return (self._getCoreTop(coreInfo) + self.getShift(coreInfo).distance) >= (self._getCoreTop(compareCoreInfo) + self.getShift(compareCoreInfo).distance)
    

# Reference to hole and core for affine shifts
class AffineCoreInfo:
    def __init__(self, hole, core):
        assert isinstance(hole, str)
        assert isinstance(core, str)
        self.hole = hole
        self.core = core
        
    @classmethod
    def createBogus(cls):
        return cls("ZZZ", "-999")
        
    def GetHoleCoreStr(self):
        return "{}{}".format(self.hole, self.core)

    # 'A' < 'B' < 'AA' < 'AB' < 'BA' < 'BB' ...
    def _holeLessThan(self, otherHole):
        assert isinstance(self.hole, str)
        assert isinstance(otherHole, str)
        if len(self.hole) == len(otherHole):
            # use alphabetical comparison if holes are same length  
            return self.hole.upper() < otherHole.upper()
        return len(self.hole) < len(otherHole)
    
    def _coreLessThan(self, otherCore):
        assert isinstance(self.core, str)
        assert isinstance(otherCore, str)
        return int(self.core) < int(otherCore)
    
    def __hash__(self):
        return hash(repr(self))
    
    def __str__(self):
        return self.GetHoleCoreStr()
            
    def __repr__(self):
        return self.GetHoleCoreStr()
    
    def __eq__(self, other):
        return self.hole == other.hole and self.core == other.core
    
    def __ne__(self, other):
        return self.hole != other.hole or self.core != other.core
    
    # support sorting operations
    def __lt__(self, other):
        if self.hole != other.hole:
            return self._holeLessThan(other.hole)
        else:
            return self._coreLessThan(other.core)

# convenience method to create AffineCoreInfo
def aci(hole, core):
    return AffineCoreInfo(hole, core)

# convenience method to create AffineCoreInfo from string of form "[hole][core]"
def acistr(holeCoreStr):
    charNumPattern = "([A-Z]+)([0-9]+)"
    hc_items = re.match(charNumPattern, holeCoreStr)
    if hc_items and len(hc_items.groups()) == 2:
        hole = hc_items.groups()[0]
        core = hc_items.groups()[1]
        return AffineCoreInfo(hole, core)
    raise InvalidHoleCoreStringError(holeCoreStr, "Cannot be parsed into an alphabetic hole and numeric core")

# create list of AffineCoreInfos from list of "[hole][core]" strings
def acilist(coreStrs):
    return [acistr(c) for c in coreStrs]


# malformed hole core string
class InvalidHoleCoreStringError(AffineError):
    def __init__(self, expression, message):
        AffineError.__init__(self, expression, message)

# are all elements of elts found in listToSearch?
def elementsInList(elts, listToSearch):
    allFound = True
    for elt in elts:
        if elt not in listToSearch:
            allFound = False
            break
    return allFound

# do list1 and list2 have same elements, independent of their order?
def sameElements(list1, list2, report=False):
    union = set().union(list1, list2)
    same = len(union) == len(list1) == len(list2)
    if not same and report:
        print "sameElements(): no match!\nlist1 = {}\nlist2 = {}".format(list1, list2)
    return same

# - searchCore: AffineCoreInfo to find in coreList
# - coreList: list of AffineCoreInfos
# return nearest core in coreList above searchCore, or None if none exists
def findCoreAbove(searchCore, coreList):
    coreAbove = None
    hole = searchCore.hole
    core = int(searchCore.core)
    while core > 0:
        core -= 1
        if aci(hole, str(core)) in coreList:
            coreAbove = aci(hole, str(core))
            break
    return coreAbove


def convert_pre_v3_AffineTable(prev3df):
    for index, row in prev3df.iterrows():
        #print "row shift type = {}".format(row['Shift Type'])
        if row['Shift Type'] in [numpy.nan, "nan", "TIE", "APPEND", "ANCHOR"]:
            prev3df.loc[index, "Shift Type"] = "REL"
    
    # add empty TIE tracking columns        
    for index, colname in enumerate(['Fixed Core', 'Fixed Tie CSF', 'Shifted Tie CSF']): 
        prev3df.insert(index + 10, colname, "")
    #print prev3df
    return prev3df


class TestAffineTable(unittest.TestCase):
    def test_chain_funcs(self):
        a1 = aci('A', '1')
        a2 = aci('A', '2')
        b1 = aci('B', '1')
        b2 = aci('B', '2')
        c1 = acistr('C1')
        c2 = aci('C', '2')
        d1 = acistr('D1')
        d2 = acistr('D2')
        d3 = acistr('D3')
        affine = AffineTable.createWithCores([a1, a2, b1, b2, c1, c2, d1, d2, d3])
        # chain: A1 > B1 > [C2 > B2, A2] 
        affine.addShift(TieShift(a1, 2.0, b1, 1.0, 1.0))
        affine.addShift(TieShift(b1, 2.5, c2, 1.0, 1.5))
        affine.addShift(TieShift(c2, 3.0, b2, 1.0, 2.0))
        affine.addShift(TieShift(b1, 2.8, a2, 2.0, 0.8))
        
        # separate chain: D1 > C1 > D2
        affine.addShift(TieShift(d1, 2.0, c1, 1.0, 1.0))
        affine.addShift(TieShift(c1, 3.0, d2, 1.2, 1.8))
        
        # inChain()
        self.assertTrue(affine.inChain(a1))
        self.assertTrue(affine.inChain(a2))
        self.assertTrue(affine.inChain(b1))
        self.assertTrue(affine.inChain(b2))
        self.assertTrue(affine.inChain(c2))
        self.assertFalse(affine.inChain(d3))
        
        # isChainTop() - A1 is chain top but is not a TIE
        self.assertTrue(affine.isChainTop(a1))
        
        # B1 is a chain top that is a TIE
        self.assertTrue(affine.isChainTop(b1))

        # all others are not chain tops        
        self.assertFalse(affine.isChainTop(b2))
        self.assertFalse(affine.isChainTop(c2))
        self.assertFalse(affine.isChainTop(a2))
        
        # countChildren()
        self.assertTrue(affine.countChildren(b1) == 2) # A2, C2
        self.assertTrue(affine.countChildren(a1) == 1) # B1
        self.assertTrue(affine.countChildren(c2) == 1) # B2
        self.assertTrue(affine.countChildren(b2) == 0)
        self.assertTrue(affine.countChildren(d3) == 0)
        
        # getParent()
        self.assertTrue(affine.getParent(a1) is None)
        self.assertTrue(affine.getParent(b1).core == a1)
        self.assertTrue(affine.getParent(c2).core == b1)
        self.assertTrue(affine.getParent(a2).core == b1)
        self.assertTrue(affine.getParent(b2).core == c2)
        
        # getRoot()
        self.assertTrue(affine.getRoot(a2).core == a1)
        self.assertTrue(affine.getRoot(b2).core == a1)
        self.assertTrue(affine.getRoot(d2).core == d1)

        # getChainCores()
        chain1Cores = affine.getChainCores(a1)
        self.assertTrue(b2 in chain1Cores)
        self.assertFalse(d1 in chain1Cores)
        
        chain2Cores = affine.getChainCores(d2)
        self.assertTrue(d1 in chain2Cores)
        
        # D3 isn't part of any chain
        self.assertTrue(affine.getChainCores(d3) == [])
        

class TestAffine(unittest.TestCase):
    # use numpy.isclose to deal with tiny floating point discrepancies causing == to return False 
    def assertClose(self, fp1, fp2):
        return self.assertTrue(numpy.isclose(fp1, fp2))
    
    def test_convert_pre_v3(self):
        oldaff, msg = tabularImport._parseFile("testdata/pre_v3_affine.csv", tabularImport.AffineFormat_pre_v3, checkcols=True)
        newaff = convert_pre_v3_AffineTable(oldaff)
    
    def test_acistr(self):
        aci1 = acistr("A1")
        self.assertTrue(aci1.hole == 'A')
        self.assertTrue(aci1.core == '1')
        aci2 = acistr("B309")
        self.assertTrue(aci2.hole == 'B')
        self.assertTrue(aci2.core == '309')
        
        # physically ridiculous but logically valid case (after hole Z, next is AA, so AZ == 52nd hole)
        aci3 = acistr("AZ69743")
        self.assertTrue(aci3.hole == 'AZ')
        self.assertTrue(aci3.core == '69743')
        
        # invalid string
        self.assertRaises(InvalidHoleCoreStringError, acistr, "1F")
        
    def test_aci_sort(self):
        a1 = acistr("A1")
        a2 = acistr("A2")
        a10 = acistr("A10")
        b1 = acistr("B1")
        b2 = acistr("B2")
        aa1 = acistr("AA1")
        ab1 = acistr("AB1")
        ab10 = acistr("AB10")
        ab11 = acistr("AB11")
        bb1 = acistr("BB1")
        self.assertFalse(a1 < a1)
        self.assertTrue(a1 < a2)
        self.assertTrue(a1 < a10)
        self.assertTrue(a2 < a10)
        self.assertTrue(a1 < b1)
        self.assertTrue(b1 < b2)
        self.assertTrue(a1 < aa1)
        self.assertTrue(aa1 < ab1)
        self.assertTrue(ab1 < ab10)
        self.assertTrue(ab10 < ab11)
        self.assertTrue(ab10 < bb1)
    
    def test_mci_eq(self):
        c1 = aci('A', '1')
        c1dup = aci('A', '1')
        self.assertTrue(c1 == c1dup)
        self.assertFalse(c1 != c1dup)
    
    # todo: move handy list routines to their own module along with this test
    def test_same_elements(self):
        list1 = [acistr("A1"), acistr("A2"), acistr("A3"), acistr("B3")]
        list2 = [acistr("B3"), acistr("A3"), acistr("A1"), acistr("A2")] # reordered elts of list1
        list3 = [acistr("B3"), acistr("A3"), acistr("A1"), acistr("A4")] # A4 is oddball
        self.assertTrue(sameElements(list1, list2))
        self.assertFalse(sameElements(list1, list3))
        self.assertFalse(sameElements(list2, list3))
        
    def test_bogus(self):
        bogusCore = AffineCoreInfo.createBogus()
        self.assertTrue(bogusCore == AffineCoreInfo.createBogus())
        
    def test_connected(self):
        secsumm = sectionSummary.SectionSummary.createWithFile('testdata/U1390_reduced_SectionSummary.csv')
        builder = AffineBuilder.createWithAffineFile('testdata/U1390_reduced_affine1.csv', secsumm)
        
        self.assertFalse(builder.affine.isConnected(acistr("C1"), [acistr("A1"), acistr("B1")], [], []))
        
        # A1 and B1 are connected - commutative
        self.assertTrue(builder.affine.isConnected(acistr("A1"), [acistr("B1")], [], []))
        self.assertTrue(builder.affine.isConnected(acistr("B1"), [acistr("A1")], [], []))
        
        # A3 is connected to both C2 and C3 via B2...
        self.assertTrue(builder.affine.isConnected(acistr("A3"), [acistr("C2")], [], []))
        self.assertTrue(builder.affine.isConnected(acistr("A3"), [acistr("C3")], [], []))
        
        # ...but if B2 is excluded, they're not
        self.assertFalse(builder.affine.isConnected(acistr("A3"), [acistr("C2")], [acistr("B2")], []))
        self.assertFalse(builder.affine.isConnected(acistr("A3"), [acistr("C3")], [acistr("B2")], []))
        
        # connected in the other direction too, i.e. starting from C2 or C3, seeking A3...
        self.assertTrue(builder.affine.isConnected(acistr("C2"), [acistr("A3")], [], []))
        self.assertTrue(builder.affine.isConnected(acistr("C3"), [acistr("A3")], [], []))
        
        # ...again, unless B2 is excluded
        self.assertFalse(builder.affine.isConnected(acistr("C2"), [acistr("A3")], [acistr("B2")], []))
        self.assertFalse(builder.affine.isConnected(acistr("C3"), [acistr("A3")], [acistr("B2")], []))
        
        # now create ties from C3 > B3 > A3...
        builder.tie(True, 0.0, acistr("C3"), 1.0, acistr("B3"), 0.5)
        builder.tie(True, 0.0, acistr("B3"), 1.0, acistr("A3"), 0.5)
        
        # ...which means there's now a path from A3 to C3 that doesn't involve B2 
        self.assertTrue(builder.affine.isConnected(acistr("A3"), [acistr("C3")], [acistr("B2")], []))
        
    # test related core gathering for "shift core and all related below" operations
    def test_chain(self):
        secsumm = sectionSummary.SectionSummary.createWithFile("testdata/FOO_SectionSummary.csv")
        builder = AffineBuilder.createWithSectionSummary(secsumm)
        
        # no existing ties, shift B1 and below
        movers = builder.gatherRelatedCores(acistr("A1"), acistr("B1"))
        self.assertTrue(sameElements(builder.getCoresBelow(acistr("B1")), movers))
        
        # shift C2 and below
        movers = builder.gatherRelatedCores(acistr("A1"), acistr("C2"))
        self.assertTrue(sameElements(builder.getCoresBelow(acistr("C2")), movers))
        
        # add tie between B3 and C3
        movers = builder.gatherRelatedCores(acistr("B3"), acistr("C3"))
        self.assertTrue(sameElements(builder.getCoresBelow(acistr("C3")), movers))
        builder.tie(False, 0.2, acistr("B3"), 0.3, acistr("C3"), 0.1)
        
        # now shift B1 and below
        movers = builder.gatherRelatedCores(acistr("A1"), acistr("B1"))
        expectedMovers = acilist(["B2", "B3", "B4", "C3", "C4"])
        self.assertTrue(sameElements(expectedMovers, movers))
        
        # or C1 and below
        movers = builder.gatherRelatedCores(acistr("A1"), acistr("C1"))
        expectedMovers = acilist(["B3", "B4", "C2", "C3", "C4"])
        self.assertTrue(sameElements(expectedMovers, movers))
        
        # reset: ties A1 > B1, B1 > C1, B2 > A3, A3 > B3
        builder.reset()
        builder.tie(False, 0.2, acistr("A1"), 0.3, acistr("B1"), 0.1) # push B down 0.2
        builder.tie(False, 0.2, acistr("B1"), 0.1, acistr("C1"), 0.1) # push C down 0.2
        builder.tie(False, 0.2, acistr("B2"), 2.0, acistr("A3"), 2.0) # push A3 down 0.2
        builder.tie(False, 0.2, acistr("A3"), 2.4, acistr("B3"), 2.2) # push B3 down 0.2 for total shift of 0.4
        
        # now shift B1
        movers = builder.gatherRelatedCores(acistr("A1"), acistr("B1"))
        #print movers
        expectedMovers = acilist(["A3", "A4", "B2", "B3", "B4", "C1", "C2", "C3", "C4"])
        self.assertTrue(sameElements(expectedMovers, movers, True))
        
        # reset, tie B2 > C2 instead of B1 > C1 as above: ties A1 > B1, B2 > C2, B2 > A3, A3 > B3
        builder.reset()
        builder.tie(False, 0.2, acistr("A1"), 0.3, acistr("B1"), 0.1) # push B1+ down 0.2
        builder.tie(False, 0.2, acistr("B2"), 1.1, acistr("C2"), 1.1) # push C2+ down 0.2
        builder.tie(False, 0.2, acistr("B2"), 2.0, acistr("A3"), 2.0) # push A3+ down 0.2
        builder.tie(False, 0.2, acistr("A3"), 2.4, acistr("B3"), 2.2) # push B3+ down 0.2 for total shift of 0.4
        
        # again, shift B1 - now C1 should remain unmoved
        movers = builder.gatherRelatedCores(acistr("A1"), acistr("B1"))
        expectedMovers = acilist(["A3", "A4", "B2", "B3", "B4", "C2", "C3", "C4"])
        self.assertTrue(sameElements(expectedMovers, movers))
        
        # tricky scenario 1 - updating A1 > B1 tie
        secsumm = sectionSummary.SectionSummary.createWithFile('testdata/U1390_reduced_SectionSummary.csv')
        builder = AffineBuilder.createWithAffineFile('testdata/U1390_reduced_affine1.csv', secsumm)
        movers = builder.gatherRelatedCores(acistr('A1'), acistr('B1'))
        expectedMovers = acilist(['A3', 'A4', 'B2', 'B3', 'B4', 'C2', 'C3', 'C4'])
#         print movers
#         print "expected = {}".format(expectedMovers)
        self.assertTrue(sameElements(expectedMovers, movers))
        
        # tricky scenario 2 replacing A1 > B1 tie with C1 > B1 should *not* move A2,
        # which currently happens because we're not considering the fact that A1 is
        # the old fixed core
        movers = builder.gatherRelatedCores(acistr('C1'), acistr('B1'))
        expectedMovers = acilist(['A3', 'A4', 'B2', 'B3', 'B4', 'C2', 'C3', 'C4'])
        self.assertTrue(sameElements(expectedMovers, movers, True))
        
        # scenario 1
        builder = AffineBuilder.createWithAffineFile('testdata/U1390_reduced_scenario1.csv', secsumm)
        
        # TIE of B1
        movers = builder.gatherRelatedCores(acistr('A1'), acistr('B1'))
        expectedMovers = acilist(['A2', 'A3', 'A4', 'B2', 'B3', 'B4', 'C3', 'C4'])
        self.assertTrue(sameElements(expectedMovers, movers, True))
        
        # SET of B1 should break A1 > B1 and A2 > B2 ties, leaving A cores unmoved
        bogusFromCore = AffineCoreInfo.createBogus()
        movers = builder.gatherRelatedCores(bogusFromCore, acistr('B1'), setAllOperation=True)
        expectedMovers = acilist(['B2', 'B3', 'B4', 'C3', 'C4'])
        self.assertTrue(sameElements(expectedMovers, movers, True))
        
        # scenario 2
        builder = AffineBuilder.createWithAffineFile('testdata/U1390_reduced_scenario2.csv', secsumm)        

        # TIE of B1
        movers = builder.gatherRelatedCores(acistr('A1'), acistr('B1'))
        expectedMovers = acilist(['A4', 'B2', 'B3', 'B4', 'C3', 'C4'])
        self.assertTrue(sameElements(expectedMovers, movers, True))
        
        # SET of B1
        movers = builder.gatherRelatedCores(bogusFromCore, acistr('B1'), setAllOperation=True)
        expectedMovers = acilist(['A4', 'B2', 'B3', 'B4', 'C3', 'C4'])
        self.assertTrue(sameElements(expectedMovers, movers, True))
        
        # scenario 3
        builder = AffineBuilder.createWithAffineFile('testdata/U1390_reduced_scenario3.csv', secsumm)
         
        # TIE of B1
        movers = builder.gatherRelatedCores(acistr('A1'), acistr('B1'))
        expectedMovers = acilist(['A2', 'A3', 'A4', 'B2', 'B3', 'B4', 'C3', 'C4'])
        self.assertTrue(sameElements(expectedMovers, movers, True))
         
        # SET of B1
        movers = builder.gatherRelatedCores(bogusFromCore, acistr('B1'), setAllOperation=True)
        expectedMovers = acilist(['A4', 'B2', 'B3', 'B4', 'C3', 'C4'])
        self.assertTrue(sameElements(expectedMovers, movers, True))

        # scenario 4
        builder = AffineBuilder.createWithAffineFile('testdata/U1390_reduced_scenario4.csv', secsumm)
         
        # TIE from C2 to B1
        movers = builder.gatherRelatedCores(acistr('C2'), acistr('B1'))
        expectedMovers = acilist(['B2', 'B3', 'B4'])
        self.assertTrue(sameElements(expectedMovers, movers, True))
         
        # SET of B1
        movers = builder.gatherRelatedCores(bogusFromCore, acistr('B1'), setAllOperation=True)
        expectedMovers = acilist(['B2', 'B3', 'B4', 'C1', 'C2', 'C3', 'C4'])
        self.assertTrue(sameElements(expectedMovers, movers, True))
        
        

if __name__ == "__main__":
    for testcase in [TestAffineTable, TestAffine]:
        suite = unittest.TestLoader().loadTestsFromTestCase(testcase)
        unittest.TextTestRunner(verbosity=2).run(suite)
    #unittest.main()
