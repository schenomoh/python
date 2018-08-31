#!/usr/bin/python3.4
#
#Linux specific
#
# To test
#
# ./psFetcher.py
#
# tail -F toto
# ^C
# tail -F toto
# 


from subprocess import Popen, check_output, PIPE, STDOUT as subprocess
from datetime import datetime, timedelta
import time, copy, re

class psFetcher:
	def __init__(self):	
		self.current={}
		self.previous={}
		self.refresh()

	'''
		Refresh the values stored in psFetcher
	'''
	def refresh(self):

		#Backup current values in self.previous
		#for key,val in self.current.items():
		#	self.previous[key] = copy.copy(self.current[key])
		self.previous = copy.deepcopy(self.current)
		self.current={}

		#Retrieve all the processes, trim all fields and returns only records older than 0 second
		psCommand=Popen("ps -ed --no-headers -o etime,ruser,pid,ppid,command -ww|awk '{$1=$1}1' | grep -v ^0' '", shell=True, stdout=PIPE)
		while True:
			psOutput = psCommand.stdout.readline().decode('UTF-8')[:-1]
			if len(psOutput) == 0: break

			psOutput=psOutput.split(' ')
			line={}
			#Fetch fields returned by ps
			t=psOutput.pop(0)
			t=t.replace('-',':').split(':')
			t=[0]*(4-len(t))+[int(i) for i in t]
			line["elapsedSecond"] = t[0]*86400+t[1]*3600+t[2]*60+t[3]
			line["user"]=psOutput.pop(0)
			line["pid"]=psOutput.pop(0)
			line["ppid"]=psOutput.pop(0)
			#Concatenate remaining fields to retrieve the unix command
			line["command"]=''
			for i in range(0, len(psOutput)):
				line["command"]=line["command"]+' '+psOutput[i]
			#Remove the ugly leading space
			line["command"] = line["command"][1:]

			#Add calculated fields
			line["startDatetime"] = datetime.now() - timedelta( seconds=int(line["elapsedSecond"]) )
			line["status"] = None # Calulated in getSpecificProcess

			#Store result in the ps array
			self.current[ line["pid"] ] = line

		#List of new processes

	'''
	_getAll(..): list all the unix processes matching the selection criteria. Returns an iterator on self.current

	Selection criteria:
		elapsedSecond: number of seconds since the process started
		user: unix user name
		pid: unix process id
		ppid: unix parent process id
		command: process full command line. Search process exact match. 
		startDatetime: process start time. Format is a datetime.datetime() structure

	To avoid refreshing self.current, set True the following parameter
		autoRefresh: when True, refresh the list of process stored in psFetcher

	'''
	def _getAll(self, autoRefresh=True, **arg): # elapsed, user, pid, ppid, command, started, 
	# + restartedSince, + stoppedSince + startedSince

		if autoRefresh: self.refresh()

		for pid, line in self.current.items():
			recordMatch=True
			for key, val in arg.items():
				if str(line[key]) != str(val):
					recordMatch=False
					break
			if recordMatch:
				yield line
	'''
	getSpecificProcess(..): Retrieve the lastest unix process matching the selection criteria. 
	Use the same selection criteria as _getAll() plus the following one:

	To update the process list, please call psFetcher.refresh() method

	Additional selection criteria
		cmdpattern: search with (*) as wildcard. Rely on regular expression, so that it is proven difficult to search in strings containing special chars

	On top of existing fields, compute the following fields:
	status:
		duplicated: when multiple records are retrived the status is set to this value
		started: when a process started since the last refresh
		missing: when a process is not found
		running: when a process continue to be up and running
		stopped: when a process stopped since the last refresh
		restarted: when a process stop/started since the last refresh
	duplicateList: list of all the duplicated records ignored

	'''
	def getSpecificProcess(self,cmdpattern='*', **arg):

		cmdpattern = '^'+cmdpattern.replace('*','.*')+'$'
		result_list=[]

		currentpid=None
		currentstatus=None
		#Search for cmdpattern in the currentlist
		for x_line in self._getAll(autoRefresh=False,**arg):
			#regular expression does not work fine with special chars in command (ex: square bracket)
			if re.search(cmdpattern, x_line["command"]):
				result_list.append(x_line)
				currentpid=x_line["pid"]
				currentstatus=x_line["status"]
		del x_line

		#Search for cmdpattern in the previouslist
		#Retrieve the previous line
		lastline={}
		lastpid=None
		#laststatus=None
		for x_pid, x_line in self.previous.items():
			if re.search(cmdpattern, x_line["command"]):
				lastpid=x_line["pid"]
				#laststatus=x_line["status"]
				lastline=copy.copy(x_line)
				break
		del x_pid, x_line

		#If no record found
		if len(result_list) == 0: 
			#If cmdpattern is found in self.previous, then process is stopped
			if lastline == {}:
				result={"status":"missing"}
				currentstatus="missing"
			else:
				result=lastline
			currentstatus="stopped"

		#If duplicate records are found
		elif len(result_list) > 1:

			#Sort latest process first
			result_list.sort(key = lambda x: (x["elapsedSecond"], x["pid"]), reverse=True )
			result=result_list.pop(0)
			currentstatus="duplicated"
			result["duplicateList"]=result_list

		#Else, exactly one record is found
		else:
			result=result_list[0]
			#Process already exists in self.previous
			currentstatus="running"


		#Delta status calculation
		if   currentstatus=="duplicated":
			result["status"] = "duplicated"

		elif lastpid == None and currentpid != None:
			result["status"] = "started"

		elif lastpid == None and currentpid == None:
			result["status"] = "missing"

		elif lastpid == currentpid and currentstatus == "running":
			result["status"] = "running"

		elif lastpid != None and currentpid == None:
			result["status"] = "stopped"

		elif lastpid != currentpid:
			result["status"] = "restarted"


		#print(lastpid, currentpid, currentstatus, "\n  ", end="")

		return result

ps=psFetcher()

while True:
	#ps._getAll(command='tail -F toto') # pid=4246, user='root')
	#print('python',ps.new)

	ps.refresh()
	toto=ps.getSpecificProcess(cmdpattern='*tail -F toto*')
	titi=ps.getSpecificProcess(cmdpattern='*tail -F titi*')
	#print (  a["status"] )
	print ('toto:',toto["status"], '- titi:',titi["status"])
	time.sleep(2)


	#print(ps.previous)
#for line in ps.ps:
#	print(line)


