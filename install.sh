# Verify that user wants to install
echo "This script will install the following packages:"
# Are you sure you want to continue? [y/n]
read -p "Are you sure you want to continue? [y/n] " -n 1 -r
if [[ $REPLY =~ ^[Yy]$ ]]
then
    sudo apt update
    sudo apt install git python3 python3-pip docker containerd docker.io -y
    python3 -m pip install flask flask_sock flask_cors docker waitress
    cd /etc
    sudo git clone https://github.com/Xeonpanel/Deamon.git deamon
    sudo mv /etc/deamon/deamon.service /etc/systemd/system/
    echo "Installing nginx config..."
	clear
    read -p 'Enter your domain ( No IP ): '  domain
    echo "Enter the domain name you want to use: "
    read domain
    service nginx stop
    certbot certonly --standalone -d $domain
    cp /etc/deamon/deamon.conf /etc/nginx/sites-available/deamon.conf
    sed -i "s/url/\n$domain\n/g" /etc/nginx/sites-available/deamon.conf
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