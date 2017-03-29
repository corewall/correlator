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
    def __init__(self):
        pass

# An affine shift resulting from the shift of another core that "pushes" or "pulls"
# all cores below and/or related cores to maintain spacing of cores. Because the user
# didn't explicitly shift this core, it isn't a TIE or a SET, but a "convenience" shift
# that maintains relative positions between cores in a hole. Ultimately, such
# shifts will usually be replaced with a TIE or SET as they're integrated into
# the CCSF-A/MCD depth scale.
class ImplicitShift(AffineShift):
    def __init__(self, core, distance, comment=""):
        AffineShift.__init__(self)
        self.core = core
        self.distance = distance
        self.comment = comment
    
    def __repr__(self):
        commentStr = "({})".format(self.comment) if self.comment != "" else ""
        return "Implicit shift of {} by {}m {}".format(self.core, self.distance, commentStr)
    

class TieShift(AffineShift):
    def __init__(self, fromCore, fromDepth, core, depth, distance, comment=""):
        AffineShift.__init__(self)
        self.fromCore = fromCore # core to which self.core was tied
        self.fromDepth = fromDepth # MBSF depth of "from" core's TIE point
        self.core = core # CoreInfo for shifted core
        self.depth = depth # MBSF depth of shifted core's TIE point
        self.distance = distance # distance of shift: distance + depth = MCD
        self.comment = comment

    def __repr__(self):
        fmtStr = "TIE from {}@{}mcd to {}@{}mcd ({}mbsf), shifted {}m {}" 
        commentStr = "({})".format(self.comment) if self.comment != "" else ""
        return fmtStr.format(self.fromCore, self.fromDepth, self.core, self.depth, self.depth - self.distance, self.distance, commentStr)


class SetShift(AffineShift):
    def __init__(self, core, distance, comment=""):
        AffineShift.__init__(self)
        self.core = core # CoreInfo for shifted core
        self.distance = distance # distance of shift: distance + depth = MCD
        self.comment = comment

    def __repr__(self):
        commentStr = "({})".format(self.comment) if self.comment != "" else ""
        return "SET: {} shifted {}m {}".format(self.core, self.distance, commentStr)
    
def isTie(shift):
    return isinstance(shift, TieShift)

def isSet(shift):
    return isinstance(shift, SetShift)

def isImplicit(shift):
    return isinstance(shift, ImplicitShift)

class UnknownCoreError(AffineError):
    def __init__(self, expression, message):
        AffineError.__init__(self, expression, message)

class AffineBuilder:
    def __init__(self):
        self.shifts = [] # list of TieShifts and SetShifts representing the current affine state
        
    def __repr__(self):
        superstr = "AffineBuilder: {} shifts\n".format(len(self.shifts))
        for index, shift in enumerate(self.shifts):
            superstr += "  {}: {}\n".format(index, shift)
        return superstr
        
    def clear(self):
        self.shifts = []
        
    # add implicit shift
    def addImplicit(self, core, distance, comment=""):
        self.shifts.append(ImplicitShift(core, distance, comment))
        
    # modify existing shift by deltaDistance
    def adjust(self, core, deltaDistance):
        self.getShift(core).distance += deltaDistance
     
    # shift a single core by a given distance (SET) 
    def set(self, core, distance, comment=""):
        deltaDist = distance
        if not self.coreHasShift(core):
            ss = SetShift(core, distance, comment)
            self.add(ss)
        else:
            shift = self.getShift(core)
            if isSet(shift):
                deltaDist = distance - shift.distance
                shift.distance = distance
                print "core already has shift {}, adjusting by {} to {}".format(shift, deltaDist, distance)
            else: # it's a TIE - probably want to confirm with user? wilBreakTie() method?
                print "No can do, brah! SET will break existing shift {} and that would be weird.\nTODO: Confirmation dialog.".format(shift)
                return
        # update TIE chain, since the shifted core may be the fromCore of a chain
        # at present this would only apply to the topmost core in a chain since there's
        # no notion of SET-chaining right now (though that may be desired going forward)
        self.updateTieChain(core, deltaDist)
    
    # hmmm better to just have set() at this level and let Controller issue individual set() calls?
    def setBelow(self, core, distance, comment=""):
        pass
            
    def tie(self, fromCore, fromDepth, core, depth, comment=""):
        deltaDist = fromDepth - depth
        if not self.coreHasShift(core):
            #raise UnknownCoreError(core, "Core {} not found in AffineBuilder.shifts")
            ts = TieShift(fromCore, fromDepth, core, depth, deltaDist, comment)
            self.add(ts)
        else: # core already has a shift...should always get here!
            oldShift = self.getShift(core)
            #if isinstance(oldShift, SetShift): # if it's a SET, override it entirely
            if isSet(oldShift) or isImplicit(oldShift):
                ts = TieShift(fromCore, fromDepth, core, depth, deltaDist, comment)
                self.replace(oldShift, ts)
            else: # it's a TIE, the new shift distance is the old shift distance plus fromDepth - depth
                newDist = deltaDist + oldShift.distance
                print "   current TIE shift {} + new shift {} = cumulative shift {}".format(oldShift.distance, deltaDist, newDist)
                ts = TieShift(fromCore, fromDepth, core, depth - oldShift.distance, newDist, comment)
                self.replace(oldShift, ts)
                

        # update TieShifts that descend from the core we just shifted     
        self.updateTieChain(core, deltaDist)
        # return new TieShift?
        
    # return list of cores that will be moved if shiftCore moves, either due to TIE
    # relationships or cores below being "pushed", which could affect other TIE relationships
    def gatherAffectedCores(self, shiftCore):
        # first, consider case with no ties, just cores below
        
        pass
    
    # get all cores in hole below core by name - not actual position!
    # todo: abstract concept of "below"?
    # todo: this really shouldn't be part of AffineBuilder, should be done
    # through SectionSummary so we can deal with holes/cores directly instead
    # of cracking open Shifts to get at hole/core names. Or at least at
    # AffineController level where there's a notion of SectionSummary.
    # But for now...and therefore forever...
    def getCoresBelow(self, hole, core):
        cb = [shift.core for shift in self.shifts if shift.core.hole == hole and int(shift.core.core) > int(core)]
        return cb
    
    def isLegalTie(self, fromCore, core):
        return not self.isUpstream(fromCore, core)
    
    # is searchCore the fromCore for anything upstream?
    def isUpstream(self, searchCore, curCore):
        curShift = self.getShift(curCore)
        if not isTie(curShift):
            return False
        elif curShift.fromCore == searchCore:
            return True
        else:
            return self.isUpstream(searchCore, curShift.fromCore)
        
    # returns True if searchCore is the top of a chain or chains
    def isChainTop(self, searchCore):
        tiedChainTop = self.countChildren(searchCore) > 1 and isTie(self.getShift(searchCore))
        return tiedChainTop or (self.countChildren(searchCore) > 0 and not isTie(self.getShift(searchCore)))
        
    # is searchCore part of a TIE chain?
    def inChain(self, searchCore):
        shift = self.getShift(searchCore)
        return isTie(shift) or self.isChainTop(searchCore)
    
    # get immediate descendants of searchCore
    def getChildren(self, searchCore):
        return [shift for shift in self.shifts if isTie(shift) and shift.fromCore == searchCore]
    
    # count immediate descendants of searchCore
    def countChildren(self, searchCore):
        return len(self.getChildren(searchCore)) 
    
    def updateTieChain(self, core, deltaDist):
        for shift in [s for s in self.shifts if isTie(s) and s.fromCore == core]:
            shift.distance += deltaDist
            print "{} has parent {}, shifting by {} for a total shift of {}".format(shift.core, shift.fromCore, deltaDist, shift.distance)
            self.updateTieChain(shift.core, deltaDist) # recurse
            
    def printChain(self, core, count=0):
        shift = self.getShift(core)
        if shift is not None and isTie(shift):
            self.printChain(shift.fromCore, count + 1)
        endstr = ".\n" if count == 0 else " ->"
        print "{}{}".format(core, endstr),
            
    def add(self, shift):
        print "adding {}".format(shift)
        self.shifts.append(shift)
    
    def delete(self, shift):
        assert shift in self.shifts
        print "deleting {}".format(shift)
        self.shifts.remove(shift)
        
    def replace(self, oldShift, newShift):
        self.delete(oldShift)
        self.add(newShift)
        
    def coreHasShift(self, core):
        return self.getShift(core) is not None
    
    def getShift(self, core):
        shifts = [s for s in self.shifts if s.core == core]
        assert len(shifts) <= 1
        return shifts[0] if len(shifts) == 1 else None
    
    # don't think we need it and how do we handle case where there is no shift?
#     def getShiftDistance(self, core):
#         shift = self.getShift(core)
#         return shift.distance if shift is not None else 0.0


# Reference to hole and core for affine shifts
class AffineCoreInfo:
    def __init__(self, hole, core):
        self.hole = hole
        self.core = core
        
    def GetHoleCoreStr(self):
        return "{}{}".format(self.hole, self.core)
    
    def __repr__(self):
        return self.GetHoleCoreStr()
    
    def __eq__(self, other):
        return self.hole == other.hole and self.core == other.core

# convenience method to create AffineCoreInfo
def aci(hole, core):
    return AffineCoreInfo(hole, core)


class InvalidHoleCoreStringError(AffineError):
    def __init__(self, expression, message):
        AffineError.__init__(self, expression, message)

# create AffineCoreInfo from string of form "[hole][core]"
def acistr(holeCoreStr):
    charNumPattern = "([A-Z]+)([0-9]+)"
    hc_items = re.match(charNumPattern, holeCoreStr)
    if hc_items and len(hc_items.groups()) == 2:
        hole = hc_items.groups()[0]
        core = hc_items.groups()[1]
        return AffineCoreInfo(hole, core)
    raise InvalidHoleCoreStringError(holeCoreStr, "Cannot be parsed into an alphabetic hole and numeric core")



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
        
        # physically ridiculous but logically valid case (AZ == 51st hole)
        aci3 = acistr("AZ69743")
        self.assertTrue(aci3.hole == 'AZ')
        self.assertTrue(aci3.core == '69743')
        
        # invalid string
        self.assertRaises(InvalidHoleCoreStringError, acistr, "1F")
    
    def test_mci_eq(self):
        c1 = aci('A', '1')
        c1dup = aci('A', '1')
        self.assertTrue(c1 == c1dup)
    
    def test_set_shift(self):
        c1 = aci('A', '1')
        ss = SetShift(c1, 1.0)
        self.assertTrue(isSet(ss))
        self.assertTrue(ss.distance == 1.0)
        
    def test_tie_shift(self):
        a1 = aci('A', '1')
        b1 = aci('B', '1')
        ts = TieShift(a1, 0.5, b1, 0.25, 0.25)
        self.assertTrue(isTie(ts))
        self.assertTrue(ts.distance == 0.25)

    def test_inChain(self):
        a1 = aci('A', '1')
        a2 = aci('A', '2')
        b1 = aci('B', '1')
        b2 = aci('B', '2')
        c2 = aci('C', '2')
        ab = AffineBuilder()
        ab.tie(a1, 2.0, b1, 1.0)
        ab.tie(b1, 2.5, c2, 1.0)
        ab.tie(c2, 3.0, b2, 1.0)
        ab.tie(b1, 2.8, a2, 2.0)
        
        self.assertTrue(ab.inChain(a1))
        self.assertTrue(ab.inChain(a2))
        self.assertTrue(ab.inChain(b1))
        self.assertTrue(ab.inChain(b2))
        self.assertTrue(ab.inChain(c2))
        
    def test_isChainTop(self):
        a1 = aci('A', '1')
        a2 = aci('A', '2')
        b1 = aci('B', '1')
        b2 = aci('B', '2')
        c2 = aci('C', '2')
        ab = AffineBuilder()
        ab.tie(a1, 2.0, b1, 1.0)
        ab.tie(b1, 2.5, c2, 1.0)
        ab.tie(c2, 3.0, b2, 1.0)
        ab.tie(b1, 2.8, a2, 2.0)
        
        # A1 is chain top but is not a TIE
        self.assertTrue(ab.isChainTop(a1))
        
        # B1 is a chain top that is a TIE
        self.assertTrue(ab.isChainTop(b1))

        # all others are not chain tops        
        self.assertFalse(ab.isChainTop(b2))
        self.assertFalse(ab.isChainTop(c2))
        self.assertFalse(ab.isChainTop(a2))

    def test_countChildren(self):
        a1 = aci('A', '1')
        a2 = aci('A', '2')
        b1 = aci('B', '1')
        b2 = aci('B', '2')
        c2 = aci('C', '2')
        ab = AffineBuilder()
        ab.tie(a1, 2.0, b1, 1.0)
        ab.tie(b1, 2.5, c2, 1.0)
        ab.tie(c2, 3.0, b2, 1.0)
        ab.tie(b1, 2.8, a2, 2.0)
        
        self.assertTrue(ab.countChildren(b1) == 2) # A2, C2
        self.assertTrue(ab.countChildren(a1) == 1) # B1
        self.assertTrue(ab.countChildren(c2) == 1) # B2
        self.assertTrue(ab.countChildren(b2) == 0)
        
    def test_getCoresBelow(self):
        # mock up some holes 'n cores
        mockAci = []
        for hole in ['A', 'B', 'C', 'D']:
            for core in range(10):
                mockAci.append(acistr(hole + str(core + 1)))
        
        # add implicit shift for each mock core
        ab = AffineBuilder()
        for maci in mockAci:
            ab.addImplicit(maci, 0.0, 'mock core')
            
        self.assertTrue(ab.getCoresBelow('A', '10') == [])
        coresBelow = ab.getCoresBelow('A', '8')
        self.assertFalse(acistr('A8') in coresBelow)
        self.assertTrue(acistr('A9') in coresBelow)
        self.assertTrue(acistr('A10') in coresBelow)
        
        bcores = ab.getCoresBelow('B', '2')
        bcbs = [core for core in [acistr(hc) for hc in ['B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9', 'B10']] if core in bcores]
        self.assertTrue(len(bcbs) == 8)
        
        # OK! Now hook up basic case of TIE and all related, SET and all related
        
        
    def test_builder(self):
        a1 = aci('A', '1')
        b1 = aci('B', '1')
        c1 = aci('C', '1')
        d1 = aci('D', '1')
        ab = AffineBuilder()
        ab.tie(a1, 0.5, b1, 0.25)
        self.assertTrue(ab.coreHasShift(b1))
        self.assertTrue(ab.getShift(b1).distance == 0.25)
        self.assertFalse(ab.coreHasShift(a1))
          
        ab.tie(b1, 1.0, c1, 0.5)
        self.assertTrue(ab.coreHasShift(c1))
        self.assertTrue(ab.getShift(c1).distance == 0.5)
          
        # push a1 down by 0.2 - ensure b1 and c1 are pushed by same distance
        ab.tie(d1, 0.5, a1, 0.3)
        self.assertTrue(ab.coreHasShift(a1))
        self.assertTrue(ab.getShift(a1).distance == 0.2)
        self.assertTrue(ab.getShift(b1).distance == 0.45)
        self.assertTrue(ab.getShift(c1).distance == 0.7)
           
        # chain 1: d1 -> a1 -> b1 -> c1
        self.assertTrue(ab.isUpstream(b1, c1))
        self.assertTrue(ab.isUpstream(a1, c1))
        self.assertTrue(ab.isUpstream(a1, b1))
        self.assertTrue(ab.isUpstream(d1, a1))
        self.assertFalse(ab.isUpstream(b1, a1))
           
        # build a separate chain and test upstream-ness
        # chain 2: a2 -> b2 -> c2 -> d2
        a2 = aci('A', '2')
        b2 = aci('B', '2')
        c2 = aci('C', '2')
        d2 = aci('D', '2')
        ab.tie(a2, 0.8, b2, 1.0)
        self.assertClose(-0.2, ab.getShift(b2).distance)
        ab.tie(b2, 1.5, c2, 1.4)
        self.assertClose(0.1, ab.getShift(c2).distance)
        ab.tie(c2, 1.7, d2, 2.0)
        self.assertClose(-0.3, ab.getShift(d2).distance)
           
        self.assertTrue(ab.isUpstream(a2, b2))
        self.assertTrue(ab.isUpstream(b2, c2))
        self.assertTrue(ab.isUpstream(c2, d2))
        self.assertTrue(ab.isUpstream(a2, d2))
           
        # chains 1 and 2 are separate
        self.assertFalse(ab.isUpstream(a1, b2))
           
        # join those chains and test new upstream-ness state
        self.assertFalse(ab.isUpstream(c1, d2))
        ab.tie(c1, 1.0, a2, 0.5)
        self.assertTrue(ab.isUpstream(c1, d2))
        
    def test_tie_override_of_set(self):        
        # confirm TIE overrides SET
        a1 = aci('A', '1')
        b1 = aci('B', '1')
        ab = AffineBuilder()
        ab.set(a1, 1.0)
        ab.tie(b1, 1.0, a1, 1.5)
        shift = ab.getShift(a1)
        self.assertTrue(isTie(shift))
        self.assertClose(shift.distance, -0.5)
        
    # confirm new TIE correctly replaces existing TIE        
    def test_tie_override_of_tie(self):
        # initial TIE
        a1 = aci('A', '1')
        b1 = aci('B', '1')
        ab = AffineBuilder()
        ab.tie(b1, 1.0, a1, 1.5)
        shift = ab.getShift(a1)
        self.assertClose(shift.fromDepth, 1.0)
        self.assertClose(shift.depth, 1.5)
        self.assertClose(shift.distance, -0.5)
        
        # replace TIE with same fromCore at different depth. Current
        # TIE shifts A1 by -0.5m
        ab.tie(b1, 1.2, a1, 1.5) # A1 1.5mcd = 2.0mbsf due to current shift
        shift = ab.getShift(a1)
        self.assertTrue(isTie(shift))
        self.assertClose(shift.fromDepth, 1.2)
        self.assertClose(shift.depth, 2.0)
        self.assertClose(shift.distance, -0.8) # shifted a further -0.3m + current -0.5m
        
    # confirm a SET can be the top of a TIE chain
    def test_set_to_tie_chain(self):
        a1 = aci('A', '1')
        b1 = aci('B', '1')
        ab = AffineBuilder()
        ab.set(a1, 1.0)
        ab.tie(a1, 1.5, b1, 1.0)
        self.assertTrue(ab.getShift(b1).fromCore == a1)
        
        c1 = aci('C', '1')
        ab.tie(b1, 2.0, c1, 1.0)
        self.assertClose(ab.getShift(c1).distance, 1.0)
        
        # chain: a1 -> b1 -> c1
        #ab.printChain(c1)
        
        # does adjusting a1 push chain as expected?
        ab.set(a1, 2.0)
        self.assertTrue(ab.isUpstream(a1, c1))
        self.assertClose(ab.getShift(b1).distance, 1.5)
        self.assertClose(ab.getShift(c1).distance, 2.0)

if __name__ == "__main__":
    unittest.main()
