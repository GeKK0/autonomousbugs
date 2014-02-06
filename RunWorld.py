#!/usr/bin/env python

START_ANTS=1000
MIN_FOOD=1000


LOCALDISPLAY = True # display using pygame
TIMEPRINT = False

if 1: #large space
    # size of grid 'squares'
    RECT_SIZE_X = 4
    RECT_SIZE_Y = 4
    # number of grid squares
    XMAX = 236
    YMAX = 170
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
STATE_COLOR =[(0xff,0,0),(0xff,0xff,0),(0,0xff,0xff),(0,0,0xff)]

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

def drawant(x,y,a):
    #scale color to show health
    scale  = (a.energy-world.ENERGY_MIN)
    scale /= (world.ENERGY_MAX-world.ENERGY_MIN)
    scale  = 0.3+max(0.0,0.7*min(1.0,scale))
    #clr=tuple(int(scale*c) for c in ANT_COLOR)
    clr=tuple(int(scale*c) for c in STATE_COLOR[a.gm.currentstate])
    drawbox(x,y,clr)
    x *= RECT_SIZE_X
    y *= RECT_SIZE_Y
    clr=(0xff,0xff,0xff)#STATE_COLOR[a.gm.currentstate]    
    if a.dir==world.NORTH:
        screen.fill(clr,(x,y,RECT_SIZE_X,1))
    elif a.dir==world.EAST:
        screen.fill(clr,(x+RECT_SIZE_X-1,y,1,RECT_SIZE_Y))
    elif a.dir==world.SOUTH:
        screen.fill(clr,(x,y+RECT_SIZE_Y-1,RECT_SIZE_X,1))
    elif a.dir==world.WEST:
        screen.fill(clr,(x,y,1,RECT_SIZE_Y))


def drawcell(x,y):
    val=w.grid[y][x]
    if val==world.EMPTY:
        drawbox(x,y,BACK_COLOR)
    elif val==world.ROCK:
        drawbox(x,y,ROCK_COLOR)
    elif val==world.FOOD:
        drawbox(x,y,FOOD_COLOR)
    elif val==world.ANT:
	drawant(x,y,w.obj[y][x])
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

import pickle
roundnum=0

def SetupRound():
    global roundnum

    #print some statistics
    fitN=[f[0] for f in w.fitlistNorm]
    fitC=[f[0] for f in w.fitlistChild]
    if len(fitN)==0:
        fitN=[0.0]
    if len(fitC)==0:
        fitC=[0.0]
    stat  = "round num: %d\n"%roundnum
    stat += "  gen 0 ants, max:%15f avg:%15f\n"%(max(fitN),sum(fitN)/len(fitN))
    stat += "  child ants, max:%15f avg:%15f\n"%(max(fitC),sum(fitC)/len(fitC))
    print stat
    open("save_stats.txt","a").write(stat)

    #save round fitnesses
    pickle.dump( (w.fitlistNorm,w.fitlistChild), open("save_fitlist.bin","wb"))

    #now setup for new round
    w.BuildBreedingPool()
    w.ClearFitlists()
    roundnum+=1

    # clear anything that is not a rock
    for y in xrange(YMAX):
        for x in xrange(XMAX):
            if w.grid[y][x]!=world.ROCK:
                w.SetPos(x,y,world.EMPTY,None)

    # now add starting food
    for i in xrange(MIN_FOOD):
        w.RandAddObj(world.FOOD)

    # now add starting ants
    for i in xrange(START_ANTS):
        w.RandAddObj(world.ANT)




#w.SetPos(XMAX/2,YMAX/2,world.ANT,world.Ant(w))

# try to continue last run
try:
    f=open("save_fitlist.bin","rb")
    print "Loading saved fitness lists from previous run"
    w.fitlistNorm,w.fitlistChild = pickle.load(f)
    f.close()
except:
    print "No saved data, starting fresh."    


running = True
while running:
    if TIMEPRINT:
        print "loop %d :"%w.time, time.time()

    # if ants all dead, start new round
    n = sum(sum(1 for i in row if i==world.ANT) for row in w.grid)
    if n == 0:
        SetupRound()

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

