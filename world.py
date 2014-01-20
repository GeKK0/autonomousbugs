# This has all the objects for our world simulation

import geneticmachine
import random

rand=random.Random()
rand.seed(12345)

# Some settings for the ants    
ENERGY_MAX = 1.0
ENERGY_MIN = 0.0
ENERGY_START = 0.5  #energy a new ant is born with
ENERGY_BREED = 0.5  #energy cost to lay or fertilize egg
ENERGY_LIVE = 0.001 #energy cost each step for living
ENERGY_FOOD = 0.1   #energy per turn that can be eaten from food
ENERGY_MOVE = 0.001 #energy to go forward
ENERGY_TURN = 0.001 #energy to turn

# enumerate some direction, positive turn=counter-clockwise
EAST=0
NORTH=1
WEST=2
SOUTH=3

# enumerate some objects
EMPTY=0
ROCK=1
ANT=2
EGG=3
FOOD=4

# Useful for converting type to neural input list
_TypeLookup = {
    EMPTY:(-1,-1,-1,-1),
    ROCK:(1,-1,-1,-1),
    ANT:(-1,1,-1,-1),
    EGG:(-1,-1,1,-1),
    FOOD:(-1,-1,-1,1)}

# useful for scaling values for neural net to [-1,1] range
def nscale(val,vmin,vmax):
    return (val-vmin)*2.0/(vmax-vmin) - 1.0


#############################################################################
      
class World:
    # for the moment, each grid has:
    #   grid[y][x] = type
    #   obj[y][x] = info for object if necessary 
    #     ant -> ref, egg -> ant.gm, food -> energy left, other -> None
    #  eventually, add scents? for communication?

    def __init__(self,xmax,ymax):
        self.xmax=xmax
        self.ymax=ymax
        self.grid=[[EMPTY for x in xrange(xmax)] for y in xrange(ymax)]
        self.obj=[[None for x in xrange(xmax)] for y in xrange(ymax)]
        self.time=0

    def GetGridInfo(self,x,y):
        return _TypeLookup[self.grid[y][x]]
        
    def SetPos(self,x,y,thing,info):
        self.grid[y][x]=thing
        self.obj[y][x]=info

    def RandAddObj(self,thing,info):
        while 1:
            x=rand.randrange(self.xmax)
            y=rand.randrange(self.ymax)
            if self.grid[y][x]==EMPTY:
                break
        self.SetPos(x,y,thing,info)

    def Update(self):
        self.time += 1
        for y in xrange(self.ymax):
            for x in xrange(self.xmax):
                if self.grid[y][x]==ANT:
                    self.obj[y][x].update(x,y)

class Ant:
    '''
     input:
      energy, (rock, ant, egg, food) * 5
      where 'F' is front, 'FL' is fron-left, etc. the world around 
      the ant looks like
           FL  F  FR 
           L  ant  R
           .   .   .
  
     output:
      turn right, turn left, move forward,
      breed, eat, 
      state_change1, state_change2, state_change3

      allow 4 states
      state_change is relative, newstate=(current+change)%numstate
    '''
    
    def __init__(self,world,gene=None):
        self.world=world
        self.gm=geneticmachine.GeneticMachine(21,8,nstate=4,gene=gene)
        self.dir=NORTH
        self.energy=ENERGY_START
        self.time=world.time

    def update(self,x,y):
        w=self.world
        #make sure we're not updating twice (due to moving)
        if self.time==w.time:
            return
        self.time=w.time

        #build up inputs to genetic machine,
        #when possible, scale to [-1,1]
        data=[nscale(self.energy,ENERGY_MIN,ENERGY_MAX)]
        if self.dir==EAST:
            fx,fy = (x+1,y)
            data.extend(w.GetGridInfo(x+0,y+1)) # R
            data.extend(w.GetGridInfo(x+1,y+1)) # FR
            data.extend(w.GetGridInfo(x+1,y+0)) # F
            data.extend(w.GetGridInfo(x+1,y-1)) # FL
            data.extend(w.GetGridInfo(x+0,y-1)) # L
        elif self.dir==NORTH:
            fx,fy = (x,y-1)
            data.extend(w.GetGridInfo(x+1,y+0)) # R
            data.extend(w.GetGridInfo(x+1,y-1)) # FR
            data.extend(w.GetGridInfo(x+0,y-1)) # F
            data.extend(w.GetGridInfo(x-1,y-1)) # FL
            data.extend(w.GetGridInfo(x-1,y+0)) # L
        elif self.dir==WEST:
            fx,fy = (x-1,y)
            data.extend(w.GetGridInfo(x+0,y-1)) # R
            data.extend(w.GetGridInfo(x-1,y-1)) # FR
            data.extend(w.GetGridInfo(x-1,y+0)) # F
            data.extend(w.GetGridInfo(x-1,y+1)) # FL
            data.extend(w.GetGridInfo(x+0,y+1)) # L
        elif self.dir==SOUTH:
            fx,fy = (x,y+1)
            data.extend(w.GetGridInfo(x-1,y+0)) # R
            data.extend(w.GetGridInfo(x-1,y+1)) # FR
            data.extend(w.GetGridInfo(x+0,y+1)) # F
            data.extend(w.GetGridInfo(x+1,y+1)) # FL
            data.extend(w.GetGridInfo(x+1,y+0)) # L

        (turnR,turnL,move,breed,eat,s1,s2,s3) = self.gm.calc(data)

        self.energy -= ENERGY_LIVE
            
        # do the genetic machine's bidding
        if eat > 0.0 and w.grid[fy][fx]==FOOD:
            if w.obj[fy][fx] > ENERGY_FOOD:
                self.energy += ENERGY_FOOD
                w.obj[fy][fx] -= ENERGY_FOOD
            else:
                self.energy += w.obj[fy][fx]
                w.SetPos(fx,fy,EMPTY,None)

        if breed > 0.0:
            self.energy -= ENERGY_BREED
            if w.grid[fy][fx]==EGG and self.energy>ENERGY_MIN:
                #fertilize egg, making a new ant
                c=Ant(w)
                if w.obj[fy][fx]==self.gm:
                    #our own egg, pretend fertilize with random
                    c.gm=c.gm.breed(self.gm)
                else:
                    #not our egg, fertilize normally
                    c.gm=w.obj[fy][fx].breed(self.gm)
                w.SetPos(fx,fy,ANT,c)
            elif w.grid[fy][fx]==EMPTY and self.energy>ENERGY_MIN:
                #lay egg
                w.SetPos(fx,fy,EGG,self.gm)

        if move > 0.0:
            self.energy -= ENERGY_MOVE
            if w.grid[fy][fx]==EMPTY and self.energy>ENERGY_MIN:
                w.SetPos(x,y,EMPTY,None)
                w.SetPos(fx,fy,ANT,self)
        if turnR > 0.0:
            self.dir = (self.dir-1)%4
            self.energy -= ENERGY_TURN
        if turnL > 0.0:
            self.dir = (self.dir+1)%4
            self.energy -= ENERGY_TURN

        # State changes will be prioritized, by first selected
        if s1>0.0:
            self.gm.IncrementState(1)
        elif s2>0.0:
            self.gm.IncrementState(2)
        elif s3>0.0:
            self.gm.IncrementState(3)

        # check for death
        if self.energy < ENERGY_MIN:
            w.SetPos(x,y,EMPTY,None)
        # enforce energy limit as well
        if self.energy > ENERGY_MAX:
            self.energy = ENERGY_MAX


 
