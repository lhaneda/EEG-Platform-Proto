#!/usr/bin/env python3
import paramiko
import sys
from os.path import expanduser 
from os.path import exists
import time

DIR_NAME = B'EEGPlatform'
STR_DIR_NAME = 'EEGPlatform'

ec2_address = 'ec2-34-204-73-41.compute-1.amazonaws.com'
user = 'webuser'
key_file = '/.ssh/EEGProject2019.pem'
# 1. SSH to box:
print( "Connecting to box" )

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(ec2_address, username = user, key_filename = expanduser("~") +  key_file)

# 2. Check whether the EC2 has git installed. Otherwise install git.
stdin, stdout, stderr = ssh.exec_command("git --version")

if(b"command not found" in stderr.read() ):
    print ("Installing Git")
    stdin, stdout, stderr = ssh.exec_command("sudo yum -y install git")
    
    while True:
        print("...")
        time.sleep(10)
        stdin, stdout, stderr = ssh.exec_command("git --version")
      
        if(b"command not found" in stderr.read()):
            print("...")
            time.sleep(10)
        else:
            print("Finished installing Git")
            break

#TODO DMW: Expire after time out
# 3 - 5. Check for lock file:
_, stdout, _ = ssh.exec_command("ls")
files = stdout.read()
file_names = files.split(b'\n')
print('Got the file names')

# TODO: enter again when deploy is stable
while True:
    if b'flock' not in file_names:
        break
    print("...")
    time.sleep(10)

    _, stdout, _ = ssh.exec_command("ls")
    files = stdout.read()
    file_names = files.split(b'\n')


#TODO DMW : Expire after time out
print("No processes running. Updating files.")

ssh.exec_command("mkdir flock") # Creating dummy lock directory when we get past the loop

# 5. Add Crontab

# 7. Remove and reset CRON file
if 1 == 1:
    ssh.exec_command("crontab -r")

    newcronline = "* * * * * cd /home/webuser/EEGPlatform/code && flock -n /home/webuser/bosunlock.lock -c \'\"/opt/anaconda3/bin/python /home/webuser/EEGPlatform/code/SimpleHelper.py\"\' >> /home/webuser/logs/log.log"
### the above isn't working because I'm getting a failed importlib.util not found... BUT ITS THERE.
    ssh.exec_command("crontab -l | { cat; echo \"" + newcronline + "\"; } | crontab -")
    print("Crontab updated")
else:
    print("No crontab changes")

# 6. Git pull from bitbucket

stdin, stdout, stderr = ssh.exec_command("rm -rf " + STR_DIR_NAME + " ; " + " git clone git@github.com:NickRoss/EEGPlatform.git ")
time.sleep(3)
print("rm -rf " + STR_DIR_NAME + " ; " + " git clone git@github.com:NickRoss/EEGPlatform.git ")
#print(stdin, stdout, stderr)
print("Pull from Git successfully")

if DIR_NAME in files:
    # Only do the above on the remote machine
    
    pass

# 8. Remove dummy lock directory to finish:
ssh.exec_command("rm -r flock")
# This updates the 2016 dataasdfasdfasdfsdaf
print("Script fully executed ... exiting")

# 9. Close your connection.
ssh.close()

## EOF ##

