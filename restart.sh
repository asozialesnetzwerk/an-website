#!/bin/sh

git pull

sed "s/user-placeholder/$USER/g" an-website.service > /etc/systemd/system/an-website.service

systemctl enable an-website.service
systemctl restart an-website.service