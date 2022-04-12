api-deploy-wired:
	ssh pi@pi-wired 'rm -rf /www/api'
	rsync -rv -e ssh --exclude='**.log' --exclude='**.DS_Store' --exclude='**.pyc' --exclude='**.gitkeep' --exclude='**/__pycache__' --exclude='api/uploads/**' --exclude='export/temp/**' `pwd`/rpi/api pi@pi-wired:/www/

api-deploy-wireless:
	ssh pi@pi-wireless 'rm -rf /www/api'
	rsync -rv -e ssh --exclude='**.log' --exclude='**.DS_Store' --exclude='**.pyc' --exclude='**.gitkeep' --exclude='**/__pycache__' --exclude='api/uploads/**' --exclude='export/temp/**' `pwd`/rpi/api pi@pi-wireless:/www/

web-deploy-wired:
	make web-build-prod
	ssh pi@pi-wired 'rm -rf /www/web'
	scp -r `pwd`/rpi/ui/viewer/dist/viewer pi@pi-wired:/www/web

web-deploy-wireless:
	make web-build-prod
	ssh pi@pi-wireless 'rm -rf /www/web'
	scp -r `pwd`/rpi/ui/viewer/dist/viewer pi@pi-wireless:/www/web

web-watch:
	cd rpi/ui && \
	docker build -t tomfumb/bvsar-ng . && \
	docker run -d --name bvsar-web-watch --rm -w $$PWD/viewer:/viewer -w /viewer tomfumb/bvsar-ng ng build --watch --baseHref /web/ && \
	docker logs -f bvsar-web-watch

web-build:
	cd rpi/ui && \
	docker build -t tomfumb/bvsar-ng . && \
	docker run --rm -w $$PWD/viewer:/viewer -w /viewer tomfumb/bvsar-ng ng build --baseHref /web/

web-build-prod:
	cd rpi/ui && \
	docker build -t tomfumb/bvsar-ng . && \
	docker run --rm -w $$PWD/viewer:/viewer -w /viewer tomfumb/bvsar-ng ng build --prod --baseHref /web/