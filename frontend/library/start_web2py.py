#!/usr/bin/env python

import sys, os, psutil, subprocess as sub, logging, time
from signal import SIGTERM

base_path = os.path.dirname(os.path.abspath(__file__))

class Web2PyProcess():
	def __init__(self):
		self.pidfile = base_path +"/web2py/web2py.pid"
		logging.basicConfig(filename=base_path + '../log/frontend.log',level=logging.DEBUG, format='%(asctime)s.%(msecs)d %(levelname)s %(module)s - %(funcName)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

	def start(self):
		# Check for a pidfile to see if the daemon already runs
		try:
			pf = file(self.pidfile,'r')
			pid = int(pf.read().strip())
			pf.close()
		except IOError:
			pid = None
	
		if pid:
			message = "Web2Py pidfile %s already exist. Daemon already running?\n"
			sys.stderr.write(message % self.pidfile)
			sys.exit(1)

		web2py_process = sub.Popen(["nohup","python", base_path +"/web2py/web2py.py", "-a", "OLI32tuks", "-i", "0.0.0.0", "-p" ,"8000"],stdout=None,stderr=None)
		logging.info("Web2Py pid: %s" %(str(web2py_process.pid)))
		file(self.pidfile,'w+').write("%s\n" % web2py_process.pid)

	def stop(self):
		# Get the pid from the pidfile
		try:
			pf = file(self.pidfile,'r')
			pid = int(pf.read().strip())
			pf.close()
		except IOError:
			pid = None
	
		if not pid:
			message = "pidfile %s does not exist. Daemon not running?\n"
			sys.stderr.write(message % self.pidfile)
			return # not an error in a restart

		# Try killing the daemon process	
		try:
			while 1:
				self.kill_child_processes(pid)
				os.kill(pid, SIGTERM)
				time.sleep(0.1)
		except OSError, err:
			err = str(err)
			if err.find("No such process") > 0:
				if os.path.exists(self.pidfile):
					os.remove(self.pidfile)
			else:
				print str(err)
				sys.exit(1)

	def restart(self):
		"""
		Restart the daemon
		"""
		self.stop()
		self.start()

	def kill_child_processes(self, parent_pid):
	    try:
	    	p = psutil.Process(parent_pid)
	    except psutil.NoSuchProcess:
	    	return
	    
	    child_pid = p.children(recursive=True)
	    for pid in child_pid:
	    	os.kill(pid.pid, SIGTERM)      