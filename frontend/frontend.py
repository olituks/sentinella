#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys, logging, json, base64, platform, datetime, multiprocessing, time, uuid

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/library')

import redis
import tornado.web, tornado.websocket, tornado.ioloop
from multiprocessing import Process
from daemonize import Daemon
from start_web2py import Web2PyProcess

#-----------------------------------

base_path = os.path.dirname(os.path.abspath(__file__))
redis_db = None
config = None
web2py_process = None
host_name = platform.node()

def get_current_date(offset):
	try:
		current_date = {}
		current_date["now"] = datetime.datetime.now()
		if offset < 0:
			current_date["now"] = current_date["now"] - datetime.timedelta(seconds=abs(offset))
		else:
			current_date["now"] = current_date["now"] + datetime.timedelta(seconds=abs(offset))

		current_date["today"] = datetime.date.today()
		current_date["M"] = '%02d' % current_date["today"].month
		current_date["D"] = '%02d' % current_date["today"].day
		current_date["YYYY"] = current_date["today"].year
		current_date["h"] = '%02d' % current_date["now"].hour
		current_date["m"] = '%02d' % current_date["now"].minute
		current_date["s"] = '%02d' % current_date["now"].second
		
		return current_date
	except:
		logging.error("Unexpected error in get_current_date: %s" %(sys.exc_info()[0]))
		return None

def worker_communication_client(ws):
	logging.basicConfig(filename=base_path + '/log/frontend.log',level=logging.DEBUG, format='%(asctime)s.%(msecs)d %(levelname)s %(module)s - %(funcName)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

	ws.write_message("You are connected in frontend")
	my_id = uuid.uuid1()
	ws.write_message("Your uuid:" + str(my_id))
	
	while True:
		try:
			current_date = get_current_date(-60)
			logging.debug(str(my_id) + " | " + str(current_date["today"]) + " " + str(current_date["h"]) + ":" + str(current_date["m"]))
			#2014-11-10 06:54:09.284529:stal0008:cpu_count
			all_keys = redis_db.keys("%s*:*:cpu_count*" %(str(current_date["today"]) + " " + str(current_date["h"]) + ":" + str(current_date["m"])))
			# logging.debug(str(my_id) + " | " + str(all_keys))
			
			result = []
			for index in all_keys:
				my_json = {}
				my_json["key"] = index
				my_json["value"] = redis_db.get(index)
				result.append(my_json)
				
			ws.write_message(json.dumps(result))
		except:
			logging.error("Unexpected error in worker_communication_client: %s" %(sys.exc_info()[0]))

		time.sleep(60)

class WebSocketHandler(tornado.websocket.WebSocketHandler):

	def check_origin(self, origin):
		return True

	def open(self):

		q = multiprocessing.Process(target=worker_communication_client, args=(self,))
		q.start()

	def on_message(self, message):
		try:
			logging.debug("Receive this message: %s" %(str(message)))
			#2014-11-10 06:54:09.284529:stal0008:cpu_count
			all_keys = redis_db.keys("%s*:*:cpu_count" %(str(message)))
			result = []
			for index in all_keys:
				my_json = {}
				my_json["key"] = index
				my_json["value"] = redis_db.get(index)
				result.append(my_json)
				
			self.write_message(json.dumps(result))
		except:
			logging.error("Unexpected error in WebSocketHandler: %s" %(sys.exc_info()[0]))

	# agent disconnected
	def on_close(self):
		logging.info('Client disconnected')

class MyDaemon(Daemon):
	def run(self):
		try:

			#start tornado webserver
			#unsecure tornado server
			application.listen(config["internal_ws"]["port"])
			logging.info('Frontend listen on %s port' %(config["internal_ws"]["port"]))

			#secure tornado server
			#http_server = tornado.httpserver.HTTPServer(application, ssl_options={
			#	"certfile": "/var/pyTest/keys/ca.csr",
			#	"keyfile": "/var/pyTest/keys/ca.key",
			#})
			#http_server.listen(443)

			tornado.ioloop.IOLoop.instance().start()

			# while True:
			# 	time.sleep(1)

		except:
			logging.error("Unexpected error in MyDaemon: %s" %(sys.exc_info()[0]))

class JsonHandler(tornado.web.RequestHandler):
	def set_default_headers(self):
		# VM OK
		#self.set_header("Access-Control-Allow-Origin", "http://192.168.1.130:8000")

		# local OK
		self.set_header("Access-Control-Allow-Origin", "http://127.0.0.1:8000")
		self.set_header("Content-Type", "application/json; charset=utf-8")

	@tornado.web.asynchronous
	def get(self):
		try:
			# logging.debug("in get function")
			# self.write("Hello, world")
			# logging.debug("send HelloWorld...")
			# self.finish()

			message = self.get_argument("message", default="")
			logging.debug("Receive this message: %s" %(str(message)))
			#2014-11-10 06:54:09.284529:stal0008:cpu_count
			all_keys = redis_db.keys("%s*:*:cpu_count" %(str(message)))
			result = []
			for index in all_keys:
				my_json = {}
				my_json["key"] = index
				my_json["value"] = redis_db.get(index)
				result.append(my_json)
				
			self.write(json.dumps(result))
			self.finish()
		except:
			logging.error("Unexpected error in JsonHandler - get: %s" %(sys.exc_info()[0]))

application = tornado.web.Application([
    (r"/*", WebSocketHandler),
    (r"/get_json/", JsonHandler),
])

if __name__ == '__main__':

	logging.basicConfig(filename=base_path + '/log/frontend.log',level=logging.DEBUG, format='%(asctime)s.%(msecs)d %(levelname)s %(module)s - %(funcName)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

	#Load the config file
	try:
		stream = open(base_path + '/config.json', 'r')
		config = json.load(stream)
		stream.close()
		logging.info("config file %s load: OK" %(base_path + '/config.json'))
	except:
		logging.error("Unexpected error in load config file: %s" %(sys.exc_info()[0]))
		sys.exit(1)

	#Initialise redis communication
	try:
		logging.info("redis connection : %s:%s" %(config["redis"]["ip"], config["redis"]["port"]))
		redis_db = redis.StrictRedis(host=config["redis"]["ip"], port=config["redis"]["port"], db=0)
		logging.info("redis connexion: OK")
	except:
		logging.error("Unexpected error in redis connexion: %s" %(sys.exc_info()[0]))
		sys.exit(1)

	#test if redis server is available
	# try:
	#	response = rs.client_list()
	# except redis.ConnectionError:
	# 	your error handlig code here

	daemon = MyDaemon('/tmp/daemon-frontend.pid')
	web2pyprocess = Web2PyProcess()
	if len(sys.argv) == 2:
		if 'start' == sys.argv[1]:
			logging.info('Start the application')
			web2pyprocess.start()
			daemon.start()
		elif 'stop' == sys.argv[1]:
			logging.info('Stop the application')
			web2pyprocess.stop()
			daemon.stop()
		elif 'restart' == sys.argv[1]:
			logging.info('Restart the application')
			web2pyprocess.restart()
			daemon.restart()
		else:
			logging.info('Unknown command!')
			print "Unknown command"
			sys.exit(2)
		sys.exit(0)
	else:
		print "usage: %s start|stop|restart" % sys.argv[0]
		sys.exit(2)