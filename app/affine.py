'''
Created on Feb 22, 2017

@author: bgrivna

Support for the creation and editing of Affine Shifts and resulting tables.
'''

class AffineShift:  
    def __init__(self):
        pass

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
        fmtStr = "TIE from {}@{}mcd to {}@{}mcd ({}mbsf), shifted {}{}" 
        commentStr = "({})".format(self.comment) if self.comment != "" else ""
        return fmtStr.format(self.fromCore, self.fromDepth, self.core, self.depth, self.depth - self.distance, self.distance, commentStr)


class SetShift(AffineShift):
    def __init__(self, core, distance, comment=""):
        AffineShift.__init__(self)
        self.core = core # CoreInfo for shifted core
        self.distance = distance # distance of shift: distance + depth = MCD
        self.comment = comment

    def __repr__(self):
        commentStr = "{}".format(self.comment) if self.comment != "" else ""
        return "SET: {} shifted {}m ({})".format(self.core.GetHoleCoreStr(), self.distance, commentStr)
    
def isTie(shift):
    return isinstance(shift, TieShift)

def isSet(shift):
    return isinstance(shift, SetShift)


class AffineBuilder:
    def __init__(self, shifts=[]):
        self.shifts = shifts # list of TieShifts and SetShifts representing the current affine state
     
    def set(self, core, distance, comment=""):
        if not self.coreHasShift(core):
            ss = SetShift(core, distance, comment)
            self.add(ss)
            #print "added shift {}".format(ss)
        else:
            print "core already has shift {}".format(self.getShift(core))
            
    def tie(self, fromCore, fromDepth, core, depth, comment=""):
        deltaDist = fromDepth - depth
        if not self.coreHasShift(core):
            ts = TieShift(fromCore, fromDepth, core, depth, deltaDist, comment)
            self.add(ts)
        else: # core already has a shift...
            oldShift = self.getShift(core)
            if isinstance(oldShift, SetShift): # if it's a SET, override it entirely
                ts = TieShift(core, depth, fromCore, fromDepth, deltaDist, comment)
                self.replace(oldShift, ts)
            else: # it's a TIE, the new shift distance is the old shift distance plus fromDepth - depth
                newDist = deltaDist + oldShift.distance
                print "   current TIE shift {} + new shift {} = cumulative shift {}".format(oldShift.distance, deltaDist, newDist)
                #fromShiftDist = self.getShiftDistance(fromCore)
                ts = TieShift(core, depth - oldShift.distance, fromCore, deltaDist, newDist, comment)
                self.replace(oldShift, ts)

        # update TieShifts that descend from the core we just shifted     
        self.updateTieChain(core, deltaDist)
    
    def isLegalTie(self, core, fromCore):
        pass
    
    # is searchCore the fromCore for anything upstream?
    def isUpstream(self, searchCore, curCore):
        curShift = self.getShift(curCore)
        if curShift is None:
            return False
        elif curShift.fromCore == searchCore:
            return True
        else:
            return self.isUpstream(searchCore, curShift.fromCore)
    
    def updateTieChain(self, core, deltaDist):
        for shift in [s for s in self.shifts if isTie(s) and s.fromCore == core]:
            print "{} has parent {}, shifting by {}".format(shift.core, shift.fromCore, deltaDist)
            shift.distance += deltaDist
            self.updateTieChain(shift.core, deltaDist) # recurse
            
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
    
    def getShiftDistance(self, core):
        shift = self.getShift(core)
        return shift.distance if shift is not None else 0.0


# purely for testing in this module - we only care about hole and core identifiers
class MockCoreInfo:
    def __init__(self, hole, holeCore):
        self.hole = hole
        self.holeCore = holeCore
        
    def GetHoleCoreStr(self):
        return "{}{}".format(self.hole, self.holeCore)
    
    def __repr__(self):
        return self.GetHoleCoreStr()
    
    def __eq__(self, other):
        return self.hole == other.hole and self.holeCore == other.holeCore

if __name__ == "__main__":
    assert MockCoreInfo("A", "1") == MockCoreInfo("A", "1")
    assert not MockCoreInfo("A", "1") == MockCoreInfo("B", "1")
    
    ab = AffineBuilder()
    ab.set(MockCoreInfo("A", "2"), 2.03, "I am a fake SET")
    ab.tie(MockCoreInfo("B", "1"), 1.6, MockCoreInfo("A", "1"), 1.45)
    ab.tie(MockCoreInfo("C", "1"), 1.8, MockCoreInfo("B", "1"), 1.60)
    ab.tie(MockCoreInfo("B", "2"), 2.8, MockCoreInfo("C", "1"), 2.3)
    assert ab.isUpstream(MockCoreInfo("B", "1"), MockCoreInfo("A", "1"))
#     
#     ss2 = SetShift(MockCoreInfo("A", "3"), 2.03, "I am a fake SET")
#     ss3 = SetShift(MockCoreInfo("A", "4"), 2.03, "I am a fake SET")
#     ss4 = SetShift(MockCoreInfo("A", "4"), 2.03, "I am a fake SET")
#     shifts = [ss, ss2, ss3, ss4]
    
#     ts = TieShift(MockCoreInfo("A", "1"), 1.45, MockCoreInfo("B", "1"), 1.6, 0.15, "I am a fake TIE")
#     print ts
#     ss = SetShift(MockCoreInfo("A", "2"), 2.03, "I am a fake SET")
#     print ss