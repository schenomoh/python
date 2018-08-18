#!/usr/bin/python3.4
# Execute a subprocess, capture its standard output and standard error 
#
# How to test:
#  rm toto 
#  ./LinuxTail.py
#  echo "hello" >> toto
#  echo "world" >> toto
#  rm toto 
#  echo "file was deleted" >> toto

import sys, os
from subprocess import Popen, PIPE, STDOUT as subprocess
from fcntl import fcntl, F_GETFL, F_SETFL

#Call the tail -F Unix shell command within a subprocess called "sub"
sub=Popen("tail -F toto", 
	shell=True, 
	stdout=PIPE, stderr=PIPE)

# Add O_NONBLOCK to sub.xxx existing file descriptors flags
# This prevent sub.xxx.readline() to wait for EOL
fcntl(sub.stdout, F_SETFL, fcntl(sub.stdout, F_GETFL) | os.O_NONBLOCK)
fcntl(sub.stderr, F_SETFL, fcntl(sub.stderr, F_GETFL) | os.O_NONBLOCK)

#output, error_output = sub.communicate()

while True:
	#Read the data
	line=sub.stdout.readline().decode('UTF-8')
	error=sub.stderr.readline().decode('UTF-8')

	#If they are not empty, diplay the data
	if len(line) != 0:
		print('stdout', line, end="")
	if len(error) != 0:
		print('stderr', error, end="")
