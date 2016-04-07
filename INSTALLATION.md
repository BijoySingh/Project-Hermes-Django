# Installations

- Install required software

```lang=bash
sudo apt-get update
sudo apt-get install python3-pip python3.5-dev libpq-dev postgresql postgresql-contrib memcached \
libjpeg8 libjpeg62-dev libfreetype6 libfreetype6-dev libxml2-dev libxslt1-dev libffi-dev nodejs \
nodejs-legacy npm
```

- Create a postgresql user and database. Taken from
[postgresql wiki](https://wiki.postgresql.org/wiki/First_steps).

```lang=bash
sudo su - postgres
psql # Now you must be in postgresql command line mode

CREATE DATABASE project_hermes;
CREATE USER project_hermes WITH PASSWORD 'project_hermes';
GRANT ALL PRIVILEGES ON DATABASE project_hermes TO project_hermes;
\q
exit
```

- Install configured lint tools
```lang=bash
sudo npm install -g csslint jsonlint jscs
```
