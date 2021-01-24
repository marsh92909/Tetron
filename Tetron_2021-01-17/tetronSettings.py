# -*- coding: latin-1 -*-


import os
import sys
import threading


# An object with attributes containing values and information about a setting.
class Setting:
	def __init__(self, value, data_type, step=None, lower=-1e9, upper=1e9, value_previous=None, value_list=None, unit='', name=None, editable=True, savable=True):
		# The current value of the setting.
		self.value = value
		# The default value of the setting.
		self.default = value
		# The data type of the value.
		self.data_type = data_type
		# The increment by which the setting can be changed. Only used by numeric settings shown as a spin box in the GUI.
		self.step = step
		# The minimum value of the setting. Only used by numeric settings.
		self.lower = lower
		# The maximum value of the setting. Only used by numeric settings.
		self.upper = upper
		# The previous value of the setting.
		self.value_previous = value
		# A list of all the allowed values of the setting. Only used by settings shown as a popup menu.
		self.value_list = value_list
		# A string of the units of the value.
		self.unit = unit
		# A string of the setting name shown in the GUI.
		self.name = name
		# A boolean indicating if the setting value can be changed. Set to False for settings that should never change.
		self.editable = editable
		# A boolean indicating if the setting value should not be saved when the program closes. Used by settings that require a specific value on each startup.
		self.savable = savable

		# Create a lock object to prevent race conditions if multiple threads access the setting object.
		self.lock = threading.Lock()

	# Set the value of the setting.
	def set_value(self, value):
		self.lock.acquire()
		if self.editable:
			# Set the previous value.
			self.value_previous = self.value
			# Set the current value.
			if self.data_type == float or self.data_type == int:
				# Keep numeric values inside the range.
				value = self.data_type(value)
				value = max(self.lower, value)
				value = min(self.upper, value)
				self.value = self.data_type(value)
			elif value == 'True':
				self.value = True
			elif value == 'False':
				self.value = False
			else:
				self.value = value
		else:
			print('The setting {} cannot be changed.'.format(self.name))
		self.lock.release()

	# Return the current value of the setting.
	def get_value(self):
		self.lock.acquire()
		value = self.value
		self.lock.release()
		return value

	# Return the previous value of the setting.
	def get_value_previous(self):
		self.lock.acquire()
		value_previous = self.value_previous
		self.lock.release()
		return value_previous


# A dictionary containing settings object for the program. Only one instance of this class is created.
class ProgramSettings(dict):
	def __init__(self):
		dict.__init__(self)

		# Program and directories.
		self['program_name'] = Setting(value='Tetron', data_type=str, name='Program Name', editable=False, savable=False)
		self['version_number'] = Setting(value='X.X.X', data_type=str, name='Version Number', editable=False, savable=False)
		self['version_date'] = Setting(value='2021-01-01', data_type=str, name='Version Date', editable=False, savable=False)
		self['installDir'] = Setting(value=self.getInstallDir(), data_type=str, editable=False)
		self['currentFolder'] = Setting(value='./Models', data_type=str)
		self['tmpDir'] = Setting(value=self.getInstallDir()+'/tmp', data_type=str, editable=False)
		self['imagesDir'] = Setting(value='Images', data_type=str, editable=False)

		# Game settings.
		self['row_count'] = Setting(value=20, data_type=int, step=1, lower=4, upper=100, name='Rows')
		self['column_count'] = Setting(value=10, data_type=int, step=1, lower=4, upper=100, name='Columns')
		self['speed'] = Setting(value=5, data_type=int, step=1, lower=0.2, upper=1000, unit='lines/sec.', name='Block Falling Speed')
		self['next_count'] = Setting(value=5, data_type=int, step=1, lower=1, upper=10, name='Next Blocks Shown')

	# Write values of settings to a file.
	def save_to_file(self, path):
		# Set file path.
		if path[-1] != '/':
			path += '/'
		# Open a file and write each setting to the file.
		with open(path + 'settings', 'w') as f:
			for setting in self:
				# Convert to string and write to file.
				if self[setting].savable:
					string = setting + '|' + str(self[setting].get_value()) + '\n'
					f.write(string)

	# Load values of settings from a file.
	def load_from_file(self, path, filename=None):
		# Format the path.
		if filename is None:
			filename = 'settings'
		if path[-1] != '/':
			path += '/'
		filename = path + filename
		# Open the file and set the values of each setting.
		try:
			with open(filename, 'r') as f:
				for line in f:
					line = line.strip()
					if line != '':
						setting_name, value = line.split('|')
						try:
							if self[setting_name].savable:
								self[setting_name].set_value(value)
						except KeyError:
							print('The setting {} does not exist and was skipped.'.format(setting_name))
		except IOError:
			pass

	# Set all settings to their default values.
	def set_default(self):
		for setting in self:
			if self[setting].default:
				self[setting].value = self[setting].default

	# Get install dir for running from packaged exe or script.
	# https://stackoverflow.com/questions/7674790/bundling-data-files-with-pyinstaller-onefile
	def getInstallDir(self):
		try:
			# PyInstaller creates a temp folder and stores path in _MEIPASS
			base_path = sys._MEIPASS
		except AttributeError:
			base_path = os.path.abspath('.')
		return base_path

	def getModuleList(self):
		moduleList = self['printModulesGCode'].value.split(';')
		for i in range(len(moduleList)):
			moduleList[i] = moduleList[i].split(',')
			# Turn True/False string into boolean.
			moduleList[i][-1] = eval(moduleList[i][-1])
			moduleList[i][-2] = eval(moduleList[i][-2])
		return moduleList

	def setModuleList(self, moduleList):
		settingString = ''
		for row in range(len(moduleList)):
			settingString += str(moduleList[row])
			if row < len(moduleList)-1:
				settingString += ';'
		self['printModulesGCode'].value = settingString

	def getPrintProcessList(self):
		printProcessList = self['printProcessGCode'].value.split(';')
		for i in range(len(printProcessList)):
			# Split comma separated string for each command.
			printProcessList[i] = printProcessList[i].split(',')
			# Turn True/False string into boolean.
			printProcessList[i][-1] = eval(printProcessList[i][-1])
			printProcessList[i][-2] = eval(printProcessList[i][-2])
		return printProcessList

	def setPrintProcessList(self, moduleList):
		settingString = ''
		for row in range(len(moduleList)):
			for item in range(len(moduleList[row])):
				settingString += str(moduleList[row][item])
				if item < len(moduleList[row])-1:
					settingString += ','
			if row < len(moduleList)-1:
				settingString += ';'
		self['printProcessGCode'].value = settingString