#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys, tornado.web, tornado.websocket, tornado.ioloop, multiprocessing, json, base64, sqlite3, logging, redis, datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/library')

from datetime import timedelta
from daemonize import Daemon
from multiprocessing import Queue, TimeoutError

#-----------------------------------

base_path = os.path.dirname(os.path.abspath(__file__))
redis_db = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)

db_connexion = sqlite3.connect(base_path + '/collector.db')
db_cursor = db_connexion.cursor()
db_cursor.execute('''CREATE TABLE IF NOT EXISTS messages (date DATETIME, agent_name text, function text, value text)''')

def worker_db(communication_queue):
	while True:
		message = communication_queue.get(0.1)
		value = json.loads(message)
		try:
			value["value"] = base64.b64decode(value["value"])
		except TypeError:
			pass
		else:
			logging.error("Unexpected error in worker_db: %s" %(sys.exc_info()[0]))

		current_date = get_current_date()
		save_warning_in_redis(str(current_date["now"]) + ":" + value["agent"] + ":" + value["function"], value["value"])
		save_warning_in_sqlite("INSERT INTO messages VALUES ('%s','%s','%s','%s')" % (current_date["now"], value["agent"], value["function"], value["value"]))

def get_current_date():
	try:
		current_date = {}
		current_date["now"] = datetime.datetime.now()
		return current_date
	except:
		logging.error("Unexpected error in get_current_date: %s" %(sys.exc_info()[0]))
		return None

def save_warning_in_redis(key, value):
	try:
		#logging.debug("key / value: %s / %s" %(key, value) )
		redis_db.set(key, value)
		redis_db.expire(key, timedelta(days=2))
	except:
		logging.error("Unexpected error in save_publich_warning_in_redis: %s" %(sys.exc_info()[0]))

def save_warning_in_sqlite(sql):
	try:
		#logging.debug("sql %s" %(sql))
		db_cursor.execute(sql)
		db_connexion.commit()
	except:
		logging.error("Unexpected error in save_warning_in_sqlite: %s" %(sys.exc_info()[0]))

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

		logging.info('    Received: ' + message)
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

class JsonHandler(tornado.web.RequestHandler):
	@tornado.web.asynchronous
	def get(self):
		self.write("Hello, world")
		self.finish()

class MyDaemon(Daemon):
	def run(self):
		try:
			#start a worker to save all messages in local db
			p = multiprocessing.Process(target=worker_db, args=(communication_queue,))
			p.start()

			#start tornado webserver

			#unsecure tornado server
			application.listen(8888)
			logging.info('Collector listen on 8888 port')

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
    (r"/", WebSocketHandler),
    (r"/get_json/", JsonHandler),
])

if __name__ == "__main__":

	logging.basicConfig(filename=base_path + '/log/collector.log',level=logging.DEBUG)

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


