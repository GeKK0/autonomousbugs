'''
Neural network preconditioning
http://www.willamette.edu/~gorr/classes/cs449/precond.html
 - use tanh activation function
 - try to bias and scale inputs so they are [-1,1]
 - random weights chosen from [-r,r] with r=1/sqrt(ninputs+1)
'''

import random
import operator
from math import sqrt, tanh

#global random, to ensure it is repeatable for tests
rand=random.Random()
rand.seed(12345)


def RandWeights(size):
    r=1/sqrt(size)
    return [rand.uniform(-r,r) for x in xrange(size)]



'''
Neuron class
    weight = list of ninput floats for inputs, +1 for bias
    in = bias + sum weight_i * input_i
    out = tanh(in)
'''
class Neuron:
    def __init__(self,ninput,gene=None):
        self.ninput=ninput
        if gene:
            if len(gene)!=Neuron.genesize(ninput):
                raise Exception("gene wrong length")
            weights=gene
        else:
            weights=RandWeights(ninput+1)
        self.w=weights[:ninput]
        self.bias=weights[ninput]
        
    def calc(self,data):
        if len(data)!=self.ninput:
            raise Exception("input wrong length")
        activation  = self.bias + sum(map(operator.mul,self.w,data))
        return tanh(activation)

    def gene(self):
        g=list(self.w)
        g.append(self.bias)
        return g

    @staticmethod
    def genesize(ninput):
        return ninput+1


class NeuronLayer:
    def __init__(self,ninput,noutput,gene=None):
        if gene and len(gene)!=NeuronLayer.genesize(ninput,noutput):
            raise Exception("gene wrong size")
        self.ninput = ninput
        self.noutput= noutput
        self.neuron = []
        pos=0
        n=Neuron.genesize(ninput)
        for i in xrange(noutput):
            if gene:
                weights=gene[pos:pos+n]
                pos+=n
            else:
                weights=None
            self.neuron.append(Neuron(ninput,gene=weights))

    def calc(self,data):
        if len(data)!=self.ninput:
            raise Exception("input wrong length")
        return [self.neuron[i].calc(data) for i in xrange(self.noutput)]

    def gene(self):
        g=[]
        for N in self.neuron:
            g.extend(N.gene())
        return g

    @staticmethod
    def genesize(ninput,noutput):
        return noutput*Neuron.genesize(ninput)

# layersize is a list: input, first layer of neurons, second ..., output
class NeuralNetwork:
    def __init__(self,layersize,gene=None):
        if gene and len(gene)!=NeuralNetwork.genesize(layersize):
            raise Exception("gene wrong size")
        self.layersize = layersize
        self.layer = []
        pos=0
        for i in xrange(len(layersize)-1):
            ninput=layersize[i]
            noutput=layersize[i+1]
            if gene:
                n=NeuronLayer.genesize(ninput,noutput)
                weights=gene[pos:pos+n]
                pos+=n
            else:
                weights=None
            self.layer.append(NeuronLayer(ninput,noutput,gene=weights))
    
    def calc(self,data):        
        if len(data)!=self.layersize[0]:
            raise Exception("input wrong length")
        for i in xrange(len(self.layersize)-1):
            data=self.layer[i].calc(data)
        return data

    def gene(self):
        g=[]
        for L in self.layer:
            g.extend(L.gene())
        return g

    @staticmethod
    def genesize(layersize):
        n=0
        for i in xrange(len(layersize)-1):
            n+=NeuronLayer.genesize(layersize[i],layersize[i+1])
        return n



