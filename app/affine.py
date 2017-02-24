'''
Created on Feb 22, 2017

@author: bgrivna

Support for the creation and editing of Affine Shifts and resulting tables.
'''

class AffineShift:  
    def __init__(self):
        pass
    
    def isTie(self): # hmmm this may be dumb.
        pass
    
    def isSet(self):
        pass

class TieShift(AffineShift):
    def __init__(self, core, depth, fromCore, fromDepth, distance, comment=""):
        AffineShift.__init__(self)
        self.core = core # CoreInfo for shifted core
        self.depth = depth # MBSF depth of shifted core's TIE point
        self.fromCore = fromCore # core to which self.core was tied
        self.fromDepth = fromDepth # MBSF depth of "from" core's TIE point
        self.distance = distance # distance of shift: distance + depth = MCD
        self.comment = comment

    def isTie(self):
        return True
    
    def isSet(self):
        return False

    def __repr__(self):
        fmtStr = "TIE: {}@{}mcd ({}mbsf) shifted {}m to align with {}@{}mcd ({})" 
        commentStr = "{}".format(self.comment) if self.comment != "" else ""
        return fmtStr.format(self.core.GetHoleCoreStr(), self.depth, self.depth - self.distance, self.distance, self.fromCore.GetHoleCoreStr(), self.fromDepth, commentStr)


class SetShift(AffineShift):
    def __init__(self, core, distance, comment=""):
        AffineShift.__init__(self)
        self.core = core # CoreInfo for shifted core
        self.distance = distance # distance of shift: distance + depth = MCD
        self.comment = comment

    def isTie(self):
        return False
    
    def isSet(self):
        return True
        
    def __repr__(self):
        commentStr = "{}".format(self.comment) if self.comment != "" else ""
        return "SET: {} shifted {}m ({})".format(self.core.GetHoleCoreStr(), self.distance, commentStr)


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
            
    def tie(self, core, depth, fromCore, fromDepth, comment=""):
        deltaDist = (fromDepth - depth) 
        if not self.coreHasShift(core):
            ts = TieShift(core, depth, fromCore, fromDepth, fromDepth - depth, comment)
            self.add(ts)
        else: # core already has a shift...
            oldShift = self.getShift(core)
            if isinstance(oldShift, SetShift): # if it's a SET, override it entirely
                ts = TieShift(core, depth, fromCore, fromDepth, fromDepth - depth, comment)
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
        elif curShift.fromCore == searchCore: #.hole == searchCore.hole and curShift.fromCore.holeCore == searchCore.holeCore:
            return True
        else:
            return self.isUpstream(searchCore, curShift.fromCore)
    
    def updateTieChain(self, core, deltaDist):
        for shift in [s for s in self.shifts if s.isTie() and s.fromCore == core]: #s.fromCore.hole == core.hole and s.fromCore.holeCore == core.holeCore]:
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
        shifts = [s for s in self.shifts if s.core == core] #s.core.hole == core.hole and s.core.holeCore == core.holeCore]
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
    ss = SetShift(MockCoreInfo("A", "2"), 2.03, "I am a fake SET")
    ts = TieShift(MockCoreInfo("A", "1"), 1.45, MockCoreInfo("B", "1"), 1.6, 0.15, "I am a fake TIE")
    ab.set(MockCoreInfo("A", "2"), 2.03, "I am a fake SET")
    ab.tie(MockCoreInfo("A", "1"), 1.45, MockCoreInfo("B", "1"), 1.6)
    ab.tie(MockCoreInfo("B", "1"), 1.60, MockCoreInfo("C", "1"), 1.8)
    ab.tie(MockCoreInfo("C", "1"), 2.3, MockCoreInfo("B", "2"), 2.8)
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