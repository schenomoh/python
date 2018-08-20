#!/usr/bin/python3.4
#Convert a csv to a json file
#
# Use yield/generator to (hopefully) handle big files
# 
# Does not handle sting encoding properly (accents & all)
#
# Test command
# ./csv2json.py ../training/res/media_library.csv
#

import json, csv, sys

def csv2json(filepath):
	result={'header':None, 'content':[]}
	try:
		#open file pointer
		f=open(filepath, 'r')

		#auto detect file format
		dialect = csv.Sniffer().sniff(f.read(10000))
		f.seek(0)
		has_header=csv.Sniffer().has_header(f.read(10000))
		f.seek(0)

		#Create csv reader
		csvreader=csv.reader(f, dialect)

	except Exception as e:
		raise BaseException("Unable to open the csv files "+ str(e) )
	else:
		#manage header
		if has_header:
			#result["header"]=csvreader.__next__()
			yield '{"header":' + json.dumps(csvreader.__next__() ) 

		#Read first line
		yield ',"content":[\n ' + json.dumps(  csvreader.__next__()  )

		#read file
		for line in csvreader:
			#result["content"].append(line)
			yield ',' + json.dumps(line)
	finally:
		f.close()
		#write last line
		yield ']}'
		#return json.dumps(result)

# Main function for script mode
if __name__ == '__main__':
	if len(sys.argv) == 1:
		print ('Please provide csv file name as first argument')
		sys.exit(1)

	for line in csv2json(sys.argv[1]):
		print (line)



