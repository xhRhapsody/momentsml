import matplotlib
matplotlib.use("AGG")


import megalut
import config
import measfcts
import simparams

import glob
import os
import numpy as np
import astropy

import logging
logger = logging.getLogger(__name__)




traindir = os.path.join(config.workdir, "train_Nico4nn")
traincatpath = os.path.join(config.simdir, "Nico4nn", "groupmeascat.pkl")

#traindir = os.path.join(config.workdir, "train_Nico4")
#traincatpath = os.path.join(config.simdir, "Nico4", "groupmeascat.pkl")


conflist = [
	#("conf/ada4g1.cfg", "conf/sum55.cfg"),
	#("conf/ada4g2.cfg", "conf/sum55.cfg")
	("conf/ada4g1.cfg", "conf/sum55.cfg")
	#("conf/ada4g2.cfg", "conf/sum55.cfg")
	#("conf/ada4g1.cfg", "conf/mult44free.cfg")
	#("conf/fh4g1.cfg", "conf/sum55.cfg")
	#("conf/fh4g2.cfg", "conf/sum55.cfg")
]



traincat = megalut.tools.io.readpickle(traincatpath)
dirnames = megalut.learn.tenbilacrun.train(traincat, conflist, traindir)
dirname = dirnames[0]
#dirname = "fh4g1_sum55"


# Self-predicting

precatpath = os.path.join(traindir, dirname, "selfprecat.pkl")

cat = megalut.tools.io.readpickle(traincatpath)
cat = megalut.learn.tenbilacrun.predict(cat, conflist, traindir)
print megalut.tools.table.info(cat)
megalut.tools.io.writepickle(cat, precatpath)


# Predicting the validation set

valcatpath = os.path.join(config.simdir, "Nico4shear_snc10000", "groupmeascat_cases.pkl")
valprecatpath = os.path.join(traindir, dirname, "valprecat.pkl")

cat = megalut.tools.io.readpickle(valcatpath)
cat = megalut.learn.tenbilacrun.predict(cat, conflist, traindir)
megalut.tools.io.writepickle(cat, valprecatpath)

# Idem for the low-SN set:

valcatpath = os.path.join(config.simdir, "Nico4shear_snc10000_lowSN", "groupmeascat_cases.pkl")
valprecatpath = os.path.join(traindir, dirname, "valprecat_lowSN.pkl")

cat = megalut.tools.io.readpickle(valcatpath)
cat = megalut.learn.tenbilacrun.predict(cat, conflist, traindir)
megalut.tools.io.writepickle(cat, valprecatpath)

