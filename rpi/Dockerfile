FROM node:12 as ng-builder

RUN npm install -g @angular/cli
COPY ui/viewer /viewer
WORKDIR /viewer
RUN npm install
RUN ng build --prod --baseHref=/web/


FROM debian:buster

RUN apt-get update && \ 
    apt-get install -y python3 python3-pip gdal-bin libgdal-dev gunicorn3 libxcb1-dev

RUN adduser --disabled-password --gecos "" pi

COPY requirements.txt /
RUN pip3 install -r /requirements.txt

RUN mkdir -p /www/tiles
RUN mkdir /www/uploads
RUN mkdir /www/files

COPY api /www/api
RUN mkdir -p /www/api/log
RUN mkdir -p /www/web
RUN mkdir -p /www/api/export/temp

COPY --from=ng-builder /viewer/dist/viewer /www/web

RUN chown -R pi: /www


WORKDIR /www

CMD [ "gunicorn3", "-b", "0.0.0.0:80", "--log-file", "/www/api/log/main.log", "--access-logfile", "/www/api/log/access.log", "--timeout", "3600", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "api.main:app" ]
