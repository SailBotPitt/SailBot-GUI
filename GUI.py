import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSlot, QTimer, Qt
import PyQt5.QtGui as QtGui
from PyQt5.QtGui import QPainter, QColor, QPen

import PodSixNet
from PodSixNet.Connection import connection, ConnectionListener
from PodSixNet.Channel import Channel
from PodSixNet.Server import Server

from threading import Thread
from time import sleep
import math

class ClientChannel(Channel):

	def Network(self, data):#Whenever the client does connection.Send(mydata), the Network() method will be called. 
		print(str(data))
		BOAT_DATA.message = str(data)
		
		if hasattr(BOAT_DATA, data['action']):
			setattr(BOAT_DATA, data['action'], data['value'])


		if DATA_REFRESH:
			DATA_REFRESH()

class MyServer(Server):
	
	channelClass = ClientChannel
	#Set channelClass to the channel class created above.


	def __init__(self, *args, **kwargs):
		Server.__init__(self, *args, **kwargs)
		self.channels = []
		
	def Connected(self, channel, addr):
		print(channel, "Connected")
		self.channels.append(channel)

	def send_data(self, data):
		for client in self.channels:
			client.Send(data)

	def send_once(self, data, index = 0):
		self.channels[-1].Send(data)

def server_update():
	global RUN_THREAD
	while RUN_THREAD:
		SERVER.Pump()
		sleep(.1)
		
class boat_data:
	def __init__(self):
		self.gps = None
		self.rudder_pos = None
		self.sail_pos = None
		self.boat_orient = None
		self.wind_speed = None
		self.wind_dir = None

		self.message = None

class mainWindow(QMainWindow):
	def __init__(self):
		super(mainWindow, self).__init__ ()
		self.setWindowTitle('Sailbot')
		self.resize(800, 600)

		self.tabs = tabWidget(self)
		self.setCentralWidget(self.tabs)

		self.show()

class tabWidget(QWidget):
	def __init__(self, parent):
		super(QWidget, self).__init__(parent)
		self.layout = QVBoxLayout(self)
		self.setFont(QtGui.QFont('SansSerif', 13)) 

		# Initialize tab screen
		self.tabs = QTabWidget()

		self.tab1()
		self.tab2()
		self.tab3()

		self.paint_counter = 0
		

		# Add tabs to widget
		self.layout.addWidget(self.tabs)
		self.setLayout(self.layout)

	def tab1(self):
		self.tab1 = QWidget()
		self.tabs.addTab(self.tab1,"Boat Info")

		self.tab1.layout = QGridLayout(self)
		#self.pushButton1 = QPushButton("PyQt5 button")
		#self.tab1.layout.addWidget(self.pushButton1)

		self.gps_lbl = QLabel()
		self.rudder_pos_lbl = QLabel()
		self.sail_pos_lbl = QLabel()
		self.boat_orient_lbl = QLabel()
		self.wind_speed_lbl = QLabel()
		self.wind_dir_lbl = QLabel()

		self.img = QtGui.QPixmap(300, 300)
		self.img_lbl = QLabel()
		self.img_lbl.setPixmap(self.img)
		#self.img_lbl.setFixedSize(400, 300)

		self.message_box = QTextEdit()

		self.message_box .setReadOnly(True)
		self.message_box .setLineWrapMode(QTextEdit.NoWrap)
		self.message_box.setEnabled(False)

		self.console = QLineEdit()
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
		for i in range(5):
			newBtn = QPushButton('Mode ' + str(i+1) + ": " + btnNames[i])
			newBtn.clicked.connect(lambda:SERVER.send_data({"action": 'setMode', 'value' : (i+1)}))
			self.tab2.layout.addWidget(newBtn)
			self.buttons.append(newBtn)

		

		self.tab2.setLayout(self.tab2.layout)

	def tab3(self):

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

		#self.R_pos_lbl = QLabel("Rudder Position:")
		#self.S_pos_lbl = QLabel("Sail Position:")

		self.tooltip = QLabel("A, D to adjust Sail Position. L_Arrow, R_Arrow to adjust Rudder Position")

		self.tab3.layout.addWidget(self.img_lbl2, 0, 1, 1, 1)
		self.tab3.layout.addWidget(self.cam_lbl, 0, 0, 1, 1)

		#self.tab3.layout.addWidget(self.R_pos_lbl, 1, 0, 1, 1)
		#self.tab3.layout.addWidget(self.S_pos_lbl, 1, 1, 1, 1)

		self.tab3.layout.addWidget(self.tooltip, 2, 0, 1, 2)

		self.tab3.layout.addWidget(self.console2, 20, 0, 1, 2)

		self.tab3.setLayout(self.tab3.layout)


	def commit_message(self, textBox):
		text = textBox.text()
		arry = text.split(' ')
		if len(arry) > 1:
			data = {"action": arry[0], 'value' : str(arry[1])}
			SERVER.send_once(data)

		else:
			if text == 'terminate':
				crash_app()

		textBox.setText('')

	def paintEvent(self, event):
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

		L = 45
		spacer = 30
		#self.angle += .1
		
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
		max_L = 425
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
		print("\n")
		for currentQTableWidgetItem in self.tableWidget.selectedItems():
			print(currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text())


def crash_app():
	end_program()


if __name__ == "__main__":

	
	SERVER = MyServer(localaddr=('0.0.0.0', 1337))
	DATA_REFRESH = None
	BOAT_DATA = boat_data()

	global RUN_THREAD
	RUN_THREAD = True
	pump_thread = Thread(target=server_update)
	pump_thread.start()
	

	app = QApplication(sys.argv)
	w = mainWindow()

	sys.exit(app.exec_())

