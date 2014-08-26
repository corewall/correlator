#!/usr/bin/env python

## For Mac-OSX
#/usr/bin/env pythonw
import platform
platform_name = platform.uname()

import wx 
import wx.lib.sheet as sheet
from wx.lib import plot
import random, sys, os, re, time, ConfigParser, string
import numpy
from datetime import datetime

import dbutils as dbu
import dialog
import globals as glb
import model

from importManager import py_correlator

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


def MessageDialog(parent, title, msg, nobutton):
	style = 0
	if title == "Error":
		style = wx.ICON_ERROR
	elif title == "About" or title == "Help" or title == "Information":
		style = wx.ICON_INFORMATION

	if nobutton == 0:
		style = style | wx.YES_NO
	elif nobutton == 1:
		style = style | wx.OK
	elif nobutton == 2:
		style = style | wx.OK | wx.CANCEL

	return wx.MessageDialog(parent, msg, title, style)

class MessageDialogOLD(wx.Dialog):
	def __init__(self, parent, title, msg, nobutton):
		if title == "About" or title == "Help" : 
			wx.Dialog.__init__(self, parent, -1, title, size=(330, 130), style= wx.STAY_ON_TOP)
		else :
			wx.Dialog.__init__(self, parent, -1, title, size=(330, 110), style= wx.STAY_ON_TOP)

		self.Center()
		vbox_top = wx.BoxSizer(wx.VERTICAL)
		panel1 = wx.Panel(self, -1, style = wx.WANTS_CHARS)
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

		#wx.EVT_KEY_UP(self, self.OnCharUp)
		panel1.Bind(wx.EVT_CHAR, self.OnCharUp)
		self.SetSizer(vbox_top)

	# 9/17/2013 brg: Seems we only need to handle enter for Okay, escape
	# is automatically handled by wx.Dialog
	def OnCharUp(self,event):
		if event.GetKeyCode() == wx.WXK_RETURN :
			self.EndModal(wx.ID_OK)
		else:
			event.Skip()

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


class AddTypeDialog(wx.Dialog):
	def __init__(self, parent):
		wx.Dialog.__init__(self, parent, -1, title="Add Custom Data Type", size=(300, 130),
						   style=wx.STAY_ON_TOP | wx.DEFAULT_DIALOG_STYLE)

		self.Center()
		vbox_top = wx.BoxSizer(wx.VERTICAL)
		self.txt = wx.TextCtrl(self, -1, "[new type]", size = (270, 25), style=wx.SUNKEN_BORDER )

		vbox_top.Add(self.txt, 0, wx.LEFT | wx.TOP | wx.BOTTOM, 10)

		grid = wx.FlexGridSizer(1, 3, vgap=0, hgap=10)
		self.register = wx.CheckBox(self, -1, 'Register')
		grid.Add(self.register, 1)
		okBtn = wx.Button(self, wx.ID_OK, "OK")
		okBtn.SetDefault()
		grid.Add(okBtn, 1)
		cancelBtn = wx.Button(self, wx.ID_CANCEL, "Cancel")
		grid.Add(cancelBtn, 1)
		vbox_top.Add(grid, 0, wx.LEFT, 20)

		self.SetSizer(vbox_top)

		self.Bind(wx.EVT_BUTTON, self.OnOK, okBtn)
		wx.EVT_KEY_UP(self, self.OnCharUp)

	def OnOK(self, event):
		newType = self.txt.GetValue()
		if len(newType) == 0:
			glb.OnShowMessage("Error", "Enter a type name", 1)
			return
		if newType.find("-", 0) >= 0:
			glb.OnShowMessage("Error", "Types cannot contain hyphens (-)", 1)
			return
		elif glb.UserTypeExists(newType):
			glb.OnShowMessage("Error", "The type '{}' already exists".format(newType), 1)
			return
		else:
			if self.register.GetValue() == True:
				glb.AddUserType(newType)
			self.EndModal(wx.ID_OK)

	# brgtodo 8/12/2014: this isn't getting hit on Mac, but setting OK button
	# as default accomplishes the same result as this code, and Escape already
	# worked correctly - check on Windows, may be unnecessary
	def OnCharUp(self,event):
		keyid = event.GetKeyCode() 
		if keyid == wx.WXK_RETURN:
			self.OnOK()
		elif keyid == wx.WXK_ESCAPE:
			self.EndModal(wx.ID_CANCEL)

class EditBoxDialog(wx.Dialog):
	def __init__(self, parent, title):
		wx.Dialog.__init__(self, parent, -1, title, size=(300, 130),
							style=wx.STAY_ON_TOP | wx.DEFAULT_DIALOG_STYLE)

		self.Center()
		vbox_top = wx.BoxSizer(wx.VERTICAL)
		self.txt = wx.TextCtrl(self, -1, "", size = (270, 25), style=wx.SUNKEN_BORDER )

		vbox_top.Add(self.txt, 0, wx.LEFT | wx.TOP | wx.BOTTOM, 15)

		grid = wx.GridSizer(1,2)
		okBtn = wx.Button(self, wx.ID_OK, "OK")
		okBtn.SetDefault()
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
		self.types = wx.ComboBox(self, -1, "Diatoms", (0,0), (250, -1), ("Diatoms", "Radioloria", "Foraminifera", "Nannofossils", "Paleomag"), wx.CB_DROPDOWN)

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

		wx.Button(self, wx.ID_OK, "Select", ((25, 135)))
		wx.Button(self, wx.ID_CANCEL, "Cancel", ((110, 135)))
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

		wx.Button(self, wx.ID_OK, "Save", ((85, 265)))
		wx.Button(self, wx.ID_CANCEL, "Cancel", ((180, 265)))
		wx.EVT_KEY_UP(self, self.OnCharUp)

	def OnCharUp(self,event):
		keyid = event.GetKeyCode() 
		if keyid == wx.WXK_RETURN :
			self.EndModal(wx.ID_OK) 
		elif keyid == wx.WXK_ESCAPE :
			self.EndModal(wx.ID_CANCEL) 


class ExportCoreDialog(wx.Dialog):
	def __init__(self, parent):
		wx.Dialog.__init__(self, parent, -1, "Export Core", size=(300, 260),style= wx.DEFAULT_DIALOG_STYLE |wx.NO_FULL_REPAINT_ON_RESIZE)

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
		wx.Button(self, wx.ID_CANCEL, "Cancel", ((140, 200)))
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
		self.all = wx.ComboBox(panel, -1, "", (90,20), (220,-1), (""), wx.CB_DROPDOWN)
		for types in parent.Window.range :
			if types[0] != "splice" and types[0] != "altsplice" :
				self.all.Append(types[0])
		if self.all.GetCount() > 0 :
			self.all.Select(0)

		self.all.SetForegroundColour(wx.BLACK)
		self.all.SetEditable(False)
		#self.Bind(wx.EVT_COMBOBOX, self.SetTYPE, self.all)

		self.splice = wx.ComboBox(panel, -1, "", (90,60), (220,-1), (""), wx.CB_DROPDOWN)
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
		okBtn = wx.Button(self, -1, "Select", (70, 135))
		self.Bind(wx.EVT_BUTTON, self.OnSELECT, okBtn)
		cancelBtn = wx.Button(self, wx.ID_CANCEL, "Cancel", (210, 135))
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

		panel1 = wx.Panel(self, -1)
		sizer1 = wx.StaticBoxSizer(wx.StaticBox(panel1, -1, 'Color set'), orient=wx.VERTICAL)
		self.colorSet = wx.ComboBox(panel1, -1, "Custom", (0,0), (270,-1), ("ODP", "Corporate", "Maritime", "Earth", "Santa Fe", "Custom"), wx.CB_DROPDOWN)
		self.colorSet.SetForegroundColour(wx.BLACK)
		self.Bind(wx.EVT_COMBOBOX, self.SetColorSet, self.colorSet)
		self.colorSet.SetEditable(False)
		sizer1.Add(self.colorSet)
		panel1.SetSizer(sizer1)
		vbox_top.Add(panel1, 0, wx.TOP | wx.LEFT, 9)

		panel2 = wx.Panel(self, -1)
		grid1 = wx.GridSizer(1, 2)

		sizer2 = wx.StaticBoxSizer(wx.StaticBox(panel2, -1, 'Customize color'), orient=wx.VERTICAL)
		grid2 = wx.FlexGridSizer(9, 4)
		self.colorPicker01 = wx.ColourPickerCtrl(panel2, 1)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeColor, self.colorPicker01)
		grid2.Add(self.colorPicker01)
		
		if platform_name[0] == "Windows" :	
			grid2.Add(wx.StaticText(panel2, -1, 'mbsf             '))	
		else :
			grid2.Add(wx.StaticText(panel2, -1, 'mbsf'))

		self.colorPicker02 = wx.ColourPickerCtrl(panel2, 2)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeColor, self.colorPicker02)
		grid2.Add(self.colorPicker02, 0, wx.LEFT, 10)
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
		grid2.Add(self.colorPicker04, 0, wx.LEFT, 10)
		grid2.Add(wx.StaticText(panel2, -1, 'Smooth'))

		self.colorPicker05 = wx.ColourPickerCtrl(panel2, 5)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeColor, self.colorPicker05)
		grid2.Add(self.colorPicker05)
		grid2.Add(wx.StaticText(panel2, -1, 'splice'))

		self.colorPicker06 = wx.ColourPickerCtrl(panel2, 6)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeColor, self.colorPicker06)
		grid2.Add(self.colorPicker06, 0, wx.LEFT, 10)
		grid2.Add(wx.StaticText(panel2, -1, 'log'))

		self.colorPicker07 = wx.ColourPickerCtrl(panel2, 7)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeColor, self.colorPicker07)
		grid2.Add(self.colorPicker07)
		grid2.Add(wx.StaticText(panel2, -1, 'mudline adjust'))

		self.colorPicker08 = wx.ColourPickerCtrl(panel2, 8)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeColor, self.colorPicker08)
		grid2.Add(self.colorPicker08, 0, wx.LEFT, 10)
		grid2.Add(wx.StaticText(panel2, -1, 'fixed tie'))

		self.colorPicker09 = wx.ColourPickerCtrl(panel2, 9)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeColor, self.colorPicker09)
		grid2.Add(self.colorPicker09)
		grid2.Add(wx.StaticText(panel2, -1, 'shift tie'))

		self.colorPicker10 = wx.ColourPickerCtrl(panel2, 10)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeColor, self.colorPicker10)
		grid2.Add(self.colorPicker10, 0, wx.LEFT, 10)
		grid2.Add(wx.StaticText(panel2, -1, 'paleomag'))

		self.colorPicker11 = wx.ColourPickerCtrl(panel2, 11)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeColor, self.colorPicker11)
		grid2.Add(self.colorPicker11)
		grid2.Add(wx.StaticText(panel2, -1, 'diatom'))

		self.colorPicker12 = wx.ColourPickerCtrl(panel2, 12)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeColor, self.colorPicker12)
		grid2.Add(self.colorPicker12, 0, wx.LEFT, 10)
		grid2.Add(wx.StaticText(panel2, -1, 'rad'))

		self.colorPicker13 = wx.ColourPickerCtrl(panel2, 13)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeColor, self.colorPicker13)
		grid2.Add(self.colorPicker13)
		grid2.Add(wx.StaticText(panel2, -1, 'foram'))

		self.colorPicker14 = wx.ColourPickerCtrl(panel2, 14)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeColor, self.colorPicker14)
		grid2.Add(self.colorPicker14, 0, wx.LEFT, 10)
		grid2.Add(wx.StaticText(panel2, -1, 'nano'))

		self.colorPicker15 = wx.ColourPickerCtrl(panel2, 15)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeColor, self.colorPicker15)
		grid2.Add(self.colorPicker15)
		grid2.Add(wx.StaticText(panel2, -1, 'background'))

		self.colorPicker16 = wx.ColourPickerCtrl(panel2, 16)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeColor, self.colorPicker16)
		grid2.Add(self.colorPicker16, 0, wx.LEFT, 10)
		grid2.Add(wx.StaticText(panel2, -1, 'labels'))

		self.colorPicker17 = wx.ColourPickerCtrl(panel2, 17)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeColor, self.colorPicker17)
		grid2.Add(self.colorPicker17)
		grid2.Add(wx.StaticText(panel2, -1, 'cor. window'))

		self.colorPicker18 = wx.ColourPickerCtrl(panel2, 18)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeColor, self.colorPicker18)
		grid2.Add(self.colorPicker18, 0, wx.LEFT, 10)
		grid2.Add(wx.StaticText(panel2, -1, 'guide'))

		sizer2.Add(grid2)
		grid1.Add(sizer2)

		sizer3 = wx.StaticBoxSizer(wx.StaticBox(panel2, -1, 'Overlapped hole color'), orient=wx.VERTICAL)
		grid3 = wx.FlexGridSizer(10, 2)
		# 9/17/2012 brg: start holePicker IDs at 101 to avoid collision with colorPicker IDs
		self.holePicker01 = wx.ColourPickerCtrl(panel2, 101)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeHoleColor, self.holePicker01)
		grid3.Add(self.holePicker01, 0, wx.LEFT, 5)
		grid3.Add(wx.StaticText(panel2, -1, '1st hole             '))
		self.holePicker02 = wx.ColourPickerCtrl(panel2, 102)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeHoleColor, self.holePicker02)
		grid3.Add(self.holePicker02, 0, wx.LEFT, 5)
		grid3.Add(wx.StaticText(panel2, -1, '2nd hole'))
		self.holePicker03 = wx.ColourPickerCtrl(panel2, 103)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeHoleColor, self.holePicker03)
		grid3.Add(self.holePicker03, 0, wx.LEFT, 5)
		grid3.Add(wx.StaticText(panel2, -1, '3rd hole'))
		self.holePicker04 = wx.ColourPickerCtrl(panel2, 104)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeHoleColor, self.holePicker04)
		grid3.Add(self.holePicker04, 0, wx.LEFT, 5)
		grid3.Add(wx.StaticText(panel2, -1, '4th hole'))
		self.holePicker05 = wx.ColourPickerCtrl(panel2, 105)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeHoleColor, self.holePicker05)
		grid3.Add(self.holePicker05, 0, wx.LEFT, 5)
		grid3.Add(wx.StaticText(panel2, -1, '5th hole'))
		self.holePicker06 = wx.ColourPickerCtrl(panel2, 106)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeHoleColor, self.holePicker06)
		grid3.Add(self.holePicker06, 0, wx.LEFT, 5)
		grid3.Add(wx.StaticText(panel2, -1, '6th hole'))
		self.holePicker07 = wx.ColourPickerCtrl(panel2, 107)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeHoleColor, self.holePicker07)
		grid3.Add(self.holePicker07, 0, wx.LEFT, 5)
		grid3.Add(wx.StaticText(panel2, -1, '7th hole'))
		self.holePicker08 = wx.ColourPickerCtrl(panel2, 108)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeHoleColor, self.holePicker08)
		grid3.Add(self.holePicker08, 0, wx.LEFT, 5)
		grid3.Add(wx.StaticText(panel2, -1, '8th hole'))
		self.holePicker09 = wx.ColourPickerCtrl(panel2, 109)
		self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.ChangeHoleColor, self.holePicker09)
		grid3.Add(self.holePicker09, 0, wx.LEFT, 5)
		grid3.Add(wx.StaticText(panel2, -1, '9th hole'))
		sizer3.Add(grid3)

		grid1.Add(sizer3, 0, wx.LEFT, 30)
		panel2.SetSizer(grid1)
		vbox_top.Add(panel2, 0, wx.TOP | wx.LEFT, 9)


		grid4 = wx.FlexGridSizer(1, 2)
		applyBtn = wx.Button(self, -1, "Apply", size=(120, 30))
		self.Bind(wx.EVT_BUTTON, self.OnApplyColor, applyBtn)
		grid4.Add(applyBtn, 0, wx.LEFT, 100)		

		cancelBtn = wx.Button(self, wx.ID_CANCEL, "Dismiss", size=(120, 30))
		grid4.Add(cancelBtn, 0, wx.LEFT, 25)		

		vbox_top.Add(grid4, 0, wx.LEFT | wx.TOP, 0)

		self.SetSizer(vbox_top)
		self.updateItem()
		wx.EVT_KEY_UP(self, self.OnCharUp)

	def OnCharUp(self,event):
		keyid = event.GetKeyCode() 
		if keyid == wx.WXK_ESCAPE :
			self.EndModal(wx.ID_CANCEL) 


	def updateItem(self):
		if self.initiated == 0 :
			self.colorPicker01.SetColour(self.parent.Window.colorDict['mbsf'])
			self.colorPicker02.SetColour(self.parent.Window.colorDict['mcd'])
			self.colorPicker03.SetColour(self.parent.Window.colorDict['eld'])
			self.colorPicker04.SetColour(self.parent.Window.colorDict['smooth'])
			self.colorPicker05.SetColour(self.parent.Window.colorDict['splice'])
			self.colorPicker06.SetColour(self.parent.Window.colorDict['log'])
			self.colorPicker07.SetColour(self.parent.Window.colorDict['mudlineAdjust'])
			self.colorPicker08.SetColour(self.parent.Window.colorDict['fixedTie'])
			self.colorPicker09.SetColour(self.parent.Window.colorDict['shiftTie'])
			self.colorPicker10.SetColour(self.parent.Window.colorDict['paleomag'])
			self.colorPicker11.SetColour(self.parent.Window.colorDict['diatom'])
			self.colorPicker12.SetColour(self.parent.Window.colorDict['rad'])
			self.colorPicker13.SetColour(self.parent.Window.colorDict['foram'])
			self.colorPicker14.SetColour(self.parent.Window.colorDict['nano'])
			self.colorPicker15.SetColour(self.parent.Window.colorDict['background'])
			self.colorPicker16.SetColour(self.parent.Window.colorDict['foreground'])
			self.colorPicker17.SetColour(self.parent.Window.colorDict['corrWindow'])
			self.colorPicker18.SetColour(self.parent.Window.colorDict['guide'])

			self.holePicker01.SetColour(self.parent.Window.overlapcolorList[0])
			self.holePicker02.SetColour(self.parent.Window.overlapcolorList[1])
			self.holePicker03.SetColour(self.parent.Window.overlapcolorList[2])
			self.holePicker04.SetColour(self.parent.Window.overlapcolorList[3])
			self.holePicker05.SetColour(self.parent.Window.overlapcolorList[4])
			self.holePicker06.SetColour(self.parent.Window.overlapcolorList[5])
			self.holePicker07.SetColour(self.parent.Window.overlapcolorList[6])
			self.holePicker08.SetColour(self.parent.Window.overlapcolorList[7])
			self.holePicker09.SetColour(self.parent.Window.overlapcolorList[8])

			for key in self.parent.Window.colorDictKeys :
				self.colorList.append(self.parent.Window.colorDict[key])

			for i in range(9) :
				self.overlapcolorList.insert(i, self.parent.Window.overlapcolorList[i])
			self.initiated = 1

	def SetColorSet(self, event):
		# mbsf, mcd, eld, smooth, splice, log, mudline adjust, fixed tie, shift tie
		# paleomag, diatom, rad, foram, nano
		#"ODP", "Corporate", "Maritime", "Earth", "Santa Fe", "Custom"
		self.colorList = []
		if self.colorSet.GetValue() == "ODP" :
			self.colorList = [ wx.Colour(255, 215, 0), wx.Colour(30, 144, 255), \
			wx.Colour(127, 255, 212), wx.Colour(255, 246, 143), wx.Colour(30, 144, 255), \
			wx.Colour(255, 0, 0), wx.Colour(155, 48, 255), wx.Colour(139, 0, 0), \
			wx.Colour(0, 139, 0), wx.Colour(139, 0, 0), wx.Colour(173, 255, 47), \
			wx.Colour(255, 255, 255), wx.Colour(255, 140, 0), wx.Colour(0, 245, 255), wx.Colour(0, 0, 0), wx.Colour(255, 255, 255), wx.Colour(30, 144, 255), wx.Colour(224, 255, 255)] 
		elif self.colorSet.GetValue() == "Corporate" :
			self.colorList = [ wx.Colour(34, 139, 34), wx.Colour(0, 0, 255), \
			wx.Colour(0, 255, 255), wx.Colour(205, 133, 63), wx.Colour(139, 76, 57), \
			wx.Colour(125, 38, 205), wx.Colour(105, 139, 105), wx.Colour(139, 0, 0), \
			wx.Colour(0, 139, 0), wx.Colour(30, 144, 255), wx.Colour(255, 255, 255), \
			wx.Colour(143, 188, 143), wx.Colour(255, 20, 147), wx.Colour(72, 61, 139), wx.Colour(220, 220, 220), wx.Colour(0, 0, 0), wx.Colour(30, 144, 255), wx.Colour(224, 255, 255)] 
		elif self.colorSet.GetValue() == "Maritime" :
			self.colorList = [ wx.Colour(60, 179, 113), wx.Colour(250, 128, 114), \
			wx.Colour(72, 61, 139), wx.Colour(92, 92, 92), wx.Colour(25, 25, 112), \
			wx.Colour(125, 38, 205), wx.Colour(255, 99, 71), wx.Colour(255, 0, 0), \
			wx.Colour(0, 255, 0), wx.Colour(255, 0, 0), wx.Colour(0, 255, 0), \
			wx.Colour(255, 255, 255), wx.Colour(255, 192, 203), wx.Colour(191, 239, 255), wx.Colour(102, 205, 170), wx.Colour(54, 100, 139), wx.Colour(30, 144, 255), wx.Colour(224, 255, 255)] 
		elif self.colorSet.GetValue() == "Earth" :
			self.colorList = [ wx.Colour(112, 128, 144), wx.Colour(85, 107, 47), \
			wx.Colour(0, 255, 255), wx.Colour(150, 150, 150), wx.Colour(135, 206, 235), \
			wx.Colour(238, 130, 238), wx.Colour(165, 42, 42), wx.Colour(255, 0, 0), \
			wx.Colour(0, 255, 0), wx.Colour(0, 0, 255), wx.Colour(0, 255, 127), \
			wx.Colour(255, 255, 255), wx.Colour(255, 105, 180), wx.Colour(165, 42, 42), wx.Colour(255, 222, 173), wx.Colour(165, 42, 42), wx.Colour(30, 144, 255), wx.Colour(224, 255, 255)] 
		elif self.colorSet.GetValue() == "Santa Fe" :
			self.colorList = [ wx.Colour(0, 100, 0), wx.Colour(99, 184, 255), \
			wx.Colour(0, 255, 255), wx.Colour(255, 228, 225), wx.Colour(255, 105, 180), \
			wx.Colour(160, 32, 240), wx.Colour(255, 192, 203), wx.Colour(255, 0, 0), \
			wx.Colour(0, 255, 0), wx.Colour(255, 0, 0), wx.Colour(255, 255, 255), \
			wx.Colour(155, 205, 155), wx.Colour(255, 20, 147), wx.Colour(100, 149, 237), wx.Colour(205, 85, 85), wx.Colour(255, 231, 186), wx.Colour(30, 144, 255), wx.Colour(224, 255, 255)] 
		elif self.colorSet.GetValue() == "Custom" :
			for key in self.parent.Window.colorDictKeys :
				self.colorList.append(self.parent.Window.colorDict[key])

		# 9/12/2012 brgtodo: list of colorPickers?
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
		idx = event.GetId() - 101 # see 9/17/2012 brg
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
		i = 0
		for key in self.parent.Window.colorDictKeys :
			self.parent.Window.colorDict[key] = self.colorList[i]
			i = i + 1

		self.parent.Window.overlapcolorList = []
		for i in range(9) :
			self.parent.Window.overlapcolorList.insert(i, self.overlapcolorList[i])
		self.parent.Window.UpdateDrawing()


# adjust a core's MCD based on previous cores' growth rate
class ProjectDialog(wx.Dialog):
	def __init__(self, parent):
		self.parent = parent
		self.coreData = {}
		self.lastHole = -1
		self.HoleData = self.parent.Window.HoleData

		# vars for output
		self.outHole = ""
		self.outCore = ""
		self.outType = None
		self.outOffset = 0

		wx.Dialog.__init__(self, parent, -1, "Project", size=(300,200), style=wx.DEFAULT_DIALOG_STYLE |
						   wx.NO_FULL_REPAINT_ON_RESIZE |wx.STAY_ON_TOP)
		dlgSizer = wx.BoxSizer(wx.VERTICAL)
		
		corePanel = wx.Panel(self, -1)
		coreSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.holeChoice = wx.Choice(corePanel, -1, size=(70,-1))
		self.coreChoice = wx.Choice(corePanel, -1, size=(70,-1))
		coreSizer.Add(wx.StaticText(corePanel, -1, "Hole:"), 0, wx.TOP | wx.BOTTOM, 5)
		coreSizer.Add(self.holeChoice, 0, wx.ALL, 5)
		coreSizer.Add(wx.StaticText(corePanel, -1, "Core:"), 0, wx.TOP | wx.BOTTOM, 5)
		coreSizer.Add(self.coreChoice, 0, wx.ALL, 5)
		corePanel.SetSizer(coreSizer)

		self.growthRateText = wx.StaticText(self, -1, "Growth Rate at [previous core] = [GR])")
		self.mbsfText = wx.StaticText(self, -1, "MBSF/CSF-A of [current core name] = [mbsf]")

		shiftPanel = wx.Panel(self, -1)
		shiftSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.shiftLabel = wx.StaticText(shiftPanel, -1, "Suggested shift: ")
		self.shiftField = wx.TextCtrl(shiftPanel, -1, "1.000")
		shiftSizer.Add(self.shiftLabel, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)
		shiftSizer.Add(self.shiftField, 0)
		shiftPanel.SetSizer(shiftSizer)

		buttonPanel = wx.Panel(self, -1)
		buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.cancelButton = wx.Button(buttonPanel, wx.ID_CANCEL, "Cancel")
		self.applyButton = wx.Button(buttonPanel, wx.ID_OK, "Apply")
		buttonSizer.Add(self.cancelButton, 0, wx.ALL, 5)
		buttonSizer.Add(self.applyButton, 0, wx.ALL, 5)
		buttonPanel.SetSizer(buttonSizer)

		dlgSizer.Add(corePanel, 0, wx.ALL | wx.EXPAND, 10)
		dlgSizer.Add(self.mbsfText, 0, wx.LEFT, 10)
		dlgSizer.AddStretchSpacer()
		dlgSizer.Add(self.growthRateText, 0, wx.LEFT, 10)
		dlgSizer.AddStretchSpacer()
		dlgSizer.Add(shiftPanel, 0, wx.LEFT, 10)
		dlgSizer.AddStretchSpacer()
		dlgSizer.Add(buttonPanel, 0, wx.ALIGN_RIGHT | wx.ALL, border=5)
	
		self.SetSizer(dlgSizer)

		self.InitChoices()

		self.Bind(wx.EVT_CHOICE, self.UpdateCoreChoice, self.holeChoice)
		self.Bind(wx.EVT_CHOICE, self.UpdateText, self.coreChoice)
		self.Bind(wx.EVT_BUTTON, self.OnApply, self.applyButton)

	def OnApply(self, evt):
		print "OnApply called"
		self.outHole = self.holeChoice.GetStringSelection()
		self.outCore = self.coreChoice.GetStringSelection()
		self.outOffset = float(self.shiftField.GetValue())
		# self.outType already set
		self.EndModal(wx.ID_OK)


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
					growthRate = numpy.polyfit(mbsfVals, mcdVals, 1)
					#print "msbf = {}, mcd = {}, gr = {}".format(mbsfVals, mcdVals, growthRate)
					coreDict[holeName][coreName] = (coreName, mbsf, mcd, round(growthRate[0], 3))

		# update self.coreData
		for hole in coreDict:
			self.coreData[hole] = []
			s = sorted(coreDict[hole], key=int)
			for key in s:
				self.coreData[hole].append(coreDict[hole][key])
			
		if self.holeChoice.GetCount() > 0:
			self.holeChoice.Select(0)
			self.UpdateCoreChoice()

	def UpdateCoreChoice(self, evt=None):
		curHoleIndex = self.holeChoice.GetSelection()
		if self.lastHole == curHoleIndex:
			return
		self.lastHole = curHoleIndex
		self.coreChoice.Clear()
		curHoleStr = self.holeChoice.GetStringSelection()
		for coreTuple in self.coreData[curHoleStr]:
			self.coreChoice.Append(coreTuple[0])
		if self.coreChoice.GetCount() > 0:
			self.coreChoice.Select(0)
			self.UpdateText()

	def UpdateText(self, evt=None):
		coreIndex = self.coreChoice.GetSelection()
		curHole = self.holeChoice.GetStringSelection()
		self.UpdateGrowthRateText(coreIndex, curHole)
		self.UpdateMbsfText(coreIndex, curHole)

	def UpdateGrowthRateText(self, coreIndex, curHole):
		if coreIndex > 0:
			coreTuple = self.coreData[curHole][coreIndex - 1]
			belowMbsf = self.coreData[curHole][coreIndex][1]
			coreName = curHole + str(coreTuple[0])
			if coreIndex == 1:
				gr = coreTuple[2] # use mcd depth (assuming 0.0 mbsf)
			else:
				gr = coreTuple[3]
			self.growthRateText.SetLabel("Growth Rate at core " + coreName + " = " + str(round(gr, 3)))
			suggShift = belowMbsf * gr - belowMbsf
			self.shiftField.SetValue(str(suggShift))
		else:
			self.growthRateText.SetLabel("Growth Rate undefined at topmost core")
			self.shiftField.SetValue("")

	def UpdateMbsfText(self, coreIndex, curHole):
		coreTuple = self.coreData[curHole][coreIndex]
		coreName = curHole + str(coreTuple[0])
		self.mbsfText.SetLabel("MBSF/CSF-A of core " + coreName + " = " + str(coreTuple[1]))



class AboutDialog(wx.Dialog):
	def __init__(self, parent, version) :
		wx.Dialog.__init__(self, parent, -1, "About Correlator " + version, size=(500, 300), style= wx.DEFAULT_DIALOG_STYLE |wx.NO_FULL_REPAINT_ON_RESIZE |wx.STAY_ON_TOP)

		desctext = "Correlator facilitates the adjustment of core depth data drilled in a multi-hole scenario by usually correlating measured whole-core (GRA, MSLP, PWC, #NGR) or half-core (RSC) sensor data across holes using an optimized cross-correlation approach."

		desc = wx.StaticText(self, -1, desctext, (10,10))
		desc.Wrap(480)

		wx.HyperlinkCtrl(self, -1, 'For more detailed information, please visit the Correlator Website', 'http://www.corewall.org', (15,95))

		wx.StaticText(self, -1, 'Developer:  Sean Higgins(shiggins@oceanleadership.org)', (20, 130))
		wx.StaticText(self, -1, 'Hyejung Hur(hhur2@uic.edu)', (95, 150))

		wx.StaticText(self, -1, 'Organization: ', (20, 180))
		wx.HyperlinkCtrl(self, -1, 'EVL', 'http://www.evl.uic.edu', (25, 200))
		wx.HyperlinkCtrl(self, -1, 'NSF', 'http://www.nsf.gov/', (25, 220))
		wx.HyperlinkCtrl(self, -1, 'LacCore', 'http://lrc.geo.umn.edu/LacCore/laccore.html', (120, 200))
		wx.HyperlinkCtrl(self, -1, 'Lamont Doherty', 'http://www.ldeo.columbia.edu/', (120, 220))

		okBtn = wx.Button(self, wx.ID_OK, "Close", ((230, 240)))
		wx.EVT_KEY_UP(self, self.OnCharUp)

	def OnCharUp(self,event):
		keyid = event.GetKeyCode() 
		if keyid == wx.WXK_ESCAPE :
			self.EndModal(wx.ID_CANCEL) 


class BackgroundPanel(wx.Panel):
        def __init__(self, parent, background, panel_size):
                wx.Panel.__init__(self, parent, -1, size=panel_size, style=wx.WANTS_CHARS)
        
                img = wx.Image(background, wx.BITMAP_TYPE_ANY)
                self.buffer = wx.BitmapFromImage(img)
                dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
            
                self.Bind(wx.EVT_PAINT, self.OnPaint)

        def OnPaint(self, evt):
                dc = wx.BufferedPaintDC(self, self.buffer)
        
# 9/17/2013 brg: rename to splash?
class OpenFrame(wx.Dialog):
	def __init__(self, parent, id, user, version):
                panel_size=(800, 370)
		wx.Dialog.__init__(self, parent, id, "Correlator " + version, size=panel_size,style= wx.DEFAULT_DIALOG_STYLE |wx.NO_FULL_REPAINT_ON_RESIZE | wx.STAY_ON_TOP)

		panel = BackgroundPanel(self, 'images/corewall_suite.jpg', panel_size)
 
		self.version = version
		wx.StaticText(self, -1, 'COMPOSITE, SPLICE, CORE-LOG INTEGRATION, AGE MODEL', (60, 30))

		wx.StaticText(self, -1, 'User Name : ', (250, 220))
		self.name = wx.TextCtrl(self, -1, user, (340, 220), size=(150, 25))
		     
		okBtn = wx.Button(panel, -1, "Start", (500, 213), size=(80, 30))
		self.Bind(wx.EVT_BUTTON, self.OnSTART, okBtn)

		self.user = user
		if platform_name[0] == "Windows" :
			cancelBtn = wx.Button(panel, wx.ID_CANCEL, "Cancel", (580, 220), size=(80, 30))

		wx.HyperlinkCtrl(self, -1, 'Go to Correlator Web', 'http://www.corewall.org', (60, 300))

		aboutBtn = wx.Button(panel, -1, "About", (200, 290), size=(80, 30))
		self.Bind(wx.EVT_BUTTON, self.OnABOUT, aboutBtn)

		wx.EVT_KEY_DOWN(self.name, self.OnPanelChar)
		panel.Bind(wx.EVT_CHAR, self.OnPanelChar)

	def OnABOUT(self, event) :
		dlg = AboutDialog(self, self.version)
		dlg.Centre()
		dlg.ShowModal()
		dlg.Destroy()

	def OnOK(self):
		self.user = self.name.GetValue()
		self.EndModal(wx.ID_OK)

	def OnSTART(self, event) :
		self.OnOK()

	# Close on Escape, continue on Enter
	def OnPanelChar(self, event):
		keyid = event.GetKeyCode()
		if keyid == 13 : # ENTER
			self.OnOK()
		elif keyid == 27 : # ESC 
			self.EndModal(wx.ID_CANCEL)
		else:
			event.Skip() # allow unhandled key events to propagate up the chain


class ImportDialog(wx.Dialog):
	def __init__(self, parent, id, paths, header, siteDict):
		wx.Dialog.__init__(self, parent, id, "Import", size=(1000, 700), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

		self.paths = paths
		self.header = header
		self.siteDict = siteDict # dictionary of sites keyed on site name

		self.selectedCol = -1
		self.colLabels = ["Data", "Depth", "?", "Leg", "Site", "Hole", "Core", "CoreType",
						  "Section", "TopOffset", "BottomOffset", "RunNo", "Unselect", "Depth"]
		self.typeLabels = ["NaturalGamma", "Susceptibility", "Reflectance", "Bulk Density(GRA)",
						   "Pwave", "Other", "Add type..."]

		# layout
		sz = wx.BoxSizer(wx.VERTICAL)
		self.SetSizer(sz)
		self.sheet = CoreSheet(self, 120, 100)
		sz.Add(self.sheet, 1, wx.EXPAND)

		buttonPanel = wx.Panel(self, -1)
		buttonPanel.SetSizer(wx.BoxSizer(wx.HORIZONTAL))
		self.importButton = wx.Button(buttonPanel, wx.ID_OK, "Import")
		self.cancelButton = wx.Button(buttonPanel, wx.ID_CANCEL, "Cancel")
		buttonPanel.GetSizer().Add(self.importButton)
		buttonPanel.GetSizer().Add(self.cancelButton)
		sz.Add(buttonPanel, 0, wx.RIGHT | wx.ALIGN_RIGHT, 10)

		# events
		self.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.ColHeaderSelected, self.sheet)
		self.Bind(wx.EVT_BUTTON, self.OnOK, self.importButton)

		# spreadsheet setup + init
		self.sheet.SetColLabelValue(0, "Data Type")
		for i in range(1, 39):
			self.sheet.SetColLabelValue(i, "?")
		self.UpdateColHeaders(header)
		self.PopulateCells(paths)

	def PopulateCells(self, paths):
		expectedTokenCount = -1
		addedRows = 0
		for path in paths:
			if path.find(".xml", 0) >= 0:
				path = xml.ConvertFromXML(path, glb.LastDir)

			# convert to standard Correlator format
			py_correlator.formatChange(path, glb.DBPath + "tmp/")

			curLine = 1
			f = open(glb.DBPath + "tmp/tmp.core", "r+")
			for line in f:
				tokens = line.split()
				tokenCount = len(tokens)
				if expectedTokenCount == -1:
					expectedTokenCount = tokenCount
				elif tokenCount != expectedTokenCount:
					glb.OnShowMessage("Error", "Found {} columns on line {}, expected {}".format(tokenCount, curLine, expectedTokenCount))
					return False

				if tokens[0] == "-" or tokens[0] == "null":
					continue

				for index in range(tokenCount):
					if len(tokens[index]) > 0:
						if tokens[index] != "null":
							self.sheet.SetCellValue(addedRows, index + 1, tokens[index])

				curLine += 1
				addedRows += 1
				if addedRows % 30 == 0:
					break
			f.close()

		return True

	def AddUserTypeMenuItems(self, popupMenu):
		menuId = 8
		for type in glb.GetUserTypes():
			popupMenu.Append(menuId, "&" + type)
			wx.EVT_MENU(popupMenu, menuId, self.OnTypeChanged)
			menuId += 1

	def ColHeaderSelected(self, event):
		self.selectedCol = event.GetCol()
		pos = event.GetPosition()

		# brgtodo
# 		if self.importType == "LOG" :
# 			popupMenu = wx.Menu()
# 			for i in [13, 0, 12]:
# 				popupMenu.Append(i + 1, self.colLabels[i])
# 			self.PopupMenu(popupMenu, pos)
# 			return

		if self.selectedCol == 0: # Data Type
			popupMenu = wx.Menu()
			for i in range(5):
				popupMenu.Append(i + 1, "&" + self.typeLabels[i])
				wx.EVT_MENU(popupMenu, i + 1, self.OnTypeChanged)
			self.AddUserTypeMenuItems(popupMenu)
			popupMenu.Append(7, "&Add type...")
			wx.EVT_MENU(popupMenu, 7, self.OnTypeChanged)
			self.PopupMenu(popupMenu, pos)
		elif self.selectedCol == 1: # Leg/Expedition
			popupMenu = wx.Menu()
			popupMenu.Append(1, "&Edit Leg No")
			wx.EVT_MENU(popupMenu, 1, self.OnEditLeg)
			self.PopupMenu(popupMenu, pos)
		elif self.selectedCol == 2: # Site
			popupMenu = wx.Menu()
			popupMenu.Append(2, "&Edit Site No")
			wx.EVT_MENU(popupMenu, 2, self.OnEditSite)
			self.PopupMenu(popupMenu, pos)
		elif self.selectedCol >= 3: # Non-special column
			popupMenu = wx.Menu()
			for i in range(len(self.colLabels)):
				popupMenu.Append(i + 1, "&" + self.colLabels[i])
				wx.EVT_MENU(popupMenu, i + 1, self.OnLabelChanged)
			self.PopupMenu(popupMenu, pos)

	def OnEditSite(self, event):
		editDlg = dialog.EditBoxDialog(self, "Enter New Site")
		if editDlg.ShowModal() == wx.ID_OK:
			# brgtodo for now, assume Site column index is 2
			for ridx in range(self.sheet.GetNumberRows()):
				self.sheet.SetCellValue(ridx, 2, editDlg.txt.GetValue())
	
	def OnEditLeg(self, event):
		editDlg = dialog.EditBoxDialog(self, "Enter New Leg")
		if editDlg.ShowModal() == wx.ID_OK:
			# brgtodo for now, assume Leg column index is 1
			for ridx in range(self.sheet.GetNumberRows()):
				self.sheet.SetCellValue(ridx, 1, editDlg.txt.GetValue())

	def OnOK(self, event):
		# confirm a data type was selected
		if len(self.sheet.GetCellValue(3, 0)) == 0:
			glb.OnShowMessage("Error", "Select a Data Type by clicking the leftmost column header", 1)
			return
		elif not self.HasCol("Data"):
			glb.OnShowMessage("Error", "Specify a Data column", 1)
		elif self.DoImport():
			self.EndModal(wx.ID_OK)

	def OnAddType(self):
		typeDlg = dialog.AddTypeDialog(self)
		if typeDlg.ShowModal() == wx.ID_OK:
			return typeDlg.txt.GetValue()
		return None

	def OnTypeChanged(self, event):
		menuId = event.GetId()
		datatype = ""
		if menuId > 0 and menuId < 7:
			datatype = self.typeLabels[menuId - 1]
		elif menuId == 7: # create datatype
			datatype = self.OnAddType()
			if datatype is None: # user canceled
				return
		else:
			userType = event.GetEventObject().GetLabel(menuId)
			datatype = userType[1:] # strip leading '&'
		
		# brgtodo? if in Edit mode, prevent change to an existing datatype
		# see dbmanager.py line 7708 ("Change")

		for ridx in range(self.sheet.GetNumberRows()):
			self.sheet.SetCellValue(ridx, 0, datatype)

	def OnLabelChanged(self, event):
		# Unselect - a log editing thing? Resetting label to original val?
		opId = event.GetId()
		if opId < 13 or opId == 14:
			self.sheet.SetColLabelValue(self.selectedCol, self.colLabels[opId - 1])
		elif opId == 13: # Unselect - a log editing thing? Resetting label to original val?
			origin_label = ""
			ith = 0 
			for label in self.importLabel:
				if ith == self.selectedCol:
					origin_label = label
					break
				ith = ith + 1
			self.sheet.SetColLabelValue(self.selectedCol, origin_label)

		self.selectedCol = -1

	def HasCol(self, colName):
		result = False
		for cidx in range(self.sheet.GetNumberCols()):
			if self.sheet.GetColLabelValue(cidx) == colName:
				result = True
				break
		return result

	def UpdateColHeaders(self, header):
		if header != "":
			# attempt to determine the file's delimiter
			delims = [' ', ',', '\t']
			counts = [len(header.split(d)) for d in delims]
			maxIndex = counts.index(max(counts))
			print "Guessing delimiter = {}".format(delims[maxIndex])

			tokens = header.split(delims[maxIndex])
			for i in range(len(tokens)):
				self.sheet.SetColLabelValue(i + 1, tokens[i].capitalize())
		else: # use default Correlator columns
			for cidx in range(3,11): # 'Leg' through 'BottomOffset'
				self.sheet.SetColLabelValue(cidx - 2, self.colLabels[cidx])
		
	# brgtodo
	def GetDatasort(self):
		datasort = [ -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1 ]
		cols = self.sheet.GetNumberCols()
		for i in range(cols):
			if self.sheet.GetColLabelValue(i) == "Leg":
				datasort[0] = i - 1 
			elif self.sheet.GetColLabelValue(i) == "Site":
				datasort[1] = i - 1
			elif self.sheet.GetColLabelValue(i) == "Hole":
				datasort[2] = i - 1
			elif self.sheet.GetColLabelValue(i) == "Core":
				datasort[3] = i - 1
			elif self.sheet.GetColLabelValue(i) == "CoreType":
				datasort[4] = i - 1
			elif self.sheet.GetColLabelValue(i) == "Section":
				datasort[5] = i - 1
			elif self.sheet.GetColLabelValue(i) == "TopOffset":
				datasort[6] = i - 1
				datasort[7] = i - 1
			elif self.sheet.GetColLabelValue(i) == "BottomOffset":
				datasort[7] = i - 1
			elif self.sheet.GetColLabelValue(i) == "Depth":
				datasort[8] = i - 1
			elif self.sheet.GetColLabelValue(i) == "Data":
				datasort[9] = i - 1
			elif self.sheet.GetColLabelValue(i) == "RunNo":
				datasort[10] = i - 1

		# CHECKING VALIDATION
		for ith in range(10) :
			if ith == 4: # okay for no CoreType col (4) to be defined
				continue
			if datasort[ith] == -1 :
				colName = self.colLabels[ith + 3]
				glb.OnShowMessage("Error", "Please select a {} column".format(colName), 1)
				return []

		# use Depth if TopOffset or BottomOffset are absent
		if datasort[6] == -1:
			datasort[6] = datasort[8]
		if datasort[7] == -1:
			datasort[7] = datasort[8]

		return datasort

	""" return list of unique hole names in Hole column """
	def GetImportHoles(self, holeCol):
		holes = set()
		curRow = 3 
		while curRow < self.sheet.GetNumberRows():
			val = self.sheet.GetCellValue(curRow, holeCol)
			if val == "":
				break
			holes.add(val)
			curRow += 1
		return list(holes)
	
	def DoImport(self):
		# brgtodo - logs and datafile editing cases
		
		datasort = self.GetDatasort()
		if datasort == []:
			return False

		typeStr = self.sheet.GetCellValue(3, 0) # Data Type
		typeNum = glb.GetTypeNum(typeStr)
		typeAbbv = glb.GetTypeAbbv(typeStr)
		typeAnnot = ""
		if typeAbbv == typeStr:
			typeAnnot = typeStr

		leg = self.sheet.GetCellValue(3, datasort[0] + 1)
		site = self.sheet.GetCellValue(3, datasort[1] + 1)
		lsPair = leg + "-" + site

		# brgtodo: confirm hole/datatype pair doesn't already exist
		holesToImport = self.GetImportHoles(datasort[2] + 1)
		for h in holesToImport:
			if self.siteDict[lsPair].HasHole(typeStr, h):
				glb.OnShowMessage("Error", "Site {} already contains hole {} of type {}".format(lsPair, h, typeStr), 1)
				return False
		
		glb.MainFrame.OnNewData(None)
		
		# create site dir if needed # brgtodo dbutils?
		siteDirPath = glb.DBPath + "db/" + lsPair	
		if os.access(siteDirPath, os.F_OK) == False:
			os.mkdir(siteDirPath)
			siteDb = open(glb.DBPath + "db/datalist.db", "a+")
			siteDb.write("\n" + lsPair)
			siteDb.close()
		
		# write datasort to file for unknown reasons (C++ side?)
		colSortFile = siteDirPath + "/." + typeAbbv
		fout = open(colSortFile, 'w+')
		for r in datasort:
			s = str(r) + "\n"
			fout.write(s)
		fout.close()

		pathCount = 0
		dataFilePrefix = siteDirPath + "/" + lsPair # [root]/[siteDir]/[leg]-[site]
		for path in self.paths:
			idx = datasort[2] + 1
			hole = holesToImport[pathCount]
			if hole[0] == '\t': # brgtodo necessary? wouldn't tabs be stripped from tsv data at this point?
				hole = hole[1:]
			dataFileName = lsPair + "-" + hole + "." + typeAbbv + ".dat" # filename
			dataFilePath = dataFilePrefix + dataFileName
			fout = open(dataFilePath, 'w+')
			dbu.WriteDataHeader(fout, typeStr)

			if path.find(".xml", 0) >= 0:
				path = xml.ConvertFromXML(path, glb.LastDir)
			tmpPath = glb.DBPath + "tmp/"
			py_correlator.formatChange(path, tmpPath)

			# "MAX COLUMN TESTING"
			# finds the first line with >= 10 columns and sets MAX_COLUMN to
			# that number - 1, making it zero-based for array indexing.
			MAX_COLUMN = 9 
			f = open(tmpPath + "tmp.core", 'r+')
			for line in f :
				modifiedLine = line[0:-1].split()
				if modifiedLine[0] == 'null' :
					continue
				MAX_COLUMN = len(modifiedLine) - 1
				if MAX_COLUMN < 9 : 
					continue
				break
			f.close()

			# write source file contents to internal datafile
			f = open(tmpPath + "tmp.core", 'r+')
			for line in f :
				modifiedLine = line[0:-1].split()
				if modifiedLine[0] == 'null' :
					continue
				max = len(modifiedLine)
				s = ""
				if max <= MAX_COLUMN :
					continue;
				if modifiedLine[MAX_COLUMN].find("null", 0) >= 0 :
					continue
				else :
					for j in range(11) :
						idx = datasort[j]
						if idx > MAX_COLUMN :
							continue
						if idx >= 0 :
							s = s + modifiedLine[idx] + " "
						else :
							s = s + "-" + " "
					s = s + "\n"
					fout.write(s)
			f.close()
			fout.close()

			# load file into C++ side to retrieve range
			glb.MainFrame.LOCK = 0
			py_correlator.openHoleFile(dataFilePath, -1, typeNum, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, typeAnnot)
			glb.MainFrame.OnInitDataUpdate()
			glb.MainFrame.LOCK = 1

			s = "Import Core Data: " + dataFilePath + "\n"
			glb.MainFrame.logFileptr.write(s)

			# brgtodo model-level method to add a hole (creating new site if needed)
			if lsPair in self.siteDict:
				destSite = self.siteDict[lsPair]
			else:
				destSite = self.siteDict[lsPair] = model.SiteData(lsPair)
			
			holeData = model.HoleData(hole)
			holeData.file = dataFileName
			holeData.origSource = path
			dataRange = py_correlator.getRange(typeStr)
			holeData.min = str(int(float(dataRange[0]) * 100.0) / 100.0) # "round" to two digits
			holeData.max = str(int(float(dataRange[1]) * 100.0) / 100.0)
			destSite.AddHole(typeStr, holeData)
			dbu.SaveSite(destSite)
			
			pathCount += 1

			glb.MainFrame.OnNewData(None)			

		glb.MainFrame.logFileptr.write("\n")

		# 8/15/2014 brgtodo: update DB file, then reload into model+view!
		
		return True
