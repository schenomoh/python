#!/usr/bin/env python3

####################################################
#
#  https://github.com/schenomoh/python
#
####################################################

# ./kudiff.py -p ../training/res/diff.param -r HELLO -1 ../training/res/media_library.csv -2 ../training/res/media_library.csv

from json import dumps as json_dumps

#################################################"
def _usage(errorMessage=None):
	print("""
This script compares CSV files. Please note its main caracteristics:
=> Designed to compare 10k lines CSV with Unix shell
=> Store everything in memory
=> Functions have side effects
=> Adapted for JSON and Windows

== Example: explicit path in script call ==

$HOME/m2r/python_lib/kudiff.py --file1=$HOME/APR/CHAINTEST/prod.csv --file2=$HOME/APR/CHAINTEST/u01.csv --rule=M2R_DTM_MIFID --param $HOME/APR/CHAINTEST/test.param
test.param
	[GLOBAL]
	[M2R_DTM_MIFID]
	PRIMARY_KEY=REPORTINGID, REPORTINGVERSION, REPORTINGTYPE, SOURCENAME, DATE_APPLI
	IGNORE_FIELD=MIFIDKEYID, DATE_SESSION

== Example: no path specified. All files have to be in the current folder ==

$HOME/m2r/python_lib/kudiff.py --rule=M2R_DTM_MIFID
kudiff.param
	[GLOBAL]
	[M2R_DTM_MIFID]
	PRIMARY_KEY=REPORTINGID, REPORTINGVERSION, REPORTINGTYPE, SOURCENAME, DATE_APPLI
	IGNORE_FIELD=MIFIDKEYID, DATE_SESSION
	FILE1=prod.csv
	FILE2=u01.csv

== Script argument ==
		""")
	print(" Usage: " + sys.argv[0] +" [OPTIONS]")
	print("   -h, --help: this help")
	print("   -p, --param: param file location")
	print("   -r, --rule: section of the param file containing the comparaison rules")
	print("   -1, --file1: reference file for comparaison")
	print("   -2, --file1: file compared")

	if errorMessage != None:
		print("\n", errorMessage)
	sys.exit(2)




import csv, io, sys, getopt, copy, os
import configparser
import json

#Identify if path separator is force slash or anti slash
if os.path.abspath('.').count('/') > 0:
  OS_PATHSEPARATOR='/'
else:
  OS_PATHSEPARATOR = '\\'

####################################################
# Returns the list of duplicated values
#
def _get_duplicate_in_csv(list):
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

class Log:
	def __init__(self, 
				defaultdir=os.getcwd(), 
				paramfile_name="kudiff.param",
				file1_defaultdir=None,
				file2_defaultdir=None,
				compare_rule=None,
				file1_name=None,
				file2_name=None
				):
		self.result=[]
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
		self.compare_dict2={}
		self.ignore_field=None
		self.lastErrorObject=None

	def success(self, group, **arg): self._store_result(status='SUCCESS', group=group, **arg)
	def failure(self, group, message=None, **arg): self._store_result(status='FAILURE', group=group, message=message, **arg)
	def debug(self, group, message=None, **arg): self._store_result(status='DEBUG', group=group, message=message, **arg)
	
	
	def error  (self, group, message=None, **arg): 
		self._store_result(status='ERROR', group=group, message=message, **arg)
		
		#Print status when called from Shell
		if __name__ == '__main__':
			print(self)
			sys.exit(-1)
		#Raise clean exception when imported as library
		else:
			raise BaseException(message)

	def _store_result(self, status, group, message=None, key=None, file1_value=None, file2_value=None, fieldname=None, file1_offset=None, file2_offset=None, file1_line=None, file2_line=None):
		compare_rule=self.compare_rule

		#Replace the variable names in $message
		var_replace={'$defaultdir':self.defaultdir,
		'$paramfile_name':self.paramfile_name,
		'$file1_defaultdir':self.file1_defaultdir,
		'$file2_defaultdir':self.file2_defaultdir,
		'$file1_name':self.file1_name,
		'$file2_name':self.file2_name,
		'$file1_name_init':self.file1_name_init,
		'$file2_name_init':self.file1_name_init,
		'$compare_rule':self.compare_rule,
		'$compare_key':str(self.compare_key),
		'$compare_dict':str(self.compare_dict),
		'$ignore_field':str(self.ignore_field)}
		for var, val in var_replace.items():
			if not val: val = 'None'
			if message:	message=message.replace(var, val)
		del var_replace, var, val

		if group and not key : key = group

		self.result.append(  dict({ (i,j) for i,j  in locals().items() if j and i !='self' }) )

	def __str__(self):
		return self.dump(format="STRING")

	#print override for python prompt
	def __repr__(self):
		return self.dump(format="STRING")

	def dump(self, format="JSON", delimiter=' ; '):
		
		#Basic output: pseudo array
		if format=="JSON":
			output={
				'paramfile_name':self.paramfile_name,
				'compare_rule':self.compare_rule,
				'file1_name':self.file1_name,
				'file2_name':self.file2_name,
				'ignore_field':self.ignore_field, 
				'compare_key':self.compare_key,
				'result':[]}
			last_rule = None
			last_key = None
			
			#Get status of init. When sorting alphabetically, order will be: ERROR, FAILURE, SUCCESS
			init_status = sorted([a['status'] for a in self.result if a['group']=='INIT' ])[0]
			output['result'].append( 
				{#'key': dict(zip(self.compare_key, last_key)),
				'group': 'INIT',
				'status': init_status,
				'details':[]
				}
			)
			
			
			#If new key found, create new entry in output result
			for line in self.result:
				#print(line)
				if line['key'] != last_key and line['group'] != 'INIT':
					last_key = line['key']
					output['result'].append( 
						{'key': dict(zip(self.compare_key, last_key)),
						'group': line['group'],
						'status': line['status'],
						'details':[]
						}
					)
					
				if 'message' in line:
					output['result'][-1]['message']=line['message']
				#Add diff details at the end of output result
				if 'fieldname' in line:
					output['result'][-1]['details'].append({
						'fieldname':line['fieldname'],
						'file1_value':line['file1_value'],
						'file2_value':line['file2_value'],
						'file1_line':line['file1_line'],
						'file2_line':line['file2_line']
						})

		
			return json_dumps(output, indent=2, ensure_ascii=False)
		
		else:
		#Manage CSV like format
			output=[]
			#Debug data
			output.append( delimiter.join([ str(self.compare_rule), 'DEBUG  ', 'INIT', '(INIT)',  "$paramfile_name = '"+str(self.paramfile_name)+"'" ])  ) 
			output.append( delimiter.join([ str(self.compare_rule), 'DEBUG  ', 'INIT', '(INIT)',  "$file1_name = '"+str(self.file1_name)+"'" ])  ) 
			output.append( delimiter.join([ str(self.compare_rule), 'DEBUG  ', 'INIT', '(INIT)',  "$file2_name = '"+str(self.file2_name)+"'" ])  ) 
			output.append( delimiter.join([ str(self.compare_rule), 'DEBUG  ', 'INIT', '(INIT)',  "$ignore_field = "+str(self.ignore_field) ])  ) 
			output.append( delimiter.join([ str(self.compare_rule), 'DEBUG  ', 'INIT', '(INIT)',  "$compare_key = "+str(self.compare_key) ])  ) 


			for record in self.result:
				#First fields
				if 'compare_rule' in record: compare_rule = record['compare_rule']
				else: compare_rule = "None"
				tmp = [compare_rule, record['status'].ljust(7), record['group'] ] 
				#Manage the key
				if record['group'] == 'INIT' : tmp += [ '('+record['key']+')' ]
				else: tmp += [ str(  '-'.join((record['key']))  ) ]

				if 'message' in record: tmp += [ record['message'] ]
				elif 'fieldname' in record :
					if 'file1_value' in record: val1 = record['file1_value']
					else: val1 = ''
					if 'file2_value' in record: val2 = record['file2_value']
					else: val2 = ''

					expected = [ "File 1 {} = '{}' at line {}".format( record['fieldname'], val1, record['file1_line'] ) ] 
					output.append(delimiter.join(tmp + expected) )
					tmp += [ "File 2 {} = '{}' at line {}".format( record['fieldname'], val2, record['file2_line'] ) ]
				else:
					tmp += [ '' ] # No message
				output.append(delimiter.join(tmp) )

			return '\n'.join(output)


	def read_param(self):
		#Check param file exist

		self.paramfile_name = self._clean_path(self.paramfile_name)

		if not os.path.isfile(self.paramfile_name):
			self.error("INIT", "Unable to find param file '$paramfile_name'. It can be defined by script argument: --param or by class constructor argument: paramfile_name='/mydir/myfile.param'")

		#Open param file
		param = configparser.ConfigParser()
		try:
			param.read(self.paramfile_name)
		except Exception as e:
			self.lastErrorObject = e
			pass
		#Use script custom error management, if any
		if self.lastErrorObject is not None:
			self.error("INIT", str(self.lastErrorObject).replace('\n',' - '))
		else:
			self.lastErrorObject = None
			
		if 'GLOBAL' not in param.sections():
			self.error("INIT", "Unable to find [GLOBAL] section in param file '$paramfile_name'")

		#Get file1 default directory
		if "FILE1_DEFAULTDIR".lower() in param.options('GLOBAL'):
			mydir = param.get('GLOBAL', 'FILE1_DEFAULTDIR')
		else:
			mydir = '.'
		self.file1_defaultdir=self._clean_path(mydir)

		#Get file2 default directory
		if "FILE2_DEFAULTDIR".lower() in param.options('GLOBAL'):
			mydir = param.get('GLOBAL', 'FILE2_DEFAULTDIR')
		else:
			mydir = '.'
		self.file2_defaultdir=self._clean_path(mydir)

		#Ensure a section exists for the files to be compared
		if self.compare_rule not in param.sections():
			self.error("INIT", "Unable to find [$compare_rule] section in param file: '$paramfile_name'")


		#Read the param file
		if 'PRIMARY_KEY'.lower() not in param.options(self.compare_rule):
			 self.error("INIT", "Unable to find $compare_rule.PRIMARY_KEY in '$paramfile_name'")
		else:
			self.compare_key=[i.strip().lower() for i in param.get(self.compare_rule, 'PRIMARY_KEY').split(',')]
		if 'IGNORE_FIELD'.lower() not in param.options(self.compare_rule):
			self.debug("INIT", "No key $compare_rule.IGNORE_FIELD in '$paramfile_name'")
		else:
			self.ignore_field=[i.strip().lower() for i in param.get(self.compare_rule, 'IGNORE_FIELD').split(',')]

		#------------- Manage FILE1 -------------
		#If no FILE1, retrieve FILE1 from param file
		if self.file1_name == '' : self.file1_name = None
		if self.file1_name == None and "FILE1".lower() in param.options(self.compare_rule):
			self.file1_name = self._clean_path( param.get(self.compare_rule, "FILE1"), self.file1_defaultdir) 

		#If still no FILE1, raise a warning 
		if self.file1_name == None:
			self.error("INIT", "Please define parameter '--file1' or class attribute file1_name")
		else:
		#Get file1_name full clean path
			self.file1_name = self._clean_path(self.file1_name)

		#------------- Manage FILE2 -------------
		#If no FILE2, retrieve FILE2 from param file
		if self.file2_name == '' : self.file2_name = None
		if self.file2_name == None and "FILE2".lower() in param.options(self.compare_rule):
			self.file2_name = self._clean_path( param.get(self.compare_rule, "FILE2"), self.file2_defaultdir)

		#If still no FILE2, raise an exception
		if self.file2_name == None:
			self.error("INIT", "Please define parameter '--file2' or class attribute file2_name")
		else:
		#Get file2_name full clean path
			self.file2_name = self._clean_path(self.file2_name)

		#------------- Manage dialect -------------
		if 'DELIMITER1'.lower() in param.options(self.compare_rule):
			self.debug("INIT", "CSV format sniffer disabled for file1")
			try:
				self.dialect1={
					'delimiter':param.get(self.compare_rule, "DELIMITER1").replace('\\t', '\t'),
					'doublequote':param.get(self.compare_rule, "DOUBLEQUOTE1"),
					'escapechar':param.get(self.compare_rule, "ESCAPECHAR1"),
					'lineterminator':  (param.get(self.compare_rule, "LINETERMINATOR1")).replace('\\n','\n').replace('\\r','\r'),
					'quotechar':param.get(self.compare_rule, "QUOTECHAR1"),
					'quoting':int(param.get(self.compare_rule, "QUOTING1")),
					'skipinitialspace':param.get(self.compare_rule, "SKIPINITIALSPACE1")
				}
			except:
				self.error("INIT", "DELIMITER1 is set for file1. All the other properties must also be set: DOUBLEQUOTE1, ESCAPECHAR1, LINETERMINATOR1, QUOTECHAR1, QUOTING1, SKIPINITIALSPACE1")

		if 'DELIMITER2'.lower() in param.options(self.compare_rule):
			self.debug("INIT", "CSV format sniffer disabled for file2")
			try:
				self.dialect2={
					'delimiter':param.get(self.compare_rule, "DELIMITER2").replace('\\t', '\t'),
					'doublequote':param.get(self.compare_rule, "DOUBLEQUOTE2"),
					'escapechar':param.get(self.compare_rule, "ESCAPECHAR2"),
					'lineterminator':  (param.get(self.compare_rule, "LINETERMINATOR2")).replace('\\n','\n').replace('\\r','\r'),
					'quotechar':param.get(self.compare_rule, "QUOTECHAR2"),
					'quoting':int(param.get(self.compare_rule, "QUOTING2")),
					'skipinitialspace':param.get(self.compare_rule, "SKIPINITIALSPACE2")
				}
			except:
				self.error("INIT", "DELIMITER2 is set for file2. All the other properties must also be set: DOUBLEQUOTE2, ESCAPECHAR2, LINETERMINATOR2, QUOTECHAR2, QUOTING2, SKIPINITIALSPACE2")
			
	def check_isfile(self):
		#Ensure the file exists
		if not os.path.isfile(self.file1_name):
			self.error("INIT", "Unable to find file1_name='$file1_name'")
		
		#Ensure the file exists
		if not os.path.isfile(self.file2_name):
			self.error("INIT", "Unable to find file2_name='$file2_name'")


			
			

		#----------------------------------------------------
		# Check the file dialects
	def sniff_dialect1(self):
	
		#If dialect already set, no need to sniff
		if hasattr(self, 'dialect1'): return
		
		#Check dialect1
		try:

			file1=open(self.file1_name, 'r')
			dialect1 = csv.Sniffer().sniff(file1.read(2000))
			file1.seek(0)
		except:
			del(file1)
			try:
				file1=open(self.file1_name, 'r')
				dialect1 = csv.Sniffer().sniff(file1.read(50))
				file1.seek(0)
			except Exception as e:
				self.error("INIT", self.file1_name + ": "+str(e)+". Common root causes are: empty file with no header, field count mismatch on the few first lines, string quote missmatch, string with carriage return not enclosed in quote, string with unescaped inner quote, file has less than 50 caracters. To disable sniffer feature, please define DELIMITER1 in param file")

		self.dialect1={
			'delimiter':str(dialect1.delimiter),
			'doublequote':dialect1.doublequote,
			'escapechar':(dialect1.escapechar),
			'lineterminator':str(dialect1.lineterminator),
			'quotechar':(dialect1.quotechar),
			'quoting':(dialect1.quoting),
			'skipinitialspace':(dialect1.skipinitialspace)
		}
				
		if self.dialect1['delimiter'] not in [',', ';', '|', '\t'] :
			self.error("INIT","CSV format sniffer determined an unexpected delimiter for file1: " + repr(self.dialect1['delimiter']) +". You can enforce this DELIMITER1 value in param file")


			
			
			
	def sniff_dialect2(self):
		#If dialect already set, no need to sniff
		if hasattr(self, 'dialect2'): return
		
		try:
			file2=open(self.file2_name, 'r')
			dialect2 = csv.Sniffer().sniff(file2.read(2000))
			file2.seek(0)
		except:
			del(file2)
			try:
				file2=open(self.file2_name, 'r')
				dialect2 = csv.Sniffer().sniff(file2.read(50))
				file2.seek(0)
			except Exception as e:
				self.error("INIT", self.file2_name + ": "+str(e)+". Common root causes are: empty file with no header, field count mismatch on the few first lines, string quote missmatch, string with carriage return not enclosed in quote, string with unescaped inner quote, file has less than 50 caracters. To disable sniffer feature, please define DELIMITER2 in param file")

		#Check dialect2
		self.dialect2={
			'delimiter':str(dialect2.delimiter),
			'doublequote':dialect2.doublequote,
			'escapechar':(dialect2.escapechar),
			'lineterminator':str(dialect2.lineterminator),
			'quotechar':(dialect2.quotechar),
			'quoting':(dialect2.quoting),
			'skipinitialspace':(dialect2.skipinitialspace)
		}

		if self.dialect2['delimiter'] not in [',', ';', '|', '\t'] :
			self.error("INIT","CSV format sniffer determined an unexpected delimiter for file2: " + repr(self.dialect2['delimiter']) +". You can enforce this DELIMITER1 value in param file")

			
			
	def compare_csv(self):			
		#----------------------------------------------------
		# Manage missmatching dialects


		checkFailed=False
		for key in self.dialect1:
			value1=repr(str(self.dialect1[key]))[1:-1]
			value2=repr(str(self.dialect2[key]))[1:-1]
			if value1 != value2:
				checkFailed=True
				#self.failure('INIT', "CSV dialect missmatch. " + str(key) + " is '"+value1
				#+ "' in file1 but '"+value2+"' in file2")
				self.failure("INIT", key='INIT', 
					file1_value = value1,
					file2_value = value2,
					file1_line = 1,
					file2_line = 1,
					fieldname = "__"+str(key)+"__"
					)
		try:

			tmp={k:v for k,v in self.dialect1.items() }
			if tmp['escapechar'] == None or tmp['escapechar'] == 'None':
				tmp.pop('escapechar', None)
			csv1=csv.reader(open(self.file1_name, 'r'), **tmp)

		except Exception as e:
			self.error('INIT', "Unable to read file1='$file1_name' "+ str(e) )

		try:

			tmp={k:v for k,v in self.dialect2.items() }
			if tmp['escapechar'] == None or tmp['escapechar'] == 'None':
				tmp.pop('escapechar', None)

			csv2=csv.reader(open(self.file2_name, 'r'), **tmp)
			del tmp

		except Exception as e:
			self.error('INIT',"Unable to read file2='$file2_name' "+ str(e) )


		#----------------------------------------------------
		# Manage header logic

		for header1 in csv1:
			header1=[i.lower() for i in header1]
			break
		for header2 in csv2:
			header2=[i.lower() for i in header2]
			break


		#Ensure there is no duplicate in headers
		if len(_get_duplicate_in_csv(header1)): self.error('INIT', "Header 1 has duplicated fields: "+ str(_get_duplicate_in_csv(header1)))
		if len(_get_duplicate_in_csv(header2)):	self.error('INIT', "Header 2 has duplicated fields: "+ str(_get_duplicate_in_csv(header2)))

		#Ensure all the compare key fields are available in header file
		if len(set(self.compare_key) - set(header1)) != 0:	self.error('INIT',"Key fields are missing in header1"+str(set(self.compare_key) - set(header1)))
		if len(set(self.compare_key) - set(header2)) != 0:	self.error('INIT',"Key fields are missing in header2: "+str(set(self.compare_key) - set(header2)))

		if header1 == header2:
			pass
		elif header1[:len(header1)] == header2[:len(header1)]:
			checkFailed=True
			self.failure("INIT", "Header2 match with additional fields: "+str(list(set(header2)-set(header1))))
		elif len(set(header1) - set(header2))==0:
			checkFailed=True
			#self.failure("INIT", "Header 2 has wrong field order") 
			self.failure("INIT", 
			fieldname="__header__",
			file1_value = str(header1),
			file2_value = str(header2),
			file1_line = "1",
			file2_line = "1"
			)
			#self.failure("INIT", "Header 1: "+ str(header1))
			#self.failure("INIT", "Header 2: "+ str(header2))
		else:
			checkFailed=True
			missing=set(header1)-set(header2)
			if missing != set():
				self.error("INIT", "Missing in header2:" + str(missing))
			missing=set(header2)-set(header1)
			if missing != set():
				self.failure("INIT", "Missing in header1:" + str(missing))
			del missing
			#self.error('INIT', "Header2 field name missmatch")


		#Store both field number and field name in the self.compare_dict variable
		self.compare_dict={fieldName: header1.index(fieldName) for fieldName in self.compare_key}
		self.compare_dict2={fieldName: header2.index(fieldName) for fieldName in self.compare_key}
		#Number of fields required to be able to retrive the compare key

		required_fieldcount = max({ v for k,v in self.compare_dict.items()}) + 1 

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
				self.failure("INIT", "File1, Missing compare key at line " + str(csv1.line_num) + ": " + str(record1))

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
				self.failure("INIT", "File2, Missing compare key at line " + str(csv2.line_num) + ": " + str(record2))

		if checkFailed:
		#	self.failure('INIT',"File format missmatch")
			pass
		else:
			self.success('INIT',message="File format match")
		del checkFailed
		checkFailed=False


		#sort the content of my files
		content1.sort(key=self._get_key)
		content2.sort(key=self._get_key2)

		#----------------------------------------------------
		#Remove duplicate in file 1

		i=0
		while len(content1) > i+1:
			if self._get_key(content1[i]) == self._get_key(content1[i+1]):
				#checkFailed=True
				#self.preparedetail("INIT", "File 1 duplicate skipped "+self._get_key(content1[i], True))
				self.error("INIT", "Compare_key " + str(self._get_key(content1[i])) + " is duplicated in file 1: "+ " at lines " + str(content1[i][-1]) + " and " + str(content1[i+1][-1]) )
				#" at lines "+str(content1[i][-1]) +" and " + str(content1[i+1][-1])  )
				#self.error('MAIN',  "File 1 duplicated key found")
				del(content1[i])
				i=i-1
			i=i+1


		#----------------------------------------------------
		#Remove duplicate in file 2

		i=0
		while len(content2) > i+1:
			if self._get_key2(content2[i]) == self._get_key2(content2[i+1]):
				checkFailed=True
				self.failure("MAIN", "Duplicated key in file 2 at lines " +  str(content2[i][-1]) + ' and ' +str(content2[i+1][-1]), 
					key=self._get_key2(content2[i])
					)
				# +" at lines "+str(content2[i][-1]) +" and " + str(content2[i+1][-1])  )
				del(content2[i])
				i=i-1
			i=i+1

	#	if checkFailed:
	#		self.failure("INIT", "Duplicated records found in file 2")
	#	else:
	#		self.success("INIT", message="No duplicated record in file 2")


		unexpected=[]
		#----------------------------------------------------
		#Loop on file1
		while len(content1) > 0 and len(content2) > 0 :
			key1=self._get_key(content1[0])
			key2=self._get_key2(content2[0])
			if key1 < key2:
				self.failure("MAIN", "Missing record in file 2", key=self._get_key(content1[0]))
				del content1[0]
			elif key1 > key2:
				unexpected.append(self._get_key2(content2[0], True))
				del content2[0]
			else:
				#Process the field comparaison
				fieldNum=0
				checkFailed=False
				for field in content1[0][:-1]:
					if self.ignore_field is None or header1[fieldNum] not in self.ignore_field:
						fieldNum2 = header2.index(header1[fieldNum])
						if field != content2[0][fieldNum2]:
							checkFailed=True
							#self.failure("MAIN",  "File 1 {'" + str(header1[fieldNum]) +"': " + str(field) +"}" )
							#self.failure("MAIN",  "File 2 {'"+ str(header1[fieldNum])  +"': " + str(content2[0][fieldNum])+"}" )
							self.failure("MAIN", key=self._get_key(content1[0]), 
								file1_value = str(field),
								file2_value = str(content2[0][fieldNum2]),
								file1_line = str(content1[0][-1]),
								file2_line = str(content2[0][-1]),
								fieldname = str(header1[fieldNum])
								)
					fieldNum+=1
				if checkFailed:
					pass
					#self.failure("MAIN", "Data extracted from file 1 at line "+ str(content1[0][-1]) +", and from file 2 at line " +str(content2[0][-1]))
					#self.failure("MAIN", key=self._get_key(content1[0], prettyPrint=True)) 
				else:
					self.success("MAIN", key=self._get_key(content1[0]) )
				del checkFailed

				del content1[0]
				del content2[0]


		#----------------------------------------------------
		#Trailing missing records from file1
		for record in content1:
			self.failure("MAIN", "Missing record in file 2. For reference, please check file 1, line " +str(content1[0][-1]), key=self._get_key(record))

		checkFailed=False
		#----------------------------------------------------
		#Trailing unexpected records in file2
		for record in content2:
			checkFailed=True
			unexpected.append(self._get_key2(record))
		if unexpected != []:
			checkFailed=True
			for detail in unexpected:
				self.failure("MAIN", "Unexpected file 2 record: " + str(detail))


		if checkFailed:
			self.failure("MAIN", message="File 2 has unexpected records")
		#else:
		#	self.success("MAIN", message="File 2 has no additional record")



	# Get the absolute path of a file
	#  mypath: file path and name
	#  defaultdir: default directory of the file. if empty, self.defaultdir will be used
	def _clean_path(self, mypath, defaultdir=None):
		#file1_name
		if defaultdir == None: 
			defaultdir = self.defaultdir
		mypath = os.path.expandvars(mypath)
		if mypath.count(OS_PATHSEPARATOR) == 0:
			mypath = os.path.abspath( defaultdir +OS_PATHSEPARATOR + mypath )
		else:
			mypath = os.path.abspath(mypath)

		return mypath

	#Retrieve the key for a single input csv record
	def _get_key(self, record, prettyPrint=False):

		if not prettyPrint:
			out=[]
			for name in self.compare_key:
				out.append(record[self.compare_dict[name]])
			return tuple(out)
		else:
			out={}
			for name in self.compare_key:
				out[name]=record[self.compare_dict[name]]
			return str(out)

	def _get_key2(self, record, prettyPrint=False):
		if not prettyPrint:
			out=[]
			for name in self.compare_key:
				out.append(record[self.compare_dict2[name]])
			return tuple(out)
		else:
			out={}
			for name in self.compare_key:
				out[name]=record[self.compare_dict2[name]]
			return str(out)


if __name__ == '__main__':

	res=Log()

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
	res.sniff_dialect1()
	res.sniff_dialect2()
	res.compare_csv()


	#print( res.dump(format='OBJECT') )
	print (res )
