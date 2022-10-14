FROM osgeo/gdal:ubuntu-full-3.5.1

RUN apt-get -y update \
 && apt-get install -y --no-install-recommends \
   build-essential \
   git \
   python3-dev \
   python3-pip \
 && apt-get clean

COPY requirements.txt /requirements.txt
RUN pip3 install --no-cache-dir -r /requirements.txt
RUN rm /requirements.txt

RUN mkdir -p /usr/local/apps/mbutil
RUN git clone https://github.com/mapbox/mbutil.git /usr/local/apps/mbutil
ENV MBUTIL_LOCATION=/usr/local/apps/mbutil/mb-util

RUN mkdir -p /tiledata/areas

COPY data /provisioning/data
COPY app /provisioning/app

WORKDIR /provisioning

CMD [ "python", "-m", "app.runner" ]
