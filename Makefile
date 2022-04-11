api-deploy-wired:
	ssh pi@pi-wired 'rm -rf /www/api'
	rsync -rv -e ssh --exclude='**.log' --exclude='**.DS_Store' --exclude='**.pyc' --exclude='**.gitkeep' --exclude='**/__pycache__' --exclude='api/uploads/**' --exclude='export/temp/**' `pwd`/rpi/api pi@pi-wired:/www/

api-deploy-wireless:
	ssh pi@pi-wireless 'rm -rf /www/api'
	rsync -rv -e ssh --exclude='**.log' --exclude='**.DS_Store' --exclude='**.pyc' --exclude='**.gitkeep' --exclude='**/__pycache__' --exclude='api/uploads/**' --exclude='export/temp/**' `pwd`/rpi/api pi@pi-wireless:/www/

web-build-prod:
	rm -rf rpi/ui/viewer/dist
	ng build --prod --baseHref /web/

web-deploy-wired:
	make web-build-prod
	ssh pi@pi-wired 'rm -rf /www/web'
	scp -r `pwd`/rpi/ui/viewer/dist/viewer pi@pi-wired:/www/web

web-deploy-wireless:
	make web-build-prod
	ssh pi@pi-wireless 'rm -rf /www/web'
	scp -r `pwd`/rpi/ui/viewer/dist/viewer pi@pi-wireless:/www/web

web-local-dev:
	@cd rpi/ui/viewer
	ng build --watch --baseHref /web/