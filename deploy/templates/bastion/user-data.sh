#!/bin/bash

sudo yum update -y
sudo amazon-linux-extras install -y docker
sudo systemctl enable docker.service
sudo systemctl start docker.service
sudo usermod -aG docker ec2-user
sudo yum install python3-pip -y
sudo pip3 install notebook
su ec2-user -c 'jupyter notebook --generate-config'
su ec2-user -c 'export DB_HOST=1234'
sed -i "1 a\
c.NotebookApp.ip = '0.0.0.0'\\
c.NotebookApp.open_browser = False" /home/ec2-user/.jupyter/jupyter_notebook_config.py
echo "export GOROOT=/usr/local/go" >> /etc/profile
echo "export TEST=1234" >> /etc/profile