FROM httpd:2.4 

RUN rm /usr/local/apache2/htdocs/index.html
COPY httpd.conf /usr/local/apache2/conf/httpd.conf
COPY .htaccess /usr/local/apache2/htdocs/.htaccess
