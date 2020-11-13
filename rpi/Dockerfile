FROM node:12 as ng-builder

RUN npm install -g @angular/cli
COPY ui/viewer /viewer
WORKDIR /viewer
RUN npm install
RUN ng build --prod --baseHref=/web/


FROM debian:buster

RUN apt-get update
RUN apt-get install -y python3
RUN apt-get install -y python3-pip
RUN apt-get install -y gdal-bin
RUN apt-get install -y libgdal-dev
RUN apt-get install -y gunicorn3
RUN apt-get install -y libxcb1-dev
RUN apt-get install -y default-jre

RUN adduser --disabled-password --gecos "" pi

COPY requirements.txt /
RUN pip3 install -r /requirements.txt

RUN mkdir -p /www/tiles
RUN mkdir /www/uploads

COPY api /www/api
RUN mkdir -p /www/api/log
RUN mkdir -p /www/api/export/temp

COPY --from=ng-builder /viewer/dist/viewer /www/web

RUN chown -R pi: /www


WORKDIR /www

CMD [ "gunicorn3", "-b", "0.0.0.0:80", "--log-file", "/www/api/log/main.log", "--access-logfile", "/www/api/log/access.log", "--timeout", "3600", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "api.main:app" ]
