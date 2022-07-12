# Verify that user wants to install
echo "This script will install the following packages:"
# Are you sure you want to continue? [y/n]
read -p "Are you sure you want to continue? [y/n] " -n 1 -r
if [[ $REPLY =~ ^[Yy]$ ]]
then
    sudo apt update
    sudo apt install git python3 python3-pip docker containerd docker.io -y
    python3 -m pip install flask flask_sock flask_cors docker waitress
    cd /var/www
    sudo git clone https://github.com/Xeonpanel/Deamon.git deamon
    sudo mv /var/www/deamon/deamon.service /etc/systemd/system/
    systemctl enable deamon --now
    echo "\n\n Deamon succesfully installed, and started.. \n\n"
else
    echo "Installation cancelled."
fi