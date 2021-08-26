Readme for future developers
======
This tool is not actively developed anymore (since August 2021). The purpose of this document is to provide an entry point for potential future development.

A quick word on the generality of the tool
-------
First of all, I initially assumed that I was supposed to develop a general tool that could work with different ontologies: You install a general version of the tool on your server
and then upload your own ontology and other configuration files. The dummy data contains the configuration files that are used for our special use case.
However, later that turned out to be irrelevant because the tool would only be used for one purpose with one ontology and the strict distinction between the general tool and the
configuration for the specific use case were not sustained if that would mean significantly more effort.
In particular, the script deploy.sh installs both the general tool and our specific configuration and the template `overview_table.html` is made specifically for our ontology and would not work
with any other because I haven't found a way that users could specify different overview tables without allowing them to upload arbitrary code that would be executed on the server.
Further the tool was never tested with any other configuration and there is no documentation as to what properties an ontology must have to work with the general tool.

Overview
------
todo

Remote access to the webtentacle server
------
Currently, the tool is running on the webtentacle server of the technical faculty of the University Bielefeld. Here is how I accessed it remotely:
1. Access techfak shell via `ssh techfakusername@shell.techfak.de`. See [this guide](https://techfak.net/dienste/remote/shell) on how to set this up.
2. From there, access webtentacle via `ssh webtentacleusername@webtentacle1.techfak.uni-bielefeld.de`. Ask an admin to get you a username and a password.
3. I stored the data for the tool at `~/ratio`.
4. I found [this](https://bashupload.com/) to be the most convenient way to get files to and from the server.

Update workflow
------
Here is what I did when I updated the tool:

1. Make and test changes locally.
2. 1. If the tool is running on the server: In the admin interface, set the admin message to something like
   "The tool will be updated today (01.02.2021) from 20:00 to 00:00. Changes made in that time are not persisted in the database" (if people are actively using it, else skip the admin message). 
   At the specified time download the backup from the admin interface.
   2. If the tool is not running and cannot be started (maybe because the version on the server is broken), access the server, go to `~/ratio/venv/var/ratio-instance` 
      and download the database `ratio.sqlite`.
3. Replace `dummy_db.sqlite` with the database just downloaded from the server, do `flask db-init` and `flask db-add-dummy`, test again with the new database.
   If there is an error in the database itself (maybe the tool accidentally stored an `owl:NamedIndividual` without a `ctro` type or something like that, 
   causing a crash when trying to display the subgraph in the tool), use your favourite SQL tool (e.g. SQLite directly or python with `sqlite3`) to find and fix it.
4. Stop the tool on the server with `pkill gunicorn` and delete everything from the `~/ratio` folder.
5. Install and run the updated tool on the server. See _Deploy with Gunicorn_ in `README.md`.

Loose ends
-------
todo