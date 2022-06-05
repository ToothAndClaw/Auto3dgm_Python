from pathos.multiprocessing import ProcessingPool as Pool
import pathos.multiprocessing as multiprocessing 
import logging
#mpl = multiprocessing.log_to_stderr()
#mpl.setLevel(logging.INFO)
import traceback
import pdb
from tvtk.api import tvtk 
from numpy import all, amin, any, argmax, array, isclose, ndarray, where, empty
import random
from scipy.spatial.distance import cdist
from auto3dgm_nazar.mesh.mesh import Mesh
from auto3dgm_nazar.mesh.meshfactory import MeshFactory
import numpy as np


class Multi:
    def multi_run_wrapper(twargs):
        fun=twargs['func']
        data=twargs['data']
        params=twargs['params']
        results=fun(**data,**params)
        return(results)   
