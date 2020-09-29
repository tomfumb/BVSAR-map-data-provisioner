TILEMILL_NAME=tomfumb/bvsar-tilemill
HTTPD_NAME=tomfumb/bvsar-httpd
PROVISIONER_NAME=tomfumb/bvsar-provisioner

build-tilemill:
	docker build tilemill -t $(TILEMILL_NAME)
start-tilemill:
	docker run -p 20009:20009 -p 20008:20008 -v $(DATA_LOCATION)/run:/tiledata/run -v $(DATA_LOCATION)/export:/root/Documents/MapBox/export -d --name ${TILEMILL_NAME} --rm tomfumb/bvsar-tilemill
stop-tilemill:
	docker stop ${TILEMILL_NAME}
push-tilemill:
	docker push $(TILEMILL_NAME)

build-http:
	docker build httpd -t $(HTTPD_NAME)
start-http:
	docker run -p 8001:80 -v $(DATA_LOCATION)/result:/usr/local/apache2/htdocs -d --name ${HTTPD_NAME} --rm tomfumb/bvsar-httpd
stop-http:
	docker stop ${HTTPD_NAME}
push-http:
	docker push $(HTTPD_NAME)

build-provisioner:
	docker build provisioning -t $(PROVISIONER_NAME)
start-provisioner:
	docker run -v $(DATA_LOCATION)/result:/tiledata/result -v $(DATA_LOCATION)/run:/tiledata/run -v $(DATA_LOCATION)/export:/tiledata/export -v $(DATA_LOCATION)/cache:/tiledata/cache -d --name ${PROVISIONER_NAME} --rm --network bvsar tomfumb/bvsar-provisioner
stop-provisioner:
	docker stop $(PROVISIONER_NAME)
push-provisioner:
	docker push $(PROVISIONER_NAME)
