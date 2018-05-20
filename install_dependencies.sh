#!/bin/bash

sudo apt-get update
sudo apt-get install ssh -y
sudo apt-get install vim -y
sudo apt-get install python -y
sudo apt-get install python-setuptools -y
sudo apt-get install redis-server -y
sudo easy_install redis
sudo easy_install web.py

sudo apt-get install terminator -y
sudo apt-get install apt-transport-https ca-certificates -y
sudo apt-key adv                --keyserver hkp://ha.pool.sks-keyservers.net:80                --recv-keys 58118E89F3A912897C070ADBF76221572C52609D
deb https://apt.dockerproject.org/repo ubuntu-xenial main
sudo apt-get install linux-image-extra-$(uname -r) linux-image-extra-virtual -y
sudo apt-get install apache2 -y

sudo echo "deb https://apt.dockerproject.org/repo ubuntu-xenial main" >> /etc/apt/sources.list
sudo apt-get update
sudo apt-get install docker-engine -y
sudo apt-get install docker -y
sudo service docker start
#WRITE BELOW YOU USERNAME
echo "Please write your username"
read username
sudo usermod -aG docker $username
sudo apt-get install openvswitch-switch -y

sudo apt-get install python-dev -y
sudo easy_install netifaces
sudo easy_install docker-py
sudo easy_install "docker-py==1.5.0"
sudo apt-get install screen -y
