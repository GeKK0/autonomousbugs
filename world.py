# This has all the objects for our world simulation

import geneticmachine
import time
import random

rand=random.Random()
rand.seed(12345)

# Some settings for the world
MAX_FITLIST_LEN=10  #'breeding pool' for random ants
ENERGY_FOOD = 4.0   #energy in a new food pellet

# Some settings for the ants    
ENERGY_MAX = 1.0
ENERGY_MIN = 0.0
ENERGY_START = 0.5      #energy a new ant is born with
ENERGY_LAYEGG = 0.6     #energy cost to lay egg
ENERGY_FERTILIZE = 0.1  #energy cost to fertilize egg
ENERGY_LIVE = 0.001     #energy cost each step for living
ENERGY_EATFOOD = 0.1    #energy per turn that can be eaten from food
ENERGY_EATANT = 0.1     #energy per turn that can be eaten from ant
ENERGY_MOVE = 0.001     #energy to go forward
ENERGY_TURN = 0.001     #energy to turn

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
        # holds (fitness,gm) pairs, sorted by fitness
        self.fitlistNorm=[]   # for generation 0 ants
        self.fitlistChild=[]  # for children ants
        # final list of gm taken from fitlist
        self.breedingpool=[]

    def GetGridInfo(self,x,y):
        return _TypeLookup[self.grid[y][x]]
        
    def SetPos(self,x,y,thing,info):
        self.grid[y][x]=thing
        self.obj[y][x]=info

    def ClearFitlists(self):
        self.fitlistNorm=[]
        self.fitlistChild=[]

    def BuildBreedingPool(self):
        self.breedingpool=[]
        for f in self.fitlistNorm:
            self.breedingpool.append(f[1])
        for f in self.fitlistChild:
            self.breedingpool.append(f[1])

    def Fitness(self,a):
        # lots of tweeking can be done here
        f  = 1000000.0*a.generation
        f += 10000.0*(a.layegg+a.fertilize)
        f += 100.0*(a.eatfood+a.eatant)
        f += a.tick
        f += a.move
        return f

    def AddFitnessList(self,a):
        '''add ant to fitness list if it is "worthy" '''
        f=self.Fitness(a)
        if a.generation>0:
            fitlist=self.fitlistChild
        else:
            fitlist=self.fitlistNorm

        if len(fitlist)>=MAX_FITLIST_LEN and f<fitlist[0][0]:
            return
        #print "added genes from ant, gen:",a.generation," fitness:",f
        fitlist.append((f,a.gm))
        fitlist.sort(key=lambda x: x[0])
        if len(fitlist)>MAX_FITLIST_LEN:
            del fitlist[0]

    def RandAddObj(self,thing,info=None):
        if info==None:
            if thing==ANT:
                info=Ant(self)
                n=len(self.breedingpool)
                if n>=2:
                    i=rand.randrange(n)
                    j=rand.randrange(n)
                    a=self.breedingpool[i]
                    if i!=j:
                        b=self.breedingpool[j]
                    else:
                        # when i==j, breed with a random
                        b=Ant(self).gm
                    info.gm=a.breed(b)
            elif thing==FOOD:
                info=ENERGY_FOOD

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
                    a=self.obj[y][x]
                    if a.energy < ENERGY_MIN:
                        self.AddFitnessList(a)
                        self.SetPos(x,y,EMPTY,None)
                    else:
                        a.update(x,y)
    
    def DumpAntFile(self,filename):
        '''dump all ant genes to a file'''
        f=open(filename,"a")
        f.write("# Ant dump - " + time.ctime() + "\n")
        f.write("ants=[]\n")
        for y in xrange(self.ymax):
            for x in xrange(self.xmax):
                if self.grid[y][x]==ANT:
                    g=self.obj[y][x].gm.gene()
                    f.write("ants.append("+repr(g)+")\n")
        f.close()



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
        #some statistics
        self.tick=0
        self.move=0
        self.layegg=0
        self.fertilize=0
        self.eatfood=0
        self.eatant=0
        self.generation=0

    def update(self,x,y):
        '''use genetic machine to determine a move, then perform it.
           NOTE: death is not handled by this routine. This is done
           to easily allow fitness breeding to be added'''

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
        self.tick += 1
            
        # do the genetic machine's bidding
        if eat > 0.0:
            if w.grid[fy][fx]==FOOD:
                self.eatfood += 1
                if w.obj[fy][fx] > ENERGY_EATFOOD:
                    self.energy += ENERGY_EATFOOD
                    w.obj[fy][fx] -= ENERGY_EATFOOD
                else:
                    self.energy += w.obj[fy][fx]
                    w.SetPos(fx,fy,EMPTY,None)
            elif w.grid[fy][fx]==ANT:
                self.eatant += 1
                self.energy += ENERGY_EATANT
                w.obj[fy][fx].energy -= ENERGY_EATANT
            else:
                #penalty for trying to eat nothing
                self.energy -= ENERGY_EATFOOD

        if breed > 0.0:
            if w.grid[fy][fx]==EGG:
                self.energy -= ENERGY_FERTILIZE
                if self.energy>0:
                    #fertilize egg, making a new ant
                    self.fertilize += 1
                    c=Ant(w)
                    egg=w.obj[fy][fx]
                    if egg==self:
                        #our own egg, pretend fertilize with random
                        c.gm=c.gm.breed(self.gm)
                    else:
                        #not our egg, fertilize normally
                        c.gm=egg.gm.breed(self.gm)
                    c.generation=max(self.generation,egg.generation)+1
                    w.SetPos(fx,fy,ANT,c)
            elif w.grid[fy][fx]==EMPTY:
                self.energy -= ENERGY_LAYEGG
                if self.energy>0:
                    #lay egg
                    self.layegg += 1
                    w.SetPos(fx,fy,EGG,self)
            else:
                #penalty for trying to fertilize something other than egg
                self.energy -= ENERGY_FERTILIZE

        if move > 0.0:
            self.energy -= ENERGY_MOVE
            if w.grid[fy][fx]==EMPTY and self.energy>ENERGY_MIN:
                self.move += 1
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

        # enforce energy limit as well
        if self.energy > ENERGY_MAX:
            self.energy = ENERGY_MAX


 
