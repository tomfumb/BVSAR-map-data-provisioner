FROM ubuntu:18.04 

ENV APP_NAME="tilemill"

EXPOSE 20008
EXPOSE 20009

RUN export DEBIAN_FRONTEND=noninteractive \
 && apt-get update -y \
 && apt-get install -y --no-install-recommends apt-utils git curl locales ca-certificates \
 && locale-gen en_US.UTF-8 \
 && update-ca-certificates \
 && curl -sL https://deb.nodesource.com/setup_8.x | bash - \
 && apt-get update -y \
 && apt-get install -y --no-install-recommends nodejs

RUN mkdir -p /opt/tilemill

WORKDIR /opt/tilemill
RUN git clone https://github.com/tilemill-project/tilemill.git
WORKDIR /opt/tilemill/tilemill
RUN npm install && npm cache clean --force

WORKDIR /opt/tilemill
COPY run_tilemill.sh run_tilemill.sh

RUN mkdir -p /tiledata/input

COPY icons /icons

ENTRYPOINT [ "/opt/tilemill/run_tilemill.sh" ]