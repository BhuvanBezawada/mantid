from mantid import config, logger, mtd, AlgorithmFactory
from mantid.api import *
from mantid.kernel import *
from mantid.simpleapi import *
import os.path

class FuryFitMultiple(PythonAlgorithm):
 
    def category(self):
        return "Workflow\\MIDAS;PythonAlgorithms"

    def PyInit(self):
        self.declareProperty(name="InputType", defaultValue="File",validator=StringListValidator(['File', 'Workspace']),
                             doc='Origin of data input - File (_red.nxs) or Workspace')
        self.declareProperty(name="Instrument", defaultValue="iris",validator=StringListValidator(['irs', 'iris', 'osi', 'osiris']),
                             doc='Instrument')
        self.declareProperty(name='Analyser', defaultValue='graphite002', validator=StringListValidator(['graphite002', 'graphite004']),
                             doc='Analyser & reflection')
        self.declareProperty(name="RunNumber",defaultValue=-1, validator=IntBoundedValidator(lower=0),
                             doc="Sample run number")
        self.declareProperty(name="TimeMax", defaultValue=0.2, validator=FloatMandatoryValidator(), 
                             doc="Multiplicative scale factor")
        self.declareProperty(name='Plot', defaultValue='None', validator=StringListValidator(['None', 'Intensity', 'Tau', 'Beta', 'All']),
                             doc='Switch Plot Off/On')
 
    def PyExec(self):
        from IndirectDataAnalysis import furyfitMult

        workdir = config['defaultsave.directory']
        inType = self.getProperty('InputType').value
        prefix = self.getProperty('Instrument').value
        ana = self.getProperty('Analyser').value
        RunNumb = self.getProperty('RunNumber').value
        xMax = self.getProperty('TimeMax').value
        file = prefix + str(RunNumb) + '_' + ana
        plotOp = self.getProperty('Plot').value
        inWS = file + '_iqt'
        if inType == 'File':
            spath = os.path.join(workdir, inWS + '.nxs')  # path name for sample nxs file
            logger.notice('Input from File : ' + spath)
            LoadNexusProcessed(Filename=spath, OutputWorkspace=inWS)
        else:
            logger.notice('Input from Workspace : ' + inWS)
        CropWorkspace(InputWorkspace=inWS, OutputWorkspace=inWS, XMin=0.0, XMax=xMax)
        function = 'name=LinearBackground,A0=0.02,A1=0,ties=(A1=0);'
        function +=     'name=UserFunction,Formula=Intensity*exp(-(x/Tau)^Beta),Intensity=0.98,Tau=0.02,Beta=0.8'

        furyfitMult(inWS, function, 'SSSS', 0.0, 0.2, False, plotOp, True)

AlgorithmFactory.subscribe(FuryFitMultiple)