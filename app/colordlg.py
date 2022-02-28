#!/usr/bin/env python

# Select Color dialog
import platform
platform_name = platform.uname()

import wx

class ColorsDialog(wx.Dialog):
    def __init__(self, parent, colorDict, defaultColorDict, colorLabelDict):
        wx.Dialog.__init__(self, parent, -1, "Set Colors", style=wx.DEFAULT_DIALOG_STYLE)

        self.defaultColorDict = defaultColorDict
        self.pickerDict = {}
        # TODO: Color picker pops behind this dialog if Correlator is deactivated and reactivated, ugh...STAY_ON_TOP
        # may not be what we need here

        dlgSizer = wx.BoxSizer(wx.VERTICAL)

        envPanel = wx.Panel(self, -1)
        envSizer = wx.StaticBoxSizer(wx.StaticBox(envPanel, -1, "Environment"), orient=wx.HORIZONTAL)
        for idx, key in enumerate(['background', 'foreground', 'imageOverlay']):
            cp = self.makeColorPicker(envPanel, idx, colorDict[key])
            self.pickerDict[key] = cp
            envSizer.Add(cp, 0, wx.ALIGN_CENTER_VERTICAL)
            envSizer.Add(wx.StaticText(envPanel, -1, colorLabelDict[key]), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 20)
        envPanel.SetSizer(envSizer)
        dlgSizer.Add(envPanel, 0, wx.ALL, 5)

        sasPanel = self.makePickerPanel("Shifting and splicing", ['corrWindow', 'spliceTrace', 'splice', 'spliceSel'])
        shiftPanel = self.makePickerPanel("Shift type", ['mbsf', 'ccsfTie', 'ccsfSet', 'ccsfRel'])
        row1Sizer = wx.BoxSizer(wx.HORIZONTAL)
        row1Sizer.Add(sasPanel, 1, wx.ALL, 5)
        row1Sizer.Add(shiftPanel, 1, wx.ALL, 5)
        dlgSizer.Add(row1Sizer, 0, wx.EXPAND)

        holePanel = self.makePickerPanel("Color traces by hole", ['hole'+h for h in ['A','B','C','D','E','F']])
        smoothPanel = self.makePickerPanel("Smooth data traces", ['smooth'+h for h in ['A','B','C','D','E','F']])
        row2Sizer = wx.BoxSizer(wx.HORIZONTAL)
        row2Sizer.Add(holePanel, 1, wx.ALL, 5)
        row2Sizer.Add(smoothPanel, 1, wx.ALL, 5)
        dlgSizer.Add(row2Sizer, 0, wx.EXPAND)

        buttonPanel = wx.Panel(self, -1)
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        applyButton = wx.Button(buttonPanel, -1, "Apply")
        self.Bind(wx.EVT_BUTTON, self.onApply, applyButton)
        resetButton = wx.Button(buttonPanel, -1, "Reset defaults")
        self.Bind(wx.EVT_BUTTON, self.onReset, resetButton)
        closeButton = wx.Button(buttonPanel, wx.ID_OK, "Close")
        buttonSizer.Add(applyButton, 0, wx.ALL, 10)
        buttonSizer.Add(resetButton, 0, wx.ALL, 10)
        buttonSizer.Add(closeButton, 0, wx.ALL, 10)
        buttonPanel.SetSizer(buttonSizer)

        dlgSizer.Add(buttonPanel, 0, wx.ALIGN_CENTER)

        self.SetSizerAndFit(dlgSizer)
        self.Center()

    def makeColorPicker(self, parent, cpid, color):
        # force a reasonable width, otherwise controls are needlessly wide on Windows
        cpsize = (50,-1) if platform_name[0] == "Windows" else wx.DefaultSize 
        return wx.ColourPickerCtrl(parent, cpid, color, size=cpsize)

    # return wx.Panel with a column of color pickers
    def makePickerPanel(self, title, keys):
        panel = wx.Panel(self, -1)
        sizer = wx.StaticBoxSizer(wx.StaticBox(panel, -1, title), orient=wx.VERTICAL)
        for idx, key in enumerate(keys):
            cp = self.makeColorPicker(panel, idx, colorDict[key])
            self.pickerDict[key] = cp
            sz = wx.BoxSizer(wx.HORIZONTAL)
            sz.Add(cp, 0, wx.ALIGN_CENTER_VERTICAL)
            sz.Add(wx.StaticText(panel, -1, colorLabelDict[key]), 0, wx.ALIGN_CENTER_VERTICAL)
            sizer.Add(sz, 0)
        panel.SetSizer(sizer)
        return panel

    # return colorDict reflecting state of all pickers
    def getColorDict(self):
        colorDict = {}
        for key, picker in self.pickerDict.items():
            colorDict[key] = picker.GetColour()
        return colorDict

    # set pickers to contents of colorDict
    def installColorDict(self, colorDict):
        for key, picker in self.pickerDict.items():
            picker.SetColour(colorDict[key])

    def onApply(self, evt):
        colorDict = self.getColorDict()
        print(colorDict)

    def onReset(self, evt):
        self.installColorDict(self.defaultColorDict)

class MockApp(wx.App):
    def __init__(self):
        wx.App.__init__(self)
        self.frame = None
        
    def OnInit(self):
        self.frame = wx.Frame(None, -1, "MockFrame", wx.Point(200,200), size=(200,200))
        self.SetTopWindow(self.frame)
        self.frame.Show()
        self.frame.Center()
        return True

if __name__ == "__main__":
    app = MockApp()

    # OLD COLORS dictionary so we can name colors - also need a list of names since dictionary is unordered
    # colorDictKeys = [ 'mbsf', 'ccsfTie', 'ccsfSet', 'ccsfRel', 'eld', 'smooth', 'splice', 'log', 'mudlineAdjust', \
    #                         'fixedTie', 'shiftTie', 'paleomag', 'diatom', 'rad', 'foram', \
    #                         'nano', 'background', 'foreground', 'corrWindow', 'guide', 'imageOverlay' ] 
    # colorDict = { 'mbsf': wx.Colour(238, 238, 0), 'ccsfTie': wx.Colour(0, 139, 0), \
    #                     'ccsfSet': wx.Colour(0, 102, 255), 'ccsfRel': wx.Colour(255, 153, 0), \
    #                     'eld': wx.Colour(0, 255, 255), 'smooth': wx.Colour(238, 216, 174), \
    #                     'splice': wx.Colour(30, 144, 255), 'log': wx.Colour(64, 224, 208), \
    #                     'mudlineAdjust': wx.Colour(0, 255, 0), 'fixedTie': wx.Colour(139, 0, 0), \
    #                     'shiftTie': wx.Colour(0, 139, 0), 'paleomag': wx.Colour(30, 144, 255), \
    #                     'diatom': wx.Colour(218, 165, 32), 'rad': wx.Colour(147, 112, 219), \
    #                     'foram': wx.Colour(84, 139, 84), 'nano': wx.Colour(219, 112, 147), \
    #                     'background': wx.Colour(0, 0, 0), 'foreground': wx.Colour(255, 255, 255), \
    #                     'corrWindow': wx.Colour(178, 34, 34), 'guide': wx.Colour(224, 255, 255), \
    #                     'imageOverlay': wx.Colour(238,238,0) }
    # assert len(colorDictKeys) == len(colorDict)

    colorDictKeys = ['background', 'foreground', 'imageOverlay',  'mbsf', \
         'ccsfTie', 'ccsfSet', 'ccsfRel', 'corrWindow', 'splice', 'spliceSel', 'spliceTrace', 'holeA', 'holeB', \
        'holeC', 'holeD', 'holeE', 'holeF', 'smoothA', 'smoothB', 'smoothC', \
        'smoothD', 'smoothE', 'smoothF']
    colorDict = {'background':wx.Colour(0,0,0), 'foreground':wx.Colour(255,255,255), 'imageOverlay':wx.Colour(238,238,0), \
        'mbsf':wx.Colour(238,238,0), 'ccsfTie':wx.Colour(0,139,0), 'ccsfSet':wx.Colour(0,102,255), 'ccsfRel':wx.Colour(255,153,0), \
        'corrWindow':wx.Colour(178,34,34), 'splice':wx.Colour(30,144,255), 'spliceSel':wx.GREEN, 'spliceTrace':wx.Colour(178,34,34), \
        'holeA':wx.Colour(234,153,153), 'holeB':wx.Colour(128,215,168), 'holeC':wx.Colour(158,196,247), 'holeD':wx.Colour(255,229,153), \
        'holeE':wx.Colour(213,166,189), 'holeF':wx.Colour(180,167,214), 'smoothA':wx.Colour(206,40,36), 'smoothB':wx.Colour(0,158,15), \
        'smoothC':wx.Colour(43,120,228), 'smoothD':wx.Colour(255,157,11), 'smoothE':wx.Colour(255,0,255), 'smoothF':wx.Colour(153,0,255)
    }
    defaultColorDict = dict(colorDict)
    colorLabelDict = {'background':'Background', 'foreground':'General labels', 'imageOverlay':'Section numbers on images', \
        'mbsf':'CSF-A', 'ccsfTie':'CCSF by TIE', 'ccsfSet':'CCSF by SET', 'ccsfRel':'Shifted along untied', \
        'corrWindow':'Shift core trace', 'splice':'Splice', 'spliceSel':'Selected splice interval', 'spliceTrace':'Splice core trace', \
        'holeA':'Hole A', 'holeB':'Hole B', 'holeC':'Hole C', 'holeD':'Hole D', 'holeE':'Hole E', 'holeF':'Hole F', \
        'smoothA':'Smooth A', 'smoothB':'Smooth B', 'smoothC':'Smooth C', 'smoothD':'Smooth D', 'smoothE':'Smooth E', 'smoothF':'Smooth F'}
    assert len(colorDict) == len(colorDictKeys) == len(colorLabelDict)

    # print(colorLabelDict.keys())
    dlg = ColorsDialog(app.frame, colorDict, defaultColorDict, colorLabelDict)
    result = dlg.ShowModal()
