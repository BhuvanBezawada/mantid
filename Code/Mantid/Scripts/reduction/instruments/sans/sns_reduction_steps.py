"""
    Implementation of reduction steps for SNS EQSANS
    
    TODO:   - Allow use of FindNexus when we are on an analysis computer  
"""
import os
from reduction import ReductionStep
from sans_reduction_steps import BaseTransmission
from reduction import extract_workspace_name

# Mantid imports
from mantidsimple import *

class LoadRun(ReductionStep):
    """
        Load a data file, move its detector to the right position according
        to the beam center and normalize the data.
    """
    def __init__(self, datafile=None):
        super(LoadRun, self).__init__()
        self._data_file = datafile
                
    def execute(self, reducer, workspace, force=False):      
        # If we don't have a data file, look up the workspace handle
        # Only files that are used for computing data corrections have
        # a path that is passed directly. Data files that are reduced
        # are simply found in reducer._data_files 
        if self._data_file is None:
            if workspace in reducer._data_files:
                data_file = reducer._data_files[workspace]
            elif workspace in reducer._extra_files:
                data_file = reducer._extra_files[workspace]
            else:
                raise RuntimeError, "SNSReductionSteps.LoadRun doesn't recognize workspace handle %s" % workspace
        else:
            data_file = self._data_file
        
        # Load data
        filepath = reducer._full_file_path(data_file)

        # Check whether that file was already loaded
        # The file also has to be pristine
        if mtd[workspace] is not None and not force and reducer.is_clean(workspace):
            mantid.sendLogMessage("Data %s is already loaded: delete it first if reloading is intended" % (workspace))
            return "Data %s is already loaded: delete it first if reloading is intended" % (workspace)

        # Find all the necessary files
        event_file = ""
        pulseid_file = ""
        nxs_file = ""
        
        # Check if we have an event file or a pulseid file.
        is_event_nxs = False
        
        if filepath.find("_neutron_event")>0:
            event_file = filepath
            pulseid_file = filepath.replace("_neutron_event", "_pulseid")
        elif filepath.find("_pulseid")>0:
            pulseid_file = filepath
            event_file = filepath.replace("_pulseid", "_neutron_event")
        else:
            #raise RuntimeError, "SNSReductionSteps.LoadRun couldn't find the event and pulseid files"
            # Doesn't look like event pre-nexus, try event nexus
            is_event_nxs = True
        
        # Mapping file
        mapping_file = reducer.instrument.definition.getStringParameter("TS_mapping_file")[0]
        directory,_ = os.path.split(event_file)
        mapping_file = os.path.join(directory, mapping_file)
        
        if is_event_nxs:
            mantid.sendLogMessage("Loading %s as event Nexus" % (filepath))
            LoadSNSEventNexus(Filename=filepath, OutputWorkspace=workspace+'_evt')
        else:
            mantid.sendLogMessage("Loading %s as event pre-Nexus" % (filepath))
            nxs_file = event_file.replace("_neutron_event.dat", ".nxs")
            LoadEventPreNeXus(EventFilename=event_file, OutputWorkspace=workspace+'_evt', PulseidFilename=pulseid_file, MappingFilename=mapping_file, PadEmptyPixels=1)
            LoadLogsFromSNSNexus(Workspace=workspace+'_evt', Filename=nxs_file)
        
        # Store the sample-detector distance.
        sdd = mtd[workspace+'_evt'].getRun()["detectorZ"].getStatistics().mean
        mtd[workspace+'_evt'].getRun().addProperty_dbl("sample_detector_distance", sdd, True)
        
        # Move the detector to its correct position
        MoveInstrumentComponent(workspace+'_evt', "detector1", Z=sdd/1000.0, RelativePosition=0)

        # Move detector array to correct position
        [pixel_ctr_x, pixel_ctr_y] = reducer.get_beam_center()
        if pixel_ctr_x is not None and pixel_ctr_y is not None:
            [beam_ctr_x, beam_ctr_y] = reducer.instrument.get_coordinate_from_pixel(pixel_ctr_x, pixel_ctr_y)
            [default_pixel_x, default_pixel_y] = reducer.instrument.get_default_beam_center()
            [default_x, default_y] = reducer.instrument.get_coordinate_from_pixel(default_pixel_x, default_pixel_y)
            MoveInstrumentComponent(workspace+'_evt', "detector1", 
                                    X = default_x-beam_ctr_x,
                                    Y = default_y-beam_ctr_y,
                                    RelativePosition="1")
        else:
            mantid.sendLogMessage("Beam center isn't defined: skipping beam center alignment for %s" % workspace)

        # Modify TOF
        a = EQSANSTofStructure(InputWorkspace=workspace+'_evt')
        offset = float(a.getPropertyValue("TofOffset"))
        wl_min = float(a.getPropertyValue("WavelengthMin"))
        wl_max = float(a.getPropertyValue("WavelengthMax"))
        frame_skipping = a.getPropertyValue("FrameSkipping")
        mantid.sendLogMessage("Frame-skipping option: %s" % str(frame_skipping))
        
        x_step = 100
        x_min = offset-offset%x_step
        x_max = 2*1e6/60.0+offset
        x_max -= x_max%x_step
        Rebin(workspace+'_evt', workspace, "%6.0f, %6.0f, %6.0f" % (x_min, x_step, x_max))

        ConvertUnits(workspace, workspace, "Wavelength")
        
        # Rebin so all the wavelength bins are aligned
        Rebin(workspace, workspace, "%4.2f,%4.2f,%4.2f" % (wl_min, 0.1, wl_max))
        
        mantid.sendLogMessage("Loaded %s: sample-detector distance = %g [frame-skipping: %s]" %(workspace, sdd, str(frame_skipping)))
        
        # Remove the dirty flag if it existed
        reducer.clean(workspace)
        return "Data file loaded: %s" % (workspace)



class Normalize(ReductionStep):
    """
        Normalize the data to the accelerator current
    """
    def execute(self, reducer, workspace):
        # Flag the workspace as dirty
        reducer.dirty(workspace)
        
        #NormaliseByCurrent(workspace, workspace)
        proton_charge = mantid.getMatrixWorkspace(workspace).getRun()["proton_charge"].getStatistics().mean
        duration = mantid.getMatrixWorkspace(workspace).getRun()["proton_charge"].getStatistics().duration
        frequency = mantid.getMatrixWorkspace(workspace).getRun()["frequency"].getStatistics().mean
        acc_current = 1.0e-12 * proton_charge * duration * frequency
        Scale(InputWorkspace=workspace, OutputWorkspace=workspace, Factor=1.0/acc_current, Operation="Multiply")
        
        return "Data normalized to accelerator current" 
    
    
class Transmission(BaseTransmission):
    """
        Perform the transmission correction for EQ-SANS
    """
    def __init__(self, normalize_to_unity=False, theta_dependent=False):
        super(Transmission, self).__init__()
        self._normalize = normalize_to_unity
        self._theta_dependent = theta_dependent
        self._transmission_ws = None
    
    def execute(self, reducer, workspace):
        # The transmission calculation only works on the original un-normalized counts
        if not reducer.is_clean(workspace):
            raise RuntimeError, "The Transmission can only be calculated using un-modified data"
        
        beam_center = reducer.get_beam_center()

        if self._transmission_ws is None:
            self._transmission_ws = "transmission_"+workspace

        # Calculate the transmission as a function of wavelength
        EQSANSTransmission(InputWorkspace=workspace,
                           OutputWorkspace=self._transmission_ws,
                           XCenter=beam_center[0],
                           YCenter=beam_center[1],
                           NormalizeToUnity = self._normalize)
        
        # Apply the transmission. For EQSANS, we just divide by the 
        # transmission instead of using the angular dependence of the
        # correction.
        reducer.dirty(workspace)
        if self._theta_dependent:
            # To apply the transmission correction using the theta-dependent algorithm
            # we should get the beam spectrum out of the measured transmission
            # We should then re-apply it when performing normalization
            ApplyTransmissionCorrection(workspace, workspace, self._transmission_ws)
        else:
            Divide(workspace, self._transmission_ws, workspace)
        ReplaceSpecialValues(workspace, workspace, NaNValue=0.0,NaNError=0.0)
        
        return "Transmission correction applied"
    
    
class SubtractDarkCurrent(ReductionStep):
    """
        Subtract the dark current from the input workspace.
        Works only if the proton charge time series is available from DASlogs.
    """
    def __init__(self, dark_current_file):
        super(SubtractDarkCurrent, self).__init__()
        self._dark_current_file = dark_current_file
        self._dark_current_ws = None
        
    def execute(self, reducer, workspace):
        """
            Subtract the dark current from the input workspace.
            If no timer workspace is provided, the counting time will be extracted
            from the input workspace.
            
            @param reducer: Reducer object for which this step is executed
            @param workspace: input workspace
        """
        # Sanity check
        if self._dark_current_file is None:
            raise RuntimeError, "SubtractDarkCurrent called with no defined dark current file"

        # Check whether the dark current was already loaded, otherwise load it
        # Load dark current, which will be used repeatedly
        if self._dark_current_ws is None:
            filepath = reducer._full_file_path(self._dark_current_file)
            self._dark_current_ws = extract_workspace_name(filepath)
            reducer._data_loader.__class__(datafile=filepath).execute(reducer, self._dark_current_ws)
            
        # Normalize the dark current data to counting time
        dark_duration = mtd[self._dark_current_ws].getRun()["proton_charge"].getStatistics().duration
        duration = mtd[workspace].getRun()["proton_charge"].getStatistics().duration
        scaling_factor = duration/dark_duration
    
        # Scale the stored dark current by the counting time
        scaled_dark_ws = "scaled_dark_current"
        Scale(InputWorkspace=self._dark_current_ws, OutputWorkspace=scaled_dark_ws, Factor=scaling_factor, Operation="Multiply")
        
        # Perform subtraction
        Minus(workspace, scaled_dark_ws, workspace)  
        
        return "Dark current subtracted [%s]" % (scaled_dark_ws)
    
        