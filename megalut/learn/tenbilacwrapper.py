"""
Wrapper around Tenbilac

https://github.com/mtewes/tenbilac

There is not that much to do here, as tenbilac directly uses numpy arrays natively.

"""


import os
import numpy as np
from datetime import datetime

import tenbilac

import logging
logger = logging.getLogger(__name__)




class TenbilacParams:
	"""
	
	"""
	
	
	def __init__(self, hidden_nodes, errfctname="msrb", max_iterations=100, 
		valfrac=0.5, shuffle=True, mbsize=None, mbloops=1,
		normtype="-11", actfctname="tanh", verbose=False, name="default", reuse=True, keepdata=False):
		"""
		
		:param hidden_nodes: list giving the number of nodes per hidden layer
		:param max_itrations: 
		:param errfct: either "msb" or "msrb"
		:param normtype:
		:param actfct: either "sig" or "tanh"
		:param name:
		
		:param reuse: if True, will start the training from the existing state (if available)
		
		:param keepdata: if True, the data is kept in the final pickle saved once the training is done.
			Can be useful for plots and debugging, but is huge.
		
		"""
		self.hidden_nodes = hidden_nodes 
		self.max_iterations = max_iterations
		self.errfctname = errfctname
		self.valfrac = valfrac
		self.shuffle = shuffle
		self.mbsize = mbsize
		self.mbloops = mbloops
		self.normtype = normtype
		self.actfctname = actfctname
		self.verbose = verbose
		self.name = name
		self.reuse = reuse
		self.keepdata = keepdata
		
		
	def __str__(self):
		return "Tenbilac parameters \"{self.name}\" ({self.hidden_nodes}, {self.max_iterations}, {self.normtype}, {self.actfctname}, self.errfctname)".format(self=self)
		

class TenbilacWrapper:

	def __init__(self, params, workdir=None):
	
		if workdir == None:
			self.workdir = "Tenbilac_workdir"
		else:
			self.workdir = workdir
		
		self.netpath = os.path.join(self.workdir, "Tenbilac.pkl")
			
		self.params = params
		
		
	def __str__(self):
		return "Tenbilac '%s' in %s" % (self.params.name, os.path.basename(self.workdir))

	
	def train(self, features, labels):
		"""
		Note that we might take over a previous training.
		
		:param features: a 3D numpy array, possibly masked, with indices (rea, feature, galaxy)
		:param labels: a 2D array, with indices (label, galaxy)
		
		"""
		starttime = datetime.now()
		
		# Setting up the workdir:
		if not os.path.isdir(self.workdir):
			os.makedirs(self.workdir)
		else:
			logger.info("Tenbilac workdir %s already exists" % self.workdir)
			
		# Some tests to start with
		assert features.ndim == 3
		assert labels.ndim == 2
		
		# We normalize the features and labels, and save the Normers for later denormalizing.
		logger.info("{0}: normalizing training features...".format((str(self))))
		self.feature_normer = tenbilac.data.Normer(features, type=self.params.normtype)
		normfeatures = self.feature_normer(features)
		
		logger.info("{0}: normalizing training labels...".format((str(self))))
		self.label_normer = tenbilac.data.Normer(labels, type=self.params.normtype)
		normlabels = self.label_normer(labels)

		# We can prep the traindata object:
		dat = tenbilac.data.Traindata(normfeatures, normlabels, valfrac=self.params.valfrac, shuffle=self.params.shuffle)


		# Now we take care of setting up the network (even if we might reuse an existing one)
		ni = features.shape[1]
		nhs = self.params.hidden_nodes
		no = labels.shape[0]
		ann = tenbilac.net.Tenbilac(ni, nhs, no, actfctname=self.params.actfctname)
		
		# And set up the training object:
		training = tenbilac.train.Training(ann, dat, 
				errfctname=self.params.errfctname,
				itersavepath=self.netpath,
				verbose=self.params.verbose,
				name=self.params.name)


		# Let's see if an existing training is available
		oldtrain = None
		if os.path.exists(self.netpath) and self.params.reuse:
			# Then we try to read the existing training and start the training from it's parameters.
			logger.info("Reading in existing training... ")
			oldtrain = tenbilac.utils.readpickle(self.netpath)			

	
		# And now see if we take over the previous trainign or not:
		if oldtrain is None:
			training.net.setidentity()
			training.net.addnoise(wscale=0.1, bscale=0.1)
						
		else:
			logger.info("Reusing previous network!")
			training.takeover(oldtrain)

		# Ready!

		logger.info("{0}: starting the training".format((str(self))))
		
		#training.bfgs(maxiter=self.params.max_iterations)
		
		training.minibatch_bfgs(mbsize=self.params.mbsize, mbloops=self.params.mbloops, maxiter=self.params.max_iterations)
		
		training.save(self.netpath, self.params.keepdata)
	
		
	
	
	def predict(self, features):
			
		# We read the Tenbilac:
		training = tenbilac.utils.readpickle(self.netpath)
		ann = training.net
		
		logger.info("{0}: normalizing features for prediction...".format((str(self))))
		normfeatures = self.feature_normer(features)
		
		# As simple as this:		
		normpreds = ann.predict(normfeatures)
		
		# Those normpreds are appropriatedly masked.
		# We denormalize these predictions
	
		preds = self.label_normer.denorm(normpreds)
	
		return preds
	
		

if __name__ == "__main__":
	"""
	A little demo and test !
	"""
	
	"""
	import matplotlib.pyplot as plt
	import logging
	logging.basicConfig(level=logging.DEBUG)

	# Simple 1D case : we predict y(x) from noisy data points.
	
	
	n = 100
	x = np.random.uniform(0, 10, n)
	y = np.sin(x)*x + 0.3*np.random.randn(len(x))
	
	#x = np.random.uniform(-5, 10, n)
	#y = np.sin(x)*x + 0.3*np.random.randn(len(x))
	#y[x<=0] += 5
	
	
	
	# x and y are 1D arrays. But our SkyNet wrapper works only with 2D arrays.
	# First index = datapoint, sedond index : the different features.
	
	features = x.reshape(n, 1)
	labels = y.reshape(n, 1)
	
	
	for nhid in [10]:
	
		plt.clf()
		params = FANNParams(hidden_nodes = [nhid], learning_rate=0.5,
				    max_iterations=1000, activation_steepness_hidden=0.5)
	
		obj = FANNWrapper(params)
		obj.train(features, labels)
	
		# Let's make some predictions on a fine grid of points :
		pred_features = np.linspace(-2, 12, 1000).reshape(1000, 1)
		pred_labels = obj.predict(pred_features)
	
		#print pred_labels.shape
		#print pred_features.shape
	
		plt.plot(x, y, "r.")
		plt.plot(pred_features, pred_labels, "b-")
		plt.xlabel("x")
		plt.ylabel("y")
		#plt.xlim(-7, 12)
		plt.xlim(-2, 12)
		
		plt.ylim(-10, 10)
		#plt.show()
		#plt.title("%i hidden nodes" % (nhid))
		#plt.savefig("%i.pdf" % (nhid))
		plt.show()

	"""
