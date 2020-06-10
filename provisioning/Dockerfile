FROM osgeo/gdal:ubuntu-small-3.1.0

RUN apt-get -y update \
 && apt-get install -y --no-install-recommends python3-pip \
 && rm -rf /var/lib/apt/lists/* \
 && apt-get clean 

RUN useradd --create-home appuser

COPY requirements.txt /requirements.txt
RUN pip3 install --no-cache-dir -r /requirements.txt
RUN rm /requirements.txt

WORKDIR /home/appuser
USER appuser

# COPY app app

# CMD ["python", "-m", "app.update"]
CMD ["sleep", "1000"]