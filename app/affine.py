'''
Created on Feb 22, 2017

@author: bgrivna

Support for the creation and editing of Affine Shifts and resulting tables.
'''

import re # to parse combined hole/core strings
import unittest
import numpy

class AffineError(Exception):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message

class AffineShift:
    def __init__(self, core, distance, comment=""):
        self.core = core # CoreInfo (or AffineCoreInfo) for the shifted core
        self.distance = distance # shift distance (can be 0)
        self.comment = comment # user comment
        
    # adjust current shift by deltaDistance
    def adjust(self, deltaDistance):
        self.distance += deltaDistance

# An affine shift resulting from the shift of another core that "pushes" or "pulls"
# all cores below and/or related cores to maintain spacing of cores. Because the user
# didn't explicitly shift this core, it isn't a TIE or a SET, but a "convenience" shift
# that maintains relative positions between cores in a hole. Ultimately, such
# shifts will usually be replaced with a TIE or SET as they're integrated into
# the CCSF-A/MCD depth scale.
class ImplicitShift(AffineShift):
    def __init__(self, core, distance, comment=""):
        AffineShift.__init__(self, core, distance, comment)
    
    def __repr__(self):
        commentStr = " ({})".format(self.comment) if self.comment != "" else ""
        return "Implicit shift of {} by {}m{}".format(self.core, self.distance, commentStr)
    

class TieShift(AffineShift):
    def __init__(self, fromCore, fromDepth, core, depth, distance, comment=""):
        AffineShift.__init__(self, core, distance, comment)
        self.fromCore = fromCore # CoreInfo for core to which self.core was tied
        self.fromDepth = fromDepth # MBSF depth of "from" core's TIE point
        self.depth = depth # MBSF depth of shifted core's TIE point

    def __repr__(self):
        fmtStr = "TIE from {}@{}mbsf to {}@{}mbsf ({}mcd), shifted {}m{}" 
        commentStr = " ({})".format(self.comment) if self.comment != "" else ""
        return fmtStr.format(self.fromCore, self.fromDepth, self.core, self.depth, self.depth + self.distance, self.distance, commentStr)


class SetShift(AffineShift):
    def __init__(self, core, distance, comment=""):
        AffineShift.__init__(self, core, distance, comment)

    def __repr__(self):
        commentStr = " ({})".format(self.comment) if self.comment != "" else ""
        return "SET: {} shifted {}m{}".format(self.core, self.distance, commentStr)
    
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

    def __repr__(self):
        superstr = "AffineTable: {} shifts\n".format(len(self.shifts))
        for index, shift in enumerate(self.shifts):
            superstr += "  {}: {}\n".format(index, shift)
        return superstr
        
    def clear(self):
        self.shifts = []
        
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
        print "replacing {} with {}".format(oldShift, newShift)
        self._delete(oldShift)
        self._add(newShift)
        
    # modify existing shift by deltaDistance
    def adjust(self, core, deltaDistance):
        self.getShift(core).adjust(deltaDistance)
    
    def getShift(self, core):
        shifts = [s for s in self.shifts if s.core == core]
        assert len(shifts) <= 1
        return shifts[0] if len(shifts) == 1 else None
    
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
        
    def __repr__(self):
        return str(self.affine)
        
    def clear(self):
        self.affine.clear()
        
    # modify existing shift by deltaDistance
    def adjust(self, core, deltaDistance):
        self.affine.getShift(core).adjust(deltaDistance)
     
    # shift core(s) by a given distance (SET) 
    def set(self, coreOnly, core, distance, comment=""):
        if coreOnly:
            self.affine.addShift(SetShift(core, distance, comment))
        else: # consider related
            fromCore = aci('Z', '666') # bogus core to ensure nothing matches
            shift = self.affine.getShift(core)
            deltaDistance = distance - shift.distance
            relatedCores = self.gatherRelatedCores(core, fromCore)
            self.affine.addShift(SetShift(core, distance, comment))
            for ci in relatedCores:
                self.affine.adjust(ci, deltaDistance)            

    # shift core(s) based on a tie between two cores
    # coreOnly - if True, shift core only, else shift core and all related
    # mcdShiftDistance - distance between tie points in MCD space
    # fromCore, fromDepth - core and MBSF depth of tie on fixed core
    # core, depth - core and MBSF depth of tie on core to be shifted
    # comment - user comment/annotation of shift
    def tie(self, coreOnly, mcdShiftDistance, fromCore, fromDepth, core, depth, comment=""):
        totalShiftDistance = self.affine.getShiftDistance(core) + mcdShiftDistance
        if coreOnly:
            self.affine.addShift(TieShift(fromCore, fromDepth, core, depth, totalShiftDistance, comment))
            # need to update any shifts for which this is a from core to be SetShifts...right? Or Implicit?
        else:
            relatedCores = self.gatherRelatedCores(core, fromCore)
            self.affine.addShift(TieShift(fromCore, fromDepth, core, depth, totalShiftDistance, comment))
            for ci in relatedCores:
                self.affine.adjust(ci, mcdShiftDistance)
        
    # will shifting core have side effects that require user confirmation to proceed?
    # returns tuple of form (confirmation needed [boolean], warning message [string])
    def needConfirmation(self, fromCore, core, coreOnly):
        if coreOnly:
            shift = self.affine.getShift(core)
            if self.affine.inChain(core):
                #print "old fromCore = {}, new = {}".format(shift.fromCore, fromCore)
                if isTie(shift) and shift.fromCore != fromCore or self.affine.isChainTop(core):
            #if self.affine.inChain(core):
                    return True, "Shifting core {} only will break a TIE chain.".format(core)
        else:
            pass

        return False, ""
    
    # gather all cores that will be shifted by "Shift by [shiftCore] and related cores below" action
    # this only makes sense to use for TIE operations.
    def gatherRelatedCores(self, shiftCore, fromCore):
        topChainCores = {shiftCore.hole: shiftCore} # for each hole encountered (key), track topmost chain core (value)
        chainCores = []
        done = False
        curCore = shiftCore
        while not done:
            topCore = self._gatherHoleChainCores(curCore, fromCore, chainCores)
            
            # update topChainCores for current hole if needed
            if topCore is not None:
                if curCore.hole not in topChainCores or topCore.core < topChainCores[curCore.hole].core:
                    topChainCores[curCore.hole] = topCore
                    
            # find a core in chainCores with hole != curCore.hole that's above the current topChainCores
            # value for that hole, if any, and make it the new curCore
            offHoleCores = [c for c in chainCores if c.hole != curCore.hole and c != fromCore]
            offHoles = set(c.hole for c in offHoleCores)
            for hole in offHoles:
                topOffHoleCore = self._topCoreInHole(hole, offHoleCores)
                if topOffHoleCore is not None:
                    if hole not in topChainCores or topOffHoleCore.core < topChainCores[hole].core:
                        topChainCores[hole] = topOffHoleCore
                        curCore = topOffHoleCore
                        break
            else: # otherwise, we're done!
                done = True
                
        # All related chain cores have been gathered. Now gather all non-chain
        # cores below the topmost chain core in each hole.
        nonChainCores = []
        for hole, ci in topChainCores.items():
#             print "searching hole {} for non-chain cores below {}...".format(hole, ci.core)
#             nccBelow = []
#             for shift in self.affine.shifts:
#                 print "trying core {}".format(shift.core)
#                 if shift.core.hole == ci.hole:
#                     print "hole {} match".format(ci.hole)
#                     if int(shift.core.core) > int(ci.core):
#                         print "core {} is greater".format(int(shift.core.core))
#                         if not self.affine.inChain(shift.core):
#                             print "not in chain - adding!"
#                             nccBelow.append(shift.core)
            nccBelow = [core for core in self.getCoresInHole(ci.hole) if int(core.core) > int(ci.core) and not self.affine.inChain(core)]
            nonChainCores.extend(nccBelow)
        
        relatedCores = chainCores + nonChainCores
        
        # remove shiftCore from relatedCores!
        relatedCores = [c for c in relatedCores if c != shiftCore]
        
        # remove any cores above shiftCore!
        shiftCoreTop = self._getCoreTop(shiftCore) + self.getShift(shiftCore).distance
        relatedCores = [c for c in relatedCores if self._getCoreTop(c) + self.getShift(c).distance >= shiftCoreTop]
        return relatedCores
        
    # search core and below for chain cores - add all to chainCores list
    def _gatherHoleChainCores(self, core, fromCore, chainCores):
        foundCores = []
        for c in [core] + self.getCoresBelow(core):
            if c not in chainCores and self.affine.inChain(c):
                newChainCores = [nc for nc in self.affine.getChainCores(c) if nc != fromCore]
                foundCores.extend(newChainCores)
                chainCores.extend(foundCores)
        
        return self._topCoreInHole(core.hole, foundCores)
        
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
        
    def coreHasShift(self, core):
        return self.getShift(core) is not None
    
    def getShift(self, core):
        #print "core type = {}, hole type = {}".format(type(core.core), type(core.hole))
        return self.affine.getShift(core)
    
    def isTie(self, core):
        return isTie(self.getShift(core))
    

# Reference to hole and core for affine shifts
class AffineCoreInfo:
    def __init__(self, hole, core):
        assert isinstance(hole, str)
        assert isinstance(core, str)
        self.hole = hole
        self.core = core
        
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


# malformed hole core string
class InvalidHoleCoreStringError(AffineError):
    def __init__(self, expression, message):
        AffineError.__init__(self, expression, message)

def assertElementsInList(elements, listToSearch):
    allFound = True
    for elt in elements:
        if elt not in listToSearch:
            allFound = False
            break
    return allFound

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
        
        # AffineBuilder tests
        ab = AffineBuilder()
        ab.affine = affine

        # D3 isn't in a chain and there's nothing below it, thus no related cores
        relCores = ab.gatherRelatedCores(d3)
        self.assertTrue(relCores == [])
        
        # chain 1 should gather only itself
        relCores = ab.gatherRelatedCores(a1)
        self.assertTrue(len(relCores) == 5)
        self.assertTrue(assertElementsInList([a1, a2, b1, b2, c2], relCores))
        
        # chain 2 should gather itself *and* all chain 1 elements *and* D3 because it's
        # a non-chain core below chain elements
        relCores = ab.gatherRelatedCores(d1)
        self.assertTrue(len(relCores) == 9)
        self.assertTrue(assertElementsInList([a1, a2, b1, b2, c1, c2, d1, d2, d3], relCores))

class TestAffine(unittest.TestCase):
    # use numpy.isclose to deal with tiny floating point discrepancies causing == to return False 
    def assertClose(self, fp1, fp2):
        return self.assertTrue(numpy.isclose(fp1, fp2))
    
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


if __name__ == "__main__":
    #suite = unittest.TestLoader().loadTestsFromTestCase(TestAffineTable)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAffine)
    unittest.TextTestRunner(verbosity=2).run(suite)
    #unittest.main()
