#!/bin/sh

git pull

cp an-website.service /etc/systemd/system/an-website.service


[ ! -d /usr/lib/an-website/ ] && mkdir /usr/lib/an-website

cp -r * /usr/lib/an-website/

systemctl enable an-website.service
systemctl restart an-website.service