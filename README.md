
# Coding Challenges Platform


A good reference for building this app is:
https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world

## Installation
To run the worker you'll need:
.* redis-server
(on Debian-like Linux distribution install using: `sudo apt-get install redis-server`)

To run the server you'll need some Python dependencies:
.* flask (1.0.2)
.* flask_sqlalchemy (2.3.2)
.* flask_migrate (2.3.0)
.* flask_login (0.4.1)
.* rq (0.12.0)
.* flask_wtf (0.14.2)
.* Jinja2>=2.10 (from flask) (2.10)
.* click>=5.1 (from flask) (7.0)
.* Werkzeug>=0.14 (from flask) (0.14.1)
.* itsdangerous>=0.24 (from flask) (1.1.0)
.* SQLAlchemy>=0.8.0 (from flask_sqlalchemy) (1.2.14)
.* alembic>=0.7 (from flask_migrate) (1.0.2)
.* redis>=2.7.0 (from rq) (2.10.6)
.* WTForms (from flask_wtf) (2.2.1)
.* MarkupSafe>=0.23 (from Jinja2>=2.10->flask) (1.1.0)
.* Mako (from alembic>=0.7->flask_migrate) (1.0.7)
.* python-editor>=0.3 (from alembic>=0.7->flask_migrate) (1.0.3)
.* python-dateutil (from alembic>=0.7->flask_migrate) (2.7.5)
.* six>=1.5 (from python-dateutil->alembic>=0.7->flask_migrate) (1.11.0)
(on my machine I installed using `pip install flask flask_sqlalchemy flask_migrate flask_login rq flask_wtf` #- you may do it in a `virtualenv`!)


## Setup

I suggest using lighttpd to run the server. Unfortunately, I do not add the settings here. I am normally run the server in a safe environment with debug settings.

1. Create needed folders:
.* `mkdir upload tmp`
2. Create private key and certificate (in a real life scenario you'd have to get them signed somewhere, in a prototype case do and accept in your browser):
.* ```openssl req \
       -newkey rsa:2048 -nodes -keyout key.key \
       -x509 -days 365 -out key.crt```


### Settings for a safer judging environment:

1. Create another user to run the worker:
.* `sudo useradd judge`
2. Create another group and set to the worker and the server:
.* `sudo groupadd codingchallenges`
3. Set the server and the worker to the new group:
.* `sudo usermod -a -G codingchallenges judge`
.* `sudo usermod -a -G codingchallenges <serveruser>`
4. Set permissions inside the server folder (so the judge can get the problem files):
.* `chgrp -R codingchallenges *`
.* `chmod -R 750 *`
5. Limit the internet access on the judge (this is a temporary setting, you need to set a global setting if deploying):
```
sudo su

iptables --append OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# create a new chain
iptables --new-chain chk_apache_user

# use new chain to process in the judge
iptables -A OUTPUT -m owner --uid-owner judge -j chk_apache_user #note the judge here

# allow the judge to use redis
iptables -A chk_apache_user -p tcp --syn -d 127.0.0.1 --dport 6379  -j RETURN

# reject everything else and stop hackers downloading code into our server
iptables -A chk_apache_user -j REJECT

# reference: https://www.cyberciti.biz/tips/block-outgoing-network-access-for-a-single-user-from-my-server-using-iptables.html
```
This setting will make the judge safer when executing the submitted code as it won't be able to access the internet and possibly download other unsafe code.
6. Do more: these settings are a minimum. It is adequate to have other types of sandboxing when executing external code. For example, block access to libraries. Also a proper logging of activity and files is a must.


## Run
.* NOTE: THE USER `hue` WILL BE AUTOMATICALLY SET AS ADMIN WHEN OPENING THE PAGE `/admin`
.* `python worker.py`
.* `python server.py`


## Create more problems:
The judge command accept commands like this:
.* `cat {input_file} | Rscript {script_file} > {tempfile}; diff --strip-trailing-cr {tempfile} {res_file}`

## TO-DOs:
1. hanging files:
..* problem files
..* test cases
..* UserProblemSubmission
2. forms validation:
..* do not let remove let a file that is associated somewhere (as descrition or testcase) be removed
3. cronjob:
..* update each user rank (each 5 minutes or something)
..* compute index, each section and each problem so it is not queried from the db each time

