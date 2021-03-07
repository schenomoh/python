#!/usr/bin/env python3

import time, datetime, sys, os, subprocess
import curses, queue, threading

#Config management
import yaml_reader as yaml
param = yaml.load('alita_ui.yaml')

MENU_PAD = [ i for i in param if 'MENU_PAD' in i]
BANNER = [ i for i in param if 'BANNER' in i][0]['BANNER']
BIND_KEY = [ i['BIND_KEY'] for i in param if tuple(i)[0] == 'BIND_KEY' ][0]

PARAM = {'SLEEP_DURATION':2}

with open(r"unicorn.txt", "r+") as f:
	unicorn =f.read()





question = queue.Queue()
workq = queue.Queue()
display = queue.Queue()

def dummy():
	time.sleep(10)
	return "done"

#Echo back question to the screen
def question_logger():
	while True:
		command = question.get()
		workq.put(command)
		display.put(str(datetime.datetime.now())[:19]+' - SENT	- '+command+'\n')
		question.task_done()

def worker(worker_id, repeat=False,sleep_duration=PARAM['SLEEP_DURATION']):
	while True:
		command = workq.get()
		#os.system(command)
		display.put(str(datetime.datetime.now())[:19]+' - START - '+command+'\n')
		subprocess.call(command, stdout=subprocess.PIPE, shell=True)
		display.put(str(datetime.datetime.now())[:19]+' - DONE	- '+command+'\n')
		workq.task_done()
	
	#Loop
		if repeat:
			time.sleep(sleep_duration)
			workq.put(command)

# turn-on the worker thread
threading.Thread(target=worker, args=[1,True, PARAM['SLEEP_DURATION'] ], daemon=True).start()
threading.Thread(target=question_logger, daemon=True).start()



class MyPad():
	def __init__(self, PAD_ITEMS, TOP_MARGIN=0, RIGHT_MARGIN=20, LEFT_MARGIN=8, VISIBLE_HEIGHT=1, OBJECT_ID=1, BACKGROUND_NORMAL=189, TEXT_NORMAL=231, TEXT_SELECTED=237,BACKGROUND_SELECTED=189, *args, **kwargs):
		self.pad_items = [ tuple(i)[0] for i in PAD_ITEMS ]
		#Define colors
		self.OBJECT_ID=OBJECT_ID
		curses.init_pair(OBJECT_ID*8+10, TEXT_SELECTED, BACKGROUND_SELECTED)
		curses.init_pair(OBJECT_ID*8+11, TEXT_NORMAL, BACKGROUND_NORMAL)
		self.COLORPAIR_SELECTED=curses.color_pair(OBJECT_ID*8+10)
		self.COLORPAIR_NORMAL=curses.color_pair(OBJECT_ID*8+11)
		#Calculate size
		self.START_COLUMN=LEFT_MARGIN
		self.END_COLUMN=curses.COLS-RIGHT_MARGIN
		self.START_LINE=TOP_MARGIN
		self.END_LINE=self.START_LINE + VISIBLE_HEIGHT
		#Create pad
		self.pad = curses.newpad(VISIBLE_HEIGHT, curses.COLS)
		self.pad.bkgd(self.COLORPAIR_NORMAL)

	def addstr(self, *args, **kwargs):
		return self.pad.addstr(*args, **kwargs)
	
	def refresh(self, highlight_column=None, *args, **kwargs):
		for i, label in enumerate(self.pad_items):
			if i == highlight_column: c=self.COLORPAIR_NORMAL
			else: c=self.COLORPAIR_SELECTED
			self.pad.addstr(0,2+10*i,label,c)

		self.pad.refresh(0,0,self.START_LINE,self.START_COLUMN,self.END_LINE,self.END_COLUMN)
		return

		
		
#########################################################################
class MyMenu():
	def __init__(self, mypad_list):
		self.menu_items=[]
		for i  in mypad_list:
			self.menu_items.append(  MyPad(**i['MENU_PAD'])  )
		self.column, self.line = (0, 0)

	def refresh(self):
		for line, pad in enumerate(self.menu_items):
			if line == self.line: pad.refresh(highlight_column=self.column)
			else: pad.refresh()
	def next_line(self): 
		self.line = (self.line +1) % len(self.menu_items)
		self.refresh()
	def previous_line(self): 
		self.line = (self.line -1) % len(self.menu_items)
		self.refresh()
	def previous_column(self): 
		self.column = (self.column -1 ) % len(self.menu_items[self.line].pad_items)
		self.refresh()
	def next_column(self): 
		self.column = (self.column +1 ) % len(self.menu_items[self.line].pad_items)
		self.refresh()
		
		
def pbar(window):
	height, width = window.getmaxyx()
	if height < 10 or width < 40: raise BaseException('Terminal size must be at least 10 lines and 40 columns wide')
	top_margin=3
	left_margin=5
	bottom_margin=1
	right_margin=1

	curses.curs_set(0)
	#export TERM=xterm-256color
	#curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE )


	curses.init_pair(2, curses.COLOR_WHITE, 234 )
	COLORPAIR_PAD =	curses.color_pair(2)

	#window.border()
	output = curses.newpad(height-3, width-left_margin-right_margin)
	output.bkgd(COLORPAIR_PAD)
	output.addstr(0,0,'this is a test')
	#pad.border()
	output_pos = 0
	#Banner is the keyboard listener
	#keyboard_listener = curses.newpad(len(MENU_PAD), 12)
	#keyboard_listener.bkgd(COLORPAIR_MENU)
	print(BANNER)
	banner = MyPad(**BANNER)
	banner.refresh()
	keyboard_listener = banner.pad
	#keyboard_listener.addstr(0,1,'ALITA')
	#keyboard_listener.refresh(0,0,0,0,3,12)
	keyboard_listener.nodelay(True)
	keyboard_listener.keypad(True)
	
	###############################################

	menu = MyMenu(  MENU_PAD  )
	menu.refresh()
	
	###############################################
	
	output.scrollok(True)
	


	while True:
		output.refresh(output_pos,0, top_margin,left_margin, height-bottom_margin,width-right_margin)

		#################################################
		#Capture key
		try:
			ch = keyboard_listener.getch()
			#key = window.getkey()
		except:
			ch = -1

		#################################################
		# Handle key
		if ch ==BIND_KEY['QUIT']: break
		elif ch == BIND_KEY['UP_ARROW']: 
			menu.previous_line()
		elif ch == BIND_KEY['DOWN_ARROW']: 
			menu.next_line()
		elif ch == BIND_KEY['LEFT_ARROW']:
			menu.previous_column()
		elif ch == BIND_KEY['RIGHT_ARROW']:
			menu.next_column()
		elif ch == BIND_KEY['ENTER']:
			output.clear()
			x= menu_item[menu_line][menu_column]
			if x == '--': display.put(unicorn)
			elif x == 'loop': question.put('echo "Hello world"')
		elif ch != -1: display.put(" key:"+str(ch))
		
		try:
			stdout = display.get(False)
			output.addstr(stdout)
		except:
			pass
		#print(stdout)

curses.wrapper(pbar)


