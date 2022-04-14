FROM osgeo/gdal:ubuntu-full-3.4.2

RUN export DEBIAN_FRONTEND=noninteractive \
 && apt-get update --fix-missing \
 && apt-get install -y --no-install-recommends python3-pip git \
 && rm -rf /var/lib/apt/lists/* \
 && apt-get clean

COPY requirements.txt /requirements.txt
RUN pip3 install --no-cache-dir -r /requirements.txt
RUN rm /requirements.txt

RUN mkdir -p /usr/local/apps/mbutil
RUN git clone https://github.com/mapbox/mbutil.git /usr/local/apps/mbutil
ENV MBUTIL_LOCATION=/usr/local/apps/mbutil/mb-util

RUN mkdir -p /tiledata/areas

COPY data /data
COPY app /app

CMD [ "python", "-m", "app.runner" ]
