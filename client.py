#!/usr/bin/env python
#filename: client.py
#purpose: a client to interact with keybase to encrypt and decrypt messages

#module include section
import threading
import gtk
import gobject
import socket
import re
import time
import datetime

#tell gobject to expect calls from multiple threads
gobject.threads_init()

#gui class definition
class MainWindow(gtk.Window):
	def __init__(self):
		#initialise the base gtk window class
		super(MainWindow, self).__init__()

		#create controls
		self.set_title("Keybase Messenger")
		vbox = gtk.VBox()
		hbox = gtk.HBox()
		self.username_label = gtk.Label()
		self.text_entry = gtk.Entry()
		send_button = gtk.Button("Send")
		self.text_buffer = gtk.TextBuffer()
		text_view = gtk.TextView(self.text_buffer)

		#connect events
		self.connect("destroy",self.graceful_quit)
		send_button.connect("clicked", self.send_message)

		#activate event when user presses enter
		self.text_entry.connect("activate", self.send_message)

		#do layout
		vbox.pack_start(text_view)
		hbox.pack_start(self.username_label, expand = False)
		hbox.pack_start(self.text_entry)
		hbox.pack_end(send_button, expand = False)
		vbox.pack_end(hbox, expand = False)

		#show ourselves
		self.add(vbox)
		self.show_all()

		#go through the configuration process
		self.configure()

	def ask_for_info(self, question):
		#shows a message box with a text entry and returns the response
		dialog = gtk.MessageDialog(parent = self, type = gtk.MESSAGE_QUESTION,
			flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
			buttons = gtk.BUTTONS_OK_CANCEL, message_format = question)

		entry = gtk.Entry()
		entry.show()
		dialog.vbox.pack_end(entry)
		response = dialog.run()
		response_text = entry.get_text()
		dialog.destroy()
		if response == gtk.RESPONSE_OK:
			return response_text
		else:
			return None

	def configure(self):
		#performs the steps to connect to a server
		#show a dialog box asking for server address followed by a port
		server = self.ask_for_info("server_address:port")

		#regex that crudely matches an IP address and a port number
		regex = re.search('^(\d+\.\d+\.\d+\.\d+):(\d+)$', server)
		address = regex.group(1).strip()
		port = regex.group(2).strip()

		#ask for a username
		self.username = self.ask_for_info("username")
		self.username_label.set_text(self.username)

		#attempt to conect to the server and then start listening
		self.network = Networking(self, self.username, address, int(port))
		self.network.listen()

	def add_text(self, new_text):
		#add text to the text view
		text_with_timestamp = "{0} {1}".format(datetime.datetime.now(),new_text)

		#get the position of the end of the text buffer, so we know
		#where to insert new text
		end_itr = self.text_buffer.get_end_iter()

		#add new text at the end of buffer
		self.text_buffer.insert(end_itr, text_with_timestamp)

	def send_message(self, widget):
		#clear the text entry and send messfe to the server
		#we don't need to display it as it will be echoed back to each client
		#including us
		new_text = self.text_entry.get_text()
		self.text_entry.set_text("")
		message = "{0} says: {1}\n".format(self.username, new_text)
		self.network.send(message)

	def graceful_quit(self, widget):
		#when application is closed, tell gtk to quit, then tell the server
		#we are quitting and to clean up the network
		gtk.main_quit()
		self.network.send("QUIT")
		self.network.tidy_up()

class Networking():
	def __init__(self, window, username, server, port):
		#setup the networking class
		self.window = window
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.connect((server, port))
		self.listening = True

		#tell the server that a new user has joined
		self.send("USERNAME {0}".format(username))

	def listen(self):
		#start the listening thread
		self.listen_thread = threading.Thread(target=self.listener)

		#stop the child thread from keeping the application open
		self.listen_thread.daemon = True
		self.listen_thread.start()

	def send(self, message):
		#send a message to the server
		print "Sending: {0}".format(message)
		try:
			self.socket.sendall(message)
		except socket.error:
			print "Unable to send message"

	def tidy_up(self):
		#used to clean up
		self.listening = False
		self.socket.close()

		#we wont see this if it's us that's quitting as 
		#the window will be gone shortly
		gobject.idle_add(self.window.add_text, "Server has quit. \n")

	def handle_msg(self, data):
		if data == "QUIT":
			#server is quitting
			self.tidy_up()
		elif data == "":
			#server has probably quit unexpectedly
			self.tidy_up()
		else:
			#tell the gtk thread to add some text when it is ready
			gobject.idle_add(self.window.add_text, data)

#main program
if __name__ == "__main__":
	#create an isntance of the main window and start the gtk main loop
	MainWindow()
	gtk.main()





























