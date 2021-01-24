#!/usr/bin/python
# -*- coding: latin-1 -*-


import getopt  # Needed to parse command line arguments.
import os
import sys
import time

import tetronGui
import tetronGuiHelper
import tetronSettings


def runGui():
	# Create a dictionary containing the program settings.
	program_settings = tetronSettings.ProgramSettings()
	# Load settings from file.
	cwd = os.getcwd()
	program_settings.load_from_file(cwd)
	
	# Create a debug console text buffer.
	console = tetronGuiHelper.ConsoleText()

	# Create version string.
	program_name = program_settings['program_name'].get_value()
	version_number = program_settings['version_number'].get_value()
	print('Starting ' + program_name + ' ' + version_number + '.')
	console.addLine(program_name + ' ' + version_number)

	# Get current working directory for EXE.
	directory = getInstallDir()
	program_settings['installDir'].set_value(directory)
	print('Running from ' + directory)

	# Create model collection object, which contains the data and settings for each model.
	# model_collection = theaterModelHandling.modelCollection(program_settings, console)

	# Create GUI.
	gui = tetronGui.GUI(program_settings, console) # model_collection, console)
	# Enter the main event loop.
	gui.exec_()


# https://stackoverflow.com/questions/7674790/bundling-data-files-with-pyinstaller-onefile
def getInstallDir():
	try:
		# PyInstaller creates a temp folder and stores path in _MEIPASS
		base_path = sys._MEIPASS
	except AttributeError:
		base_path = os.path.abspath('.')
	return base_path

runGui()