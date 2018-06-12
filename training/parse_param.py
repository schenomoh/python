#!/usr/bin/python
# --------------------------------------------------------
# 2018-06-12 / https://github.com/schenomoh/lib
#
# Training script to read a sample param file from Informatica PowerCenter
#
# --------------------------------------------------------

################################
# Import required libraries
import ConfigParser

################################
#Initialize variables
filePathName="res/informatica.param"

#Create the file object as a config parser (param file reader)
fileObject = ConfigParser.ConfigParser()
#Read the param file, and load its content in fileObject
fileObject.read(filePathName)


################################

#Note how we can use double quote instead of single quote. 
#This allow us to print easily single quote or double quote

print ''
print 'What is the value of "$pmcachedir" from [GLOBAL] section?' 
print '> ' + fileObject.get('GLOBAL', '$pmcachedir')

print ""
print "Has '" + filePathName +"' a [GLOBAL] section? "
print ">",
#If "[GLOBAL]" is found in the section list of fileObject, then print "True". Else, print "False"
#Due to operator and function priority, this must be read as:
# print ( if("GLOBAL" in fileObject.sections()), True, False) )
#Please note how we get rid of useless parenthesis and redundant boolean logic. As "GLOBAL" is a section of fileObject, the test is true and pytton simply write.. well.. "True"
print "GLOBAL" in fileObject.sections()

# Here we could use a quit() statement to exit the script 
# Very usefull for debugging purpose
# quit()

################################
#Loop on the sections of the param files [GLOBAL], [TRAINING.WF:WF_main_flow], [TRAINING.WF:WF_main_flow.ST:S_M_staging], ..
print ""
for section in fileObject.sections():

	#Skip the special section [GLOBAL]
	if section == "GLOBAL":
		continue
	
	#Split the session name on char "." to retrieve the names of each item in task_location. Structure of session name is: [FOLDER.WORKFLOW.SESSIONTASK].
	# Example: [TRAINING.WF:WF_main_flow.ST:S_M_datamart]
	#  FOLDER=TRAINING
	#  WORKFLOW=WF:WF_main_flow
	#  SESSIONTASK=ST:S_M_datamart
	task_location=(section).split(".")

	# ------------------------
	#Sub loop 1 on each task_location item: FOLDER, WORKFLOW, SESSIONTASK
	for name in task_location:
		#Take the last element from each item when splitting them by ":" separator
		# Example: "WF:WF_main_flow" has "WF" for first element and "WF_main_flow" for last one
		# Please note the -1 index. This means the first element when counting from the end
		print "/ " + name.split(':')[-1], 

	# ------------------------

	#Final carriage return when the task_location is fully written
	print ""
	
	# ------------------------

	#Sub loop 2 to display the key / pair values (options) of each section
	for key in fileObject.options(section):
		print "... " + key + " = " + fileObject.get(section, key)

