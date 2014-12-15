# -*- coding: utf-8 -*-
from __future__ import division

import os, sys, logging, json, base64, psutil, platform
import cronus.beat as beat

base_path = os.path.dirname(os.path.abspath(__file__))
host_name = platform.node()

def my_frequency(tick):
	return 1.0 / float(tick)

def psutil_process(communication_queue, worker_id, worker_parameters):
	logging.basicConfig(filename=base_path + '/log/agent.log',level=logging.DEBUG, format='%(asctime)s.%(msecs)d %(levelname)s %(module)s - %(funcName)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

	tick = worker_parameters["tick"]
	warning = {}
	if tick > 0:
		tick = my_frequency(tick)
		beat.set_rate(tick)
		while beat.true():
			for proc in psutil.process_iter():
				try:
					pinfo = proc.as_dict(attrs=['pid', 'name'])
					pinfo = base64.b64encode(json.dumps(pinfo))
				except psutil.NoSuchProcess:
					pass
				else:
					message = {"agent": host_name, "function": "process", "value": pinfo }
					communication_queue.put(json.dumps(message))

			beat.sleep()

def psutil_cpu_count(communication_queue, worker_id, worker_parameters):
	logging.basicConfig(filename=base_path + '/log/agent.log',level=logging.DEBUG, format='%(asctime)s.%(msecs)d %(levelname)s %(module)s - %(funcName)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
	
	tick = worker_parameters["tick"]
	warning = {}
	warning["cpu_count"] = 0
	warning["cpu_count_logical"] = 0
	if tick > 0:
		beat.set_rate(my_frequency(tick))

		while beat.true():
			#Physical CPU
			try:
				pinfo = psutil.cpu_count(logical=False)
				if int(pinfo < worker_parameters["min_cpu"]):
					message = {"agent": host_name, "function": "cpu_count", "value": pinfo}
					communication_queue.put(json.dumps(message))
					
					warning["cpu_count"] = 1
					beat.set_rate(my_frequency(worker_parameters["tick_error"]))
				else:
					if warning["cpu_count"] == 1:
						logging.debug("in solved cpu_count")
						warning["cpu_count"] = 0
						message = {"agent": host_name, "function": "cpu_count", "value": "solved"}
						communication_queue.put(json.dumps(message))
			except:
				logging.error("Unexpected error in psutil_cpu_count - cpu_count: %s" %(sys.exc_info()[0]))
				pass
		
			#Logical CPU
			try:
				pinfo = psutil.cpu_count(logical=True)
				if int(pinfo < worker_parameters["min_logical_cpu"]):
					message = {"agent": host_name, "function": "cpu_count_logical", "value": pinfo}
					communication_queue.put(json.dumps(message))
					
					warning["cpu_count_logical"] = 1
					beat.set_rate(my_frequency(worker_parameters["tick_error"]))
				else:
					if warning["cpu_count_logical"] == 1:
						logging.debug("in solved cpu_count_logical")
						warning["cpu_count_logical"] = 0
						message = {"agent": host_name, "function": "cpu_count_logical", "value": "solved"}
						communication_queue.put(json.dumps(message))
			except:
				logging.error("Unexpected error in psutil_cpu_count - cpu_count_logical: %s" %(sys.exc_info()[0]))
				pass

			beat.sleep()
