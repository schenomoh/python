#!/usr/bin/python
# --------------------------------------------------------
# 2018-06-12 / https://github.com/schenomoh/lib
#
# Training script to read a sample param file from Informatica PowerCenter
#
# --------------------------------------------------------

################################
# Import required libraries
import time, sys

################################
#Initialize variables

#Store the message in a variable
#Python is a ducked-typed langage: if it looks like a duck, then it is a duck
# => If it looks like a string, then it is a string
message='-- Hello world ! '
lng=len(message)

################################
# Part I, loop for the static message

#Loop on the first characters of our string
#Do not forget the trailing ":" on the for statement
#This means some indentation is required
for i in range(0, 6):
  #Here we cast the interger variable i into string
  #And we concatenate it with the + operator
  #At the end of line, the comma separator prevent the print function to append a line break
  print str(i) + "  | ",
  # The [i:] syntax select all charaters starting from position i and up to the end of the string
  # The [0:i] syntax select all characters between position 0 and position i
  print message[i:] + message[0:i]


################################
# Part II, loop for the sliding message

print ""

#Slide for 50 caracters max
for i in range(0, 50):
	#Same logic as previously, but with a modulo (% operator)
	print message[i%lng:] + message[0:i%lng],
	
	#Force unix to diplay the line, even if there is no carriage return
	sys.stdout.flush()

	#Wait for a few milliseconds
	time.sleep(0.3)

	#The \b stands for backspace but we should better call him "left arrow". Indeed, it moves the cursor one char to the left, but char deletion is optional. 
	# As the [ print "xxx", ] command add a trailing space after the "xxx" we need to "backspace" two additional chars, one for the initial print, and another one for the deletion print
	# To print 20 time "\b", we can simply write [ print 20 * "\b" ]
	print (lng+2) * "\b",

