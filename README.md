sentinelle
==========

"in development" this python application performe a recurrent system surveillance, publish the alerts on a RSS server and display an admin custom dashboard.

![Sentinelle architecture](http://drive.google.com/uc?export=view&id=0B7kQatBvjEOzN1A4OUYzanpBNjA "Sentinelle architecture")

- The application is multitreaded.
- Perform surveliance on UNIX, Linux and Windows operating system.
- The application is composed bu agents, collector and frontend.
- The agents can be customized to perform surveillance. It report warnings via websocket to collector.
- The collector save data provide by all agents in a redis db and local sqlite3 db.
- The frontend server retreive data directly in redis db and provide the web page to the clients.

Currently all the test are made in the same machine 127.0.0.1
Start servers:
- python collector.py start
- python frontend.py start
- python agent.py start

Start client:
the client web page detect if your navigator can use websocket, if not it use a fallback solution.
- cd client
- python -m SimpleHTTPServer
