FROM node:16

RUN npm install -g @angular/cli
COPY viewer /viewer
WORKDIR /viewer
RUN npm install
RUN ng build --prod --baseHref=/web/