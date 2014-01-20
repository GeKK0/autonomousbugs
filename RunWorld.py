#!/usr/bin/env python

MIN_ANTS=100
MIN_FOOD=20


LOCALDISPLAY = True # display using pygame
TIMEPRINT = False

if 0: #large space
    # size of grid 'squares'
    RECT_SIZE_X = 2
    RECT_SIZE_Y = 2
    # number of grid squares
    XMAX = 320
    YMAX = 240
else: #small space
    # size of grid 'squares'
    RECT_SIZE_X = 8
    RECT_SIZE_Y = 8
    # number of grid squares
    XMAX = 64
    YMAX = 48

# Border / obstacle color
ROCK_COLOR = (0x55,0x55,0x55)  
BACK_COLOR = (0,0,0)
EGG_COLOR = (0xff,0xff,0xff)
ANT_COLOR = (0xff,0,0)
FOOD_COLOR = (0,0xff,0)

###########################################################################

import time
import random
rand=random.Random()
rand.seed(1234)

import world

# global world object
w = world.World(XMAX,YMAX)

# global drawing surface
if LOCALDISPLAY:
    import pygame
    screen = pygame.display.set_mode((XMAX*RECT_SIZE_X,YMAX*RECT_SIZE_Y))



###########################################################################

def drawbox(x,y,color):
    screen.fill(color,(x*RECT_SIZE_X,y*RECT_SIZE_Y,RECT_SIZE_X,RECT_SIZE_Y))

def drawcell(x,y):
    val=w.grid[y][x]
    if val==world.EMPTY:
        drawbox(x,y,BACK_COLOR)
    elif val==world.ROCK:
        drawbox(x,y,ROCK_COLOR)
    elif val==world.FOOD:
        drawbox(x,y,FOOD_COLOR)
    elif val==world.ANT:
        #scale color to show health
        scale  = (w.obj[y][x].energy-world.ENERGY_MIN)
        scale /= (world.ENERGY_MAX-world.ENERGY_MIN)
        scale  = 0.3+max(0.0,0.7*min(1.0,scale))
        clr=tuple(int(scale*c) for c in ANT_COLOR)
        drawbox(x,y,clr)
    elif val==world.EGG:
        drawbox(x,y,EGG_COLOR)
    else:
        print "(%d,%d) unknown type %d"%(x,y,val)
    
def refreshscreen():
    for y in xrange(YMAX):
        for x in xrange(XMAX):
            drawcell(x,y)

###########################################################################

# Initially add:
#   1 block rock border
#   random blocks
for y in xrange(YMAX):
    for x in xrange(XMAX):
        if (x<1 or x>=XMAX-1):
            w.SetPos(x,y,world.ROCK,None)
        elif (y<1 or y>=YMAX-1):
            w.SetPos(x,y,world.ROCK,None)
        elif rand.uniform(0.0,1.0)<0.05:
            w.SetPos(x,y,world.ROCK,None)
        else:
            w.SetPos(x,y,world.EMPTY,None)

#w.SetPos(XMAX/2,YMAX/2,world.ANT,world.Ant(w))

# try to include any saved ants
try:
    import antdump
    print "Loaded saved ants from antdump.py"
    for g in antdump.ants:
        w.RandAddObj(world.ANT,world.Ant(w,gene=g))
except:
    print "There were no saved ants, starting fresh."


running = True
while running:
    if TIMEPRINT:
        print "loop %d :"%w.time, time.time()

    # if we need more ants, add them
    n = sum(sum(1 for i in row if i==world.ANT) for row in w.grid)
    if n < MIN_ANTS:
        for i in xrange(MIN_ANTS-n):
            w.RandAddObj(world.ANT)

    # if we need more food, add it
    n = sum(sum(1 for i in row if i==world.FOOD) for row in w.grid)
    if n < MIN_FOOD:
        for i in xrange(MIN_FOOD-n):
            w.RandAddObj(world.FOOD)

    w.Update()

    if LOCALDISPLAY:
        if TIMEPRINT:
            print "refresh gui", time.time()

        # handle gui
        refreshscreen()
        #pygame.event.pump()
        while 1:
            event = pygame.event.poll()
            #print repr(event)
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.NOEVENT:
                break
        pygame.display.flip()

w.DumpAntFile("antdump.py")

