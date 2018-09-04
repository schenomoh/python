#!/usr/bin/python3.4
#!/usr/bin/python
####################################################
#
#  https://github.com/schenomoh/python
#
####################################################

# ./kudiff -p ../training/res/diff.param -r HELLO -1 ../training/res/media_library.csv -2 ../training/res/media_library.csv

### Sample param file ######
#[GLOBAL]
#file1_defaultdir=$HOME/APR/python
#file2_defaultdir=$HOME/APR/python
#
#[OVERRIDE]
#LOAD_DATE=2018-16-02
#
#[HELLO]
#FILE1=$file1_defaultdir/training/res/media_library.csv
#FILE2=$HOME/APR/python/training/res/media_library2.csv
#
#IGNORE_FIELD=load_id, LAST_UPDATE,
#res.compare_key=Main artist, Album, Track Id, 

import csv, io, sys, getopt, copy, os
import configparser
import json


####################################################
# Returns the list of duplicated values
#
def get_duplicate(list):
	found=[]
	duplicate=[]
	for key in list:
		#If we discover a new value, put it in "found"
		#If the value was already found, it is a duplicate
		if key not in found:
			found.append(key)
		else:
			duplicate.append(key)
	return duplicate

####################################################
# Class to store the result
#
class kudiff:

	def __init__(self, 
				defaultdir=os.getcwd(), 
				paramfile_name="kudiff.param",
				file1_defaultdir=None,
				file2_defaultdir=None,
				compare_rule=None,
				file1_name=None,
				file2_name=None
				):
		self.record=[]
		self.tmpdetail=[]
		self.defaultdir = defaultdir
		self.paramfile_name = paramfile_name

		self.file1_defaultdir = file1_defaultdir
		self.file2_defaultdir = file2_defaultdir

		self.file1_name=file1_name
		self.file2_name=file2_name

		self.file1_name_init=file1_name
		self.file2_name_init=file2_name
		
		self.compare_rule=compare_rule
		self.compare_key=[] # Field names from param file or input
		self.compare_dict={} #Field name and id 
		self.ignore_field=None


	#Add a result at the end of the record[] array
	#def result(self, status, message, detail=""):
	#	self.record.append({'status':status, 'message':message, 'detail':[]})

	def success(self, message):
		self.record.append({'status':'SUCCESS', 'message':message, 'detail':self.tmpdetail})
		self.tmpdetail=[]
	def failure(self, message):
		self.record.append({'status':'FAILURE', 'message':message, 'detail':self.tmpdetail})
		self.tmpdetail=[]
	def warning(self, message):
		self.record.append({'status':'WARNING', 'message':message, 'detail':[]})
		#self.tmpdetail=[]
	def error(self, message):
		self.record.append({'status':'ERROR  ', 'message':message, 'detail':self.tmpdetail})
		self.tmpdetail=[]
		self.bye()
	def bye(self, return_code=0):
		print(self)
		sys.exit(return_code)

	#Add a warning on the last result created
	def detail(self, detail):
		self.record[-1]['detail'].append(detail)

	def preparedetail(self, detail):
		self.tmpdetail.append(detail)

	#Pretty print of the kudiff
	def __str__(self):

		print("DEBUG   -", self.compare_rule, "- defaultdir =",  self.defaultdir)
		print("DEBUG   -", self.compare_rule, "- file1_defaultdir =",  self.file1_defaultdir)
		print("DEBUG   -", self.compare_rule, "- file2_defaultdir =",  self.file2_defaultdir)
		print("DEBUG   -", self.compare_rule, "- file1_name =",  self.file1_name)
		print("DEBUG   -", self.compare_rule, "- file2_name =",  self.file2_name)
		print("DEBUG   -", self.compare_rule, "- paramfile_name =",  self.paramfile_name)
		if self.compare_key != []:
			print("DEBUG   -", self.compare_rule, "- compare_key =", str(set(self.compare_key)))
		else:
			print("DEBUG   -", self.compare_rule, "- compare_key =", None)
		if self.compare_dict != []:
			print("DEBUG   -", self.compare_rule, "- compare_dict =", str(self.compare_dict))
		else:
			print("DEBUG   -", self.compare_rule, "- compare_dict =", None)
		
		if self.ignore_field != None:
			print("DEBUG   -", self.compare_rule, "- ignore_field =", str(set(self.ignore_field)))

		res=""
		for data in self.record:
			if res != "": res+="\n"
			res += str(data['status']) + " - " + str(self.compare_rule) + " - " + str(data['message'])
			for w in data['detail']:
				res += "\n | "+data['status']+" - "+ str(self.compare_rule) + " - " +str(w)
		return res

	#print override for python prompt
	def __repr__(self):
		return __str__(self)


	def read_param(self):
		#Check param file exist

		self.paramfile_name = self.clean_path(self.paramfile_name)

		if not os.path.isfile(self.paramfile_name):
			res.preparedetail("It can be defined by script argument: --param")
			res.preparedetail("or by class constructor argument: 'paramfile_name'")
			self.error("Unable to find param file: '" + str(self.paramfile_name)+"'")

		#Open param file
		param = configparser.ConfigParser()
		param.read(self.paramfile_name)

		if 'GLOBAL' not in param.sections():
			res.preparedetail("Please create this section, let it empty if required")
			self.error("Unable to find [GLOBAL] section in param file: '"+self.paramfile_name+"'")

		#Get file1 default directory
		if "FILE1_DEFAULTDIR".lower() in param.options('GLOBAL'):
			mydir = param.get('GLOBAL', 'FILE1_DEFAULTDIR')
		else:
			mydir = '.'
		self.file1_defaultdir=self.clean_path(mydir)

		#Get file2 default directory
		if "FILE2_DEFAULTDIR".lower() in param.options('GLOBAL'):
			mydir = param.get('GLOBAL', 'FILE2_DEFAULTDIR')
		else:
			mydir = '.'
		self.file2_defaultdir=self.clean_path(mydir)

		#Ensure a section exists for the files to be compared
		if self.compare_rule not in param.sections():
			self.error("Unable to find ["+str(self.compare_rule)+"] section in param file: '"+self.paramfile_name+"'")


		#Read the param file
		if 'COMPARE_FIELD'.lower() not in param.options(self.compare_rule):
			 self.error("Unable to find COMPARE_FIELD")
		else:
			self.compare_key=[i.strip().lower() for i in param.get(self.compare_rule, 'COMPARE_FIELD').split(',')]
		if 'IGNORE_FIELD'.lower() not in param.options(self.compare_rule):
			self.warning("No section IGNORE_FIELD")
		else:
			self.ignore_field=[i.strip().lower() for i in param.get(self.compare_rule, 'IGNORE_FIELD').split(',')]



		#------------- Manage FILE1 -------------
		#If no FILE1_NAME, retrieve FILE1_NAME from param file
		if self.file1_name == None and "FILE1_NAME".lower() in param.options(self.compare_rule):
			self.file1_name = self.clean_path( param.get(self.compare_rule, "FILE1_NAME"))

		#If still no FILE1_NAME, raise a warning 
		if self.file1_name == None:
			self.error("FILE1_NAME is not defined")
		else:
		#Get file1_name full clean path
			self.file1_name = self.clean_path(self.file1_name)

		#------------- Manage FILE2 -------------
		#If no FILE2_NAME, retrieve FILE2_NAME from param file
		if self.file2_name == None and "FILE2_NAME".lower() in param.options(self.compare_rule):
			self.file2_name = self.clean_path( param.get(self.compare_rule, "FILE2_NAME"))

		#If still no FILE2_NAME, raise an exception
		if self.file2_name == None:
			self.error("FILE2_NAME is not defined")
		else:
		#Get file2_name full clean path
			self.file2_name = self.clean_path(self.file2_name)


	def check_isfile(self):
		#Ensure the file exists
		if not os.path.isfile(self.file1_name):
			res.preparedetail("It can be defined by script argument: --file1")
			res.preparedetail("or else by class constructor argument: 'file1_name'")
			res.preparedetail("or else by param file variable: 'FILE1_NAME'")
			self.error("Unable to find FILE1_NAME: '" + str(self.file1_name)+"'")
		
		#Ensure the file exists
		if not os.path.isfile(self.file2_name):
			res.preparedetail("It can be defined by script argument: --file2")
			res.preparedetail("or else by class constructor argument: 'file2_name'")
			res.preparedetail("or else by param file variable: 'FILE2_NAME'")
			self.error("Unable to find FILE2_NAME: '" + str(self.file2_name)+"'")


	def get_dialect(self):
		#----------------------------------------------------
		# Check the file dialects
		try:

			file1=open(self.file1_name, 'r')
			file2=open(self.file2_name, 'r')
			dialect1 = csv.Sniffer().sniff(file1.read(2000))
			dialect2 = csv.Sniffer().sniff(file2.read(2000))
			file1.seek(0)
			file2.seek(0)
		except:
			del(file1)
			del(file2)

			try:
				file1=open(self.file1_name, 'r')
				file2=open(self.file2_name, 'r')
				dialect1 = csv.Sniffer().sniff(file1.read(50))
				dialect2 = csv.Sniffer().sniff(file2.read(50))
				file1.seek(0)
				file2.seek(0)
			except Exception as e:
				self.error("Unable to open the csv files "+ str(e))

		#----------------------------------------------------
		# Manage missmatching dialects
		self.dialect1={
			'delimiter':str(dialect1.delimiter),
			'doublequote':dialect1.doublequote,
			'escapechar':(dialect1.escapechar),
			'lineterminator':str(dialect1.lineterminator),
			'quotechar':(dialect1.quotechar),
			'quoting':(dialect1.quoting),
			'skipinitialspace':(dialect1.skipinitialspace)
		}

		self.dialect2={
			'delimiter':str(dialect2.delimiter),
			'doublequote':dialect2.doublequote,
			'escapechar':(dialect2.escapechar),
			'lineterminator':str(dialect2.lineterminator),
			'quotechar':(dialect2.quotechar),
			'quoting':(dialect2.quoting),
			'skipinitialspace':(dialect2.skipinitialspace)
		}

		if self.dialect1['delimiter'] not in [',', ';', '|'] :
			self.error("Unable to determine the field delimiter for '"+self.file1_name+"'. This shall be due to a missmatching number or fields on the first few records.")

		if self.dialect2['delimiter'] not in [',', ';', '|'] :
			self.error("Unable to determine the field delimiter for '"+self.file2_name+"'. This shall be due to a missmatching number or fields on the first few records.")

	# Get the absolute path of a file
	#  mypath: file path and name
	#  defaultdir: default directory of the file. if empty, self.defaultdir will be used
	def clean_path(self, mypath, defaultdir=None):
		#file1_name
		if defaultdir == None: 
			defaultdir = self.defaultdir
		mypath = os.path.expandvars(mypath)
		if mypath[0] != '/':
			mypath = os.path.abspath( defaultdir +'/' + mypath )
		else:
			mypath = os.path.abspath(mypath)

		return mypath

	#Retrieve the key for a single input csv record
	def get_key(self, record, prettyPrint=False):

		if not prettyPrint:
			out=[]
			for name, number in self.compare_dict.items():
				out.append(record[number])
			return out
		else:
			out={}
			for name, number in self.compare_dict.items():
				out[name]=record[number]
			return str(out)


#################################################"
def _usage(errorMessage=None):
	print(" Usage: " + sys.argv[0] +" [OPTIONS]")
	print("   -h, --help: this help")
	print("   -p, --param: param file location")
	print("   -r, --rule: section of the param file containing the comparaison rules")
	print("   -1, --file1: reference file for comparaison")
	print("   -2, --file1: file compared")
	if errorMessage != None:
		print("\n", errorMessage)
	sys.exit(2)



if __name__ == '__main__':

	res=kudiff()

	try:
		optlist, args = getopt.getopt(sys.argv[1:], 'p:r:1:2:h', ['help', 'param=', 'rule=', 'file1=', 'file2=', 'separator='])
	except:
		_usage()

	for opt, a in optlist:
		if opt in ('-h', '--help'):
			_usage()
		if opt in ('-p', '--param'):
			res.paramfile_name=a
		if opt in ('-r', '--rule'):
			res.compare_rule=a
		if opt in ('-1', '--file1'): res.file1_name=a
		if opt in ('-2', '--file2'): res.file2_name=a

	res.read_param()
	res.check_isfile()
	res.get_dialect()

	checkFailed=False
	for key in res.dialect1:
		if res.dialect1[key] !=  res.dialect2[key]:
			checkFailed=True
			res.preparedetail("CSV dialect missmatch. " + str(key) + " is '"+str( res.dialect1[key])
			+ "' in file1 but '"+str( res.dialect2[key])+"' in file2")

	try:

		tmp={k:v for k,v in res.dialect1.items() }
		if tmp['escapechar'] == None or tmp['escapechar'] == 'None':
			tmp.pop('escapechar', None)
		csv1=csv.reader(open(res.file1_name, 'r'), **tmp)

	except Exception as e:
		res.error("Unable to read file1 '" + res.file2_name + "', "+ str(e) )

	try:

		tmp={k:v for k,v in res.dialect2.items() }
		if tmp['escapechar'] == None or tmp['escapechar'] == 'None':
			tmp.pop('escapechar', None)

		csv2=csv.reader(open(res.file2_name, 'r'), **tmp)
		del tmp

	except Exception as e:
		res.error("Unable to read file2 '" + res.file2_name + "', "+ str(e) )

	#----------------------------------------------------
	# Manage header logic

	for header1 in csv1:
		header1=[i.lower() for i in header1]
		break
	for header2 in csv2:
		header2=[i.lower() for i in header2]
		break


	#Ensure there is no duplicate in headers
	if len(get_duplicate(header1)): res.error("Header 1 has duplicated fields: "+ str(get_duplicate(header1)))
	if len(get_duplicate(header2)):	res.error("Header 2 has duplicated fields: "+ str(get_duplicate(header2)))

	#Ensure all the compare key fields are available in header file
	if len(set(res.compare_key) - set(header1)) != 0:	res.error("Key fields are missing in header1: "+str(set(res.compare_key) - set(header1)))
	if len(set(res.compare_key) - set(header2)) != 0:	res.error("Key fields are missing in header2: "+str(set(res.compare_key) - set(header2)))

	if header1 == header2:
		pass
	elif header1[:len(header1)] == header2[:len(header1)]:
		res.warning("Header2 match with additional fields: "+str(list(set(header2)-set(header1))))
	elif len(set(header1) - set(header2))==0:
		checkFailed=True
		res.preparedetail("Header2 order missmatch")
		res.preparedetail("Header 1: "+ str(header1))
		res.preparedetail("Header 2: "+ str(header2))
	else:
		checkFailed=True
		missing=set(header1)-set(header2)
		if missing != set():
			res.preparedetail("Missing in header2:" + str(missing))
		missing=set(header2)-set(header1)
		if missing != set():
			res.preparedetail("Missing in header1:" + str(missing))
		del missing
		res.error("Header2 field name missmatch")


	#Store both field number and field name in the res.compare_dict variable
	res.compare_dict={fieldName: header1.index(fieldName) for fieldName in res.compare_key}

	#Number of fields required to be able to retrive the compare key

	required_fieldcount = max({ v for k,v in res.compare_dict.items()}) + 1 

	#Fetch fields from files
	#Do not forget header were already fetched
	content1=[]
	content2=[]



	#Read all rows and ensure they contains the compare key
	for record1 in csv1:
		if len(record1)>=required_fieldcount:
			record1.append(csv1.line_num)
			content1.append(record1)
		else:
			#Ignore blank line
			if len(record1)==0: continue
			#Log error
			checkFailed=True
			res.preparedetail("File1, Missing compare key for " + str(csv1.line_num) + ": " + str(record1))

	#Read all rows and ensure they contains the compare key
	for record2 in csv2:
		if len(record2)>=required_fieldcount:
			record2.append(csv2.line_num)
			content2.append(record2)
		else:
			#Ignore blank line
			if len(record2)==0: continue
			#Log error
			checkFailed=True
			res.preparedetail("File2, Missing compare key for " + str(csv2.line_num) + ": " + str(record2))

	if checkFailed:
		res.failure("File format missmatch")
	else:
		res.success("File format match")
	del checkFailed
	checkFailed=False

	#sort the content of my files
	content1.sort(key=res.get_key)
	content2.sort(key=res.get_key)



	#----------------------------------------------------
	#Remove duplicate in file 1

	i=0
	while len(content1) > i+1:
		if res.get_key(content1[i]) == res.get_key(content1[i+1]):
			#checkFailed=True
			#res.preparedetail("File 1 duplicate skipped "+res.get_key(content1[i], True))
			res.preparedetail(  "Duplicated key: "+res.get_key(content1[i], True) +" at lines "+str(content1[i][-1]) +" and " + str(content1[i+1][-1])  )
			res.error(  "File 1 duplicated key found")
			del(content1[i])
			i=i-1
		i=i+1


	#----------------------------------------------------
	#Remove duplicate in file 2

	i=0
	while len(content2) > i+1:
		if res.get_key(content2[i]) == res.get_key(content2[i+1]):
			checkFailed=True
			res.preparedetail(  "Duplicated key: "+res.get_key(content2[i], True) +" at lines "+str(content2[i][-1]) +" and " + str(content2[i+1][-1])  )
			del(content2[i])
			i=i-1
		i=i+1

	if checkFailed:
		res.failure("Duplicated records found in file 2")
	else:
		res.success("No duplicated record in file 2")


	unexpected=[]
	#----------------------------------------------------
	#Loop on file1
	while len(content1) > 0 and len(content2) > 0 :
		key1=res.get_key(content1[0])
		key2=res.get_key(content2[0])
		if key1 < key2:
			res.failure("missing record in file2" + res.get_key(content1[0], True))
			del content1[0]
		elif key1 > key2:
			unexpected.append(res.get_key(content1[0], True))
			del content2[0]
		else:
			#Process the field comparaison
			fieldNum=0
			checkFailed=False
			for field in content1[0][:-1]:
				if header1[fieldNum] not in res.ignore_field:
					if field != content2[0][fieldNum]:
						checkFailed=True
						res.preparedetail( "File 1 {'" + str(header1[fieldNum]) +"': " + str(field) +"}" )
						res.preparedetail( "File 2 {'"+ str(header1[fieldNum])  +"': " + str(content2[0][fieldNum])+"}" )
				fieldNum+=1
			if checkFailed:
				res.preparedetail("Data extracted from file 1 at line "+ str(content1[0][-1]) +", and from file 2 at line " +str(content2[0][-1]))
				res.failure("Key: "+ res.get_key(content1[0], prettyPrint=True))
				# 
			else:
				res.success("Key: " + res.get_key(content1[0], prettyPrint=True) )
			del checkFailed

			del content1[0]
			del content2[0]


	#----------------------------------------------------
	#Trailing missing records from file1
	for record in content1:
		res.failure("missing record in file2" + res.get_key(record, True))

	checkFailed=False
	#----------------------------------------------------
	#Trailing unexpected records in file2
	for record in content2:
		checkFailed=True
		unexpected.append(res.get_key(record))
	if unexpected != []:
		checkFailed=True
		for detail in unexpected:
			res.preparedetail("Unexpected file 2 record: " + str(detail))


	if checkFailed:
		res.failure("File 2 has unexpected records")
	else:
		res.success("File 2 has no additional record")


	res.bye()

