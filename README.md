sentinella
==========

"in development" this python application performe system surveillance, publish the alerts on a RSS server and admin dashboard.

![Sentinella architecture](http://drive.google.com/uc?export=view&id=0B7kQatBvjEOzN1A4OUYzanpBNjA "Sentinella architecture")

- The application is multitreaded.
- Perform surveliance on UNIX, Linux and Windows operating system.
- The application is composed by agents, collector and frontend.
- The agents can be customized to perform surveillance. It report warnings via websocket to collector.
- The collector save data provide by all agents in a redis db and local sqlite3 db.
- The frontend server retreive data directly in redis db and provide the web page to the clients.

Each part of the application can be split to diferent server or working localy.
Start servers:
- python collector.py start
- python frontend.py start
- python agent.py start

Start client:
the client web page detect if your navigator can use websocket, if not it use a fallback solution.
- http://<frontend server name or IP>/sentinella
