# -*- coding: utf-8 -*-
import os, sys, logging
from websocket import create_connection
from multiprocessing import TimeoutError

base_path = os.path.dirname(os.path.abspath(__file__))

def communication(communication_queue, worker_id, worker_parameters):
	logging.basicConfig(filename=base_path + '/log/agent.log',level=logging.DEBUG, format='%(asctime)s.%(msecs)d %(levelname)s %(module)s - %(funcName)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

	#Open websocket connexion.
	try:	
		ws = create_connection(worker_parameters["ws"])
		logging.info("The process websocket_client is connected.")
	except:
		logging.error("Unable to perform the websocket connexion - %s" %(worker_parameters["ws"]))
		pass

	while True:
		try:
			flux = communication_queue.get(0.1)
			
			try:
				ws.send(flux)
				logging.debug("Send data: %s" %(flux))
				result =  ws.recv()
				logging.debug("Receive data: %s" %(result))
			except:
				#In case of the websocket is close, retry a new connexion.
				try:
					logging.info("Web socket is closed, I retry to connect it: %s" %(worker_parameters["ws"]))
					ws = create_connection(worker_parameters["ws"])
					ws.send(flux)
					result = ws.recv()
				except:
					logging.error("WebSocket can't re send data.")
					pass

		except TimeoutError:
			logging.error("TimeoutError to get data in queue.")
			pass
		except KeyboardInterrupt:
			sys.exit(0)

	ws.close()
