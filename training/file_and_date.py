#!/usr/bin/python3.4

import os, time, datetime

#from datetime import timezone

for filename in os.listdir("."):
	#skip directories
	if not os.path.isfile(filename): continue
	#Display file modification time and filename
	print (  filename)
	print (  " age in seconds ", time.time() - os.path.getmtime(filename)  )
	print (  " iso last update", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(filename) ) ) )

#current time
print('\n`sysdate`')
print( " seconds since epoch",  time.time())
print( " sysdate iso format ",  str(datetime.datetime.now())[0:19])
print('\n')
