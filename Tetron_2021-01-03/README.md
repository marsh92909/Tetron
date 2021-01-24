# Resin Theater
Resin Theater is a slicer program for 3D DLP printers. It runs on Windows and is written in Python. It is a modified version of an open-source slicer program called monkeyprint, which is available at: https://github.com/robotsinthesun/monkeyprint.

## Features
* View STL files and control their position, rotation, and scale.
* Generate supports, hollow models, and create infill.
* Slice models and configure printing parameters.
* Control a DLP printer by sending G-code commands through a serial port.

## Dependencies
Resin Theater is programmed in Python 2.7 and uses the following libraries:
* `PyQt4` for the GUI
* `VTK` for the model view and slicing
* `openCV` for slice image handling
* `numpy` for slice image handling
* `pyserial` and `zmq` for communication

## Compilation


## Installation