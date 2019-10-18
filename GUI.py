import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSlot, QTimer, Qt
import PyQt5.QtGui as QtGui
from PyQt5.QtGui import QPainter, QColor, QPen
import keyboard

import PodSixNet
from PodSixNet.Connection import connection, ConnectionListener
from PodSixNet.Channel import Channel
from PodSixNet.Server import Server

from threading import Thread
from time import sleep

import math

import serial

class ClientChannel(Channel):

	def Network(self, data):#Whenever the client does connection.Send(mydata), the Network() method will be called. 
		print(str(data))
		BOAT_DATA.message = str(data)
		
		if data['action'] == 'quit':
			close_app()

		#if the action is an attribute of BOAT_DATA then set the value of that attribute to the value in data
		elif hasattr(BOAT_DATA, data['action']):
			setattr(BOAT_DATA, data['action'], data['value'])

		#refreshes the screen with new boat data
		if DATA_REFRESH:
			DATA_REFRESH()

class MyServer(Server):
	"""
	The GUI is setup to act as a server, the client is the boat
	"""	
	channelClass = ClientChannel
	#Set channelClass to the channel class created above.


	def __init__(self, *args, **kwargs):
		Server.__init__(self, *args, **kwargs)
		self.channels = [] # clients (boats) connected to the server
		# the channels is an array due to potential disconnects and reconects of the boat, this will store them all
		
	def Connected(self, channel, addr):
		print(channel, "Connected")
		self.channels.append(channel)

	def send_data(self, data):
		if ARDUINO:
			ARDUINO.send(data)
		for client in self.channels:
			client.Send(data)

	def send_once(self, data, index = 0):
		if ARDUINO:
			ARDUINO.send(data)
		if len(self.channels) > 0:
			self.channels[-1].Send(data)
		#sends data to most recently connected client (last element in the array)

def server_update():
	global RUN_THREAD, DATA_REFRESH, BOAT_DATA, ARDUINO #global boolean var to stop the tread from anywhere
	while RUN_THREAD: # repeatedly pumps the server

		if CHECK_INPUT:
			handle_input()

		if ARDUINO:
			message = str(ARDUINO.read())[2:-5]

			if message:
				BOAT_DATA.message = message
				if DATA_REFRESH:
					DATA_REFRESH()

		if SERVER:
			SERVER.Pump() # removing Network data from buffer and running the Network function of ClientChannel object

		sleep(.1) # saves resources by waiting a fraction of a second between pumps
		
class boat_data:
	"""
	Stores all of the boat information in one object
	"""
	def __init__(self):
		self.gps = None
		self.rudder_pos = None
		self.sail_pos = None
		self.boat_orient = None
		self.wind_speed = None
		self.wind_dir = None

		self.message = None

class mainWindow(QMainWindow):
	"""
	Main window od the GUI, only has one child widget (tab widget)
	"""
	def __init__(self):
		super(mainWindow, self).__init__ ()
		self.setWindowTitle('Sailbot')
		self.resize(800, 600)

		self.tabs = tabWidget(self)
		self.setCentralWidget(self.tabs)

		self.show()

class tabWidget(QWidget):
	def __init__(self, parent):
		super(QWidget, self).__init__(parent) # calls QWidget.init (parent class of tabWidget)
		self.layout = QVBoxLayout(self) #lines items up vertically, not relevent as theres only one item (tabWidget)
		self.setFont(QtGui.QFont('SansSerif', 13)) 

		# Initialize tab screen
		self.tabs = QTabWidget()

		# init tabs
		self.tab1()
		self.tab2()
		self.tab3()

		#used for animation of wind
		self.paint_counter = 0
		

		# Add tabs to widget
		self.layout.addWidget(self.tabs)
		self.setLayout(self.layout)

	def tab1(self):
		self.tab1 = QWidget()
		self.tabs.addTab(self.tab1,"Boat Info")

		self.tab1.layout = QGridLayout(self)

		self.gps_lbl = QLabel()
		self.rudder_pos_lbl = QLabel()
		self.sail_pos_lbl = QLabel()
		self.boat_orient_lbl = QLabel()
		self.wind_speed_lbl = QLabel()
		self.wind_dir_lbl = QLabel()

		#img and img_lbl is for the picture of the boat and wind
		self.img = QtGui.QPixmap(300, 300) # drawing surface
		self.img_lbl = QLabel() # label to hold the drawing surface
		self.img_lbl.setPixmap(self.img)
		#self.img_lbl.setFixedSize(400, 300)

		self.message_box = QTextEdit() # stores all recived data

		self.message_box .setReadOnly(True)
		self.message_box .setLineWrapMode(QTextEdit.NoWrap)
		#self.message_box.setEnabled(False)

		self.console = QLineEdit() # entry box for sending messages to boat
		self.console.editingFinished.connect(lambda : self.commit_message(self.console))

		global DATA_REFRESH
		DATA_REFRESH = self.data_refresh
		self.data_refresh()

		self.tab1.layout.addWidget(self.gps_lbl, 0, 0)
		self.tab1.layout.addWidget(self.rudder_pos_lbl, 1, 0)
		self.tab1.layout.addWidget(self.sail_pos_lbl, 2, 0)
		self.tab1.layout.addWidget(self.boat_orient_lbl, 3, 0)
		self.tab1.layout.addWidget(self.wind_speed_lbl, 4, 0)
		self.tab1.layout.addWidget(self.wind_dir_lbl, 5, 0)

		self.tab1.layout.addWidget(self.img_lbl, 0, 1, 6, 1)

		self.tab1.layout.addWidget(self.message_box, 6, 0, 1, 2)
		self.tab1.layout.addWidget(self.console, 7, 0, 1, 2)


		self.tab1.setLayout(self.tab1.layout)

	def tab2(self):
		self.tab2 = QWidget()
		self.tabs.addTab(self.tab2,"Set Mode")
		self.tab2.layout = QGridLayout(self)

		self.buttons = []

		btnNames = ['1', '2', '3', '4', '5']
		# generates buttons with names from btnNames array
		for i in range(5):
			newBtn = QPushButton('Mode ' + str(i+1) + ": " + btnNames[i])
			#buttons send command: setMode [button number] to clients
			newBtn.clicked.connect(lambda:SERVER.send_data({"action": 'setMode', 'value' : (i+1)}))
			self.tab2.layout.addWidget(newBtn)
			self.buttons.append(newBtn)

		

		self.tab2.setLayout(self.tab2.layout)

	def tab3(self):
		"""
		Incomplete, mostly just formated labels and boxes
		"""

		self.tab3 = QWidget()
		self.tabs.addTab(self.tab3,"Manual Control")
		self.tab3.layout = QGridLayout(self)

		self.console2 = QLineEdit()
		self.console2.editingFinished.connect(lambda : self.commit_message(self.console2))

		self.img_lbl2 = QLabel()
		self.img_lbl2.setPixmap(self.img)


		self.cam_img = QtGui.QPixmap(300, 300)
		self.cam_lbl = QLabel()
		self.cam_lbl.setPixmap(self.cam_img)

		self.toggleBtn = QPushButton('Toggle Manual Control : Disabled')
		self.toggleBtn.clicked.connect(self.toggleManual)

		self.tooltip = QLabel("A, D to adjust Sail Position. L_Arrow, R_Arrow to adjust Rudder Position")

		self.tab3.layout.addWidget(self.img_lbl2, 0, 1, 1, 1)
		self.tab3.layout.addWidget(self.cam_lbl, 0, 0, 1, 1)

		self.tab3.layout.addWidget(self.tooltip, 2, 0, 1, 2)

		self.tab3.layout.addWidget(self.console2, 20, 0, 1, 2)

		self.tab3.setLayout(self.tab3.layout)


	def commit_message(self, textBox):
		"""
		called whenever a enter is pressed when console widget is targeted
		retrives data from textbox and sends a message to clients
		message must be formated as such [action] [value] ; ex) "test 123"
		message can also be a one word command for the GUI, 
		if the message is one word and not a keyword then it is ignored
		"""
		text = textBox.text()
		if ARDUINO:
			ARDUINO.send(text)
		arry = text.split(' ')
		if len(arry) > 1 and SERVER:
			data = {"action": arry[0], 'value' : str(arry[1])}
			SERVER.send_once(data)

		#one word keywords for local commands
		else:
			if text == 'terminate':
				close_app()

			elif text.startswith('ARDU_'):

				text = text.split('_')

				if text[1] == "INIT":
					#try:
					make_arduino(str(text[2]))
					# except TypeError:
					# 	print("ARDU_INIT requires a COM port index")
					# except:
					# 	print("unable to create ARDUINO object")

		textBox.setText('')

	def paintEvent(self, event):
		#called every frame, draws images used for data visualization
		qp = QPainter()
		qp.begin(self.img)
		qp.fillRect(0, 0, 300, 300, QColor("#000000"))  
		self.draw_boat(event, qp)
		self.draw_wind(event, qp)
		qp.end()
		
		self.img_lbl.setPixmap(self.img)
		self.img_lbl2.setPixmap(self.img)
		
	def draw_boat(self, event, qp):

		center = 150

		L = 45 #length of line
		spacer = 30 # angle between arms of boat hulls in degrees
		
		angle = float(BOAT_DATA.boat_orient) if BOAT_DATA.boat_orient else 0

		# DRAW HULL
		x1 = math.cos(math.radians(angle - spacer)) * L
		y1 = math.sin(math.radians(angle - spacer)) * L

		x2 = math.cos(math.radians(angle + spacer)) * L
		y2 = math.sin(math.radians(angle + spacer)) * L

		qp.setPen(QPen(QColor(255, 100, 0), 4))

		qp.drawLine(center, center, center + x1, center + y1)
		qp.drawLine(center, center, center + x2, center + y2)

		# DRAW SAIL 
		angle = float(BOAT_DATA.boat_orient) if BOAT_DATA.boat_orient else 0 
		angle += float(BOAT_DATA.sail_pos) if BOAT_DATA.sail_pos else 0

		x2 = math.cos(math.radians(angle)) * L
		y2 = math.sin(math.radians(angle)) * L

		qp.setPen(QPen(QColor(255, 255, 255), 4))

		qp.drawLine(center, center, center + x2, center + y2)


	def draw_wind(self, event, qp):
		qp.setPen(QPen(QColor(0, 0, 255), 2))
		max_L = 425 # length of lines for wind
		self.paint_counter += .05
		if self.paint_counter > 150:
			self.paint_counter = -150
		theta = float(BOAT_DATA.wind_dir) if BOAT_DATA.wind_dir else 0

		c1 = 150 + self.paint_counter * math.sin(math.radians(theta))
		c2 = 150 + self.paint_counter * math.cos(math.radians(theta))

		for i in range(-300, 300, 60):

			x1 = (math.cos(math.radians(-theta))*max_L + (c1 + i))
			y1 = (math.sin(math.radians(-theta))*max_L + (c2 + i))

			x2 = (math.cos(math.radians(-theta+180))*max_L + (c1 + i))
			y2 = (math.sin(math.radians(-theta+180))*max_L + (c2 + i))

			

			qp.drawLine(x1, y1, x2, y2)


	def toggleManual(self):
		pass
		

	def data_refresh(self):
		"""
		refreshes lbels with new data from BOAT_DATA object
		"""
		self.gps_lbl.setText("GPS: " + str(BOAT_DATA.gps))
		self.rudder_pos_lbl.setText("Rudder Position: " + str(BOAT_DATA.rudder_pos))
		self.sail_pos_lbl.setText("Sail Position: " + str(BOAT_DATA.sail_pos))
		self.boat_orient_lbl.setText("Boat Orientation: " + str(BOAT_DATA.boat_orient))
		self.wind_speed_lbl.setText("Wind Speed: " + str(BOAT_DATA.wind_speed))
		self.wind_dir_lbl.setText("Wind Direction: " + str(BOAT_DATA.wind_dir))

		if BOAT_DATA.message:
			self.message_box.append(BOAT_DATA.message)
			sleep(.1)
			sb = self.message_box.verticalScrollBar()
			sb.setValue(sb.maximum())

			BOAT_DATA.message = None

		if hasattr(self, 'R_pos_lbl'):
			self.R_pos_lbl.setText("Rudder Position: " + str(BOAT_DATA.rudder_pos))
			self.S_pos_lbl.setText("Sail Position: " + str(BOAT_DATA.sail_pos))


	@pyqtSlot()
	def on_click(self):
		#dont worry about this
		print("\n")
		for currentQTableWidgetItem in self.tableWidget.selectedItems():
			print(currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text())

#     /\           | |     (_)              / ____|                   
#    /  \   _ __ __| |_   _ _ _ __   ___   | |     ___  _ __ ___  ___ 
#   / /\ \ | '__/ _` | | | | | '_ \ / _ \  | |    / _ \| '_ ` _ \/ __|
#  / ____ \| | | (_| | |_| | | | | | (_) | | |___| (_) | | | | | \__ \
# /_/    \_\_|  \__,_|\__,_|_|_| |_|\___/   \_____\___/|_| |_| |_|___/
                                                                
class arduino:

	def __init__(self, port_num):
		self.ser1 = serial.Serial('COM'+port_num, 9600) 


	def send(self, data):
		self.ser1.write(str(data).encode())

	def read(self):
		message = self.ser1.readline()
		print(message)
		return message



def close_app():
	app.quit()
	sys.exit()

	#attempts to close app, if  causes the app to crash,
	#this is important because if you just close the window the app keeps running in the console
	#to truly close it you have to press control-break or similar in the console
	#and the break key is like wayyy at the top of the keayboard and hard to press
	end_program()

def handle_input():
	if keyboard.is_pressed('a') and SERVER:
		val = min((BOAT_DATA.sail_pos + 5), 90) if BOAT_DATA.sail_pos else 5
		SERVER.send_data({'action' : 'sail_pos', 'value' : val})
		

	elif keyboard.is_pressed('d') and SERVER:
		val = max((BOAT_DATA.sail_pos - 5), -90) if BOAT_DATA.sail_pos else -5
		SERVER.send_data({'action' : 'sail_pos', 'value' : val})

def make_arduino(com_port):

	global RUN_THREAD, ARDUINO

	ARDUINO = arduino(com_port)

	RUN_THREAD = True
	pump_thread = Thread(target=server_update)# creates a Thread running an infinite loop pumping server
	pump_thread.start()


if __name__ == "__main__":
	
	try:
		make_arduino(sys.argv.pop())
	except:
		ARDUINO = None
		print("Could not create ARDUINO object, did you include a COM port is args?")
		print("use the following command to add ARDUINO: ARDU_INIT_[COM port]")

	handle_input()
	CHECK_INPUT = True

	SERVER = MyServer(localaddr=('0.0.0.0', 1338)) # creates a server object accepting connections from any IP on port 1337
	DATA_REFRESH = None
	BOAT_DATA = boat_data() # creates BOAT_DATA object and sets it as a global variable

	


	app = QApplication(sys.argv)
	w = mainWindow()

	sys.exit(app.exec_())


