#!/usr/bin/env python

## For Mac-OSX
#/usr/bin/env pythonw
import platform
platform_name = platform.uname()

#from wxPython.wx import *
import wx 
import wx.lib.sheet as sheet
from wx.lib import plot
import random, sys, os, re, time, ConfigParser, string

import py_correlator

class CoreSheet(sheet.CSheet):
	def __init__(self, parent, x, y):
		sheet.CSheet.__init__(self, parent)
	 	self.SetWindowStyle(wx.ALWAYS_SHOW_SB)
		self.SetNumberRows(x)
		self.SetNumberCols(y)

class HoldDialog(wx.Frame):
	def __init__(self, parent):
		wx.Frame.__init__(self, parent, -1, "Communication", size=(330, 130), style = wx.DEFAULT_DIALOG_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE |wx.STAY_ON_TOP)
		self.Center()
		bmp = wx.StaticBitmap(self, -1, wx.Bitmap('icons/about-32x32.png'), (10, 30))
		wx.StaticText(self, -1, "Waiting for Fine Tune from Corelyzer", (60,30))
		#self.EndModal(wx.ID_OK)


class MessageDialog(wx.Dialog):
	def __init__(self, parent, title, msg, nobutton):
		if title == "About" or title == "Help" : 
			wx.Dialog.__init__(self, parent, -1, title, size=(330, 130), style= wx.STAY_ON_TOP)
		else :
			wx.Dialog.__init__(self, parent, -1, title, size=(330, 110), style= wx.STAY_ON_TOP)

		self.Center()
		vbox_top = wx.BoxSizer(wx.VERTICAL)
		panel1 = wx.Panel(self, -1)
		sizer = wx.FlexGridSizer(1, 2)
		if title == "Error" : 
			bmp = wx.StaticBitmap(panel1, -1, wx.Bitmap('icons/ErrorCircle-32x32.png'))
			sizer.Add(bmp, 0, wx.LEFT | wx.TOP, 9)
		elif title == "Information" or title == "Help" :
			bmp = wx.StaticBitmap(panel1, -1, wx.Bitmap('icons/about-32x32.png'))
			sizer.Add(bmp, 0, wx.LEFT | wx.TOP, 9)
		elif title == "About" :
			bmp = wx.StaticBitmap(panel1, -1, wx.Bitmap('icons/help-32x32.png'))
			sizer.Add(bmp, 0, wx.LEFT | wx.TOP, 9)
		sizer.Add(wx.StaticText(panel1, -1, msg), 0, wx.LEFT | wx.TOP | wx.BOTTOM, 15)
		panel1.SetSizer(sizer)
		vbox_top.Add(panel1)

		if nobutton == 1 :
			okBtn = wx.Button(self, wx.ID_OK, "OK")
			vbox_top.Add(okBtn, 0, wx.LEFT, 110)
		else :
			grid = wx.GridSizer(1,2)
			okBtn = wx.Button(self, wx.ID_OK, "OK")
			grid.Add(okBtn)
			cancelBtn = wx.Button(self, wx.ID_CANCEL, "Cancel")
			grid.Add(cancelBtn, 0, wx.LEFT, 10)
			vbox_top.Add(grid, 0, wx.LEFT, 70)

		wx.EVT_KEY_UP(self, self.OnCharUp)
		self.SetSizer(vbox_top)

	def OnCharUp(self,event):
		keyid = event.GetKeyCode() 
		if keyid == wx.WXK_RETURN :
			self.EndModal(wx.ID_OK) 
		elif keyid == wx.WXK_ESCAPE :
			self.EndModal(wx.ID_CANCEL) 

class Message3Button(wx.Dialog):
	def __init__(self, parent, msg):
		wx.Dialog.__init__(self, parent, -1, "About", size=(330, 130), style= wx.STAY_ON_TOP)

		self.Center()
		vbox_top = wx.BoxSizer(wx.VERTICAL)
		panel1 = wx.Panel(self, -1)
		sizer = wx.FlexGridSizer(1, 2)
		bmp = wx.StaticBitmap(panel1, -1, wx.Bitmap('icons/help-32x32.png'))
		sizer.Add(bmp, 0, wx.LEFT | wx.TOP, 9)
		sizer.Add(wx.StaticText(panel1, -1, msg), 0, wx.LEFT | wx.TOP | wx.BOTTOM, 15)
		panel1.SetSizer(sizer)
		vbox_top.Add(panel1)

		grid = wx.GridSizer(1,3)
		okBtn = wx.Button(self, wx.ID_YES, "Yes")
		self.Bind(wx.EVT_BUTTON, self.OnYES, okBtn)
		grid.Add(okBtn)
		noBtn = wx.Button(self, wx.ID_OK, "No")
		grid.Add(noBtn)
		cancelBtn = wx.Button(self, wx.ID_CANCEL, "Cancel")
		grid.Add(cancelBtn, 0, wx.LEFT, 10)
		vbox_top.Add(grid, 0, wx.LEFT, 40)

		self.SetSizer(vbox_top)
		wx.EVT_KEY_UP(self, self.OnCharUp)

	def OnYES(self, event):
		self.EndModal(wx.ID_YES)

	def OnCharUp(self,event):
		keyid = event.GetKeyCode() 
		if keyid == wx.WXK_RETURN :
			self.EndModal(wx.ID_OK) 
		elif keyid == wx.WXK_ESCAPE :
			self.EndModal(wx.ID_CANCEL) 


class BoxDialog(wx.Dialog):
	def __init__(self, parent, title):
		wx.Dialog.__init__(self, parent, -1, title, size=(300, 130), style= wx.STAY_ON_TOP)

		self.Center()
		vbox_top = wx.BoxSizer(wx.VERTICAL)
		self.txt = wx.TextCtrl(self, -1, "", size = (270, 25), style=wx.SUNKEN_BORDER )

		vbox_top.Add(self.txt, 0, wx.LEFT | wx.TOP | wx.BOTTOM, 15)

		#self.register = wx.CheckBox(self, -1, 'Register')
		#vbox_top.Add(self.register, 0, wx.LEFT, 70)

		grid = wx.GridSizer(1,3)
		self.register = wx.CheckBox(self, -1, 'Register')
		grid.Add(self.register)
		okBtn = wx.Button(self, wx.ID_OK, "OK")
		grid.Add(okBtn)
		cancelBtn = wx.Button(self, wx.ID_CANCEL, "Cancel")
		grid.Add(cancelBtn, 0, wx.LEFT, 10)
		vbox_top.Add(grid, 0, wx.LEFT, 20)

		self.SetSizer(vbox_top)
		wx.EVT_KEY_UP(self, self.OnCharUp)

	def OnCharUp(self,event):
		keyid = event.GetKeyCode() 
		if keyid == wx.WXK_RETURN :
			self.EndModal(wx.ID_OK) 
		elif keyid == wx.WXK_ESCAPE :
			self.EndModal(wx.ID_CANCEL) 

class EditBoxDialog(wx.Dialog):
	def __init__(self, parent, title):
		wx.Dialog.__init__(self, parent, -1, title, size=(300, 130), style= wx.STAY_ON_TOP)

		self.Center()
		vbox_top = wx.BoxSizer(wx.VERTICAL)
		self.txt = wx.TextCtrl(self, -1, "", size = (270, 25), style=wx.SUNKEN_BORDER )

		vbox_top.Add(self.txt, 0, wx.LEFT | wx.TOP | wx.BOTTOM, 15)

		grid = wx.GridSizer(1,2)
		okBtn = wx.Button(self, wx.ID_OK, "OK")
		grid.Add(okBtn)
		cancelBtn = wx.Button(self, wx.ID_CANCEL, "Cancel")
		grid.Add(cancelBtn, 0, wx.LEFT, 10)
		vbox_top.Add(grid, 0, wx.LEFT, 50)
		self.SetSizer(vbox_top)
		wx.EVT_KEY_UP(self, self.OnCharUp)

	def OnCharUp(self,event):
		keyid = event.GetKeyCode() 
		if keyid == wx.WXK_RETURN :
			self.EndModal(wx.ID_OK) 
		elif keyid == wx.WXK_ESCAPE :
			self.EndModal(wx.ID_CANCEL) 


class StratTypeDialog(wx.Dialog):
	def __init__(self, parent):
		wx.Dialog.__init__(self, parent, -1, "Stratigraphy Type", size=(300, 130), style= wx.STAY_ON_TOP)

		self.Center()
		vbox_top = wx.BoxSizer(wx.VERTICAL)
		self.types = wx.ComboBox(self, -1, "Diatoms", (0,0), (250, 30), ("Diatoms", "Radioloria", "Foraminifera", "Nannofossils", "Paleomag"), wx.CB_DROPDOWN)

		vbox_top.Add(self.types, 0, wx.LEFT | wx.TOP, 25)

		grid = wx.GridSizer(1,2)
		okBtn = wx.Button(self, wx.ID_OK, "Chnage")
		grid.Add(okBtn, 0, wx.LEFT, 50)
		cancelBtn = wx.Button(self, wx.ID_CANCEL, "Cancel")
		grid.Add(cancelBtn, 0, wx.LEFT, 30)

		vbox_top.Add(grid, 0, wx.TOP, 15)

		self.SetSizer(vbox_top)
		wx.EVT_KEY_UP(self, self.OnCharUp)

	def OnCharUp(self,event):
		keyid = event.GetKeyCode() 
		if keyid == wx.WXK_RETURN :
			self.EndModal(wx.ID_OK) 
		elif keyid == wx.WXK_ESCAPE :
			self.EndModal(wx.ID_CANCEL) 


class ClearDataDialog(wx.Dialog):
	def __init__(self, parent, list):
		wx.Dialog.__init__(self, parent, -1, "Clear Core", size=(290, 370), style= wx.STAY_ON_TOP)
		self.Center()
		self.parent = parent

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(wx.StaticText(self, -1, "Select Type to Clear :"), 0, wx.LEFT | wx.TOP, 9)
		self.fileList = wx.ListBox(self, -1, (0,0), (265,250), "", style=wx.LB_HSCROLL|wx.LB_NEEDED_SB)	 
		vbox.Add(self.fileList, 0, wx.LEFT | wx.TOP, 9)

		n = list.GetCount()
		types = ""
		for i in range(n) :
			types = list.GetString(i)
			if types[0:3] == "All" :
				self.fileList.Append(list.GetString(i))

		if self.fileList.GetCount() > 0 :	
			self.fileList.Select(0)
		self.fileList.SetForegroundColour(wx.BLACK)

		grid4 = wx.FlexGridSizer(1, 2)
		okBtn = wx.Button(self, wx.ID_OK, "Clear", size=(120, 30))
		self.Bind(wx.EVT_BUTTON, self.OnClearData, okBtn)
		grid4.Add(okBtn)
		cancelBtn = wx.Button(self, wx.ID_CANCEL, "Cancel", size= (120, 30))
		grid4.Add(cancelBtn, 0, wx.LEFT, 15)
		vbox.Add(grid4, 0, wx.LEFT | wx.TOP , 15)

		self.SetSizer(vbox)
		wx.EVT_KEY_UP(self, self.OnCharUp)

		self.ShowModal()
		self.Destroy()

	def OnCharUp(self,event):
		keyid = event.GetKeyCode() 
		if keyid == wx.WXK_RETURN :
			self.EndModal(wx.ID_OK) 
		elif keyid == wx.WXK_ESCAPE :
			self.EndModal(wx.ID_CANCEL) 

	def OnClearData(self, event):
		ret = 0
		size = self.fileList.GetCount()
		for i in range(size) :
			if self.fileList.IsSelected(i) == True :
				if i == 0 : 
					self.parent.OnNewData(None)
				elif i == 1 and size == 2 :
					self.parent.OnNewData(None)
				else :
					py_correlator.cleanDataType(self.fileList.GetString(i))
					self.fileList.Delete(i)
				break	

		self.EndModal(wx.ID_OK) 


class AgeListDialog(wx.Dialog):
	def __init__(self, parent, active_list):
		wx.Dialog.__init__(self, parent, -1, "Selected Age List", size=(210, 200),style= wx.DEFAULT_DIALOG_STYLE |wx.NO_FULL_REPAINT_ON_RESIZE)
		self.ageList = wx.ListBox(self, -1, (5,5),(200,100), "", style=wx.LB_HSCROLL|wx.LB_NEEDED_SB|wx.LB_EXTENDED)
		self.Bind(wx.EVT_LISTBOX, self.OnSelect, self.ageList)
		self.selectedNo =  -1 

		idx = 0
		for age in active_list :
			self.ageList.InsertItems([str(age)], idx)
			idx += 1

		wx.Button(self, wx.ID_OK, "SELECT", ((25, 135)))
		wx.Button(self, wx.ID_CANCEL, "CANCEL", ((110, 135)))
		wx.EVT_KEY_UP(self, self.OnCharUp)

	def OnCharUp(self,event):
		keyid = event.GetKeyCode() 
		if keyid == wx.WXK_RETURN :
			self.EndModal(wx.ID_OK) 
		elif keyid == wx.WXK_ESCAPE :
			self.EndModal(wx.ID_CANCEL) 

	def OnSelect(self, event) :
		for i in range(self.ageList.GetCount()) :
			if self.ageList.IsSelected(i) == True :
				self.selectedNo = i 
				return


class SaveTableDialog(wx.Dialog):
	def __init__(self, parent, id, affine, splice):
		wx.Dialog.__init__(self, parent, id, "Save", size=(340, 340),style= wx.DEFAULT_DIALOG_STYLE |wx.NO_FULL_REPAINT_ON_RESIZE|wx.STAY_ON_TOP)

		wx.StaticText(self, -1, 'Check to Save to Data Manager', (50, 10))
		panel = wx.Panel ( self, -1, (10, 30), size=(320, 40), style=wx.BORDER)

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

		panel2 = wx.Panel ( self, -1, (10, 120), size=(320, 40), style=wx.BORDER)
		self.eldCheck = wx.CheckBox(panel2, -1, 'ELD Table', (10, 10))
		self.eldUpdate = wx.RadioButton(panel2, -1, "Update", (120, 10), style=wx.RB_GROUP)
		self.eldUpdate.SetValue(True)
		wx.RadioButton(panel2, -1, "Create New", (190, 10))

		panel3 = wx.Panel ( self, -1, (10, 165), size=(320, 40), style=wx.BORDER)
		self.ageCheck = wx.CheckBox(panel3, -1, 'Age/Depth', (10, 10))
		self.ageUpdate = wx.RadioButton(panel3, -1, "Update", (120, 10), style=wx.RB_GROUP)
		self.ageUpdate.SetValue(True)
		wx.RadioButton(panel3, -1, "Create New", (190, 10))

		panel4 = wx.Panel ( self, -1, (10, 210), size=(320, 40), style=wx.BORDER)
		self.seriesCheck = wx.CheckBox(panel4, -1, 'Age Model', (10, 10))
		self.seriesUpdate = wx.RadioButton(panel4, -1, "Update", (120, 10), style=wx.RB_GROUP)
		self.seriesUpdate.SetValue(True)
		wx.RadioButton(panel4, -1, "Create New", (190, 10))

		wx.Button(self, wx.ID_OK, "SAVE", ((85, 265)))
		wx.Button(self, wx.ID_CANCEL, "CANCEL", ((180, 265)))
		wx.EVT_KEY_UP(self, self.OnCharUp)

	def OnCharUp(self,event):
		keyid = event.GetKeyCode() 
		if keyid == wx.WXK_RETURN :
			self.EndModal(wx.ID_OK) 
		elif keyid == wx.WXK_ESCAPE :
			self.EndModal(wx.ID_CANCEL) 


class ExportCoreDialog(wx.Dialog):
	def __init__(self, parent):
		wx.Dialog.__init__(self, parent, -1, "Export Core", size=(260, 260),style= wx.DEFAULT_DIALOG_STYLE |wx.NO_FULL_REPAINT_ON_RESIZE)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(wx.StaticText(self, -1, 'Check to Export Core data'), 0, wx.TOP | wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 12)

		#self.core = wx.CheckBox(self, -1, 'Raw Core data')
		#self.core.SetValue(True)
		#self.core.Enable(False)
		#vbox.Add(self.core, 0, wx.TOP | wx.LEFT, 9)

		panel = wx.Panel(self, -1)
		vbox_opt = wx.BoxSizer(wx.HORIZONTAL)

		opt_panel = wx.Panel(panel, -1)
		sizer = wx.StaticBoxSizer(wx.StaticBox(opt_panel, -1, 'Options'), orient=wx.VERTICAL)

		self.cull = wx.CheckBox(opt_panel, -1, 'Apply Cull')
		sizer.Add(self.cull)
		self.cull.SetValue(True)

		self.affine = wx.CheckBox(opt_panel, -1, 'Apply Affine')
		sizer.Add(self.affine)
		self.splice = wx.CheckBox(opt_panel, -1, 'Apply Splice')
		sizer.Add(self.splice, 0, wx.TOP, 4)
		opt_panel.Bind(wx.EVT_CHECKBOX, self.OnSPLICE, self.splice)

		self.eld = wx.CheckBox(opt_panel, -1, 'Apply ELD')
		sizer.Add(self.eld, 0, wx.TOP, 4)
		opt_panel.Bind(wx.EVT_CHECKBOX, self.OnELD, self.eld)

		self.age = wx.CheckBox(opt_panel, -1, 'Apply Age Model')
		sizer.Add(self.age, 0, wx.TOP, 4)
		#opt_panel.Bind(wx.EVT_CHECKBOX, self.OnAGE, self.age)

		opt_panel.SetSizer(sizer)
		vbox_opt.Add(opt_panel)

		format_panel = wx.Panel(panel, -1)
		format_sizer = wx.StaticBoxSizer(wx.StaticBox(format_panel, -1, 'Format'), orient=wx.VERTICAL)
		self.format = wx.RadioButton(format_panel, -1, "Text", (40, 185), style=wx.RB_GROUP)
		self.format.SetValue(True)
		format_sizer.Add(self.format)
		xml_btn = wx.RadioButton(format_panel, -1, "XML", (110, 185))
		format_sizer.Add(xml_btn, 0, wx.TOP, 9)
		format_panel.SetSizer(format_sizer)
		vbox_opt.Add(format_panel, 0, wx.LEFT, 14)
		panel.SetSizer(vbox_opt)
		vbox.Add(panel, 0, wx.TOP | wx.LEFT, 12)

		self.SetSizer(vbox)

		wx.Button(self, wx.ID_OK, "Next", ((45, 200)))
		wx.Button(self, wx.ID_CANCEL, "CANCEL", ((140, 200)))
		wx.EVT_KEY_UP(self, self.OnCharUp)

	def OnCharUp(self,event):
		keyid = event.GetKeyCode() 
		if keyid == wx.WXK_ESCAPE :
			self.EndModal(wx.ID_CANCEL) 

	def OnSPLICE(self, event) :
		ret = self.splice.GetValue()

		self.affine.SetValue(ret)

	def OnELD(self, event) :
		ret = self.eld.GetValue()

		self.affine.SetValue(ret)
		#self.splice.SetValue(ret)

	def OnAGE(self, event) :
		ret = self.age.GetValue()
		self.affine.SetValue(ret)


class AltSpliceDialog(wx.Dialog):
	def __init__(self, parent):
		wx.Dialog.__init__(self, parent, -1, "Select Second Splice(View Only)", size=(360, 200),style= wx.DEFAULT_DIALOG_STYLE |wx.NO_FULL_REPAINT_ON_RESIZE)
		panel = wx.Panel ( self, -1, (15, 15), size=(330, 100), style=wx.BORDER)
		wx.StaticText(panel, -1, 'Data Type', (10, 20))
		wx.StaticText(panel, -1, 'Splice', (10, 60))
		self.all = wx.ComboBox(panel, -1, "", (90,20), (220,30), (""), wx.CB_DROPDOWN)
		for types in parent.Window.range :
			if types[0] != "splice" and types[0] != "altsplice" :
				self.all.Append(types[0])
		if self.all.GetCount() > 0 :
			self.all.Select(0)

		self.all.SetForegroundColour(wx.BLACK)
		self.all.SetEditable(False)
		#self.Bind(wx.EVT_COMBOBOX, self.SetTYPE, self.all)

		self.splice = wx.ComboBox(panel, -1, "", (90,60), (220,70), (""), wx.CB_DROPDOWN)
		parent.dataFrame.Update_PROPERTY_ITEM(parent.dataFrame.selectBackup)
		property = parent.dataFrame.propertyIdx
		totalcount = parent.dataFrame.tree.GetChildrenCount(property, False)
		if totalcount > 0 :
			child = parent.dataFrame.tree.GetFirstChild(property)
			child_item = child[0]
			if parent.dataFrame.tree.GetItemText(child_item, 1) == "SPLICE" :
				filename = parent.dataFrame.tree.GetItemText(child_item, 8)
				self.splice.Append(filename)
			for k in range(1, totalcount) :
				child_item = parent.dataFrame.tree.GetNextSibling(child_item)
				if parent.dataFrame.tree.GetItemText(child_item, 1) == "SPLICE" :
					self.splice.Append(parent.dataFrame.tree.GetItemText(child_item, 8))
		if self.splice.GetCount() > 0 :
			self.splice.Select(0)

		self.splice.SetForegroundColour(wx.BLACK)
		self.splice.SetEditable(False)

		self.selectedType = "" 
		self.selectedSplice = "" 
		okBtn = wx.Button(self, -1, "SELECT", (70, 135))
		self.Bind(wx.EVT_BUTTON, self.OnSELECT, okBtn)
		cancelBtn = wx.Button(self, wx.ID_CANCEL, "CANCEL", (210, 135))
		wx.EVT_KEY_UP(self, self.OnCharUp)

	def OnCharUp(self,event):
		keyid = event.GetKeyCode() 
		if keyid == wx.WXK_ESCAPE :
			self.EndModal(wx.ID_CANCEL) 

	def OnSELECT(self, event) :
		self.selectedSplice = self.splice.GetValue()
		self.selectedType = self.all.GetValue() 
		self.EndModal(wx.ID_OK) 


class ColorTableDialog(wx.Dialog):
	def __init__(self, parent):
		wx.Dialog.__init__(self, parent, -1, "Color Set", size=(480, 480),style= wx.DEFAULT_DIALOG_STYLE |wx.NO_FULL_REPAINT_ON_RESIZE)
		self.colorList = []
		self.overlapcolorList = []
		self.initiated = 0
		self.parent = parent

		vbox_top = wx.BoxSizer(wx.VERTICAL)

		vbox_top.Add(wx.StaticLine(self, -1, size=(480,1)), 0, wx.TOP | wx.LEFT, 9)

		panel1 = wx.Panel(self, -1)
		sizer1 = wx.StaticBoxSizer(wx.StaticBox(panel1, -1, 'Color set'), orient=wx.VERTICAL)
		self.colorSet = wx.ComboBox(panel1, -1, "Custom", (0,0), (270,30), ("ODP", "Corporate", "Maritime", "Earth", "Santa Fe", "Custom"), wx.CB_DROPDOWN)
		self.colorSet.SetForegroundColour(wx.BLACK)
		self.Bind(wx.EVT_COMBOBOX, self.SetColorSet, self.colorSet)
		self.colorSet.SetEditable(False)
		sizer1.Add(self.colorSet)
		panel1.SetSizer(sizer1)
		vbox_top.Add(panel1, 0, wx.TOP | wx.LEFT, 9)

		panel2 = wx.Panel(self, -1)
		grid1 = wx.GridSizer(1, 2)

		sizer2 = wx.StaticBoxSizer(wx.StaticBox(panel2, -1, 'Customize color'), orient=wx.VERTICAL)
		grid2 = wx.FlexGridSizer(16, 4)
		self.colorPicker01 = wx.ColourPickerCtrl(panel2, 1)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeColor, self.colorPicker01)
		grid2.Add(self.colorPicker01)
		if platform_name[0] == "Windows" :	
			grid2.Add(wx.StaticText(panel2, -1, 'mbsf             '))	
		else :
			grid2.Add(wx.StaticText(panel2, -1, 'mbsf'))

		self.colorPicker02 = wx.ColourPickerCtrl(panel2, 2)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeColor, self.colorPicker02)
		grid2.Add(self.colorPicker02, 0, wx.LEFT, 60)
		if platform_name[0] == "Windows" :		
			grid2.Add(wx.StaticText(panel2, -1, 'mcd               '))
		else :
			grid2.Add(wx.StaticText(panel2, -1, 'mcd'))
		self.colorPicker03 = wx.ColourPickerCtrl(panel2, 3)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeColor, self.colorPicker03)
		grid2.Add(self.colorPicker03)
		grid2.Add(wx.StaticText(panel2, -1, 'eld'))

		self.colorPicker04 = wx.ColourPickerCtrl(panel2, 4)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeColor, self.colorPicker04)
		grid2.Add(self.colorPicker04, 0, wx.LEFT, 60)
		grid2.Add(wx.StaticText(panel2, -1, 'Smooth'))

		self.colorPicker05 = wx.ColourPickerCtrl(panel2, 5)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeColor, self.colorPicker05)
		grid2.Add(self.colorPicker05)
		grid2.Add(wx.StaticText(panel2, -1, 'splice'))

		self.colorPicker06 = wx.ColourPickerCtrl(panel2, 6)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeColor, self.colorPicker06)
		grid2.Add(self.colorPicker06, 0, wx.LEFT, 60)
		grid2.Add(wx.StaticText(panel2, -1, 'log'))

		self.colorPicker07 = wx.ColourPickerCtrl(panel2, 7)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeColor, self.colorPicker07)
		grid2.Add(self.colorPicker07)
		grid2.Add(wx.StaticText(panel2, -1, 'mudline adjust'))

		self.colorPicker08 = wx.ColourPickerCtrl(panel2, 8)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeColor, self.colorPicker08)
		grid2.Add(self.colorPicker08, 0, wx.LEFT, 60)
		grid2.Add(wx.StaticText(panel2, -1, 'fixed tie'))

		self.colorPicker09 = wx.ColourPickerCtrl(panel2, 9)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeColor, self.colorPicker09)
		grid2.Add(self.colorPicker09)
		grid2.Add(wx.StaticText(panel2, -1, 'shift tie'))

		self.colorPicker10 = wx.ColourPickerCtrl(panel2, 10)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeColor, self.colorPicker10)
		grid2.Add(self.colorPicker10, 0, wx.LEFT, 60)
		grid2.Add(wx.StaticText(panel2, -1, 'paleomag'))

		self.colorPicker11 = wx.ColourPickerCtrl(panel2, 11)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeColor, self.colorPicker11)
		grid2.Add(self.colorPicker11)
		grid2.Add(wx.StaticText(panel2, -1, 'diatom'))

		self.colorPicker12 = wx.ColourPickerCtrl(panel2, 12)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeColor, self.colorPicker12)
		grid2.Add(self.colorPicker12, 0, wx.LEFT, 60)
		grid2.Add(wx.StaticText(panel2, -1, 'rad'))

		self.colorPicker13 = wx.ColourPickerCtrl(panel2, 13)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeColor, self.colorPicker13)
		grid2.Add(self.colorPicker13)
		grid2.Add(wx.StaticText(panel2, -1, 'foram'))

		self.colorPicker14 = wx.ColourPickerCtrl(panel2, 14)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeColor, self.colorPicker14)
		grid2.Add(self.colorPicker14, 0, wx.LEFT, 60)
		grid2.Add(wx.StaticText(panel2, -1, 'nano'))

		self.colorPicker15 = wx.ColourPickerCtrl(panel2, 15)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeColor, self.colorPicker15)
		grid2.Add(self.colorPicker15)
		grid2.Add(wx.StaticText(panel2, -1, 'background'))

		self.colorPicker16 = wx.ColourPickerCtrl(panel2, 16)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeColor, self.colorPicker16)
		grid2.Add(self.colorPicker16, 0, wx.LEFT, 60)
		grid2.Add(wx.StaticText(panel2, -1, 'labels'))

		self.colorPicker17 = wx.ColourPickerCtrl(panel2, 17)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeColor, self.colorPicker17)
		grid2.Add(self.colorPicker17)
		grid2.Add(wx.StaticText(panel2, -1, 'cor. window'))

		self.colorPicker18 = wx.ColourPickerCtrl(panel2, 18)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeColor, self.colorPicker18)
		grid2.Add(self.colorPicker18, 0, wx.LEFT, 60)
		grid2.Add(wx.StaticText(panel2, -1, 'guide'))

		sizer2.Add(grid2)
		grid1.Add(sizer2)

		sizer3 = wx.StaticBoxSizer(wx.StaticBox(panel2, -1, 'Overlapped hole color'), orient=wx.VERTICAL)
		grid3 = wx.FlexGridSizer(10, 2)
		self.holePicker01 = wx.ColourPickerCtrl(panel2, 1)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeHoleColor, self.holePicker01)
		grid3.Add(self.holePicker01, 0, wx.LEFT, 5)
		grid3.Add(wx.StaticText(panel2, -1, '1st hole             '))
		self.holePicker02 = wx.ColourPickerCtrl(panel2, 2)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeHoleColor, self.holePicker02)
		grid3.Add(self.holePicker02, 0, wx.LEFT, 5)
		grid3.Add(wx.StaticText(panel2, -1, '2nd hole'))
		self.holePicker03 = wx.ColourPickerCtrl(panel2, 3)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeHoleColor, self.holePicker03)
		grid3.Add(self.holePicker03, 0, wx.LEFT, 5)
		grid3.Add(wx.StaticText(panel2, -1, '3rd hole'))
		self.holePicker04 = wx.ColourPickerCtrl(panel2, 4)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeHoleColor, self.holePicker04)
		grid3.Add(self.holePicker04, 0, wx.LEFT, 5)
		grid3.Add(wx.StaticText(panel2, -1, '4th hole'))
		self.holePicker05 = wx.ColourPickerCtrl(panel2, 5)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeHoleColor, self.holePicker05)
		grid3.Add(self.holePicker05, 0, wx.LEFT, 5)
		grid3.Add(wx.StaticText(panel2, -1, '5th hole'))
		self.holePicker06 = wx.ColourPickerCtrl(panel2, 6)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeHoleColor, self.holePicker06)
		grid3.Add(self.holePicker06, 0, wx.LEFT, 5)
		grid3.Add(wx.StaticText(panel2, -1, '6th hole'))
		self.holePicker07 = wx.ColourPickerCtrl(panel2, 7)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeHoleColor, self.holePicker07)
		grid3.Add(self.holePicker07, 0, wx.LEFT, 5)
		grid3.Add(wx.StaticText(panel2, -1, '7th hole'))
		self.holePicker08 = wx.ColourPickerCtrl(panel2, 8)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeHoleColor, self.holePicker08)
		grid3.Add(self.holePicker08, 0, wx.LEFT, 5)
		grid3.Add(wx.StaticText(panel2, -1, '8th hole'))
		self.holePicker09 = wx.ColourPickerCtrl(panel2, 9)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeHoleColor, self.holePicker09)
		grid3.Add(self.holePicker09, 0, wx.LEFT, 5)
		grid3.Add(wx.StaticText(panel2, -1, '9th hole'))
		sizer3.Add(grid3)

		grid1.Add(sizer3, 0, wx.LEFT, 10)
		panel2.SetSizer(grid1)
		vbox_top.Add(panel2, 0, wx.TOP | wx.LEFT, 9)


		grid4 = wx.FlexGridSizer(1, 2)
		applyBtn = wx.Button(self, -1, "Apply", size=(120, 30))
		self.Bind(wx.EVT_BUTTON, self.OnApplyColor, applyBtn)
		grid4.Add(applyBtn, 0, wx.LEFT, 100)		

		cancelBtn = wx.Button(self, wx.ID_CANCEL, "Dismiss", size=(120, 30))
		grid4.Add(cancelBtn, 0, wx.LEFT, 25)		

		vbox_top.Add(grid4, 0, wx.LEFT | wx.TOP, 15)		

		self.SetSizer(vbox_top)
		self.updateItem()
		wx.EVT_KEY_UP(self, self.OnCharUp)

	def OnCharUp(self,event):
		keyid = event.GetKeyCode() 
		if keyid == wx.WXK_ESCAPE :
			self.EndModal(wx.ID_CANCEL) 


	def updateItem(self):
		if self.initiated == 0 :
			self.colorPicker01.SetColour(self.parent.Window.colorList[0])
			self.colorPicker02.SetColour(self.parent.Window.colorList[1])
			self.colorPicker03.SetColour(self.parent.Window.colorList[2])
			self.colorPicker04.SetColour(self.parent.Window.colorList[3])
			self.colorPicker05.SetColour(self.parent.Window.colorList[4])
			self.colorPicker06.SetColour(self.parent.Window.colorList[5])
			self.colorPicker07.SetColour(self.parent.Window.colorList[6])
			self.colorPicker08.SetColour(self.parent.Window.colorList[7])
			self.colorPicker09.SetColour(self.parent.Window.colorList[8])
			self.colorPicker10.SetColour(self.parent.Window.colorList[9])
			self.colorPicker11.SetColour(self.parent.Window.colorList[10])
			self.colorPicker12.SetColour(self.parent.Window.colorList[11])
			self.colorPicker13.SetColour(self.parent.Window.colorList[12])
			self.colorPicker14.SetColour(self.parent.Window.colorList[13])
			self.colorPicker15.SetColour(self.parent.Window.colorList[14])
			self.colorPicker16.SetColour(self.parent.Window.colorList[15])
			self.colorPicker17.SetColour(self.parent.Window.colorList[16])
			self.colorPicker18.SetColour(self.parent.Window.colorList[17])

			self.holePicker01.SetColour(self.parent.Window.overlapcolorList[0])
			self.holePicker02.SetColour(self.parent.Window.overlapcolorList[1])
			self.holePicker03.SetColour(self.parent.Window.overlapcolorList[2])
			self.holePicker04.SetColour(self.parent.Window.overlapcolorList[3])
			self.holePicker05.SetColour(self.parent.Window.overlapcolorList[4])
			self.holePicker06.SetColour(self.parent.Window.overlapcolorList[5])
			self.holePicker07.SetColour(self.parent.Window.overlapcolorList[6])
			self.holePicker08.SetColour(self.parent.Window.overlapcolorList[7])
			self.holePicker09.SetColour(self.parent.Window.overlapcolorList[8])

			for i in range(18) :
				self.colorList.insert(i, self.parent.Window.colorList[i])

			for i in range(9) :
				self.overlapcolorList.insert(i, self.parent.Window.overlapcolorList[i])
			self.initiated = 1

	def SetColorSet(self, event):
		# mbsf, mcd, eld, smooth, splice, log, mudline adjust, fixed tie, shift tie
		# paleomag, diatom, rad, foram, nano
		#"ODP", "Corporate", "Maritime", "Earth", "Santa Fe", "Custom"
		self.colorList = []
		if self.colorSet.GetValue() == "ODP" :
			self.colorList = [ wx.Color(255, 215, 0), wx.Color(30, 144, 255), \
			wx.Color(127, 255, 212), wx.Color(255, 246, 143), wx.Color(30, 144, 255), \
			wx.Color(255, 0, 0), wx.Color(155, 48, 255), wx.Color(139, 0, 0), \
			wx.Color(0, 139, 0), wx.Color(139, 0, 0), wx.Color(173, 255, 47), \
			wx.Color(255, 255, 255), wx.Color(255, 140, 0), wx.Color(0, 245, 255), wx.Color(0, 0, 0), wx.Color(255, 255, 255), wx.Color(30, 144, 255), wx.Color(224, 255, 255)] 
		elif self.colorSet.GetValue() == "Corporate" :
			self.colorList = [ wx.Color(34, 139, 34), wx.Color(0, 0, 255), \
			wx.Color(0, 255, 255), wx.Color(205, 133, 63), wx.Color(139, 76, 57), \
			wx.Color(125, 38, 205), wx.Color(105, 139, 105), wx.Color(139, 0, 0), \
			wx.Color(0, 139, 0), wx.Color(30, 144, 255), wx.Color(255, 255, 255), \
			wx.Color(143, 188, 143), wx.Color(255, 20, 147), wx.Color(72, 61, 139), wx.Color(220, 220, 220), wx.Color(0, 0, 0), wx.Color(30, 144, 255), wx.Color(224, 255, 255)] 
		elif self.colorSet.GetValue() == "Maritime" :
			self.colorList = [ wx.Color(60, 179, 113), wx.Color(250, 128, 114), \
			wx.Color(72, 61, 139), wx.Color(92, 92, 92), wx.Color(25, 25, 112), \
			wx.Color(125, 38, 205), wx.Color(255, 99, 71), wx.Color(255, 0, 0), \
			wx.Color(0, 255, 0), wx.Color(255, 0, 0), wx.Color(0, 255, 0), \
			wx.Color(255, 255, 255), wx.Color(255, 192, 203), wx.Color(191, 239, 255), wx.Color(102, 205, 170), wx.Color(54, 100, 139), wx.Color(30, 144, 255), wx.Color(224, 255, 255)] 
		elif self.colorSet.GetValue() == "Earth" :
			self.colorList = [ wx.Color(112, 128, 144), wx.Color(85, 107, 47), \
			wx.Color(0, 255, 255), wx.Color(150, 150, 150), wx.Color(135, 206, 235), \
			wx.Color(238, 130, 238), wx.Color(165, 42, 42), wx.Color(255, 0, 0), \
			wx.Color(0, 255, 0), wx.Color(0, 0, 255), wx.Color(0, 255, 127), \
			wx.Color(255, 255, 255), wx.Color(255, 105, 180), wx.Color(165, 42, 42), wx.Color(255, 222, 173), wx.Color(165, 42, 42), wx.Color(30, 144, 255), wx.Color(224, 255, 255)] 
		elif self.colorSet.GetValue() == "Santa Fe" :
			self.colorList = [ wx.Color(0, 100, 0), wx.Color(99, 184, 255), \
			wx.Color(0, 255, 255), wx.Color(255, 228, 225), wx.Color(255, 105, 180), \
			wx.Color(160, 32, 240), wx.Color(255, 192, 203), wx.Color(255, 0, 0), \
			wx.Color(0, 255, 0), wx.Color(255, 0, 0), wx.Color(255, 255, 255), \
			wx.Color(155, 205, 155), wx.Color(255, 20, 147), wx.Color(100, 149, 237), wx.Color(205, 85, 85), wx.Color(255, 231, 186), wx.Color(30, 144, 255), wx.Color(224, 255, 255)] 
		elif self.colorSet.GetValue() == "Custom" :
			for i in range(18) :
				self.colorList.insert(i, self.parent.Window.colorList[i])

		self.colorPicker01.SetColour(self.colorList[0])
		self.colorPicker02.SetColour(self.colorList[1])
		self.colorPicker03.SetColour(self.colorList[2])
		self.colorPicker04.SetColour(self.colorList[3])
		self.colorPicker05.SetColour(self.colorList[4])
		self.colorPicker06.SetColour(self.colorList[5])
		self.colorPicker07.SetColour(self.colorList[6])
		self.colorPicker08.SetColour(self.colorList[7])
		self.colorPicker09.SetColour(self.colorList[8])
		self.colorPicker10.SetColour(self.colorList[9])
		self.colorPicker11.SetColour(self.colorList[10])
		self.colorPicker12.SetColour(self.colorList[11])
		self.colorPicker13.SetColour(self.colorList[12])
		self.colorPicker14.SetColour(self.colorList[13])
		self.colorPicker15.SetColour(self.colorList[14])
		self.colorPicker16.SetColour(self.colorList[15])
		self.colorPicker17.SetColour(self.colorList[16])
		self.colorPicker18.SetColour(self.colorList[17])

		self.holePicker01.SetColour(self.overlapcolorList[0])
		self.holePicker02.SetColour(self.overlapcolorList[1])
		self.holePicker03.SetColour(self.overlapcolorList[2])
		self.holePicker04.SetColour(self.overlapcolorList[3])
		self.holePicker05.SetColour(self.overlapcolorList[4])
		self.holePicker06.SetColour(self.overlapcolorList[5])
		self.holePicker07.SetColour(self.overlapcolorList[6])
		self.holePicker08.SetColour(self.overlapcolorList[7])
		self.holePicker09.SetColour(self.overlapcolorList[8])

	def ChangeHoleColor(self, event):
		idx = event.GetId() - 1
		self.overlapcolorList.pop(idx)
		if idx == 0 :
			self.overlapcolorList.insert(idx, self.holePicker01.GetColour())
		elif idx == 1 :
			self.overlapcolorList.insert(idx, self.holePicker02.GetColour())
		elif idx == 2 :
			self.overlapcolorList.insert(idx, self.holePicker03.GetColour())
		elif idx == 3 :
			self.overlapcolorList.insert(idx, self.holePicker04.GetColour())
		elif idx == 4 :
			self.overlapcolorList.insert(idx, self.holePicker05.GetColour())
		elif idx == 5 :
			self.overlapcolorList.insert(idx, self.holePicker06.GetColour())
		elif idx == 6 :
			self.overlapcolorList.insert(idx, self.holePicker07.GetColour())
		elif idx == 7 :
			self.overlapcolorList.insert(idx, self.holePicker08.GetColour())
		elif idx == 8 :
			self.overlapcolorList.insert(idx, self.holePicker09.GetColour())

	def ChangeColor(self, event):
		self.colorSet.SetStringSelection("Custom")
		idx = event.GetId() - 1
		self.colorList.pop(idx)
		if idx == 0 :
			self.colorList.insert(idx, self.colorPicker01.GetColour())
		elif idx == 1 :
			self.colorList.insert(idx, self.colorPicker02.GetColour())
		elif idx == 2 :
			self.colorList.insert(idx, self.colorPicker03.GetColour())
		elif idx == 3 :
			self.colorList.insert(idx, self.colorPicker04.GetColour())
		elif idx == 4 :
			self.colorList.insert(idx, self.colorPicker05.GetColour())
		elif idx == 5 :
			self.colorList.insert(idx, self.colorPicker06.GetColour())
		elif idx == 6 :
			self.colorList.insert(idx, self.colorPicker07.GetColour())
		elif idx == 7 :
			self.colorList.insert(idx, self.colorPicker08.GetColour())
		elif idx == 8 :
			self.colorList.insert(idx, self.colorPicker09.GetColour())
		elif idx == 9 :
			self.colorList.insert(idx, self.colorPicker10.GetColour())
		elif idx == 10 :
			self.colorList.insert(idx, self.colorPicker11.GetColour())
		elif idx == 11 :
			self.colorList.insert(idx, self.colorPicker12.GetColour())
		elif idx == 12 :
			self.colorList.insert(idx, self.colorPicker13.GetColour())
		elif idx == 13 :
			self.colorList.insert(idx, self.colorPicker14.GetColour())
		elif idx == 14 :
			self.colorList.insert(idx, self.colorPicker15.GetColour())
		elif idx == 15 :
			self.colorList.insert(idx, self.colorPicker16.GetColour())
		elif idx == 16 :
			self.colorList.insert(idx, self.colorPicker17.GetColour())
		elif idx == 17 :
			self.colorList.insert(idx, self.colorPicker18.GetColour())

	def OnApplyColor(self, event):
		self.parent.Window.colorList = []
		for i in range(18) :
			self.parent.Window.colorList.insert(i, self.colorList[i])

		self.parent.Window.overlapcolorList = []
		for i in range(9) :
			self.parent.Window.overlapcolorList.insert(i, self.overlapcolorList[i])
		self.parent.Window.UpdateDrawing()



class AboutDialog(wx.Dialog):
	def __init__(self, parent, version) :
		wx.Dialog.__init__(self, parent, -1, "About Correlator V" + version, size=(500, 300), style= wx.DEFAULT_DIALOG_STYLE |wx.NO_FULL_REPAINT_ON_RESIZE |wx.STAY_ON_TOP)
		wx.StaticText(self, -1, 'Correlator facilitates the adjustment of core depth data drilled in', (20, 10))
		wx.StaticText(self, -1, 'a multi-hole scenario by usually correlating measured whole-core', (20, 30))
		wx.StaticText(self, -1, '(GRA, MSLP, PWC,#NGR) or half-core (RSC) sensor data across holes using', (20, 50))
		wx.StaticText(self, -1, 'an optimized cross-correlation approach.', (20, 70))

		wx.StaticText(self, -1, 'For more detail information, ', (20, 90))
		wx.HyperlinkCtrl(self, -1, 'Go to Correlator Web', 'http://sqlcore.geo.umn.edu/CoreWallDatabase/cwWiki/index.php/Correlator', (200, 90))


		wx.StaticText(self, -1, 'Developer:  Sean Higgins(shiggins@oceanleadership.org)', (20, 130))
		wx.StaticText(self, -1, 'Hyejung Hur(hhur2@uic.edu)', (95, 150))

		wx.StaticText(self, -1, 'Organization: ', (20, 180))
		wx.HyperlinkCtrl(self, -1, 'EVL', 'http://www.evl.uic.edu', (20, 200))
		wx.HyperlinkCtrl(self, -1, 'NSF', 'http://www.nsf.gov/', (20, 220))
		wx.HyperlinkCtrl(self, -1, 'LacCore', 'http://lrc.geo.umn.edu/LacCore/laccore.html', (120, 200))
		wx.HyperlinkCtrl(self, -1, 'Lamont Doherty', 'http://www.ldeo.columbia.edu/', (120, 220))

		wx.StaticText(self, -1, '2009. May', (400, 240))
		okBtn = wx.Button(self, wx.ID_OK, "Close", ((230, 240)))
		wx.EVT_KEY_UP(self, self.OnCharUp)

	def OnCharUp(self,event):
		keyid = event.GetKeyCode() 
		if keyid == wx.WXK_ESCAPE :
			self.EndModal(wx.ID_CANCEL) 


class BackgroundPanel(wx.Panel):
        def __init__(self, parent, background, panel_size):
                wx.Panel.__init__(self, parent, -1, size=panel_size)
        
                img = wx.Image(background, wx.BITMAP_TYPE_ANY)
                self.buffer = wx.BitmapFromImage(img)
                dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
            
                self.Bind(wx.EVT_PAINT, self.OnPaint)

        def OnPaint(self, evt):
                dc = wx.BufferedPaintDC(self, self.buffer)
        
class OpenFrame(wx.Dialog):
	def __init__(self, parent, id, user, version):
                panel_size=(800, 370)
		wx.Dialog.__init__(self, parent, id, "Correlator v" + version, size=panel_size,style= wx.DEFAULT_DIALOG_STYLE |wx.NO_FULL_REPAINT_ON_RESIZE |wx.STAY_ON_TOP)

		#panel = wx.Panel ( self, -1, size=(800, 370), style=wx.BORDER)
		panel = BackgroundPanel(self, 'images/corewall_suite.jpg', panel_size)
 
		self.version = version
		#picture = wx.StaticBitmap(self)
		#picture.SetBitmap(wx.Bitmap('images/corewall_suite.jpg'))
		wx.StaticText(self, -1, 'COMPOSITE, SPLICE, CORE-LOG INTEGRATION, AGE MODEL', (60, 30))

		#self.SetBackgroundColour(wx.Color(255, 255, 255))

		wx.StaticText(self, -1, 'User Name : ', (250, 220))
		self.name = wx.TextCtrl(self, -1, user, (340, 220), size=(150, 25))
		     
		okBtn = wx.Button(panel, -1, "START", (500, 220), size=(80, 30))
				
		self.Bind(wx.EVT_BUTTON, self.OnSTART, okBtn)
		self.user = user

                if platform_name[0] == "Windows" :
                        cancelBtn = wx.Button(panel, wx.ID_CANCEL, "CANCEL", (580, 220), size=(80, 30))

		#wx.StaticText(self, -1, 'Developer:  Sean Higgins, Hyejung Hur', (60, 280))
		wx.HyperlinkCtrl(self, -1, 'Go to Correlator Web', 'http://sqlcore.geo.umn.edu/CoreWallDatabase/cwWiki/index.php/Correlator', (60, 300))

		aboutBtn = wx.Button(panel, -1, "ABOUT", (200, 300), size=(80, 30))
		self.Bind(wx.EVT_BUTTON, self.OnABOUT, aboutBtn)
                #self.SetFocusFromKbd()

		wx.EVT_KEY_DOWN(self.name, self.OnChar)
		wx.EVT_KEY_DOWN(self, self.OnChar)

	def OnABOUT(self, event) :
		dlg = AboutDialog(self, self.version)
		dlg.Centre()
		dlg.ShowModal()
		dlg.Destroy()

	def OnSTART(self, event) :
		self.user = self.name.GetValue()
		self.EndModal(wx.ID_OK) 
	
	def OnChar(self,event):
		keyid = event.GetKeyCode()
		if keyid == 13 :
			# ENTER
			self.user = self.name.GetValue()
			self.EndModal(wx.ID_OK) 
		elif keyid == 27 :
			# ESC 
			self.EndModal(wx.ID_CANCEL) 

