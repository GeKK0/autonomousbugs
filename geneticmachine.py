
import neurons
import random

# global to allow experiments to be repeatable
rand=random.Random()
rand.seed(12345)


class GeneticMachine:
    def __init__(self,ninput,noutput,layersize=None,gene=None,nstate=3):
        self.ninput=ninput
        self.noutput=noutput
        if layersize==None:
            layersize=GeneticMachine.defaultLayersize(ninput,noutput)
        self.layersize=layersize
        self.nstate=nstate
        self.currentstate=0

        n=neurons.NeuralNetwork.genesize(layersize)
        if gene and len(gene)!=n*nstate:
            raise Exception("gene wrong size")
        pos=0
        self.net=[]
        for i in xrange(nstate):
            if gene:
                weights=gene[pos:pos+n]
                pos+=n
            else:
                weights=None
            self.net.append(neurons.NeuralNetwork(layersize,gene=weights))

    def IncrementState(self,n):
        self.currentstate = (self.currentstate+n)%self.nstate

    def calc(self,data):
        if len(data)!=self.ninput:
            raise Exception("input wrong length")
        return self.net[self.currentstate].calc(data)

    def gene(self):
        g=[]
        for i in xrange(self.nstate):
            g.extend(self.net[i].gene())
        return g

    def settings(self):
        return (self.ninput,self.noutput,self.layersize,self.nstate)

    # below is stuff that can probably be tweeked

    @staticmethod
    def defaultLayersize(ninput,noutput):
        #default to a single hidden layer, of twice size
        return [ninput,2*max(ninput,noutput),noutput]        

    def breed(self,other):
        probCrossover=0.05
        probCopyErr=0.001
        errSize=0.2
        
        if self.settings()!=other.settings():
            raise Exception("can't breed machines with differing construction")
        newgene=[]
        # randomly select each state "chromosome", allowing crossover mutation
        for i in xrange(self.nstate):
            if rand.uniform(0,1)<probCrossover:
                a=self.net[i].gene()
                b=self.net[i].gene()
                r=rand.randrange(len(a))
                newgene.extend(a[:r]+b[r:])
            elif rand.choice([0,1])==0:
                newgene.extend(self.net[i].gene())
            else:
                newgene.extend(other.net[i].gene())

        # now apply additional random copy mutation                
        for i in xrange(len(newgene)):
            if rand.uniform(0,1)<probCopyErr:
                newgene[i] += rand.uniform(-errSize,errSize)

        return GeneticMachine(self.ninput,self.noutput,
            layersize=self.layersize,
            gene=newgene,
            nstate=self.nstate)            


'''
a=GeneticMachine(3,3)
b=GeneticMachine(3,3)
print a.gene()
print b.gene()
c=a.breed(b)
print c.gene()
'''

