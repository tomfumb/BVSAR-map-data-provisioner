
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
 && apt-get install -y nodejs git gdal-bin python-gdal wget unzip \
 && mkdir -p /opt/tilemill /root/Documents/tile/scripts /root/Documents/tile/input /root/Documents/tile/output \
 && cd /opt/tilemill \
 && git clone https://github.com/tilemill-project/tilemill.git \
 && cd tilemill \
 && npm install \
 && npm cache clean --force \
 && mkdir /opt/gdal-postmates \
 && cd /opt/gdal-postmates \
 && git clone https://github.com/postmates/gdal.git . \
 && apt-get clean \
 && apt-get update

ENV GDAL_SCRIPTS=/opt/gdal-postmates/scripts
ENV TILE_SCRIPTS=/root/Documents/tile/scripts
ENV TILE_INPUT=/root/Documents/tile/input
ENV TILE_OUTPUT=/root/Documents/tile/output

COPY run_tilemill.sh /opt/tilemill/run_tilemill.sh

EXPOSE 20008
EXPOSE 20009

VOLUME /root/Documents

WORKDIR /opt/tilemill

CMD [ "/bin/bash", "/opt/tilemill/run_tilemill.sh" ]
