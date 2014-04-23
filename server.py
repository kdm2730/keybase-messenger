#!/usr/bin/env python
#filename: server.py
#purpose: a server to interact with keybase to encrypt and decrypt messages

#module include section
import threading
import socket
import re
import signal
import sys
import time

#server class definition
class Server():
	def __init__(self, port):
		#create a socket and bind it to a port
		self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.listener.bind(('', port))
		self.listener.listen(1)
		print "Listening on port {0}".format(port)

		#used to store client sockets
		self.client_sockets = []

		#run the function self.signal_handler when ctrl+c is pressed
		signal.signal(signal.SIGINT, self.signal_handler)
		signal.signal(signal.SIGTERM, self.signal_handler)

	def run(self):
		while True:
			#listen for clients and create a client thread for each client
			print "Listening for more clients..."
			try:
				(client_socket, client_address) = self.listener.accept()
			except socket.error:
				sys.exit("Could not accept any more connections")
				
			self.client_sockets.append(client_socket)
			print "Starting thread for {0}".format(client_address)
			client_thread = ClientListener(self, client_socket, client_address)
			client_thread.start()
			time.sleep(0.1)

	def echo(self, data):
		#send a message to each socket in self.client
		print "echoing: {0}".format(data)
		
		#attempt to echo to all sockets
		for socket in self.client_sockets:
			try:
				socket.sendall(data)
			except socket.error:
				print "Unable to send message"

	def remove_socket(self, socket):
		#remove a specified socket from the client_sockets listener
		self.client_sockets.remove(socket)

	def signal_handler(self, signal, frame):
		#run when ctrl+c is pressed
		print "Cleaning up"

		#stop listening for new connections
		self.listener.close()

		#let each client know the server is going down
		self.echo("QUIT")

#client listener class definition
class ClientListener(threading.Thread):
	def __init__(self, server, socket, address):
		#initialise the thread base class
		super(ClientListener, self).__init__()

		#store the values that have been passed to the constructor
		self.server = server
		self.address = address
		self.socket = socket
		self.listening = True
		self.username = "No Username"

	def run(self):
		#the thread's loop to recieve and process messages
		while self.listening:
			data = ""
			try:
				data = self.socket.recv(1024)
			except socket.error:
				"Unable to recieve data"
			self.handle_msg(data)
			time.sleep(0.1)

		print "Ending client thread for {0}".format(self.address)

	def quit(self):
		#clean up and end the thread
		self.listening = False
		self.socket.close()
		self.server.remove_socket(self.socket)
		self.server.echo("{0} has quit.\n".format(self.username))

	def handle_msg(self, data):
		#print and process the recieved message
		print "{0} sent: {1}".format(self.address, data)

		#use regex to find usernames
		username_result = re.search('^USERNAME (.*)$', data)
		if username_result:
			self.username = username_result.group(1)
			self.server.echo("{0} has joined.\n".format(self.username))
		elif data == "QUIT":
			#if the client has sent quit then close this thread
			self.quit()
		elif data == "":
			#the socket on the other end is probably closed
			self.quit()
		else:
			#it is a normal message so echo it to everyone
			self.server.echo(data)

#main program
if __name__ == "__main__":
	#start server on port 3600
	server = Server(3600)
	server.run()