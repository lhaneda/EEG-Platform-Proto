# Server Information

## Main Server (Amazon Linux)

Address: ec2-34-204-73-41.compute-1.amazonaws.com

Currently the server runs, on a screen for the user webuser a flask server via the following command:

````
python EEGPlatform/website/website.py
````

### Steps done to set up the server
````sudo yum update
sudo yum install -y git gcc gcc-c++ make git openssl-devel bzip2-devel zlib-devel amazon-efs-utils readline-devel postgresql

mkdir condat
cd condtat
wget https://repo.anaconda.com/archive/Anaconda3-2018.12-Linux-x86_64.sh
sudo bash Anaconda3-2018.12-Linux-x86_64.sh
-> install to opt/anaconda3
-> copied /root/.bashrc to the .bashrc for ec2-user
Added my key to authorized keys
Removed condat directory

sudo adduser webuser
sudo su webuser
cd ~
mkdir .ssh
touch .ssh/authorized_keys
chmod 600 .ssh/*
chmod 700 .ssh

ssh-keygen -b 2048 -t rsa -f key -C webuser
mv key .ssh/id_rsa
mv key.pub .ssh/id_rsa.pub
exec ssh-agent bash

as root:
conda install boto3 psycopg2

Also add the conda information from root/.bashrc to webuser/.bashrc
add the following to bashrc:

exec ssh-agent bash
ssh-add ~/.ssh/key

(Added the public key to the repository as a deploy key)

git clone git@github.com:NickRoss/EEGPlatform.git

for webuser:
pip install flask_bootstrap flask_wtf flask_login flask_sqlalchemy pyedflib --user
````

### RDMS Server
For RDMS

````
eegplatform2.c3ogcwmqzllz.us-east-1.rds.amazonaws.com
password: iO30IG1HbXcJ
username: eeg2019
dbname: eegplatform
````

