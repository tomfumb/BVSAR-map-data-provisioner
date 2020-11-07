#!/bin/sh

cd `dirname $0`

gunicorn3 -b 0.0.0.0:80 --log-file /www/api/log/main.log --access-logfile /www/api/log/access.log --user=pi --timeout 3600 -w 2 -k uvicorn.workers.UvicornWorker api.main:app
