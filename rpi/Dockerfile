FROM navikey/raspbian-buster

RUN apt-get update
RUN apt-get install -y python3
RUN apt-get install -y python3-pip
RUN apt-get install -y gdal-bin
RUN apt-get install -y libgdal-dev
RUN apt-get install -y gunicorn3

RUN adduser --disabled-password --gecos "" pi

COPY requirements.txt /
RUN pip3 install -r /requirements.txt

RUN mkdir -p /www/tiles
RUN mkdir /www/uploads
RUN mkdir /www/web
RUN chown -R pi: /www

RUN mkdir -p /var/log/gunicorn

COPY api /www/api
RUN mkdir /www/uploads

WORKDIR /www

CMD [ "gunicorn3", "-b", "0.0.0.0:80", "--log-file", "/var/log/gunicorn/main.log", "--access-logfile /var/log/gunicorn/access.log", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "api.main:app" ]
