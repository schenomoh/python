#!/usr/bin/python3.4
''' Execute a subprocess, capture its standard output and standard error 

 Sources:https://github.com/schenomoh/python


#How to test

rm feedback* ; touch feedback ; ./monitor

echo hello >> feedback
sleep 1
echo message2a >> feedback2
echo message2b >> feedback2
echo message3  >> feedback3
echo message4A >> feedback4
echo message4B >> feedback4


 Assumption: for a given pattern, when a new file appears, old files are no more written
 We can miss the last few records when we switch from one file to another
   If the new file is created before the closure of the old one, we can miss the last records in old file
   If the new file is quickly written with plenty of records, we can miss a some of them
'''
import sys, os, time
from datetime import datetime
from subprocess import Popen, check_output, PIPE, STDOUT as subprocess
from fcntl import fcntl, F_GETFL, F_SETFL


''' ----------------------------------------- 
	Fetch the latest log in real time for a give filepattern
'''
class logfetcher(object):
	def __init__(self, filepattern, max_ageofrecord=10):
		#Filepattern and location
		tmp=filepattern.split('/')
		self.filepattern=tmp[-1]
		if len(tmp)>1:
			self.filelocation='/'.join(tmp[:-1]) 
			#Previous line join nothing when file location is ' / ' But who wants to do that ?
			if self.filelocation == '': self.filelocation='/'
			if not os.path.isdir(self.filelocation): raise BaseException("Unable to find folder '"+self.filelocation+"'")
		else:
			self.filelocation='.'
		
		self.filename=None

		self.linuxDatetime=datetime.now()
		self.startdate=""
		self.max_ageofrecord = max_ageofrecord
		self.data=[]  # Array of tuples (Date, Data)
		self.error=[] # Array of tuples (Date, Data)
		self.poller=None
	def age():
		return

	''' ----------------------------------------- 
		Search the latest file matching filepattern and reboot the poller if a new one is found
		If the poller is not running, then start it
	'''
	def _search_file(self):

		#We want Linux notation for filepattern and wildcard. So we went for Linux commands withs check_output()
		#Similarly we want Linux timestamp with Linux timezone

		#Get current date time from Linux
		linuxDatetime=check_output(
				['echo -n `date "+%Y-%m-%d %H:%M:%S.%N"`'],
				shell=True
			).decode('UTF-8')
		#Parse as datetime object so that we can easily compare it
		linuxDatetime = datetime.strptime(linuxDatetime[:26], '%Y-%m-%d %H:%M:%S.%f')
		#Linux ls to retrieve all files matching pattern
		linux_listfile=check_output(
				['ls -lt --time-style="+%Y-%m-%d %H:%M:%S.%N" ' + self.filelocation + '/' + self.filepattern + ' 2>/dev/null || echo -n ""']
				, shell=True
				#, stderr=PIPE #We are adviced to avoid using this parameter for check_output(). So, errors are managed in Linux shell command
			).decode('UTF-8').split('\n')
		
		#Parse as array of [ date_lastupdate, time_lastupdate, filename ]
		linux_listfile = [ line.split(' ')[-3:] for line in linux_listfile  if len(line)>2 ]
		#Parse as an array of (datetime, filename)
		
		linux_listfile = [ {'date':datetime.strptime(i[0]+i[1][:15], '%Y-%m-%d%H:%M:%S.%f'), 'name':i[2]} for i in linux_listfile ]

		#Sort by date desc
		linux_listfile.sort(key=lambda x: x['date'], reverse=True)

		if len(linux_listfile)>0 :
			new_filename = linux_listfile[0]['name']
		else:
			new_filename = self.filename

		if new_filename == self.filename:
			#print ("file poller", self.filename)
			poller_action="Continue"
		else:
			#print("file poller", self.filename, "-->", new_filename)
			poller_action="Update"
			for f in linux_listfile[1:] :
				#End of backload when we reach the last file
				if f['name'] == self.filename: break
				#End of back load if we reach a file older than the last file lookup
				if f['date'] < self.linuxDatetime: break

				#Backload file missed
				#print("to backload", f['name'])
				self.backload(  f['name']  )


		if poller_action == "Continue":
			self.filename =  new_filename
		elif poller_action == "Update":
			#Finish reading old file and store the data for later, when read(flush=True) will be called
			self.read(flush=False, searchfile=False)
			self.stop()
			self.filename =  new_filename
			#point poller on new one
			self.start()

		#Always update the processing time
		self.linuxDatetime=linuxDatetime


		return		

	''' ----------------------------------------- 
		Read the new content of the file
			Return the number of line read
	'''
	def read(self, flush=True, searchfile=True):
		if searchfile:
			self._search_file()

		try:
			while True:
				line=self.poller.stdout.readline().decode('UTF-8')
				if len(line) == 0: break
				self.data.append(line)
			#while True:
			#	error=self.poller.stderr.readline().decode('UTF-8')
			#	#Todo, generate some logs on error ? 
			#	if len(error) == 0: break
		except:
			pass
		finally:
			if flush:
				result = self.data[:]
				self.data=[]
				return result
			else:
				return

	''' ----------------------------------------- 
		Backload a full file
	'''
	def backload(self, filename):
		#print("backloading", filename)
		try:
			with open(self.filelocation+'/'+filename) as f:
				for line in f.readlines():
					#print (line, end="")
					self.data.append(line)
		except:
			pass
		#error=self.poller.stderr.readline().decode('UTF-8')
		#print(error)


	''' ----------------------------------------- 
		Start the poller to poll the file content
	'''
	def start(self, filename=None):
		if self.poller != None: 
			self.__exit__()
			raise BaseException('Unable to start, poller is already running:'+ str(self))
			return
		
		if filename==None: filename=self.filename

		#Start the poller by invoking a tail -F command 
		#self.poller=Popen("exec tail -F "+filename + "", shell=True, stdout=PIPE, stderr=PIPE)
		self.poller=Popen("exec tail -F "+filename + " 2>/dev/null", shell=True, stdout=PIPE)
		# Add O_NONBLOCK flag to prevent file reader to wait for EOL
		fcntl(self.poller.stdout, F_SETFL, fcntl(self.poller.stdout, F_GETFL) | os.O_NONBLOCK)
		#fcntl(self.poller.stderr, F_SETFL, fcntl(self.poller.stderr, F_GETFL) | os.O_NONBLOCK)

	
	''' ----------------------------------------- 
		Stop the poller to poll the file content
	'''
	def stop(self):
		#If there is no poller, exit function
		if self.poller == None: return

		#Stop the Linux process
		self.poller.kill()
		self.poller = None
	
	''' ----------------------------------------- 
		Randomly called by garbage collector. Do not rely on it and use __exit__ instead
	'''
	def __del__(self):
		return
		if self.poller != None:
			raise BaseException('stop() method was not properly called. Orphan Unix poller could have been created', str(self))
	
	''' ----------------------------------------- 
		Called when exiting from a with statement
	'''
	def __exit__(self):
		print("stopping")
		self.stop()

#output, error_output = sub.communicate()

'''
   Librairy test
'''
if __name__ == '__main__':

	f = logfetcher('../training/res/feedback*', max_ageofrecord=30)

	f.start('undefined')

	while True:
		#Read the data
		#f._search_file()
		for line in f.read():
			print(f.filename, line, end="")

		time.sleep(1)

	#except Exception as e: print(e, sys.exc_info())
	#finally:
	f.stop()
	quit()


