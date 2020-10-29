![MINOTAUR LOGO](./minotaur/static/assets/static/images/logo_large.png?raw=true)

# Minotaur
Custom dashboard to display email sending statistics, obtained via APIs from email services providers such as **Mailgun**, **Elastic Email**, and **AWS** (soon to be added).

Web app runs on **Django** using a **PostgreSQL** database.
Task processor runs on **Celery** on a remote Kubernetes cluster.

![MINOTAUR DASHBOARD](./minotaur/static/assets/static/images/system_screenshot.png?raw=true)

## Table of contents
1. [Requirements](#requirements)
1. [Installation and Usage](#installation-and-usage)
1. [How it works](#how-it-works)
1. [Database structure](#database-structure)
1. [APIs](#apis)
1. [Service files for the main server](#Service-files-for-the-main-server)

## Requirements
- [x] Postgres (12)
- [x] Redis (5)
- [x] Squid
- [x] Git
- [x] python/pip (3.6)


## Installation and Usage
Clone this repo on /home/minotaur
```
git clone https://gitlab.com/guidito_ito/minotaur-main.git
```

Create a virual enviroment for the project
```
pip3 install virtualenv
virtualenv -p python3 venv
cd venv
source bin/activate
```

Install requirements.txt with the virtual enviroment activated
```
pip3 install -r /path/to/requirements.txt
```

#### Install postgres
A sepparate server is running in production with the postgres database.
Tasks generate intense CPU processing so it has been offloaded from the main server.
In order to install follow the steps below

```
Follow this guide https://computingforgeeks.com/how-to-install-postgresql-12-on-centos-7/

Make sure to listen on private IP for production, or as needed on development/local on postgresql.conf
on pg_hba.conf you will need to allow authentication as well

service postgresql-12 enable
service postgresql-12 start
```

A database backup is available on request. 

Import with... (may need to create the database or users first depending on backup version) and enable/start the service

```
su postgres
psql < minotaur.backup
```

#### Migrate database
The database is required to be created previously.

```
python3 /path/to/manage.py makemigrations
python3 /path/to/manage.py migrate
```

#### Install Redis
```
Follow this guide https://www.linuxtechi.com/install-redis-server-on-centos-8-rhel-8/

Make sure to requirepass on redis.conf and listen on private IP for production, or as needed on development/local.
Private IP on production is on DigitalOceans VPN and can connect to k8s

Make sure to service redis enable
```

#### Celery

Celery is installed on a sepparate instance using https://github.com/guidosanchez/minotaur-worker

#### Config crons

Crons are not required. Scheduled tasks are taken care of by Celery Beat on the Kubernetes Cluster

#### Squid

Squid proxy is required in order for the workers and celery beat on the Kubernetes cluster can communicate to external APIs using the static IP on the main server.
Here is an example config file from the production server. 
On development, you can use it as long as you allow the IP on the localnet ACL.
Note on the file below we add DigitalOcean's network to the allowed list.

```
acl localnet src 0.0.0.1-0.255.255.255  # RFC 1122 "this" network (LAN)
acl localnet src 10.0.0.0/8             # **Digital Ocean local private network (LAN)**
acl localnet src 100.64.0.0/10          # RFC 6598 shared address space (CGN)
acl localnet src 169.254.0.0/16         # RFC 3927 link-local (directly plugged) machines
acl localnet src 172.16.0.0/12          # RFC 1918 local private network (LAN)
acl localnet src 192.168.0.0/16         # RFC 1918 local private network (LAN)
acl localnet src fc00::/7               # RFC 4193 local private network range
acl localnet src fe80::/10              # RFC 4291 link-local (directly plugged) machines

acl SSL_ports port 443
acl Safe_ports port 80          # http
acl Safe_ports port 443         # https
acl CONNECT method CONNECT

http_access deny !Safe_ports
http_access deny CONNECT !SSL_ports
http_access allow localhost manager
http_access deny manager
http_access allow SSL_ports
http_access allow localnet
http_access allow localhost
http_access deny all

http_port 3128

coredump_dir /var/spool/squid

refresh_pattern ^ftp:           1440    20%     10080
refresh_pattern ^gopher:        1440    0%      1440
refresh_pattern -i (/cgi-bin/|\?) 0     0%      0
refresh_pattern .               0       20%     4320

```

After changing the config, enable and start the service 

```
service squid enable
service squid start
```


#### Flower

We use flower to monitor the *Celery* queue. It needs to be installed with the web app.
The requirements file includes the files, just make sure to enable the service.
Make sure to add user:password to basic_auth below

```
[Unit]
Description=flower daemon
After=network.target

[Service]
User=minotaur
Group=nginx
WorkingDirectory=/home/minotaur/minotaur-main/minotaur
ExecStart=/home/minotaur/venv/bin/celery flower \
                                -A minotaur \
                                --port=8000 \
                                --basic_auth=USER:PASSWORD

[Install]
WantedBy=multi-user.target

```


#### Nginx

Used as reverse proxy. Should serve gunicorn and flower. 
At the moment flower is not completely integrated.
In production the server listens on 80 and 443. 
First install normally on port 80 and then use certbot to validate the domain and enable HTTPS automatically.

```
 server {
        server_name admin.totalcomsystems.com;
        listen 80;

        location = /favicon.ico { access_log off; log_not_found off; }
         location /static/ {
                root /home/minotaur/minotaur-main/minotaur;
        }

        location / {
                proxy_set_header Host $http_host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
                proxy_pass http://unix:/home/minotaur/minotaur-main/minotaur/minotaur.sock;
        }

    location /flower/ {
        rewrite ^/flower/(.*)$ /$1 break;
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
    }
}
```

## How it works
The main goal of this project is to obtain Email Sending Statistics from different [ESPs](https://en.wikipedia.org/wiki/Email_service_provider_(marketing)).
Each ESP has its own API to obtain the data from.

Key metrics are pulled and processed if necessary. Some of them include deliveries, bounces and complaints.
Metrics are requested by sending domain. The goal is knowing how well the domain performs while sending emails.
Some metrics are obtained raw from delivery logs and processed by workers on a Kubernetes cluster.
Once processed, the results are uploaded to the app's database with daily results.

Other important metrics involve *revenue*. 
At the moment it is obtained from [HasOffers/Tune](https://developers.tune.com/network/) only but more could be added later.
Depending on the requirements the Tune API can be for network or affiliate, each has its own endpoint and methods.

The app allows an admin to create teams with owners and users. 
The idea is for them to be able to see how well their campaigns are performing.

![MINOTAUR DASHBOARD](./minotaur/static/assets/static/images/minotaur_structure.png?raw=true)

## Database structure
![MINOTAUR LOGO](./minotaur/static/assets/static/images/DER.png?raw=true)
## APIs

From these email service providers we obtain all the information from the sending domains that we need to display statistics.
If necessary, the information is processed and then saved to the database.

#### Mailgun
Docs can be found on https://documentation.mailgun.com/en/latest/api_reference.html

#### Elastic Email
Docs can be found on https://api.elasticemail.com/public/help
## Service files for the main server

#### Minotaur.service

/etc/sysctl/system/minotaur.service
```
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=minotaur
Group=nginx
WorkingDirectory=/home/minotaur/minotaur-main/minotaur
ExecStart=/home/minotaur/venv/bin/gunicorn --workers 3 --timeout 500 \
        --bind unix:/home/minotaur/minotaur-main/minotaur/minotaur.sock \
        minotaur.wsgi:application

[Install]
WantedBy=multi-user.target
```
Make sure venv and paths in general match this service file and that the credentials for postgres and redis on the project settings.py match the ones on the service file.

#### Enable and start gunicorn
```
systemctl daemon-reload
systemctl start minotaur
```
