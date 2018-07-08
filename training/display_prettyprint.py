#!/usr/bin/python
# --------------------------------------------------------
# 2018-06-12 / https://github.com/schenomoh/lib
#
# Training script to pretty print results
#
# --------------------------------------------------------

import time
import curses

def pbar(window):
    height, width = window.getmaxyx()
    for i in range(10):
        window.addstr(height -1, 0, "[" + ("=" * i) + ">" + (" " * (10 - i )) + "]")
        window.refresh()
        time.sleep(0.5)

curses.wrapper(pbar)