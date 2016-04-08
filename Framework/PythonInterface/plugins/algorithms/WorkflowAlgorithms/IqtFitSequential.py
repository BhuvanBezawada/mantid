#pylint: disable=no-init, too-many-instance-attributes
from mantid import logger, AlgorithmFactory
from mantid.api import *
from mantid.kernel import *
from mantid.simpleapi import *
import os.path

class IqtFitSequential(PythonAlgorithm):




    def category(self):
        return "Workflow\\MIDAS"

    def summary(self):
        #pylint: disable=anomalous-backslash-in-string
        return "Fits an \*\_iqt file generated by I(Q,t) sequentially."

    def PyInit(self):


    def validateInputs(self):


    def _get_properties(self):


    def PyExec(self):


AlgorithmFactory.subscribe(IqtFitSequential)
