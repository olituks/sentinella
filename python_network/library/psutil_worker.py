# -*- coding: utf-8 -*-

from __future__ import division

import psutil
import json
import base64
import cronus.beat as beat

def psutil_process(communication_queue, worker_id, worker_parameters):
	tick = worker_parameters["tick"]
	if tick > 0:
		tick = 1 / tick
		beat.set_rate(tick)
		while beat.true():
			for proc in psutil.process_iter():
				try:
					pinfo = proc.as_dict(attrs=['pid', 'name'])
					pinfo = base64.b64encode(json.dumps(pinfo))
				except psutil.NoSuchProcess:
					pass
				else:
					message = {"agent": "stal0008", "function": "process", "value": pinfo }
					communication_queue.put(json.dumps(message))

			beat.sleep()

def psutil_cpu_count(communication_queue, worker_id, worker_parameters):
	tick = worker_parameters["tick"]
	if tick > 0:
		tick = 1 / tick
		beat.set_rate(tick)

		while beat.true():
			try:
				pinfo = psutil.cpu_count(logical=False)
				if int(pinfo < worker_parameters["min_cpu"]):
					message = {"agent": "stal0008", "function": "cpu_count", "value": pinfo}
					communication_queue.put(json.dumps(message))
			except:
				pass
		
			try:
				pinfo = psutil.cpu_count(logical=True)
				if int(pinfo < worker_parameters["min_logical_cpu"]):
					message = {"agent": "stal0008", "function": "cpu_count", "value": pinfo}
					communication_queue.put(json.dumps(message))
			except:
				pass

			beat.sleep()
