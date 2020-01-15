FROM nginx

COPY ./default.conf /etc/nginx/conf.d/default.conf

COPY ./paths.conf /etc/nginx/conf/paths.conf

COPY ./localhost.crt /etc/nginx/localhost.crt

COPY ./localhost.key /etc/nginx/localhost.key

CMD ["nginx", "-g", "daemon off;"]
