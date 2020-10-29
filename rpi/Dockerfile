FROM navikey/raspbian-buster

RUN apt-get update
RUN apt-get install -y python3
RUN apt-get install -y python3-pip
RUN apt-get install -y gdal-bin
RUN apt-get install -y libgdal-dev

RUN adduser --disabled-password --gecos "" pi

COPY requirements.txt /
RUN pip3 install -r /requirements.txt

COPY api /www/api
RUN mkdir /www/uploads

WORKDIR /www/api

CMD [ "uvicorn", "main:app", "--port=80", "--host=0.0.0.0" ]
