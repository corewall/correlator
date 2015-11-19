'''
Created on Nov 16, 2015

@author: bgrivna

Support for the creation and editing of Splice Interval Tables.
'''

import unittest

class Interval:
    def __init__(self, top, bot):
        if top >= bot:
            raise ValueError("Cannot create Interval: top must be < bot")
        self.top = top
        self.bot = bot
        
    def __repr__(self):
        return "[{} - {}]".format(self.top, self.bot)
    
    def contains(self, val):
        return contains(self, val)
    
    def containsStrict(self, val):
        return containsStrict(self, val)
    
    def equals(self, interval):
        return self.top == interval.top and self.bot == interval.bot
    
    def length(self):
        return self.bot - self.top
    
    def overlaps(self, interval):
        return overlaps(self, interval)
    
    def touches(self, interval):
        return touches(self, interval)
    
    def encompasses(self, interval):
        return self.top <= interval.top and self.bot >= interval.bot

# "Touching" intervals have a common edge but no overlap...this means
# that an Interval does *not* touch itself.
def touches(i1, i2):
    return i1.top == i2.bot or i1.bot == i2.top

# Do Intervals overlap? "Touching" intervals (i1.bot == i2.top)
# are considered to overlap as well. Need to check both to cover
# case where one interval encompasses another
def overlaps(i1, i2):
    return i1.contains(i2.top) or i1.contains(i2.bot) or i2.contains(i1.top) or i2.contains(i1.bot)

# Does Interval i contain value val (top and bot inclusive)?
def contains(interval, val): 
    return val <= interval.bot and val >= interval.top

# Does Interval i contain value val (top and bot excluded)?
def containsStrict(interval, val):
    return val < interval.bot and val > interval.top

# Combine overlapping Intervals i1 and i2, return resulting Interval
def merge(i1 ,i2):
    if not i1.overlaps(i2):
        raise ValueError("Can't merge non-overlapping intervals {} and {}".format(i1, i2))
    return Interval(min(i1.top, i2.top), max(i1.bot, i2.bot))

# Given list of Intervals, merge where possible and return resulting Intervals.
# TODO: default param to sort or not?
def union(intervals):
    intervals = sorted(intervals, key=lambda i: i.top) #  must be top-sorted
    result = []
    lastMergeIdx = -1
    for i in range(len(intervals)):
        if i <= lastMergeIdx: # skip already-merged intervals from subloop
            continue
        newint = intervals[i]
        if i == len(intervals) - 1: # last interval
            result.append(newint)
        else: # merge as many subsequent Intervals into newint as possible, then append to result list
            for j in range(i+1, len(intervals)): 
                if newint.overlaps(intervals[j]): # can we merge this interval into newint?
                    newint = merge(newint, intervals[j])
                    lastMergeIdx = j
                    if j == len(intervals) - 1: # last interval
                        result.append(newint)
                else:
                    result.append(newint)
                    break
    return result

# Return list of Intervals of any gaps within overall range of passed Intervals
def gaps(intervals, mindepth, maxdepth):
    result = []
    if len(intervals) == 0:
        result.append(Interval(mindepth, maxdepth))
    else:
        intervals = union(intervals)
        
        # gaps between min/max and start/end of intervals range
        intmin = min([i.top for i in intervals])
        intmax = max([i.bot for i in intervals])
        if mindepth < intmin:
            result.append(Interval(mindepth, intmin))
        if maxdepth > intmax:
            result.append(Interval(intmax, maxdepth))
    
        # gaps within intervals
        if len(intervals) > 1:
            for i in range(len(intervals) - 1):
                gap = Interval(intervals[i].bot, intervals[i+1].top)
                result.append(gap)
    return result


class TestIntervals(unittest.TestCase):
    def test_create(self):
        with self.assertRaises(ValueError):
            Interval(1, 1) # top == bot
        with self.assertRaises(ValueError):
            Interval(1, 0) # top > bot
        i = Interval(-1, 3.1415)
        self.assertEquals(i.top, -1)
        self.assertEquals(i.bot, 3.1415)
        
    def test_touches(self):
        i1 = Interval(0, 10)
        i2 = Interval(10, 20)
        self.assertTrue(i1.touches(i2))
        self.assertTrue(i2.touches(i1))
        self.assertFalse(i1.touches(i1))
        
    def test_contains(self):
        i = Interval(0, 10)
        self.assertTrue(i.contains(0))
        self.assertTrue(i.contains(10))
        self.assertFalse(i.containsStrict(0))
        self.assertFalse(i.containsStrict(10))
        self.assertTrue(i.contains(5))
        self.assertFalse(i.contains(-0.0001))
        self.assertFalse(i.contains(10.0001))
        
    def test_overlaps(self):
        i1 = Interval(0, 10)
        i2 = Interval(5, 15)
        i3 = Interval(10, 20)
        i4 = Interval(20.0001, 30)
        i5 = Interval(-10, 40) # all-encompassing
        self.assertTrue(i1.overlaps(i1))
        self.assertTrue(i1.overlaps(i2))
        self.assertTrue(i1.overlaps(i3))
        self.assertTrue(i2.overlaps(i3))
        self.assertFalse(i3.overlaps(i4))
        self.assertTrue(i5.overlaps(i1))
        self.assertTrue(i1.overlaps(i5))
        
    def test_merge(self):
        i1 = Interval(0, 10)
        i2 = Interval(10, 20)
        i3 = Interval(20, 30)
        i4 = Interval(5, 15)
        
        merge1 = merge(i1, i2)
        self.assertTrue(merge1.top == 0)
        self.assertTrue(merge1.bot == 20)
        
        merge2 = merge(i3, merge1)
        self.assertTrue(merge2.top == 0)
        self.assertTrue(merge2.bot == 30)
        
        merge3 = merge(i1, i4)
        self.assertTrue(merge3.top == 0)
        self.assertTrue(merge3.bot == 15)
        
        with self.assertRaises(ValueError):
            merge(i1, i3)
            
    def test_union(self):
        i1 = Interval(0, 10)
        i2 = Interval(5, 15)
        i3 = Interval(10, 20)
        i4 = Interval(21, 25)
        i5 = Interval(24, 25)
        
        u1 = union([i1, i2])
        self.assertTrue(len(u1) == 1)
        self.assertTrue(u1[0].top == 0)
        self.assertTrue(u1[0].bot == 15)
        
        u2 = union([i1, i2, i3])
        self.assertTrue(len(u2) == 1)
        self.assertTrue(u2[0].top == 0)
        self.assertTrue(u2[0].bot == 20)
        
        u3 = union([i3, i4, i5])
        self.assertTrue(len(u3) == 2)
        self.assertTrue(u3[0].top == 10)
        self.assertTrue(u3[1].top == 21)
        self.assertTrue(u3[1].bot == 25)
        
        u4 = union([Interval(0, 1), Interval(0, 1)])
        self.assertTrue(u4[0].top == 0)
        self.assertTrue(u4[0].bot == 1)
        
        u5 = union([Interval(2, 3), Interval(1, 4)])
        self.assertTrue(len(u5) == 1)
        self.assertTrue(u5[0].top == 1)
        self.assertTrue(u5[0].bot == 4)

class SpliceInterval:
    def __init__(self, coreinfo, top, bot, comment=""):
        self.coreinfo = coreinfo # CoreInfo for core used in this interval
        self.interval = Interval(top, bot)
        self.comment = comment
        
    # 11/18/2015 brg: name getTop/Bot() to avoid Python's silence when one
    # mistakenly uses SpliceInterval.top instead of top(). Confusing since
    # Interval.top/bot is legitimate. 
    def getTop(self):
        return self.interval.top
    
    def getBot(self):
        return self.interval.bot
    
    def overlaps(self, interval):
        return self.interval.overlaps(interval)
    
    def contains(self, value):
        return self.interval.contains(value)
    
    def __repr__(self):
        return str(self.interval)


class SpliceManager:
    def __init__(self):
        self.ints = [] # list of SpliceIntervals (ordered by depth?)
        
    def count(self):
        return len(self.ints)

    def datarange(self):
        if len(self.ints) > 0:
            datamin = min([i.coreinfo.minData for i in self.ints])
            datamax = max([i.coreinfo.maxData for i in self.ints])
            return datamin, datamax
        
    def getIntervalsInRange(self, mindepth, maxdepth):
        testInterval = Interval(mindepth, maxdepth)
        return [i for i in self.ints if i.overlaps(testInterval)]
        
    def add(self, coreinfo):
        interval = Interval(coreinfo.minDepth, coreinfo.maxDepth)
        if self._canAdd(interval):
            for gap in gaps(self._overs(interval), interval.top, interval.bot):
                self.ints.append(SpliceInterval(coreinfo, gap.top, gap.bot))
                self.ints = sorted(self.ints, key=lambda i: i.getTop())
                print "Added {}, now = {}".format(interval, self.ints)
        else:
            print "couldn't add interval {}".format(interval)
        
    def _canAdd(self, interval):
        u = union([i.interval for i in self.ints])
        e = [i for i in u if i.encompasses(interval)]
        if len(e) > 0:
            print "Interval {} encompassed by {}".format(interval, e)
        return len(e) == 0

    # return union of all overlapping Intervals in self.ints    
    def _overs(self, interval):
        return union([i.interval for i in self.ints if i.interval.overlaps(interval)])
    
    
    
# run unit tests on main for now
if __name__ == '__main__':
    unittest.main()