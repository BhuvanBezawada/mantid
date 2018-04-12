from __future__ import print_function

from mantid.simpleapi import CreateWorkspace, RenameWorkspace
from mantid.api import AlgorithmFactory, PropertyMode, PythonAlgorithm, WorkspaceProperty
from mantid.kernel import Direction
import numpy as np


class ApplyDetectorScanEffCorr(PythonAlgorithm):

    def category(self):
        return 'ILL\\Diffraction;Diffraction\\Utility'

    def seeAlso(self):
        return [ "PowderDiffILLDetEffCorr","LoadILLDiffraction" ]

    def name(self):
        return 'ApplyDetectorScanEffCorr'

    def summary(self):
        return 'Applies the calibration workspace generated by PowderDiffILLDetEffCorr to data loaded with LoadILLDiffraction.'

    def PyInit(self):
        self.declareProperty(WorkspaceProperty("InputWorkspace", "",
                                               optional=PropertyMode.Mandatory,
                                               direction=Direction.Input),
                             "The workspace for the detector efficiency correction to be applied to.")
        self.declareProperty(WorkspaceProperty("DetectorEfficiencyWorkspace", "",
                                               optional=PropertyMode.Mandatory,
                                               direction=Direction.Input),
                             "The workspace containing the detector efficiency correction factors generated by PowderDiffILLDetEffCorr.")
        self.declareProperty(WorkspaceProperty("OutputWorkspace", "",
                                               optional=PropertyMode.Mandatory,
                                               direction=Direction.Output),
                             "The output workspace with the calibrated data. Optionally can be the same as the input workspace.")

    def PyExec(self):
        input_ws = self.getProperty("InputWorkspace").value
        efficiency_workspace = self.getProperty("DetectorEfficiencyWorkspace").value

        y_values = input_ws.extractY()
        y_values = y_values.reshape(y_values.size)
        e_values = input_ws.extractE()
        e_values = e_values.reshape(e_values.size)

        efficiency_values = efficiency_workspace.extractY()
        efficiency_values = efficiency_values.reshape(efficiency_values.size)

        detector_info = input_ws.detectorInfo()
        for i in range(detector_info.size()):
            if detector_info.isMonitor(i):
                efficiency_values = np.insert(efficiency_values, 0, 1) # add the monitor efficiency

        if (y_values.size % efficiency_values.size) is not 0:
            raise ValueError('Number of entries in input workspace is not a multiple of number of efficiencies in detector efficiency '
                             'workspace.')
        number_time_indexes = y_values.size / efficiency_values.size

        full_efficiency_values = np.repeat(efficiency_values, number_time_indexes)
        y_values *= full_efficiency_values
        e_values *= full_efficiency_values

        __output_ws = CreateWorkspace(DataX=input_ws.extractX(), DataY=y_values, DataE=e_values, Nspec=y_values.size,
                                      ParentWorkspace=input_ws)

        RenameWorkspace(__output_ws, self.getPropertyValue("OutputWorkspace"))
        self.setProperty("OutputWorkspace", __output_ws)

AlgorithmFactory.subscribe(ApplyDetectorScanEffCorr)
