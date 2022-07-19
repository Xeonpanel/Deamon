#!/bin/bash
clear
echo "XeonPanel Deamon v0.8 Installation Script"
echo "Copyright © 2022 Xeonpanel."
echo "For support join our community: https://discord.gg/4y9X28Ubxd"
sleep 1s
echo ""
if [ "$(id -u)" != "0" ]; then
    printf "This script must be run as root\nYou can login as root with\033[0;32m sudo su -\033[0m\n" 1>&2
    exit 1
fi
read -p "Are you sure you want to continue? [y/n] " installation
if [[ $installation == "y" || $installation == "Y" || $installation == "yes" || $installation == "Yes" ]]
then
    sudo apt update
    sudo apt --ignore-missing install git python3 python3-pip docker containerd docker.io
    python3 -m pip install flask flask_sock flask_cors docker waitress
    cd /etc
    sudo git clone https://github.com/Xeonpanel/Deamon.git deamon
    sudo mv /etc/deamon/deamon.service /etc/systemd/system/
    echo "Installing nginx config..."
	clear
    read -p 'Enter your domain ( No IP ): '  domain
    service nginx stop
    certbot certonly --standalone -d $domain
    cp /etc/deamon/deamon.conf /etc/nginx/sites-available/deamon.conf
    sed -i "s/url/$domain/" /etc/nginx/sites-available/deamon.conf
    ln -s /etc/nginx/sites-available/deamon.conf /etc/nginx/sites-enabled/deamon.conf
    systemctl restart nginx
    echo ""
    echo " --> Installation completed"
    echo ""
else
    echo ""
    echo " --> Installation cancelled"
    echo ""
fi