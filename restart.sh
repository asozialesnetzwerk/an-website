#!/bin/sh

git pull

cp an-website.service /etc/systemd/system/an-website.service

systemctl enable an-website.service

[ ! -f /usr/lib/an-website/main.py ] && mkdir /usr/lib/an-website && ln -s main.py /usr/lib/an-website/main.py

systemctl restart an-website.service