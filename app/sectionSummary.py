'''
Routines and classes for loading of tabular data and conversion to target formats
'''

import os
import unittest

import pandas

import tabularImport

# compare section numbers: any integer or 'CC', which is always greatest
def cmp_section(sec1, sec2):
    if sec1 == sec2:
        return 0
    if sec1 == 'CC':
        return 1
    if sec2 == 'CC':
        return -1
    return cmp(int(sec1), int(sec2))


class SectionSummary:
    def __init__(self, name, dataframe):
        self.name = name
        self.dataframe = dataframe
        
    @classmethod
    def createWithFile(cls, filepath):
        dataframe = tabularImport.readFile(filepath)
        stringColumns = ['Site', 'Core', 'Section']
        tabularImport.forceStringDatatype(stringColumns, dataframe)
        return cls(os.path.basename(filepath), dataframe)

    @classmethod
    def createWithFiles(cls, fileList):
        dataframes = []
        for filepath in fileList:
            dataframe = tabularImport.readFile(filepath)
            stringColumns = ['Site', 'Core', 'Section']
            tabularImport.forceStringDatatype(stringColumns, dataframe)
            dataframes.append(dataframe)
            
        ssDataframe = pandas.concat(dataframes, ignore_index=True)
        
        return cls(os.path.basename(filepath), ssDataframe)
    
    @classmethod
    def createWithPandasRows(cls, rows):
        dataframe = pandas.DataFrame(columns=tabularImport.SectionSummaryFormat.req)
        dataframe = dataframe.append(rows, ignore_index=True)
        stringColumns = ['Core', 'Section']
        tabularImport.forceStringDatatype(stringColumns, dataframe)
        return cls(os.path.basename("inferred section summary"), dataframe)
    
    def containsCore(self, site, hole, core):
        cores = self._findCores(site, hole, core)
        return not cores.empty
    
    def containsSection(self, site, hole, core, section):
        sections = self._findSection(site, hole, core, section)
        return not sections.empty
    
    # return depth of top of top section, bottom of bottom section
    def getCoreRange(self, site, hole, core):
        cores = self._findCores(site, hole, core)
        cores = cores[(cores.Section != "CC")] # omit CC section for time being
        if not cores.empty:
            coremin = cores['TopDepth'].min()
            coremax = cores['BottomDepth'].max()
            return coremin, coremax
        else:
            print "getCoreRange(): Couldn't find cores for site {} hole {} core {}".format(site, hole, core)
        return None
    
    # return type of core
    def getCoreType(self, site, hole, core):
        cores = self._findCores(site, hole, core)
        cores = cores[(cores.Section != "CC")] # omit CC section for time being
        if not cores.empty:
            return cores.iloc[0]['CoreType']
        else:
            print "getCoreType(): Couldn't find cores for site {} hole {} core {}".format(site, hole, core)
        return None
    
    def getSites(self):
        return set(self.dataframe['Site'])
    
    def getHoles(self):
        return set(self.dataframe['Hole'])
    
    def getCores(self, hole):
        return set(self.dataframe[(self.dataframe['Hole'] == hole) & (self.dataframe['Section'] != "CC")]['Core'])
    
    def getSections(self, hole, core):
        return set(self.dataframe[(self.dataframe['Hole'] == hole) & (self.dataframe['Core'] == core)]['Section'])
    
    # return sorted list of SectionSummaryRows for given hole and core
    def getSectionRows(self, hole, core):
        df = self.dataframe[(self.dataframe['Hole'] == hole) & (self.dataframe['Core'] == core)]
        rows = []
        for index, row in df.iterrows():
            if row['Section'] != 'CC':
                newRow = SectionSummaryRow.createWithPandasSeries(row)
                rows.append(newRow)
        return sorted(rows, key=lambda x:x.section, cmp=cmp_section)
    
    def getCoreTop(self, site, hole, core):
        top, _ = self.getCoreRange(site, hole, core)
        return top
    
    def getCoreBottom(self, site, hole, core):
        _, bottom = self.getCoreRange(site, hole, core)
        return bottom
    
    # note: this and getSectionBot() are fairly slow, really bogged down drawing
    def getSectionTop(self, site, hole, core, section):
        return self._getSectionValue(site, hole, core, section, 'TopDepth')
    
    def getSectionBot(self, site, hole, core, section):
        return self._getSectionValue(site, hole, core, section, 'BottomDepth')
    
    def getSectionRange(self, site, hole, core, section):
        return self.getSectionTop(site, hole, core, section), self.getSectionBot(site, hole, core, section)
    
    def getSectionCoreType(self, site, hole, core, section):
        return self._getSectionValue(site, hole, core, section, 'CoreType')
    
    def getSectionAtDepth(self, site, hole, core, depth):
        sec = self._findSectionAtDepth(site, hole, core, depth)
        return sec
    
    def sectionDepthToTotal(self, site, hole, core, section, secDepth):
        top = self.getSectionTop(site, hole, core, section)
        result = top + secDepth / 100.0 # cm to m
        #print "section depth {} in section {} = {} overall".format(secDepth, section, result)        
        return result
    
    def checkStrType(self, argList):
        for arg in argList:
            if not isinstance(arg, str):
                print "SectionSummary ERROR: encountered non-str query element {}".format(arg)
    
    def _findCores(self, site, hole, core):
        # omitting core here and below since it's an integer at present
        self.checkStrType([site, hole])
        df = self.dataframe
        cores = df[(df.Site == site) & (df.Hole == hole) & (df.Core == core)]
        if cores.empty:
            print "SectionSummary: Could not find core {}-{}{}".format(site, hole, core)
        return cores

    def _findSection(self, site, hole, core, section):
        self.checkStrType([site, hole, section])
        df = self.dataframe
        section = df[(df.Site == site) & (df.Hole == hole) & (df.Core == core) & (df.Section == section)]
        if section.empty:
            print "SectionSummary: Could not find {}-{}{}-{}".format(site, hole, core, section)
        return section
    
    def _findSectionAtDepth(self, site, hole, core, depth):
        self.checkStrType([site, hole])
        df = self.dataframe
        section = df[(df.Site == site) & (df.Hole == hole) & (df.Core == core) & (depth >= df.TopDepth) & (depth <= df.BottomDepth)]
        if not section.empty:
            return section.iloc[0]['Section']
        return None    
    
    def _getSectionValue(self, site, hole, core, section, columnName):
        self.checkStrType([site, hole, section])
        section = self._findSection(site, hole, core, section)
        return section.iloc[0][columnName]

# todo? SectionSummaryRow in which data is just a pandas series with methods to access
# each item (e.g. site(), coreType())? Child of SectionSummaryRow "interface" class?
class SectionSummaryRow:
    def __init__(self, exp, site, hole, core, coreType, section, topDepth, bottomDepth):
        self.exp = exp
        self.site = site
        self.hole = hole
        self.core = core
        self.coreType = coreType
        self.section = section
        self.topDepth = topDepth
        self.bottomDepth = bottomDepth
        
    @classmethod
    def createWithPandasSeries(cls, row):
        return cls(['Exp'], row['Site'], row['Hole'], row['Core'], row['CoreType'], row['Section'], row['TopDepth'], row['BottomDepth'])
        
    def asPandasSeries(self):
        return pandas.Series({'Exp':self.exp, 'Site':self.site, 'Hole':self.hole, 'Core':self.core, 'CoreType':self.coreType,
                              'Section':self.section, 'TopDepth':self.topDepth, 'BottomDepth':self.bottomDepth})

    def identity(self):
        return "{}-{}-{}".format(self.hole, self.core, self.section)
    

class TestSectionSummary(unittest.TestCase):
    def test_cmp(self):
        self.assertTrue(cmp_section('1', '2') == -1)
        self.assertTrue(cmp_section('1', 'CC') == -1)
        self.assertTrue(cmp_section('2', '1') == 1)
        self.assertTrue(cmp_section('CC', 'CC') == 0)
        
        secs = ['2', 'CC', '5', '7', '1']
        sortedSecs = sorted(secs, cmp=cmp_section)
        self.assertTrue(sortedSecs[0] == '1')
        self.assertTrue(sortedSecs[1] == '2')
        self.assertTrue(sortedSecs[2] == '5')
        self.assertTrue(sortedSecs[3] == '7')
        self.assertTrue(sortedSecs[4] == 'CC')
    
    def test_ss(self):
        # todo: move files to test data directory
        testfiles = ["/Users/bgrivna/Desktop/U1390_{}_Summary.csv".format(hole) for hole in ['A', 'B', 'C']]
        ss = SectionSummary.createWithFiles(testfiles)
        self.assertTrue(len(ss.dataframe) == 568)
        self.assertTrue(list(ss.getSites())[0] == 'U1390')
        holes = ss.getHoles()
        self.assertTrue('A' in holes and 'B' in holes and 'C' in holes and 'D' not in holes)
        
        # test a few sections in each hole
        self.assertTrue(ss.getSectionTop('U1390', 'A', '5', '3') == 33.33)
        self.assertTrue(ss.getSectionTop('U1390', 'A', '5', 'CC') == 40.86)
        self.assertTrue(ss.getSectionTop('U1390', 'B', '17', '1') == 146.6)
        self.assertTrue(ss.getSectionTop('U1390', 'B', '17', 'CC') == 157.41)
        self.assertTrue(ss.getSectionTop('U1390', 'C', '6', '1') == 42.4)
        self.assertTrue(ss.getSectionTop('U1390', 'C', '6', 'CC') == 52.32)


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSectionSummary)
    unittest.TextTestRunner(verbosity=2).run(suite)
