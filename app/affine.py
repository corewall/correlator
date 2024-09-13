'''
Created on Feb 22, 2017

@author: bgrivna

Support for the creation and editing of Affine Shifts and resulting tables.
'''
from __future__ import print_function

from builtins import str
from builtins import object
import re # to parse combined hole/core strings
import unittest
from copy import deepcopy
from enum import Enum

import numpy

import tabularImport
import sectionSummary

class AffineError(Exception):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message

class AffineShift(object):
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
# dubbed REL that maintains relative positions between cores in a hole. Ultimately, such
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
    
# An affine shift resulting from the alignment of a point on the core to be shifted
# with a point on fromCore, which will remain fixed. The most desirable type of shift,
# as it typically results from a strong visual or measured correlation between two holes.
#
# Good to Know: The distance arg alone determines shift distance. fromDepth and depth
# args are only used for record-keeping in affine tables. Thus we don't bother
# checking 1) whether the associated cores have material at those depths, or
# 2) whether the difference between depth and fromDepth corresponds to distance.
# TODO? Perhaps we should.
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

# An affine shift in which the user selects a specific offset distance for a core
# or cores. SetShifts are typically used when a TieShift cannot be made due to 
# disrupted sediment (e.g. by drilling), or the total absence of sediment in another
# hole to which to create a TieShift.
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
class AffineTable(object):
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
    
    def getAllShifts(self):
        return self.shifts

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

    # returns True if core is the root of a chain i.e. the parent of
    # one or more cores, and non-TIE itself.
    def isRoot(self, core):
        return self.countChildren(core) > 0 and not isTie(self.getShift(core))

    # returns True if core is the root of a chain, or core is a TIE
    # and parent of 2+ cores i.e. 1+ new branches originate from core
    def isChainTop(self, core):
        # ugh can't remember what the point of this is...basically returns true
        # if core is root of a chain, or if core is mid-chain but parent to 2+
        # cores i.e. chain splits/diverges at that core
        tiedChainTop = self.countChildren(core) > 1 and isTie(self.getShift(core))
        return tiedChainTop or self.isRoot(core)#(self.countChildren(core) > 0 and not isTie(self.getShift(core)))
        
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
    
    # get immediate descendants of core - excludes core itself
    def getChildren(self, core):
        return [shift for shift in self.shifts if isTie(shift) and shift.fromCore == core]
    
    # count immediate descendants of core - excludes core itself
    def countChildren(self, core):
        return len(self.getChildren(core))

    # get all descendants of core - excludes core itself
    def getDescendants(self, core):
        descs = []
        shift = self.getShift(core)
        self._walkChain([shift], descs)
        if core in descs:
            descs.remove(core)
        return descs

    # count all descendants of core - excludes core itself
    def countDescendants(self, core):
        descs = self.getDescendants(core)
        return len(descs)
    
    # return list of all AffineCoreIds that are part of core's TIE chain (if any), including core itself
    def getChainCores(self, core):
        chainCores = []
        if self.inChain(core):
            root = self.getRoot(core)
            self._walkChain([root], chainCores)
        return chainCores
    
    # gather all cores that descend from the shifts in nodes, return in chainCores
    # nodes: a list of *shifts* (not cores) from which to walk the tie chain
    # chainCores: client-provided list to be filled with descendant cores on return
    def _walkChain(self, nodes, chainCores):
        for n in nodes:
            self._walkChain(self.getChildren(n.core), chainCores)
            chainCores.append(n.core)
            
    # get shift for immediate parent of core
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


class TieShiftMethod(Enum):
    CoreOnly = 0
    CoreAndRelatedBelow = 1
    CoreAndAllBelow = 2
    TiedAndDeeperInHoles = 3
    TiedAndDeeperInChain = 4


# Wraps AffineTable in logic that manages inter-core effects of SET and TIE operations
# on a core 'and related cores', maintaining chains where possible and noting where breaks
# will occur for a given shift.
class AffineBuilder(object):
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
        for _, row in df.iterrows(): # _ is dummy var for unused index
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
                print("Seeded missing affine shift for {} using core above {}".format(c, coreAbove))
            else:
                affineShifts.append(ImplicitShift(c, 0.0, dataUsed="", comment="seeded: no core above, no shift"))
                print("No core above found to seed affine shift for {}, no shift".format(c))
        
        affineBuilder.affine = AffineTable.createWithShifts(affineShifts)
        affineBuilder.sectionSummary = secsumm
        affineBuilder.site = list(secsumm.getSites())[0] # assume a single site!
        return affineBuilder

    def _parseAffineRow(self, row):
        hole = row['Hole']
        core = row['Core']
        offset = row['Cumulative offset (m)']
        shiftType = row['Shift type']
        dataUsed = row['Data used']
        comment = row['Quality comment']
        
        fixedCore = fixedCsf = shiftedCsf = ""
        if shiftType == 'TIE':
            if 'Reference core' in row: # new-style affine table
                fixedCore = row['Reference core']
                fixedCsf = row['Reference tie point CSF-A (m)']
                shiftedCsf = row['Shift tie point CSF-A (m)']
            else: # older affine with no TIE chain information
                pass
        
        return hole, core, offset, shiftType, fixedCore, fixedCsf, shiftedCsf, dataUsed, comment
        
    def __repr__(self):
        return str(self.affine)
        
    def clear(self):
        self.affine.clear()
        
    def reset(self):
        self.affine.reset()

    # Perform tasks in AffineOperation ao
    def execute(self, ao):
        for shift in ao.shifts:
            self.affine.addShift(shift)
        for core, distance in ao.adjusts:
            self.affine.adjust(core, distance)
        for core in ao.implicits:
            self.affine.makeImplicit(core)

    # Modify core's existing shift by deltaDistance.
    def adjust(self, core, deltaDistance):
        self.affine.getShift(core).adjust(deltaDistance)

    # Return the difference between a core's current affine shift and
    # new_shift_distance.
    # core: AffineCoreInfo
    # new_shift_distance: proposed shift distance
    def getShiftDelta(self, core, new_shift_distance):
        delta = new_shift_distance
        if self.affine.hasShift(core):
            delta = new_shift_distance - self.affine.getShiftDistance(core)
        return delta

    # Get distance of a SET shift as measured from the core's original,
    # unshifted position, handling percentage-based shifts if needed.
    # NEW: 
    # If isPercent is True, return distance of a SET shift as measured from
    # the core's CCSF depth.
    # If not, return distance of a SET as measured from core's original CSF-A depth.
    # TODO: This dichotomy is gross and should be resolved, but for now we're
    # just Making Things Work.
    def _getSETDistance(self, hole, core, value, isPercent, site, _sectionSummary):
        if isPercent:
            csf_a_top, _ = _sectionSummary.getCoreRange(site, hole, core)
            shift_dist = self.affine.getShiftDistance(aci(hole, core))
            ccsf_top = csf_a_top + shift_dist
            distance = (ccsf_top * value) - csf_a_top
        else:
            distance = value
        return distance
     
    # Shift one core by a given distance (SET).
    # core: core to shift
    # distance: distance, in meters, to shift core from its original, unshifted position
    # capitalized method name to avoid confusion with built-in set()
    def SET(self, hole, core, value, isPercent, site, _sectionSummary, dataUsed="", comment=""):
        ao = AffineOperation()
        core_id = aci(hole, core)
        breaks = self.findBreaksForSET([core_id])
        ao.infoDict['breaks'] = breaks
        shiftDistance = self._getSETDistance(hole, core, value, isPercent, site, _sectionSummary)
        ao.shifts.append(SetShift(core_id, shiftDistance, dataUsed, comment))
        for b in breaks:
            childCore = b[1]
            if childCore != core_id:
                ao.implicits.append(childCore)
        return ao
    
    # Wrapper that immediately executes AffineOperation generated by SET(), used for testing.
    def _set(self, hole, core, value, isPercent, site, _sectionSummary, dataUsed="", comment=""):
        ao = self.SET(hole, core, value, isPercent, site, _sectionSummary, dataUsed="", comment="")
        self.execute(ao)

    # Shift all cores of specified hole in coreList (SET).
    # hole: hole of cores in coreList
    # coreList: list of cores in hole to be SET
    # value: shift distance from core's original, unshifted position if isPercent is False,
    #        otherwise a percentage of core's original top depth by which to shift.
    # isPercent: if True, value is a percentage, otherwise a distance
    # site: current site (required to query SectionSummary for core top depth)
    # _sectionSummary: SectionSummary to query for core top depth
    def setAll(self, hole, coreList, value, isPercent, site, _sectionSummary, dataUsed="", comment=""):
        ao = AffineOperation()
        tieCores = [aci(hole, c) for c in coreList if self.isTie(aci(hole, c))]
        ao.infoDict['tieCores'] = tieCores

        # warn/confirm about breaks for chain roots that will be moved...
        chainRoots = [aci(hole, c) for c in coreList if self.affine.isRoot(aci(hole, c))]
        ao.infoDict['chainRoots'] = chainRoots
        breaks = self.findBreaksForSET(chainRoots)
        ao.infoDict['breaks'] = breaks
        for b in breaks:
            ao.implicits.append(b[1]) # child core

        setCoreList = [c for c in coreList if aci(hole, c) not in tieCores]
        for core in setCoreList:
            shiftDistance = self._getSETDistance(hole, core, value, isPercent, site, _sectionSummary)
            ao.shifts.append(SetShift(aci(hole, core), shiftDistance, dataUsed, comment))

        return ao
    
    # Shift entire TIE chain by a SET of chain root.
    # core: core to shift, must be root of a TIE chain
    # distance: distance, in meters, to shift chain from its original, unshifted position
    def setChainRoot(self, core, distance, dataUsed="", comment=""):
        assert self.affine.isRoot(core)
        ao = AffineOperation()
        shift = self.affine.getShift(core)
        deltaDistance = distance - shift.distance
        descendants = self.affine.getDescendants(core)
        ao.shifts.append(SetShift(core, distance, dataUsed, comment))
        for ci in descendants:
            if ci != core:
                ao.adjusts.append((ci, deltaDistance))
        return ao

    # Shift core(s) based on a tie between two cores.
    # method: TieShiftMethod
    # mcdShiftDistance: distance between tie points in MCD space
    # fromCore, fromDepth: core and MBSF depth of tie on fixed core
    # core, depth: core and MBSF depth of tie on core to be shifted
    # dataUsed: data type used to create shift
    # comment: user comment/annotation of shift
    def tie(self, method, mcdShiftDistance, fromCore, fromDepth, core, depth, dataUsed="", comment=""):
        ao = AffineOperation()
        totalShiftDistance = self.affine.getShiftDistance(core) + mcdShiftDistance
        if method == TieShiftMethod.CoreOnly:
            ao.infoDict['breaks'] = self.findBreaks(fromCore, core)
            ao.shifts.append(TieShift(fromCore, fromDepth, core, depth, totalShiftDistance, dataUsed, comment))
        elif method in [TieShiftMethod.CoreAndRelatedBelow, TieShiftMethod.CoreAndAllBelow]:
            if method == TieShiftMethod.CoreAndRelatedBelow:
                relatedCores = self.gatherRelatedCores(fromCore, core)
            else:
                relatedCores = self.gatherAllCoresBelow(fromCore, core)
            ao.infoDict['breaks'] = self.findBreaks(fromCore, core, relatedCores)
            ao.shifts.append(TieShift(fromCore, fromDepth, core, depth, totalShiftDistance, dataUsed, comment))
            for ci in relatedCores:
                ao.adjusts.append((ci, mcdShiftDistance))
        elif method == TieShiftMethod.TiedAndDeeperInHoles:
            ao.shifts.append(TieShift(fromCore, fromDepth, core, depth, totalShiftDistance, dataUsed, comment))
            relatedCores = self.gatherTiedAndDeeperInHoles(fromCore, core)
            ao.infoDict['breaks'] = self.findBreaks(fromCore, core, relatedCores)
            for ci in relatedCores:
                ao.adjusts.append((ci, mcdShiftDistance))
        elif method == TieShiftMethod.TiedAndDeeperInChain:
            ao.shifts.append(TieShift(fromCore, fromDepth, core, depth, totalShiftDistance, dataUsed, comment))
            relatedCores = self.gatherTiedAndDeeperInChain(fromCore, core)
            ao.infoDict['breaks'] = self.findBreaks(fromCore, core, relatedCores)
            for ci in relatedCores:
                ao.adjusts.append((ci, mcdShiftDistance))
        else:
            assert False, "Unknown TieShiftMethod {}".format(method)
                
        # change shift type of cores with just-broken ties to ImplicitShift
        for b in ao.infoDict['breaks']:
            childCore = b[1]
            if childCore != core: # original tie for core was broken by new tie - don't make implicit!
                ao.implicits.append(childCore)

        return ao

    # Wrapper that immediately executes AffineOperation generated by tie(), used for testing.
    def _tie(self, method, mcdShiftDistance, fromCore, fromDepth, core, depth, dataUsed="", comment=""):
        ao = self.tie(method, mcdShiftDistance, fromCore, fromDepth, core, depth, dataUsed, comment)
        self.execute(ao)

    # Wrapper that immediately executes AffineOperation generated by tie(), used for testing.
    # Omits depth and fromDepth, which are for record-keeping only, unneeded in testing.
    def _tieOmitDepths(self, method, mcdShiftDistance, fromCore, core, dataUsed="", comment=""):
        ao = self.tie(method, mcdShiftDistance, fromCore, 0, core, 0, dataUsed, comment)
        self.execute(ao)

    # Make core's shift type REL.
    def makeImplicit(self, core):
        self.affine.makeImplicit(core)

    # Find breaks for an affine operation, handling special case in which an edited
    # tie between the same two cores is *not* considered a break.
    # For a SET operation, use findBreaksForSET() wrapper.
    def findBreaks(self, fromCore, shiftCore, _movingCores=[]):
        # use local copy of _movingCores to avoid adding shiftCore to client list
        movingCores = list(_movingCores)
        if shiftCore:
            movingCores.append(shiftCore)
        breaks = []
        for core in movingCores:
            shift = self.getShift(core)
            if isTie(shift) and shift.fromCore not in movingCores and \
                (shiftCore is None or core != shiftCore or fromCore != shift.fromCore): # re-tie with same fromCore isn't a break
                breaks.append((shift.fromCore, core))
            for child in self.affine.getChildren(core):
                if child.core not in movingCores:
                    breaks.append((core, child.core))
        return breaks

    # Find breaks for a SET operation, just a wrapper of findBreaks() with
    # dummy arguments for fromCore and core.
    def findBreaksForSET(self, movingCores):
        return self.findBreaks(AffineCoreInfo.createBogus(), None, movingCores)
    
    # 9/9/2024 new approach #1
    # All downstream cores in the SHIFT core chain (if any).
    # All other chain cores (all holes) if the CCSF of the chain ROOT is deeper than CCSF of the SHIFT core.
    # All non-chain cores (all holes) if their CCSF is deeper than CCSF of the SHIFT core.
    def gatherTiedAndDeeperInHoles(self, fromCore, shiftCore):
        tadihCores = []

        # If shiftCore is part of a chain C, get all cores in C that can be shifted
        shiftCoreChainRoot = None
        if self.affine.inChain(shiftCore):
            chainCores = self.affine.getChainCores(shiftCore)
            if fromCore in chainCores:
                # fromCore cannot shift, only shift the descendants of shiftCore in this chain
                tadihCores += [core for core in self.affine.getDescendants(shiftCore)]
            elif self.affine.getParent(shiftCore):
                # if shiftCore is already tied from a different core, that core cannot shift,
                # only shiftCore and descendants should move.
                if self.affine.getParent(shiftCore).core != fromCore:
                    tadihCores += [core for core in self.affine.getDescendants(shiftCore)]
            else:
                tadihCores += [core for core in self.affine.getChainCores(shiftCore) if core != shiftCore]
            shiftCoreChainRoot = self.affine.getRoot(shiftCore).core
            # print(f"Cores in shiftCore {shiftCore} chain: {tadihCores} (excluding shiftCore)")

        # Get all cores in chains with root CCSF deeper than shiftCore, omitting
        # shiftCore's chain cores (if any), which are already gathered.
        # If fromCore is part of a chain, nothing in that chain can shift.
        shiftCoreCCSF = self.getCCSFDepth(shiftCore)
        otherChainRoots = [root for root in self.getChainRoots() if shiftCoreChainRoot is None or root != shiftCoreChainRoot]
        for root in otherChainRoots:
            if fromCore in self.affine.getChainCores(root):
                # print(f"Fixed core {fromCore} is part of chain with root {root}, skipping chain")
                continue
            # print(f"Chain root {root}: CCSF depth = {self.getCCSFDepth(root)}")
            if self.getCCSFDepth(root) > shiftCoreCCSF:
                # print(f"  Deeper than {shiftCore}, shifting chain")
                tadihCores += self.affine.getChainCores(root)

        # Get all non-chain cores with CCSF deeper than shiftCore, omitting fromCore if necessary.
        nonChainCores = [shift.core for shift in self.affine.getAllShifts() if not self.affine.inChain(shift.core)]
        deeperCores = []
        for core in nonChainCores:
            if core == fromCore: # fromCore cannot move!
                continue
            if self.getCCSFDepth(core) > shiftCoreCCSF:
                deeperCores.append(core)

        tadihCores += deeperCores

        # print(f"gatherTiedAndDeeperInHoles: fromCore = {fromCore}, shiftCore = {shiftCore}:\n{sorted(tadihCores)}")
        return tadihCores

    # 9/9/2024 new approach #2
    # All downstream cores in the SHIFT core chain (if any).
    # All other non-chain cores if a shallower core in the hole is being shifted.
    def gatherTiedAndDeeperInChain(self, fromCore, shiftCore):
        tadicCores = []

        # If shiftCore is part of a chain C, get all cores in C that can be shifted
        # TODO: near-duplicate of gatherTiedAndDeeperInHoles logic
        if self.affine.inChain(shiftCore):
            chainCores = self.affine.getChainCores(shiftCore)
            if fromCore in chainCores:
                # fromCore cannot shift, only shift the descendants of shiftCore in this chain
                tadicCores += [core for core in self.affine.getDescendants(shiftCore)]
            elif self.affine.getParent(shiftCore):
                # if shiftCore is already tied from a different core, that core cannot shift,
                # only shiftCore and descendants should move.
                if self.affine.getParent(shiftCore).core != fromCore:
                    tadicCores += [core for core in self.affine.getDescendants(shiftCore)]
            else:
                tadicCores += [core for core in self.affine.getChainCores(shiftCore) if core != shiftCore]

        # Get all non-chain cores below uppermost shifting cores in each hole represented
        # in tadicCores list plus the shiftCore itself.
        uppermostCores = self._getUppermostCores(tadicCores + [shiftCore])
        for core in uppermostCores:
            coresBelow = [cb for cb in self.getCoresBelow(core) if not self.affine.inChain(cb) and cb != fromCore]
            tadicCores += coresBelow

        return tadicCores


    # Gather all cores that will be shifted by "Shift by [shiftCore] and related
    # cores below" action. Note that the result excludes shiftCore itself.
    def gatherRelatedCores(self, fromCore, shiftCore):
        # gather all descendants of shiftCore
        shiftKids = self.affine.getDescendants(shiftCore)
        shiftKids.append(shiftCore) # include shiftCore

        # gather holes represented by descendants
        holes = list(set([sk.hole for sk in shiftKids]))
        # print("Represented holes = {}".format(holes))
        relatedCores = []
        for hole in holes:
            # find all chain cores in this hole
            holeChainCores = [h for h in shiftKids if h.hole == hole]
            # for each, gather cores below until another chain core is found
            for hcc in holeChainCores:
                if hcc != shiftCore:
                    relatedCores.append(hcc)
                coresBelow = sorted(self.getCoresBelow(hcc))
                for cb in coresBelow:
                    if not self.affine.inChain(cb) and cb != fromCore:
                        relatedCores.append(cb)
                    else: # chain core - whether it's distinct or not, restart from next holeChainCore
                        break
        return relatedCores

    # Gather all cores that will be shifted by "Shift by [shiftCore] and all cores
    # below" action. Note that the result excludes shiftCore itself.
    def gatherAllCoresBelow(self, fromCore, shiftCore):
        # print("gatherAllCoresBelow: {} -> {}".format(fromCore, shiftCore))
        # gather all descendants of shiftCore, if any
        shiftKids = self.affine.getDescendants(shiftCore)
        shiftKids.append(shiftCore) # include shiftCore

        # Of shift core and its descendants, find uppermost core in each hole,
        # of the holes represented by those cores.
        uppermostCores = self._getUppermostCores(shiftKids)

        # From each hole's uppermost core, search downward. When cores
        # in separate chains are found, gather all cores in their chains.
        separateChainCores = []
        seenChainRoots = []
        for uhcc in uppermostCores:
            coresBelow = sorted(self.getCoresBelow(uhcc))
            for cb in coresBelow:
                if self.affine.inChain(cb) and cb not in shiftKids:
                    chainRoot = self.affine.getRoot(cb)
                    if chainRoot not in seenChainRoots: # skip visited chains
                        separateChainCores += self.affine.getChainCores(cb)
                        seenChainRoots.append(chainRoot)
        # assert len(separateChainCores) == len(set(separateChainCores))

        # Now we have a list of *all* chain cores affected by the shift
        # of shiftCore. Again, find uppermost core in each hole, of the
        # holes represented by all chain cores.
        allChainCores = separateChainCores + shiftKids
        uppermostCores = self._getUppermostCores(allChainCores)

        # Each hole's uppermost core, and every core below it is a related core!
        # The only exceptions are:
        # - fromCore, which by definition cannot move
        # - shiftCore, because it is excluded from the result of this f'n
        relatedCores = list(uppermostCores)
        for uc in uppermostCores:
            relatedCores.append(uc)
            coresBelow = sorted(self.getCoresBelow(uc))
            for cb in coresBelow:
                relatedCores.append(cb)

        # print("fromCore: {}, relatedCores: {}".format(fromCore, relatedCores))
        relatedCores = list(set(relatedCores)) # remove duplicates
        if fromCore in relatedCores:
            relatedCores.remove(fromCore)
        if shiftCore in relatedCores:
            relatedCores.remove(shiftCore)

        # print("gatherAllCoresBelow: {}".format(relatedCores))
        return relatedCores

    # return list of uppermost core in each hole in list of cores
    def _getUppermostCores(self, cores):
        holes = list(set([core.hole for core in cores]))
        uppermostCores = []
        for hole in holes:
            holeCores = [hcc for hcc in cores if hcc.hole == hole]
            uppermost = min(holeCores, key=lambda hcc:self._getCoreTop(hcc))
            uppermostCores.append(uppermost)
        return uppermostCores
        
    def _getCoreTop(self, ci):
        return self.sectionSummary.getCoreTop(self.site, ci.hole, ci.core)
    
    # Get all cores in hole below core by name - not actual position!
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

    def getShiftDistance(self, core):
        return self.affine.getShiftDistance(core)
    
    def getCCSFDepth(self, core):
        return self._getCoreTop(core) + self.affine.getShiftDistance(core)
    
    # return list of shifts, sorted first by hole, then core
    def getSortedShifts(self):
        return sorted(self.affine.shifts, key=lambda x:x.core)
    
    # return sorted list of holes represented in affine table
    def getSortedHoles(self):
        holeSet = set([x.core.hole for x in self.affine.shifts])
        return sorted(list(holeSet))

    # return list of AffineCoreInfos for TIE chain roots
    def getChainRoots(self):
        roots = [s.core for s in self.affine.shifts if self.affine.isRoot(s.core)]
        return roots
    
    def isTie(self, core):
        return isTie(self.getShift(core))

    def isRoot(self, core):
        return self.affine.isRoot(core)

    def getChildren(self, core):
        return self.affine.getChildren(core)

    def countChildren(self, core):
        return self.affine.countChildren(core)
    
    # if core is "below" compareCore, return True, else False
    def coreIsBelow(self, coreInfo, compareCoreInfo):
        return (self._getCoreTop(coreInfo) + self.getShift(coreInfo).distance) >= (self._getCoreTop(compareCoreInfo) + self.getShift(compareCoreInfo).distance)
    

# Blob of shifts, adjusts, implicits, and other operation-specific data.
class AffineOperation(object):
    def __init__(self):
        self.shifts = [] # list of AffineShifts
        self.adjusts = [] # list of (AffineCoreInfo, adjust distance) tuples
        self.implicits = [] # list of AffineCoreInfos to be made implicit
        self.infoDict = {} # dictionary of operation-specific data for client use

    # Return list of AffineCoreInfos for cores that will be moved
    # by this operation.
    def getCoresToBeMoved(self):
        shifting = [s.core for s in self.shifts]
        adjusting = [a[0] for a in self.adjusts]
        # assert len(shifting) + len(adjusting) == len(set(shifting + adjusting))
        return shifting + adjusting


# Reference to hole and core for affine shifts
class AffineCoreInfo(object):
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
        print("sameElements(): no match!\nlist1 = {}\nlist2 = {}".format(list1, list2))
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
    for index, colname in enumerate(['Reference core', 'Reference tie point CSF-A', 'Shift tie point CSF-A']): 
        prev3df.insert(index + 10, colname, "")
    #print prev3df
    return prev3df


class TestAffineTable(unittest.TestCase):
    def test_chain_funcs(self):
        a1 = acistr('A1')
        a2 = acistr('A2')
        b1 = acistr('B1')
        b2 = acistr('B2')
        c1 = acistr('C1')
        c2 = acistr('C2')
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

        # All roots are chain tops, but not all chain tops are roots.
        # isRoot() - only A1 is a root since B1 is a TIE
        self.assertTrue(affine.isRoot(a1))
        self.assertFalse(affine.isRoot(b1))
        self.assertTrue(affine.isRoot(d1)) # D1 is root of separate chain
        self.assertFalse(affine.isRoot(d3)) # D3 isn't part of any chain

        # getRoot()
        self.assertTrue(affine.getRoot(a2).core == a1)
        self.assertTrue(affine.getRoot(b2).core == a1)
        self.assertTrue(affine.getRoot(d2).core == d1)
        
        # isChainTop() - A1 is chain top but is not a TIE
        self.assertTrue(affine.isChainTop(a1))
        
        # B1 is a chain top that is a TIE
        self.assertTrue(affine.isChainTop(b1))

        # all others are not chain tops        
        self.assertFalse(affine.isChainTop(b2))
        self.assertFalse(affine.isChainTop(c2))
        self.assertFalse(affine.isChainTop(a2))
        
        # countChildren() - immediate descendants only
        self.assertTrue(affine.countChildren(b1) == 2) # A2, C2
        self.assertTrue(affine.countChildren(a1) == 1) # B1
        self.assertTrue(affine.countChildren(c2) == 1) # B2
        self.assertTrue(affine.countChildren(b2) == 0)
        self.assertTrue(affine.countChildren(d3) == 0)

        # countDescendants() - all descendants
        self.assertTrue(affine.countDescendants(a1) == 4)
        self.assertTrue(affine.countDescendants(a2) == 0)
        self.assertTrue(affine.countDescendants(b1) == 3)
        self.assertTrue(affine.countDescendants(b2) == 0)
        self.assertTrue(affine.countDescendants(c1) == 1)
        self.assertTrue(affine.countDescendants(c2) == 1)
        self.assertTrue(affine.countDescendants(d1) == 2)
        self.assertTrue(affine.countDescendants(d2) == 0)

        # getParent()
        self.assertTrue(affine.getParent(a1) is None)
        self.assertTrue(affine.getParent(b1).core == a1)
        self.assertTrue(affine.getParent(c2).core == b1)
        self.assertTrue(affine.getParent(a2).core == b1)
        self.assertTrue(affine.getParent(b2).core == c2)        

        # getChainCores()
        chain1Cores = affine.getChainCores(a1)
        self.assertTrue(b2 in chain1Cores)
        self.assertFalse(d1 in chain1Cores)
        
        chain2Cores = affine.getChainCores(d2)
        self.assertTrue(d1 in chain2Cores)
        
        # D3 isn't part of any chain
        self.assertTrue(affine.getChainCores(d3) == [])


class TestAffineUtils(unittest.TestCase):
    # use numpy.isclose to deal with tiny floating point discrepancies causing == to return False 
    def assertClose(self, fp1, fp2):
        return self.assertTrue(numpy.isclose(fp1, fp2))
    
    def test_convert_pre_v3(self):
        oldaff, msg = tabularImport._parseFile("testdata/pre_v3_affine.csv", tabularImport.AffineFormat_pre_v3, checkcols=True)
        newaff = convert_pre_v3_AffineTable(oldaff)
    
    def test_acistr(self):
        aci1 = acistr('A1')
        self.assertTrue(aci1.hole == 'A')
        self.assertTrue(aci1.core == '1')
        aci2 = acistr('B309')
        self.assertTrue(aci2.hole == 'B')
        self.assertTrue(aci2.core == '309')
        
        # physically ridiculous but logically valid case (after hole Z, next is AA, so AZ == 52nd hole)
        aci3 = acistr('AZ69743')
        self.assertTrue(aci3.hole == 'AZ')
        self.assertTrue(aci3.core == '69743')
        
        # invalid string
        self.assertRaises(InvalidHoleCoreStringError, acistr, "1F")
        
    def test_aci_sort(self):
        a1 = acistr('A1')
        a2 = acistr('A2')
        a10 = acistr('A10')
        b1 = acistr('B1')
        b2 = acistr('B2')
        aa1 = acistr('AA1')
        ab1 = acistr('AB1')
        ab10 = acistr('AB10')
        ab11 = acistr('AB11')
        bb1 = acistr('BB1')
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
        self.assertTrue(sameElements([], []))
        list1 = [acistr('A1'), acistr('A2'), acistr('A3'), acistr('B3')]
        list2 = [acistr('B3'), acistr('A3'), acistr('A1'), acistr('A2')] # reordered elts of list1
        list3 = [acistr('B3'), acistr('A3'), acistr('A1'), acistr('A4')] # A4 is oddball
        self.assertTrue(sameElements(list1, list2))
        self.assertFalse(sameElements(list1, list3))
        self.assertFalse(sameElements(list2, list3))
        
    def test_bogus(self):
        bogusCore = AffineCoreInfo.createBogus()
        self.assertTrue(bogusCore == AffineCoreInfo.createBogus())

# New TIE shift scopes and rules Fall 2024, Correlator 4.5.5+
class TestNewAffineScopes(unittest.TestCase):
    def test_tied_and_deeper_all_holes(self):
        secsumm = sectionSummary.SectionSummary.createWithFile("testdata/Sep2024_SectionSummary.csv") # Holes A-D cores 1-3, plus E1.
        builder = AffineBuilder.createWithSectionSummary(secsumm)

        # Do some setup.
        # Tie A1 > B1, B1 now has CCSF 0.2m
        builder._tieOmitDepths(TieShiftMethod.CoreOnly, 0.2, acistr('A1'), acistr('B1'))

        # Bump C1 down from 0m to 0.1m.
        builder._set("C", "1", 0.1, isPercent=False, site="1", _sectionSummary=secsumm)

        # Test 0: Shift A1 from C1.
        # This should shift All A and B cores, C2, C3, D2, D3.
        # C1 is the fixed/REF core. D1 (0m) is not below A1 (0m).
        movers = builder.gatherTiedAndDeeperInHoles(acistr('C1'), acistr('A1'))
        expectedMovers = acilist(['A2', 'A3', 'B1', 'B2', 'B3', 'C2', 'C3', 'D2', 'D3'])
        self.assertTrue(sameElements(expectedMovers, movers))

        # Tie C1 > D1. D1 now has CCSF 0.5m
        builder._tieOmitDepths(TieShiftMethod.CoreOnly, 0.5, acistr('C1'), acistr('D1'))
        
        # Tie D1 > C2. C2 now has CCSF 1.2m.
        builder._tieOmitDepths(TieShiftMethod.CoreOnly, 0.2, acistr('D1'), acistr('C2'))

        # for core in [acistr('A1'), acistr('B1'), acistr('C1'), acistr('D1'), acistr('C2')]:
            # print(f"Core {core} has CCSF depth {builder.getCCSFDepth(core)}m")

        # Now our depths and chains look like this:
        # CCSF depths: A1 0m, B1 0.2m, C1 0.1m, C2 1.2m, D1 0.5m.
        # Tie chains: A1 > B1; C1 > D1 > C2.

        # Test 1: Shift A1 from fixed E1. Every A-D core should move.
        # Note: shiftCore is omitted from gatherTiedAndDeeperInHoles() return list
        movers = builder.gatherTiedAndDeeperInHoles(acistr('E1'), acistr('A1'))
        expectedMovers = acilist(['A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3', 'D1', 'D2', 'D3'])
        self.assertTrue(sameElements(expectedMovers, movers))

        # Test 2: Shift B1 from fixed E1.
        # This breaks A1 > B1 tie. A1 will not move.
        # Chain C1 > D1 > C2 will not move because root C1's CCSF is above B1's CCSF.
        # A2, A3, B2, B3, C3, D2, D3 have CCSF below B1's CCSF, they will move.
        movers = builder.gatherTiedAndDeeperInHoles(acistr('E1'), acistr('B1'))
        expectedMovers = acilist(['A2', 'A3', 'B2', 'B3', 'C3', 'D2', 'D3'])
        self.assertTrue(sameElements(expectedMovers, movers))

        # Test 3: Shift C1 from fixed E1.
        # A2, A3, B2, B3, all C and D cores should move.
        # Chain A1 > B1 should not move because root A1's CCSF is above C1's CCSF
        movers = builder.gatherTiedAndDeeperInHoles(acistr('E1'), acistr('C1'))
        expectedMovers = acilist(['A2', 'A3', 'B2', 'B3', 'C2', 'C3', 'D1', 'D2', 'D3'])
        self.assertTrue(sameElements(expectedMovers, movers))

        # Test 4: Shift D1 from fixed E1.
        # This breaks C1 > D1 tie. C1 will not move.
        # C2 is downstream of D1, it will move.
        # A2, A3, B2, B3, C3, D2, D3 have CCSF below D1's CCSF, they will move.
        movers = builder.gatherTiedAndDeeperInHoles(acistr('E1'), acistr('D1'))
        expectedMovers = acilist(['A2', 'A3', 'B2', 'B3', 'C2', 'C3', 'D2', 'D3'])
        self.assertTrue(sameElements(expectedMovers, movers))

        # Test 5: Shift C2 from fixed E1.
        # This breaks D1 > C2 tie. Remnant chain C1 > D1 will not move.
        # A1, A2, B1, B2, D2 have CCSF at or above C2's CCSF, they will not move.
        # A3, B3, C3, D3 have CCSF below C2's CCSF, they will move.
        movers = builder.gatherTiedAndDeeperInHoles(acistr('E1'), acistr('C2'))
        expectedMovers = acilist(['A3', 'B3', 'C3', 'D3'])
        self.assertTrue(sameElements(expectedMovers, movers))

        # Test 6: Re-tie B1 from A1.
        # Almost the same as Test 2, but now fixed core A1 cannot move.
        movers = builder.gatherTiedAndDeeperInHoles(acistr('A1'), acistr('B1'))
        expectedMovers = acilist(['A2', 'A3', 'B2', 'B3', 'C3', 'D2', 'D3'])
        self.assertTrue(sameElements(expectedMovers, movers))

        # Test 7: Re-tie C2 from D1.
        # A3, B3, C3, D3 should move.
        movers = builder.gatherTiedAndDeeperInHoles(acistr('D1'), acistr('C2'))
        expectedMovers = acilist(['A3', 'B3', 'C3', 'D3'])
        self.assertTrue(sameElements(expectedMovers, movers))

        # Test 8: Shift C1 from B1.
        # A2, A3, B2, B3, all C and D should move.
        movers = builder.gatherTiedAndDeeperInHoles(acistr('B1'), acistr('C1'))
        expectedMovers = acilist(['A2', 'A3', 'B2', 'B3', 'C2', 'C3', 'D1', 'D2', 'D3'])
        self.assertTrue(sameElements(expectedMovers, movers))

        # Test 9: Shift A1 from C1.
        # C1 chain will want to shift (deeper root than A1) but it cannot because
        # C1 is fixed. Thus no C1 chain cores (C1 > D1 > C2) will move. Everything else should.
        movers = builder.gatherTiedAndDeeperInHoles(acistr('C1'), acistr('A1'))
        expectedMovers = acilist(['A2', 'A3', 'B1', 'B2', 'B3', 'C3', 'D2', 'D3'])
        self.assertTrue(sameElements(expectedMovers, movers))

        # Test 10: Shift D1 from A1.
        # Existing C1 > D1 tie must be broken.
        movers = builder.gatherTiedAndDeeperInHoles(acistr('A1'), acistr('D1'))
        expectedMovers = acilist(['A2', 'A3', 'B2', 'B3', 'C2', 'C3', 'D2', 'D3'])
        self.assertTrue(sameElements(expectedMovers, movers))

    # Same setup as test_tied_and_deeper_all_holes()
    # Same test cases too, but different expected results.
    def test_tied_and_deeper_this_chain(self):
        secsumm = sectionSummary.SectionSummary.createWithFile("testdata/Sep2024_SectionSummary.csv") # Holes A-D cores 1-3, plus E1.
        builder = AffineBuilder.createWithSectionSummary(secsumm)

        # Do some setup.
        # Tie A1 > B1, B1 now has CCSF 0.2m
        builder._tieOmitDepths(TieShiftMethod.CoreOnly, 0.2, acistr('A1'), acistr('B1'))

        # Bump C1 down from 0m to 0.1m.
        builder._set("C", "1", 0.1, isPercent=False, site="1", _sectionSummary=secsumm)

        # Test 0: Shift A1 from C1.
        # This should shift All A and B cores.
        # C1 is the fixed/REF core. C2, C3, and all D cores are not below shifting cores.
        movers = builder.gatherTiedAndDeeperInChain(acistr('C1'), acistr('A1'))
        expectedMovers = acilist(['A2', 'A3', 'B1', 'B2', 'B3'])
        self.assertTrue(sameElements(expectedMovers, movers))

        # Tie C1 > D1. D1 now has CCSF 0.5m
        builder._tieOmitDepths(TieShiftMethod.CoreOnly, 0.5, acistr('C1'), acistr('D1'))
        
        # Tie D1 > C2. C2 now has CCSF 1.2m.
        builder._tieOmitDepths(TieShiftMethod.CoreOnly, 0.2, acistr('D1'), acistr('C2'))

        # Test 1: Shift A1 from fixed E1.
        # This should shift All A and B cores.
        # C, D, and E cores are not below shifting cores.
        movers = builder.gatherTiedAndDeeperInChain(acistr('E1'), acistr('A1'))
        expectedMovers = acilist(['A2', 'A3', 'B1', 'B2', 'B3'])
        self.assertTrue(sameElements(expectedMovers, movers))

        # Test 2: Shift B1 from fixed E1.
        # This breaks A1 > B1 tie. A1 will not move.
        # All B cores will shift.
        # C and D cores are not below shifting cores. E1 is fixed.
        movers = builder.gatherTiedAndDeeperInChain(acistr('E1'), acistr('B1'))
        expectedMovers = acilist(['B2', 'B3'])
        self.assertTrue(sameElements(expectedMovers, movers))

        # Test 3: Shift C1 from fixed E1.
        # All C and D cores will shift.
        # A and B cores are not below shifting cores. E1 is fixed.
        movers = builder.gatherTiedAndDeeperInChain(acistr('E1'), acistr('C1'))
        expectedMovers = acilist(['C2', 'C3', 'D1', 'D2', 'D3'])
        self.assertTrue(sameElements(expectedMovers, movers))

        # Test 4: Shift D1 from fixed E1.
        # This breaks C1 > D1 tie. C1 will not move.
        # C2, C3, and all D cores will shift.
        # A and B cores are not below shifting cores. E1 is fixed.
        movers = builder.gatherTiedAndDeeperInChain(acistr('E1'), acistr('D1'))
        expectedMovers = acilist(['C2', 'C3', 'D2', 'D3'])
        self.assertTrue(sameElements(expectedMovers, movers))

        # Test 5: Shift C2 from fixed E1.
        # This breaks D1 > C2 tie. Remnant chain C1 > D1 will not move.
        # C2, C3 will shift.
        # A, B, and D cores are not below shifting cores. E1 is fixed.
        movers = builder.gatherTiedAndDeeperInChain(acistr('E1'), acistr('C2'))
        expectedMovers = acilist(['C3'])
        self.assertTrue(sameElements(expectedMovers, movers))

        # Test 6: Re-tie B1 from A1.
        # All B cores will shift.
        # A, B, D, and E cores are not below shifting cores.
        movers = builder.gatherTiedAndDeeperInChain(acistr('A1'), acistr('B1'))
        expectedMovers = acilist(['B2', 'B3'])
        self.assertTrue(sameElements(expectedMovers, movers))

        # Test 7: Re-tie C2 from D1.
        # C2, C3 will shift.
        # A, B, D, E cores and C1 are not below shifting cores.
        movers = builder.gatherTiedAndDeeperInChain(acistr('D1'), acistr('C2'))
        expectedMovers = acilist(['C3'])
        self.assertTrue(sameElements(expectedMovers, movers))

        # Test 8: Shift C1 from B1.
        # All C and D cores will shift.
        # A, B, and E cores are not below shifting cores.
        movers = builder.gatherTiedAndDeeperInChain(acistr('B1'), acistr('C1'))
        expectedMovers = acilist(['C2', 'C3', 'D1', 'D2', 'D3'])
        self.assertTrue(sameElements(expectedMovers, movers))

        # Test 9: Shift A1 from C1.
        # All A and B cores will shift.
        # C, D, and E cores are not below shifting cores.
        movers = builder.gatherTiedAndDeeperInChain(acistr('C1'), acistr('A1'))
        expectedMovers = acilist(['A2', 'A3', 'B1', 'B2', 'B3'])
        self.assertTrue(sameElements(expectedMovers, movers))

        # Test 10: Shift D1 from A1.
        # This breaks C1 > D1 tie, C1 will not move.
        # C2, C3, all D cores will shift.
        # A, B, and E cores are not below shifting cores.
        movers = builder.gatherTiedAndDeeperInChain(acistr('A1'), acistr('D1'))
        expectedMovers = acilist(['C2', 'C3', 'D2', 'D3'])
        self.assertTrue(sameElements(expectedMovers, movers))        

class TestAffineBuilder(unittest.TestCase):
    def test_core_and_related(self):
        secsumm = sectionSummary.SectionSummary.createWithFile("testdata/FOO_SectionSummary.csv")
        builder = AffineBuilder.createWithSectionSummary(secsumm)
        method = TieShiftMethod.CoreAndRelatedBelow

        # no existing ties, tie from A1 > B1 shifts B1 and below
        movers = builder.gatherRelatedCores(acistr('A1'), acistr('B1'))
        self.assertTrue(sameElements(builder.getCoresBelow(acistr('B1')), movers))

        # B1 > A2 tie exists. New tie from A1 > B1 shifts A2+, B1+
        builder._tie(method, 0.1, acistr('B1'), 0.9, acistr('A2'), 0.8)
        movers = builder.gatherRelatedCores(acistr('A1'), acistr('B1'))
        expectedMovers = acilist(['A2', 'A3', 'A4', 'A5', 'B2', 'B3', 'B4', 'B5'])
        self.assertTrue(sameElements(expectedMovers, movers))

        ### BEGIN other old tests

        # add tie between B3 and C3
        movers = builder.gatherRelatedCores(acistr('B3'), acistr('C3'))
        self.assertTrue(sameElements(builder.getCoresBelow(acistr('C3')), movers))
        builder._tie(method, 0.2, acistr('B3'), 0.3, acistr('C3'), 0.1)
        
        # now shift B1 and below
        movers = builder.gatherRelatedCores(acistr('A1'), acistr('B1'))
        expectedMovers = acilist(['A2', 'A3', 'A4', 'A5', 'B2'])
        self.assertTrue(sameElements(expectedMovers, movers))
        
        # or C1 and below
        movers = builder.gatherRelatedCores(acistr('A1'), acistr('C1'))
        expectedMovers = acilist(['C2'])
        self.assertTrue(sameElements(expectedMovers, movers))

        # or C2 and below
        movers = builder.gatherRelatedCores(acistr('A1'), acistr('C2'))
        expectedMovers = []
        self.assertTrue(sameElements(expectedMovers, movers))

        # reset: ties A1 > B1, B1 > C1, B2 > A3, A3 > B3
        builder.reset()
        builder._tie(method, 0.2, acistr('A1'), 0.3, acistr('B1'), 0.1) # push B down 0.2
        builder._tie(method, 0.2, acistr('B1'), 0.1, acistr('C1'), 0.1) # push C down 0.2
        builder._tie(method, 0.2, acistr('B2'), 2.0, acistr('A3'), 2.0) # push A3 down 0.2
        builder._tie(method, 0.2, acistr('A3'), 2.4, acistr('B3'), 2.2) # push B3 down 0.2 for total shift of 0.4

        # now shift B1
        movers = builder.gatherRelatedCores(acistr('A1'), acistr('B1'))
        #print movers
        expectedMovers = acilist(['C1', 'C2', 'C3', 'C4', 'C5'])
        self.assertTrue(sameElements(expectedMovers, movers, True))
        
        # reset, tie B2 > C2 instead of B1 > C1 as above, resulting in three chains:
        # A1 > B1, B2 > C2, B2 > A3 > B3
        builder.reset()
        builder._tie(method, 0.2, acistr('A1'), 0.3, acistr('B1'), 0.1) # push B1+ down 0.2
        builder._tie(method, 0.2, acistr('B2'), 1.1, acistr('C2'), 1.1) # push C2+ down 0.2
        builder._tie(method, 0.2, acistr('B2'), 2.0, acistr('A3'), 2.0) # push A3+ down 0.2
        builder._tie(method, 0.2, acistr('A3'), 2.4, acistr('B3'), 2.2) # push B3+ down 0.2 for total shift of 0.4
        
        # again, shift B1 - now nothing should move
        movers = builder.gatherRelatedCores(acistr('A1'), acistr('B1'))
        expectedMovers = acilist([])
        self.assertTrue(sameElements(expectedMovers, movers))
        
        # shift B2 - should move B2+, A3+, C2+
        movers = builder.gatherRelatedCores(acistr('A2'), acistr('B2'))
        expectedMovers = acilist(['A3', 'A4', 'A5', 'B3', 'B4', 'B5', 'C2', 'C3', 'C4', 'C5'])
        self.assertTrue(sameElements(expectedMovers, movers))

        # Note that depths in the tests below are odd, but we're concerned
        # only with chaining logic, which is unaffected by depth.

        # B2 > A2 tie exists. New tie from A1 > B1 shifts only B1 because
        # B2 > A2 is a separate chain.
        builder.reset()
        builder._tie(method, 0.1, acistr('B2'), 0.9, acistr('A2'), 0.8) # wrong depths
        movers = builder.gatherRelatedCores(acistr('A1'), acistr('B1'))
        self.assertTrue(sameElements([], movers))

        # B3 > A3 tie exists. New tie from A1 > B1 shifts only B2 because
        # it's non-chain, but doesn't shift A3+ and B3+ due to the distinct
        # B3 > A3 chain.
        builder.reset()
        builder._tie(method, 0.1, acistr('B3'), 0.9, acistr('A3'), 0.8)
        movers = builder.gatherRelatedCores(acistr('A1'), acistr('B1'))
        expectedMovers = acilist(['B2'])
        self.assertTrue(sameElements(expectedMovers, movers))

        # B1 > C1, C2 > A2.
        # New tie from A1 > B1 shifts C1 (chain) and B2+ (non-chain)
        # below moving B1, but doesn't shift A2+ and C2+  due to distinct
        # C2 > A2 chain.
        builder.reset()
        builder._tie(method, 0.1, acistr('B1'), 0.9, acistr('C1'), 0.8)
        builder._tie(method, 0.1, acistr('C2'), 0.9, acistr('A2'), 0.8)
        movers = builder.gatherRelatedCores(acistr('A1'), acistr('B1'))
        expectedMovers = acilist(['B2', 'B3', 'B4', 'B5', 'C1'])
        self.assertTrue(sameElements(expectedMovers, movers))

        # Complex scenario from Peter
        builder = AffineBuilder.createWithAffineFile("testdata/FOO_affine_scenario6.csv", secsumm)
        movers = builder.gatherRelatedCores(acistr('B1'), acistr('C2')) # retie B1 > C2
        expectedMovers = acilist(['A3', 'A4', 'A5', 'B3', 'B4', 'B5', 'C3', 'C4', 'C5'])
        self.assertTrue(sameElements(expectedMovers, movers))

        # Variant of the above scenario - only difference is that C3 is part of a separate
        # chain and should not be moved
        builder = AffineBuilder.createWithAffineFile("testdata/FOO_affine_scenario6b.csv", secsumm)
        movers = builder.gatherRelatedCores(acistr('B1'), acistr('C2')) # retie B1 > C2
        expectedMovers = acilist(['A3', 'A4', 'A5', 'B3', 'B4', 'B5', 'C4', 'C5'])
        self.assertTrue(sameElements(expectedMovers, movers))

        # B1 > C1.
        # New tie from C2 > B1 shifts B1 and C1, but *cannot* shift C2
        # or anything below it since it's the fixed core.
        builder.reset()
        builder._tie(method, 0.1, acistr('B1'), 0.9, acistr('C1'), 0.8)
        movers = builder.gatherRelatedCores(acistr('C2'), acistr('B1'))
        expectedMovers = acilist(['B2', 'B3', 'B4', 'B5', 'C1'])
        self.assertTrue(sameElements(expectedMovers, movers))

    def test_core_and_all_below(self):
        secsumm = sectionSummary.SectionSummary.createWithFile("testdata/FOO_SectionSummary.csv")
        builder = AffineBuilder.createWithSectionSummary(secsumm)
        method = TieShiftMethod.CoreAndAllBelow

        # no existing ties, tie from A1 > B1 shifts B1 and below
        movers = builder.gatherAllCoresBelow(acistr('A1'), acistr('B1'))
        self.assertTrue(sameElements(builder.getCoresBelow(acistr('B1')), movers))

        # Create B1 > A2 tie.
        builder._tie(method, 0.1, acistr('B1'), 0.9, acistr('A2'), 0.8)
        # New tie from A1 > B1 shifts A2+, B1+
        movers = builder.gatherAllCoresBelow(acistr('A1'), acistr('B1'))
        expectedMovers = acilist(['A2', 'A3', 'A4', 'A5', 'B2', 'B3', 'B4', 'B5'])
        self.assertTrue(sameElements(expectedMovers, movers))

        ### BEGIN other old tests

        # add tie between B3 and C3
        # ties: A1 > B1 > A2, B3 > C3
        movers = builder.gatherAllCoresBelow(acistr('B3'), acistr('C3'))
        self.assertTrue(sameElements(builder.getCoresBelow(acistr('C3')), movers))
        builder._tie(method, 0.2, acistr('B3'), 0.3, acistr('C3'), 0.1)
        
        # now determine cores shifted by B1 and below
        movers = builder.gatherAllCoresBelow(acistr('A1'), acistr('B1'))
        expectedMovers = acilist(['A2', 'A3', 'A4', 'A5', 'B2', 'B3', 'B4', 'B5', 'C3', 'C4', 'C5'])
        self.assertTrue(sameElements(expectedMovers, movers))
        
        # or C1 and below
        movers = builder.gatherAllCoresBelow(acistr('A1'), acistr('C1'))
        expectedMovers = acilist(['B3', 'B4', 'B5', 'C2', 'C3', 'C4', 'C5'])
        self.assertTrue(sameElements(expectedMovers, movers))

        # or C2 and below
        movers = builder.gatherAllCoresBelow(acistr('A1'), acistr('C2'))
        expectedMovers = acilist(['B3', 'B4', 'B5', 'C3', 'C4', 'C5'])
        self.assertTrue(sameElements(expectedMovers, movers))


    def test_find_breaks(self):
        secsumm = sectionSummary.SectionSummary.createWithFile("testdata/FOO_SectionSummary.csv")
        builder = AffineBuilder.createWithSectionSummary(secsumm)
        method = TieShiftMethod.CoreOnly

        a1, a2, b1, b2, c1, c2 = acistr('A1'), acistr('A2'), acistr('B1'), acistr('B2'), acistr('C1'), acistr('C2')

        # no existing ties, nothing should break
        breaks = builder.findBreaksForSET([a1, a2, b1, b2, c1, c2])
        self.assertTrue(breaks == [])

        builder._tie(method, 0.1, a1, 0.1, b1, 0.0)
        builder._tie(method, 0.1, b1, 0.1, c1, 0.0)
        breaks = builder.findBreaksForSET([a1])
        self.assertTrue(breaks == [(a1, b1)])
        breaks = builder.findBreaksForSET([b1])
        self.assertTrue(sameElements(breaks, [(a1, b1), (b1, c1)]))
        breaks = builder.findBreaksForSET([c1])
        self.assertTrue(sameElements(breaks, [(b1, c1)]))

        # re-tying A1 > B1 is not considered a break
        breaks = builder.findBreaks(a1, b1, [c1])
        self.assertTrue(breaks == [])

        # if we TIE A1 > B1 only, C1 doesn't move, thus we expect a B1 > C1 break
        breaks = builder.findBreaks(a1, b1)
        self.assertTrue(breaks == [(b1, c1)])

   

if __name__ == "__main__":
    for testcase in [TestAffineUtils, TestAffineTable, TestAffineBuilder, TestNewAffineScopes]:
        suite = unittest.TestLoader().loadTestsFromTestCase(testcase)
        unittest.TextTestRunner(verbosity=2).run(suite)