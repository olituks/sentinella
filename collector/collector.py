#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys, json, base64, logging, datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/library')

import tornado.web, tornado.websocket, tornado.ioloop
from multiprocessing import Process, Queue, TimeoutError
from datetime import timedelta
from daemonize import Daemon
from worker_db import write_to_redis

#-----------------------------------

base_path = os.path.dirname(os.path.abspath(__file__))
config = None

#Create a worker
class Worker(Process):
	def __init__(self, communication_queue, function):
		self.communication_queue = communication_queue
		self.function = function
		self.config = config
		super(Worker, self).__init__()
	
	def run(self):
		method_name = self.function
		possibles = globals().copy()
		possibles.update(locals())
		
		try:
			method = possibles.get(method_name)(self.communication_queue, self.config)  
		except:
			pass

class WebSocketHandler(tornado.websocket.WebSocketHandler):
	# the agent connected

	participants = set()

	def open(self):
		logging.info('New client connected')

		# test de identity from the requester

		self.write_message("You are connected with the connector")

		#add ws participant in a queue for broadcasting
		self.participants.add(self)

	# the agent sent the message
	def on_message(self, message):

		# logging.info('    Received: ' + message)
		communication_queue.put(message)
		
		#broadcast message to all participant
		for p in self.participants.copy():
			try:
				p.write_message(message)
			except:
				logging.error("Unexpected error in WebSocketHandler - on_message: %s" %(sys.exc_info()[0]))
				#if the message can't be push in the ws, remove the ws and close them
				self.participants.remove(p)
				p.close()

	# agent disconnected
	def on_close(self):
		logging.info('Client disconnected')
		self.participants.remove(self)

class MyDaemon(Daemon):
	def run(self):
		try:
			#start a worker to save all messages in local db
			worker = Worker(communication_queue, "write_to_redis")
			worker.start()

			#start tornado webserver
			#unsecure tornado server
			application.listen(config["internal_ws"]["port"])
			logging.info('Collector listen on %s port' %(config["internal_ws"]["port"]))

			#secure tornado server
			#http_server = tornado.httpserver.HTTPServer(application, ssl_options={
			#	"certfile": "/var/pyTest/keys/ca.csr",
			#	"keyfile": "/var/pyTest/keys/ca.key",
			#})
			#http_server.listen(443)

			tornado.ioloop.IOLoop.instance().start()

		except:
			logging.error("Unexpected error in MyDaemon: %s" %(sys.exc_info()[0]))

application = tornado.web.Application([
    (r"/", WebSocketHandler)
])

if __name__ == "__main__":

	logging.basicConfig(filename=base_path + '/log/collector.log',level=logging.DEBUG, format='%(asctime)s.%(msecs)d %(levelname)s %(module)s - %(funcName)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

	#Load the config file
	try:
		stream = open(base_path + '/config.json', 'r')
		config = json.load(stream)
		stream.close()
		logging.info("config file %s load: OK" %(base_path + '/config.json'))
	except:
		logging.error("Unexpected error in load config file: %s" %(sys.exc_info()[0]))
		sys.exit(1)

	communication_queue = Queue()

	daemon = MyDaemon('/tmp/daemon-collector.pid')
	if len(sys.argv) == 2:
		if 'start' == sys.argv[1]:
			logging.info('Start the application')
			daemon.start()
		elif 'stop' == sys.argv[1]:
			logging.info('Stop the application')
			daemon.stop()
		elif 'restart' == sys.argv[1]:
			logging.info('Restart the application')
			daemon.restart()
		else:
			logging.info('Unknown command!')
			print "Unknown command"
			sys.exit(2)
		sys.exit(0)
	else:
		print "usage: %s start|stop|restart" % sys.argv[0]
		sys.exit(2)


