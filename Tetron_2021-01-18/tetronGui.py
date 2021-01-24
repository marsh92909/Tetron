# -*- coding: latin-1 -*-


import os
import Queue
import random
import shutil
import signal
import sys
import threading
import time

import numpy as np
import PyQt4
from PyQt4 import QtGui, QtCore, Qt

import tetronGuiHelper


# The main application.
class GUI(QtGui.QApplication):
	def __init__(self, program_settings, console=None): #model_collection, console=None):
		super(GUI, self).__init__(sys.argv)
		self.program_settings = program_settings
		# self.model_collection = model_collection
		self.console = console

		# Create a signal that allows Ctrl+C to close the program from console.
		signal.signal(signal.SIGINT, signal.SIG_DFL)

		# Create an instance of printcore, without connecting to the printer.
		# self.printer = tetronSerial.Printcore()

		# Create a dictionary to store the projector windows.
		# self.projector_windows = {}

		# Initialize flags that are set to True during printing, pausing, or slicing.
		self.flag_playing = False
		self.flag_paused = False
		self.flag_slicing = False

		# Initialize the block fall speed.
		self.speed = 1000/self.program_settings['speed'].get_value()

		# Get the numbers of rows and columns.
		row_count = self.program_settings['row_count'].get_value()
		column_count = self.program_settings['column_count'].get_value()
		# Initialize the array used to represent all blocks shown on the matrix.
		self.array_display = np.zeros([row_count, column_count])
		# Initialize the array used to represent only the current block.
		self.array_current = np.zeros([row_count, column_count])
		self.array_placed = np.zeros([row_count, column_count])
		# Initialize current position.
		self.current_position = [[0,0], [0,0]]

		# Create a queue for current grid array.
		self.queue_update_matrix = Queue.Queue()
		# Create a queue for next tetriminos.
		self.queue_next = Queue.Queue()
		# Create a queue for hold tetriminos.
		self.queue_hold = Queue.Queue(maxsize=1)
		# Create a queue for row and column values of current tetrimino.
		self.queue_current_position = Queue.Queue()
		# Create a queue to stop the game and timers.
		self.queue_stop = Queue.Queue()
		# Create a queue for receiving information from other threads to update the status labels.
		self.queue_status = Queue.Queue()
		# Create a queue for receiving messages from other threads to be shown in the console.
		self.queue_console = Queue.Queue()

		# # Create a queue for receiving slicing progress values from the slice thread.
		# self.queue_slicing_index = Queue.Queue()
		# # Create a queue for receiving the current slice index from the print thread to update the projector window.
		# self.queue_printing_index = Queue.Queue(maxsize=1)
		# # Create a queue for sending a boolean to the print thread to indicate that exposure can begin.
		# self.queueSliceIn = Queue.Queue(maxsize=1)
		# # Create a queue for receiving the supports data object from the supports thread.
		# self.queue_supports = Queue.Queue()

		# Create a timer that calls a function that checks the queues every n milliseconds.
		self.timer_check_queues = QtCore.QTimer()
		self.timer_check_queues.timeout.connect(self.check_queues)
		self.timer_check_queues.setInterval(50)

		# Create a timer that advances the current tetrimino down by one line every n milliseconds.
		self.timer_advance = QtCore.QTimer()
		self.timer_advance.timeout.connect(self.advance_line)
		self.timer_advance.setInterval(self.speed)

		# Create a timer that increases the block fall speed every n milliseconds.
		self.timer_increase_difficulty = QtCore.QTimer()
		self.timer_increase_difficulty.timeout.connect(self.increase_difficulty)
		self.timer_increase_difficulty.setInterval(20*1000)

		# ======================================================================
		# Create the main GUI.
		# ======================================================================

		# # Install a custom font.
		# font_database = QtGui.QFontDatabase()
		# font_database.addApplicationFont('Font/Inter-Regular.ttf')
		# # Set the application font style.
		# self.setFont(QtGui.QFont('Inter', 10))
		font = self.font()
		font.setPointSize(16)
		self.setFont(font)
		# self.setFont(QtGui.QFont().setPointSize(16))

		# Pass to tetronGuiHelper an instance of QDesktopWidget, which contains information about the geometry and arrangement of screen(s).
		tetronGuiHelper.get_screen_geometry(self.desktop())

		# Create main window.
		self.main_window = MainWindow(self, self.program_settings)
		widget_central = QtGui.QWidget()
		self.main_window.setCentralWidget(widget_central)
		self.main_window.showMaximized()

		# Create overall layout and place inside main window.
		layout = QtGui.QVBoxLayout()
		widget_central.setLayout(layout)

		# Create toolbar layout and place inside overall layout.
		layout_toolbar = QtGui.QHBoxLayout()
		# layout_toolbar.setSpacing(0)
		layout.addLayout(layout_toolbar)
		# Create action buttons widget and place inside toolbar layout.
		layout_actions = self.create_toolbar_buttons()
		layout_toolbar.addLayout(layout_actions)
		# Create status labels and place inside toolbar layout.
		self.status_labels = self.create_status_labels()
		layout_toolbar.addLayout(self.status_labels)
		# Set relative widths of widgets in toolbar.
		layout_toolbar.setStretch(0, 5)
		layout_toolbar.setStretch(1, 1)

		# Create main layout and place inside overall layout.
		layout_main = QtGui.QHBoxLayout()
		layout.addLayout(layout_main)
		# Create matrix widget and place inside main layout.
		layout_main.addStretch(1)
		self.widget_matrix = Matrix(self)
		self.layout_matrix = QtGui.QVBoxLayout()
		self.layout_matrix.addWidget(self.widget_matrix)
		layout_main.addLayout(self.layout_matrix)
		layout_main.addStretch(1)

		# # Create tab widget and place inside overall layout.
		# widget_tab = tetronGuiHelper.Tab()
		# layout.addWidget(widget_tab)
		# # Create widgets for each tab and add them to tab widget.
		# self.tab1 = Tab1(self)
		# self.tab2 = Tab2(self)
		# self.tab3 = Tab3(self)
		# self.tab4 = Tab4(self)
		# widget_tab.addTab(self.tab1, QtGui.QIcon(self.program_settings['imagesDir'].get_value()+'/tab_models.png'), 'Models')
		# widget_tab.addTab(self.tab2, QtGui.QIcon(self.program_settings['imagesDir'].get_value()+'/tab_projectors.png'), 'Projectors')
		# widget_tab.addTab(self.tab3, QtGui.QIcon(self.program_settings['imagesDir'].get_value()+'/tab_controls.png'), 'Controls')
		# widget_tab.addTab(self.tab4, QtGui.QIcon(self.program_settings['imagesDir'].get_value()+'/tab_settings.png'), 'Settings')

		# Create menu bar below title bar of main window.
		# self.menu_bar = self.create_menu_bar()

		# Update.
		# self.update_entries()
		self.main_window.show()
		self.main_window.raise_()

	# Prepare the application for closing.
	def close(self):
		# # Close projector windows.
		# self.close_projector_windows()

		# Save program settings to file.
		self.program_settings.save_to_file('./')

		# Get all threads.
		running_threads = threading.enumerate()
		# End threads except for main gui thread.
		for i in range(len(running_threads)):
			if running_threads[i].getName() != 'MainThread':
				running_threads[i].stop()
				try:
					running_threads[i].join(timeout=1000)  # Timeout in ms.
				except RuntimeError:
					print('Failed to join background thread.')
				else:
					print('Background thread ' + str(i) + ' finished.')

		# Remove temp directory.
		shutil.rmtree(self.program_settings['tmpDir'].value, ignore_errors=True)

	# # Create projector windows or show them if they already exist.
	# def create_projector_windows(self):
	# 	if len(self.projector_windows) == 0:
	# 		for projector_index in range(self.program_settings['projector_count'].get_value()):
	# 			self.projector_windows[projector_index] = tetronGuiHelper.ProjectorWindow(self.program_settings, self.model_collection, projector_index)
	# 	else:
	# 		for projector_index in self.projector_windows:
	# 			self.projector_windows[projector_index].showNormal()
	# 			self.projector_windows[projector_index].raise_()

	# # Minimize existing projector windows.
	# def minimize_projector_windows(self):
	# 	for projector_index in self.projector_windows:
	# 		self.projector_windows[projector_index].showMinimized()

	# # Close existing projector windows.
	# def close_projector_windows(self):
	# 	for projector_index in self.projector_windows:
	# 		self.projector_windows[projector_index].destroy()
	# 	self.projector_windows = {}
	
	# Create a new tetrimino at the top.
	def new_tetrimino(self):
		# Clear the current tetrimino array.
		self.array_current[:] = 0
		# Get and remove the next tetrimino from the queue.
		code = self.queue_next.get()
		# Create the array for the tetrimino.
		if code == 'I':
			self.current_tetrimino = 1 * np.ones([4, 1])
		elif code == 'J':
			self.current_tetrimino = 2 * np.ones([2, 3])
			self.current_tetrimino[0, 1:] = 0
		elif code == 'L':
			self.current_tetrimino = 3 * np.ones([2, 3])
			self.current_tetrimino[0, 0:2] = 0
		elif code == 'O':
			self.current_tetrimino = 4 * np.ones([2, 2])
		elif code == 'S':
			self.current_tetrimino = 5 * np.ones([2, 3])
			self.current_tetrimino[0, 0] = 0
			self.current_tetrimino[-1, -1] = 0
		elif code == 'T':
			self.current_tetrimino = 6 * np.ones([2, 3])
			self.current_tetrimino[0, 0] = 0
			self.current_tetrimino[0, -1] = 0
		elif code == 'Z':
			self.current_tetrimino = 7 * np.ones([2, 3])
			self.current_tetrimino[1, 0] = 0
			self.current_tetrimino[0, -1] = 0
		# Generate the next tetrimino.
		self.generate_next()

		# Update the array of the current tetrimino.
		row_left = int((self.program_settings['column_count'].get_value()-self.current_tetrimino.shape[1])/2)
		self.array_current[0:self.current_tetrimino.shape[0], row_left:row_left+self.current_tetrimino.shape[1]] = self.current_tetrimino
		# Update the displayed array.
		self.array_display = self.array_current + self.array_placed

		# Indicate to the queue that the displayed array has changed.
		self.queue_update_matrix.put(True)
		# Add the current position to the queue.
		# self.queue_current_position.put([[0,self.current_tetrimino.shape[0]], [row_left,row_left+self.current_tetrimino.shape[1]]])
	
	# Advance the current tetrimino by one line.
	def advance_line(self):
		# Row and column indices of nonzero elements in current array.
		indices_rows, indices_columns = np.nonzero(self.array_current)
		# Determine if at the bottom of the matrix.
		is_not_at_bottom = not np.any((indices_rows+1) > (self.array_placed.shape[0]-1))
		# Determine if advancing a line will intersect already placed blocks
		try:
			no_intersection = not np.any(self.array_placed[indices_rows+1, indices_columns])
		except IndexError:
			no_intersection = False
		# If not intersecting, advance one line.
		if is_not_at_bottom and no_intersection:
			self.array_current = np.roll(self.array_current, shift=1, axis=0)
			self.array_display = self.array_current + self.array_placed
			self.queue_update_matrix.put(True)
		else:
			self.place()
			self.new_tetrimino()
		# # List of Booleans indicating which columns of the matrix contain blocks from the current tetrimino.
		# columns = np.any(self.array_current, axis=0)
		# rows = np.any(self.array_current, axis=1)
		# Indices of rows containing bottommost blocks of current tetrimino. Also contains indices for last row of matrix.
		# indices_bottom_blocks = (self.array_current.shape[0]-1) - np.argmax(np.flipud(self.array_current) != 0, axis=0)
		# indices_bottom_blocks[not columns] = 0
		###

		# # Advance if bottom row is empty.
		# if not np.any(self.array_current[-1, :]) and :
		# 	self.array_current = np.roll(self.array_current, shift=1, axis=0)
		# 	self.array_display = self.array_current + self.array_placed
		# 	self.queue_update_matrix.put(True)
		# # Place the current tetrimino if at the bottom.
		# else:
		# 	self.place()
		# 	self.new_tetrimino()
		# current_rows = self.current_position[0]
		# # Advance down one line.
		# if current_rows[-1] < self.program_settings['row_count'].get_value():
		# 	current_rows[0] += 1
		# 	current_rows[-1] += 1
		# 	self.queue_current_position.put([current_rows, self.current_position[-1]])
		# # If at the bottom or reached another block, place current one.
		# else:
		# 	self.place()
		# 	self.new_tetrimino()
	
	def rotate(self, times=0):
		previous_position = self.current_position
		self.current_tetrimino = np.rot90(self.current_tetrimino, times)
		current_position = self.queue_current_position.get()

	def place(self):
		# Reset advance timer.
		self.timer_advance.start()

		# List of Booleans indicating which columns of the matrix contain blocks from the current tetrimino.
		columns = np.any(self.array_current, axis=0)
		rows = np.any(self.array_current, axis=1)
		
		# List of indices, counting from bottom (0 = bottom row), of the bottommost blocks of the current tetrimino.
		indices_current = np.argmax(np.flipud(self.array_current) != 0, axis=0)[columns]
		# List of indices of highest available positions in current tetrimino's columns.
		indices_placed = np.where(np.any(self.array_placed, axis=0), np.argmax(self.array_placed != 0, axis=0), (self.array_placed.shape[0]-1)*np.ones(self.array_placed.shape[1]))
		indices_placed = indices_placed[columns]
		
		# Index of lowest row that will contain the placed tetrimino.
		index_bottom_row = np.min(indices_placed - indices_current)
		# Index of row in which current tetrimino's bottom row is at.
		index_bottom_row_current = np.nonzero(rows)[0][-1]
		# Shift the current tetrimino down, if needed.
		shift = index_bottom_row-index_bottom_row_current
		if shift > 0:
			self.array_current = np.roll(self.array_current, shift=shift, axis=0)
		self.array_placed[self.array_current != 0] = self.array_current[self.array_current != 0]
		self.array_display = self.array_placed + self.array_current
		# If top row of matrix is filled, end the game.
		if np.any(self.array_current[0, :]):
			self.callback_stop()

		# Update GUI.
		self.queue_update_matrix.put(True)

		# Check for completed lines.
		pass

	def clear_lines(self):
		# Shift all rows down by one.
		self.array_display = np.roll(self.array_display, shift=1, axis=0)
		# Clear the top row.
		self.array_display[0, :] = 0

	# Randomly generate the next tetrimino and add it to the queue.
	def generate_next(self):
		random_integer = random.randint(1, 7)
		# Place the letter of the next tetrimino into the queue.
		if random_integer == 1:
			self.queue_next.put('I')
		elif random_integer == 2:
			self.queue_next.put('J')
		elif random_integer == 3:
			self.queue_next.put('L')
		elif random_integer == 4:
			self.queue_next.put('O')
		elif random_integer == 5:
			self.queue_next.put('S')
		elif random_integer == 6:
			self.queue_next.put('T')
		elif random_integer == 7:
			self.queue_next.put('Z')
	
	# Increase the difficulty of the game.
	def increase_difficulty(self):
		# Define the increment by which the speed is adjusted.
		speed_increment = 50
		if self.speed > speed_increment:
			self.speed -= 50
		self.timer_advance.setInterval(self.speed)

	# Check the queues for information and update the GUI during printing.
	# This function runs multiple times per second.
	def check_queues(self):
		# Update the attribute containing the current position.
		if self.queue_current_position.qsize():
			# Remove the current position from the queue and assign it to the attribute.
			self.current_position = self.queue_current_position.get()
			# Get the new row positions and column positions.
			current_rows = self.current_position[0]
			current_columns = self.current_position[1]
			# Empty the current tetrimino array and insert the current tetrimino in the updated position.
			self.array_current[:] = 0
			self.array_current[current_rows[0]:current_rows[-1], current_columns[0]:current_columns[-1]] = self.current_tetrimino
			# Empty the displayed array and recalculate where blocks are.
			self.array_display[:] = 0
			self.array_display = self.array_current + self.array_placed
			# self.array_display[np.logical_and(self.array_display != 0, self.array_current != 0)]

			# Indicate to the queue that the displayed array has changed.
			self.queue_update_matrix.put(True)

		# Check the queue, and update the matrix if it contains something.
		if self.queue_update_matrix.qsize():
			# Empty one item from the queue.
			self.queue_update_matrix.get()
			# Update the GUI.
			self.update_blocks()
		
		# 
		# if self.queue_next.qsize():
		# 	# Get and remove the next block from the queue.
		# 	next = self.queue_next.get()
		
		# 
		if self.queue_hold.qsize():
			pass
		
		if self.queue_stop.qsize():
			# Empty the queue.
			self.queue_stop.get()
			# Stop the timers.
			self.timer_check_queues.stop()
			self.timer_advance.stop()

		# If the status queue has information, update the status labels.
		if self.queue_status.qsize():
			self.update_status_labels(self.queue_status.get())

		# If console queue has info...
		if self.queue_console.qsize():
			if self.console != None:
				self.console.addLine(self.queue_console.get())

		# # If the slicing index queue has information, update the status labels and progress bar.
		# if self.queue_slicing_index.qsize():
		# 	slicing_index = self.queue_slicing_index.get()
		# 	if isinstance(slicing_index, int):
		# 		self.progress_bar.setValue(slicing_index+1)
		# 	# Show a message if any slices have errors. When slicing is finished, the slice thread sends a list of slice indices in which errors were found.
		# 	elif isinstance(slicing_index, list):
		# 		if len(slicing_index) > 0:
		# 			self.console.addLine('Warning: Possible errors in slices ' + str(slicing_index))
		
		# # If the printing index queue has information, update the projector window, the model view, and the progress bar.
		# if self.queue_printing_index.qsize():
		# 	printing_index = self.queue_printing_index.get()
		# 	# Update the projector window. A slice number of -1 shows black.
		# 	for projector_index in self.projector_windows:
		# 		self.projector_windows[projector_index].set_image(printing_index)

		# 	# Update the slice shown in the model view and update the progress bar.
		# 	if printing_index >= 0:
		# 		self.model_collection.updateAllSlices3d(printing_index)
		# 		self.tab1.model_view.render()
		# 		self.progress_bar.setValue(printing_index+1)

		# 	# Signal to the print thread that the exposure time can begin.
		# 	if self.queueSliceIn.empty():
		# 		self.queueSliceIn.put(True)
		
		# # If the supports queue has information, add the supports data to the model.
		# if self.queue_supports.qsize():
		# 	supports_data = self.queue_supports.get()
		# 	self.model_collection.get_current_model().add_supports(supports_data)
		# 	self.tab1.model_view.render()

		# Return True, otherwise function won't run again.
		return True

	# ==========================================================================
	# Methods for creating the menu bar.
	# ==========================================================================

	# Create the menu bar.
	def create_menu_bar(self):
		bar = self.main_window.menuBar()

		# Create File menu.
		menu_file = bar.addMenu('File')
		# Create items.
		action_open = QtGui.QAction('Open...', menu_file)
		action_save = QtGui.QAction('Save...', menu_file)
		action_quit = QtGui.QAction('Quit', menu_file)
		# Set callback functions.
		action_open.triggered.connect(self.callback_open)
		action_save.triggered.connect(self.callback_save)
		action_quit.triggered.connect(self.callback_menu_quit)
		# Set keyboard shortcuts.
		action_open.setShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL+QtCore.Qt.Key_O))
		action_save.setShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL+QtCore.Qt.Key_S))
		# Add items to menu.
		menu_file.addAction(action_open)
		menu_file.addAction(action_save)
		menu_file.addAction(action_quit)

		# Create Edit menu.
		menu_edit = bar.addMenu('Edit')
		# Create items.
		action_undo = QtGui.QAction('Undo', menu_edit)
		action_redo = QtGui.QAction('Redo', menu_edit)
		# Set callback functions.
		pass
		# Set keyboard shortcuts.
		action_undo.setShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL+QtCore.Qt.Key_Z))
		action_redo.setShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL+QtCore.Qt.SHIFT+QtCore.Qt.Key_Z))
		# Add items to menu.
		menu_edit.addAction(action_undo)
		menu_edit.addAction(action_redo)
		menu_edit.addSeparator()
		# Temporary: Disable actions.
		action_undo.setEnabled(False)
		action_redo.setEnabled(False)

		# Create View menu.
		menu_view = bar.addMenu('View')
		# Create items.
		action_show_axes = QtGui.QAction('Show Axes', menu_view)
		action_show_minor_gridlines = QtGui.QAction('Show Minor Gridlines', menu_view)
		# Set some items to be checkable and set initial states.
		action_show_axes.setCheckable(True)
		action_show_minor_gridlines.setCheckable(True)
		action_show_axes.setChecked(True)
		action_show_minor_gridlines.setChecked(True)
		# Set callback functions.
		# action_show_axes.triggered.connect(self.tab1.model_view.toggleVisiblityAxes)
		# action_show_minor_gridlines.triggered.connect(self.tab1.model_view.toggleVisiblityGridMinor)
		# Add items to menu.
		menu_view.addAction(action_show_axes)
		menu_view.addAction(action_show_minor_gridlines)

		# Create Help menu.
		menu_help = bar.addMenu('Help')
		# Create items.
		action_about = QtGui.QAction('About...', self)
		# Set callback functions.
		action_about.triggered.connect(self.callback_menu_about)
		# Add items to menu.
		menu_help.addAction(action_about)

		return bar

	# Close main window.
	def callback_menu_quit(self):
		self.main_window.close()
	
	# Open the settings window.
	def callback_settings(self):
		SettingsWindow(self.program_settings, self.main_window)
	
	# Open a dialog window to display information about the program.
	def callback_menu_about(self):
		AboutWindow(self.program_settings, self.main_window)
	
	# ==========================================================================
	# Methods for creating the toolbar.
	# ==========================================================================

	# Create a row of action buttons to insert in the toolbar.
	def create_toolbar_buttons(self):
		# Create layout.
		layout = QtGui.QHBoxLayout()

		# Create buttons.
		self.button_settings = tetronGuiHelper.Button(text='Settings', icon_filename=None, callback=self.callback_settings)
		self.button_play = tetronGuiHelper.Button(text='Play', icon_filename=None, callback=self.callback_play)
		self.button_stop = tetronGuiHelper.Button(text='Stop', icon_filename=None, callback=self.callback_stop)
		self.button_test = tetronGuiHelper.Button(text='Test', icon_filename=None, callback=self.callback_test)
		self.button_about = tetronGuiHelper.Button(text='About', icon_filename=None, callback=self.callback_about)
		# self.button_save = tetronGuiHelper.Button(text='Save', icon_filename='toolbar_save.png', callback=self.callback_save)
		# self.button_connect = tetronGuiHelper.Button(text='Connect', icon_filename='toolbar_connect.png', callback=self.callback_connect)
		# self.button_slice = tetronGuiHelper.Button(text='Slice', icon_filename='toolbar_slice.png', callback=self.callback_slice)
		# self.button_print = tetronGuiHelper.Button(text='Print', icon_filename='toolbar_print.png', callback=self.callback_print)
		# self.button_pause = tetronGuiHelper.Button(text='Pause', icon_filename='toolbar_pause.png', callback=self.callback_pause)
		# Set keyboard shortcuts.
		# self.button_pause.setShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL+QtCore.Qt.Key_P))
		# Add buttons to layout.
		layout.addWidget(self.button_settings)
		layout.addWidget(self.button_play)
		layout.addWidget(self.button_stop)
		layout.addWidget(self.button_test)
		layout.addWidget(self.button_about)
		# layout.addWidget(self.button_open)
		# layout.addWidget(self.button_save)
		# layout.addWidget(self.button_connect)
		# layout.addWidget(self.button_slice)
		# layout.addWidget(tetronGuiHelper.Divider('vertical'))
		# layout.addWidget(self.button_print)
		# layout.addWidget(self.button_pause)
		# layout.addWidget(self.button_stop)
		layout.addStretch(1)
		# Set initial states.
		# self.button_slice.setEnabled(False)
		# self.button_print.setEnabled(False)
		# self.button_pause.setEnabled(False)
		# self.button_stop.setEnabled(False)

		return layout

	# Start game.
	def callback_play(self):
		# Empty arrays.
		self.array_display[:] = 0
		self.array_current[:] = 0
		self.array_placed[:] = 0
		
		# Start timers.
		self.timer_check_queues.start()
		self.timer_advance.start()
		# Start the main thread.
		# self.main_thread = tetronSerial.MainThread(self.program_settings, self.queue_next, self.queue_hold, self.queue_status, self.queue_console)
		# self.main_thread.start()
		self.flag_playing = True

		# Create and override (if already existing) the main matrix widget.
		# self.widget_matrix = Matrix(self)
		# self.widget_matrix.resize()

		# Generate the next number of tetriminos.
		for i in range(self.program_settings['next_count'].get_value()):
			self.generate_next()
		
		# Create the first tetrimino.
		self.new_tetrimino()

	# Test function for debugging purposes. Delete later.
	def callback_test(self):
		w = self.widget_matrix.layout.itemAtPosition(2, 2).widget()
		w.hide()
		self.widget_matrix.layout.removeWidget(w)
		b = tetronGuiHelper.Block(3)
		self.widget_matrix.layout.addWidget(b, 2, 2)
	
	def callback_about(self):
		AboutWindow(self.program_settings, self.main_window)
	
	# Stop game.
	def callback_stop(self):
		# Stop timer.
		self.timer_advance.stop()
		# Update the GUI.
		self.queue_update_matrix.put(True)
		# Stop timers.  # Stopping these timers happens before the GUI gets to update, so it still displays the previous blocks shown.
		self.queue_stop.put(True)
	
	# Function that runs when the block fall speed setting is adjusted.
	def callback_speed(self):
		# Update the attribute.
		self.speed = 1000/self.program_settings['speed'].get_value()
		# Adjust the timer.
		self.timer_advance.setInterval(self.speed)
	
	# Update colors of blocks. Do not name 'update' to avoid overwriting.
	def update_blocks(self):
		for row in range(self.array_display.shape[0]):
			for column in range(self.array_display.shape[1]):
				if True: #self.array_display[row, column] != 0:  # Currently updating all blocks in matrix; only do ones needed to be updated
					# Get the current block to be removed.
					remove_block = self.widget_matrix.layout.itemAtPosition(row, column).widget()
					# Remove the block from display.
					remove_block.hide()
					# Delete the block.
					self.widget_matrix.layout.removeWidget(remove_block)
					# Create the new block and add it to the layout.
					block = tetronGuiHelper.Block(self.array_display[row, column])
					self.widget_matrix.layout.addWidget(block, row, column)

	# # Show file chooser window to load models.
	# def callback_open(self):
	# 	# Open a file chooser dialog.
	# 	fileChooser = QtGui.QFileDialog()
	# 	fileChooser.setFileMode(QtGui.QFileDialog.AnyFile)
	# 	fileChooser.setFilter('Stl files (*.stl)')
	# 	fileChooser.setWindowTitle('Open')
	# 	fileChooser.setDirectory(self.program_settings['currentFolder'].get_value())
	# 	filenames = QtCore.QStringList()
	# 	# exec_ returns True if OK, False if Cancel was clicked.
	# 	if fileChooser.exec_():
	# 		filepath = str(fileChooser.selectedFiles()[0])
	# 		# Check if file is an stl. If yes, load.
	# 		if filepath.lower()[-3:] != 'stl':
	# 			if self.console:
	# 				self.console.addLine('File "' + filepath + '" is not an stl file.')
	# 		else:
	# 			# Get the filename.
	# 			filename = filepath.split('/')[-1]
	# 			if self.console:
	# 				self.console.addLine('Loading file "' + filename + '".')
	# 			# Save path for next use.
	# 			self.program_settings['currentFolder'].set_value(filepath[:-len(filename)])
	# 			# Hide previous model's bounding box.
	# 			self.model_collection.get_current_model().hideBox()
	# 			# Load model into model collection. Returns ID for new model.
	# 			modelId = self.model_collection.add(filename, filepath)
	# 			# Add to model list.
	# 			self.tab1.list_view.add(modelId)
	# 			# Add actors to render view.
	# 			self.tab1.model_view.addActors(self.model_collection.get_all_actors_from_model())
	# 			# Update model view and update entries for the model.
	# 			self.tab1.model_view.render()
	# 			self.update_entries()
	# 			self.update_volume()
	
	# def callback_save(self):
	# 	pass

	# # Connect to or disconnect from printer.
	# def callback_connect(self):
	# 	if self.button_connect.text() == 'Connect':
	# 		# Update status label.
	# 		self.tab4.serial_label.setText('Connecting...')
	# 		self.tab4.serial_label.repaint()
			
	# 		# Attempt to create serial port.
	# 		self.printer.connect(self.program_settings['port'].get_value(), self.program_settings['baudrate'].get_value())

	# 		# If serial port is created...
	# 		if self.printer.printer:
	# 			# Update status label.
	# 			self.tab4.serial_label.setText('Connected on {} at {} baud.'.format(str(self.printer.port), str(self.printer.baud)))
	# 			# Update Connect button.
	# 			self.button_connect.setText('Disconnect')
	# 			self.button_connect.setIcon(QtGui.QIcon(self.program_settings['imagesDir'].get_value()+'/toolbar_disconnect.png'))
				
	# 			# Wait until the printer is online before sending commands.
	# 			while not self.printer.online:
	# 				continue
	# 			# Send G-code commands to initialize printer.
	# 			self.printer.send('G91')  # Set to relative positioning
	# 			self.printer.send('G1 F' + str(self.program_settings['controls_motor_speed'].get_value()))  # Set motor speed
	# 			self.printer.send('M17')  # Enable all stepper motors
	# 		# If serial port was not created...
	# 		else:
	# 			self.tab4.serial_label.setText('Printer not found on {}.'.format(self.program_settings['port'].get_value()))
	# 	elif self.button_connect.text() == 'Disconnect':
	# 		# Close serial port.
	# 		if self.printer.printer:
	# 			# Send G-code commands to shut down printer.
	# 			self.printer.send('M18')  # Disable all motors

	# 			# Disconnect printer.
	# 			self.printer.disconnect()
	# 			# Update status labels.
	# 			self.tab4.serial_label.setText('Not connected to printer.')
	# 			# Update button states.
	# 			self.button_print.setEnabled(False)
	# 			self.button_pause.setEnabled(False)
	# 			self.button_stop.setEnabled(False)
	# 			# Update Connect button.
	# 			self.button_connect.setText('Connect')
	# 			self.button_connect.setIcon(QtGui.QIcon(self.program_settings['imagesDir'].get_value()+'/toolbar_connect.png'))

	# # Slice all models in model view.
	# def callback_slice(self):
	# 	self.update_projector_settings()

	# 	# Calculate the memory (GB) required by the slice images. If the memory is high enough to potentially cause the computer to run out of memory, show a dialog asking whether or not to proceed with slicing.
	# 	if not self.program_settings['use_memory_efficient_slicing'].get_value():
	# 		slice_size = self.program_settings['slice_size'].get_value()
	# 		slice_memory = (slice_size[0] * slice_size[1] * 3 * self.model_collection.get_slice_count()) / 1e9
	# 		if slice_memory > 2:
	# 			reply = QtGui.QMessageBox.warning(self.main_window, 'Warning', 'The slice images will take up {0:.2f} GB of memory. It is recommended to turn on memory-efficient slicing in the settings. Do you want to continue with this setting off?'.format(slice_memory), QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
	# 			# Stop this function if No is selected.
	# 			if reply == QtGui.QMessageBox.No:
	# 				return
	# 	# Check if any model is out of bounds. Show a dialog asking whether or not to proceed with slicing.
	# 	bounds = self.model_collection.get_combined_bounds()
	# 	if bounds[0]<0 or bounds[1]>self.program_settings['print_size_x'].get_value() or bounds[2]<0 or bounds[3]>self.program_settings['print_size_y'].get_value() or bounds[4]<0 or bounds[5]>self.program_settings['print_size_z'].get_value():
	# 		reply = QtGui.QMessageBox.warning(self.main_window, 'Warning', 'One or more models are outside the print volume. Do you want to continue?', QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
	# 		# Stop this function if No is selected.
	# 		if reply == QtGui.QMessageBox.No:
	# 			return
		
	# 	# Start the slice thread.
	# 	self.timer_check_queues.start()
	# 	# self.slice_thread = theaterModelHandling.SliceThread(self.model_collection, self.program_settings, self.queue_slicing_index, self.queue_status, self.tab2.get_masks())
	# 	self.slice_thread.start()
	# 	self.flag_slicing = True
	# 	# Update status labels.
	# 	self.update_status_labels('slicing')
	# 	self.progress_bar.setMaximum(self.model_collection.get_slice_count())
	# 	self.progress_bar.setValue(0)
	# 	# Update button states.
	# 	self.button_stop.setEnabled(True)

	# # Show a Yes/No dialog window and start printing.
	# def callback_print(self):
	# 	reply = QtGui.QMessageBox.question(self.main_window, 'Start Print', 'Do you want to start the print?', QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
	# 	# Start printing.
	# 	if reply == QtGui.QMessageBox.Yes:
	# 		self.console.addLine('Starting print')
	# 		# Update status labels.
	# 		self.update_status_labels('printing')
	# 		self.progress_bar.setMaximum(self.model_collection.get_slice_count())
	# 		self.progress_bar.setValue(0)
			
	# 		# Create the projector windows.
	# 		self.create_projector_windows()
			
	# 		# Start the print thread.
	# 		self.timer_check_queues.start()
	# 		self.print_thread = tetronSerial.PrintThread(self.model_collection, self.program_settings, self.printer, self.queue_printing_index, self.queueSliceIn, self.queue_status, self.queue_console)
	# 		self.print_thread.start()
	# 		self.flag_playing = True
			
	# 		# Set button states.
	# 		self.button_print.setEnabled(False)
	# 		self.button_pause.setEnabled(True)
	# 		self.button_stop.setEnabled(True)
	
	# # Pause or resume printing.
	# def callback_pause(self):
	# 	# Pause printing.
	# 	if self.flag_playing:
	# 		self.print_thread.pause()
	# 		self.flag_playing = False
	# 		self.flag_paused = True
	# 		# Update button.
	# 		self.button_pause.setText('Resume')
	# 		self.button_pause.setIcon(QtGui.QIcon(self.program_settings['imagesDir'].get_value()+'/toolbar_print.png'))
	# 		# Update status labels.
	# 		self.update_status_labels('paused')
	# 	# Resume printing.
	# 	else:
	# 		self.print_thread.resume()
	# 		self.flag_playing = True
	# 		self.flag_paused = False
	# 		# Update button.
	# 		self.button_pause.setText('Pause')
	# 		self.button_pause.setIcon(QtGui.QIcon(self.program_settings['imagesDir'].get_value()+'/toolbar_pause.png'))
	# 		# Update status labels.
	# 		self.update_status_labels('printing')

	# Create and return a layout containing 2 status labels and a progress bar.
	def create_status_labels(self):
		# Create layout.
		layout = QtGui.QGridLayout()
		layout.setSpacing(0)

		# # Create a progress bar shown during long processes (e.g. slicing, printing).
		# self.progress_bar = tetronGuiHelper.ProgressBar()
		# layout.addWidget(self.progress_bar, 2, 1)
		# # Hide it initially.
		# self.progress_bar.hide()

		# Create the primary status label.
		self.status_label_1 = QtGui.QLabel('')
		self.status_label_1.setAlignment(QtCore.Qt.AlignRight)
		layout.addWidget(self.status_label_1, 0, 1)

		# Create the secondary status label, which is sometimes used to show detailed information.
		self.status_label_2 = QtGui.QLabel('')
		self.status_label_2.setAlignment(QtCore.Qt.AlignRight)
		self.status_label_2.setStyleSheet('color: rgb(0,0,0,38.2%)')
		layout.addWidget(self.status_label_2, 1, 1)

		# Set relative widths of widgets.
		layout.setColumnStretch(0, 1)
		layout.setColumnStretch(1, 1)

		return layout
	
	# Change the text shown in the status labels.
	def update_status_labels(self, status=''):
		status = status.lower()
		text_1 = ''
		text_2 = ''
		show_progress_bar = False

		# If no input was passed, update the status labels based on the values of the flags.
		if not status:
			if self.flag_slicing:
				status = 'slicing'
			elif self.flag_playing:
				status = 'printing'
			elif self.flag_paused:
				status = 'paused'
			else:
				status = ''
		
		# Status text related to supports.
		if status == 'supporting':
			text_1 = 'Generating Supports...'
			self.timer_check_queues.start()
		elif status == 'supported':
			self.update_volume()
			del self.tab1.supports_thread
			self.tab1.model_view.render()
			self.timer_check_queues.stop()
		# Status text related to slicing.
		elif status == 'slicing':
			text_1 = 'Slicing...'
			self.progress_bar.set_color('blue')
			show_progress_bar = True
		elif status == 'sliced':
			text_1 = 'Slicing Complete'
			self.update_print_time()
			text_2 = 'Print time: {}'.format(self.program_settings['print_time_formatted'].get_value())
			self.flag_slicing = False
			self.tab2.projector_viewer.update_slices()
			self.button_print.setEnabled(True)
			self.button_stop.setEnabled(False)
			self.timer_check_queues.stop()
		elif status == 'slice_stopped':
			text_1 = 'Slicing Stopped'
			self.progress_bar.set_color('red')
			show_progress_bar = True
			self.timer_check_queues.stop()
		# Status text related to printing.
		elif status == 'printing':
			text_1 = 'Printing...'
			self.progress_bar.set_color('blue')
			show_progress_bar = True
		elif status == 'printed':
			text_1 = 'Printing Complete'
			self.progress_bar.set_color('green')
			show_progress_bar = True
			self.flag_playing = False
			self.button_pause.setEnabled(False)
			self.button_stop.setEnabled(False)
			self.timer_check_queues.stop()
		elif status == 'paused':
			text_1 = 'Paused'
			self.progress_bar.set_color(75)
			show_progress_bar = True
		elif status == 'stopping':
			text_1 = 'Stopping...'
			self.progress_bar.set_color('red')
			show_progress_bar = True
		elif status == 'print_stopped':
			text_1 = 'Printing Stopped'
			self.progress_bar.set_color('red')
			show_progress_bar = True
			self.timer_check_queues.stop()
		
		# Update the text.
		self.status_label_1.setText(text_1.title())
		self.status_label_2.setText(text_2)
		# For some statuses, show the progress bar and hide the secondary status label.
		if show_progress_bar:
			self.status_label_2.hide()
			self.progress_bar.show()
		else:
			self.progress_bar.hide()
			self.status_label_2.show()


	# ==========================================================================
	# GUI update functions.
	# ==========================================================================

	# Calculate values for settings related to the projectors and update the corresponding labels.
	def update_projector_settings(self):
		# Calculate the slice size (height, width), in pixels, of all projectors combined and without overlap.
		if self.program_settings['projector_arrangement'].get_value() == 'horizontal':
			slice_size = [self.program_settings['projector_height'].get_value(), self.program_settings['projector_width'].get_value()*self.program_settings['projector_count'].get_value()]
		elif self.program_settings['projector_arrangement'].get_value() == 'vertical':
			slice_size = [self.program_settings['projector_height'].get_value()*self.program_settings['projector_count'].get_value(), self.program_settings['projector_width'].get_value()]
		
		# Calculate the XY resolution.
		if self.program_settings['slice_region'].get_value() == 'fill':
			resolution_xy = float(min(self.program_settings['print_size_x'].get_value(), self.program_settings['print_size_y'].get_value())) / float(min(slice_size))
		elif self.program_settings['slice_region'].get_value() == 'fit':
			resolution_xy = float(max(self.program_settings['print_size_x'].get_value(), self.program_settings['print_size_y'].get_value())) / float(max(slice_size))

		# Calculate the overlap, in pixels.
		projector_overlap_px = int(round(self.program_settings['projector_overlap'].get_value() / resolution_xy))

		# Calculate the slice size with overlap.
		if self.program_settings['projector_count'].get_value() > 1:
			if self.program_settings['projector_arrangement'].get_value() == 'horizontal':
				slice_size[1] -= projector_overlap_px
			elif self.program_settings['projector_arrangement'].get_value() == 'vertical':
				slice_size[0] -= projector_overlap_px

		# Calculate the print size in pixels.
		print_size_x_px = round(self.program_settings['print_size_x'].get_value() / resolution_xy)
		print_size_y_px = round(self.program_settings['print_size_y'].get_value() / resolution_xy)
		
		# Update settings.
		self.program_settings['resolution_xy'].set_value(resolution_xy)
		self.program_settings['projector_overlap_px'].set_value(projector_overlap_px)
		self.program_settings['slice_size'].set_value(slice_size)
		self.program_settings['print_size_x_px'].set_value(print_size_x_px)
		self.program_settings['print_size_y_px'].set_value(print_size_y_px)
		# Update labels.
		self.tab4.label_resolution_xy.update()
		self.tab2.label_projector_overlap_px.update()

	# Get volumes of the current model and all models and update the corresponding labels.
	def update_volume(self):
		model_settings = self.model_collection.get_current_model().model_settings
		model_size = self.model_collection.get_current_model().getSize()
		model_settings['size_x'].set_value(model_size[0])
		model_settings['size_y'].set_value(model_size[1])
		model_settings['size_z'].set_value(model_size[2])
		model_settings['volume'].set_value(self.model_collection.get_current_model().get_volume())
		self.program_settings['volume_total'].set_value(self.model_collection.get_total_volume())
		self.tab1.label_size_x.update()
		self.tab1.label_size_y.update()
		self.tab1.label_size_z.update()
		self.tab1.label_support_count.update()
		self.tab1.label_volume.update()
		self.tab1.label_volume_total.update()

	# Calculate the duration of the print and update the settings.
	def update_print_time(self):
		# Get the values of the relevant settings.
		slice_count = self.model_collection.get_slice_count()
		base_layer_count = self.program_settings['base_layer_count'].get_value()
		time_exposure_base = self.program_settings['exposure_time_base'].get_value()
		time_exposure = self.program_settings['exposure_time'].get_value()
		speed = self.program_settings['lift_speed'].get_value()
		distance_down = self.program_settings['lift_distance'].get_value()
		distance_up = self.program_settings['lift_distance'].get_value() - self.program_settings['layer_height'].get_value()

		# The time (s) it takes to expose all layers, including the base layers.
		time_exposure_total = base_layer_count * time_exposure_base + max(0, slice_count-base_layer_count) * time_exposure
		# The time (s) it takes the platform to move down and move up.
		time_platform = ((distance_down + distance_up) / speed) * 60
		# The time (s) it takes for the resin to become level.
		time_settling = self.program_settings['settling_time'].get_value()
		# The time (s) it takes for the entire print.
		time_print = slice_count*time_exposure_total + (slice_count-1)*(time_platform+time_settling)

		# Update the settings and the corresponding labels.
		self.program_settings['print_time'].set_value(time_print)
		self.program_settings['print_time_formatted'].set_value(time.strftime('%H:%M:%S', time.gmtime(time_print)))
		self.tab1.label_print_time.update()

	# Disable or enable all model-specific entries and update their values using the settings of the current model.
	def update_entries(self):
		if self.model_collection.has_models():
			self.tab1.model_list.setEnabled(True)
			self.tab1.tab_orientation.setEnabled(True)
			self.tab1.tab_supports.setEnabled(True)
			self.tab1.tab_details.setEnabled(True)
			self.button_slice.setEnabled(True)

			self.tab1.entry_position_x.update()
			self.tab1.entry_position_y.update()
			self.tab1.entry_position_z.update()
			self.tab1.entry_rotation_x.update()
			self.tab1.entry_rotation_y.update()
			self.tab1.entry_rotation_z.update()
			self.tab1.entry_scaling_x.update()
			self.tab1.entry_scaling_y.update()
			self.tab1.entry_scaling_z.update()
			self.tab1.entry_overhang_angle.update()
			self.tab1.entry_spacing_x.update()
			self.tab1.entry_spacing_y.update()
			self.tab1.entry_tip_diameter.update()
			self.tab1.entry_tip_height.update()
			self.tab1.entry_shaft_diameter.update()
			self.tab1.entry_base_diameter.update()
			self.tab1.entry_base_height.update()
			self.tab1.entry_maximum_height.update()
			self.tab1.label_size_x.update()
			self.tab1.label_size_y.update()
			self.tab1.label_size_z.update()
			self.tab1.label_volume.update()
			self.tab1.label_volume_total.update()
		else:
			self.tab1.model_list.setEnabled(False)
			self.tab1.tab_orientation.setEnabled(False)
			self.tab1.tab_supports.setEnabled(False)
			self.tab1.tab_details.setEnabled(False)
			self.button_slice.setEnabled(False)

	# Transform the current model.
	def update_current_model(self):
		self.model_collection.get_current_model().updateModel()

	# Transform all models.
	def update_all_models(self):
		self.model_collection.update_all_models()

	# Resize the print volume actor in the model view.
	def resize_print_volume(self):
		self.tab1.model_view.print_volume.setSize((self.program_settings['print_size_x'].value, self.program_settings['print_size_y'].value, self.program_settings['print_size_z'].value))


# Matrix widget.
class Matrix(QtGui.QWidget):
	def __init__(self, gui):
		super(Matrix, self).__init__()
		self.gui = gui

		# Set layout.
		self.layout = QtGui.QGridLayout()
		self.layout.setSpacing(0)
		self.setLayout(self.layout)

		# Get the numbers of rows and columns.
		self.row_count = self.gui.program_settings['row_count'].get_value()
		self.column_count = self.gui.program_settings['column_count'].get_value()

		# self.block_list = np.empty([self.row_count, self.column_count], dtype=object) #[[] for row in range(self.row_count) for column in range(self.column_count)]

		# Create and add all blocks to the layout.
		for row in range(self.row_count):
			for column in range(self.column_count):
				block = tetronGuiHelper.Block()
				self.layout.addWidget(block, row, column)
				# self.block_list[row, column] = block
		# self.resize()
	
	def resize(self):
		pass
	
	# Update colors of blocks. Do not name 'update' to avoid overwriting.
	def update_blocks(self, array):
		for row in range(array.shape[0]):
			for column in range(array.shape[1]):
				if array[row, column] != 0:
					remove_block = self.layout.itemAtPosition(row, column).widget()
					# Remove the block from view.
					remove_block.hide()
					# Delete the block.
					self.layout.removeWidget(remove_block)
					# Create the new block and add it to the layout.
					block = tetronGuiHelper.Block(array[row, column])
					self.layout.addWidget(block, row, column)
					# self.update()
				# self.block_list[row, column].set_color(array[row, column])
				# self.block_list[row, column].update()


# Tab 1 widget.
class Tab1(QtGui.QWidget):
	def __init__(self, gui):
		super(Tab1, self).__init__()
		self.gui = gui

		# Set layout.
		layout = QtGui.QGridLayout()
		self.setLayout(layout)
		
		# Create model view.
		self.model_view = theaterModelView.ModelView(self.gui.program_settings, self.gui.model_collection, self.gui)

		# Create model list.
		self.model_list = self.create_model_list()

		# Create a tab widget containing settings.
		model_options = tetronGuiHelper.Tab()
		self.tab_orientation = self.create_tab_orientation()
		self.tab_supports = self.create_tab_supports()
		self.tab_details = self.create_tab_details()
		model_options.addTab(self.tab_orientation, QtGui.QIcon(self.gui.program_settings['imagesDir'].get_value()+'/models_orientation.png'), 'Orientation')
		model_options.addTab(self.tab_supports, QtGui.QIcon(self.gui.program_settings['imagesDir'].get_value()+'/models_supports.png'), 'Supports')
		model_options.addTab(self.tab_details, QtGui.QIcon(self.gui.program_settings['imagesDir'].get_value()+'/models_details.png'), 'Details')
		
		# Add items to layout.
		layout.addWidget(self.model_view, 0, 0, 2, 1)
		layout.addWidget(self.model_list, 0, 1)
		layout.addWidget(model_options, 1, 1)
		# Set relative heights of rows.
		layout.setRowStretch(0, 1)
		layout.setRowStretch(1, 3)
		# Set relative widths of columns.
		layout.setColumnStretch(0, 7)
		layout.setColumnStretch(1, 2)
		# This must be called after inserting the widget.
		self.model_view.renderWindowInteractor.Initialize()

	# Create and return a widget containing a model list and buttons for managing models.
	def create_model_list(self):
		layout = QtGui.QVBoxLayout()
		layout.setContentsMargins(0,0,0,0)
		widget = QtGui.QWidget()
		widget.setLayout(layout)

		# Create the model list.
		self.list_view = tetronGuiHelper.ListView(self.callback_change_model)

		# Create buttons.
		button_duplicate = tetronGuiHelper.Button(text='Duplicate', icon_filename='models_duplicate.png', callback=self.callback_duplicate_model)
		button_remove = tetronGuiHelper.Button(text='Remove', icon_filename='models_remove.png', callback=self.callback_remove_model)
		# Create a layout for buttons.
		layout_buttons = QtGui.QHBoxLayout()
		layout_buttons.addStretch(1)
		layout_buttons.addWidget(button_duplicate)
		layout_buttons.addWidget(button_remove)
		layout_buttons.addStretch(1)

		# Add items.
		layout.addWidget(tetronGuiHelper.Header('Models'))
		layout.addWidget(self.list_view)
		layout.addLayout(layout_buttons)

		return widget
	
	# Create and return a widget containing model orientation settings.
	def create_tab_orientation(self):
		layout = QtGui.QVBoxLayout()
		widget = QtGui.QWidget()
		widget.setLayout(layout)

		# Create position entries.
		self.entry_position_x = tetronGuiHelper.EntrySpinBox('position_x', model_collection=self.gui.model_collection, callbacks=[self.gui.update_current_model, self.model_view.interactorStyle.updateWidgets, self.model_view.render, self.gui.update_volume, self.gui.update_entries])
		self.entry_position_y = tetronGuiHelper.EntrySpinBox('position_y', model_collection=self.gui.model_collection, callbacks=[self.gui.update_current_model, self.model_view.interactorStyle.updateWidgets, self.model_view.render, self.gui.update_volume, self.gui.update_entries])
		self.entry_position_z = tetronGuiHelper.EntrySpinBox('position_z', model_collection=self.gui.model_collection, callbacks=[self.gui.update_current_model, self.model_view.interactorStyle.updateWidgets, self.model_view.render, self.gui.update_volume, self.gui.update_entries])
		# Create a layout for position buttons.
		layout_position_buttons = QtGui.QHBoxLayout()
		button_center = tetronGuiHelper.Button(text='Center', icon_filename='models_center.png', callback=self.callback_center)
		button_platform = tetronGuiHelper.Button(text='On Platform', icon_filename='models_platform.png', callback=self.callback_platform)
		button_center.setToolTip('Center the model along X and Y inside the print volume.')
		button_platform.setToolTip('Set the Z position of the model to 0.')
		layout_position_buttons.addStretch(1)
		layout_position_buttons.addWidget(button_center)
		layout_position_buttons.addWidget(button_platform)
		layout_position_buttons.addStretch(1)
		
		# Create rotation entries.
		self.entry_rotation_x = tetronGuiHelper.EntrySpinBox('rotation_x', model_collection=self.gui.model_collection, callbacks=[self.gui.update_current_model, self.model_view.interactorStyle.updateWidgets, self.model_view.render, self.gui.update_volume, self.gui.update_entries])
		self.entry_rotation_y = tetronGuiHelper.EntrySpinBox('rotation_y', model_collection=self.gui.model_collection, callbacks=[self.gui.update_current_model, self.model_view.interactorStyle.updateWidgets, self.model_view.render, self.gui.update_volume, self.gui.update_entries])
		self.entry_rotation_z = tetronGuiHelper.EntrySpinBox('rotation_z', model_collection=self.gui.model_collection, callbacks=[self.gui.update_current_model, self.model_view.interactorStyle.updateWidgets, self.model_view.render, self.gui.update_volume, self.gui.update_entries])
		
		# Create scaling entries.
		self.entry_scaling_x = tetronGuiHelper.EntrySpinBox('scaling_x', model_collection=self.gui.model_collection, callbacks=[self.gui.update_current_model, self.model_view.interactorStyle.updateWidgets, self.model_view.render, self.gui.update_volume, self.gui.update_entries])
		self.entry_scaling_y = tetronGuiHelper.EntrySpinBox('scaling_y', model_collection=self.gui.model_collection, callbacks=[self.gui.update_current_model, self.model_view.interactorStyle.updateWidgets, self.model_view.render, self.gui.update_volume, self.gui.update_entries])
		self.entry_scaling_z = tetronGuiHelper.EntrySpinBox('scaling_z', model_collection=self.gui.model_collection, callbacks=[self.gui.update_current_model, self.model_view.interactorStyle.updateWidgets, self.model_view.render, self.gui.update_volume, self.gui.update_entries])
		self.checkbox_scale_xyz = tetronGuiHelper.Checkbox('scale_xyz', program_settings=self.gui.program_settings, callbacks=None)
		# Set a callback function to update all scaling settings when one is changed.
		self.entry_scaling_x.spin_box.valueChanged.connect(self.update_scale_xyz)
		self.entry_scaling_y.spin_box.valueChanged.connect(self.update_scale_xyz)
		self.entry_scaling_z.spin_box.valueChanged.connect(self.update_scale_xyz)

		# Add items to the layout.
		layout.addWidget(tetronGuiHelper.Header('Position'))
		layout.addWidget(self.entry_position_x)
		layout.addWidget(self.entry_position_y)
		layout.addWidget(self.entry_position_z)
		layout.addLayout(layout_position_buttons)
		layout.addWidget(tetronGuiHelper.Divider('horizontal'))
		layout.addWidget(tetronGuiHelper.Header('Rotation'))
		layout.addWidget(self.entry_rotation_x)
		layout.addWidget(self.entry_rotation_y)
		layout.addWidget(self.entry_rotation_z)
		layout.addWidget(tetronGuiHelper.Divider('horizontal'))
		layout.addWidget(tetronGuiHelper.Header('Scaling'))
		layout.addWidget(self.entry_scaling_x)
		layout.addWidget(self.entry_scaling_y)
		layout.addWidget(self.entry_scaling_z)
		layout.addWidget(self.checkbox_scale_xyz)
		layout.addStretch()

		return widget
	
	# Create and return a widget containing supports settings.
	def create_tab_supports(self):
		layout = QtGui.QVBoxLayout()
		widget = QtGui.QWidget()
		widget.setLayout(layout)

		# Create entries.
		self.entry_overhang_angle = tetronGuiHelper.EntrySpinBox('overhang_angle', model_collection=self.gui.model_collection)
		self.entry_spacing_x = tetronGuiHelper.EntrySpinBox('spacing_x', model_collection=self.gui.model_collection)
		self.entry_spacing_y = tetronGuiHelper.EntrySpinBox('spacing_y', model_collection=self.gui.model_collection)
		
		self.entry_tip_diameter = tetronGuiHelper.EntrySpinBox('tip_diameter', model_collection=self.gui.model_collection)
		self.entry_tip_height = tetronGuiHelper.EntrySpinBox('tip_height', model_collection=self.gui.model_collection)
		self.entry_shaft_diameter = tetronGuiHelper.EntrySpinBox('shaft_diameter', model_collection=self.gui.model_collection)
		self.entry_base_diameter = tetronGuiHelper.EntrySpinBox('base_diameter', model_collection=self.gui.model_collection)
		self.entry_base_height = tetronGuiHelper.EntrySpinBox('base_height', model_collection=self.gui.model_collection)
		self.entry_maximum_height = tetronGuiHelper.EntrySpinBox('maximum_height', model_collection=self.gui.model_collection)
		
		# Create layout for buttons that add and remove supports.
		layout_supports_buttons = QtGui.QHBoxLayout()
		# Create buttons that add and remove supports.
		button_add_supports = tetronGuiHelper.Button(text='Generate', callback=self.callback_add_supports)
		button_remove_supports = tetronGuiHelper.Button(text='Remove', callback=self.callback_remove_supports)
		layout_supports_buttons.addWidget(button_add_supports)
		layout_supports_buttons.addWidget(button_remove_supports)
		
		# Add items to the layout.
		layout.addWidget(self.entry_overhang_angle)
		layout.addWidget(self.entry_spacing_x)
		layout.addWidget(self.entry_spacing_y)
		layout.addWidget(tetronGuiHelper.Divider('horizontal'))
		layout.addWidget(self.entry_tip_diameter)
		layout.addWidget(self.entry_tip_height)
		layout.addWidget(self.entry_shaft_diameter)
		layout.addWidget(self.entry_base_diameter)
		layout.addWidget(self.entry_base_height)
		layout.addWidget(self.entry_maximum_height)
		layout.addWidget(tetronGuiHelper.Divider('horizontal'))
		layout.addLayout(layout_supports_buttons)
		layout.addStretch()

		return widget
	
	# Create and return a widget containing information about models.
	def create_tab_details(self):
		layout = QtGui.QVBoxLayout()
		widget = QtGui.QWidget()
		widget.setLayout(layout)

		# Create entries.
		self.label_size_x = tetronGuiHelper.SettingLabel('size_x', model_collection=self.gui.model_collection)
		self.label_size_y = tetronGuiHelper.SettingLabel('size_y', model_collection=self.gui.model_collection)
		self.label_size_z = tetronGuiHelper.SettingLabel('size_z', model_collection=self.gui.model_collection)
		self.label_support_count = tetronGuiHelper.SettingLabel('support_count', model_collection=self.gui.model_collection)
		self.label_volume = tetronGuiHelper.SettingLabel('volume', model_collection=self.gui.model_collection)

		self.label_volume_total = tetronGuiHelper.SettingLabel('volume_total', program_settings=self.gui.program_settings)
		self.label_print_time = tetronGuiHelper.SettingLabel('print_time_formatted', program_settings=self.gui.program_settings)

		# Add items to the layout.
		layout.addWidget(tetronGuiHelper.Header('Selected Model'))
		layout.addWidget(self.label_size_x)
		layout.addWidget(self.label_size_y)
		layout.addWidget(self.label_size_z)
		layout.addWidget(self.label_support_count)
		layout.addWidget(self.label_volume)
		layout.addWidget(tetronGuiHelper.Divider('horizontal'))
		layout.addWidget(tetronGuiHelper.Header('All Models'))
		layout.addWidget(self.label_volume_total)
		layout.addWidget(self.label_print_time)
		layout.addStretch(1)

		return widget
	
	# Change the current model.
	def callback_change_model(self):
		# Hide the bounding box of the previous model.
		self.gui.model_collection.get_current_model().hideBox()
		
		# Change the current model.
		model_string = self.list_view.get_selected_string()
		self.gui.model_collection.set_current_id(model_string)
		self.model_view.interactorStyle.updateWidgets()
		# Show the bounding box of the new model.
		self.gui.model_collection.get_current_model().showBox()

		# Update the model view and the entries related to the model.
		self.model_view.render()
		self.gui.update_entries()

	# Duplicate the current model.
	def callback_duplicate_model(self):
		pass

	# Remove the current model.
	def callback_remove_model(self):
		# Get the currently selected string in the model list.
		model_string = self.list_view.get_selected_string()
		# Remove the currently selected string from the model list.
		self.list_view.remove()
		# Remove the actors belonging to the model from the model view.
		self.model_view.removeActors(self.gui.model_collection.get_all_actors_from_model(model_string))
		# Remove the model from the model collection.
		self.gui.model_collection.remove(model_string)
		# Update the model view.
		self.model_view.render()
		# Update the entries in the GUI.
		self.gui.update_volume()
		self.gui.update_entries()

	# Center the current model within the X and Y bounds of the print volume.
	def callback_center(self):
		model_settings = self.gui.model_collection.get_current_model().model_settings
		model_settings['position_x'].set_value(self.gui.program_settings['print_size_x'].get_value()/2.0)
		model_settings['position_y'].set_value(self.gui.program_settings['print_size_y'].get_value()/2.0)
		self.gui.model_collection.get_current_model().updateModel()
		self.gui.update_entries()
		self.model_view.interactorStyle.updateWidgets()
		self.model_view.render()
	
	# Place the current model on the platform.
	def callback_platform(self):
		self.gui.model_collection.get_current_model().model_settings['position_z'].set_value(0)
		self.gui.model_collection.get_current_model().updateModel()
		self.gui.update_entries()
		self.model_view.interactorStyle.updateWidgets()
		self.model_view.render()
	
	# Update all scaling settings when one scaling entry is changed.
	def update_scale_xyz(self, text):
		if self.gui.program_settings['scale_xyz'].get_value():
			model_settings = self.gui.model_collection.get_current_model().model_settings
			model_settings['scaling_x'].set_value(float(text))
			model_settings['scaling_y'].set_value(float(text))
			model_settings['scaling_z'].set_value(float(text))

	# Start a thread to generate supports.
	def callback_add_supports(self):
		model = self.gui.model_collection.get_current_model()
		model.update_normals()
		self.gui.update_status_labels('supporting')
		self.supports_thread = theaterModelHandling.SupportsThread(model.model_settings, self.gui.program_settings, model.overhangClipFilter.GetOutput(), model.getBoundsOverhang(), self.gui.queue_supports, self.gui.queue_status)
		self.supports_thread.start()

	# Remove supports.
	def callback_remove_supports(self):
		self.gui.model_collection.get_current_model().remove_supports()
		self.gui.update_volume()


# # Tab 2 widget.
# class Tab2(QtGui.QWidget):
# 	def __init__(self, gui):
# 		super(Tab2, self).__init__()
# 		self.gui = gui

# 		# Set layout.
# 		layout = QtGui.QGridLayout()
# 		layout.setAlignment(QtCore.Qt.AlignTop)
# 		self.setLayout(layout)

# 		# Create a tab widget containing settings.
# 		projector_options = tetronGuiHelper.Tab()
# 		self.tab_arrangement = self.create_tab_arrangement()
# 		self.tab_masks = self.create_tab_masks()
# 		projector_options.addTab(self.tab_arrangement, QtGui.QIcon(self.gui.program_settings['imagesDir'].get_value()+'/projectors_arrangement.png'), 'Arrangement')
# 		projector_options.addTab(self.tab_masks, QtGui.QIcon(self.gui.program_settings['imagesDir'].get_value()+'/projectors_masks.png'), 'Masks')

# 		# Create a projector viewer.
# 		self.projector_viewer = tetronGuiHelper.ProjectorViewer(self.gui.program_settings, self.gui.model_collection)

# 		# Add items to layout.
# 		layout.addLayout(self.projector_viewer, 0, 0, 2, 1)
# 		layout.addWidget(self.create_projector_list(), 0, 1)
# 		layout.addWidget(projector_options, 1, 1)
# 		# Set relative heights of rows.
# 		layout.setRowStretch(0, 1)
# 		layout.setRowStretch(1, 3)
# 		# Set relative widths of columns.
# 		layout.setColumnStretch(0, 7)
# 		layout.setColumnStretch(1, 2)

# 		# Brainstorm: All settings that need to be in this tab?
# 		#	vertical vs horizontal
# 		# 	buttons for showing/closing windows
# 		#   load a mask PNG file
# 		# 	set overlap between 2
# 		#	mirror (flip) projectors
	
# 	# Create and return a list containing available displays and their resolutions.
# 	def create_projector_list(self):
# 		# need library "wmi" to detect connected devices: https://stackoverflow.com/questions/22621017/find-and-identify-multiple-display-devices-monitors-using-python/43132744
		
# 		widget = QtGui.QListWidget()

# 		return widget
	
# 	# Create and return a widget containing options for projector arrangement.
# 	def create_tab_arrangement(self):
# 		layout = QtGui.QVBoxLayout()
# 		widget = QtGui.QWidget()
# 		widget.setLayout(layout)

# 		# Create arrangement settings.
# 		popup_number = tetronGuiHelper.EntryPopup('projector_count', self.gui.program_settings, editable=False, callbacks=[self.gui.update_projector_settings])
# 		popup_arrangement = tetronGuiHelper.EntryPopup('projector_arrangement', self.gui.program_settings, editable=False, callbacks=[self.gui.update_projector_settings])
		
# 		# Create overlap settings.
# 		self.entry_projector_overlap = tetronGuiHelper.EntrySpinBox('projector_overlap', program_settings=self.gui.program_settings, callbacks=[self.gui.update_projector_settings])
# 		self.label_projector_overlap_px = tetronGuiHelper.SettingLabel('projector_overlap_px', self.gui.program_settings)

# 		# Add settings, and add headers and dividers to separate them.
# 		layout.addWidget(popup_number)
# 		layout.addWidget(popup_arrangement)
# 		layout.addWidget(tetronGuiHelper.Divider())
# 		layout.addWidget(self.entry_projector_overlap)
# 		layout.addWidget(self.label_projector_overlap_px)
# 		# Add empty space at bottom.
# 		layout.addStretch()

# 		return widget

# 	# Create and return a widget containing options for masks.
# 	def create_tab_masks(self):
# 		layout = QtGui.QVBoxLayout()
# 		widget = QtGui.QWidget()
# 		widget.setLayout(layout)

# 		# Create a checkbox to indicate whether or not to use different masks for each projector.
# 		self.checkbox_separate_masks = tetronGuiHelper.Checkbox('use_separate_masks', self.gui.program_settings)
# 		self.checkbox_separate_masks.stateChanged.connect(self.callback_separate_masks)

# 		# Create an image preview shown when the checkbox is unchecked.
# 		self.mask_preview_single = tetronGuiHelper.ImageLoader()

# 		# Create image previews shown for each projector when the checkbox is checked.
# 		self.mask_preview_1 = tetronGuiHelper.ImageLoader('Projector 1')
# 		self.mask_preview_2 = tetronGuiHelper.ImageLoader('Projector 2')
# 		# Create a divider.
# 		self.divider = tetronGuiHelper.Divider('horizontal')
		
# 		# Add settings.
# 		layout.addWidget(self.checkbox_separate_masks)
# 		layout.addWidget(self.mask_preview_single)
# 		layout.addWidget(self.mask_preview_1)
# 		layout.addWidget(self.divider)
# 		layout.addWidget(self.mask_preview_2)
# 		# Add empty space at bottom.
# 		layout.addStretch()
# 		# Set the initial appearance.
# 		self.callback_separate_masks(self.checkbox_separate_masks.checkState())

# 		return widget
	
# 	# Show a single mask preview or show multiple mask previews for each projector.
# 	def callback_separate_masks(self, state=None):
# 		if state == 0:
# 			self.mask_preview_single.show()
# 			self.mask_preview_1.hide()
# 			self.divider.hide()
# 			self.mask_preview_2.hide()
# 		elif state == 2:
# 			self.mask_preview_single.hide()
# 			self.mask_preview_1.show()
# 			self.divider.show()
# 			self.mask_preview_2.show()
	
# 	# Return a list of the masks being shown in the Masks tab.
# 	def get_masks(self):
# 		image_list = []
# 		if self.checkbox_separate_masks.isChecked():
# 			mask_1 = self.mask_preview_1.label.pixmap()
# 			mask_2 = self.mask_preview_2.label.pixmap()
# 			if mask_1:
# 				image_list.append(mask_1)
# 			if mask_2:
# 				image_list.append(mask_2)
# 		else:
# 			mask = self.mask_preview_single.label.pixmap()
# 			if mask:
# 				image_list.append(mask)
			
# 		return image_list


# # Tab 3 widget.
# class Tab3(QtGui.QWidget):
# 	def __init__(self, gui):
# 		super(Tab3, self).__init__()
# 		self.gui = gui

# 		# Set layout.
# 		layout = QtGui.QGridLayout()
# 		self.setLayout(layout)
		
# 		# Add items to the layout.
# 		layout.addWidget(self.create_frame_motor(), 0, 0)
# 		layout.addWidget(self.create_frame_projector(), 0, 1)
# 		layout.addWidget(self.create_frame_gcode(), 1, 0)
# 		# Add empty space at bottom and right.
# 		layout.setRowStretch(2, 1)
# 		layout.setColumnStretch(2, 1)
	
# 	# Create and return a QGroupBox.
# 	def create_frame_motor(self):
# 		layout = QtGui.QVBoxLayout()
# 		frame = tetronGuiHelper.Frame('Motor')
# 		frame.setLayout(layout)

# 		# Define the available distances that can be used.
# 		self.distances = [0.1, 1, 5, 10, 50]

# 		# Create buttons for moving motors.
# 		button_up = tetronGuiHelper.Button(icon_filename='controls_up.png', callback=self.callback_motor_up)
# 		button_down = tetronGuiHelper.Button(icon_filename='controls_down.png', callback=self.callback_motor_down)
# 		# Set shortcuts.
# 		button_up.setShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL+QtCore.Qt.Key_Up))
# 		button_down.setShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL+QtCore.Qt.Key_Down))
# 		# Set tooltips.
# 		button_up.setToolTip('Move platform up by selected distance.')
# 		button_down.setToolTip('Move platform down by selected distance.')
		
# 		# Create buttons for selecting movement distances.
# 		button_distance_1 = tetronGuiHelper.Button(text=str(self.distances[0]) + ' mm')
# 		button_distance_2 = tetronGuiHelper.Button(text=str(self.distances[1]) + ' mm')
# 		button_distance_3 = tetronGuiHelper.Button(text=str(self.distances[2]) + ' mm')
# 		button_distance_4 = tetronGuiHelper.Button(text=str(self.distances[3]) + ' mm')
# 		button_distance_5 = tetronGuiHelper.Button(text=str(self.distances[4]) + ' mm')
# 		# Set buttons to be checkable.
# 		button_distance_1.setCheckable(True)
# 		button_distance_2.setCheckable(True)
# 		button_distance_3.setCheckable(True)
# 		button_distance_4.setCheckable(True)
# 		button_distance_5.setCheckable(True)
# 		# Set one button to be initally checked.
# 		button_distance_1.setChecked(True)
# 		# Create a button group for the distance buttons that only allows one of them to be checked at a time.
# 		self.button_group = QtGui.QButtonGroup()
# 		self.button_group.addButton(button_distance_1, 1)
# 		self.button_group.addButton(button_distance_2, 2)
# 		self.button_group.addButton(button_distance_3, 3)
# 		self.button_group.addButton(button_distance_4, 4)
# 		self.button_group.addButton(button_distance_5, 5)
# 		# Create a layout for the buttons.
# 		layout_distance = QtGui.QHBoxLayout()
# 		layout_distance.addWidget(button_distance_1)
# 		layout_distance.addWidget(button_distance_2)
# 		layout_distance.addWidget(button_distance_3)
# 		layout_distance.addWidget(button_distance_4)
# 		layout_distance.addWidget(button_distance_5)

# 		# Create entry for motor speed.
# 		entry_motor_speed = tetronGuiHelper.EntrySpinBox('controls_motor_speed', program_settings=self.gui.program_settings, callbacks=[self.callback_motor_speed])
# 		# Set tooltip.
# 		entry_motor_speed.setToolTip('Set the motor speed, in mm/min.')

# 		# Create buttons for turning motors on and off.
# 		button_on = tetronGuiHelper.Button(icon_filename='controls_on.png', callback=self.callback_motor_on)
# 		button_off = tetronGuiHelper.Button(icon_filename='controls_off.png', callback=self.callback_motor_off)
# 		button_stop = tetronGuiHelper.Button(icon_filename='controls_stop.png', callback=self.callback_motor_stop, color='red')
# 		# Set tooltips.
# 		button_on.setToolTip('Enable all stepper motors.')
# 		button_off.setToolTip('Disable all stepper motors.')
# 		button_stop.setToolTip('Stop all motors immediately.\nWarning: The printer must be disconnected and re-connected before it can operate again.')
# 		# Create a layout for the buttons.
# 		layout_power = QtGui.QHBoxLayout()
# 		layout_power.addStretch(1)
# 		layout_power.addWidget(button_on)
# 		layout_power.addWidget(button_off)
# 		layout_power.addWidget(button_stop)
# 		layout_power.addStretch(1)

# 		# Add items to layout.
# 		layout.addWidget(button_up)
# 		layout.addLayout(layout_distance)
# 		layout.addWidget(button_down)
# 		layout.addWidget(entry_motor_speed)
# 		layout.addWidget(tetronGuiHelper.Divider('horizontal'))
# 		layout.addLayout(layout_power)
# 		layout.addStretch(1)
		
# 		return frame

# 	# Send a G-code command to move the platform up.
# 	def callback_motor_up(self):
# 		if self.gui.printer.printer:
# 			speed = self.gui.program_settings['controls_motor_speed'].get_value()
# 			distance = self.distances[self.button_group.checkedId()-1]
# 			code = 'G1 F{} Z{}'.format(str(speed), str(distance))
# 			self.gui.printer.send(code)
# 			self.gcode_browser.append('Sending: ' + code)

# 	# Send a G-code command to move the platform down.
# 	def callback_motor_down(self):
# 		if self.gui.printer.printer:
# 			speed = self.gui.program_settings['controls_motor_speed'].get_value()
# 			distance = -self.distances[self.button_group.checkedId()-1]
# 			code = 'G1 F{} Z{}'.format(str(speed), str(distance))
# 			self.gui.printer.send(code)
# 			self.gcode_browser.append('Sending: ' + code)

# 	# Send a G-code command to set a new motor speed.
# 	def callback_motor_speed(self):
# 		if self.gui.printer.printer:
# 			speed = self.gui.program_settings['controls_motor_speed'].get_value()
# 			code = 'G1 F{}'.format(str(speed))
# 			self.gui.printer.send(code)
# 			self.gcode_browser.append('Sending: ' + code)
	
# 	# Send a G-code command to turn on all motors.
# 	def callback_motor_on(self):
# 		if self.gui.printer.printer:
# 			code = 'M17'
# 			self.gui.printer.send(code)
# 			self.gcode_browser.append('Sending: ' + code)

# 	# Send a G-code command to turn off all motors.
# 	def callback_motor_off(self):
# 		if self.gui.printer.printer:
# 			code = 'M18'
# 			self.gui.printer.send(code)
# 			self.gcode_browser.append('Sending: ' + code)
	
# 	# Send a G-code command to immediately stop all motors.
# 	def callback_motor_stop(self):
# 		if self.gui.printer.printer:
# 			code = 'M112'
# 			self.gui.printer.send(code)
# 			self.gcode_browser.append('Sending: ' + code)

# 			# Stop a print process if it is occuring.
# 			if self.gui.flag_playing:
# 				self.gui.print_thread.stop()
# 				self.gui.flag_playing = False

# 	# Create and return a QGroupBox.
# 	def create_frame_projector(self):
# 		layout = QtGui.QVBoxLayout()
# 		frame = tetronGuiHelper.Frame('Projector')
# 		frame.setLayout(layout)

# 		# Create buttons.
# 		button_blank = tetronGuiHelper.Button(text='Blank', icon_filename='controls_blank.png', callback=self.callback_projector_blank)
# 		button_border = tetronGuiHelper.Button(text='Border', icon_filename='controls_border.png', callback=self.callback_projector_border)
# 		button_grid = tetronGuiHelper.Button(text='Grid', icon_filename='controls_grid.png', callback=self.callback_projector_grid)
# 		button_minimize = tetronGuiHelper.Button(text='Minimize', icon_filename='controls_minimize.png', callback=self.gui.minimize_projector_windows)
# 		button_show = tetronGuiHelper.Button(text='Show', icon_filename='controls_show.png', callback=self.gui.create_projector_windows)
# 		button_close = tetronGuiHelper.Button(text='Close', icon_filename='controls_close.png', callback=self.gui.close_projector_windows)
# 		# Set shortcuts.
# 		button_blank.setShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL+QtCore.Qt.Key_N))
# 		button_border.setShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL+QtCore.Qt.Key_B))
# 		# Create layouts for some buttons.
# 		layout_window_buttons = QtGui.QHBoxLayout()
# 		layout_window_buttons.addStretch(1)
# 		layout_window_buttons.addWidget(button_minimize)
# 		layout_window_buttons.addWidget(button_show)
# 		layout_window_buttons.addWidget(button_close)
# 		layout_window_buttons.addStretch(1)
		
# 		# Create entries.
# 		entry_grid_spacing = tetronGuiHelper.EntrySpinBox('controls_projector_grid_spacing', program_settings=self.gui.program_settings, callbacks=self.callback_projector_grid_spacing)
# 		entry_projector_position_x = tetronGuiHelper.EntrySpinBox('projector_position_x', program_settings=self.gui.program_settings, callbacks=self.callback_projector_position)
# 		entry_projector_position_y = tetronGuiHelper.EntrySpinBox('projector_position_y', program_settings=self.gui.program_settings, callbacks=self.callback_projector_position)
		
# 		# Add items to layout.
# 		layout.addWidget(button_blank)
# 		layout.addWidget(button_border)
# 		layout.addWidget(button_grid)
# 		layout.addWidget(entry_grid_spacing)
# 		layout.addWidget(entry_projector_position_x)
# 		layout.addWidget(entry_projector_position_y)
# 		layout.addWidget(tetronGuiHelper.Divider('horizontal'))
# 		layout.addLayout(layout_window_buttons)
# 		layout.addStretch(1)

# 		return frame
	
# 	# Show black images in each projector window.
# 	def callback_projector_blank(self):
# 		self.gui.create_projector_windows()
# 		for projector_index in self.gui.projector_windows:
# 			self.gui.projector_windows[projector_index].image.set_image_blank()

# 	# Show images with grids in each projector window.
# 	def callback_projector_grid(self):
# 		self.gui.create_projector_windows()
# 		for projector_index in self.gui.projector_windows:
# 			self.gui.projector_windows[projector_index].image.set_image_grid()

# 	# Show images with a border along their perimeters in each projector window.
# 	def callback_projector_border(self):
# 		self.gui.create_projector_windows()
# 		for projector_index in self.gui.projector_windows:
# 			self.gui.projector_windows[projector_index].image.set_image_border()

# 	# Adjust the grid spacing of the grid image shown in each projector window.
# 	def callback_projector_grid_spacing(self):
# 		for projector_index in self.gui.projector_windows:
# 			self.gui.projector_windows[projector_index].image.set_image_grid()

# 	# Adjust the positions of each projector window.
# 	def callback_projector_position(self):
# 		for projector_index in self.gui.projector_windows:
# 			self.gui.projector_windows[projector_index].set_window_position()

# 	# Create and return a QGroupBox.
# 	def create_frame_gcode(self):
# 		layout = QtGui.QVBoxLayout()
# 		frame = tetronGuiHelper.Frame('G-Code')
# 		frame.setLayout(layout)

# 		# Create a widget for typing and sending G-code commands, consisting of a text editor and a send button.
# 		self.gcode_text = QtGui.QLineEdit()
# 		self.gcode_text.setPlaceholderText('Type G-code command...')
# 		self.gcode_text.returnPressed.connect(self.callback_gcode_send)
# 		button_send = tetronGuiHelper.Button(text='Send', callback=self.callback_gcode_send)
		
# 		layout_send = QtGui.QHBoxLayout()
# 		layout_send.addWidget(self.gcode_text)
# 		layout_send.addWidget(button_send)

# 		# Create a widget for displaying sent G-code commands and printer responses.
# 		self.gcode_browser = QtGui.QTextBrowser()
		
# 		# Add items to layout.
# 		layout.addLayout(layout_send)
# 		layout.addWidget(self.gcode_browser)
# 		layout.addStretch(1)

# 		return frame
	
# 	# Send a G-code command typed in the text editor.
# 	def callback_gcode_send(self):
# 		if self.gui.printer.printer:
# 			code = str(self.gcode_text.text())
# 			self.gui.printer.send(code)
# 			self.gcode_browser.append('Sending: ' + code)


# # Tab 4 widget.
# class Tab4(QtGui.QWidget):
# 	def __init__(self, gui):
# 		super(Tab4, self).__init__()
# 		self.gui = gui

# 		# Set layout.
# 		layout = QtGui.QGridLayout()
# 		self.setLayout(layout)
		
# 		"""  # Outdated variable names
# 		# Make the tab scrollable.
# 		self.scrollArea = QtGui.QScrollArea()
# 		self.scrollArea.setWidgetResizable(True)
# 		self.scrollArea.setWidget(self.widgetTab4)
# 		self.widgetTab.addTab(self.scrollArea, 'Settings')  # Adding widgetTab4 to widgetTab must be deleted if this line is used
# 		"""

# 		# Create a layout containing settings.
# 		layout_settings = QtGui.QGridLayout()
# 		layout_settings.addWidget(self.create_frame_dimensions(), 0, 0)
# 		layout_settings.addWidget(self.create_frame_communications(), 0, 1)
# 		layout_settings.addWidget(self.create_frame_slicing(), 1, 0)
# 		layout_settings.addWidget(self.create_frame_printing(), 1, 1)
# 		# Add empty space at bottom and right.
# 		layout_settings.setRowStretch(3, 1)
# 		layout_settings.setColumnStretch(2, 1)

# 		# Create text browser for console outputs.
# 		self.console_browser = tetronGuiHelper.ConsoleBrowser(self.gui.console)
		
# 		# Add items to layout.
# 		layout.addLayout(layout_settings, 0, 0)
# 		layout.addWidget(self.console_browser, 0, 1)
# 		# Set relative widths of columns.
# 		layout.setColumnStretch(0, 7)
# 		layout.setColumnStretch(1, 2)
	
# 	# Create and return a QGroupBox.
# 	def create_frame_dimensions(self):
# 		# Create frame and set layout.
# 		layout = QtGui.QVBoxLayout()
# 		frame = tetronGuiHelper.Frame('Dimensions')
# 		frame.setLayout(layout)

# 		# Create entries.
# 		self.entry_print_size_x = tetronGuiHelper.EntrySpinBox('print_size_x', program_settings=self.gui.program_settings, callbacks=[self.gui.resize_print_volume, self.gui.update_projector_settings])
# 		self.entry_print_size_y = tetronGuiHelper.EntrySpinBox('print_size_y', program_settings=self.gui.program_settings, callbacks=[self.gui.resize_print_volume, self.gui.update_projector_settings])
# 		self.entry_print_size_z = tetronGuiHelper.EntrySpinBox('print_size_z', program_settings=self.gui.program_settings, callbacks=[self.gui.resize_print_volume, self.gui.update_projector_settings])
# 		self.entry_projector_height = tetronGuiHelper.EntrySpinBox('projector_height', program_settings=self.gui.program_settings, callbacks=[self.gui.update_all_models, self.gui.update_projector_settings])
# 		self.entry_projector_width = tetronGuiHelper.EntrySpinBox('projector_width', program_settings=self.gui.program_settings, callbacks=[self.gui.update_all_models, self.gui.update_projector_settings])
		
# 		# Create a label to show the XY print resolution calculated from the print size, projector size, and projector arrangement.
# 		self.label_resolution_xy = tetronGuiHelper.SettingLabel('resolution_xy', self.gui.program_settings)
		
# 		# Add items to layout.
# 		layout.addWidget(self.entry_print_size_x)
# 		layout.addWidget(self.entry_print_size_y)
# 		layout.addWidget(self.entry_print_size_z)
# 		layout.addWidget(self.entry_projector_height)
# 		layout.addWidget(self.entry_projector_width)
# 		layout.addWidget(self.label_resolution_xy)
# 		layout.addStretch(1)

# 		return frame

# 	# Create and return a QGroupBox.
# 	def create_frame_communications(self):
# 		# Create frame and set layout.
# 		layout = QtGui.QVBoxLayout()
# 		frame = tetronGuiHelper.Frame('Communications')
# 		frame.setLayout(layout)
		
# 		# Create entries.
# 		self.entry_port = tetronGuiHelper.Entry('port', program_settings=self.gui.program_settings)
# 		self.entry_baudrate = tetronGuiHelper.EntryPopup('baudrate', self.gui.program_settings)
# 		self.checkbox_use_projector_serial = tetronGuiHelper.Checkbox('use_projector_serial', program_settings=self.gui.program_settings)
# 		self.entry_port_projector = tetronGuiHelper.Entry('port_projector', program_settings=self.gui.program_settings)
# 		self.entry_baudrate_projector = tetronGuiHelper.Entry('baudrate_projector', program_settings=self.gui.program_settings)
# 		self.entry_projector_on_command = tetronGuiHelper.Entry('projector_on_command', self.gui.program_settings)
# 		self.entry_projector_off_command = tetronGuiHelper.Entry('projector_off_command', self.gui.program_settings)

# 		# Create a label to show the status of the serial connection.
# 		self.serial_label = tetronGuiHelper.SmallLabel('Not connected to printer.')
		
# 		# Add items to layout.
# 		layout.addWidget(self.entry_port)
# 		layout.addWidget(self.entry_baudrate)
# 		layout.addWidget(self.serial_label)
# 		# layout.addWidget(tetronGuiHelper.Divider('horizontal'))
# 		# layout.addWidget(self.checkbox_use_projector_serial)
# 		# layout.addWidget(self.entry_port_projector)
# 		# layout.addWidget(self.entry_baudrate_projector)
# 		# layout.addWidget(self.entry_projector_on_command)
# 		# layout.addWidget(self.entry_projector_off_command)
# 		layout.addStretch(1)

# 		return frame

# 	# Create and return a QGroupBox.
# 	def create_frame_slicing(self):
# 		layout = QtGui.QVBoxLayout()
# 		frame = tetronGuiHelper.Frame('Slicing')
# 		frame.setLayout(layout)

# 		# Create entries.
# 		self.entry_layer_height = tetronGuiHelper.EntrySpinBox('layer_height', program_settings=self.gui.program_settings)
# 		self.checkbox_has_multiple_bodies = tetronGuiHelper.Checkbox('has_multiple_bodies', program_settings=self.gui.program_settings, callbacks=[self.gui.update_all_models])
# 		self.checkbox_use_memory_efficient_slicing = tetronGuiHelper.Checkbox('use_memory_efficient_slicing', program_settings=self.gui.program_settings, callbacks=None)
# 		self.popup_slice_region = tetronGuiHelper.EntryPopup('slice_region', program_settings=self.gui.program_settings, editable=False)
# 		# Set tooltips.
# 		self.popup_slice_region.setToolTip('Fill: Fill the slice image with the print area. Some parts of the print area may be outside the slice image.\nFit: Show the entire print area inside the slice image.')
		
# 		# Add items.
# 		layout.addWidget(self.entry_layer_height)
# 		layout.addWidget(self.checkbox_has_multiple_bodies)
# 		layout.addWidget(self.checkbox_use_memory_efficient_slicing)
# 		layout.addWidget(self.popup_slice_region)
# 		layout.addStretch(1)

# 		return frame

# 	# Create and return a QGroupBox.
# 	def create_frame_printing(self):
# 		layout = QtGui.QVBoxLayout()
# 		frame = tetronGuiHelper.Frame('Printing')
# 		frame.setLayout(layout)

# 		# Create entries.
# 		self.entry_exposure_time = tetronGuiHelper.EntrySpinBox('exposure_time', program_settings=self.gui.program_settings)
# 		self.entry_exposure_time_base = tetronGuiHelper.EntrySpinBox('exposure_time_base', program_settings=self.gui.program_settings)
# 		self.entry_base_layer_count = tetronGuiHelper.EntrySpinBox('base_layer_count', program_settings=self.gui.program_settings)
# 		self.entry_lift_distance = tetronGuiHelper.EntrySpinBox('lift_distance', program_settings=self.gui.program_settings)
# 		self.entry_lift_speed = tetronGuiHelper.EntrySpinBox('lift_speed', program_settings=self.gui.program_settings)
# 		self.entry_settling_time = tetronGuiHelper.EntrySpinBox('settling_time', program_settings=self.gui.program_settings)

# 		# Add items.
# 		layout.addWidget(self.entry_exposure_time)
# 		layout.addWidget(self.entry_exposure_time_base)
# 		layout.addWidget(self.entry_base_layer_count)
# 		layout.addWidget(self.entry_lift_distance)
# 		layout.addWidget(self.entry_lift_speed)
# 		layout.addWidget(self.entry_settling_time)
# 		layout.addStretch(1)

# 		return frame


# Main window of the program.
class MainWindow(QtGui.QMainWindow):
	def __init__(self, gui, program_settings):
		QtGui.QMainWindow.__init__(self)
		self.gui = gui

		# Set window title.
		self.setWindowTitle(program_settings['program_name'].get_value() + ' ' + program_settings['version_number'].get_value())
		# # Set window icon.
		# self.setWindowIcon(QtGui.QIcon(program_settings['installDir'].get_value()+'/logo.png'))

	# # Show a confirmation dialog when the user tries to close the window.
	# # This method overrides the close event of the parent class.
	# def closeEvent(self, event):
	# 	if self.gui.model_collection.has_models():
	# 		if self.gui.flag_playing:
	# 			result = QtGui.QMessageBox.information(self, 'Print in Progress', 'You cannot exit while a print is running.', QtGui.QMessageBox.Ok)
	# 		else:
	# 			result = QtGui.QMessageBox.question(self, 'Exit', 'Are you sure you want to exit?', QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
	# 		if result == QtGui.QMessageBox.Yes:
	# 			self.gui.close()
	# 			event.accept()
	# 		else:
	# 			event.ignore()
	# 	else:
	# 		self.gui.close()
	# 		event.accept()


# Settings window.
class SettingsWindow(QtGui.QDialog):
	def __init__(self, program_settings, main_window):
		# Create an instance of QDialog.
		QtGui.QDialog.__init__(self, main_window, QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.WindowTitleHint)

		# Set window title.
		self.setWindowTitle('Settings')
		# Require window to be closed before the main window can be used.
		self.setModal(True)
		# Display the window.
		self.show()

		# Create a label containing the logo.
		# logo = QtGui.QLabel()
		# logo.setPixmap(QtGui.QPixmap(program_settings['installDir'].get_value()+'/logo.png'))

		# Create settings entries.
		self.entry_row_count = tetronGuiHelper.EntrySpinBox('row_count', program_settings=main_window.gui.program_settings, callbacks=[])
		self.entry_column_count = tetronGuiHelper.EntrySpinBox('column_count', program_settings=main_window.gui.program_settings, callbacks=[])
		self.entry_speed = tetronGuiHelper.EntrySpinBox('speed', program_settings=main_window.gui.program_settings, callbacks=[main_window.gui.callback_speed])

		# Add labels to the layout.
		layout = QtGui.QVBoxLayout()
		layout.setAlignment(QtCore.Qt.AlignTop)
		layout.addWidget(self.entry_row_count)
		layout.addWidget(self.entry_column_count)
		layout.addWidget(self.entry_speed)

		self.setLayout(layout)


# A dialog window that displays information about the program.
class AboutWindow(QtGui.QDialog):
	def __init__(self, program_settings, main_window):
		# Create an instance of QDialog.
		QtGui.QDialog.__init__(self, main_window, QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.WindowTitleHint)

		# Set window title.
		self.setWindowTitle('About')
		# Require window to be closed before the main window can be used.
		self.setModal(True)
		# Display the window.
		self.show()

		# Create a label containing the logo.
		logo = QtGui.QLabel()
		logo.setPixmap(QtGui.QPixmap(program_settings['installDir'].get_value()+'/logo.png'))

		# Create labels containing text.
		label_program_name = QtGui.QLabel(program_settings['program_name'].get_value())
		label_version_number = QtGui.QLabel('Version ' + program_settings['version_number'].get_value())
		label_version_date = QtGui.QLabel(program_settings['version_date'].get_value())
		label_program_name.setAlignment(QtCore.Qt.AlignCenter)
		label_version_number.setAlignment(QtCore.Qt.AlignCenter)
		label_version_date.setAlignment(QtCore.Qt.AlignCenter)
		# Set style sheets for labels.
		label_program_name.setStyleSheet('font-size: 20pt; font-weight: bold;')
		label_version_date.setStyleSheet('color: rgba(0%,0%,0%,25%)')

		# Add labels to the layout.
		layout = QtGui.QVBoxLayout()
		layout.setAlignment(QtCore.Qt.AlignCenter)
		layout.addWidget(logo)
		layout.addWidget(label_program_name)
		layout.addWidget(label_version_number)
		layout.addWidget(label_version_date)

		self.setLayout(layout)