#!/usr/bin/env python

## For Mac-OSX
#/usr/bin/env pythonw
from __future__ import print_function
from builtins import chr
from builtins import str
from builtins import range
import platform
platform_name = platform.uname()

from enum import Enum

import re

import wx
import wx.grid
import wx.lib.sheet as sheet
from wx.lib import plot
from wx.lib.agw.hyperlink import HyperLinkCtrl
import random, sys, os, re, time, string
import numpy

import smooth
from utils import load_bmp_resource, get_resource_path


class CoreSheet(sheet.CSheet):
    def __init__(self, parent, x, y):
        sheet.CSheet.__init__(self, parent)
        self.SetWindowStyle(wx.ALWAYS_SHOW_SB)
        self.SetNumberRows(x)
        self.SetNumberCols(y)
        self.EnableEditing(False)

class HoldDialog(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, -1, "Communication", size=(330, 130), style = wx.DEFAULT_DIALOG_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE |wx.STAY_ON_TOP)
        self.Center()
        bmp = wx.StaticBitmap(self, -1, load_bmp_resource('icons/about-32x32.png'), (10, 30))
        wx.StaticText(self, -1, "Waiting for Fine Tune from Corelyzer", (60,30))
        #self.EndModal(wx.ID_OK)


# Should be interchangeable with MessageDialog 'nobutton'
class MsgDlgButtons(Enum):
    YesNo = 0
    Ok = 1
    OkCancel = 2

# - customLabels: list of 1 or 2 strings to use instead of "Yes/OK" and "No/Cancel".
# If nobutton == 0, element 0 replaces "Yes" and element 1 replaces "No".
# If nobutton == 1, element 0 replaces "OK".
# If nobutton == 2, element 0 replaces "OK" and element 1 replaces "Cancel".
def MessageDialog(parent, title, msg, nobutton, makeNoDefault=False, customLabels=None):
    style = _createMessageDialogStyle(title, nobutton, makeNoDefault)
    dlg = wx.MessageDialog(parent, msg, title, style)
    if customLabels:
        _setCustomLabels(dlg, nobutton, customLabels)
    return dlg

# Argh! RichMessageDialog is not part of wx 2.9.5 on Mac or Win, despite
# doc claiming it's available in 2.9.2 and beyond. Once we upgrade to
# wx 4+, the below should work.
# Use SuppressibleMessageDialog class for now.
# def SuppressibleMessageDialog_wx4(parent, title, msg, nobutton, suppressMsg, makeNoDefault=False, customLabels=None):
# 	style = _createMessageDialogStyle(title, nobutton, makeNoDefault)
# 	dlg = wx.RichMessageDialog(parent, msg, title, style)
# 	dlg.ShowCheckBox(suppressMsg)
# 	if customLabels:
# 		_setCustomLabels(dlg, nobutton, customLabels)
# 	return dlg

def _createMessageDialogStyle(title, nobutton, makeNoDefault):
    style = 0
    if title == "Error":
        style = wx.ICON_ERROR
    elif title in ["About", "Help", "Information", "Warning"]:
        style = wx.ICON_INFORMATION

    if nobutton == 0:
        style = style | wx.YES_NO
        if makeNoDefault:
            style = style | wx.NO_DEFAULT
    elif nobutton == 1:
        style = style | wx.OK
    elif nobutton == 2:
        style = style | wx.OK | wx.CANCEL
    return style

def _setCustomLabels(dlg, nobutton, customLabels):
    if nobutton == 0 and len(customLabels) == 2:
        dlg.SetYesNoLabels(customLabels[0], customLabels[1])
    elif nobutton == 1 and len(customLabels) == 1:
        dlg.SetOKLabel(customLabels[0])
    elif nobutton == 2 and len(customLabels) == 2:
        dlg.SetOKCancelLabels(customLabels[0], customLabels[1])

# brg 2/27/2022
# Hack-job, good enough for the few spots we need a suppressible message dialog.
# To be replaced with RichMessageDialog when we upgrade to wx 4+.
# Warning: if buttons=MsgDlgButtons.YesNo, the dialog still returns
# wx.ID_OK for Yes and wx.ID_CANCEL for no!
class SuppressibleMessageDialog(wx.Dialog):
    def __init__(self, parent, title, msg, buttons, suppressMsg="Don't show this message again", customLabels=None):
        wx.Dialog.__init__(self, parent, -1, title, size=(350,-1))
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        panel = wx.Panel(self, -1)
        sizer = wx.BoxSizer(wx.VERTICAL)
        text = wx.StaticText(panel, -1, msg)
        sizer.Add(text, 1, wx.ALL, 10)
        self.box = wx.CheckBox(panel, -1, suppressMsg)
        sizer.Add(self.box, 0, wx.ALL, 10)
        if buttons == MsgDlgButtons.OkCancel:
            if customLabels and len(customLabels) == 2:
                buttonPanel = OkButtonPanel(panel, okName=customLabels[0], cancelName=customLabels[1])
            else:
                buttonPanel = OkButtonPanel(panel)
        elif buttons == MsgDlgButtons.YesNo:
            buttonPanel = OkButtonPanel(panel, okName="Yes", cancelName="No")
        elif buttons == MsgDlgButtons.Ok:
            buttonPanel = OkButtonPanel(panel, okOnly=True)
        sizer.Add(buttonPanel, 0, wx.ALL | wx.ALIGN_CENTER, 10)
        panel.SetSizer(sizer)
        mainSizer.Add(panel)
        text.Wrap(350)
        self.SetSizerAndFit(mainSizer)
        self.Center()

    def IsCheckBoxChecked(self):
        return self.box.IsChecked()


class MessageDialogOLD(wx.Dialog):
    def __init__(self, parent, title, msg, nobutton):
        if title == "About" or title == "Help": 
            wx.Dialog.__init__(self, parent, -1, title, size=(330, 130), style= wx.STAY_ON_TOP)
        else:
            wx.Dialog.__init__(self, parent, -1, title, size=(330, 110), style= wx.STAY_ON_TOP)

        self.Center()
        vbox_top = wx.BoxSizer(wx.VERTICAL)
        panel1 = wx.Panel(self, -1, style = wx.WANTS_CHARS)
        sizer = wx.FlexGridSizer(1, 2, gap=(0,0))
        if title == "Error": 
            bmp = wx.StaticBitmap(panel1, -1, load_bmp_resource('icons/ErrorCircle-32x32.png'))
            sizer.Add(bmp, 0, wx.LEFT | wx.TOP, 9)
        elif title == "Information" or title == "Help":
            bmp = wx.StaticBitmap(panel1, -1, load_bmp_resource('icons/about-32x32.png'))
            sizer.Add(bmp, 0, wx.LEFT | wx.TOP, 9)
        elif title == "About":
            bmp = wx.StaticBitmap(panel1, -1, load_bmp_resource('icons/help-32x32.png'))
            sizer.Add(bmp, 0, wx.LEFT | wx.TOP, 9)
        sizer.Add(wx.StaticText(panel1, -1, msg), 0, wx.LEFT | wx.TOP | wx.BOTTOM, 15)
        panel1.SetSizer(sizer)
        vbox_top.Add(panel1)

        if nobutton == 1:
            okBtn = wx.Button(self, wx.ID_OK, "OK")
            vbox_top.Add(okBtn, 0, wx.LEFT, 110)
        else:
            grid = wx.GridSizer(1,2, gap=(0,0))
            okBtn = wx.Button(self, wx.ID_OK, "OK")
            grid.Add(okBtn)
            cancelBtn = wx.Button(self, wx.ID_CANCEL, "Cancel")
            grid.Add(cancelBtn, 0, wx.LEFT, 10)
            vbox_top.Add(grid, 0, wx.LEFT, 70)

        #wx.EVT_KEY_UP(self, self.OnCharUp)
        panel1.Bind(wx.EVT_CHAR, self.OnCharUp)
        self.SetSizer(vbox_top)

    # 9/17/2013 brg: Seems we only need to handle enter for Okay, escape
    # is automatically handled by wx.Dialog
    def OnCharUp(self,event):
        if event.GetKeyCode() == wx.WXK_RETURN:
            self.EndModal(wx.ID_OK)
        else:
            event.Skip()

class Message3Button(wx.Dialog):
    def __init__(self, parent, msg, yesLabel="Yes", okLabel="No", cancelLabel="Cancel"):
        wx.Dialog.__init__(self, parent, -1, "About", style=wx.DEFAULT_DIALOG_STYLE)

        self.Center()
        vbox_top = wx.BoxSizer(wx.VERTICAL)
        panel1 = wx.Panel(self, -1)
        sizer = wx.FlexGridSizer(1, 2, gap=(0,0))
        bmp = wx.StaticBitmap(panel1, -1, load_bmp_resource('icons/help-32x32.png'))
        sizer.Add(bmp, 0, wx.LEFT | wx.TOP, 9)
        sizer.Add(wx.StaticText(panel1, -1, msg), 0, wx.LEFT | wx.TOP | wx.BOTTOM, 15)
        panel1.SetSizer(sizer)
        vbox_top.Add(panel1)

        grid = wx.BoxSizer(wx.HORIZONTAL)
        okBtn = wx.Button(self, wx.ID_YES, yesLabel)
        self.Bind(wx.EVT_BUTTON, self.OnYES, okBtn)
        grid.Add(okBtn, 1, wx.LEFT | wx.RIGHT, 5)
        noBtn = wx.Button(self, wx.ID_OK, okLabel)
        grid.Add(noBtn, 1, wx.LEFT | wx.RIGHT, 5)
        cancelBtn = wx.Button(self, wx.ID_CANCEL, cancelLabel)
        grid.Add(cancelBtn, 1, wx.LEFT | wx.RIGHT, 5)
        vbox_top.Add(grid, 0, wx.ALIGN_RIGHT | wx.ALL, 10)

        self.SetSizer(vbox_top)
        self.GetSizer().Fit(self)
        wx.EVT_KEY_UP(self, self.OnCharUp)

    def OnYES(self, event):
        self.EndModal(wx.ID_YES)

    def OnCharUp(self,event):
        keyid = event.GetKeyCode() 
        if keyid == wx.WXK_RETURN:
            self.EndModal(wx.ID_OK) 
        elif keyid == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL) 


# Dialog with a wx.Grid widget for viewing tabular data
class ViewDataFileDialog(wx.Dialog):
    def __init__(self, parent, title, dataframe):
        if platform_name[0] == "Windows":
            # Using wx.RESIZE_BORDER | wx.CLOSE_BOX resulted in odd titlebar-less window on Windows.
            # This set of style options yields a typical window.
            style = wx.DEFAULT_DIALOG_STYLE | wx.MINIMIZE_BOX | wx.MAXIMIZE_BOX | wx.RESIZE_BORDER | wx.STAY_ON_TOP
        else:
            style = wx.RESIZE_BORDER | wx.CLOSE_BOX | wx.STAY_ON_TOP
        wx.Dialog.__init__(self, parent, -1, title, style=style)

        self.dataframe = dataframe

        # table
        self.filePanel = wx.Panel(self, -1)
        self.table = wx.grid.Grid(self.filePanel, -1)
        self.table.DisableDragRowSize()

        # close button
        self.closeButton = wx.Button(self.filePanel, -1, "Close")
        self.closeButton.SetDefault()
        self.Bind(wx.EVT_BUTTON, self.OnClose, self.closeButton)

        # layout
        fpsizer = wx.BoxSizer(wx.VERTICAL)		
        fpsizer.Add(self.table, 1, wx.EXPAND)
        fpsizer.Add(self.closeButton, 0, wx.ALIGN_RIGHT | wx.ALL, 10)
        self.filePanel.SetSizer(fpsizer)

        self._populateTable()

        # events
        wx.EVT_CHAR_HOOK(self, self.OnKey)

    def _populateTable(self):
        self.table.CreateGrid(len(self.dataframe), len(self.dataframe.columns.tolist()))
        self.table.EnableEditing(False)

        # populate headers if any
        for colidx, name in enumerate(self.dataframe.columns.tolist()):
            if name is not None:
                self.table.SetColLabelValue(colidx, name)

        # populate cells
        for ridx, row in enumerate(self.dataframe.itertuples()):
            for cidx in range(0, len(row) - 1):
                cellStr = str(row[cidx + 1])
                if cellStr == "nan":
                    cellStr = ""
                self.table.SetCellValue(ridx, cidx, cellStr) # skip leading index column

        self.table.AutoSize() # resize columns to fit header+data...bogs things down with large files
        tableWidth, tableHeight = self.table.GetSize()
        # 3/20/2019 todo: revisit this and find a less fudgy solution!
        # 50 is a fudge factor to account for the window's titlebar and Close button panel.
        # Without it, window was too short to see contents of short files (<= 3 rows),
        # forcing user to resize, which was silly.
        self.SetClientSize((tableWidth, tableHeight + 50))

    def OnClose(self, evt):
        self.EndModal(wx.ID_OK)

    def OnKey(self, evt):
        if evt.GetKeyCode() == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_OK)


class CustomDataTypeDialog(wx.Dialog):
    def __init__(self, parent, title):
        wx.Dialog.__init__(self, parent, -1, title, style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP)

        self.Center()
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.txt = wx.TextCtrl(self, -1, "[new data type]", size=(250,-1))

        vbox.Add(self.txt, 1, wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND, 15)

        self.register = wx.CheckBox(self, -1, 'Add Data Type to List')
        vbox.Add(self.register, 0, wx.ALL, 10)

        grid = wx.GridSizer(1,2, gap=(0,0))
        # grid.Add(self.register)
        okBtn = wx.Button(self, wx.ID_OK, "OK")
        grid.Add(okBtn)
        cancelBtn = wx.Button(self, wx.ID_CANCEL, "Cancel")
        grid.Add(cancelBtn, 0, wx.LEFT, 10)
        vbox.Add(grid, 0, wx.ALL | wx.ALIGN_CENTER, 10)
        self.SetSizer(vbox)
        self.Fit()
        self.txt.SelectAll()
        wx.EVT_KEY_UP(self, self.OnCharUp)

    def OnCharUp(self,event):
        keyid = event.GetKeyCode() 
        if keyid == wx.WXK_RETURN:
            self.EndModal(wx.ID_OK) 
        elif keyid == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL) 

class EditBoxDialog(wx.Dialog):
    def __init__(self, parent, title):
        wx.Dialog.__init__(self, parent, -1, title, size=(300, 130), style=wx.STAY_ON_TOP | wx.DEFAULT_DIALOG_STYLE)

        self.Center()
        vbox_top = wx.BoxSizer(wx.VERTICAL)
        self.txt = wx.TextCtrl(self, -1, "", size=(270, 25), style=wx.SUNKEN_BORDER)

        vbox_top.Add(self.txt, 0, wx.LEFT | wx.TOP | wx.BOTTOM, 15)

        grid = wx.GridSizer(1,2, gap=(0,0))
        okBtn = wx.Button(self, wx.ID_OK, "OK")
        grid.Add(okBtn)
        cancelBtn = wx.Button(self, wx.ID_CANCEL, "Cancel")
        grid.Add(cancelBtn, 0, wx.LEFT, 10)
        vbox_top.Add(grid, 0, wx.LEFT, 50)
        self.SetSizer(vbox_top)
        wx.EVT_KEY_UP(self, self.OnCharUp)		

    def OnCharUp(self,event):
        keyid = event.GetKeyCode() 
        if keyid == wx.WXK_RETURN:
            self.EndModal(wx.ID_OK) 
        elif keyid == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL) 
            
    def getText(self):
        return self.txt.GetValue()


class StratTypeDialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, "Stratigraphy Type", size=(300, 130), style=wx.STAY_ON_TOP)

        self.Center()
        vbox_top = wx.BoxSizer(wx.VERTICAL)
        self.types = wx.ComboBox(self, -1, "Diatoms", (0,0), (250, -1), ("Diatoms", "Radioloria", "Foraminifera", "Nannofossils", "Paleomag"), wx.CB_DROPDOWN)

        vbox_top.Add(self.types, 0, wx.LEFT | wx.TOP, 25)

        grid = wx.GridSizer(1,2, gap=(0,0))
        okBtn = wx.Button(self, wx.ID_OK, "Chnage")
        grid.Add(okBtn, 0, wx.LEFT, 50)
        cancelBtn = wx.Button(self, wx.ID_CANCEL, "Cancel")
        grid.Add(cancelBtn, 0, wx.LEFT, 30)

        vbox_top.Add(grid, 0, wx.TOP, 15)

        self.SetSizer(vbox_top)
        wx.EVT_KEY_UP(self, self.OnCharUp)

    def OnCharUp(self,event):
        keyid = event.GetKeyCode() 
        if keyid == wx.WXK_RETURN:
            self.EndModal(wx.ID_OK) 
        elif keyid == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL) 



# constant tracking last-used option (total depth or section depth)
LAST_USE_TOTAL = True
class SetDepthDialog(wx.Dialog):
    def __init__(self, parent, totalDepth, sectionDepth, section):
        wx.Dialog.__init__(self, parent, -1, "Set Depth", style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP)
        
        global LAST_USE_TOTAL
        self.useTotal = LAST_USE_TOTAL
        
        # total depth panel
        tdPanel = wx.Panel(self, -1)
        self.totalRadio = wx.RadioButton(tdPanel, -1, "Total Depth:")
        self.totalRadio.Bind(wx.EVT_RADIOBUTTON, self.totalRadioClicked)
        
        fieldSize = (70,-1) # brgtodo: fields always come out too wide without manual sizing
        self.totalDepth = wx.TextCtrl(tdPanel, -1, str(totalDepth), size=fieldSize)
        tdsz = wx.BoxSizer(wx.HORIZONTAL)
        tdsz.Add(self.totalRadio, 0, wx.ALIGN_CENTER_VERTICAL)
        tdsz.Add(self.totalDepth, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        tdsz.Add(wx.StaticText(tdPanel, -1, "m"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 2)
        tdPanel.SetSizer(tdsz)
        
        # section depth panel
        sdPanel = wx.Panel(self, -1)
        self.sectionRadio = wx.RadioButton(sdPanel, -1, "Section Depth:")
        self.sectionRadio.Bind(wx.EVT_RADIOBUTTON, self.sectionRadioClicked)
        self.sectionDepth = wx.TextCtrl(sdPanel, -1, str(sectionDepth), size=fieldSize)
        self.sectionNumber = wx.TextCtrl(sdPanel, -1, str(section),size=fieldSize)
        sdsz = wx.BoxSizer(wx.HORIZONTAL)
        sdsz.Add(self.sectionRadio, 0, wx.ALIGN_CENTER_VERTICAL)
        sdsz.Add(self.sectionDepth, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        sdsz.Add(wx.StaticText(sdPanel, -1, "cm"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 2)
        sdsz.Add(wx.StaticText(sdPanel, -1, "Section:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
        sdsz.Add(self.sectionNumber, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)
        sdPanel.SetSizer(sdsz)
        
        # button panel
        btnPanel = wx.Panel(self, -1)
        bsz = wx.BoxSizer(wx.HORIZONTAL)
        okBtn = wx.Button(btnPanel, wx.ID_OK, "Set Depth")
        okBtn.SetDefault()
        bsz.Add(okBtn, 1)
        bsz.Add(wx.Button(btnPanel, wx.ID_CANCEL, "Cancel"), 1, wx.LEFT, 10)
        btnPanel.SetSizer(bsz)
        
        sz = wx.BoxSizer(wx.VERTICAL)
        sz.Add(tdPanel, 1, wx.EXPAND | wx.ALL, 10)
        sz.Add(sdPanel, 1, wx.EXPAND | wx.ALL, 10)
        sz.Add(btnPanel, 1, wx.ALIGN_RIGHT | wx.ALIGN_BOTTOM | wx.ALL, 10)
        self.SetSizer(sz)
        self.Fit()
        
        self._updateRadios() # set initial radio state
        
    def totalRadioClicked(self, event):
        self.useTotal = True
        self._updateRadios()
        
    def sectionRadioClicked(self, event):
        self.useTotal = False
        self._updateRadios()
        
    def _updateRadios(self):
        self.totalRadio.SetValue(self.useTotal)
        self.sectionRadio.SetValue(not self.useTotal)
        global LAST_USE_TOTAL
        LAST_USE_TOTAL = self.useTotal
        self._updateFocus()

    def _updateFocus(self):
        if self.useTotal:
            self.totalDepth.SetFocus()
            self.totalDepth.SelectAll()
        else:
            self.sectionDepth.SetFocus()
            self.sectionDepth.SelectAll()


class AgeListDialog(wx.Dialog):
    def __init__(self, parent, active_list):
        wx.Dialog.__init__(self, parent, -1, "Selected Age List", size=(210, 200),style=wx.DEFAULT_DIALOG_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE | wx.STAY_ON_TOP)
        self.ageList = wx.ListBox(self, -1, (5,5),(200,100), "", style=wx.LB_HSCROLL|wx.LB_NEEDED_SB|wx.LB_EXTENDED)
        self.Bind(wx.EVT_LISTBOX, self.OnSelect, self.ageList)
        self.selectedNo =  -1 

        idx = 0
        for age in active_list:
            self.ageList.InsertItems([str(age)], idx)
            idx += 1

        wx.Button(self, wx.ID_OK, "Select", ((25, 135)))
        wx.Button(self, wx.ID_CANCEL, "Cancel", ((110, 135)))
        wx.EVT_KEY_UP(self, self.OnCharUp)

    def OnCharUp(self,event):
        keyid = event.GetKeyCode() 
        if keyid == wx.WXK_RETURN:
            self.EndModal(wx.ID_OK) 
        elif keyid == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL) 

    def OnSelect(self, event):
        for i in range(self.ageList.GetCount()):
            if self.ageList.IsSelected(i) == True:
                self.selectedNo = i 
                return

# Save dialog used in 3.0. Largely a duplicate of unused Message3Button
# with a few modifications. Shameful, but time is short.
class SaveDialog(wx.Dialog):
    def __init__(self, parent, msg, enableUpdateExisting):
        wx.Dialog.__init__(self, parent, -1, "About", style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP)

        self.Center()
        vbox_top = wx.BoxSizer(wx.VERTICAL)
        panel1 = wx.Panel(self, -1)
        sizer = wx.FlexGridSizer(1, 2, gap=(0,0))
        bmp = wx.StaticBitmap(panel1, -1, load_bmp_resource('icons/help-32x32.png'))
        sizer.Add(bmp, 0, wx.LEFT | wx.TOP, 9)
        sizer.Add(wx.StaticText(panel1, -1, msg), 0, wx.LEFT | wx.TOP | wx.BOTTOM, 15)
        panel1.SetSizer(sizer)
        vbox_top.Add(panel1)

        grid = wx.BoxSizer(wx.HORIZONTAL)
        okBtn = wx.Button(self, wx.ID_YES, "Create New")
        self.Bind(wx.EVT_BUTTON, self.OnYES, okBtn)
        grid.Add(okBtn, 1, wx.LEFT | wx.RIGHT, 5)
        noBtn = wx.Button(self, wx.ID_OK, "Update Existing")
        grid.Add(noBtn, 1, wx.LEFT | wx.RIGHT, 5)
        noBtn.Enable(enableUpdateExisting)
        cancelBtn = wx.Button(self, wx.ID_CANCEL, "Cancel")
        grid.Add(cancelBtn, 1, wx.LEFT | wx.RIGHT, 5)
        vbox_top.Add(grid, 0, wx.ALIGN_RIGHT | wx.ALL, 10)

        self.SetSizer(vbox_top)
        self.GetSizer().Fit(self)
        self.Bind(wx.EVT_KEY_UP, self.OnCharUp)

    def OnYES(self, event):
        self.EndModal(wx.ID_YES)

    def OnCharUp(self,event):
        keyid = event.GetKeyCode() 
        if keyid == wx.WXK_RETURN:
            self.EndModal(wx.ID_OK) 
        elif keyid == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL) 


# Unused.
class SaveTableDialog(wx.Dialog):
    def __init__(self, parent, id, affine, splice):
        wx.Dialog.__init__(self, parent, id, "Save", size=(340, 180),style= wx.DEFAULT_DIALOG_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE | wx.STAY_ON_TOP)

        wx.StaticText(self, -1, 'Check to Save to Data Manager', (50, 10))
        panel = wx.Panel( self, -1, (10, 30), size=(320, 40), style=wx.BORDER)

        self.affineCheck = wx.CheckBox(panel, -1, 'Affine Table', (10, 10))
        self.affineCheck.SetValue(affine)
        self.affineUpdate = wx.RadioButton(panel, -1, "Update", (120, 10), style=wx.RB_GROUP)
        self.affineUpdate.SetValue(True)
        wx.RadioButton(panel, -1, "Create New", (190, 10))

        panel1 = wx.Panel ( self, -1, (10, 75), size=(320, 40), style=wx.BORDER)
        self.spliceCheck = wx.CheckBox(panel1, -1, 'Splice Table', (10, 10))
        self.spliceCheck.SetValue(splice)
        self.spliceUpdate = wx.RadioButton(panel1, -1, "Update", (120, 10), style=wx.RB_GROUP)
        self.spliceUpdate.SetValue(True)
        wx.RadioButton(panel1, -1, "Create New", (190, 10))

        # panel2 = wx.Panel ( self, -1, (10, 120), size=(320, 40), style=wx.BORDER)
        # self.eldCheck = wx.CheckBox(panel2, -1, 'ELD Table', (10, 10))
        # self.eldUpdate = wx.RadioButton(panel2, -1, "Update", (120, 10), style=wx.RB_GROUP)
        # self.eldUpdate.SetValue(True)
        # wx.RadioButton(panel2, -1, "Create New", (190, 10))

        # panel3 = wx.Panel ( self, -1, (10, 165), size=(320, 40), style=wx.BORDER)
        # self.ageCheck = wx.CheckBox(panel3, -1, 'Age/Depth', (10, 10))
        # self.ageUpdate = wx.RadioButton(panel3, -1, "Update", (120, 10), style=wx.RB_GROUP)
        # self.ageUpdate.SetValue(True)
        # wx.RadioButton(panel3, -1, "Create New", (190, 10))

        # panel4 = wx.Panel ( self, -1, (10, 210), size=(320, 40), style=wx.BORDER)
        # self.seriesCheck = wx.CheckBox(panel4, -1, 'Age Model', (10, 10))
        # self.seriesUpdate = wx.RadioButton(panel4, -1, "Update", (120, 10), style=wx.RB_GROUP)
        # self.seriesUpdate.SetValue(True)
        # wx.RadioButton(panel4, -1, "Create New", (190, 10))

        wx.Button(self, wx.ID_OK, "Save", ((85,120))) #((85, 265)))
        wx.Button(self, wx.ID_CANCEL, "Cancel", ((180,120))) #((180, 265)))
        wx.EVT_KEY_UP(self, self.OnCharUp)

    def OnCharUp(self,event):
        keyid = event.GetKeyCode() 
        if keyid == wx.WXK_RETURN:
            self.EndModal(wx.ID_OK) 
        elif keyid == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL)

class OkButtonPanel(wx.Panel):
    def __init__(self, parent, okOnly=False, okName="OK", cancelName="Cancel"):
        wx.Panel.__init__(self, parent, -1)
        self.ok = wx.Button(self, wx.ID_OK, okName)
        self.ok.SetDefault()
        sz = wx.BoxSizer(wx.HORIZONTAL)
        if not okOnly:
            self.cancel = wx.Button(self, wx.ID_CANCEL, cancelName)
            sz.Add(self.cancel, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10)
        sz.Add(self.ok, 0, wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, 5)
        self.SetSizer(sz)

class FormatListPanel(wx.Panel):
    def __init__(self, parent, formatChoices=None):
        wx.Panel.__init__(self, parent, -1)
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "Export Format:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM | wx.RIGHT, 5)
        formats = formatChoices if formatChoices is not None else ["CSV", "XML", "Text"] 
        self.formatList = wx.Choice(self, -1, choices=formats)
        self.formatList.SetSelection(0)
        sz.Add(self.formatList, 1, wx.EXPAND | wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, 5)
        self.SetSizer(sz)

class AffineListPanel(wx.Panel):
    def __init__(self, parent, affineItems):
        wx.Panel.__init__(self, parent, -1)
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "Apply Affine:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM | wx.RIGHT, 5)
        self.affineList = wx.Choice(self, -1)
        sz.Add(self.affineList, 1, wx.EXPAND | wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, 5)
        self.affineList.Append("[None]")
        for item in affineItems:
            self.affineList.Append(item)
        self.SetSizer(sz)
        
class SpliceListPanel(wx.Panel):
    def __init__(self, parent, spliceItems, none_item=True):
        wx.Panel.__init__(self, parent, -1)
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "Apply Splice:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM | wx.RIGHT, 5)
        self.spliceList = wx.Choice(self, -1)
        sz.Add(self.spliceList, 1, wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, 5)
        if none_item:
            self.spliceList.Append("[None]")
        for item in spliceItems:
            self.spliceList.Append(item)
        self.SetSizer(sz)


class ExportFormatDialog(wx.Dialog):
    def __init__(self, parent, title="Select Export Format"):
        wx.Dialog.__init__(self, parent, -1, title, style=wx.DEFAULT_DIALOG_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE | wx.RESIZE_BORDER | wx.STAY_ON_TOP)

        sz = wx.BoxSizer(wx.VERTICAL)
        formatPanel = FormatListPanel(self)
        self.formatList = formatPanel.formatList
        sz.Add(formatPanel, 0, wx.EXPAND | wx.ALL, 10)
        self.buttonPanel = OkButtonPanel(self, okName="Export")
        sz.Add(self.buttonPanel, 0, wx.ALIGN_RIGHT | wx.ALIGN_BOTTOM | wx.RIGHT | wx.LEFT, 10)
        self.SetSizerAndFit(sz)
        
        self.buttonPanel.ok.SetDefault()
        self.Bind(wx.EVT_BUTTON, self.ButtonPressed, self.buttonPanel.ok)
        self.Bind(wx.EVT_BUTTON, self.ButtonPressed, self.buttonPanel.cancel)
        
        self.formatList.SetStringSelection("CSV")

    def GetSelectedFormat(self):
        return self.formatList.GetStringSelection()
        
    def ButtonPressed(self, evt):
        if evt.GetEventObject() == self.buttonPanel.ok:
            self.EndModal(wx.ID_OK)
        else:
            self.EndModal(wx.ID_CANCEL)


class ExportSpliceDialog(wx.Dialog):
    def __init__(self, parent, affineItems, initialSelection=None):
        wx.Dialog.__init__(self, parent, -1, "Export Splice", style= wx.DEFAULT_DIALOG_STYLE |wx.NO_FULL_REPAINT_ON_RESIZE | wx.RESIZE_BORDER | wx.STAY_ON_TOP)

        sz = wx.BoxSizer(wx.VERTICAL)
        formatPanel = FormatListPanel(self, formatChoices=["CSV", "Text"])
        self.formatList = formatPanel.formatList
        sz.Add(formatPanel, 0, wx.EXPAND | wx.ALL, 5)
        hsz = wx.BoxSizer(wx.HORIZONTAL)
        hsz.Add(wx.StaticText(self, -1, "Splice Format:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM | wx.RIGHT, 5)
        self.spliceFormatChoice = wx.Choice(self, -1, choices=["Interval Table", "Tie Table"])
        self.spliceFormatChoice.SetSelection(0)
        hsz.Add(self.spliceFormatChoice, 1,  wx.EXPAND | wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, 5)
        sz.Add(hsz, 0, wx.EXPAND | wx.RIGHT | wx.LEFT | wx.BOTTOM, 5)
        affinePanel = AffineListPanel(self, affineItems)
        self.affineList = affinePanel.affineList
        sz.Add(affinePanel, 0, wx.EXPAND | wx.RIGHT | wx.LEFT | wx.BOTTOM, 10)
        self.buttonPanel = OkButtonPanel(self, okName="Export")
        sz.Add(self.buttonPanel, 0, wx.ALIGN_RIGHT | wx.ALIGN_BOTTOM | wx.RIGHT, 10)
        self.SetSizerAndFit(sz)
        
        self.buttonPanel.ok.SetDefault()
        self.Bind(wx.EVT_BUTTON, self.ButtonPressed, self.buttonPanel.ok)
        self.Bind(wx.EVT_BUTTON, self.ButtonPressed, self.buttonPanel.cancel)
        
        if initialSelection is not None:
            self.affineList.SetStringSelection(initialSelection)

    def GetSelectedAffine(self):
        return self.affineList.GetStringSelection()
    
    def GetSelectedFormat(self):
        return self.formatList.GetStringSelection()
    
    def GetExportSIT(self):
        return self.spliceFormatChoice.GetStringSelection() == "Interval Table"
        
    def ButtonPressed(self, evt):
        if evt.GetEventObject() == self.buttonPanel.ok:
            self.EndModal(wx.ID_OK)
        else:
            self.EndModal(wx.ID_CANCEL)


class ExportSpliceImageDialog(wx.Dialog):
    def __init__(self, parent, spliceFiles, initialDir):
        self.initialDir = initialDir
        self.outpath = None
        self.outfile = None
        wx.Dialog.__init__(self, parent, -1, "Export Spliced Image", style=wx.DEFAULT_DIALOG_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE | wx.STAY_ON_TOP)

        panel = wx.Panel(self, -1)
        psz = wx.BoxSizer(wx.VERTICAL)
        splicePanel = SpliceListPanel(panel, spliceFiles, none_item=False)
        self.spliceList = splicePanel.spliceList
        psz.Add(splicePanel, 0, wx.EXPAND | wx.BOTTOM, 10)
        self.showSectionLines = wx.CheckBox(panel, -1, "Show Section Boundaries")
        self.showIntervalLines = wx.CheckBox(panel, -1, "Show Splice Interval Boundaries")
        self.showSectionNames = wx.CheckBox(panel, -1, "Show Section IDs")
        psz.Add(self.showSectionLines, 0, wx.BOTTOM, 5)
        psz.Add(self.showIntervalLines, 0, wx.BOTTOM, 5)
        psz.Add(self.showSectionNames, 0, wx.BOTTOM, 5)
        panel.SetSizer(psz)

        sz = wx.BoxSizer(wx.VERTICAL)
        sz.Add(panel, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        self.buttonPanel = OkButtonPanel(self, okName="Export")
        sz.Add(self.buttonPanel, 0, wx.ALIGN_RIGHT | wx.RIGHT, 10)
        self.SetSizerAndFit(sz)
        
        self.buttonPanel.ok.SetDefault()
        self.Bind(wx.EVT_BUTTON, self.ButtonPressed, self.buttonPanel.ok)
        self.Bind(wx.EVT_BUTTON, self.ButtonPressed, self.buttonPanel.cancel)

    def GetSelectedSplice(self):
        return self.spliceList.GetStringSelection()

    def GetOptions(self):
        options = {}
        options['sectionLines'] = self.showSectionLines.IsChecked()
        options['intervalLines'] = self.showIntervalLines.IsChecked()
        options['sectionNames'] = self.showSectionNames.IsChecked()
        return options
        
    def ButtonPressed(self, evt):
        if evt.GetEventObject() == self.buttonPanel.ok:
            spliceFile = self.GetSelectedSplice()
            dot_idx = spliceFile.rindex('.')
            filename = spliceFile[:dot_idx] + '.png'
            savedlg = wx.FileDialog(self, "Save Spliced Image", self.initialDir, defaultFile=filename, style=wx.FD_SAVE)
            if savedlg.ShowModal() == wx.ID_OK:
                self.outpath = savedlg.GetDirectory()
                self.outfile = savedlg.GetFilename()
                self.EndModal(wx.ID_OK)
            return
        else:
            self.EndModal(wx.ID_CANCEL)


class ExportELDDialog(wx.Dialog):
    def __init__(self, parent, affineItems, initialAffine, spliceItems, initialSplice):
        wx.Dialog.__init__(self, parent, -1, "Export Splice", size=(300, 200),style= wx.DEFAULT_DIALOG_STYLE |wx.NO_FULL_REPAINT_ON_RESIZE | wx.RESIZE_BORDER | wx.STAY_ON_TOP)

        sz = wx.BoxSizer(wx.VERTICAL)
        formatPanel = FormatListPanel(self)
        self.formatList = formatPanel.formatList
        sz.Add(formatPanel, 0, wx.EXPAND | wx.ALL, 10)
        affinePanel = AffineListPanel(self, affineItems)
        self.affineList = affinePanel.affineList
        sz.Add(affinePanel, 0, wx.EXPAND | wx.RIGHT | wx.LEFT | wx.BOTTOM, 10)
        splicePanel = SpliceListPanel(self, spliceItems)
        self.spliceList = splicePanel.spliceList
        sz.Add(splicePanel, 0, wx.EXPAND | wx.RIGHT | wx.LEFT | wx.BOTTOM, 10)
        self.buttonPanel = OkButtonPanel(self, okName="Export")
        sz.Add(self.buttonPanel, 0, wx.ALIGN_RIGHT | wx.ALIGN_BOTTOM | wx.RIGHT, 10)
        self.SetSizer(sz)
        
        self.buttonPanel.ok.SetDefault()
        self.Bind(wx.EVT_BUTTON, self.ButtonPressed, self.buttonPanel.ok)
        self.Bind(wx.EVT_BUTTON, self.ButtonPressed, self.buttonPanel.cancel)
        
        if initialAffine is not None:
            self.affineList.SetStringSelection(initialAffine)
        if initialSplice is not None:
            self.spliceList.SetStringSelection(initialSplice)

    def GetSelectedSplice(self):
        return self.spliceList.GetStringSelection()
    
    def GetSelectedAffine(self):
        return self.affineList.GetStringSelection()
    
    def GetSelectedFormat(self):
        return self.formatList.GetStringSelection()
        
    def ButtonPressed(self, evt):
        if evt.GetEventObject() == self.buttonPanel.ok:
            self.EndModal(wx.ID_OK)
        else:
            self.EndModal(wx.ID_CANCEL)


class ExportCoreDialog(wx.Dialog):
    # parent: parent window of dialog
    # enableAffine: boolean indicating whether or not to enable "Apply Affine" checkbox
    # enableSplice: boolean indicating whether or not to enable "Apply Splice" checkbox
    # holes: list of strings indicating hole(s) to be exported e.g. ['A', 'B', 'C']
    # siteName: string indicating export exp-site
    # datatype: string inidcating export datatype
    # spliceHoles: string combining all holes participating in enabled splice (if any) e.g. "ABD"
    def __init__(self, parent, enableAffine, enableSplice, holes, siteName, datatype, spliceHoles):
        wx.Dialog.__init__(self, parent, -1, "Export Core Data", style= wx.DEFAULT_DIALOG_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE | wx.RESIZE_BORDER | wx.STAY_ON_TOP)
        self.holes = holes
        self.siteName = siteName
        self.datatype = datatype
        self.spliceHoles = spliceHoles

        vbox = wx.BoxSizer(wx.VERTICAL)
        # vbox.Add(wx.StaticText(self, -1, 'Check to Export Core data'), 0, wx.TOP | wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 12)

        panel = wx.Panel(self, -1)
        vbox_opt = wx.BoxSizer(wx.HORIZONTAL)

        opt_panel = wx.Panel(panel, -1)
        sizer = wx.StaticBoxSizer(wx.StaticBox(opt_panel, -1, 'Export Options'), orient=wx.VERTICAL)

        self.cull = wx.CheckBox(opt_panel, -1, 'Apply Cull')
        # sizer.Add(self.cull, 1, wx.EXPAND)
        self.cull.SetValue(False)
        self.cull.Hide()

        # 2/26/2019: Hide unused items rather than removing them entirely since
        # the export process refers to them and I don't want to shake the jello further.
        self.affine = wx.CheckBox(opt_panel, -1, 'Apply Affine')
        self.affine.Show(True)
        sizer.Add(self.affine, 1)
        self.affine.Enable(enableAffine)
        self.splice = wx.CheckBox(opt_panel, -1, 'Apply Splice')
        self.splice.Show(True)
        sizer.Add(self.splice, 1, wx.BOTTOM, 5)
        self.splice.Enable(enableSplice)
        opt_panel.Bind(wx.EVT_CHECKBOX, self.OnSplice, self.splice)
        opt_panel.Bind(wx.EVT_CHECKBOX, self.OnAffine, self.affine)

        self.eld = wx.CheckBox(opt_panel, -1, 'Apply ELD')
        self.eld.Show(False)
        # sizer.Add(self.eld, 1)
        opt_panel.Bind(wx.EVT_CHECKBOX, self.OnELD, self.eld)

        self.age = wx.CheckBox(opt_panel, -1, 'Apply Age Model')
        self.age.Show(False)
        # sizer.Add(self.age, 1)
        #opt_panel.Bind(wx.EVT_CHECKBOX, self.OnAGE, self.age)

        self.prefix = wx.TextCtrl(opt_panel, -1)
        self.suffix = wx.TextCtrl(opt_panel, -1)
        prefixSizer = wx.BoxSizer(wx.HORIZONTAL)
        prefixSizer.Add(wx.StaticText(opt_panel, -1, "Output File Prefix:"), 0, wx.ALIGN_CENTER_VERTICAL)
        prefixSizer.Add(self.prefix, 1, wx.EXPAND | wx.ALL, 5)
        self.Bind(wx.EVT_TEXT, self.UpdateOutputFiles, self.prefix)
        sizer.Add(prefixSizer, 0, wx.EXPAND)
        suffixSizer = wx.BoxSizer(wx.HORIZONTAL)
        suffixSizer.Add(wx.StaticText(opt_panel, -1, "Output File Suffix:"), 0, wx.ALIGN_CENTER_VERTICAL)
        suffixSizer.Add(self.suffix, 1, wx.EXPAND | wx.ALL, 5)
        self.Bind(wx.EVT_TEXT, self.UpdateOutputFiles, self.suffix)
        sizer.Add(suffixSizer, 0, wx.EXPAND)

        opt_panel.SetSizer(sizer)
        vbox_opt.Add(opt_panel, 1, wx.EXPAND)
        panel.SetSizer(vbox_opt)
        vbox.Add(panel, 0, wx.EXPAND | wx.ALL, 10)

        # Output Files options
        outputPanel = wx.Panel(self, -1)
        outputSizer = wx.StaticBoxSizer(wx.StaticBox(outputPanel, -1, 'Output File Names'), orient=wx.VERTICAL)

        self.fileTextControls = [wx.StaticText(outputPanel, -1, self._outputFileName(h)) for h in self.holes]
        for ftc in self.fileTextControls:
            outputSizer.Add(ftc)

        outputPanel.SetSizer(outputSizer)
        vbox.Add(outputPanel, 0, wx.EXPAND | wx.ALL, 10)

        btnPanel = wx.Panel(self, -1)
        okBtn = wx.Button(btnPanel, wx.ID_OK, "Export")
        cancelBtn = wx.Button(btnPanel, wx.ID_CANCEL, "Cancel")
        bsz = wx.BoxSizer(wx.HORIZONTAL)
        bsz.Add(okBtn, 1, wx.ALIGN_CENTER_VERTICAL, 5)
        bsz.Add(cancelBtn, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        btnPanel.SetSizer(bsz)
        vbox.Add(btnPanel, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 5)
        
        wx.EVT_KEY_UP(self, self.OnCharUp)
        
        self.SetSizer(vbox)
        self.Fit() # fit dialog to controls, otherwise lower half will be obscured
        self.SetSize((500, -1)) # expand width only, to allow space for prefixes/suffixes

    # Update list of output filenames to reflect current options
    def UpdateOutputFiles(self, event):
        if self.splice.GetValue():
            spliceFile = self._outputFileName(self.spliceHoles)
            self.fileTextControls[0].SetLabel(spliceFile)
            for ftc in self.fileTextControls[1:]:
                ftc.SetLabel("")
        else:
            for index, ftc in enumerate(self.fileTextControls):
                ftc.SetLabel(self._outputFileName(self.holes[index]))

    # Return list of output filenames based on current options
    def GetOutputFiles(self):
        return [ftc.GetLabel() for ftc in self.fileTextControls]

    # Return filename of format
    # [optional prefix]-site-hole(s)_datatype_[RAW/SHIFTED/SPLICED]-[optional suffix].csv
    # hole: string indicating hole (or holes in the case of splice e.g. "ABD")
    def _outputFileName(self, hole):
        prefix = self.prefix.GetValue() + "-" if len(self.prefix.GetValue()) > 0 else ""
        suffix = "-" + self.suffix.GetValue() if len(self.suffix.GetValue()) > 0 else ""
        return "{}{}-{}_{}_{}{}.csv".format(prefix, self.siteName, hole, self.datatype, self._getExportType(), suffix)

    # Return string corresponding to currently-applied affine and splice, if any
    def _getExportType(self):
        if not self.affine.GetValue() and not self.splice.GetValue():
            exportType = "RAW"
        elif self.affine.GetValue() and not self.splice.GetValue():
            exportType = "SHIFTED"
        else:
            exportType = "SPLICED"
        return exportType

    def OnCharUp(self,event):
        keyid = event.GetKeyCode() 
        if keyid == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL)

    # Affine must be applied to apply splice. Uncheck splice box
    # if affine box is unchecked to enforce this.
    def OnAffine(self, event):
        applyAffine = self.affine.GetValue()
        if not applyAffine and self.splice.GetValue():
            self.splice.SetValue(False)
        self.UpdateOutputFiles(None)

    # Affine must be applied to apply splice. Check affine box if needed
    # when splice box is checked.
    def OnSplice(self, event):
        if self.splice.GetValue():
            self.affine.SetValue(True)
        self.UpdateOutputFiles(None)

    def OnELD(self, event):
        ret = self.eld.GetValue()
        self.affine.SetValue(ret)
        #self.splice.SetValue(ret)

    def OnAGE(self, event):
        ret = self.age.GetValue()
        self.affine.SetValue(ret)


class AltSpliceDialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, "View Alternate Splice", size=(360, 200),style=wx.DEFAULT_DIALOG_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE | wx.STAY_ON_TOP)
        panel = wx.Panel(self, -1, (15, 15), size=(330, 100), style=wx.BORDER)
        wx.StaticText(panel, -1, 'Data Type', (10, 20))
        wx.StaticText(panel, -1, 'Splice', (10, 60))
        self.all = wx.Choice(panel, -1, (90,20), (220,-1))
        for types in parent.Window.range:
            if types[0] != "splice" and types[0] != "altsplice":
                typename = types[0]
                if typename == "NaturalGamma":
                    typename = "Natural Gamma"
                self.all.Append(typename)
        if self.all.GetCount() > 0:
            self.all.Select(0)

        self.splice = wx.Choice(panel, -1, (90,60), (220,-1))
        parent.dataFrame.Update_PROPERTY_ITEM(parent.dataFrame.selectBackup)
        property = parent.dataFrame.propertyIdx
        totalcount = parent.dataFrame.tree.GetChildrenCount(property, False)
        if totalcount > 0:
            child = parent.dataFrame.tree.GetFirstChild(property)
            child_item = child[0]
            if parent.dataFrame.tree.GetItemText(child_item, 1) == "SPLICE":
                filename = parent.dataFrame.tree.GetItemText(child_item, 8)
                self.splice.Append(filename)
            for k in range(1, totalcount):
                child_item = parent.dataFrame.tree.GetNextSibling(child_item)
                if parent.dataFrame.tree.GetItemText(child_item, 1) == "SPLICE":
                    self.splice.Append(parent.dataFrame.tree.GetItemText(child_item, 8))
        if self.splice.GetCount() > 0:
            self.splice.Select(0)

        self.selectedType = "" 
        self.selectedSplice = "" 
        okBtn = wx.Button(self, -1, "Select", (70, 135))
        self.Bind(wx.EVT_BUTTON, self.OnSELECT, okBtn)
        cancelBtn = wx.Button(self, wx.ID_CANCEL, "Cancel", (210, 135))
        wx.EVT_KEY_UP(self, self.OnCharUp)

    def OnCharUp(self,event):
        keyid = event.GetKeyCode() 
        if keyid == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL) 

    def OnSELECT(self, event):
        self.selectedSplice = self.splice.GetStringSelection()
        self.selectedType = self.all.GetStringSelection() 
        self.EndModal(wx.ID_OK) 


class CommentTextCtrl(wx.TextCtrl):
    def __init__(self, parent, wxid, value=wx.EmptyString, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        wx.TextCtrl.__init__(self, parent, wxid, value, pos, size, style)
        self.Bind(wx.EVT_CHAR, self._prohibitCommas)

    # for unambiguous CSV output, don't allow commas in comment field
    def _prohibitCommas(self, evt):
        try:
            if chr(evt.GetKeyCode()) != ',':
                evt.Skip()
        except ValueError: # handle key code out of 0-255 range (e.g arrow keys)
            print("Can't convert key code {} to char".format(evt.GetKeyCode()))
            evt.Skip()

# adjust a core's MCD based on a percentage or a fixed distance,
# resulting in an affine shift of type SET
class SetDialog(wx.Dialog):
    def __init__(self, parent):
        self.parent = parent
        self.coreData = {}
        self.lastHole = -1
        self.HoleData = self.parent.Window.HoleData
        
        # vars for output
        self.outHole = ""
        self.outCore = ""
        self.outCoreList = [] # list of all cores in current hole
        self.outType = None # datatype
        self.outRate = None
        self.outOffset = 0
        self.outComment = ""

        wx.Dialog.__init__(self, parent, -1, "SET", size=(300,360), style=wx.DEFAULT_DIALOG_STYLE |
                           wx.NO_FULL_REPAINT_ON_RESIZE | wx.STAY_ON_TOP)
        self.SetBackgroundColour(wx.WHITE)
        dlgSizer = wx.BoxSizer(wx.VERTICAL)

        coreSizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, "Apply shift to:"), orient=wx.VERTICAL)
        hsz = wx.BoxSizer(wx.HORIZONTAL)
        self.holeText = wx.StaticText(self, -1, "Hole:")
        hsz.Add(self.holeText, 0, wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, 5)
        self.holeChoice = wx.Choice(self, -1, size=(70,-1))
        hsz.Add(self.holeChoice, 0, wx.ALL, 5)
        self.coreChoice = wx.Choice(self, -1, size=(70,-1))
        self.coreText = wx.StaticText(self, -1, "Core:")
        hsz.Add(self.coreText, 0, wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, 5)
        hsz.Add(self.coreChoice, 0, wx.ALL, 5)
        coreSizer.Add(hsz, 0, wx.EXPAND)		

        self.coreAndBelow = wx.RadioButton(self, -1, "Selected core and all untied cores below in this hole", style=wx.RB_GROUP)
        self.coreOnly = wx.RadioButton(self, -1, "Selected core only")

        chainSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.coreAndChain = wx.RadioButton(self, -1, "Entire TIE chain starting from core:")
        self.rootCoreChoice = wx.Choice(self, -1)
        self.rootCoreChoice.Enable(False)
        chainSizer.Add(self.coreAndChain, 0, wx.EXPAND | wx.RIGHT, 5)
        chainSizer.Add(self.rootCoreChoice, 0)

        self.coreAndBelow.SetValue(True)
        coreSizer.Add(self.coreAndBelow, 0, wx.EXPAND | wx.TOP, 5)
        coreSizer.Add(self.coreOnly, 0, wx.EXPAND | wx.TOP, 5)
        coreSizer.Add(chainSizer, 0, wx.EXPAND | wx.TOP, 5)
        
        methodSizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, "Shift by:"), orient=wx.VERTICAL)
        hsz = wx.BoxSizer(wx.HORIZONTAL)
        distSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.distRadio = wx.RadioButton(self, -1, "Distance from current offset(s)", style=wx.RB_GROUP)
        self.distRadio.SetValue(True)
        self.distField = wx.TextCtrl(self, -1, "0.0", size=(70,-1))
        distSizer.Add(self.distRadio, 0, wx.RIGHT, 5)
        distSizer.Add(self.distField)
        distSizer.Add(wx.StaticText(self, -1, "m"), 0, wx.LEFT, 3)
        self.percentRadio = wx.RadioButton(self, -1, "Percent of original CSF-A depth(s)")
        self.percentField = wx.TextCtrl(self, -1, "10.0", size=(70,-1))
        pctSizer = wx.BoxSizer(wx.HORIZONTAL)
        pctSizer.Add(self.percentRadio, 0, wx.RIGHT, 5)
        pctSizer.Add(self.percentField)
        self.percentLabel = wx.StaticText(self, -1, "%")
        pctSizer.Add(self.percentLabel, 0, wx.LEFT, 3)
        methodSizer.Add(hsz, 0, wx.EXPAND | wx.BOTTOM, 5)
        methodSizer.Add(distSizer, 0, wx.BOTTOM, 5)
        methodSizer.Add(pctSizer, 0)
        
        self.currentShiftText = wx.StaticText(self, -1, "Current shift:")
        methodSizer.Add(self.currentShiftText, 0, wx.EXPAND | wx.TOP, 5)

        commentSizer = wx.BoxSizer(wx.HORIZONTAL)
        commentSizer.Add(wx.StaticText(self, -1, "Comment:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.commentField = CommentTextCtrl(self, -1)
        commentSizer.Add(self.commentField, 1, wx.EXPAND)

        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.cancelButton = wx.Button(self, wx.ID_CANCEL, "Cancel")
        self.applyButton = wx.Button(self, wx.ID_OK, "Apply")
        buttonSizer.Add(self.cancelButton, 0, wx.ALL, 5)
        buttonSizer.Add(self.applyButton, 0, wx.ALL, 5)

        dlgSizer.Add(coreSizer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)
        dlgSizer.Add(methodSizer, 0, wx.ALL | wx.EXPAND, 5)
        dlgSizer.Add(commentSizer, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND, 10)
        dlgSizer.Add(buttonSizer, 0, wx.ALIGN_RIGHT | wx.ALL, border=5)
    
        self.SetSizer(dlgSizer)
        self.Fit()

        self.InitChoices()
        self.InitChainRoots()

        self.Bind(wx.EVT_CHOICE, self.UpdateCoreChoice, self.holeChoice)
        self.Bind(wx.EVT_CHOICE, self.UpdateData, self.coreChoice)
        self.Bind(wx.EVT_BUTTON, self.OnApply, self.applyButton)
        self.Bind(wx.EVT_RADIOBUTTON, self.MethodRadioChanged, self.coreAndBelow)
        self.Bind(wx.EVT_RADIOBUTTON, self.MethodRadioChanged, self.coreAndChain)
        self.Bind(wx.EVT_RADIOBUTTON, self.MethodRadioChanged, self.coreOnly)
        self.Bind(wx.EVT_RADIOBUTTON, self.UpdateData, self.percentRadio)
        self.Bind(wx.EVT_RADIOBUTTON, self.UpdateData, self.distRadio)
        self.Bind(wx.EVT_TEXT, self.UpdateData, self.percentField)
        self.Bind(wx.EVT_TEXT, self.UpdateData, self.distField)

    def OnApply(self, evt):
        # gather and validate distance/percentage input
        try:
            # self.distField is a delta from the current affine shift, but SET
            # logic expects the total shift from its CSF-A (unshifted) depth, thus
            # we return the sum of the current shift and the value of distField.
            self.outOffset = self.curCoreShift + float(self.distField.GetValue())
        except ValueError:
            self.parent.OnShowMessage("Error", "Invalid distance {}".format(self.distField.GetValue()), 1)
            return
        try:
            self.outRate = float(self.percentField.GetValue())/100.0 + 1.0
        except ValueError:
            self.parent.OnShowMessage("Error", "Invalid percentage {}".format(self.percentField.GetValue()), 1)
            return

        # str() to convert from type unicode
        if self.coreAndChain.GetValue():
            hcstr = str(self.rootCoreChoice.GetStringSelection())
            charNumPattern = "([A-Z]+)([0-9]+)"
            hc_items = re.match(charNumPattern, hcstr)
            if hc_items and len(hc_items.groups()) == 2:
                self.outHole = hc_items.groups()[0]
                self.outCore = hc_items.groups()[1]
            else:
                # In the unlikely event someone got this far with non-standard hole and core naming,
                # notify and refuse to proceed with this method.
                errstr = "Couldn't parse hole-core string {}, expected alphabetic hole (A-Z) and numeric core (1+)".format(hcstr)
                self.parent.OnShowMessage("Error", errstr, 1)
                return
        else:
            self.outHole = str(self.holeChoice.GetStringSelection())
            self.outCore = str(self.coreChoice.GetStringSelection())

        self.outComment = self.commentField.GetValue()
        # self.outType already set
        self.EndModal(wx.ID_OK)

    # Populate self.coreData with loaded holes and cores
    def InitChoices(self):
        self.coreData = {}
        self.holeChoice.Clear()
        coreDict = {}
        for hole in self.HoleData:
            if self.outType == None:
                self.outType = hole[0][0][2]
            holeName = hole[0][0][7]
            if holeName not in coreDict:
                coreDict[holeName] = {}
                self.holeChoice.Append(holeName)

            # gather core data: core sets may be inconsistent for different datatypes in same hole
            mbsfVals = []
            mcdVals = []
            for core in hole[0][1:len(hole[0])]:
                coreName = core[0]
                if coreName not in coreDict[holeName]:
                    mcd = core[9][0] # first element in section depth list
                    mcdVals.append(mcd)
                    mbsf = mcd - core[5] # offset
                    mbsfVals.append(mbsf)
                    coreDict[holeName][coreName] = (coreName, mbsf, mcd)

        # update self.coreData
        for hole in coreDict:
            self.coreData[hole] = []
            s = sorted(coreDict[hole], key=int)
            for key in s:
                self.coreData[hole].append(coreDict[hole][key])
                
        if self.holeChoice.GetCount() > 0:
            self.holeChoice.Select(0)
            self.UpdateCoreChoice()

    # Populate self.rootCoreChoice with TIE chain roots, or disable
    # chain root controls if no roots exist.
    def InitChainRoots(self):
        roots = self.parent.affineManager.getChainRoots()
        if len(roots) > 0:
            for crstr in sorted([cr[0] + cr[1] for cr in roots]):
                self.rootCoreChoice.Append(crstr)
        else:
            self.coreAndChain.Enable(False)
            self.rootCoreChoice.Enable(False)

    # Update core dropdown with available cores for currently-selected hole
    def UpdateCoreChoice(self, evt=None):
        curHoleIndex = self.holeChoice.GetSelection()
        if self.lastHole == curHoleIndex:
            return
        self.lastHole = curHoleIndex
        self.coreChoice.Clear()
        curHoleStr = self.holeChoice.GetStringSelection()
        for coreTuple in self.coreData[curHoleStr]:
            self.coreChoice.Append(coreTuple[0])
            self.outCoreList.append(coreTuple[0])
        if self.coreChoice.GetCount() > 0:
            self.coreChoice.Select(0)
            self.UpdateData()

    # Enable/disable controls based on 'Entire TIE chain...' radio state.
    def MethodRadioChanged(self, evt=None):
        chainSelected = self.coreAndChain.GetValue()
        if chainSelected:
            if self.percentRadio.GetValue():
                self.distRadio.SetValue(True)
            self.UpdateData()

        self.rootCoreChoice.Enable(chainSelected) # only enabled if chain radio is selected

        # percent and hole/core dropdowns aren't used in chain SET, disable if selected
        self.holeText.Enable(not chainSelected)
        self.holeChoice.Enable(not chainSelected)
        self.coreText.Enable(not chainSelected)
        self.coreChoice.Enable(not chainSelected)
        self.percentRadio.Enable(not chainSelected)
        self.percentField.Enable(not chainSelected)
        self.percentLabel.Enable(not chainSelected)

    # Based on selected hole/core pair or chain root, udpate current core shift text.
    # For multi-core non-chain root shift, update list of affected cores in self.outCoreList.
    def UpdateData(self, evt=None):
        if self.coreAndChain.GetValue(): # root of TIE chain selected
            rootCore = self.rootCoreChoice.GetStringSelection()
            holeCorePattern = re.compile("([A-Z]+)([0-9]+)")
            match = holeCorePattern.match(rootCore)
            curHole, coreName = match.group(1), match.group(2)
            coreIndex = self.coreChoice.FindString(coreName)
            curCore = self.coreData[curHole][coreIndex]
            self.curCoreName = rootCore
        else:
            curHole = self.holeChoice.GetStringSelection()
            coreIndex = self.coreChoice.GetSelection()
            curCore = self.coreData[curHole][coreIndex]
            self.curCoreName = curHole + self.coreChoice.GetStringSelection()
        self.curCoreShift = curCore[2] - curCore[1]
        
        if self.coreAndBelow.GetValue(): # outCoreList is unused for single-core and chain root SETs
            self.outCoreList = []
            for coreTuple in [ct for ct in self.coreData[curHole] if int(ct[0]) >= int(self.coreChoice.GetStringSelection())]:
                self.outCoreList.append(coreTuple[0])

        self.UpdateCurShiftText()
    
    def UpdateCurShiftText(self):
        if self.curCoreName is not None:
            self.currentShiftText.SetLabel("Current " + self.curCoreName + " affine shift: " + str(self.curCoreShift))


class CorrParamsDialog(wx.Dialog):
    def __init__(self, parent, minDepthStep, depthStep, winLength, leadLag):
        wx.Dialog.__init__(self, parent, -1, "Correlation Parameters", size=(280,170), style=wx.CAPTION | wx.STAY_ON_TOP)
        
        self.minDepthStep = minDepthStep
        
        paramPanel = wx.Panel(self, -1)
        sz = wx.FlexGridSizer(3, 2, gap=(5,5))
        sz.Add(wx.StaticText(paramPanel, -1, 'Interpolated Depth Step (m):'), 0, wx.ALIGN_CENTER_VERTICAL)
        self.depthStep = wx.TextCtrl(paramPanel, -1, str(depthStep), size=(70,-1))
        sz.Add(self.depthStep, 1)
        sz.Add(wx.StaticText(paramPanel, -1, 'Correlation Window Length:'),  0, wx.ALIGN_CENTER_VERTICAL)
        self.winLength = wx.TextCtrl(paramPanel, -1, str(winLength), size=(70,-1))
        sz.Add(self.winLength, 1)
        sz.Add(wx.StaticText(paramPanel, -1, 'Correlation Lead/Lag:'), 0, wx.ALIGN_CENTER_VERTICAL)
        self.leadLag = wx.TextCtrl(paramPanel, -1, str(leadLag), size=(70,-1))
        sz.Add(self.leadLag, 1)
        paramPanel.SetSizer(sz)
        
        # brgtodo 9/4/2014: CreateButtonSizer() for default OK/Cancel/etc button panel creation?
        buttonPanel = wx.Panel(self, -1)
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.cancelButton = wx.Button(buttonPanel, wx.ID_CANCEL, "Cancel")
        self.applyButton = wx.Button(buttonPanel, wx.ID_OK, "Apply")
        self.applyButton.SetDefault()
        buttonSizer.Add(self.cancelButton, 0, wx.ALL, 5)
        buttonSizer.Add(self.applyButton, 0, wx.ALL, 5)
        buttonPanel.SetSizer(buttonSizer)
        
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self.GetSizer().Add(paramPanel, 1, wx.EXPAND | wx.ALL, 5)
        self.GetSizer().Add(buttonPanel, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM, 5)
        
        self.Bind(wx.EVT_BUTTON, self.OnApply, self.applyButton)
        
    def OnApply(self, evt):
        depthStep = float(self.depthStep.GetValue())
        if depthStep < self.minDepthStep:
            dlg = MessageDialog(self, "Error", "Depth Step must be at least {}".format(self.minDepthStep), 1)
            dlg.ShowModal()
            self.depthStep.SetValue(str(self.minDepthStep))
            return
        self.outDepthStep = depthStep 
        self.outWinLength = float(self.winLength.GetValue())
        self.outLeadLag = float(self.leadLag.GetValue())
        self.EndModal(wx.ID_OK)


class DepthRangeDialog(wx.Dialog):
    def __init__(self, parent, min, max):
        wx.Dialog.__init__(self, parent, -1, "Depth Display Range", style=wx.CAPTION | wx.STAY_ON_TOP)
        
        # min/max edit controls
        ctrlPanel = wx.Panel(self, -1)
        sz = wx.FlexGridSizer(1, 4, gap=(5,0))
        sz.Add(wx.StaticText(ctrlPanel, -1, "min:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.minField = wx.TextCtrl(ctrlPanel, -1, min, size=(70,-1))
        sz.Add(self.minField, 0)
        sz.Add(wx.StaticText(ctrlPanel, -1, "max:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.maxField = wx.TextCtrl(ctrlPanel, -1, max, size=(70,-1))
        sz.Add(self.maxField)
        ctrlPanel.SetSizerAndFit(sz)
        
        # brgtodo 9/4/2014: CreateButtonSizer() for default OK/Cancel/etc button panel creation?
        buttonPanel = wx.Panel(self, -1)
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.cancelButton = wx.Button(buttonPanel, wx.ID_CANCEL, "Cancel")
        self.applyButton = wx.Button(buttonPanel, wx.ID_OK, "Apply")
        self.applyButton.SetDefault()
        buttonSizer.Add(self.cancelButton, 0, wx.ALL, 5)
        buttonSizer.Add(self.applyButton, 0, wx.ALL, 5)
        buttonPanel.SetSizer(buttonSizer)

        #btnSizer = self.CreateButtonSizer(wx.ID_CANCEL | wx.ID_APPLY)
        
        dlgSizer = wx.BoxSizer(wx.VERTICAL)
        dlgSizer.Add(ctrlPanel, 1, wx.EXPAND | wx.ALL, 10)
        dlgSizer.Add(buttonPanel, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM, 5)
        self.SetSizerAndFit(dlgSizer)
        
        self.Bind(wx.EVT_BUTTON, self.OnApply, self.applyButton)
        
    def OnApply(self, evt):
        min = float(self.minField.GetValue())
        max = float(self.maxField.GetValue())
        if min >= max:
            return
        self.outMin = min 
        self.outMax = max
        self.EndModal(wx.ID_OK)


class DecimateDialog(wx.Dialog):
    def __init__(self, parent, deciValue):
        wx.Dialog.__init__(self, parent, -1, "Create Decimate Filter", style=wx.CAPTION | wx.STAY_ON_TOP)
        self.deciValue = deciValue
        self.createGUI()

    def createGUI(self):
        decValPanel = wx.Panel(self, -1)
        self.decimate = wx.TextCtrl(decValPanel, -1, str(self.deciValue))
        dvSizer = wx.BoxSizer(wx.HORIZONTAL)
        dvSizer.Add(wx.StaticText(decValPanel,  -1, "Show every"), 0, wx.LEFT | wx.RIGHT, 5)
        dvSizer.Add(self.decimate, 0, wx.RIGHT, 5)
        dvSizer.Add(wx.StaticText(decValPanel,  -1, "points"), 0, wx.LEFT | wx.RIGHT, 5)
        decValPanel.SetSizer(dvSizer)

        btnPanel = OkButtonPanel(self, okName="Apply")
        self.Bind(wx.EVT_BUTTON, self.OnApply, btnPanel.ok)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(decValPanel, 1, wx.ALL, 10)
        sizer.Add(btnPanel, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        self.SetSizer(sizer)
        self.Fit()

    def OnInvalid(self):
        dlg = MessageDialog(self, "Error", "Value must be a positive integer.", 1)
        dlg.ShowModal()
        dlg.Destroy()

    def OnApply(self, evt):
        deciValue = None
        try:
            deciValue = int(self.decimate.GetValue())
        except ValueError:
            self.OnInvalid()
            return
        if deciValue < 1:
            self.OnInvalid()
            return
        self.deciValue = deciValue
        self.EndModal(wx.ID_OK)


class ImageCullDialog(wx.Dialog):
    def __init__(self, parent, imageCullPct):
        wx.Dialog.__init__(self, parent, -1, "Create image cull filter", style=wx.CAPTION | wx.STAY_ON_TOP)
        self.icpValue = imageCullPct
        self.createGUI()

    def createGUI(self):
        panel = wx.Panel(self, -1)
        self.icp = wx.TextCtrl(panel, -1, str("0" if self.icpValue is None else self.icpValue), size=(50,-1))
        icSizer = wx.StaticBoxSizer(wx.StaticBox(panel, -1, "Remove lateral image margins"), orient=wx.HORIZONTAL)
        icSizer.Add(wx.StaticText(panel,  -1, "Trim"), 0, wx.ALIGN_CENTER_VERTICAL)
        icSizer.Add(self.icp, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)
        icSizer.Add(wx.StaticText(panel,  -1, "% from left and right of images"), 0, wx.ALIGN_CENTER_VERTICAL)
        panel.SetSizer(icSizer)

        btnPanel = OkButtonPanel(self, okName="Apply")
        self.Bind(wx.EVT_BUTTON, self.OnApply, btnPanel.ok)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(panel, 1, wx.ALL, 10)
        sizer.Add(btnPanel, 0, wx.ALIGN_CENTER)
        self.SetSizer(sizer)
        self.Fit()

    def OnInvalid(self):
        dlg = MessageDialog(self, "Error", "Value must be between 0.0 and 99.0.", 1)
        dlg.ShowModal()
        dlg.Destroy()

    def OnApply(self, evt):
        icpValue = None
        try:
            icpValue = float(self.icp.GetValue())
        except ValueError:
            self.OnInvalid()
            return
        if icpValue < 0.0 or icpValue > 99.0:
            self.OnInvalid()
            return
        self.icpValue = icpValue
        self.EndModal(wx.ID_OK)


# Modify datatype display order.
# Deprecated, replaced by DatatypeVisibilityAndOrderDialog
class DisplayOrderDialog(wx.Dialog):
    def __init__(self, parent, displayOrder):
        wx.Dialog.__init__(self, parent, -1, "Display Order", size=(-1, 400), style=wx.CAPTION | wx.STAY_ON_TOP)
        self.parent = parent
        self.displayOrder = displayOrder
        self.createGUI()

    def createGUI(self):
        mainPanel = wx.Panel(self, -1)
        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.orderList = wx.ListBox(mainPanel, -1, size=(-1, 120), choices=self.displayOrder, style=wx.LB_SINGLE)
        self.Bind(wx.EVT_LISTBOX, self.ListSelectionChanged, self.orderList)
        mainSizer.Add(self.orderList)

        upDownSizer = wx.BoxSizer(wx.VERTICAL)
        self.upButton = wx.Button(mainPanel, -1, "Move Up")
        self.Bind(wx.EVT_BUTTON, self.OnUp, self.upButton)
        self.downButton = wx.Button(mainPanel, -1, "Move Down")
        self.Bind(wx.EVT_BUTTON, self.OnDown, self.downButton)
        upDownSizer.Add(self.upButton, 0, wx.ALIGN_CENTER | wx.BOTTOM, 5)
        upDownSizer.Add(self.downButton, 0, wx.ALIGN_CENTER)
        mainSizer.Add(upDownSizer, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        mainPanel.SetSizer(mainSizer)

        self.cancel = wx.Button(self, wx.ID_CANCEL, "Close")
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(mainPanel, 1, wx.ALL, 10)
        sizer.Add(self.cancel, 0, wx.ALIGN_CENTER | wx.BOTTOM, 5)
        self.SetSizerAndFit(sizer)

        if len(self.displayOrder) > 0:
            self.orderList.SetSelection(0)
            self.ListSelectionChanged(None)

    def OnUp(self, evt):
        sel = self.orderList.GetSelection()
        if sel > 0:
            self.displayOrder[sel-1], self.displayOrder[sel] = self.displayOrder[sel], self.displayOrder[sel-1]
            self.orderList.SetItems(self.displayOrder)
            self.orderList.SetSelection(sel-1)
            self.Update()

    def OnDown(self, evt):
        sel = self.orderList.GetSelection()
        if sel < self.orderList.GetCount() - 1:
            self.displayOrder[sel+1], self.displayOrder[sel] = self.displayOrder[sel], self.displayOrder[sel+1]
            self.orderList.SetItems(self.displayOrder)
            self.orderList.SetSelection(sel+1)
            self.Update()

    def ListSelectionChanged(self, evt):
        sel = self.orderList.GetSelection()
        self.upButton.Enable(sel > 0)
        self.downButton.Enable(sel < self.orderList.GetCount() - 1)

    def Update(self):
        self.ListSelectionChanged(None)
        self.parent.Window.layoutManager.setDatatypeOrder(list(self.displayOrder)) # copy
        self.parent.Window.UpdateDrawing()


# Show/hide holes by name.
# - visibleHoles: dict of hole name:visbility pairs {'A':True, 'B':False, ...}
class HoleVisibilityDialog(wx.Dialog):
    def __init__(self, parent, visibleHoles):
        wx.Dialog.__init__(self, parent, -1, "Show holes", size=(-1, 200), style=wx.CAPTION | wx.STAY_ON_TOP | wx.RESIZE_BORDER)
        self.parent = parent
        self.createGUI(visibleHoles)

    def createGUI(self, visibleHoles):
        mainPanel = wx.Panel(self, -1)
        mainSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.holeList = wx.CheckListBox(mainPanel, -1, size=(-1, 120))
        sortedHoleKeys = sorted(visibleHoles.keys())
        self.holeList.SetItems(sortedHoleKeys)
        for row, h in enumerate(sortedHoleKeys):
            self.holeList.Check(row, visibleHoles[h])

        self.Bind(wx.EVT_CHECKLISTBOX, self.HoleItemChecked, self.holeList)

        mainSizer.Add(self.holeList, 1, wx.EXPAND)
        mainPanel.SetSizer(mainSizer)

        self.cancel = wx.Button(self, wx.ID_CANCEL, "Close")
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(mainPanel, 1, wx.ALL | wx.EXPAND, 10)
        sizer.Add(self.cancel, 0, wx.ALIGN_CENTER | wx.BOTTOM, 5)
        self.SetSizerAndFit(sizer)

        # Widen the window slightly, a workaround for this issue with CheckListBox on
        # certain versions of macOS: https://github.com/wxWidgets/Phoenix/issues/1210
        cur_size = self.GetSize()
        cur_size.SetWidth(cur_size.GetWidth() + 1)
        self.SetSize(cur_size)

    def HoleItemChecked(self, evt):
        curVisibleHoles = {}
        for idx in range(self.holeList.GetCount()):
            curVisibleHoles[self.holeList.GetString(idx)] = self.holeList.IsChecked(idx)
        self.parent.Window.layoutManager.updateVisibleHoles(curVisibleHoles)
        self.parent.Window.UpdateDrawing()


# Show/hide datatypes and adjust their display order.
# - displayOrder: list of datatype names in display order, copy of layoutManager.displayOrder
# - visibleDatatypes: dict of datatype name:visibility pairs {'NaturalGamma':True, 'WRMSL':False, ...}
class DatatypeVisibilityAndOrderDialog(wx.Dialog):
    def __init__(self, parent, displayOrder, visibleDatatypes):
        wx.Dialog.__init__(self, parent, -1, "Show and Order Data Types", size=(300, 200), style=wx.CAPTION | wx.STAY_ON_TOP | wx.RESIZE_BORDER)
        self.parent = parent
        self.displayOrder = displayOrder
        self.visibleDatatypes = visibleDatatypes
        self.createGUI()

    def createGUI(self):
        mainPanel = wx.Panel(self, -1)
        mainSizer = wx.BoxSizer(wx.HORIZONTAL)

        # move up/down arrows
        upDownSizer = wx.BoxSizer(wx.VERTICAL)
        up_img = load_bmp_resource("icons/arrow-up.png")
        self.upButton = wx.BitmapButton(mainPanel, -1, up_img)
        self.Bind(wx.EVT_BUTTON, self.OnUp, self.upButton)
        down_img = load_bmp_resource("icons/arrow-down.png")
        self.downButton = wx.BitmapButton(mainPanel, -1, down_img)
        self.Bind(wx.EVT_BUTTON, self.OnDown, self.downButton)
        upDownSizer.Add(self.upButton, 0, wx.ALIGN_CENTER | wx.BOTTOM, 5)
        upDownSizer.Add(self.downButton, 0, wx.ALIGN_CENTER)

        # datatype list
        typeSizer = wx.BoxSizer(wx.VERTICAL)
        typeSizer.Add(wx.StaticText(mainPanel, -1, "Show data type"), 0)
        self.typeList = wx.CheckListBox(mainPanel, -1, size=(-1,120))
        self._updateList()
        self.Bind(wx.EVT_LISTBOX, self.ListSelectionChanged, self.typeList)
        typeSizer.Add(self.typeList, 1, wx.EXPAND)

        self.Bind(wx.EVT_CHECKLISTBOX, self.ItemChecked, self.typeList)

        mainSizer.Add(typeSizer, 1, wx.EXPAND)
        mainSizer.Add(upDownSizer, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
        mainPanel.SetSizer(mainSizer)

        self.cancel = wx.Button(self, wx.ID_CANCEL, "Close")
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(mainPanel, 1, wx.ALL | wx.EXPAND, 10)
        sizer.Add(self.cancel, 0, wx.ALIGN_CENTER | wx.BOTTOM, 5)
        self.SetSizer(sizer)

        if self.typeList.GetCount() > 0:
            self.typeList.SetSelection(0)

        # Widen the window slightly, a workaround for this issue with CheckListBox on
        # certain versions of macOS: https://github.com/wxWidgets/Phoenix/issues/1210
        cur_size = self.GetSize()
        cur_size.SetWidth(cur_size.GetWidth() + 1)
        self.SetSize(cur_size)

    def _updateList(self):
        self.typeList.SetItems(self.displayOrder)
        for row, dt in enumerate(self.displayOrder):
            self.typeList.Check(row, self.visibleDatatypes[dt])

    def ItemChecked(self, evt):
        for idx in range(self.typeList.GetCount()):
            self.visibleDatatypes[self.typeList.GetString(idx)] = self.typeList.IsChecked(idx)
        self.parent.Window.layoutManager.updateVisibleDatatypes(self.visibleDatatypes)
        self.parent.Window.UpdateDrawing()

    def OnUp(self, evt):
        sel = self.typeList.GetSelection()
        if sel > 0:
            self.displayOrder[sel-1], self.displayOrder[sel] = self.displayOrder[sel], self.displayOrder[sel-1]
            self._updateList()
            self.typeList.SetSelection(sel-1)
            self.Update()

    def OnDown(self, evt):
        sel = self.typeList.GetSelection()
        if sel < self.typeList.GetCount() - 1:
            self.displayOrder[sel+1], self.displayOrder[sel] = self.displayOrder[sel], self.displayOrder[sel+1]
            self._updateList()
            self.typeList.SetSelection(sel+1)
            self.Update()

    def ListSelectionChanged(self, evt):
        sel = self.typeList.GetSelection()
        self.upButton.Enable(sel > 0)
        self.downButton.Enable(sel < self.typeList.GetCount() - 1)

    def Update(self):
        self.ListSelectionChanged(None)
        self.parent.Window.layoutManager.setDatatypeOrder(list(self.displayOrder)) # copy
        self.parent.Window.UpdateDrawing()


class SmoothDialog(wx.Dialog):
    def __init__(self, parent, width=9, units=1, style=1):
        wx.Dialog.__init__(self, parent, -1, "Create Smooth Filter", style=wx.CAPTION | wx.STAY_ON_TOP)
        self.parent = parent
        self.createGUI()
        self.width.SetValue(str(width))
        self.units.SetSelection(units - 1)
        self.style.SetSelection(style)

    def createGUI(self):
        smoothPanel = wx.Panel(self, -1)
        smoothParamsSizer = wx.GridBagSizer(3, 3)
        
        smoothParamsSizer.Add(wx.StaticText(smoothPanel, -1, "Width"), (0,0), flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=5)
        self.width = wx.TextCtrl(smoothPanel, -1, "9", size=(60, 25))
        smoothParamsSizer.Add(self.width, (0,1), flag=wx.BOTTOM, border=3)

        self.units = wx.Choice(smoothPanel, -1, choices=["Points", "Depth (cm)"])
        self.units.SetForegroundColour(wx.BLACK)
        smoothParamsSizer.Add(self.units, (0,2), flag=wx.ALIGN_CENTER_VERTICAL)

        smoothParamsSizer.Add(wx.StaticText(smoothPanel, -1, "Display"), (1,0), flag=wx.RIGHT, border=5)
        self.style = wx.Choice(smoothPanel, -1, (0,0), (180, -1), ("Original Only", "Smoothed Only", "Original & Smoothed"))
        self.style.SetForegroundColour(wx.BLACK)
        smoothParamsSizer.Add(self.style, (1,1), span=(1,2), flag=wx.BOTTOM, border=5)
        smoothPanel.SetSizer(smoothParamsSizer)

        btnPanel = OkButtonPanel(self, okName="Apply")
        self.Bind(wx.EVT_BUTTON, self.OnApply, btnPanel.ok)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(smoothPanel, 1, wx.EXPAND | wx.ALL, 10)
        sizer.Add(btnPanel, 0, wx.ALIGN_CENTER)
        self.SetSizer(sizer)
        self.Fit()

    def OnInvalid(self):
        dlg = MessageDialog(self, "Error", "Bad smoothing", 1)
        dlg.ShowModal()
        dlg.Destroy()

    def OnApply(self, evt):
        width = int(self.width.GetValue())
        units = self.units.GetSelection() + 1
        style = self.style.GetSelection()
        self.outSmoothParams = smooth.SmoothParameters(width, units, style)
        self.EndModal(wx.ID_OK)


class CullDialog(wx.Dialog):
    def __init__(self, parent, cullData):
        wx.Dialog.__init__(self, parent, -1, "Create Cull Filter", style=wx.CAPTION | wx.STAY_ON_TOP)
        self.parent = parent
        self.createGUI()
        self.fillValues(cullData)

    def createGUI(self):
        cullSizer = wx.BoxSizer(wx.VERTICAL)

        edgesSizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Cull data from sample edges'))
        cullTopsPanel = wx.Panel(self, -1)
        ctSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.cullTops = wx.TextCtrl(cullTopsPanel, -1, "", size=(50,-1))
        ctSizer.Add(wx.StaticText(cullTopsPanel, -1, "Cull"), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)
        ctSizer.Add(self.cullTops, 0, wx.ALIGN_CENTER_VERTICAL)
        ctSizer.Add(wx.StaticText(cullTopsPanel, -1, "cm from core tops"), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)
        cullTopsPanel.SetSizer(ctSizer)
        edgesSizer.Add(cullTopsPanel, 0, wx.ALL, 5)
        cullSizer.Add(edgesSizer, 0, wx.ALL, 5)

        outlierSizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Cull outliers'), orient=wx.VERTICAL)
        cullGTPanel = wx.Panel(self, -1)
        cgtSizer = wx.BoxSizer(wx.HORIZONTAL)
        cgtSizer.Add(wx.StaticText(cullGTPanel, -1, "Cull data values > "), 0)
        self.cullGT = wx.TextCtrl(cullGTPanel, -1, "", size=(50,-1))
        cgtSizer.Add(self.cullGT, 0)
        cullGTPanel.SetSizer(cgtSizer)
        outlierSizer.Add(cullGTPanel, 0, wx.EXPAND | wx.ALL, 5)

        cullLTPanel = wx.Panel(self, -1)
        cltSizer = wx.BoxSizer(wx.HORIZONTAL)
        cltSizer.Add(wx.StaticText(cullLTPanel, -1, "Cull data values < "), 0)
        self.cullLT = wx.TextCtrl(cullLTPanel, -1, "", size=(50,-1))
        cltSizer.Add(self.cullLT, 0)
        cullLTPanel.SetSizer(cltSizer)
        outlierSizer.Add(cullLTPanel, 0, wx.EXPAND | wx.ALL, 5)

        cullSizer.Add(outlierSizer, 1, wx.EXPAND | wx.ALL, 5)

        btnPanel = OkButtonPanel(self, okName="Apply")
        self.Bind(wx.EVT_BUTTON, self.OnApply, btnPanel.ok)
        cullSizer.Add(btnPanel, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        self.SetSizer(cullSizer)
        self.Fit()

    def _nonDummyValue(self, cullSign, cullValue):
        return (cullSign == '>' and float(cullValue) < 9999.0) or (cullSign == '<' and float(cullValue) > -9999.0)

    # Populate fields with values from cull data, omitting dummy values
    def fillValues(self, cullData):
        datalen = len(cullData)
        if datalen >= 3:
            self.cullTops.SetValue(cullData[2])
        if datalen == 5 or datalen == 6:
            if self._nonDummyValue(cullData[3], cullData[4]):
                if cullData[3] == ">":
                    self.cullGT.SetValue(cullData[4])
                else:
                    self.cullLT.SetValue(cullData[4])
        elif datalen == 7 or datalen == 8:
            if self._nonDummyValue(cullData[3], cullData[4]):
                if cullData[3] == ">":
                    self.cullGT.SetValue(cullData[4])
                else:
                    self.cullLT.SetValue(cullData[4])
            if self._nonDummyValue(cullData[5], cullData[6]):
                if cullData[5] == ">":
                    self.cullGT.SetValue(cullData[6])
                else:
                    self.cullLT.SetValue(cullData[6])

    def OnInvalid(self):
        dlg = MessageDialog(self, "Error", "Invalid cull parameter", 1)
        dlg.ShowModal()
        dlg.Destroy()

    def hasTops(self):
        return self.cullTops.GetValue() != ""

    def hasGT(self):
        return self.cullGT.GetValue() != ""

    def hasLT(self):
        return self.cullLT.GetValue() != ""

    def OnApply(self, evt):
        try:
            self.outCullTops = 0.0 if not self.hasTops() else float(self.cullTops.GetValue())
            self.outCullValue1 = 9999.99
            self.outCullValue2 = -9999.99
            self.outSign1 = 1
            self.outSign2 = 2
            self.outJoin = 1
            if self.hasGT() and self.hasLT():
                self.outSign1 = 1
                self.outCullValue1 = float(self.cullGT.GetValue())
                self.outSign2 = 2
                self.outCullValue2 = float(self.cullLT.GetValue())
                self.outJoin = 2
            elif self.hasGT() and not self.hasLT():
                self.outCullValue1 = float(self.cullGT.GetValue())
                self.outSign1 = 1
            elif self.hasLT() and not self.hasGT():
                self.outCullValue1 = float(self.cullLT.GetValue())
                self.outSign1 = 2
        except ValueError:
            self.OnInvalid()
            return
        self.EndModal(wx.ID_OK)


class ApplicationPreferencesDialog(wx.Dialog):
    def __init__(self, parent, prefs):
        wx.Dialog.__init__(self, parent, -1, "Correlator Preferences", size=(200,200), style=wx.CAPTION | wx.STAY_ON_TOP)

        self.prefsMap = prefs

        panel = wx.StaticBoxSizer(wx.StaticBox(self, -1, "Data Loading Options"), orient=wx.VERTICAL)
        self.inferSectionSummary = wx.CheckBox(self, -1, "Infer Section Summary if none is provided")
        panel.Add(self.inferSectionSummary, 0, wx.BOTTOM, 5)
        self.checkForSpliceCores = wx.CheckBox(self, -1, "Check for cores required by enabled splice")
        panel.Add(self.checkForSpliceCores)
        
        buttonPanel = wx.Panel(self, -1)
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.cancelButton = wx.Button(buttonPanel, wx.ID_CANCEL, "Cancel")
        self.okButton = wx.Button(buttonPanel, wx.ID_OK, "OK")
        self.okButton.SetDefault()
        self.Bind(wx.EVT_BUTTON, self.OnOK, self.okButton)
        buttonSizer.Add(self.cancelButton, 0, wx.ALL, 5)
        buttonSizer.Add(self.okButton, 0, wx.ALL, 5)
        buttonPanel.SetSizer(buttonSizer)

        dlgSizer = wx.BoxSizer(wx.VERTICAL)
        dlgSizer.Add(panel, wx.ALL, 10)
        dlgSizer.Add(buttonPanel, 0, wx.ALIGN_RIGHT | wx.ALL, 10)
        self.SetSizerAndFit(dlgSizer)
        self.InitPrefs(prefs)

    def InitPrefs(self, prefs):
        self.inferSectionSummary.SetValue(self.prefsMap['inferSectionSummary'])
        self.checkForSpliceCores.SetValue(self.prefsMap['checkForSpliceCores'])

    def UpdatePrefs(self):
        self.prefsMap['inferSectionSummary'] = self.inferSectionSummary.IsChecked()
        self.prefsMap['checkForSpliceCores'] = self.checkForSpliceCores.IsChecked()

    def OnOK(self, evt):
        self.UpdatePrefs()
        self.EndModal(wx.ID_OK)


class AboutDialog(wx.Dialog):
    def __init__(self, parent, version):
        wx.Dialog.__init__(self, parent, -1, "About Correlator " + version, style= wx.DEFAULT_DIALOG_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE | wx.STAY_ON_TOP)

        vertSizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(vertSizer)

        description = "The Correlator application facilitates the construction of " \
                    "'Core Composite depth below Sea Floor' (CCSF) depth scales when " \
                    "core data from multiple holes are available, by allowing users " \
                    "to align correlative features across holes and shift the core " \
                    "depths accordingly. Correlator also facilitates the definition " \
                    "of stratigraphic splices at the CCSF scale by allowing users to " \
                    "select the most suitable and contiguous core intervals."

        desc = wx.StaticText(self, -1, description)
        desc.Wrap(530)
        vertSizer.Add(desc, 0, wx.ALL, 10)

        corryUrl = "https://csdco.umn.edu/resources/software/correlator"
        link = HyperLinkCtrl(self, -1, 'For more detailed information, please visit the Correlator Website', URL=corryUrl)
        vertSizer.Add(link, 0, wx.LEFT, 10)
        vertSizer.Add((15,15), 0) # add some vertical space between sections

        vertSizer.Add(wx.StaticText(self, -1, 'Developers:'), 0, wx.LEFT, 10)
        vertSizer.Add((5,5), 0)
        devs = 'Peter Blum (blum@iodp.tamu.edu)  |  Brian Grivna (brian.grivna@gmail.com)'
        vertSizer.Add(wx.StaticText(self, -1, devs), 0, wx.LEFT, 10)
        vertSizer.Add((15,15), 0)

        devsEmeritus = 'Sean Higgins  |  Hyejung Hur'
        vertSizer.Add(wx.StaticText(self, -1, 'Developers Emeritus:'), 0, wx.LEFT, 10)
        vertSizer.Add((5,5), 0)
        vertSizer.Add(wx.StaticText(self, -1, devsEmeritus), 0, wx.LEFT, 10)
        vertSizer.Add((15,15), 0)

        vertSizer.Add(wx.StaticText(self, -1, 'Organizations:'), 0, wx.LEFT, 10)
        vertSizer.Add((5,5), 0)
        grid = wx.FlexGridSizer(2, 3, (20,10))
        grid.Add(HyperLinkCtrl(self, -1, 'National Science Foundation', URL='https://www.nsf.gov/'))
        grid.Add(HyperLinkCtrl(self, -1, 'CSD Facility (University of Minnesota)', URL='https://cse.umn.edu/csd'))
        grid.Add(HyperLinkCtrl(self, -1, 'IODP/JR Science Operator', URL='https://iodp.tamu.edu/'))
        grid.Add(HyperLinkCtrl(self, -1, 'Lamont-Doherty Earth Observatory', URL='https://www.ldeo.columbia.edu/'))
        grid.Add(HyperLinkCtrl(self, -1, 'EVL (University of Illinois)', URL='https://www.evl.uic.edu/'))
        vertSizer.Add(grid, 0, wx.LEFT | wx.RIGHT, 15)

        vertSizer.Add((20,20), 0)
        okBtn = wx.Button(self, wx.ID_OK, "Close")
        vertSizer.Add(okBtn, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)

        self.Fit() # auto-adjust dialog size to fit all elements
        wx.EVT_KEY_UP(self, self.OnCharUp)

    def OnCharUp(self,event):
        keyid = event.GetKeyCode() 
        if keyid == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL) 


class BackgroundPanel(wx.Panel):
    def __init__(self, parent, image):
        wx.Panel.__init__(self, parent, -1, size=(image.GetWidth(), image.GetHeight()), style=wx.WANTS_CHARS)
        self.buffer = wx.Bitmap(image)
        dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    @classmethod
    def createWithImage(cls, parent, imagefile):
        image = wx.Image(imagefile, wx.BITMAP_TYPE_ANY)
        return cls(parent, image)

    def OnPaint(self, evt):
        dc = wx.BufferedPaintDC(self, self.buffer)


class SplashScreen(wx.Dialog):
    def __init__(self, parent, id, user, version):
        wx.Dialog.__init__(self, parent, id, "Correlator " + version, style=wx.DEFAULT_DIALOG_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE | wx.STAY_ON_TOP)

        sizer = wx.BoxSizer(wx.VERTICAL)
        panel = BackgroundPanel.createWithImage(self, get_resource_path('images/splashscreen.png'))

        self.version = version

        controlSizer = wx.BoxSizer(wx.HORIZONTAL)
        usernameText = wx.StaticText(self, -1, 'Username (optional):')
        self.name = wx.TextCtrl(self, -1, user)

        okBtn = wx.Button(self, -1, "Start")
        okBtn.SetBackgroundColour(wx.GREEN)
        okBtn.SetDefault()
        self.Bind(wx.EVT_BUTTON, self.OnSTART, okBtn)

        self.user = user
        cancelBtn = wx.Button(self, wx.ID_CANCEL, "Close")

        aboutBtn = wx.Button(self, -1, "About", size=(60,-1))
        self.Bind(wx.EVT_BUTTON, self.OnABOUT, aboutBtn)

        self.name.Bind(wx.EVT_KEY_DOWN, self.OnPanelChar)
        panel.Bind(wx.EVT_CHAR, self.OnPanelChar)

        userSizer = wx.BoxSizer(wx.HORIZONTAL)
        userSizer.Add(usernameText, 0, wx.ALIGN_CENTER_VERTICAL)
        userSizer.Add(self.name, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)

        okCloseSizer = wx.BoxSizer(wx.HORIZONTAL)
        okCloseSizer.Add(okBtn, 1)
        okCloseSizer.Add(cancelBtn, 1, wx.LEFT, 10)

        aboutSizer = wx.BoxSizer(wx.HORIZONTAL)
        aboutSizer.AddStretchSpacer()
        aboutSizer.Add(aboutBtn, 0)

        controlSizer.Add(userSizer, 1)
        controlSizer.Add(okCloseSizer, 1, wx.ALIGN_CENTER)
        controlSizer.Add(aboutSizer, 1)
        
        sizer.Add(panel, 1, wx.EXPAND)
        sizer.Add(controlSizer, 0, wx.ALL | wx.EXPAND, 10)
        self.SetSizerAndFit(sizer)


    def OnABOUT(self, event):
        dlg = AboutDialog(self, self.version)
        dlg.Centre()
        dlg.ShowModal()
        dlg.Destroy()

    def OnOK(self):
        self.user = self.name.GetValue()
        self.EndModal(wx.ID_OK)

    def OnSTART(self, event):
        self.OnOK()

    # Close on Escape, continue on Enter
    def OnPanelChar(self, event):
        keyid = event.GetKeyCode()
        if keyid == 13: # ENTER
            self.OnOK()
        elif keyid == 27: # ESC 
            self.EndModal(wx.ID_CANCEL)
        else:
            event.Skip() # allow unhandled key events to propagate up the chain

            
class MockApp(wx.App):
    def __init__(self):
        wx.App.__init__(self)
        self.frame = None
        
    def OnInit(self):
        self.frame = wx.Frame(None, -1, "MockFrame", wx.Point(200,200), size=(200,200))
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True

if __name__ == "__main__":
    app = MockApp()
    # msg = "Fairly long message about some serious stuff"
    msg = "Exceedingly long message that goes on for a super duper super duper  super duper super duper super duper super duper super duper super duper super duper super duper long time."
    suppMsg = "Don't show this message again"
    dlg = SuppressibleMessageDialog(app.frame, "Warning", msg, MsgDlgButtons.YesNo, suppMsg, customLabels=["Foo", "Bar"])
    result = dlg.ShowModal()
    if result == wx.ID_OK:
        print("OK")
    elif result == wx.ID_CANCEL:
        print("Cancel")
    else:
        assert False, "WTF?"
    print("Checkbox checked? {}".format(dlg.IsCheckBoxChecked()))