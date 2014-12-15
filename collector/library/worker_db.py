# -*- coding: utf-8 -*-
import os, sys, logging, datetime, json, base64, sqlite3

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import redis
from multiprocessing import TimeoutError
from datetime import timedelta

base_path = os.path.dirname(os.path.abspath(__file__))
redis_db = None
db_cursor = None
db_connexion = None

def get_current_date():
	logging.basicConfig(filename=base_path + '/log/collector.log',level=logging.DEBUG, format='%(asctime)s.%(msecs)d %(levelname)s %(module)s - %(funcName)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

	try:
		current_date = {}
		current_date["now"] = datetime.datetime.now()
		return current_date
	except:
		logging.error("Unexpected error in get_current_date: %s" %(sys.exc_info()[0]))
		return None

def save_warning_in_redis(key, value, redis_db):
	logging.basicConfig(filename=base_path + '/log/collector.log',level=logging.DEBUG, format='%(asctime)s.%(msecs)d %(levelname)s %(module)s - %(funcName)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

	try:
		logging.debug("key / value: %s / %s" %(key, value))
		redis_db.set(key, value)
		redis_db.expire(key, timedelta(days=2))
	except:
		logging.error("Unexpected error in save_publich_warning_in_redis: %s" %(sys.exc_info()[0]))

def save_warning_in_sqlite(sql, db_connexion, db_cursor):
	logging.basicConfig(filename=base_path + '/log/collector.log',level=logging.DEBUG, format='%(asctime)s.%(msecs)d %(levelname)s %(module)s - %(funcName)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
	try:
		logging.debug("sql %s" %(sql))
		db_cursor.execute(sql)
		db_connexion.commit()
	except:
		logging.error("Unexpected error in save_warning_in_sqlite: %s" %(sys.exc_info()[0]))

def write_to_redis(communication_queue, config):
	logging.basicConfig(filename=base_path + '/log/collector.log',level=logging.DEBUG, format='%(asctime)s.%(msecs)d %(levelname)s %(module)s - %(funcName)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

	#Initialise redis communication
	try:
		redis_db = redis.StrictRedis(host=config["redis"]["ip"], port=config["redis"]["port"], db=0)
		logging.info("redis connexion: OK")
	except:
		logging.error("Unexpected error in redis connexion: %s" %(sys.exc_info()[0]))
		sys.exit(1)

	#Initialise sqlite3 local db
	try:
		db_connexion = sqlite3.connect(os.path.dirname(base_path) + '/collector.db')
		db_cursor = db_connexion.cursor()
		db_cursor.execute('''CREATE TABLE IF NOT EXISTS messages (date DATETIME, agent_name text, function text, value text)''')
		logging.info("sqlite3 initilisation: OK")
	except:
		logging.error("Unexpected error in sqlite3: %s" %(sys.exc_info()[0]))
		sys.exit(1)

	try:
		while True:
			message = communication_queue.get(0.1)
			#logging.debug(message)
			value = json.loads(message)
			try:
				value["value"] = base64.b64decode(value["value"])
			except TypeError:
				pass
			else:
				logging.error("Unexpected error in write_to_redis: %s" %(sys.exc_info()[0]))

			current_date = get_current_date()
			save_warning_in_redis(str(current_date["now"]) + ":" + value["agent"] + ":" + value["function"], value["value"], redis_db)
			save_warning_in_sqlite("INSERT INTO messages VALUES ('%s','%s','%s','%s')" % (current_date["now"], value["agent"], value["function"], value["value"]), db_connexion, db_cursor)

	except TimeoutError:
		logging.error("TimeoutError to get data in queue.")
		pass
	except KeyboardInterrupt:
		sys.exit(0)
	except:
		logging.error("Unexpected error in write_to_redis: %s" %(sys.exc_info()[0]))


# def communication(communication_queue, worker_id, worker_parameters):
# 	logging.basicConfig(filename=base_path + '/log/agent.log',level=logging.DEBUG, format='%(asctime)s.%(msecs)d %(levelname)s %(module)s - %(funcName)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

# 	#Open websocket connexion.
# 	try:	
# 		ws = create_connection(worker_parameters["ws"])
# 		logging.info("The process websocket_client is connected.")
# 	except:
# 		logging.error("Unable to perform the websocket connexion.")
# 		pass

# 	while True:
# 		try:
# 			flux = communication_queue.get(0.1)
			
# 			try:
# 				ws.send(flux)
# 				logging.debug("Send data: %s" %(flux))
# 				result =  ws.recv()
# 				logging.debug("Receive data: %s" %(result))
# 			except:
# 				#In case of the websocket is close, retry a new connexion.
# 				try:
# 					logging.info("Web socket is closed, I retry to connect it: %s" %(worker_parameters["ws"]))
# 					ws = create_connection(worker_parameters["ws"])
# 					ws.send(flux)
# 					result = ws.recv()
# 				except:
# 					logging.error("WebSocket can't re send data.")
# 					pass

# 		except TimeoutError:
# 			logging.error("TimeoutError to get data in queue.")
# 			pass
# 		except KeyboardInterrupt:
# 			sys.exit(0)

# 	ws.close()
