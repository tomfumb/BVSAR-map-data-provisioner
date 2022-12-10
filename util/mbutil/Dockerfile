FROM python:3.9

RUN apt-get -y update \
 && apt-get install -y --no-install-recommends \
   git \
 && apt-get clean

WORKDIR /app
RUN git clone https://github.com/mapbox/mbutil.git
WORKDIR /app/mbutil
RUN pip install .

CMD ["mb-util", "-h"]
