TILEMILL_NAME=bvsar-tilemill
TILEMILL_IMAGE_NAME=tomfumb/$(TILEMILL_NAME)
HTTPD_NAME=bvsar-httpd
HTTPD_IMAGE_NAME=tomfumb/$(HTTPD_NAME)
PROVISIONER_NAME=bvsar-provisioner
PROVISIONER_IMAGE_NAME=tomfumb/$(PROVISIONER_NAME)

build-tilemill:
	docker build tilemill -t $(TILEMILL_IMAGE_NAME)
start-tilemill:
	docker run -p 20009:20009 -p 20008:20008 -v $(DATA_LOCATION)/run:/tiledata/run -v $(DATA_LOCATION)/export:/root/Documents/MapBox/export -d --name ${TILEMILL_NAME} --rm $(TILEMILL_IMAGE_NAME)
stop-tilemill:
	docker stop ${TILEMILL_NAME}
push-tilemill:
	docker push $(TILEMILL_IMAGE_NAME)

build-http:
	docker build httpd -t $(HTTPD_IMAGE_NAME)
start-http:
	docker run -p 8001:80 -v $(DATA_LOCATION)/result:/usr/local/apache2/htdocs -d --name ${HTTPD_NAME} --rm $(HTTPD_IMAGE_NAME)
stop-http:
	docker stop ${HTTPD_NAME}
push-http:
	docker push $(HTTPD_IMAGE_NAME)

build-provisioner:
	docker build provisioning -t $(PROVISIONER_IMAGE_NAME)
start-provisioner:
	docker run -v $(DATA_LOCATION)/result:/tiledata/result -v $(DATA_LOCATION)/run:/tiledata/run -v $(DATA_LOCATION)/export:/tiledata/export -v $(DATA_LOCATION)/cache:/tiledata/cache -d --name ${PROVISIONER_NAME} --rm --network bvsar $(PROVISIONER_IMAGE_NAME)
stop-provisioner:
	docker stop $(PROVISIONER_NAME)
push-provisioner:
	docker push $(PROVISIONER_IMAGE_NAME)
