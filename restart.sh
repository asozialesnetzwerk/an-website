#!/bin/sh

git pull

[ ! -f /etc/systemd/system/an-website.service ] && ln -s an-website.service /etc/systemd/system/an-website.service && systemctl enable an-website.service

[ ! -f /usr/lib/an-website/main.py ] && ln -s main.py /usr/lib/an-website/main.py

systemctl restart an-website.service