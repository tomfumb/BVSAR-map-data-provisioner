#!/bin/sh

cd `dirname $0`

gunicorn3 -b 0.0.0.0:80 --log-file /var/log/gunicorn/main.log --access-logfile /var/log/gunicorn/access.log --user=pi --timeout 600 -w 4 -k uvicorn.workers.UvicornWorker api.main:app
