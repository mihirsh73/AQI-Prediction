pip install padasip

import numpy as np

class Reg_Hoeff_Tree:
    

    def __init__(self,gamma=0.01,n_min = 96,alpha=0.05,thresh=50,learn=0.01):

        self.root = LeafNode(self,n_min=n_min,gamma=gamma,alpha=alpha,thresh=thresh,learn=learn)
        self.gamma = gamma
        self.alpha = alpha
        self.thresh = thresh
        self.n_min = n_min
        self.detect = True
        self.l = learn
        self.c = 0
        pass

    def eval(self,x):
        try:
            k = x[0]
        except:
            x = [x]
        yp = self.root.eval(np.array(x))
        return yp

    def eval_and_learn(self,x,y):
        try:
            k = x[0]
        except:
            x = [x]
        self.c += 1
        self.root.isroot = True
        yp = self.root.eval_and_learn(np.array(x),y)
        global l
        l += 1
        return yp

class Node:

    i_c = 0

    def __init__(self,parent,key=None,key_dim=0,left=None,right=None,alpha=0.005,thresh=50,n_min=100,gamma=0.01,learn=0.1):
       
        self.gamma = gamma
        self.c_x = 0
        self.y = 0.0
        self.y_sq = 0.0
        self.alpha = alpha
        self.n_min = n_min
        self.key = key
        self.key_dim = key_dim
        self.parent = parent
        self.left = left
        self.right = right
        self.isLeaf = False
        Node.i_c += 1
        self.index = Node.i_c 
        self.cumloss = 0.0
        self.minPH = None
        self.PH = 0.0
        self.thresh = thresh
        self.detect = True
        self.alt_tree = None
        self.isAlt = False
        self.sq_loss = 0.0
        self.cum_sq_loss = 0.0
        self.alt_counter = 0
        self.isroot = False
        self.update_root()
        self.l = learn
        self.S_i = 0

    def update_root(self):
        if isinstance(self.parent,Reg_Hoeff_Tree):
            self.isroot = True
        else:
            self.isroot = False

    def update_alt(self,val):
        self.isAlt = val
        if self.left != None:
            self.left.update_alt(val)
        if self.right != None:
            self.right.update_alt(val)

    def eval(self,x):
        
        if x[self.key_dim] <= self.key:
            yp = self.left.eval(x)
        else:
            yp = self.right.eval(x)
        return yp

    def eval_and_learn(self,x,y):
        
        self.c_x += 1
        yp = 0.0
        if x[self.key_dim] <= self.key:
            yp = self.left.eval_and_learn(x,y)
        else:
            yp = self.right.eval_and_learn(x,y)

        if self.alt_tree != None:
            self.alt_counter += 1
            self.alt_tree.eval_and_learn(x,y)
        self.sq_loss = (y - yp)**2
        self.S_i = (self.S_i*0.995) + self.sq_loss
        if self.alt_tree != None and self.alt_counter%self.n_min == 0 and self.alt_counter != 0:
            if self.c_x == 0:
                this_q = 0.0
                alt_q = 1.0
            else:

                this_q = self.S_i
                alt_q = self.alt_tree.S_i
            if alt_q == 0:
                alt_q = 0.00000001
            if not this_q == 0.0 and np.log(this_q/alt_q) > 0:
                global l
                if self.isroot:
                    self.parent.root = self.alt_tree
                elif self.parent.left.index == self.index:
                    self.parent.left = self.alt_tree
                else:
                    self.parent.right = self.alt_tree
                self.alt_tree.parent = self.parent
                self.alt_tree.update_alt(False)
                self.alt_tree.detect = True
            if self.alt_counter >= self.n_min*10:
                #if alternate tree is still not better than the current one, remove it
                self.alt_tree = None
                self.alt_counter = 0
        self.cum_sq_loss += self.sq_loss

        if self.detect_change(y,yp) and self.detect and not self.isAlt and self.alt_tree is None:
            self.parent.detect = False
            self.grow_alt_tree()
        if self.alt_tree != None or (not self.detect and not self.isAlt):
            self.parent.detect = False
            self.detect = False
        else:
            self.detect = True
        return yp


    def grow_alt_tree(self):
        
        global l
        self.alt_tree = LeafNode(self,self.n_min,None,self.gamma,self.alpha,thresh=self.thresh,learn=self.l)
        self.alt_tree.isAlt = True
        return

    def detect_change(self,y,yp):
        
        error = np.fabs(y-yp)
        self.cumloss += error



        self.PH += error - (self.cumloss/self.c_x) - self.alpha

        if  self.minPH is None or self.PH < self.minPH:
            self.minPH = self.PH
        return self.PH - self.minPH > self.thresh

class LeafNode(Node):
    
    def __init__(self,parent,n_min,model=None,gamma=0.01,alpha=0.005,thresh=50,learn=0.1):
        
        Node.__init__(self,parent,None,0,None,None,alpha=alpha,thresh=thresh,n_min=n_min)
        self.isLeaf = True
        self.n_min = n_min
        self.gamma = gamma
        self.alpha = alpha
        self.l = learn
        if model is None:
            self.model = LinearRegressor(self)
        else:
            self.model = model
        self.ebst = None
        self.c = 0
        pass

    def split(self,splits,index):
        
        node = Node(self.parent,n_min=self.n_min,key_dim=index,key=splits['bestsplit'],gamma=self.gamma,learn = self.l,thresh=self.thresh,alpha=self.alpha)
        left = LeafNode(parent=node,n_min=self.n_min,gamma=self.gamma,alpha=self.alpha,learn = self.l,thresh=self.thresh)
        right = LeafNode(parent=node,n_min=self.n_min,gamma=self.gamma,alpha=self.alpha,learn = self.l,thresh=self.thresh)
        l1 = LinearRegressor(left,self.model.w,learn = self.l)
        l2 = LinearRegressor(right,self.model.w,learn = self.l)
        left.model = l1
        right.model = l2
        node.left = left
        node.right = right
        try:
            if self.isroot:
                self.parent.root = node
                node.update_root()
            elif self.parent.left.index == self.index:
                self.parent.left = node
            elif self.parent.right.index == self.index:
                self.parent.right = node
            else:
                self.parent.alt_tree = node
                node.update_alt(True)
        except:
            self.parent.root = node
            node.update_root()

    def eval(self,x):
        
        return self.model.eval(x)

    def eval_and_learn(self,x,y):
        
        self.c += 1
        self.c_x += 1
        self.y += y
        self.y_sq += y**2
        yp = self.model.eval_and_learn(x,y)

        if self.alt_tree != None:
            self.alt_counter += 1
            self.alt_tree.eval_and_learn(x,y)
        self.sq_loss = (y - yp)**2
        self.S_i = (self.S_i*0.995) + self.sq_loss
        if self.alt_tree != None and self.alt_counter%self.n_min == 0 and self.alt_counter != 0:
            if self.alt_tree.c_x == 0:
                this_q = 0.0
                alt_q = 0.0
            else:

                this_q = self.S_i
                alt_q = self.alt_tree.S_i
            if not this_q == 0.0 and np.log(this_q/alt_q) > 0:
                self.update_root()
                if self.isroot:
                    self.parent.root = self.alt_tree
                elif self.parent.left.index == self.index:
                    self.parent.left = self.alt_tree
                else:
                    self.parent.right = self.alt_tree
                self.alt_tree.isAlt = False
                self.alt_tree.detect = True
                self.alt_tree.parent = self.parent
            if self.alt_counter >= self.n_min*10:
                self.alt_tree = None
                self.alt_counter = 0
        self.cum_sq_loss += self.sq_loss

        if self.detect_change(y,yp) and self.detect and not self.isAlt and self.alt_tree is None:
            self.parent.detect = False
            self.grow_alt_tree()
        elif not self.detect and not self.isAlt:
            self.parent.detect = False
            self.detect = True
        if self.alt_tree != None or (not self.detect and not self.isAlt):
            self.parent.detect = False
            self.detect = False
        else:
            self.detect = True
        if self.ebst is None:
            self.ebst = list()
            try:
                for xi in x:
                    tree = E_BST()
                    self.ebst.append(tree)
            except:
                tree = E_BST()
                self.ebst.append(tree)
        for i in range(len(self.ebst)):
            self.ebst[i].add(x[i],y)
        if self.c == self.n_min:
            #try to split
            self.c = 0
            splits = list()
            for tree in self.ebst:
                splits.append(self.findBestSplit(tree))
            bi = int(self.findBest(splits))
            bound = 1-self.hoefding_bound(splits[bi]['n'])
            if splits[bi]['score'] < bound or self.hoefding_bound(splits[bi]['n']) < 0.05 or len(splits) == 1:
                self.split(splits[bi],bi)
        return yp


    def findBest(self,splits):
        
        max_index = None
        second_place = None
        for i in range(len(splits)):
            m = splits[i]['max']
            if max_index is None or m > max_index:
                second_place = max_index
                max_index = i

        if second_place != None:
            splits[max_index]['score'] = splits[second_place]['max']/splits[max_index]['max']
        return max_index


    def findBestSplit(self,tree,sdr = None):
        
        assert(isinstance(tree,E_BST))
        if sdr is None:
            sdr = {}
            sdr['sumtotalLeft'] = 0.0
            sdr['sumtotalRight'] = tree.root.l_y + tree.root.r_y
            sdr['sumsqtotalLeft'] = 0.0
            sdr['sumsqtotalRight'] = tree.root.l_y_sq + tree.root.r_y_sq
            sdr['righttotal'] = tree.root.l_count + tree.root.r_count
            sdr['total'] = sdr['righttotal']
            sdr['n'] = sdr['total']
            sdr['max'] = None

        if tree.root.left != None:
            self.findBestSplit(E_BST(tree.root.left),sdr)
        sdr['sumtotalLeft'] = sdr['sumtotalLeft'] + tree.root.l_y
        sdr['sumtotalRight'] = sdr['sumtotalRight'] - tree.root.l_y
        sdr['sumsqtotalLeft'] = sdr['sumsqtotalLeft'] + tree.root.l_y_sq
        sdr['sumsqtotalRight'] = sdr['sumsqtotalRight'] - tree.root.l_y_sq
        sdr['righttotal'] = sdr['righttotal'] - tree.root.l_count

        new_sdr = self.computeSDR(sdr)
        if(sdr['max'] is None or new_sdr > sdr['max']):
            sdr['2nd'] = sdr['max']
            sdr['max'] = new_sdr
            try:
                if not new_sdr == 0.0:
                    sdr['score'] = new_sdr#sdr['2nd'] / new_sdr
                else:
                    sdr['score'] = 1.0
            except:
                sdr['score'] = 1.0
            sdr['bestsplit'] = tree.root.key

        if tree.root.right != None:
            self.findBestSplit(E_BST(tree.root.right),sdr)
        sdr['sumtotalLeft'] = sdr['sumtotalLeft'] - tree.root.l_y
        sdr['sumtotalRight'] = sdr['sumtotalRight'] + tree.root.l_y
        sdr['sumsqtotalLeft'] = sdr['sumsqtotalLeft'] - tree.root.l_y_sq
        sdr['sumsqtotalRight'] = sdr['sumsqtotalRight'] + tree.root.l_y_sq
        sdr['righttotal'] = sdr['righttotal'] + tree.root.l_count
        return sdr

    def sd(self,n,y_sq_count, y_count):
        if n == 0:
            return 0.0
        n_inv = 1/float(n)
        return np.sqrt(np.fabs(n_inv*(y_sq_count - (n_inv*(y_count**2)))))

    def computeSDR(self,sdr):
        
        n_l = sdr['total']- sdr['righttotal']
        n_r = sdr['righttotal']
        l_s = sdr['sumtotalLeft']
        l_s_sq = sdr['sumsqtotalLeft']
        r_s = sdr['sumtotalRight']
        r_s_sq = sdr['sumsqtotalRight']
        total = float(n_l+n_r)
        base = self.sd(n_l+n_r, l_s_sq+r_s_sq, l_s+r_s)
        sd_l = self.sd(n_l,l_s_sq,l_s)
        ratio_l = n_l/total
        sd_r = self.sd(n_r,r_s_sq,r_s)
        ratio_r = n_r/total
        return base - (ratio_l*sd_l) - (ratio_r*sd_r)

    def hoefding_bound(self,n):
        
        log = np.log(1.0/self.gamma)
        n = 2*n
        result = np.sqrt(log/n)
        return result

import padasip as pa
class LinearRegressor:

    def __init__(self,leafnode,w=None,learn = 0.01):
        self.leafnode = leafnode
        self.l = learn
        self.covM = 10 ** 3
        if w is None:
            self.w = w
        else:
            self.w = np.zeros(len(w))
            for i in range(len(self.w)):
                self.w[i] = w[i]
            self.S = self.covM * np.identity(len(self.w))
            self.filter = pa.filters.FilterRLS(len(self.w))
        self.x_count = None
        self.x_sq_count = None
        self.c = 0.0

        self.forgF = 1.0

    def eval(self,x):
        if self.x_count is None:
            self.x_count = np.zeros(len(x))
            self.x_sq_count = np.zeros(len(x))
        x = np.hstack((1.0,x))
        if self.w is None:
            self.w = np.random.rand(len(x))
            self.w = self.w/np.linalg.norm(self.w)
            self.S = self.covM * np.identity(len(self.w))
            self.filter = pa.filters.FilterRLS(len(self.w))
        yp = np.inner(x,self.w)
        return yp

    def eval_and_learn(self,x,y):
        yp = self.eval(x)
        self.x_count += x
        self.x_sq_count += x**2
        self.c += 1.0
        x = self.normalize(x,y)
        x = np.hstack((1.0,x))
        self.learn(x,y,yp)
        return yp

    def rls_learn(self, x, phiX, y, yp):
        deltaAlpha = np.dot(self.S, phiX) / ((self.forgF + np.inner(phiX, np.dot(self.S, phiX))) * (y - yp))

        self.S = self.S / self.forgF - np.outer(np.dot(self.S, phiX), np.dot(phiX, self.S)) \
                                       / (self.forgF * (self.forgF + np.inner(np.dot(phiX, self.S), phiX)))

        self.filter.adapt(y,x)
        return deltaAlpha

    def learn(self,x,y,yp):
        delta = self.l * (y - yp)*x
        self.rls_learn(x,self.w,y,yp)
        self.w += delta

    def normalize(self,x,y):
        sd = self.leafnode.sd(self.c,self.x_sq_count,self.x_count)
        avg = self.x_count/self.c
        for i,xi in enumerate(x):
            if sd[i] != 0.0:
                x[i] = (xi - avg[i])/(3*sd[i])
            else:
                x[i] = 0.0
        return x

    def denormalize(self,x,y):
        pass

class E_BST:

    def __init__(self,root = None):
        self.root = root

    def add(self,key,y):
        if self.root is None:
            self.root = Node_EBST(key,y)
        else:
            self.root.add(key,y)

class Node_EBST:

    def __init__(self,x,y,parent = None):
        self.key = x
        self.parent = parent
        self.left = None
        self.right = None

        self.l_count = 1
        self.l_y = y
        self.l_y_sq = y**2

        self.r_count = 0
        self.r_y = 0
        self.r_y_sq = 0

    def add(self,val,y):
        if val <= self.key:
            self.l_count += 1
            self.l_y += y
            self.l_y_sq += y**2
            if self.left is None and val != self.key:
                self.left = Node_EBST(val,y,self)
            elif val == self.key:
                pass
            else:
                self.left.add(val,y)
        else:
            self.r_count += 1
            self.r_y += y
            self.r_y_sq += y**2
            if self.right is None:
                self.right = Node_EBST(val,y,self)
            else:
                self.right.add(val,y)
        return

global l
l = 0

model = Reg_Hoeff_Tree()

import pandas as pd

tr = pd.read_csv("Train.csv")

usecols=['feature_1', 'feature_2', 'feature_3', 'feature_4', 'feature_5']

x = tr.loc[:, usecols].values

y = tr.loc[:, ['target']].values

for i in range(len(y)):
  model.eval_and_learn(x[i],y[i])

tr1 = pd.read_csv("Test.csv")

xtest = tr1.loc[:, usecols].values

ytest = tr1.loc[:, ['target']].values

error=0
yp = []
for i in range(len(ytest)):
  yp.append(model.eval(xtest[i]))
  error += (yp[i]-ytest[i])**2

(error/np.sum(ytest**2))

dict = {"feature_1": xtest[:, 0], "feature_2": xtest[:, 1], "feature_3": xtest[:, 2], "feature_4": xtest[:, 3], "feature_5": xtest[:, 4], "results": yp}

df = pd.DataFrame(dict)

df

df.to_csv('test_results.csv', index=False)
