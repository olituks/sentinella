#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys, logging, uuid, datetime, time, redis

base_path = os.path.dirname(os.path.abspath(__file__))

#-----------------------------------

redis_db = None

def get_current_date(offset):
	logging.basicConfig(filename=base_path + '/log/frontend.log',level=logging.DEBUG, format='%(asctime)s.%(msecs)d %(levelname)s %(module)s - %(funcName)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

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
	ws.write_message("You uuid:" + str(my_id))
	
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