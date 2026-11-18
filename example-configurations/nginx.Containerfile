FROM docker.io/library/nginx:stable-alpine-slim

RUN <<EOF

printf '%s' '
events {
    worker_connections 1024;
}

http {
    upstream an-website {
        server unix:/run/an-website.sock;
    }

    upstream static-files {
        server unix:/run/lighttpd.sock;
    }

    server {
        listen 80;

        gzip off;

        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;

        proxy_http_version 1.1;
        proxy_send_timeout 20s;
        proxy_read_timeout 20s;

        location /static {
            proxy_pass http://static-files;
        }

        location /soundboard/files {
            proxy_pass http://static-files;
        }

        location /@apm-rum/ {
            proxy_pass http://static-files;
        }

        location / {
            proxy_pass http://an-website;
        }

        location @proxy {
            proxy_pass http://an-website;
        }

        location /api/backdoor {
            proxy_pass http://unix:/var/run/an-website/an-website.0.sock;
        }

        location /api/update {
            proxy_pass http://an-website;

            proxy_request_buffering off;
            client_max_body_size    50M;
        }

        location /websocket/ {
            proxy_pass http://an-website;

            proxy_set_header Host              $http_host;
            proxy_set_header X-Real-IP         $remote_addr;
            proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header Connection        upgrade;
            proxy_set_header Upgrade           $http_upgrade;
        }
    }
}
' > /etc/nginx/nginx.conf

nginx -t
EOF

EXPOSE 80
