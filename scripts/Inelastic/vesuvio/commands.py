# pylint: disable=too-many-arguments,invalid-name,too-many-locals,too-many-branches
"""
Defines functions and classes to start the processing of Vesuvio data.
The main entry point that most users should care about is fit_tof().
"""
from __future__ import (absolute_import, division, print_function)

import re
import numpy as np

import itertools

from mantid import mtd
from mantid.api import (AlgorithmManager, AnalysisDataService, MatrixWorkspace, WorkspaceFactory, TextAxis)
from mantid.kernel import MaterialBuilder
from mantid.simpleapi import (CropWorkspace, ConjoinWorkspaces, DeleteWorkspace, GroupWorkspaces, LoadVesuvio, Rebin,
                              RenameWorkspace, UnGroupWorkspace, VesuvioCorrections, VesuvioTOFFit)

from vesuvio.loading import VesuvioLoadHelper, VesuvioTOFFitInput

# --------------------------------------------------------------------------------
# Functions
# --------------------------------------------------------------------------------

def fit_tof(runs, flags, iterations=1, convergence_threshold=None):
    vesuvio_loader = VesuvioLoadHelper(flags['diff_mode'], flags['fit_mode'],
                                       flags['ip_file'], flags['bin_parameters'],
                                       flags.get('load_log_files', True))

    vesuvio_input = VesuvioTOFFitInput(runs, flags['container_runs'],
                                       flags['spectra'], vesuvio_loader)
    ms_helper = None
    if flags.get('ms_enabled', True):
        hydrogen_constraints = flags['ms_flags'].pop("HydrogenConstraints", {})
        ms_helper = VesuvioMSHelper(**flags['ms_flags'])
        ms_helper.add_hydrogen_constraints(hydrogen_constraints)

    fit_helper = VesuvioTOFFitHelper(_create_background_str(flags.get('background', None)),
                                     _create_intensity_constraint_str(flags['intensity_constraints']),
                                     _create_user_defined_ties_str(flags['masses']),
                                     flags.get('max_fit_iterations', 5000),
                                     flags['fit_minimizer'])

    corrections_helper = VesuvioCorrectionsHelper(flags.get('gamma_correct', False),
                                                  flags.get('ms_enabled', True),
                                                  flags.get('fixed_gamma_scaling', 0.0),
                                                  flags.get('fixed_container_scaling', 0.0),
                                                  flags['intensity_constraints'])

    create_mass_profile = _mass_profile_generator(MaterialBuilder())
    profiles = [create_mass_profile(profile) for profile in flags['masses']]
    mass_profile_collection = MassProfileCollection2D(MassProfileCollection(profiles))

    vesuvio_fit_routine = VesuvioTOFFitRoutine(ms_helper, fit_helper, corrections_helper,
                                               mass_profile_collection, flags['fit_mode'])
    vesuvio_output, result, exit_iteration  = vesuvio_fit_routine(vesuvio_input, iterations, convergence_threshold,
                                                                  flags.get('output_verbose_corrections', False))
    return (result, vesuvio_output.prefit_parameters_workspace, vesuvio_output.fit_parameters_workspace, exit_iteration)

# -----------------------------------------------------------------------------------------

class VesuvioTOFFitRoutine(object):
    """
    A class for executing the the Vesuvio TOF Fit Routine from a Vesuvio Driver Script.

    Attributes:
        _ms_helper                   A helper object for multiple scattering parameters.
        _fit_helper                  A helper object for computing a VesuvioTOFFit.
        _corrections_helper          A helper object for computing VesuvioCorrections.
        _mass_profile_collection     An object for storing and manipulating mass values
                                     and profiles.
        _fit_mode                    The fit mode to use in the fitting routine.
    """

    def __init__(self, ms_helper, fit_helper, corrections_helper, mass_profile_collection, fit_mode):
        self._ms_helper = ms_helper
        self._fit_helper = fit_helper
        self._corrections_helper = corrections_helper
        self._mass_profile_collection = mass_profile_collection
        self._fit_mode = fit_mode

    def __call__(self, vesuvio_input, iterations, convergence_threshold, verbose_output=False):
        if iterations < 1:
            raise ValueError('Must perform at least one iteration')
        # Creation of a fit routine iteration
        tof_iteration = VesuvioTOFFitRoutineIteration(self._ms_helper, self._fit_helper,
                                                      self._corrections_helper,
                                                      VesuvioFitNamer(vesuvio_input, self._fit_mode),
                                                      self._mass_profile_collection,
                                                      self._fit_mode)

        update_filter = ignore_hydrogen_filter if vesuvio_input.using_back_scattering_spectra else None
        exit_iteration = 0
        previous_output = None
        vesuvio_output = None
        fit_output = None
        corrections_output = None

        for iteration in range(1, iterations + 1):
            # Update the mass profiles using the previous result if it exists
            if vesuvio_output is not None:
                parameters = _extract_parameters_from_workspace(vesuvio_output.fit_parameters_workspace)
                self._mass_profile_collection.update_profiles(parameters, update_filter)

            print("=== Iteration {0} out of a possible {1}".format(iteration, iterations))
            vesuvio_output = tof_iteration(vesuvio_input, vesuvio_output, iteration, verbose_output)
            exit_iteration += 1
            # Check whether the change in the cost function between the result and
            # previous results is smaller than the convergence threshold.
            if previous_output is not None and convergence_threshold is not None:
                cost_function_change = _change_in_cost_function(previous_output, vesuvio_output)
                print("Cost function change: {0}".format(cost_function_change))

                if cost_function_change <= convergence_threshold:
                    print("Stopped at iteration {0} due to minimal change in cost function"
                          .format(exit_iteration))
                    return vesuvio_output, exit_iteration

            _add_parameters_to_ads(vesuvio_output, vesuvio_input.sample_runs, iteration)
            fit_output = _add_fit_output_to_ads(vesuvio_output, vesuvio_input.sample_runs, iteration)
            corrections_output = _group_corrections(vesuvio_output, vesuvio_input.sample_runs, iteration)
            previous_output = vesuvio_output
        return vesuvio_output, [x for x in (fit_output, corrections_output) if x is not None], exit_iteration


# ------------------------------------------------------------------------------------------------------

class VesuvioTOFFitRoutineIteration(object):
    """
    A class for executing a single iteration of the Vesuvio TOF Fit Routine, from a
    Vesuvio Driver Script.

    Attributes:
        _ms_helper                   A helper object for multiple scattering parameters.
        _fit_helper                  A helper object for computing a VesuvioTOFFit.
        _corrections_helper          A helper object for computing VesuvioCorrections.
        _mass_profile_collection     An object for storing and manipulating mass values
                                     and profiles.
        _fit_mode                    The fit mode to use in the fitting routine.
    """

    def __init__(self, ms_helper, fit_helper, corrections_helper, fit_namer, mass_profile_collection, fit_mode):
        if ms_helper is not None:
            self._ms_corrections_args = ms_helper.to_dict()
        else:
            self._ms_corrections_args = {}

        self._fit_helper = fit_helper
        self._fit_namer = fit_namer
        self._corrections_helper = corrections_helper
        self._mass_profile_collection = mass_profile_collection
        self._fit_mode = fit_mode

    def __call__(self, vesuvio_input, iteration, verbose_output=False):
        self._fit_namer.set_iteration(iteration)
        vesuvio_output = VesuvioTOFFitOutput()

        if vesuvio_input.using_back_scattering_spectra:
            fit_profile_collection = self._mass_profile_collection.filter(ignore_hydrogen_filter)
        else:
            fit_profile_collection = self._mass_profile_collection

        all_mass_values = self._mass_profile_collection.masses
        fit_mass_values = fit_profile_collection.masses

        for index in range(vesuvio_input.sample_data.getNumberHistograms()):
            self._fit_namer.set_index(index)
            all_profiles = self._mass_profile_collection.functions(index)
            fit_profiles = fit_profile_collection.functions(index)

            # Calculate pre-fit to retrieve parameter approximations for corrections
            prefit_result = self._prefit(vesuvio_input.sample_data, index, fit_mass_values, fit_profiles)

            # Calculate corrections
            corrections_result = self._corrections(vesuvio_input.sample_data, vesuvio_input.container_data, index,
                                                   all_mass_values, all_profiles, prefit_result[1], verbose_output)

            # Calculate final fit
            fit_result = self._final_fit(corrections_result[-1], index, fit_mass_values, fit_profiles)

            # Update output with results from fit
            _update_output(vesuvio_output, prefit_result, corrections_result, fit_result)

            # Clear ADS of intermediate workspaces and workspace groups
            UnGroupWorkspace(corrections_result[0])
            UnGroupWorkspace(corrections_result[1])
            mtd.remove(prefit_result[1].getName())
            mtd.remove(corrections_result[2].getName())
            mtd.remove(fit_result[1].getName())

        return vesuvio_output

    def _prefit(self, sample_data, index, masses, profiles):
        return self._fit_helper(InputWorkspace=sample_data,
                                WorkspaceIndex=index,
                                Masses=masses,
                                MassProfiles=profiles,
                                OutputWorkspace="__prefit",
                                FitParameters=self._fit_namer.prefit_parameters_name,
                                StoreInADS=False)

    def _corrections(self, sample_data, container_data, index, masses, profiles, prefit_parameters, verbose_output):
        correction_args = self._corrections_arguments(container_data, prefit_parameters, verbose_output)
        return self._corrections_helper(InputWorkspace=sample_data,
                                        WorkspaceIndex=index,
                                        Masses=masses,
                                        MassProfiles=profiles,
                                        MassIndexToSymbolMap=self._mass_profile_collection.index_to_symbol_map,
                                        OutputWorkspace=self._fit_namer.corrected_data_name,
                                        LinearFitResult=self._fit_namer.corrections_parameters_name,
                                        **correction_args)

    def _corrections_arguments(self, container_data, prefit_parameters, verbose_output):
        correction_args = {'FitParameters' : prefit_parameters}

        if container_data is not None:
            correction_args['ContainerWorkspace'] = container_data
        if verbose_output:
            correction_args['CorrectionWorkspaces'] = self._fit_namer.corrections_group_name
            correction_args['CorrectedWorkspaces'] = self._fit_namer.corrected_group_name

        correction_args.update(self._ms_corrections_args)
        return correction_args

    def _final_fit(self, corrected_data, index, masses, profiles):
        fit_result = self._fit_helper(InputWorkspace=corrected_data,
                                      WorkspaceIndex=index,
                                      Masses=masses,
                                      MassProfiles=profiles,
                                      OutputWorkspace=self._fit_namer.fit_output_name,
                                      FitParameters=self._fit_namer.fit_parameters_name)
        DeleteWorkspace(corrected_data)
        return fit_result

# ------------------------------------------------------------------------------------------------------

class VesuvioMSHelper(object):
    """
    A helper class for storing and manipulating the multiple scattering paramaters of
    the Vesuvio TOF Fit Routine.

    Attributes:
        _beam_radius        The radius of the neutron beam
        _sample_height      The height of the sample
        _sample_width       The width of the sample
        _sample_depth       The depth of the sample
        _sample_density     The density of the sample
        _seed               The seed to use in generating random
                            scattering events
        _num_scatters       The number of times a neutron will be scattered
        _num_runs           The number of runs
        _num_events         The number of scattering events to simulate
        _smooth_neighbours
    """

    def __init__(self, BeamRadius=2.5, SampleHeight=5.0, SampleWidth=5.0, SampleDepth=5.0,
                 SampleDensity=1.0, Seed=123456789, NumScatters=3, NumRuns=10, NumEvents=50000,
                 SmoothNeighbours=3):
        self._beam_radius = BeamRadius
        self._sample_height = SampleHeight
        self._sample_width = SampleWidth
        self._sample_depth = SampleDepth
        self._sample_density = SampleDensity
        self._seed = Seed
        self._num_scatters = NumScatters
        self._num_runs = NumRuns
        self._num_events = NumEvents
        self._smooth_neighbours = SmoothNeighbours
        # Setup hydrogen constraints
        def parser(constraint):
            return self._parse_hydrogen_constraint(constraint)
        self._hydrogen_constraints = VesuvioConstraints("HydrogenConstraints", parser)

    def add_hydrogen_constraints(self, constraints):
        self._hydrogen_constraints.extend(constraints)

    def _parse_hydrogen_constraint(self, constraint):
        symbol = constraint.pop("symbol", None)

        if symbol is None:
            raise RuntimeError("Invalid hydrogen constraint: " +
                               str(constraint) +
                               " - No symbol provided")
        return {symbol: constraint}

    def to_dict(self):
        return {"BeamRadius": self._beam_radius,
                "SampleHeight": self._sample_height,
                "SampleWidth": self._sample_width,
                "SampleDepth": self._sample_depth,
                "SampleDensity": self._sample_density,
                "Seed": self._seed,
                "NumScatters": self._num_scatters,
                "NumRuns": self._num_runs,
                "NumEvents": self._num_events,
                "SmoothNeighbours": self._smooth_neighbours,
                "HydrogenConstraints": self._hydrogen_constraints.to_dict()}


# -----------------------------------------------------------------------------------------


class VesuvioTOFFitHelper(object):
    """
    A helper class for executing a VesuvioTOFFit.

    Attributes:
        _background              The background to use in the fit
        _intensity_constraints   The intensity constraints to use in the fit
        _ties                    The ties to use in the fit
        _max_iterations          The max number of iterations in which to attempt to find
                                 a peak using the minimizer
        _minimizer               The minimizer to use in the fit
    """
    def __init__(self, background, intensity_constraints, ties, max_iterations, minimizer):
        self._background = background
        self._intensity_constraints = intensity_constraints
        self._ties = ties
        self._max_iterations = max_iterations
        self._minimizer = minimizer

    def __call__(self, **fit_args):
        return VesuvioTOFFit(Background=self._background,
                             IntensityConstraints=self._intensity_constraints,
                             Ties=self._ties,
                             MaxIterations=self._max_iterations,
                             Minimizer=self._minimizer,
                             **fit_args)


# -----------------------------------------------------------------------------------------


class VesuvioCorrectionsHelper(object):
    """
    A helper class for executing VesuvioCorrections.

    Attributes:
        _gamma_correct          Boolean specifying whether to calculate gamma
                                background corrections
        _multiple_scattering    Boolean specifying whether to calculate multiple
                                scattering corrections
        _gamma_background_scale The value to scale the gamma corrections by
        _container_scale        The value to scale the container corrections by
        _intensity_constraints  The intensity constraints to use in the corrections
                                calculation
    """
    def __init__(self, gamma_correct, multiple_scattering, gamma_background_scale,
                 container_scale, intensity_constraints):
        self._gamma_correct = gamma_correct
        self._multiple_scattering = multiple_scattering
        self._gamma_background_scale = gamma_background_scale
        self._container_scale = container_scale
        self._intensity_constraints = intensity_constraints

    def __call__(self, **correction_args):
        return VesuvioCorrections(GammaBackground=self._gamma_correct,
                                  IntensityConstraints=self._intensity_constraints,
                                  MultipleScattering=self._multiple_scattering,
                                  GammaBackgroundScale=self._gamma_background_scale,
                                  ContainerScale=self._container_scale,
                                  **correction_args)


# -----------------------------------------------------------------------------------------


class VesuvioConstraints(object):
    """
    A class for parsing and storing a set of constraints for the Vesuvio Fit Routine

    Attributes:
        _name           The name of this set of constraints
        _parser         The parser to be used
        _constraints    The set of parsed constraints
    """
    def __init__(self, name, parser):
        self._name = name
        self._parser = parser
        self._constraints = dict()

    def __iter__(self):
        return self._constraints.__iter__()

    def __contains__(self, key):
        return self._constraints.__contains__(key)

    def add(self, key, constraint):
        self._constraints[key] = constraint

    def extend(self, constraints):
        try:
            if not isinstance(constraints, dict):
                for constraint in constraints:
                    self._constraints.update(self._parser(constraint))
            else:
                self._constraints.update(self._parser(constraints))
        except AttributeError:
            raise RuntimeError(self._name + ": Constraints are incorrectly formatted.")

    def to_dict(self):
        return dict(self._constraints)


# -----------------------------------------------------------------------------------------

class MassProfile(object):

    def __init__(self, symbol, mass, function, width, **parameters):
        self.symbol = symbol
        self.mass = mass
        self.width = width
        self._function = function
        self._parameters = parameters

    @property
    def function(self):
        return _create_function_str(self._function, self._parameters)

    @property
    def parameters(self):
        return {'value' : self._mass, 'width' : self._width}.update(self._parameters)

    @parameters.setter
    def parameters(self, values):
        self._mass = values.pop('value', self._mass)

        if isinstance(self._width, list):
            self._width[1] = values.pop('width', self._width)
        else:
            self._width = values.pop('width', self._width)

        self._parameters = values

    def copy(self):
        return MassProfile(self.symbol, self.mass, self._function, self.width, **self._parameters.copy())

# -----------------------------------------------------------------------------------------

class MassProfileCollection(object):

    def __init__(self, profiles):
        self._profiles = profiles

    @property
    def functions(self):
        return [profile.function for profile in self._profiles]

    @property
    def masses(self):
        return [profile.mass for profile in self._profiles]

    def filter(self, profile_filter):
        return MassProfileCollection(filter(profile_filter, self._profiles))

    def set_parameters(self, parameters, profile_filter=None):
        if profile_filter is None:
            profiles = self._profiles
        else:
            profiles = filter(profile_filter, self._profiles)

        for profile, parameters in zip(profiles, parameters):
            profile.parameters = parameters

    def copy(self):
        return MassProfileCollection([profile.copy() for profile in self._profiles])

    def __iter__(self):
        return self._profiles

# -----------------------------------------------------------------------------------------

class MassProfileCollection2D(object):

    def __init__(self, *collections, index_to_symbol_map=None):
        self._collections = list(collections)

        if index_to_symbol_map is None:
            self._index_to_symbol_map = { index : profile.symbol for index, profile in
                                          enumerate(self._collections[0]) if profile.symbol is not None }
        else:
            self._index_to_symbol_map = index_to_symbol_map

    @property
    def masses(self):
        return self._collections[0].masses

    @property
    def index_to_symbol_map(self):
        return self._index_to_symbol_map

    def functions(self, index):
        return self._collections[index].functions

    def filter(self, profile_filter):
        filtered_profiles = [collection.filter(profile_filter) for collection in self._collections]
        return MassProfileCollection2D(filtered_profiles, self._index_to_symbol_map)

    def add_collection(self, collection):
        self._collections.append(collection)

    def update_profiles(self, parameters, profile_filter=None):
        collection_number = len(self._collections)

        for index, collection_parameters in enumerate(parameters):
            if index >= collection_number:
                self.add_collection(self._collections[0].copy())
            self._collections[index].set_parameters(collection_parameters, profile_filter)

# -----------------------------------------------------------------------------------------


class VesuvioFitNamer(object):

    def __init__(self, vesuvio_input, fit_mode):
        self._sample_runs = str(vesuvio_input.sample_runs)
        self._spectra = vesuvio_input.spectra
        self._fit_mode = vesuvio_input.fit_mode
        self._index_to_spectrum = lambda index : vesuvio_input.sample_data.getSpectrum(index)
        self._iteration = 0
        self._index = 0

        if self._fit_mode == "bank":
            self._suffix_prefix = "_" + self._spectra + "_bank_"
            self._index_to_string = lambda index : str(index + 1)
        else:
            self._suffix_prefix = "_spectrum_"
            self._index_to_string = lambda index : str(self._index_to_spectrum(index))

        self._iteration_string = ""
        self._index_string = ""
        self._suffix = ""

    @property
    def suffix(self):
        if self._suffix == "":
            self._suffix = self._suffix_prefix + self._index_string + self._iteration_string
        return self._suffix

    def set_iteration(self, iteration):
        if iteration is not None:
            self._iteration_string = "_iteration_" + str(iteration)
            self._iteration = iteration
        else:
            self._iteration_string = ""
        self._suffix = ""

    def set_index(self, index):
        self._index_string = self._index_to_string(index)
        self._index = index
        self._suffix = ""

    @property
    def prefit_parameters_name(self):
        return self._sample_runs + "_params_pre_correction" + self.suffix

    @property
    def corrections_parameters_name(self):
        return self._sample_runs + "_correction_fit_scale" + self.suffix

    @property
    def corrected_data_name(self):
        return self._sample_runs + "_tof_corrected" + self.suffix

    @property
    def fit_output_name(self):
        return self._sample_runs + "_data" + self.suffix

    @property
    def fit_parameters_name(self):
        return self._sample_runs + "_params" + self.suffix

    @property
    def prefit_parameters_correction_name(self):
        return self._sample_runs + "_params_pre_correction_iteration_" + str(self._iteration)

    @property
    def fit_parameters_correction_name(self):
        return self._sample_runs + "_params_iteration_" + str(self._iteration)

    @property
    def fit_correction_name(self):
        return self._sample_runs + "_correction_fit_scale_iteration_" + str(self._iteration)

    @property
    def corrections_group_name(self):
        return self._sample_runs + "_correction" + self.suffix

    @property
    def corrected_group_name(self):
        return self._sample_runs + "_corrected" + self.suffix

# -----------------------------------------------------------------------------------------

class VesuvioTOFFitOutput(object):

    def __init__(self):
        self._prefit_parameters = []
        self._correction_parameters = []
        self._fit_parameters = []
        self._fit_output_workspaces = []
        self._correction_groups = []
        self._corrected_groups = []
        self._chi2_values = []

    @property
    def prefit_parameters_workspace(self):
        return _merge_table_workspaces(self._prefit_parameters)

    @property
    def correction_parameters_workspace(self):
        return _merge_table_workspaces(self._correction_parameters)

    @property
    def fit_parameters_workspace(self):
        return _merge_table_workspaces(self._fit_parameters)

    @property
    def fit_output_workspaces(self):
        return self._fit_output_workspaces

    @property
    def correction_workspaces(self):
        return _conjoin_groups(self._correction_groups)

    @property
    def corrected_workspaces(self):
        return _conjoin_groups(self._corrected_groups)

    @property
    def chi2_values(self):
        return np.asarray(self._chi2_values)

    def add_prefit_parameters_workspace(self, workspace):
        self._prefit_parameters.append(workspace)

    def add_correction_parameters_workspace(self, workspace):
        self._correction_parameters.append(workspace)

    def add_fit_parameters_workspace(self, workspace):
        self._fit_parameters.append(workspace)

    def add_fit_output_workspace(self, workspace):
        self._fit_output_workspaces.append(workspace)

    def add_corrections_workspaces(self, workspaces):
        self._correction_groups.append(workspaces)

    def add_corrected_workspaces(self, workspaces):
        self._corrected_groups.append(workspaces)

    def add_chi2_value(self, value):
        self._chi2_values.append(value)

# --------------------------------------------------------------------------------
# Private Functions
# --------------------------------------------------------------------------------

def _mass_profile_generator(material_builder):
    def generator(mass_input):
        return _create_mass_profile(material_builder, mass_input)
    return generator


def _create_mass_profile(material_builder, mass_input):
    mass_value = _extract_mass_value(material_builder, mass_input)
    symbol = mass_input.pop('symbol', None)
    mass_function = _extract_mass_function(mass_input)
    width = _extract_mass_width(mass_input)
    return MassProfile(mass_value, symbol, mass_function, width, **mass_input)


def _extract_mass_function(mass_input):
    mass_function = mass_input.pop('function', None)

    if mass_function is None:
        raise RuntimeError('Invalid mass specified - ' + str(mass_input)
                           + " - no function was given.")
    return mass_function


def _extract_mass_width(mass_input):
    mass_width = mass_input.pop('width', None)

    if mass_width is None:
        raise RuntimeError('Invalid mass specified - ' + str(mass_input)
                           + " - no width was given.")
    return mass_width


def _extract_mass_value(material_builder, mass_input):
    mass_value = mass_input.pop('value', None)

    if mass_value is None:
        symbol = mass_input.get('symbol', None)

        if symbol is None:
            raise RuntimeError('Invalid mass specified - ' + str(mass_input)
                               + " - either 'value' or 'symbol' must be given.")

        try:
            mass_value = material_builder.setFormula(symbol).build().relativeMolecularMass()
        except BaseException as exc:
            raise RuntimeError('Error when parsing mass - ' + str(mass_input) + ": "
                               + "\n" + str(exc))
    return mass_value


def _extract_parameters_from_workspace(workspace):
    parameter_names, profile_indices = _extract_parameter_names_from_workspace(workspace)
    profile_number = max(profile_indices)
    parameters = []

    for spectrum in range(workspace.blocksize()):
        parameters.append([])
        parameters[spectrum].append([] * profile_number)

        for index, parameter in enumerate(parameters):
            parameters[spectrum][profile_indices[index]][parameter] = workspace.dataY(index)[spectrum]
    return parameters


def _extract_parameter_names_from_workspace(workspace):
    function_regex = re.compile("f([0-9]+).([A-z0-9_]+)")
    parameter_labels = workspace.getAxis(1).extractValues()
    profile_indices = []
    parameter_names = []

    for index, parameter in enumerate(parameter_labels):
        if parameter != "Cost function value":
            parameter_re = function_regex.match(parameter)
            profile_indices.append(int(parameter_re.group(1)))
            parameter_names.append(parameter_re.group(2).lower())

    return parameter_names, profile_indices


def _create_background_str(background_flags):
    """
    Create a string suitable for the algorithms out of the background flags
    :param background_flags: A dict for the background (can be None)
    :return: A string to pass to the algorithm
    """
    if background_flags:
        return _create_function_str(background_flags.pop("function"), background_flags)
    return ""


def _create_function_str(function, parameters):
    parameter_string = ",".join(["{0}={1}".format(key, value) for key, value in parameters.items()])
    return "function=" + function + "," + parameter_string


def _create_intensity_constraint_str(intensity_constraints):
    """
    Create a string suitable for the algorithms out of the intensity constraint flags
    :param intensity_constraints: A list of lists for the constraints (can be None)
    :return: A string to pass to the algorithm
    """
    if intensity_constraints:
        if not isinstance(intensity_constraints[0], list):
            intensity_constraints = [intensity_constraints]
        # Make each element a string and then join them together
        intensity_constraints = [str(c) for c in intensity_constraints]
        intensity_constraints_str = ";".join(intensity_constraints)
    else:
        intensity_constraints_str = ""

    return intensity_constraints_str


def _create_user_defined_ties_str(masses):
    """
    Creates the internal ties for each mass profile as defined by the user to be used when fitting the data
    @param masses   :: The mass profiles for the data which contain the the ties
    @return         :: A string to be passed as the Ties input to fitting
    """
    user_defined_ties = []
    for index, mass in enumerate(masses):
        if 'ties' in mass:
            ties = mass['ties'].split(',')
            function_identifier = 'f' + str(index) + '.'
            for t in ties:
                tie_str = function_identifier + t
                equal_pos = tie_str.index('=') + 1
                tie_str = tie_str[:equal_pos] + function_identifier + tie_str[equal_pos:]
                user_defined_ties.append(tie_str)
    user_defined_ties = ','.join(user_defined_ties)
    return user_defined_ties


def _merge_table_workspaces(table_workspaces):
    merged = _create_parameter_workspace(len(table_workspaces), table_workspaces[0])

    for index, parameter_workspace in enumerate(table_workspaces[1:], 1):
        _read_table_into_workspace(merged, parameter_workspace, index)
    return merged


def _create_parameter_workspace(num_spec, param_table):
    num_params = param_table.rowCount()
    param_workspace = WorkspaceFactory.Instance().create("Workspace2D",
                                                         num_params, num_spec,
                                                         num_spec)
    x_axis = TextAxis.create(num_spec)
    param_workspace.replaceAxis(0, x_axis)

    y_axis = TextAxis.create(num_params)
    for idx, parameter_name in enumerate(param_table.column('Name')):
        y_axis.setLabel(idx, parameter_name)
    param_workspace.replaceAxis(1, y_axis)
    return param_workspace


def _read_table_into_workspace(workspace, table_workspace, spectrum):
    for idx in range(table_workspace.rowCount()):
        workspace.dataX(idx)[spectrum] = spectrum
        workspace.dataY(idx)[spectrum] = table_workspace.column('Value')[idx]
        workspace.dataE(idx)[spectrum] = table_workspace.column('Error')[idx]


def _conjoin_groups(workspace_groups):
    conjoined_workspaces = workspace_groups[0]

    for workspace_group in workspace_groups[1:]:
        conjoined_workspaces = [ConjoinWorkspaces(InputWorkspace1=conjoined, InputWorkspace2=workspace,
                                                  OutputWorkspace="", StoreInADS=False)
                                for conjoined, workspace in zip(conjoined_workspaces, workspace_group)]
    return conjoined_workspaces


def _update_output(vesuvio_output, prefit_result, corrections_result, fit_result):
    vesuvio_output.add_fit_output_workspace(fit_result[0])
    vesuvio_output.add_chi2_value(fit_result[-1])
    vesuvio_output.add_prefit_parameters_workspace(prefit_result[1])
    vesuvio_output.add_correction_parameters_workspace(corrections_result[2])
    vesuvio_output.add_fit_parameters_workspace(fit_result[1])
    vesuvio_output.add_corrections_workspaces(list(corrections_result[0]))
    vesuvio_output.add_corrected_workspaces(list(corrections_result[1]))


def _change_in_cost_function(previous_output, current_output):
    return np.abs(np.max(previous_output.chi2_values - current_output.chi2_values))


def _add_fit_output_to_ads(vesuvio_output, sample_runs, iteration):
    if vesuvio_output.fit_output_workspaces:
        return GroupWorkspaces(InputWorkspaces=[workspace.getName() for workspace
                                                in vesuvio_output.fit_output_workspaces],
                               OutputWorkspace=sample_runs + "_iteration_" + str(iteration) + "_data")
    return None


def _add_parameters_to_ads(vesuvio_output, sample_runs, iteration):
    params_pre_corr_name = sample_runs + "_params_pre_correction_iteration_" + str(iteration)
    params_corr_name = sample_runs + "_correction_fit_scale_iteration_" + str(iteration)
    params_name = sample_runs + "_params_iteration_" + str(iteration)
    mtd.addOrReplace(params_pre_corr_name, vesuvio_output.prefit_parameters_workspace)
    mtd.addOrReplace(params_corr_name, vesuvio_output.correction_parameters_workspace)
    mtd.addOrReplace(params_name, vesuvio_output.fit_parameters_workspace)


def _group_corrections(vesuvio_output, sample_runs, iteration):
    prefix = sample_runs + "_iteration_" + str(iteration)
    corrections = _add_corrections_to_ads(vesuvio_output.correction_workspaces, prefix + "_correction_")
    corrected = _add_corrections_to_ads(vesuvio_output.corrected_workspaces, prefix + "_corrected_")
    workspaces = itertools.chain(corrections, corrected)

    if workspaces:
        return GroupWorkspaces(InputWorkspaces=[workspace.getName() for workspace in workspaces],
                               OutputWorkspace=prefix)
    return None


def _add_corrections_to_ads(corrections_group, prefix):
    corrections_names = []

    for correction_workspace in corrections_group:
        name = prefix + correction_workspace.rsplit('_', 1)[1]
        mtd.addOrReplace(name, correction_workspace)
        corrections_names.append(name)
    return corrections_names


def ignore_hydrogen_filter(profile):
    return profile.symbol is None or profile.symbol != 'H'
