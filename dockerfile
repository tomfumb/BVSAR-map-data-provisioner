
    # tilemill = TileMillManager()
    # tilemill.generate(outputDirectory, self.scalesAndZooms, boundsMinX, boundsMinY, boundsMaxX, boundsMaxY, environmentConfig)FROM ubuntu:18.04 
MAINTAINER juca <juca@juan-carlos.info>

ENV APP_NAME="tilemill"

RUN export DEBIAN_FRONTEND=noninteractive \
 && apt-get update -y \
 && apt-get install -y --no-install-recommends apt-utils \
 && apt-get install -y locales && locale-gen en_US.UTF-8 \
 && apt-get install -y curl \
 && curl -sL https://deb.nodesource.com/setup_8.x | bash - \
 && apt-get update -y \
 && apt-get install -y nodejs git gdal-bin python-gdal wget unzip pip3 \
 && mkdir -p /root/Documents/provisioning \
 && cd /opt/tilemill \
 && git clone https://github.com/tilemill-project/tilemill.git \
 && cd tilemill \
 && npm install \
 && npm cache clean --force \
 && mkdir /opt/gdal-postmates \
 && git clone https://github.com/postmates/gdal.git /opt/gdal-postmates \
 && mkdir /opt/mbutil \
 && git clone https://github.com/mapbox/mbutil.git /opt/mbutil \
 && apt-get clean \
 && apt-get update \
 && pip3 install pyproj

ENV GDAL_SCRIPTS=/opt/gdal-postmates/scripts
ENV MB_UTIL=/opt/mbutil/mb-util
ENV PROVISIONING_HOME=/root/Documents/provisioning

COPY run_tilemill.sh /opt/tilemill/run_tilemill.sh

EXPOSE 20008
EXPOSE 20009

VOLUME /root/Documents

WORKDIR /opt/tilemill

CMD [ "/bin/bash", "/opt/tilemill/run_tilemill.sh" ]
