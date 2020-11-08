TILEMILL_NAME=bvsar-tilemill
TILEMILL_IMAGE_NAME=tomfumb/$(TILEMILL_NAME)
HTTPD_NAME=bvsar-httpd
HTTPD_IMAGE_NAME=tomfumb/$(HTTPD_NAME)
PROVISIONER_NAME=bvsar-provisioner
PROVISIONER_IMAGE_NAME=tomfumb/$(PROVISIONER_NAME)

NG_SERVE_NAME=bvsar-ng-serve
NG_SERVE_IMAGE_NAME=tomfumb/bvsar-angular-cli

build-tilemill:
	docker build tilemill -t $(TILEMILL_IMAGE_NAME)
start-tilemill:
	docker run -p 20009:20009 -p 20008:20008 -v $(DATA_LOCATION)/run:/tiledata/run -v $(DATA_LOCATION)/export:/root/Documents/MapBox/export -d --name ${TILEMILL_NAME} --rm $(TILEMILL_IMAGE_NAME)
stop-tilemill:
	docker stop ${TILEMILL_NAME}
push-tilemill:
	docker push $(TILEMILL_IMAGE_NAME)

build-provisioner:
	docker build provisioning -t $(PROVISIONER_IMAGE_NAME)
start-provisioner:
	docker run -v $(DATA_LOCATION)/result:/tiledata/result -v $(DATA_LOCATION)/run:/tiledata/run -v $(DATA_LOCATION)/export:/tiledata/export -v $(DATA_LOCATION)/cache:/tiledata/cache -d --name ${PROVISIONER_NAME} --rm --network bvsar $(PROVISIONER_IMAGE_NAME)
stop-provisioner:
	docker stop $(PROVISIONER_NAME)
push-provisioner:
	docker push $(PROVISIONER_IMAGE_NAME)


api-deploy-prod:
	ssh pi@pi-wired 'rm -rf /www/api'
	rsync -rv -e ssh --exclude='**.log' --exclude='**.DS_Store' --exclude='**.pyc' --exclude='**.gitkeep' --exclude='**/__pycache__' --exclude='api/uploads/**' `pwd`/rpi/api pi@pi-wired:/www/

web-build-prod:
	rm -rf rpi/ui/viewer/dist
	docker run --rm -v `pwd`/rpi/ui/viewer:/workdir -w /workdir tomfumb/bvsar-angular-cli ng build --prod --baseHref=/web/

web-deploy-prod:
	make web-build-prod
	ssh pi@pi-wired 'rm -rf /www/web'
	scp -r `pwd`/rpi/ui/viewer/dist/viewer pi@pi-wired:/www/web

ng-serve-start:
	docker build -t $(NG_SERVE_IMAGE_NAME) ./angular-cli
	docker run --rm -d --name $(NG_SERVE_NAME) -v `pwd`/rpi/ui/viewer:/workdir -w /workdir $(NG_SERVE_IMAGE_NAME)
	docker logs -f $(NG_SERVE_NAME)

ng-serve-stop:
	docker stop $(NG_SERVE_NAME)
