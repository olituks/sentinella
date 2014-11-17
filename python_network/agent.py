#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys, time, logging, yaml

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/library')

from daemonize import Daemon
from multiprocessing import Process, Queue, TimeoutError
from websocket_client import * 
from psutil_worker import *

#-----------------------------------

base_path = os.path.dirname(os.path.abspath(__file__))

#Create a worker for each entry in yaml config file
class Worker(Process):
	def __init__(self, communication_queue, worker_id, function, worker_parameters):
		self.communication_queue = communication_queue
		self.worker_id = worker_id or None
		self.function = function
		self.worker_parameters = worker_parameters
		super(Worker, self).__init__()
	
	def run(self):
		method_name = self.function
		possibles = globals().copy()
		possibles.update(locals())
		
		try:
			method = possibles.get(method_name)(self.communication_queue, self.worker_id, self.worker_parameters)    
		except:
			pass

class MyDaemon(Daemon):
	def run(self):
		try:
			#Load the config file
			stream = open(base_path + '/worker_config.yaml', 'r')
			config = yaml.load(stream)
			stream.close()

			#Initialise interprocess queue
			communication_queue = Queue()
			
			#Start subprocess
			worker_count = 0
			for worker_function in config:
				worker_parameters = config[worker_function]
				worker = Worker(communication_queue, worker_count, worker_function, worker_parameters)
				worker.start()
				logging.info('start worker ' + worker_function)
				worker_count = worker_count + 1

			while True:
				time.sleep(1)
		except:
			logging.error("Unexpected error in MyDaemon: %s" %(sys.exc_info()[0]))

if __name__ == '__main__':

	logging.basicConfig(filename=base_path + '/log/agent.log',level=logging.DEBUG)

	daemon = MyDaemon('/tmp/daemon-agent.pid')
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
