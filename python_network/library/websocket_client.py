# -*- coding: utf-8 -*-
from websocket import create_connection
from multiprocessing import TimeoutError

def communication(communication_queue, worker_id, worker_parameters):
	#Open websocket connexion.
	try:	
		ws = create_connection(worker_parameters["ws"])
	except:
		pass

	while True:
		try:
			flux = communication_queue.get(0.1)
			
			try:
				ws.send(flux)
				result =  ws.recv()
			except:
				#In case of the websocket is close, retry a new connexion.
				try:
					ws = create_connection(worker_parameters["ws"])
					ws.send(flux)
					result = ws.recv()
				except:
					pass

		except TimeoutError:
			pass
		except KeyboardInterrupt:
			sys.exit(0)

	ws.close()
