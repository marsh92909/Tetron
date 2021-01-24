# -*- coding: latin-1 -*-


from collections import deque
import errno
from functools import wraps, reduce
import logging
import numpy as np
import os
import platform
import Queue
from queue import Queue, Empty as QueueEmpty
import re
from select import error as SelectError
import socket
import threading
import time
import traceback

import serial


# The main thread.
class MainThread(threading.Thread):
    # Override __init__ method.
    def __init__(self, program_settings, queue_next, queue_hold, queue_status, queue_console):
        super(MainThread, self).__init__()
        self.program_settings = program_settings
        self.queue_next = queue_next
        self.queue_hold = queue_hold
        self.queue_status = queue_status
        self.queue_console = queue_console
        
        # Create an event that, when True, stops the game.
        self.stop_event = threading.Event()
        # Create an event that, when True, pauses the game.
        self.pause_event = threading.Event()
        # # Create an event that is True when the projector is displaying a slice.
        # self.expose_event = threading.Event()
    
    # Override run method.
    def run(self):
        # Create an array to contain block data.
        row_count = self.program_settings['row_count'].get_value()
        column_count = self.program_settings['column_count'].get_value()
        self.data = np.zeros([row_count, column_count])

    # Move the current tetronimo to the bottom.
    def place(self):
        pass
    
    # Lower the current tetronimo by one row.
    def advance(self):
        pass


# A thread that controls a print process from start to finish.
class PrintThread(threading.Thread):
	# Override __init__ method.
	def __init__(self, model_collection, program_settings, printer, queue_printing_index, queueSliceIn, queue_status, queue_console):
		super(PrintThread, self).__init__()
		self.model_collection = model_collection
		self.program_settings = program_settings
		self.printer = printer
		self.queue_printing_index = queue_printing_index
		self.queueSliceIn = queueSliceIn
		self.queue_status = queue_status
		self.queue_console = queue_console

		# Create an event that, when True, stops the print process.
		self.stop_event = threading.Event()
		# Create an event that, when True, pauses the print process.
		self.pause_event = threading.Event()
		# Create an event that is True when the projector is displaying a slice.
		self.expose_event = threading.Event()

	# Override run method.
	def run(self):
		# Get the values of settings required during printing.
		speed = self.program_settings['lift_speed'].get_value()
		distance_lift = self.program_settings['lift_distance'].get_value()
		distance_retract = self.program_settings['lift_distance'].get_value() - self.program_settings['layer_height'].get_value()
		time_settle = self.program_settings['settling_time'].get_value()
		base_layer_count = self.program_settings['base_layer_count'].get_value()
		time_exposure_base = self.program_settings['exposure_time_base'].get_value()
		time_exposure = self.program_settings['exposure_time'].get_value()
		# Calculate how much time the platform takes to move, in seconds.
		time_platform = ((distance_lift + distance_retract) / speed) * 60

		# Define the G-code commands used in the print process.
		list_commands_start = ['G21','G91','M17','G1 F'+str(speed)]
		list_commands_printing = ['G1 Z-'+str(distance_lift), 'G1 Z'+str(distance_retract)]
		list_commands_finish = ['M18']

		# Initialize slice number.
		self.current_index = 0
		self.slice_count = self.model_collection.get_slice_count()

		# ======================================================================
		# Run commands before printing.
		# ======================================================================
		for gcode in list_commands_start:
			# Exit this loop if the print was stopped.
			if self.stop_event.is_set():
				break 
			self.send_gcode(gcode)

		# ======================================================================
		# Run commands during printing.
		# ======================================================================
		while self.current_index < self.slice_count:
			# Exit this loop if the print was stopped.
			if self.stop_event.is_set():
				break
			# Wait indefinitely if the print was paused.
			while self.pause_event.is_set():
				time.sleep(0.5)
			
			# Show a message and update the status text.
			print('Printing slice {} of {}.'.format(str(self.current_index), str(self.slice_count)))
			# self.queue_console.put('Exposing with {} s.'.format(str(self.exposureTime)))

			# Show the slice on the projector.
			self.expose_event.set()
			self.set_image(self.current_index)
			# Wait during exposure.
			if self.current_index < base_layer_count:
				self.wait(time_exposure_base)
			else:
				self.wait(time_exposure)
			# Stop exposure by showing a black image.
			self.expose_event.clear()
			self.set_image(-1)

			# Send G-code commands to move the platform.
			for gcode in list_commands_printing:
				self.send_gcode(gcode)
			# Wait while the platform is moving.
			self.wait(time_platform)

			# Wait for the resin to settle.
			self.wait(time_settle)
			
			# Increment the slice number.
			self.current_index += 1

		# ======================================================================
		# Run commands after printing and shut down.
		# ======================================================================
		for gcode in list_commands_finish:
			self.send_gcode(gcode)
		
		# Show a message and update the status text.
		print('\nPrint stopped after {} slices.'.format(str(self.current_index-1)))
		if self.stop_event.is_set():
			self.queue_status.put('print_stopped')
		else:
			self.queue_status.put('printed')

	# Put the current slice index in a queue to let the GUI update the projector window.
	def set_image(self, slice_index):
		# Empty the queue used by the GUI.
		if not self.queueSliceIn.empty():
			self.queueSliceIn.get()

		# Put the slice index in the queue to update the projector window.
		while not self.queue_printing_index.empty():
			time.sleep(0.1)
		self.queue_printing_index.put(slice_index)

		# Wait until GUI puts True in the queue.
		while not self.queueSliceIn.qsize():
			time.sleep(0.1)
		self.queueSliceIn.get()

	# Send a G-code command to the printer.
	def send_gcode(self, gcode):
		# Stop this function if the print was stopped.
		if self.stop_event.is_set():
			return
		# Wait indefinitely if the print was paused.
		while self.pause_event.is_set():
			time.sleep(0.5)
		
		# Substitute in values needed for some G-code commands.
		if all(string in gcode for string in '{}'):
			index_1 = gcode.find('{')
			index_2 = gcode.find('}')
			setting_name = gcode[index_1+1:index_2]
			gcode = gcode.replace(gcode[index_1:index_2+1], str(self.program_settings[setting_name].get_value()))
		# Print the command.
		print('G-code command:      "{}".'.format(gcode))
		# Send the command.
		self.printer.send(gcode)

	# Wait for a number of seconds.
	def wait(self, duration):
		time_elapsed = 0
		time_start = time.time()
		while time_elapsed < duration:
			# Stop this function if the print was stopped.
			if self.stop_event.is_set():
				return
			# Wait indefinitely if the print was paused.
			while self.pause_event.is_set():
				time.sleep(0.5)
			
			# Wait and record the elapsed time.
			time.sleep(.1)
			time_elapsed = time.time() - time_start
	
	# Pause printing.
	def pause(self):
		self.queue_printing_index.put(-1)
		self.pause_event.set()
	
	# Resume printing.
	def resume(self):
		if self.expose_event.is_set():
			self.queue_printing_index.put(self.current_index)
		else:
			self.queue_printing_index.put(-1)
		self.pause_event.clear()

	# Stop printing.
	def stop(self):
		self.queue_printing_index.put(-1)
		self.stop_event.set()
		self.pause_event.clear()
		self.queue_status.put('stopping')

	"""
	# Create printer serial port.
	def createSerial(self):
#		if not self.debug and not self.stopThread.isSet():
			self.queue_status.put("preparing:connecting:")
			serialPrinter = theaterSerial.printerStandalone(self.program_settings)
			# Check if serial is operational.
			if serialPrinter.serial == None: #and not self.debug:
				self.queue_status.put("error:connectionFail:")
				#self.queue_status.put("Serial port " + self.program_settings['Port'].value + " not found. Aborting.")
				self.queue_console.put("Serial port " + self.program_settings['port'].value + " not found. Aborting.\nMake sure your board is plugged in and you have defined the correct serial port in the settings menu.")
				print('Connection to printer not established. Aborting print process. Check your settings!')
				self.stopThread.set()
			else: #elif not self.debug:
				# Send ping to test connection.
				#TODO: do this for GCode board.
				if self.program_settings['monkeyprintBoard'].value:
					if serialPrinter.send(["ping", None, True, None]) == True:
						self.queue_status.put("preparing:connectionSuccess:")
						#self.queue_status.put("Connection to printer established.")
						print('Connection to printer established.')
			return serialPrinter
#		else:
#			return None

	# Create projector serial port.
	def createProjectorSerial(self):
#		if not self.debug and not self.stopThread.isSet():
			#self.queue_status.put("Connecting to projector...")
			self.queue_status.put("preparing:startingProjector:")
			serialProjector = theaterSerial.projector(self.program_settings)
			if serialProjector.serial == None:
				#self.queue_status.put("Projector not found on port " + self.program_settings['Port'].value + ". Start manually.")
				self.queue_status.put("error:projectorNotFound:")
				self.queue_console.put("Projector not found on port " + self.program_settings['port'].value + ". \nMake sure you have defined the correct serial port in the settings menu.")
				projectorControl = False
			else:
				#self.queue_status.put("Projector started.")
				self.queue_status.put("preparing:projectorConnected:")
			return serialProjector
	"""


# Copied from Printrun. ========================================================
def locked(f):
    @wraps(f)
    def inner(*args, **kw):
        with inner.lock:
            return f(*args, **kw)
    inner.lock = threading.Lock()
    return inner

def control_ttyhup(port, disable_hup):
    """Controls the HUPCL"""
    if platform.system() == "Linux":
        if disable_hup:
            os.system("stty -F %s -hup" % port)
        else:
            os.system("stty -F %s hup" % port)

def enable_hup(port):
    control_ttyhup(port, False)

def disable_hup(port):
    control_ttyhup(port, True)

def decode_utf8(s):
    try:
        s = s.decode("utf-8")
    except:
        pass
    return s

PRINTCORE_HANDLER = []  # This statement replaces a deleted import statement that references a file that defines the variable here as an empty list

gcode_strip_comment_exp = re.compile("\([^\(\)]*\)|;.*|[/\*].*\n")
# ==============================================================================


# A class for creating and connecting to a serial port for the printer.
# Copied and modified from Printrun.
class Printcore():
    def __init__(self, port = None, baud = None, dtr=None):
        """Initializes a printcore instance. Pass the port and baud rate to
           connect immediately"""
        self.baud = None
        self.dtr = None
        self.port = None
        # self.analyzer = gcoder.GCode()  # ML: Don't need?
        # Serial instance connected to the printer, should be None when
        # disconnected
        self.printer = None
        # clear to send, enabled after responses
        # FIXME: should probably be changed to a sliding window approach
        self.clear = 0
        # The printer has responded to the initial command and is active
        self.online = False
        # is a print currently running, true if printing, false if paused
        self.printing = False
        self.mainqueue = None
        self.priqueue = Queue(0)
        self.queueindex = 0
        self.lineno = 0
        self.resendfrom = -1
        self.paused = False
        self.sentlines = {}
        self.log = deque(maxlen = 10000)
        self.sent = []
        self.writefailures = 0
        self.tempcb = None  # impl (wholeline)
        self.recvcb = None  # impl (wholeline)
        self.sendcb = None  # impl (wholeline)
        self.preprintsendcb = None  # impl (wholeline)
        self.printsendcb = None  # impl (wholeline)
        self.layerchangecb = None  # impl (wholeline)
        self.errorcb = None  # impl (wholeline)
        self.startcb = None  # impl ()
        self.endcb = None  # impl ()
        self.onlinecb = None  # impl ()
        self.loud = True  # emit sent and received lines to terminal
        self.tcp_streaming_mode = False
        self.greetings = ['start', 'Grbl ']
        self.wait = 0  # default wait period for send(), send_now()
        self.read_thread = None
        self.stop_read_thread = False
        self.send_thread = None
        self.stop_send_thread = False
        self.print_thread = None
        self.event_handler = PRINTCORE_HANDLER
        for handler in self.event_handler:
            try: handler.on_init()
            except: logging.error(traceback.format_exc())
        if port is not None and baud is not None:
            self.connect(port, baud)
        self.xy_feedrate = None
        self.z_feedrate = None

    def addEventHandler(self, handler):
        '''
        Adds an event handler.
        
        @param handler: The handler to be added.
        '''
        self.event_handler.append(handler)

    def logError(self, error):
        for handler in self.event_handler:
            try: handler.on_error(error)
            except: logging.error(traceback.format_exc())
        if self.errorcb:
            try: self.errorcb(error)
            except: logging.error(traceback.format_exc())
        else:
            logging.error(error)

    @locked
    def disconnect(self):
        """Disconnects from printer and pauses the print
        """
        if self.printer:
            if self.read_thread:
                self.stop_read_thread = True
                if threading.current_thread() != self.read_thread:
                    self.read_thread.join()
                self.read_thread = None
            if self.print_thread:
                self.printing = False
                self.print_thread.join()
            self._stop_sender()
            try:
                self.printer.close()
            except socket.error:
                pass
            except OSError:
                pass
        for handler in self.event_handler:
            try: handler.on_disconnect()
            except: logging.error(traceback.format_exc())
        self.printer = None
        self.online = False
        self.printing = False

    @locked
    def connect(self, port=None, baud=None, dtr=None):
        """Set port and baudrate if given, then connect to printer
        """
        if self.printer:
            self.disconnect()
        if port is not None:
            self.port = port
        if baud is not None:
            self.baud = baud
        if dtr is not None:
            self.dtr = dtr
        if self.port is not None and self.baud is not None:
            # Connect to socket if "port" is an IP, device if not
            host_regexp = re.compile("^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$|^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$")
            is_serial = True
            if ":" in port:
                bits = port.split(":")
                if len(bits) == 2:
                    hostname = bits[0]
                    try:
                        port = int(bits[1])
                        if host_regexp.match(hostname) and 1 <= port <= 65535:
                            is_serial = False
                    except:
                        pass
            self.writefailures = 0
            if not is_serial:
                self.printer_tcp = socket.socket(socket.AF_INET,
                                                 socket.SOCK_STREAM)
                self.printer_tcp.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.timeout = 0.25
                self.printer_tcp.settimeout(1.0)
                try:
                    self.printer_tcp.connect((hostname, port))
                    self.printer_tcp.settimeout(self.timeout)
                    self.printer = self.printer_tcp.makefile()
                except socket.error as e:
                    if(e.strerror is None): e.strerror=""
                    self.logError("Could not connect to %s:%s:" % (hostname, port) +
                                  "\n" + "Socket error %s:" % e.errno +
                                  "\n" + e.strerror)
                    self.printer = None
                    self.printer_tcp = None
                    return
            else:
                disable_hup(self.port)
                self.printer_tcp = None
                try:
                    self.printer = serial.Serial(port = self.port,
                                          baudrate = self.baud,
                                          timeout = 0.25,
                                          parity = serial.PARITY_ODD)
                    self.printer.close()
                    self.printer.parity = serial.PARITY_NONE
                    try:  #this appears not to work on many platforms, so we're going to call it but not care if it fails
                        self.printer.setDTR(dtr)
                    except:
                        #self.logError("Could not set DTR on this platform") #not sure whether to output an error message
                        pass
                    self.printer.open()
                except serial.SerialException as e:
                    self.logError("Could not connect to %s at baudrate %s:" % (self.port, self.baud) +
                                  "\n" + "Serial error: %s" % e)
                    self.printer = None
                    return
                except IOError as e:
                    self.logError("Could not connect to %s at baudrate %s:" % (self.port, self.baud) +
                                  "\n" + "IO error: %s" % e)
                    self.printer = None
                    return
            for handler in self.event_handler:
                try: handler.on_connect()
                except: logging.error(traceback.format_exc())
            self.stop_read_thread = False
            self.read_thread = threading.Thread(target = self._listen)
            self.read_thread.start()
            self._start_sender()

    def reset(self):
        """Reset the printer
        """
        if self.printer and not self.printer_tcp:
            self.printer.setDTR(1)
            time.sleep(0.2)
            self.printer.setDTR(0)

    def _readline(self):
        try:
            try:
                try:
                    line = self.printer.readline().decode('ascii')
                except UnicodeDecodeError:
                    self.logError("Got rubbish reply from %s at baudrate %s:" % (self.port, self.baud) +
                                  "\n" + "Maybe a bad baudrate?")
                    return None
                if self.printer_tcp and not line:
                    raise OSError(-1, "Read EOF from socket")
            except socket.timeout:
                return ""

            if len(line) > 1:
                self.log.append(line)
                for handler in self.event_handler:
                    try: handler.on_recv(line)
                    except: logging.error(traceback.format_exc())
                if self.recvcb:
                    try: self.recvcb(line)
                    except: self.logError(traceback.format_exc())
                if self.loud: logging.info("RECV: %s" % line.rstrip())
            return line
        except SelectError as e:
            if 'Bad file descriptor' in e.args[1]:
                self.logError("Can't read from printer (disconnected?) (SelectError {0}): {1}".format(e.errno, decode_utf8(e.strerror)))
                return None
            else:
                self.logError("SelectError ({0}): {1}".format(e.errno, decode_utf8(e.strerror)))
                raise
        except serial.SerialException as e:
            self.logError("Can't read from printer (disconnected?) (SerialException): {0}".format(decode_utf8(str(e))))
            return None
        except socket.error as e:
            self.logError("Can't read from printer (disconnected?) (Socket error {0}): {1}".format(e.errno, decode_utf8(e.strerror)))
            return None
        except OSError as e:
            if e.errno == errno.EAGAIN:  # Not a real error, no data was available
                return ""
            self.logError("Can't read from printer (disconnected?) (OS Error {0}): {1}".format(e.errno, e.strerror))
            return None

    def _listen_can_continue(self):
        if self.printer_tcp:
            return not self.stop_read_thread and self.printer
        return (not self.stop_read_thread
                and self.printer
                and self.printer.isOpen())

    def _listen_until_online(self):
        while not self.online and self._listen_can_continue():
            self._send("M105")
            if self.writefailures >= 4:
                logging.error("Aborting connection attempt after 4 failed writes.")
                return
            empty_lines = 0
            while self._listen_can_continue():
                line = self._readline()
                if line is None: break  # connection problem
                # workaround cases where M105 was sent before printer Serial
                # was online an empty line means read timeout was reached,
                # meaning no data was received thus we count those empty lines,
                # and once we have seen 15 in a row, we just break and send a
                # new M105
                # 15 was chosen based on the fact that it gives enough time for
                # Gen7 bootloader to time out, and that the non received M105
                # issues should be quite rare so we can wait for a long time
                # before resending
                if not line:
                    empty_lines += 1
                    if empty_lines == 15: break
                else: empty_lines = 0
                if line.startswith(tuple(self.greetings)) \
                   or line.startswith('ok') or "T:" in line:
                    self.online = True
                    for handler in self.event_handler:
                        try: handler.on_online()
                        except: logging.error(traceback.format_exc())
                    if self.onlinecb:
                        try: self.onlinecb()
                        except: self.logError(traceback.format_exc())
                    return

    def _listen(self):
        """This function acts on messages from the firmware
        """
        self.clear = True
        if not self.printing:
            self._listen_until_online()
        while self._listen_can_continue():
            line = self._readline()
            if line is None:
                break
            if line.startswith('DEBUG_'):
                continue
            if line.startswith(tuple(self.greetings)) or line.startswith('ok'):
                self.clear = True
            if line.startswith('ok') and "T:" in line:
                for handler in self.event_handler:
                    try: handler.on_temp(line)
                    except: logging.error(traceback.format_exc())
            if line.startswith('ok') and "T:" in line and self.tempcb:
                # callback for temp, status, whatever
                try: self.tempcb(line)
                except: self.logError(traceback.format_exc())
            elif line.startswith('Error'):
                self.logError(line)
            # Teststrings for resend parsing       # Firmware     exp. result
            # line="rs N2 Expected checksum 67"    # Teacup       2
            if line.lower().startswith("resend") or line.startswith("rs"):
                for haystack in ["N:", "N", ":"]:
                    line = line.replace(haystack, " ")
                linewords = line.split()
                while len(linewords) != 0:
                    try:
                        toresend = int(linewords.pop(0))
                        self.resendfrom = toresend
                        break
                    except:
                        pass
                self.clear = True
        self.clear = True

    def _start_sender(self):
        self.stop_send_thread = False
        self.send_thread = threading.Thread(target = self._sender)
        self.send_thread.start()

    def _stop_sender(self):
        if self.send_thread:
            self.stop_send_thread = True
            self.send_thread.join()
            self.send_thread = None

    def _sender(self):
        while not self.stop_send_thread:
            try:
                command = self.priqueue.get(True, 0.1)
            except QueueEmpty:
                continue
            while self.printer and self.printing and not self.clear:
                time.sleep(0.001)
            self._send(command)
            while self.printer and self.printing and not self.clear:
                time.sleep(0.001)

    def _checksum(self, command):
        return reduce(lambda x, y: x ^ y, map(ord, command))

    def startprint(self, gcode, startindex = 0):
        """Start a print, gcode is an array of gcode commands.
        returns True on success, False if already printing.
        The print queue will be replaced with the contents of the data array,
        the next line will be set to 0 and the firmware notified. Printing
        will then start in a parallel thread.
        """
        if self.printing or not self.online or not self.printer:
            return False
        self.queueindex = startindex
        self.mainqueue = gcode
        self.printing = True
        self.lineno = 0
        self.resendfrom = -1
        self._send("M110", -1, True)
        if not gcode or not gcode.lines:
            return True
        self.clear = False
        resuming = (startindex != 0)
        self.print_thread = threading.Thread(target = self._print,
                                             kwargs = {"resuming": resuming})
        self.print_thread.start()
        return True

    def cancelprint(self):
        self.pause()
        self.paused = False
        self.mainqueue = None
        self.clear = True

    # run a simple script if it exists, no multithreading
    def runSmallScript(self, filename):
        if filename is None: return
        f = None
        try:
            with open(filename) as f:
                for i in f:
                    l = i.replace("\n", "")
                    l = l[:l.find(";")]  # remove comments
                    self.send_now(l)
        except:
            pass

    def pause(self):
        """Pauses the print, saving the current position.
        """
        if not self.printing: return False
        self.paused = True
        self.printing = False

        # try joining the print thread: enclose it in try/except because we
        # might be calling it from the thread itself
        try:
            self.print_thread.join()
        except RuntimeError as e:
            if e.message == "cannot join current thread":
                pass
            else:
                self.logError(traceback.format_exc())
        except:
            self.logError(traceback.format_exc())

        self.print_thread = None

        # saves the status
        """   # Gcoder doesn't exist
        self.pauseX = self.analyzer.abs_x
        self.pauseY = self.analyzer.abs_y
        self.pauseZ = self.analyzer.abs_z
        self.pauseE = self.analyzer.abs_e
        self.pauseF = self.analyzer.current_f
        self.pauseRelative = self.analyzer.relative
        """

    def resume(self):
        """Resumes a paused print.
        """
        if not self.paused: return False
        if self.paused:
            # restores the status
            self.send_now("G90")  # go to absolute coordinates

            xyFeedString = ""
            zFeedString = ""
            if self.xy_feedrate is not None:
                xyFeedString = " F" + str(self.xy_feedrate)
            if self.z_feedrate is not None:
                zFeedString = " F" + str(self.z_feedrate)

            self.send_now("G1 X%s Y%s%s" % (self.pauseX, self.pauseY,
                                            xyFeedString))
            self.send_now("G1 Z" + str(self.pauseZ) + zFeedString)
            self.send_now("G92 E" + str(self.pauseE))

            # go back to relative if needed
            if self.pauseRelative: self.send_now("G91")
            # reset old feed rate
            self.send_now("G1 F" + str(self.pauseF))

        self.paused = False
        self.printing = True
        self.print_thread = threading.Thread(target = self._print,
                                             kwargs = {"resuming": True})
        self.print_thread.start()

    def send(self, command, wait = 0):
        """Adds a command to the checksummed main command queue if printing, or
        sends the command immediately if not printing"""

        if self.online:
            if self.printing:
                self.mainqueue.append(command)
            else:
                self.priqueue.put_nowait(command)
        else:
            self.logError("Not connected to printer.")

    def send_now(self, command, wait = 0):
        """Sends a command to the printer ahead of the command queue, without a
        checksum"""
        if self.online:
            self.priqueue.put_nowait(command)
        else:
            self.logError("Not connected to printer.")

    def _print(self, resuming = False):
        self._stop_sender()
        try:
            for handler in self.event_handler:
                try: handler.on_start(resuming)
                except: logging.error(traceback.format_exc())
            if self.startcb:
                # callback for printing started
                try: self.startcb(resuming)
                except:
                    self.logError("Print start callback failed with:" +
                                  "\n" + traceback.format_exc())
            while self.printing and self.printer and self.online:
                self._sendnext()
            self.sentlines = {}
            self.log.clear()
            self.sent = []
            for handler in self.event_handler:
                try: handler.on_end()
                except: logging.error(traceback.format_exc())
            if self.endcb:
                # callback for printing done
                try: self.endcb()
                except:
                    self.logError("Print end callback failed with:" +
                                  "\n" + traceback.format_exc())
        except:
            self.logError("Print thread died due to the following error:" +
                          "\n" + traceback.format_exc())
        finally:
            self.print_thread = None
            self._start_sender()

    def process_host_command(self, command):
        """only ;@pause command is implemented as a host command in printcore, but hosts are free to reimplement this method"""
        command = command.lstrip()
        if command.startswith(";@pause"):
            self.pause()

    def _sendnext(self):
        if not self.printer:
            return
        while self.printer and self.printing and not self.clear:
            time.sleep(0.001)
        # Only wait for oks when using serial connections or when not using tcp
        # in streaming mode
        if not self.printer_tcp or not self.tcp_streaming_mode:
            self.clear = False
        if not (self.printing and self.printer and self.online):
            self.clear = True
            return
        if self.resendfrom < self.lineno and self.resendfrom > -1:
            self._send(self.sentlines[self.resendfrom], self.resendfrom, False)
            self.resendfrom += 1
            return
        self.resendfrom = -1
        if not self.priqueue.empty():
            self._send(self.priqueue.get_nowait())
            self.priqueue.task_done()
            return
        if self.printing and self.mainqueue.has_index(self.queueindex):
            (layer, line) = self.mainqueue.idxs(self.queueindex)
            gline = self.mainqueue.all_layers[layer][line]
            if self.queueindex > 0:
                (prev_layer, prev_line) = self.mainqueue.idxs(self.queueindex - 1)
                if prev_layer != layer:
                    for handler in self.event_handler:
                        try: handler.on_layerchange(layer)
                        except: logging.error(traceback.format_exc())
            if self.layerchangecb and self.queueindex > 0:
                (prev_layer, prev_line) = self.mainqueue.idxs(self.queueindex - 1)
                if prev_layer != layer:
                    try: self.layerchangecb(layer)
                    except: self.logError(traceback.format_exc())
            for handler in self.event_handler:
                try: handler.on_preprintsend(gline, self.queueindex, self.mainqueue)
                except: logging.error(traceback.format_exc())
            if self.preprintsendcb:
                if self.mainqueue.has_index(self.queueindex + 1):
                    (next_layer, next_line) = self.mainqueue.idxs(self.queueindex + 1)
                    next_gline = self.mainqueue.all_layers[next_layer][next_line]
                else:
                    next_gline = None
                gline = self.preprintsendcb(gline, next_gline)
            if gline is None:
                self.queueindex += 1
                self.clear = True
                return
            tline = gline.raw
            if tline.lstrip().startswith(";@"):  # check for host command
                self.process_host_command(tline)
                self.queueindex += 1
                self.clear = True
                return

            # Strip comments
            tline = gcode_strip_comment_exp.sub("", tline).strip()
            if tline:
                self._send(tline, self.lineno, True)
                self.lineno += 1
                for handler in self.event_handler:
                    try: handler.on_printsend(gline)
                    except: logging.error(traceback.format_exc())
                if self.printsendcb:
                    try: self.printsendcb(gline)
                    except: self.logError(traceback.format_exc())
            else:
                self.clear = True
            self.queueindex += 1
        else:
            self.printing = False
            self.clear = True
            if not self.paused:
                self.queueindex = 0
                self.lineno = 0
                self._send("M110", -1, True)

    def _send(self, command, lineno = 0, calcchecksum = False):
        # Only add checksums if over serial (tcp does the flow control itself)
        if calcchecksum and not self.printer_tcp:
            prefix = "N" + str(lineno) + " " + command
            command = prefix + "*" + str(self._checksum(prefix))
            if "M110" not in command:
                self.sentlines[lineno] = command
        if self.printer:
            self.sent.append(command)
            # run the command through the analyzer
            gline = None
            """
            try:
                gline = self.analyzer.append(command, store = False)
            except:
                logging.warning("Could not analyze command %s:" % command +
                                "\n" + traceback.format_exc())
            """
            if self.loud:
                logging.info("SENT: %s" % command)

            for handler in self.event_handler:
                try: handler.on_send(command, gline)
                except: logging.error(traceback.format_exc())
            if self.sendcb:
                try: self.sendcb(command, gline)
                except: self.logError(traceback.format_exc())
            try:
                self.printer.write((command + "\n").encode('ascii'))
                if self.printer_tcp:
                    try:
                        self.printer.flush()
                    except socket.timeout:
                        pass
                self.writefailures = 0
            except socket.error as e:
                if e.errno is None:
                    self.logError("Can't write to printer (disconnected ?):" +
                                  "\n" + traceback.format_exc())
                else:
                    self.logError("Can't write to printer (disconnected?) (Socket error {0}): {1}".format(e.errno, decode_utf8(e.strerror)))
                self.writefailures += 1
            except serial.SerialException as e:
                self.logError("Can't write to printer (disconnected?) (SerialException): {0}".format(decode_utf8(str(e))))
                self.writefailures += 1
            except RuntimeError as e:
                self.logError("Socket connection broken, disconnected. ({0}): {1}".format(e.errno, decode_utf8(e.strerror)))
                self.writefailures += 1


"""
class printerStandalone:
	def __init__(self, settings):
		self.settings = settings

		# Get serial parameters from settings.
		self.port = self.settings['port'].value
		self.baudrate = self.settings['baudrate'].value

		self.terminator = '\n'

		print('Opening serial on port ' + self.port + ' with baud rate ' + str(self.baudrate) + '.')
		# Configure and open serial.
		try:
			self.serial = serial.Serial(
				port = self.port,
				baudrate = self.baudrate,
				bytesize = serial.EIGHTBITS,  # Number of bits per byte
				parity = serial.PARITY_NONE,  # Set parity check: no parity
				stopbits = serial.STOPBITS_ONE,
				timeout = 0	 # Wait for incoming bytes forever.
				)
		# If serial port does not exist...
		except serial.SerialException:
			# ... define a dummy.
			self.serial = None
			print('Could not open serial on port ' + str(self.port) + ' with baud rate ' + str(self.baudrate) + '.')
		else:
			self.flush()

	def flush(self, timeout=1.):
		oldTimeout = self.serial.timeout
		self.serial.timeout = timeout
		string = 'Flushing incoming messages.'
		while string != '':
			string = self.serial.readline()
			print(string)
		self.serial.timeout = oldTimeout
		return string

	def waitForOk(self, timeout=.5):
		oldTimeout = self.serial.timeout
		self.serial.timeout = timeout
		for i in range(20):
			printerResponse = self.serial.readline()
			print(printerResponse)
			if printerResponse.strip() == 'ok':
				break
			elif printerResponse.strip().split(':')[-1] == 'processing':
				i = 0
				print('Processing...')
		self.serial.timeout = oldTimeout
		return printerResponse

	# Divide command in parts beginning with G or M.
	def splitGCode(self, command):
		return filter(None, re.split('([M][^MG]*|[G][^MG]*)', command))

	# ML: This is only for splitting Gcode strings that contain multiple commands. The actual function that sends in below.
	def sendGCode(self, command):
		print(command[0])  # debugging
		commandList = self.splitGCode(command[0])
		print(commandList)  # debugging
		value = command[1]
		retry = command[2]
		wait = command[3]
		for commandString in commandList:
			self.send((commandString, value, retry, wait))

	# ML: The actual function that sends Gcode to printer.
	def send(self, command):
		# Create return value.
		returnValue = True
		# Process command.
		if len(command) < 4:
			raise ValueError('Serial command has to contain four values.')
		string = command[0]
		value = command[1]
		retry = command[2]
		wait = command[3]

		# Send command.
		if self.serial != None:
			# Cast inputs.
		#	if value != None: value = int(value)
			if wait != None: wait = int(wait)
			# Start loop that sends and waits for ack until timeout five times.
			# Set timeout to 5 seconds.
			count = 0
			self.serial.timeout = 5
			while count < 5:
				sendString = string
				# Create command string from string and value.
				# Separate string and value by space.
				if value != None:
					sendString = sendString + ' ' + str(value)
				print('Sending: ' + sendString + '.')
				# Send command.
				self.serial.write(sendString + self.terminator)
				# If retry flag is set...
				# In case fo GCode, flush input until ok is received.
				printerResponse = ''
				printerResponse = self.waitForOk()
				print('Printer response: ' + printerResponse)
				if retry:
					# ... listen for ack until timeout.
					printerResponse = printerResponse.strip()
					# Compare ack with sent string or with 'ok' in case of g-code board.
					# If match...
					if printerResponse == string or printerResponse == 'ok':
						# ... set the return value to success and...
						returnValue = True
						# ... exit the send loop.
					#	print "exiting"
						break
					# If ack does not match string...
					else:
						# ... set the return value to fail.
						returnValue = False
					#	print "resending"
				# If retry flag is not set...
				else:
					# ... exit the loop.
					break
				# Increment counter.
				count += 1
				# Place giving up message in queue if necessary.
			#	if count == 5:
			#		self.queue.put("Printer not responding. Giving up...")
								# Wait for response from printer that signals end of action.
			# If wait value is provided...
			if wait != None:
				# If wait value is 0...
				if wait == 0:
					#... set the timeout value to infinity.
					self.serial.timeout = 0
				# Else...
				else:
					# ... set timeout to one second.
					self.serial.timeout = 1
				count = 0
				while count < wait:
					# ... and listen for "done" string until timeout.
					printerResponse = self.serial.readline()
					printerResponse = printerResponse.strip()
					# Listen for "done" string.Check if return string is "done".
					if printerResponse == 'done':
						#self.queue.put("Printer done.")
						break
					else:
						count += 1
				# In case of timeout...
			#	if count == wait:
					# ... place fail message.
					#self.queue.put("Printer did not finish within timeout.")
			# Reset the timeout.
			self.serial.timeout = None
			# Flush incoming messages.
			self.flush()
			# Return success info.
			return returnValue
		else:
	#		self.flush()
			return False

	'''
	# Override run function.
	# Send a command string with optional value.
	# Method allows to retry sending until ack is received as well
	# as waiting for printer to process the command.
	def run(self):
		if self.serial != None:
			self.queue.put("Serial waiting for commands to send.")
		else:
			self.queue.put('Serial not operational.')
		# Start loop.
		while 1 and not self.stopThread.isSet():
			# Get command from queue.
			if self.queueCommands.qsize():
				command = self.queueCommands.get()
				string = command[0]
				value = command[1]
				retry = command[2]
				wait = command[3]
				if self.serial != None:
					# Cast inputs.
					if value != None: value = float(value)
					if wait != None: wait = int(wait)
					# ... start infinite loop that sends and waits for ack.
					count = 0
					# Set timeout to 5 seconds.
					self.serial.timeout = 5
					while count < 5 and not self.stopThread.isSet():
						# Create command string from string and value.
						# Separate string and value by space.
						if value != None:
							string = string + " " + str(value)
						# Place send message in queue.
						self.queue.put("Sending command \"" + string + "\".")
						# Send command.
						self.serial.write(string)
						# If retry flag is set...
						if retry:
							# ... listen for ack until timeout.
							printerResponse = self.serial.readline()
							printerResponse = printerResponse.strip()
							# Compare ack with sent string. If match...
							if printerResponse == string:
								# Place success message in queue.
								self.queue.put("Command \"" + string + "\" sent successfully.")
								if wait != None:
									self.queue.put("Wait for printer to finish...")
								# ... exit the send loop.
								break
						# If retry flag is not set...
						else:
							# ... exit the loop.
							break
						# Increment counter.
						count += 1
						# Place giving up message in queue if necessary.
						if count == 5:
							self.queue.put("Printer not responding. Giving up...")

					# Wait for response from printer that signals end of action.
					# If wait value is provided...
					if wait != 0:
						# ... set timeout to one second...
						self.serial.timeout = 1
						count = 0
						while count < wait and not self.stopThread.isSet():
							# ... and listen for "done" string until timeout.
							printerResponse = self.serial.readline()
							printerResponse = printerResponse.strip()
							# Listen for "done" string.Check if return string is "done".
							if printerResponse == "done":
								self.queue.put("Printer done.")
								break
							else:
								count += 1
						# In case of timeout...
						if count == wait:
							# ... place fail message.
							self.queue.put("Printer did not finish within timeout.")
					# Reset the timeout.
					self.serial.timeout = None
					# Put done flag into queue to signal end of command process.
					self.queue.put('done')
				else:
					self.queue.put('Sending failed. Port does not exist.')
					self.queue.put('done')
			else:
				time.sleep(.1)
	'''

	def close(self):
		if self.serial != None:
			self.serial.close()

	'''
	# Commands.
	def buildHome(self):
		self.serial.write("buildHome")
		self.waitForAckInfinite()

	def buildBaseUp(self):
		while 1:
			self.serial.timeout = 5
			self.serial.write("buildBaseUp")
			printerResponse = self.serial.readline()           # Wait for 5 sec for anything
			print "PRINTER RESPONSE: " + printerResponse
			printerResponse = printerResponse.strip()
			if printerResponse == "done":
				break
			else:
				print "      No response from printer. Resending command..."
		self.serial.timeout = None

	def buildUp(self):
		while 1:
			self.serial.write("buildUp")
			self.serial.timeout = 5
			printerResponse = self.serial.readline()           # Wait for 5 sec for anything
			print "PRINTER RESPONSE: " + printerResponse
			printerResponse = printerResponse.strip()
			if printerResponse == "done":
				break
			else:
				print "      No response from printer. Resending command..."
		self.serial.timeout = None

	def buildTop(self):
		self.serial.write("buildTop")
		self.waitForAckInfinite()

	def tilt(self):
		self.serial.write("tilt")
		self.waitForAckInfinite()

	def setStart(self):
		self.serial.write("printingFlag 1")

	def setStop(self):
		self.serial.write("printingFlag 0")

	# Settings.
	def setLayerHeight(self):
		self.serial.write("buildLayer " + str(self.settings.getLayerHeight() * self.settings.getStepsPerMm()))

	def setBaseLayerHeight(self):
		self.serial.write("buildBaseLayer " + str(self.settings.getBaseLayerHeight() * self.settings.getStepsPerMm()))

	def setBuildSpeed(self):
		self.serial.write("buildSpeed " + str(self.settings.getBuildSpeed))

	def setTiltSpeedSlow(self):
		self.serial.write("tiltSpeed " + str(self.settings.getTiltSpeedSlow))

	def setTiltSpeedFast(self):
		self.serial.write("tiltSpeed " + str(self.settings.getTiltSpeedFast))

	def setTiltAngle(self):
		self.serial.write("tiltAngle " + str(self.settings.getTiltAngle))

	def setNumberOfSlices(self, numberOfSlices):
		self.serial.write("nSlices " + str(numberOfSlices))

	def setCurrentSlice(self, currentSlice):
		self.serial.write("slice " + str(currentSlice))

#	def setTimeout(self, timeout):
#		self.serial.timeout = timeout	# Timeout for readline command. 0 is infinity, other values are seconds.

#	def waitForAckFinite(self,timeout):
#		self.serial.timeout = timeout
#		printerResponse = self.serial.readline()           # Wait for 5 sec for anything
#		print "PRINTER RESPONSE: " + printerResponse
#		printerResponse = printerResponse.strip()
#		if printerResponse=="done":
#			return 1
#		elif printerResponse != "done":
#			print "Got strange response from printer: " + printerResponse
#			return 0
#		elif printerResponse == ""
#			return 0

	def waitForAckInfinite(self):
		print "waitForAck"
		self.serial.timeout = None
		printerResponse = self.serial.readline()           # Wait forever for anything
		print "PRINTER RESPONSE: " + printerResponse
		printerResponse = printerResponse.strip()
		if printerResponse=="done":
			return "done"
		elif printerResponse != "done":
			print "Got strange response from printer: " + printerResponse
			return None
		else:
			return None

	def ping(self):
		self.serial.write("ping")
		self.serial.timeout = 10
		printerResponse = self.serial.readline()  # Wait forever for anything
		printerResponse = printerResponse.strip()
		if printerResponse!="ping":
			return 0
		else:
			return 1

	def close(self):
		if self.serial != None:
			self.serial.close()
#		print "printer serial closed"

#dontNeedThis = serialPrinter.flushInput()
	'''
"""


"""
# A serial port for a projector.
class projector:
	def __init__(self, settings):
		self.settings = settings

		# Configure and open serial.
		try:
			self.serial = serial.Serial(
				port = self.settings['port_projector'].value,
				baudrate = self.settings['baudrate_projector'].value,
				bytesize = serial.EIGHTBITS,  # Number of bits per byte
				parity = serial.PARITY_NONE,  # Set parity check: no parity
				stopbits = serial.STOPBITS_ONE
				)
		# If serial port does not exist...
		except serial.SerialException:
			# ... define a dummy.
			self.serial = None

	def activate(self):
		command = self.settings['projector_on_command'].value
		if self.serial != None:
			self.serial.write(command+'\r')

	def deactivate(self):
		command = self.settings['projector_off_command'].value
		if self.serial != None:
			self.serial.write(command+'\r')

	def close(self):
		if self.serial != None:
			self.serial.close()
#		print "projector serial closed"
"""