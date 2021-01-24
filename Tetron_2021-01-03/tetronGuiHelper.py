# -*- coding: latin-1 -*-


import shutil
import threading

import numpy
from PIL import Image
import PyQt4
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt


# Qt style sheets references:
# Reference: https://doc.qt.io/archives/qt-4.8/stylesheet-reference.html
# Syntax: https://doc.qt.io/qt-5/stylesheet-syntax.html


# Create global variables that define the sizes of GUI elements.
# This function is called by theaterGui, which passes to this function an instance of QDesktopWidget, which contains the size of the screen, in pixels. The values of some global variables created here are calculated as fractions of the screen size, which results in consistent sizes of GUI elements across devices with different screen resolutions.
def get_screen_geometry(widget_desktop):
	# Get an instance of QRect.
	screen_geometry = widget_desktop.screenGeometry()
	# Get the height of the screen, in pixels.
	global height_screen
	height_screen = screen_geometry.height()
	
	# The border widths of some elements.
	global width_border
	width_border = '3px'
	# The size of space between adjacent elements (e.g. buttons, boxes).
	global spacing
	spacing = round(height_screen*(16.0/1600.0))
	# The size of space between border and content in some elements (e.g. buttons).
	global padding
	padding = str(spacing/4.0) + 'px'
	# The radius of some elements (e.g. boxes).
	global radius
	radius = str(spacing) + 'px'
	# The radius of some smaller elements (e.g. buttons).
	global radius_small
	radius_small = str(spacing/2.0) + 'px'
	# The height and width of (square) icons.
	global size_icon
	size_icon = round(height_screen*(40.0/1600.0))
	global size_icon_small
	size_icon_small = round(height_screen*(25.0/1600.0))


# Return a string with RGB values used for setting colors in GUI elements.
# The string is formatted as 'rgba(R,G,B,A%)', where R, G, B can be numbers between 0 and 255 or percentages between 0 and 100. For input parameter 'color', input a number (int or float) between 0 and 100 for a grayscale color (100 is white, 0 is black), or input a string with the name of a color ('blue', 'green', 'yellow', 'red'). For optional input parameter 'opacity', input a number (int or float) between 0 and 100 to set the opacity of the color (100 is fully opaque, 0 is fully transparent).
def rgb(color, opacity=100):
	# Select the default blank color if 'color' is None.
	if color is None:
		color = 25

	# Create a grayscale color if 'color' is a number.
	if isinstance(color, int) or isinstance(color, float):
		color = str(color)
		color = '{}%,{}%,{}%'.format(color, color, color)
	# Create a non-grayscale color if 'color' is a string.
	elif isinstance(color, str):
		if color == 'I':
			color = '0,175,191'
		elif color == 'J':
			color = '0,149,255'
		elif color == 'L':
			color = '255,128,0'
		elif color == 'O':
			color = '255,191,0'
		elif color == 'S':
			color = '0,191,96'
		elif color == 'T':
			color = '140,102,255'
		elif color == 'Z':
			color = '255,64,64'
	return 'rgba({},{}%)'.format(color, str(opacity))


# A block in the form of a button.
class Block(QtGui.QPushButton):
	def __init__(self, color_code=0):
		super(Block, self).__init__()

		# Disable button.
		self.setEnabled(False)

		# Set color of button.
		if color_code > 0:
			opacity_background = 75
			opacity_border = 100
		else:
			opacity_background = 10
			opacity_border = 50
		if color_code == 0:
			color = None
		elif color_code == 1:
			color = 'I'
		elif color_code == 2:
			color = 'J'
		elif color_code == 3:
			color = 'L'
		elif color_code == 4:
			color = 'O'
		elif color_code == 5:
			color = 'S'
		elif color_code == 6:
			color = 'T'
		elif color_code == 7:
			color = 'Z'
		style = """
		QPushButton:disabled {
			background-color: %s;
			border-color: %s;
			border-style: solid;
			border-width: %s;
			}
		""" % (rgb(color, opacity_background), rgb(color, opacity_border), 5)
		self.setStyleSheet(style)

		# Set size.
		self.setFixedHeight(50)
		self.setFixedWidth(50)
		# Set size policy.
		# self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Maximum))

	# # Set the color.
	# def set_color(self, data=None):
	# 	if data < 0:
	# 		opacity_background = 10
	# 		opacity_border = 50
	# 	else:
	# 		opacity_background = 50
	# 		opacity_border = 100
	# 	if data == 0 or data is None:
	# 		color = None
	# 	elif data == 1:
	# 		color = 'I'
	# 	elif data == 2:
	# 		color = 'J'
	# 	elif data == 3:
	# 		color = 'L'
	# 	elif data == 4:
	# 		color = 'O'
	# 	elif data == 5:
	# 		color = 'S'
	# 	elif data == 6:
	# 		color = 'T'
	# 	elif data == 7:
	# 		color = 'Z'
	# 	# style = """
	# 	# QPushButton:disabled {
	# 	# 	background-color: %s;
	# 	# 	border-color: %s;
	# 	# 	border-style: solid;
	# 	# 	border-width: %s;
	# 	# 	}
	# 	# """ % (
	# 	# 	rgb(color, opacity_background), rgb(color, opacity_border), 5
	# 	# 	)
	# 	# if isinstance(color, str):
	# 	# 	print(color)
	# 	style = """
	# 	QPushButton:disabled {
	# 		background-color: %s;
	# 		border-color: %s;
	# 		border-style: solid;
	# 		border-width: %s;
	# 		}
	# 	""" % (rgb(color, opacity_background), rgb(color, opacity_border), 5)
	# 	self.setStyleSheet(style)
	# 	self.update()


# A text box with a text label used for modifying a setting. Changing the value in the text box changes the setting. If a model collection object is passed, the text box updates its value when the current model changes. Pass a function or a list of functions to be run after the setting is changed.
class Entry(QtGui.QWidget):
	def __init__(self, setting_name, program_settings=None, model_collection=None, callbacks=None):
		QtGui.QWidget.__init__(self)
		self.setting_name = setting_name
		self.model_collection = model_collection
		self.callbacks = callbacks

		# Set layout.
		layout = QtGui.QHBoxLayout()
		layout.setContentsMargins(0,0,0,0)
		layout.setSpacing(0)
		self.setLayout(layout)
		
		# Get setting object from model collection or program settings.
		if model_collection != None:
			self.setting = model_collection.get_current_model().model_settings[self.setting_name]
		elif program_settings != None:
			self.setting = program_settings[self.setting_name]

		# Create label.
		label_text = str(self.setting.name)
		if self.setting.unit:
			label_text = label_text + ' (' + self.setting.unit + ')'
		self.label = QtGui.QLabel(label_text)
		# Create text box.
		self.text_box = QtGui.QLineEdit()
		self.text_box.setText(str(self.setting.get_value()))
		self.text_box.setAlignment(QtCore.Qt.AlignRight)
		
		# Add items to layout.
		layout.addWidget(self.label)
		layout.addWidget(self.text_box)
		# Set relative widths of items.
		layout.setStretch(0, 5)
		layout.setStretch(1, 3)

		# Set callback function to run when Enter key is pressed or when text box loses focus.
		self.text_box.editingFinished.connect(self.callback_update_setting)

	# Update the setting when the text box is edited, or empty the text box if no models are loaded.
	def callback_update_setting(self):
		# Get the text in the text box and update the setting object.
		text = self.text_box.text()
		self.switch_model()

		# Update the setting value.
		if self.setting:
			# Adjust the value if it is out of bounds (int, float only).
			try:
				value = self.setting.data_type(text)
				if self.setting.lower:
					if value < self.setting.lower:
						value = self.setting.data_type(self.setting.lower)
				if self.setting.upper:
					if value > self.setting.upper:
						value = self.setting.data_type(self.setting.upper)
			# Revert to the existing setting value if an invalid value was entered.
			except ValueError:
				value = self.setting.value
			
			# Update the value of the setting and the text shown in the text box.
			self.setting.set_value(value)
			self.text_box.setText(str(value))
		else:
			self.text_box.clear()

		# Run the callback functions.
		if self.callbacks is not None:
			if type(self.callbacks) is list:
				for function in self.callbacks:
					function()
			else:
				self.callbacks()

	# Update the value in the text box with the current model, or empty the text box if no models are loaded.
	def update(self):
		self.switch_model()
		if self.setting:
			self.text_box.setText(str(self.setting.get_value()))
		else:
			self.text_box.clear()

	# Return the setting object of the current model, or return None if no models are loaded.
	def switch_model(self):
		if self.model_collection != None:
			model = self.model_collection.get_current_model()
			if model:
				self.setting = model.model_settings[self.setting_name]
			else:
				self.setting = None


# A spin box and a text label used for modifying a setting with a numerical value. Changing the value in the spin box changes the setting. If a model collection object is passed, the spin box updates its value when the current model changes. Pass a function or a list of functions to be run after the setting is changed.
class EntrySpinBox(QtGui.QWidget):
	def __init__(self, setting_name, program_settings=None, model_collection=None, callbacks=None):
		QtGui.QWidget.__init__(self)
		self.setting_name = setting_name
		self.model_collection = model_collection
		self.callbacks = callbacks

		# Set layout.
		layout = QtGui.QHBoxLayout()
		layout.setContentsMargins(0,0,0,0)
		layout.setSpacing(0)
		self.setLayout(layout)
		
		# Get setting object from model collection or program settings.
		if model_collection != None:
			self.setting = model_collection.get_current_model().model_settings[self.setting_name]
		elif program_settings != None:
			self.setting = program_settings[self.setting_name]

		# Create label.
		self.label = QtGui.QLabel(str(self.setting.name))
		# Create spin box.
		if self.setting.data_type is int:
			self.spin_box = QtGui.QSpinBox()
			self.spin_box.setSingleStep(int(self.setting.step))
		elif self.setting.data_type is float:
			self.spin_box = QtGui.QDoubleSpinBox()
			self.spin_box.setSingleStep(float(self.setting.step))
		self.spin_box.setRange(self.setting.lower, self.setting.upper)
		self.spin_box.setValue(self.setting.get_value())
		self.spin_box.setSuffix(' ' + self.setting.unit)
		self.spin_box.setAlignment(QtCore.Qt.AlignRight)
		self.spin_box.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred))
		
		# Add items to layout.
		layout.addWidget(self.label)
		layout.addWidget(self.spin_box)
		# Set relative widths of items.
		layout.setStretch(0, 5)
		layout.setStretch(1, 3)

		# Set callback function to run when the value in the spin box changes.
		self.spin_box.valueChanged.connect(self.callback_update_setting)

	# Update the setting when the spin box is edited.
	def callback_update_setting(self):
		# Get the value in the spin box and update the setting object.
		value = self.spin_box.value()
		self.switch_model()

		# Update the setting value.
		if self.setting:
			# Adjust the value if it is out of bounds (int, float only).
			try:
				value = self.setting.data_type(value)
				if value < self.setting.lower:
					value = self.setting.data_type(self.setting.lower)
				if value > self.setting.upper:
					value = self.setting.data_type(self.setting.upper)
			# Revert to the existing setting value if an invalid value was entered.
			except ValueError:
				value = self.setting.value
			
			# Update the value of the setting and the value shown in the spin box.
			self.setting.set_value(value)
			self.spin_box.setValue(value)
		else:
			self.spin_box.clear()

		# Run the callback functions.
		if self.callbacks is not None:
			if type(self.callbacks) is list:
				for function in self.callbacks:
					function()
			else:
				self.callbacks()

	# Update the value in the spin box with the current model, or empty the spin box if no models are loaded.
	def update(self):
		self.switch_model()
		if self.setting:
			self.spin_box.setValue(self.setting.get_value())
		else:
			self.spin_box.clear()

	# Update the setting attribute with the setting object of the current model, or return None if no models are loaded.
	def switch_model(self):
		if self.model_collection != None:
			model = self.model_collection.get_current_model()
			if model:
				self.setting = model.model_settings[self.setting_name]
			else:
				self.setting = None


# A popup list with a text label used for modifying a setting with a small number of possible values. Selecting an item in the popup list changes the setting. If a model collection object is passed, the popup updates its value when the current model changes. Pass a function or a list of functions to be run after the setting is changed.
class EntryPopup(QtGui.QWidget):
	def __init__(self, setting_name, program_settings, editable=True, callbacks=None):
		super(EntryPopup, self).__init__()
		self.callbacks = callbacks

		# Set layout.
		layout = QtGui.QHBoxLayout()
		layout.setContentsMargins(0,0,0,0)
		layout.setSpacing(0)
		# layout.setAlignment(QtCore.Qt.AlignLeft)
		self.setLayout(layout)

		# Get the setting object.
		self.setting = program_settings[setting_name]

		# Create label.
		label_text = str(self.setting.name)
		if self.setting.unit:
			label_text = label_text + ' (' + self.setting.unit + ')'
		self.label = QtGui.QLabel(label_text)
		# Create popup list and add to it the possible values of the setting.
		self.popup = QtGui.QComboBox()
		self.popup.setEditable(editable)
		if editable:
			self.popup.lineEdit().setAlignment(QtCore.Qt.AlignRight)
		for value in self.setting.value_list:
			self.popup.addItem(str(value).title())
		# Set the popup list to display the value contained in the setting.
		self.popup.setCurrentIndex(self.popup.findText(str(self.setting.value).title()))
		
		# Add items to layout.
		layout.addWidget(self.label)
		layout.addWidget(self.popup)
		# Set relative widths of items.
		layout.setStretch(0, 5)
		layout.setStretch(1, 3)

		# Set callback function to run when a new item in the popup list is selected and when the text in the line edit widget is changed.
		self.popup.currentIndexChanged[str].connect(self.update_setting)
		self.popup.editTextChanged.connect(self.update_setting)
	
	# Update the setting value when a new item in the popup list is selected.
	def update_setting(self, text):
		# Get the selected item in the popup list.
		text = str(text).lower()
		# Convert the selected item from str to the appropriate type.
		text = self.setting.data_type(text)
		# Set the value.
		self.setting.set_value(text)

		# Run the callback functions.
		if self.callbacks is not None:
			if type(self.callbacks) is list:
				for function in self.callbacks:
					function()
			else:
				self.callbacks()


# A label showing the value of a setting and a text label on the left. This widget cannot be modified and is used to display settings whose values are calculated using the values of other settings.
class SettingLabel(QtGui.QWidget):
	def __init__(self, setting_name, program_settings=None, model_collection=None):
		super(SettingLabel, self).__init__()
		self.setting_name = setting_name
		self.program_settings = program_settings
		self.model_collection = model_collection

		# Set layout.
		layout = QtGui.QHBoxLayout()
		layout.setContentsMargins(0,0,0,0)
		self.setLayout(layout)

		# Get setting object from program settings or model collection.
		if program_settings != None:
			self.setting = program_settings[setting_name]
		elif model_collection != None:
			self.setting = model_collection.get_current_model().model_settings[setting_name]

		# Create label for the setting name.
		self.label_name = QtGui.QLabel(str(self.setting.name))
		# Create label for the setting value.
		self.label_value = QtGui.QLabel()
		self.update()
		# Create label for the setting units.
		self.label_units = QtGui.QLabel(self.setting.unit)

		# Set appearance of labels.
		self.label_name.setAlignment(QtCore.Qt.AlignLeft)
		self.label_value.setAlignment(QtCore.Qt.AlignRight)
		self.label_units.setAlignment(QtCore.Qt.AlignLeft)
		self.label_name.setStyleSheet('color: %s' % rgb(0,50))
		self.label_value.setStyleSheet('color: %s' % rgb(0,50))
		self.label_units.setStyleSheet('color: %s' % rgb(0,50))
		
		# Add items to layout.
		layout.addWidget(self.label_name)
		layout.addWidget(self.label_value)
		if self.setting.unit != '':
			layout.addWidget(self.label_units)
		# Set relative widths of items.
		layout.setStretch(0, 5)
		layout.setStretch(1, 3)
	
	# Update the value shown, or remove the value if no models are loaded.
	def update(self):
		if self.model_collection != None:
			# Get the setting object of the current model.
			model = self.model_collection.get_current_model()
			if model:
				self.setting = model.model_settings[self.setting_name]
			else:
				self.setting = None
		if self.setting:
			value = self.setting.get_value()
			if type(value) is float:
				value = round(value,3)
			self.label_value.setText(str(value))
		else:
			self.label_value.clear()


# A checkbox with a text label used for modifying a boolean setting. Checking and unchecking the checkbox changes the setting. If a model collection object is passed, the checkbox updates its value when the current model changes. Pass a function or a list of functions to be run after the setting is changed.
class Checkbox(QtGui.QCheckBox):
	def __init__(self, setting_name, program_settings=None, model_collection=None, callbacks=None):
		super(Checkbox, self).__init__()
		self.setting_name = setting_name
		self.model_collection = model_collection
		self.callbacks = callbacks

		# Get settings object if model collection was supplied.
		if self.model_collection != None:
			self.setting = self.model_collection.get_current_model().model_settings[self.setting_name]
		elif program_settings != None:
			self.setting = program_settings[self.setting_name]

		# Add the text.
		text = str(self.setting.name)
		if self.setting.unit:
			text = text + ' (' + self.setting.unit + ')'
		self.setText(text)
		# Set initial state according to setting.
		self.setChecked(self.setting.get_value())
		
		# Set callback function to run when the checkbox is checked or unchecked.
		self.stateChanged.connect(self.update_setting)

	# Update the setting value when the checkbox is checked or unchecked.
	def update_setting(self, state=None):
		self.setting.set_value(self.isChecked())

		# Run the callback functions.
		if self.callbacks is not None:
			if type(self.callbacks) is list:
				for function in self.callbacks:
					function()
			else:
				self.callbacks()

	# Update the checkbox state if current model has changed.
	def update(self):
		# Get the settings object of the current model.
		if self.model_collection != None:
			self.setting = self.model_collection.get_current_model().model_settings[self.setting_name]
		self.setChecked(self.setting.get_value())


# A button that can have a label and an icon, with an optional callback function connected to it. Input a str to "text" and "icon_filename" (the name of the image file) and a function to "callback". For "color", refer to the comments for function "rgb".
class Button(QtGui.QPushButton):
	def __init__(self, text=None, icon_filename=None, callback=None, color='blue'):
		super(Button, self).__init__()

		# Set text.
		if text:
			self.setText(text)
		# Set icon and icon size.
		if icon_filename:
			self.setIcon(QtGui.QIcon('Images/' + icon_filename))
			self.setIconSize(QtCore.QSize(size_icon,size_icon))
		# Connect a callback function.
		if callback:
			self.clicked.connect(callback)
		
		# Set style sheet.
		style = """
		QPushButton {
			background-color: %s;
			border-color: %s;
			border-style: solid;
			border-width: %s;
			border-radius: %s;
			padding: %s;
			}
		QPushButton:hover {
			background-color: %s;
			border-color: %s;
			}
		QPushButton:pressed {
			background-color: %s;
			border-color: %s;
			}
		QPushButton:checked {
			background-color: %s;
			border-color: %s;
			}
		QPushButton:disabled {
			background-color: %s;
			border-color: %s;
			color: %s;
			}
			""" % (
				rgb(90), rgb(60), width_border, radius_small, padding,
				rgb(color,10), rgb(color),
				rgb(color,25), rgb(color),
				rgb(color,25), rgb(color),
				rgb(80), rgb(80), rgb(50),
				)
		self.setStyleSheet(style)


# NOTE: This class is nearly identical to class Button, so in future, may replace all usages of Button with this class, since QToolButton has all the capabilities of QPushButton and more (popup menus esp.).

# A button that can display a label and an icon, with a callback function connected to it. Input a str to "text" and "icon_filename" (the path to the image file) and a function to "callback". For "color", refer to the comments for function "rgb".
class ToolButton(QtGui.QToolButton):
	def __init__(self, text=None, icon_filename=None, callback=None, color='blue'):
		super(ToolButton, self).__init__()
		self.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)

		# Set text.
		if text:
			self.setText(text)
		# Set icon and icon size.
		if icon_filename:
			self.setIcon(QtGui.QIcon('Images/' + icon_filename))
			self.setIconSize(QtCore.QSize(size_icon,size_icon))
		# Connect a callback function.
		if callback:
			self.clicked.connect(callback)
		
		# Set style sheet.
		style = """
		QToolButton {
			background-color: %s;
			border-color: %s;
			border-style: solid;
			border-width: %s;
			border-radius: %s;
			padding: %s;
			}
		QToolButton:hover {
			background-color: %s;
			border-color: %s;
			}
		QToolButton:pressed {
			background-color: %s;
			border-color: %s;
			}
		QToolButton:checked {
			background-color: %s;
			border-color: %s;
			}
		QToolButton:disabled {
			background-color: %s;
			border-color: %s;
			color: %s;
			}
		QToolButton::menu-indicator {
			image: none;
			}
			""" % (
				rgb(90), rgb(60), width_border, radius_small, padding,
				rgb(color,10), rgb(color),
				rgb(color,25), rgb(color),
				rgb(color,25), rgb(color),
				rgb(80), rgb(80), rgb(50),
				)
		self.setStyleSheet(style)


# A tab widget.
class Tab(QtGui.QTabWidget):
	def __init__(self):
		super(Tab, self).__init__()
		self.setIconSize(QtCore.QSize(size_icon, size_icon))
		style = """
		QTabBar::tab {
			background-color: %s;
			border-style: solid;
			border-width: %s;
			border-color: %s;
			padding: %s;
		}
		QTabBar::tab:selected {
			background-color: %s;
			margin-top: 0px;
			border-bottom-color: %s;
		}
		QTabBar::tab:!selected {
			margin-top: 0px;
			background-color: %s;
			border-bottom-color: %s;
		}
		""" % (
			rgb(99), width_border, rgb(75), padding,
			rgb(100), rgb(100),
			rgb(90), rgb(75),
		)
		self.setStyleSheet(style)


# A group box in which other elements can be added.
class Frame(QtGui.QGroupBox):
	def __init__(self, text):
		super(Frame, self).__init__(text)
		# Set style sheet.
		style = """
		QGroupBox {
			background-color: %s;
			border-style: solid;
			border-width: %s;
			border-radius: %s;
			border-color: %s;
			padding-top: %s;
			}
		QGroupBox::title {
			subcontrol-origin: padding;
			subcontrol-position: top center;
			}
		""" % (
			rgb(99), width_border, radius, rgb(75), radius
		)
		self.setStyleSheet(style)

		# Create and set font style.
		font = QtGui.QFont('Inter', 10, 75)  # 10 pt size, bold weight
		self.setFont(font)


# A text label placed above GUI elements that are related.
class Header(QtGui.QLabel):
	def __init__(self, text):
		super(Header, self).__init__(text)
		# Set style sheet.
		self.setStyleSheet('font-weight: bold;')


# A text label.
class SmallLabel(QtGui.QLabel):
	def __init__(self, text=''):
		super(SmallLabel, self).__init__(text)
		self.setAlignment(QtCore.Qt.AlignHCenter)
		self.setStyleSheet('font-size: 8pt; color: %s' % rgb(0,50))


# A vertical or horizontal line used to separate GUI elements.
class Divider(QtGui.QFrame):
	def __init__(self, direction='horizontal'):
		super(Divider, self).__init__()
		# Set the direction of the line.
		if direction.lower() == 'horizontal':
			self.setFrameShape(QtGui.QFrame.HLine)
		elif direction.lower() == 'vertical':
			self.setFrameShape(QtGui.QFrame.VLine)
		# Set the style sheet.
		style = """
		color: %s;
		""" % (
			rgb(0, 25)
		)
		self.setStyleSheet(style)


# A progress bar displayed during long processes.
class ProgressBar(QtGui.QProgressBar):
	def __init__(self):
		super(ProgressBar, self).__init__()
		self.setMinimum(0)

		# Set the initial color.
		self.set_color('blue')
	
	# Set the color of the progress bar.
	def set_color(self, color, opacity=50):
		style = """
		QProgressBar {
			background-color: %s;
			font-size: 8pt;
			text-align: right;
			}
		QProgressBar::chunk {
			background-color: %s;
			}
		""" % (rgb(90),
			rgb(color, opacity),
		)
		self.setStyleSheet(style)


# A list that displays a single column of strings. One string can be selected at a time. Strings cannot be edited.
class ListView(QtGui.QListView):
	def __init__(self, callback):
		super(ListView, self).__init__()
		self.callback = callback

		# Create the model used to contain the items.
		self.list_model = QtGui.QStringListModel()
		self.setModel(self.list_model)
		# Set how the list view is resized in the GUI.
		self.setResizeMode(QtGui.QListView.Adjust)
		# Prevent items from being edited.
		self.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
	
	# Add a string to the list.
	def add(self, string):
		# Create a QModelIndex required to add items.
		index = self.list_model.createIndex(self.list_model.rowCount(), 0)
		# Create 1 new row.
		self.list_model.insertRows(self.list_model.rowCount(), 1)
		# Add the string to the list.
		self.list_model.setData(index, string)
		# Scroll to the new string.
		self.scrollTo(index)
		# Select the new string.
		self.setCurrentIndex(index)
	
	# Remove the currently selected string from the list.
	def remove(self):
		index = self.currentIndex()
		self.list_model.removeRows(index.row(), 1)

	# Remove all strings from the list.
	def remove_all(self):
		self.list_model.removeRows(0, self.list_model.rowCount())
	
	# Return the currently selected string.
	def get_selected_string(self):
		index = self.currentIndex()
		string = self.list_model.data(index, QtCore.Qt.DisplayRole)
		string = str(string.toString())
		return string

	# Override this inherited method, which is connected to a signal emitted when a new item becomes the current item.
	def currentChanged(self, current, previous):
		self.callback()


# String class that emits a signal on content changes.
class ConsoleText(QtCore.QObject):
	changed = QtCore.pyqtSignal()

	def __init__(self, line_count=100):
		QtCore.QObject.__init__(self)
		self.text = QtCore.QString()
		self.line_count = line_count
		self.lock = threading.Lock()

	# Add a string as a new line.
	def addLine(self, string):
		# Wait for other threads using this method to finish.
		self.lock.acquire()
		# Convert to str, QString strangely misbehaves.
		text = str(self.text)
		# Split into list of strings.
		lines = text.split('\n')
		# Remove lines at the beginning if the number of lines is reached.
		if len(lines) >= self.line_count:
			newText = ''
			for i in range(len(lines)-self.line_count, len(lines)):
				newText = newText + '\n' + lines[i]
			text = newText
		# Add new string as new line.
		text = text + '\n' + string
		# Convert back to QString.
		self.text = QtCore.QString(text)
		# Emit the signal that updates the text view.
		self.changed.emit()
		# Allow other threads to use this method.
		self.lock.release()

	# Add a string without line break.
	def addString(self, string):
		self.lock.acquire()
		self.text += string
		self.changed.emit()
		self.lock.release()


# A text brwoser that automatically updates if the referenced string is emitting a changed signal.
class ConsoleBrowser(QtGui.QTextBrowser):
	def __init__(self, text_buffer):
		QtGui.QTextBrowser.__init__(self)
		self.text_buffer = text_buffer

		# Connect to text buffers changed signal.
		# First, make a slot function.
		@QtCore.pyqtSlot()
		def textChanged():
			self.update()
		# Then, we connect the slot to the changed signal of the text buffer.
		self.text_buffer.changed.connect(textChanged)

		self.update()

	def update(self):
		self.clear()
		self.append(self.text_buffer.text)


# A layout containing slice images for each projector, a scroll bar, and a text box. The number of images shown and their arrangement relative to each other are updated when the projector settings are changed.
class ProjectorViewer(QtGui.QVBoxLayout):
	def __init__(self, program_settings, model_collection):
		super(ProjectorViewer, self).__init__()
		self.program_settings = program_settings
		self.model_collection = model_collection
		
		# Create a scroll bar.
		self.scroll_bar = QtGui.QScrollBar()
		self.scroll_bar.setOrientation(1)
		self.scroll_bar.setRange(1,1)
		self.scroll_bar.valueChanged.connect(self.callback_scroll)
		# Create an editable text box showing the current slice number.
		self.text_box = QtGui.QSpinBox()
		self.text_box.setRange(1,1)
		self.text_box.setAlignment(QtCore.Qt.AlignHCenter)
		self.text_box.valueChanged.connect(self.callback_text)
		# Create a label showing the number of slices.
		self.label_maximum = QtGui.QLabel()
		
		# Create a layout containing the projector images. This method creates an attribute containing the layout.
		self.update_layout()

		# Create a layout containing the text box and label.
		layout_slice_labels = QtGui.QHBoxLayout()
		layout_slice_labels.addStretch(5)
		layout_slice_labels.addWidget(self.text_box)
		layout_slice_labels.addWidget(self.label_maximum)
		layout_slice_labels.addStretch(5)

		# Add items to the main layout.
		self.addLayout(self.layout_images)
		self.addWidget(self.scroll_bar)
		self.addLayout(layout_slice_labels)
		# Add empty space at bottom.
		self.addStretch()
	
	# Change the images when the scroll bar moves.
	def callback_scroll(self, slice_number):
		image_list = self.model_collection.get_slice_images(slice_number-1)
		for projector_index in self.images:
			self.images[projector_index].setPixmap(image_list[projector_index])
		self.text_box.setValue(slice_number)
	
	# Change the images and update the scroll bar when the spin box is edited.
	def callback_text(self, slice_number):
		"""  DELETE, not needed for QSpinBox
		# Keep the text inside the acceptable range.
		try:
			slice_number = int(self.text_box.text())
			if slice_number < self.scroll_bar.minimum():
				slice_number = self.scroll_bar.minimum()
			elif slice_number > self.scroll_bar.maximum():
				slice_number = self.scroll_bar.maximum()
		except ValueError:
			slice_number = self.scroll_bar.value()
		self.text_box.setText(str(slice_number))
		"""
		image_list = self.model_collection.get_slice_images(slice_number-1)
		for projector_index in self.images:
			self.images[projector_index].setPixmap(image_list[projector_index])
		self.scroll_bar.setValue(slice_number)
	
	# Update the image, scroll bar, and text box when slicing is finished.
	def update_slices(self):
		slice_count = self.model_collection.get_slice_count()
		self.scroll_bar.setValue(self.scroll_bar.minimum())
		self.scroll_bar.setMaximum(slice_count)
		self.text_box.setRange(1, slice_count)
		self.text_box.setValue(self.text_box.minimum())
		for projector_index in self.images:
			self.images[projector_index].clear()
		if self.model_collection.has_models():
			for projector_index in self.images:
				self.images[projector_index].set_image(0)
		else:
			for projector_index in self.images:
				self.images[projector_index].setText('No models sliced.')
		self.label_maximum.setText('of %d' % slice_count)
	
	# Update the layout containing the images when projector settings are changed.
	def update_layout(self):
		# Create, for each projector, a layout containing an image and a label and store them in a dictionary.
		self.projector_layouts = {}
		self.images = {}
		for projector_index in range(self.program_settings['projector_count'].get_value()):
			self.images[projector_index] = ProjectorImage(self.program_settings, self.model_collection, projector_index)
			projector_label = Header('Projector %d' % (projector_index+1))
			projector_label.setAlignment(QtCore.Qt.AlignHCenter)
			layout = QtGui.QVBoxLayout()
			layout.setAlignment(QtCore.Qt.AlignHCenter)
			layout.addWidget(projector_label)
			layout.addWidget(self.images[projector_index])
			self.projector_layouts[projector_index] = layout
		
		# Create the layout containing all projector images.
		setting_arrangement = self.program_settings['projector_arrangement']
		if setting_arrangement.value.lower() == 'vertical':
			self.layout_images = QtGui.QVBoxLayout()
		elif setting_arrangement.value.lower() == 'horizontal':
			self.layout_images = QtGui.QHBoxLayout()
		for projector_index in range(self.program_settings['projector_count'].get_value()):
			self.layout_images.addLayout(self.projector_layouts[projector_index])


# # A label showing a slice image, shown in the projector window and the Projectors tab.
# class ProjectorImage(QtGui.QLabel):
# 	def __init__(self, program_settings, model_collection, projector_index=0):
# 		QtGui.QLabel.__init__(self)
# 		self.program_settings = program_settings
# 		self.model_collection = model_collection
# 		self.projector_index = projector_index

# 		# Define the height and width of the image.
# 		self.height = self.program_settings['projector_height'].get_value()
# 		self.width = self.program_settings['projector_width'].get_value()

# 		# Create black image.
# 		self.image_black = numpy.zeros((self.height,self.width,3), numpy.uint8)
# 		self.image_black = QtGui.QPixmap.fromImage(QtGui.QImage(self.image_black, self.width, self.height, QtGui.QImage.Format_RGB888))

# 		# Show the black image initially.
# 		self.setPixmap(self.image_black)

# 		# Set a style sheet.
# 		self.setStyleSheet('font-size: 8pt; color: %s' % rgb(0,50))

# 	# Change the slice image shown.
# 	def set_image(self, slice_index):
# 		# Get the slice image.
# 		if slice_index != -1:
# 			image = self.model_collection.get_slice_images(slice_index)[self.projector_index]
# 		else:
# 			image = self.image_black

# 		# Show the image.
# 		self.setPixmap(image)

# 	# Set a black image.
# 	def set_image_blank(self):
# 		self.setPixmap(self.image_black)

# 	# Set an image with a red, 1 pixel thick border along its perimeter. If projectors are being overlapped, add a border around the overlapping region.
# 	def set_image_border(self):
# 		# Create the three layers of the image.
# 		image_r = numpy.zeros((self.height,self.width), numpy.uint8)
# 		image_g = numpy.zeros((self.height,self.width), numpy.uint8)
# 		image_b = numpy.zeros((self.height,self.width), numpy.uint8)
# 		# Create a border in the red layer.
# 		print_height = min(self.program_settings['print_size_x_px'].get_value(), self.height)
# 		print_width = min(self.program_settings['print_size_y_px'].get_value(), self.width)
# 		index_top = int(round((self.height-print_height)/2.0))
# 		index_bottom = int(round((self.height-print_height)/2.0) + print_height - 1)
# 		index_left = int(round((self.width-print_width)/2.0))
# 		index_right = int(round((self.width-print_width)/2.0) + print_width - 1)
# 		image_r[[index_top,index_bottom], index_left:index_right+1] = 255
# 		image_r[index_top:index_bottom+1, [index_left,index_right]] = 255
# 		# Create a border around the overlapping region in the red layer.
# 		projector_count = self.program_settings['projector_count'].get_value()
# 		projector_arrangement = self.program_settings['projector_arrangement'].get_value()
# 		overlap_px = self.program_settings['projector_overlap_px'].get_value()
# 		if projector_count > 1 and overlap_px:
# 			if projector_arrangement == 'horizontal':
# 				if self.projector_index == 0:
# 					image_r[index_top:index_bottom+1,-overlap_px] = 255
# 				elif self.projector_index == 1:
# 					image_r[index_top:index_bottom+1,overlap_px-1] = 255
# 			elif projector_arrangement == 'vertical':
# 				if self.projector_index == 0:
# 					image_r[-overlap_px,index_left:index_right+1] = 255
# 				elif self.projector_index == 1:
# 					image_r[overlap_px-1,index_left:index_right+1] = 255
# 		# Display the image.
# 		image = numpy.dstack([image_r, image_g, image_b])
# 		image = QtGui.QPixmap.fromImage(QtGui.QImage(image, self.width, self.height, QtGui.QImage.Format_RGB888))
# 		self.setPixmap(image)

# 	# Set an image with a grid.
# 	def set_image_grid(self):
# 		# image = QtGui.QPixmap.fromImage(QtGui.QImage(image, self.width, self.height, QtGui.QImage.Format_RGB888))
# 		pass


# # A window displayed in the projector during printing.
# class ProjectorWindow(QtGui.QMainWindow):
# 	def __init__(self, program_settings, model_collection, projector_index=0):
# 		# Create window and hide borders.
# 		QtGui.QMainWindow.__init__(self, None, QtCore.Qt.FramelessWindowHint)
# 		self.program_settings = program_settings
# 		self.model_collection = model_collection
# 		self.projector_index = projector_index

# 		# Set the geometry of the window.
# 		self.set_window_position()

# 		# Create image.
# 		self.image = ProjectorImage(self.program_settings, self.model_collection, self.projector_index)
# 		self.setCentralWidget(self.image)

# 		# Show the window.
# 		self.show()

# 	def set_image(self, slice_index):
# 		self.image.set_image(slice_index)
	
# 	# Set the size and the position of the top left corner of the window, measured from the top left corner of the screen.
# 	def set_window_position(self):
# 		self.setGeometry(int(self.projector_index*self.program_settings['projector_width'].get_value()+self.program_settings['projector_position_x'].get_value()), self.program_settings['projector_position_y'].get_value(), self.program_settings['projector_height'].get_value(), self.program_settings['projector_width'].get_value())


# class messageWindowSaveSlices(QtGui.QDialog):
# 	# Override init function.
# 	def __init__(self, parent, modelCollection, path):
# 		# Call super class init function.
# 		QtGui.QDialog.__init__(self, parent)
# 		# Set title.
# 		self.setWindowTitle("Saving...")
# 		# Set modal.
# 		self.setWindowModality(QtCore.Qt.ApplicationModal)

# 		# Main layout.
# 		layout = QtGui.QVBoxLayout()
# 		self.setLayout(layout)

# 		# Progress bar.
# 		self.bar = QtGui.QProgressBar()
# 		self.bar.setValue(0)
# 		layout.addWidget(self.bar)

# 		# Show dialog.
# 		self.open()

# 		# This function was deleted:
# 		# Save the model collection to the given location.
# 		# modelCollection.saveSliceStack(path=path, updateFunction=self.updateBar)

# 	def updateBar(self, value):
# 		QtGui.QApplication.processEvents()
# 		self.bar.setValue(value)


# # A label displaying an image and buttons for opening and removing the image.
# class ImageLoader(QtGui.QWidget):
# 	def __init__(self, header=''):
# 		super(ImageLoader, self).__init__()

# 		# Set layout.
# 		layout = QtGui.QVBoxLayout()
# 		layout.setContentsMargins(0,0,0,0)
# 		self.setLayout(layout)

# 		# Create label.
# 		self.label = SmallLabel()

# 		# Create buttons.
# 		self.button_load = Button(text='Open...', callback=self.callback_load)
# 		self.button_remove = Button(text='Remove', callback=self.callback_remove)
# 		# Set initial states of buttons.
# 		self.button_remove.setEnabled(False)
# 		# Create layout for buttons.
# 		layout_buttons = QtGui.QHBoxLayout()
# 		layout_buttons.addWidget(self.button_load)
# 		layout_buttons.addWidget(self.button_remove)

# 		# Add items to layout.
# 		if header:
# 			layout.addWidget(Header(header))
# 		layout.addWidget(self.label)
# 		layout.addLayout(layout_buttons)

# 		# Set the initial appearance.
# 		self.callback_remove()
	
# 	# Show a file dialog and display the image in the label.
# 	def callback_load(self):
# 		file_dialog = QtGui.QFileDialog()
# 		file_dialog.setFileMode(QtGui.QFileDialog.ExistingFile)
# 		file_dialog.setFilter('Images (*.png *.jpg)')
# 		file_dialog.setWindowTitle('Open')
# 		# Display the selected file.
# 		if file_dialog.exec_() == QtGui.QDialog.Accepted:
# 			file_path = str(file_dialog.selectedFiles()[0])
# 			if file_path.lower().endswith('.png') or file_path.lower().endswith('.jpg'):
# 				self.label.clear()
# 				self.label.setPixmap(QtGui.QPixmap(file_path))
# 				# Update button states.
# 				self.button_remove.setEnabled(True)
	
# 	# Remove the image from the label.
# 	def callback_remove(self):
# 		self.label.clear()
# 		self.label.setText('No image loaded.')
# 		# Update button states.
# 		self.button_remove.setEnabled(False)


# Ordered list of actions performed during the print process.
class printProcessTableView(QtGui.QWidget):
	def __init__(self, settings, parent, console=None):
		# Init super class.
		QtGui.QWidget.__init__(self)
		self.show()

		# Internalise settings.
		self.settings = settings
		self.console = console
		self.parent = parent

		# Create and set layout.
		layout = QtGui.QVBoxLayout()
		self.setLayout(layout)

		"""
		# Main frame.
		framePrintProcess = QtGui.QGroupBox('Print process')
		framePrintProcess.setFlat(False)
		layout.addWidget(framePrintProcess)
		boxPrintProcess = QtGui.QVBoxLayout()
		framePrintProcess.setLayout(boxPrintProcess)
		"""

		# Load module list from settings.
		self.listModules = self.settings.getModuleList()

		# Load print process list from settings.
		#self.printProcessList = self.settings.getPrintProcessList()
		# Create table model from list.
		self.modelPrintProcess = printProcessTableModel(self.settings.getPrintProcessList(), 2)

		# Create the print process scrolled window.
		self.tableView = QtGui.QTableView()
		# Select whole rows instead of individual cells.
		self.tableView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		# Set single selection mode.
		self.tableView.setSelectionMode(1)
		# Hide the cell grid.
		self.tableView.setShowGrid(False)
		# Hide the vertical headers.
		self.tableView.verticalHeader().hide()
		"""
		# Set the row height.
		self.tableView.verticalHeader().setDefaultSectionSize(20)
		"""
		# Hide the grey dotted line of the item in focus.
		# This will disable focussing, so no keyboard events can be processed.
		self.tableView.setFocusPolicy(QtCore.Qt.NoFocus)
		# Prevent the header font from being made bold if a row is selected.
		self.tableView.horizontalHeader().setHighlightSections(False)
		layout.addWidget(self.tableView)
		# Stretch last column to fit width of view.
		self.tableView.horizontalHeader().setStretchLastSection(True)
		# Auto-adjust column widths to fit contents.
		self.tableView.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
		# Show print process module list.
		self.tableView.setModel(self.modelPrintProcess)
		# Select first row.
		self.tableView.selectRow(0)
		# Connection selection changed event.
		self.tableView.selectionModel().selectionChanged.connect(self.callbackSelectionChanged)

		# Create buttons.
		layoutButtons = QtGui.QHBoxLayout()
		layoutButtons.setSpacing(0)
		layoutButtons.setContentsMargins(0,0,0,0)
		layout.addLayout(layoutButtons)
		# Module drop down.
		self.dropdownModules = QtGui.QComboBox(self)
		for module in self.listModules:
			self.dropdownModules.addItem(module[0])
		layoutButtons.addWidget(self.dropdownModules)
		#self.dropdownModules.activated[str].connect(self.style_choice)
		# Buttons.
		# Add.
		self.buttonAdd = QtGui.QPushButton('Add')
		self.buttonAdd.clicked.connect(self.callbackButtonAdd)
		layoutButtons.addWidget(self.buttonAdd)
		# Remove.
		self.buttonRemove = QtGui.QPushButton('Remove')
		self.buttonRemove.clicked.connect(self.callbackButtonRemove)
		self.buttonRemove.setEnabled(len(self.modelPrintProcess.tableData) > 0)
		layoutButtons.addWidget(self.buttonRemove)
		# Move up.
		self.buttonUp = QtGui.QPushButton(u'\u2191')
		# self.buttonUp.setMaximumSize(QtCore.QSize(27,27))  # Dont need
		self.buttonUp.clicked.connect(self.callbackButtonUp)
		self.buttonUp.setEnabled(False)
		layoutButtons.addWidget(self.buttonUp)
		# Move down.
		self.buttonDown = QtGui.QPushButton(u'\u2193')
		# self.buttonDown.setMaximumSize(QtCore.QSize(27,27))  # Dont need
		self.buttonDown.clicked.connect(self.callbackButtonDown)
		self.buttonDown.setEnabled(False)
		layoutButtons.addWidget(self.buttonDown)
		# Set button sensitivities.
		self.setButtonSensitivities()

	# Return the raw print process list.
	def getPrintProcessList(self):
		return self.modelPrintProcess.tableData

	# Insert the module selected in drop down into the print process list.
	def callbackButtonAdd(self, widget, data=None):
		# Get current selection from dropdown.
		item = self.listModules[self.dropdownModules.currentIndex()]
		# Get current selection from table view.
		if len(self.tableView.selectionModel().selectedRows()) > 0:
			rowCurrent = self.tableView.selectionModel().selectedRows()[0].row()
		else:
			rowCurrent = -1
		# Add to table model.
		self.modelPrintProcess.insertRows(item, position=rowCurrent + 1, rows=1)
		# Set new row selected.
		self.tableView.selectRow(rowCurrent + 1)
		# Activate the remove button which was deactivated when there was no model.
		self.setButtonSensitivities()

	# Delete the selected module from the print process list.
	def callbackButtonRemove(self, widget, data=None):
		# Get selected row. We have single select mode, so only one (the first) will be selected.
		removeIndex = self.tableView.selectionModel().selectedRows()[0]
		# Find out which row to select after the current selection has been deleted.
		currentIndex = removeIndex
		# Select the next model in the list before deleting the current one.
		# If current selection at end of list but not the last element...
		if currentIndex == len(self.modelPrintProcess.tableData) - 1 and len(self.modelPrintProcess.tableData) > 1:
			# ... select the previous item.
			currentIndex -= 1
			self.tableView.selectRow(currentIndex)
		# If current selection is somewhere in the middle...
		elif currentIndex < len(self.modelPrintProcess.tableData) - 1 and len(self.modelPrintProcess.tableData) > 1:
			# ... selected the next item.
			currentIndex += 1
			self.tableView.selectRow(currentIndex)
		# If current selection is the last element remaining...
		elif len(self.modelPrintProcess.tableData) == 1:
			pass

		# Now, remove from QT table model.
		# Turn into persistent indices which keep track of index shifts as
		# items get removed from the model.
		# This is only needed for removing multiple indices (which we don't do, but what the heck...)
		persistentIndices = [QtCore.QPersistentModelIndex(index) for index in self.tableView.selectionModel().selectedRows()]
		for index in persistentIndices:
			self.modelPrintProcess.removeRow(index.row())

		# Set button sensitivities.
		self.setButtonSensitivities()

	# Swap the selected row with the one above.
	def callbackButtonUp(self, widget, data=None):
		rowCurrent = self.tableView.selectionModel().selectedRows()[0].row()
		if rowCurrent > 0:
			self.modelPrintProcess.swapRows(rowCurrent, rowCurrent-1)
		# Set selection to moved row.
		self.tableView.selectRow(rowCurrent-1)

	# Swap the selected row with the one below.
	def callbackButtonDown(self, widget, data=None):
		rowCurrent = self.tableView.selectionModel().selectedRows()[0].row()
		if rowCurrent <= len(self.modelPrintProcess.tableData):
			self.modelPrintProcess.swapRows(rowCurrent, rowCurrent+1)
		# Set selection to moved row.
		self.tableView.selectRow(rowCurrent+1)

	# Selection changed callback.
	def callbackSelectionChanged(self, selection):
		self.setButtonSensitivities()

	# Set button sensitivities according to selection and list length.
	def setButtonSensitivities(self):
		# Check if the model is empty.
		if len(self.modelPrintProcess.tableData) > 0 and len(self.tableView.selectionModel().selectedRows()) > 0:
			rowCurrent = self.tableView.selectionModel().selectedRows()[0].row()
			# Set up button sensitivity.
			self.buttonUp.setEnabled(rowCurrent > 0)
			# Set down button sensitivity.
			self.buttonDown.setEnabled(rowCurrent != len(self.modelPrintProcess.tableData)-1)
			# Set remove button sensitivity.
			# Disable remove button for loop start and loop end commands.
			self.buttonRemove.setEnabled("loop" not in self.modelPrintProcess.tableData[rowCurrent][0])
		else:
			self.buttonUp.setEnabled(False)
			self.buttonDown.setEnabled(False)
			self.buttonRemove.setEnabled(False)


# ==============================================================================
# Create a table model for the print process including add and remove methods.
# ==============================================================================
# Custom table model.
# Data carries the following columns:
# Model name, slicer status, model ID, stl path, model acitve flag.
class printProcessTableModel(QtCore.QAbstractTableModel):
	def __init__(self, tableData, numDispCols, parent = None, *args):
		QtCore.QAbstractTableModel.__init__(self, parent, *args)

		self.tableData = tableData
		self.numDispCols = numDispCols
		self.checkBoxChanged = False

	# This will be called by the view to determine the number of rows to show.
	def rowCount(self, parent):
		return len(self.tableData)

	# This will be called by the view to determine the number of columns to show.
	# We only want to show a certain number of columns, starting from 0 and
	# ending at numDispCols
	def columnCount(self, parent):
		if len(self.tableData) > 0:
			if self.numDispCols <= len(self.tableData[0]):
				return self.numDispCols
			else:
				return len(self.tableData[0])
		else:
			return 0

	# This gets called by the view to get the data at the given index.
	# Based on the row and column number retrieved from the index, we
	# assign different roles the the returned data. This predicts how the data
	# is shown. The view will request all roles and if the requested one matches
	# the one we want to show for the given index, we'll return it.
	# DisplayRole will show the data, all other roles will modify the display.
	def data(self, index, role):
		# Return nothing if index is invalid.
		if not index.isValid():
			return QtCore.QVariant()
		# Get row and column.
		row = index.row()
		column = index.column()

		# Return the data.
		if role == Qt.DisplayRole:
			return QtCore.QVariant(self.tableData[index.row()][index.column()])

		# If user starts editing the cell by double clicking it, also return the data.
		# Otherwise cell will be empty once editing is started.
		if role == Qt.EditRole:
			return QtCore.QVariant(self.tableData[index.row()][index.column()])

		# Add a check box to all rows in column 0.
		# Set the checkbox state depending on the data in column 3.
		elif role == Qt.CheckStateRole:
			if column == 0:
				if self.tableData[row][5]:
					return Qt.Checked
				else:
					return Qt.Unchecked

		# Return tooltip.
		elif role == Qt.ToolTipRole:
			if column == 0:
				return "Use the check box to enable or disable this command.\nDouble click to rename."
			else:
				return "Double click to modify."

		# Return alignment.
		elif role == Qt.TextAlignmentRole:
			return Qt.AlignLeft + Qt.AlignVCenter

		# If none of the conditions is met, return nothing.
		return QtCore.QVariant()

	# Provide header strings for the horizontal headers.
	# Vertical headers are empty.
	# Role works the same as in data().
	def headerData(self, section, orientation, role):
		if role == Qt.DisplayRole:
			if orientation == Qt.Horizontal:
				if section == 0:
					return QtCore.QString("Module")
				elif section == 1:
					return QtCore.QString("Commands")

	# This is called once user editing of a cell has been completed.
	# The value is the new data that has to be manually set to the
	# tableData within the setData method.
	def setData(self, index, value, role=Qt.EditRole):
		row = index.row()
		column = index.column()
		if role == Qt.EditRole:
			self.tableData[row][column] = value.toString()
		elif role == Qt.CheckStateRole:
			self.checkBoxChanged = True
			if value == Qt.Checked:
				self.tableData[row][5] = Qt.Checked
			elif value == Qt.Unchecked:
				self.tableData[row][5] = Qt.Unchecked

		# Emit the data changed signal to let possible other views that
		# didn't do the editing know about the changed data.
		self.dataChanged.emit(index, index)
		return True

	# This will be called by the view to determine if the cell that
	# has been clicked is enabled, editable, checkable, selectable and so on.
	def flags(self, index):
		# Get row and column.
		row = index.row()
		column = index.column()

		if column == 0:
			# Allow modification of name for serial commands.
			# Allow modification of value for serial commands and those with a true edit flag.
			if self.tableData[row][3] == 'internal':
				return Qt.ItemIsSelectable |  Qt.ItemIsEnabled | Qt.ItemIsUserCheckable
			else:
				return Qt.ItemIsSelectable |  Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsUserCheckable
		elif column == 1:
			if self.tableData[row][4] == True:
				return Qt.ItemIsSelectable |  Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsUserCheckable
			else:
				return Qt.ItemIsSelectable |  Qt.ItemIsEnabled | Qt.ItemIsUserCheckable

	# This is called for inserting a row.
	# Position: where to insert, rows: how many to insert,
	# parent: who will be parent in a tree view?
	# beginInsertRows(index, first, last) tells the views where data is inserted.
	# index is for hierarchical data, so we pass an empty QModelIndex, that
	# points to the root index.
	def insertRows(self, data, position, rows, parent=QtCore.QModelIndex()):
		self.beginInsertRows(parent, position, position+rows-1)
		for i in range(rows):
			if len(data) == 6:
				self.tableData.insert(position, data)
			else:
				raise ValueError("Print process module has wrong length.")
		self.endInsertRows()
		return True

	# This is called for removing a row.
	# Position: where to insert, rows: how many to insert,
	# parent: who will be parent in a tree view?
	def removeRows(self, position, rows, parent=QtCore.QModelIndex()):
		self.beginRemoveRows(parent, position, position+rows-1)
		for i in range(rows):
			del self.tableData[position]

		self.endRemoveRows()
		return True

	def swapRows(self, position1, position2):
		# Get row data.
		row1 = self.tableData[position1]
		row2 = self.tableData[position2]
		# Set interchanged row data.
		self.tableData[position1] = row2
		self.tableData[position2] = row1

	# Delete all the data.
	#TODO: leave "default" model in table data upon clearing?
	#def clearData(self):
	#	if len(self.tableData) != 0:
	#		self.beginRemoveRows(QModelIndex(), 0, len(self.tableData) - 1)
	#		self.tableData = []
	#		self.endRemoveRows()