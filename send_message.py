from PodSixNet.Connection import connection, ConnectionListener
import sys
from time import sleep

class obj_network_listener(ConnectionListener):
	"""handles multiplayer connections """
	def __init__(self, host, port):
		self.Connect((host, port))

	def Network_connected(self, data):
		print("connected to the server")
	
	def Network_error(self, data):
		print("error:", data['error'][1])
	
	def Network_disconnected(self, data):
		print("disconnected from the server")

	def Network(self, data):#called on all network activity
		print(data)
		pass

def watch_network(len = 3):
	for i in range(len):
		NETWORK_LISTENER.Pump()
		connection.Pump()
		sleep(.1)

if __name__ == '__main__':

	NETWORK_LISTENER = obj_network_listener('localhost', 1337)

	for i in range(3):
		NETWORK_LISTENER.Pump()
		connection.Pump()
		sleep(.1)

	if sys.argv and len(sys.argv) >= 3:
		connection.Send({"action": sys.argv[1], 'value' : str(sys.argv[2])})

	while True:
		NETWORK_LISTENER.Pump()
		connection.Pump()
		val = str(input("	> Enter command: "))
		if val == "quit":
			break

		elif val == 'pump':
			watch_network()

		else:
			arry = val.split(' ')
			if len(arry) > 1:

				if arry[0] == 'pump':
					watch_network(int(arry[1]))

				connection.Send({"action": arry[0], 'value' : str(arry[1])})

		sleep(.1)
