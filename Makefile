TILEMILL_NAME=bvsar-tilemill
TILEMILL_IMAGE_NAME=tomfumb/$(TILEMILL_NAME)
HTTPD_NAME=bvsar-httpd
HTTPD_IMAGE_NAME=tomfumb/$(HTTPD_NAME)
NG_DEV_IMAGE_NAME=tomfumb/bvsar-angular-cli-dev
SSH_SERVE_NAME=bvsar-sshd
SSH_SERVE_IMAGE_NAME=tomfumb/bvsar-sshd
WWW_NAME=bvsar-rpi
WWW_IMAGE_NAME=tomfumb/bvsar-rpi
# PROVISIONER_NAME=provision-runner

dev-provisioning-start:
	docker build tilemill -t $(TILEMILL_IMAGE_NAME)
	docker build rpi -t $(WWW_IMAGE_NAME)
	source .env-dev && docker run --rm -p 20009:20009 -p 20008:20008 -v $$DATA_LOCATION/run:/tiledata/run -v $$DATA_LOCATION/export:/root/Documents/MapBox/export -d --name ${TILEMILL_NAME} $(TILEMILL_IMAGE_NAME)
	source .env-dev && docker run --rm -v $$DATA_LOCATION/result:/www/tiles -e PDF_EXPORT_MAX_TILES=32768 -d --name $(WWW_NAME) -p 9000:80 $(WWW_IMAGE_NAME)

dev-provisioning-stop:
	docker stop ${TILEMILL_NAME}
	docker stop $(WWW_NAME)

dev-web:
	docker build -t $(NG_DEV_IMAGE_NAME) -f rpi/ui/Dockerfile.dev rpi/ui
	docker run --rm -v `pwd`/rpi/ui/viewer:/workdir $(NG_DEV_IMAGE_NAME)

api-deploy-wired:
	ssh pi@pi-wired 'rm -rf /www/api'
	rsync -rv -e ssh --exclude='**.log' --exclude='**.DS_Store' --exclude='**.pyc' --exclude='**.gitkeep' --exclude='**/__pycache__' --exclude='api/uploads/**' --exclude='export/temp/**' `pwd`/rpi/api pi@pi-wired:/www/

api-deploy-wireless:
	ssh pi@pi-wireless 'rm -rf /www/api'
	rsync -rv -e ssh --exclude='**.log' --exclude='**.DS_Store' --exclude='**.pyc' --exclude='**.gitkeep' --exclude='**/__pycache__' --exclude='api/uploads/**' --exclude='export/temp/**' `pwd`/rpi/api pi@pi-wireless:/www/

web-build-prod:
	rm -rf rpi/ui/viewer/dist
	docker run --rm -v `pwd`/rpi/ui/viewer:/workdir -w /workdir $(NG_BUILD_IMAGE_NAME) ng build --prod --baseHref=/web/

web-deploy-wired:
	make web-build-prod
	ssh pi@pi-wired 'rm -rf /www/web'
	scp -r `pwd`/rpi/ui/viewer/dist/viewer pi@pi-wired:/www/web

web-deploy-wireless:
	make web-build-prod
	ssh pi@pi-wireless 'rm -rf /www/web'
	scp -r `pwd`/rpi/ui/viewer/dist/viewer pi@pi-wireless:/www/web

ssh-serve-start:
	docker build -t $(SSH_SERVE_IMAGE_NAME) ./sshd
	docker run --rm -d --name $(SSH_SERVE_NAME) -v bvsar-map-data-provisioner_bvsar-result:/tiledata/result -v $$SSH_PUB_KEY_LOCATION:/root/.ssh/authorized_keys -p 2222:22 $(SSH_SERVE_IMAGE_NAME)

ssh-serve-stop:
	docker stop $(SSH_SERVE_NAME)

# provision-dev:
# 	docker-compose up -d && \
# 	source .env-dev && \
# 	docker run --rm -d --name $(PROVISIONER_NAME) -v $$DATA_LOCATION:/rundata -e DATA_LOCATION=/rundata -e AREAS_LOCATION=/rundata/areas/areas-dev.gpkg -e LOCAL_FEATURES_LOCATION=/rundata/local-features/local-features.gpkg && \
# 	docker logs -f $(PROVISIONER_NAME)
