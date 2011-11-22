"""
    This module defines a simple function-style API for running Mantid
    algorithms. Each algorithm within Mantid is mapped to a Python
    function of the same name with the parameters of the algorithm becoming
    arguments to the function.
    
    For example:
   
    The Rebin algorithm is mapped to this Python function:

        Rebin(InputWorkspace, OutputWorkspace, Params, PreserveEvents=None, Version=1)
        
    It returns the output workspace and this workspace has the same name as
    the variable it is assigned to, i.e.
    
       rebinned = Rebin(input, Params = '0.1,0.05,10')
       
    would call Rebin with the given parameters and create a workspace called 'rebinned'
    and assign it to the rebinned variable
    
"""
from kernel import Direction, DataItem, funcreturns
from api import framework_mgr, analysis_data_svc, IWorkspaceProperty

def version():
    return "simpleapi - memory-based version"

def set_properties(alg_object, *args, **kwargs):
    """
        Set all of the properties of the algorithm
        @param alg_object An initialised algorithm object
        @param *args Positional arguments
        @param **kwargs Keyword arguments  
    """
    prop_order = alg_object.mandatory_properties()
    # add the args to the kw list so everything can be set in a single way
    for (key, arg) in zip(prop_order[:len(args)], args):
        kwargs[key] = arg

    # Set the properties of the algorithm.
    for key in kwargs.keys():
        value = kwargs[key]
        alg_object.set_property(key, value)
        # Make sure we set the name of any In/Out properties as well
        # See if this can be done sensibly in WorkspaceProperty
        if isinstance(value, DataItem):
            alg_object.set_property_value(key, str(value))
        
def get_additional_args(lhs, algm_obj):
    """
        Return the extra arguments that are to be passed to the algorithm
        from the information in the lhs tuple. These are basically the names 
        of output workspaces.
        The algorithm properties are iterated over in the same order
        they were created within the wrapper and for each output
        workspace property an entry is added to the returned dictionary
        that contains {PropertyName:lhs_name}.
        
        @param lhs :: A 2-tuple that contains the number of variables supplied 
                      on the lhs of the function call and the names of these
                      variables
        @param algm_obj :: An initialised algorithm object
        @returns A dictionary mapping property names to the values
                 extracted from the lhs variables
    """
    ret_names = lhs[1]
    extra_args = {}

    output_props = [ algm_obj.get_property(p) for p in algm_obj.output_properties() ]
    nprops = len(output_props)
    i = 0
    while len(ret_names) > 0 and i < nprops:
        p = output_props[i]
        if isinstance(p,IWorkspaceProperty):
            extra_args[p.name] = ret_names[0]
            ret_names = ret_names[1:]
        i += 1
    return extra_args
    
def gather_returns(lhs, algm_obj):
    """
        Gather the return values and ensure they are in the
        correct order as defined by the output properties and
        return them as a tuple. If their is a single return
        value it is returned on its own
        
        @param lhs :: A 2-tuple that contains the number of variables supplied 
               on the lhs of the function call and the names of these
               variables
        @param algm_obj :: An executed algorithm object
    """
    # Gather the returns
    # The minor complication here is the workspace properties have their
    # values stored in the ADS and not within the property
    props = [ algm_obj.get_property(p) for p in algm_obj.output_properties() ]
    retvals = []
    for p in props:
        if isinstance(p, IWorkspaceProperty):
            retvals.append(analysis_data_svc[p.value_as_str])
        else:
            retvals.append(p.value)

    nvals = len(retvals)
    if nvals > 1:
        return tuple(retvals) # Create a tuple
    elif nvals == 1:
        return retvals[0]
    else:
        return None

def create_algorithm(algorithm, version, _algm_object):
    """
        Create a function that will set up and execute an algorithm.
        The help that will be displayed is that of the most recent version.
        @param algorithm: name of the algorithm
        @param _algm_object :: the created algorithm object.
    """
    
    def algorithm_wrapper(*args, **kwargs):
        """
            Note that if the Version parameter is passed, we will create
            the proper version of the algorithm without failing.
        """
        _version = version
        if "Version" in kwargs:
            _version = kwargs["Version"]
            del kwargs["Version"]
        algm = framework_mgr.create_algorithm(algorithm, _version)
        lhs = funcreturns.lhs_info()
        extra_args = get_additional_args(lhs, algm)
        kwargs.update(extra_args)
        set_properties(algm, *args, **kwargs)
        algm.execute()
        return gather_returns(lhs, algm)
        
    
    algorithm_wrapper.__name__ = algorithm
    
    # Construct the algorithm documentation
    algorithm_wrapper.__doc__ = _algm_object.doc_string()
    
    # Dark magic to get the correct function signature
    # Calling help(...) on the wrapper function will produce a function 
    # signature along the lines of AlgorithmName(*args, **kwargs).
    # We will replace the name "args" by the list of properties, and
    # the name "kwargs" by "Version=1".
    #   1 - Get the algorithm properties and build a string to list them,
    #       taking care of giving no default values to mandatory parameters
    #   2 - All output properties will be removed from the function
    #       argument list
    
    arg_list = []
    for p in _algm_object.mandatory_properties():
        prop = _algm_object.get_property(p)
        # Mandatory parameters are those for which the default value is not valid
        if len(str(prop.is_valid))>0:
            arg_list.append(p)
        else:
            # None is not quite accurate here, but we are reproducing the 
            # behavior found in the C++ code for SimpleAPI.
            arg_list.append("%s=None" % p)

    # Build the function argument string from the tokens we found 
    arg_str = ', '.join(arg_list)
    # Calling help(...) will put a * in front of the first parameter name, so we use \b
    signature = "\b%s" % arg_str
    # Getting the code object for the algorithm wrapper
    f = algorithm_wrapper.func_code
    # Creating a new code object nearly identical, but with the two variable names replaced
    # by the property list.
    c = f.__new__(f.__class__, f.co_argcount, f.co_nlocals, f.co_stacksize, f.co_flags, f.co_code, f.co_consts, f.co_names,\
       (signature, "\b\bVersion=%d" % version), f.co_filename, f.co_name, f.co_firstlineno, f.co_lnotab, f.co_freevars)
    # Replace the code object of the wrapper function
    algorithm_wrapper.func_code = c  
    
    globals()[algorithm] = algorithm_wrapper
    
    # Register aliases
    for alias in _algm_object.alias().strip().split(' '):
        alias = alias.strip()
        if len(alias)>0:
            globals()[alias] = algorithm_wrapper
    
def create_algorithm_dialog(algorithm, version, _algm_object):
    """
        Create a function that will set up and execute an algorithm dialog.
        The help that will be displayed is that of the most recent version.
        @param algorithm: name of the algorithm
        @param _algm_object :: the created algorithm object.
    """
    def algorithm_wrapper(*args, **kwargs):
        raise RuntimeError("Dialog functions not implemented yet")
        _version = version
        if "Version" in kwargs:
            _version = kwargs["Version"]
            del kwargs["Version"]
        for item in ["Message", "Enable", "Disable"]:
            if item not in kwargs:
                kwargs[item] = ""
            
        algm = framework_mgr.create_algorithm(algorithm, _version)
        algm.setPropertiesDialog(*args, **kwargs)
        algm.execute()
        return algm
    
    algorithm_wrapper.__name__ = "%sDialog" % algorithm
    algorithm_wrapper.__doc__ = "\n\n%s dialog" % algorithm

    # Dark magic to get the correct function signature
    #_algm_object = mtd.createUnmanagedAlgorithm(algorithm, version)
    arg_list = []
    for p in _algm_object.mandatory_properties():
        arg_list.append("%s=None" % p)
    arg_str = ', '.join(arg_list)
    signature = "\b%s" % arg_str
    f = algorithm_wrapper.func_code
    c = f.__new__(f.__class__, f.co_argcount, f.co_nlocals, f.co_stacksize, f.co_flags, f.co_code, f.co_consts, f.co_names,\
       (signature, "\b\bMessage=\"\", Enable=\"\", Disable=\"\", Version=%d" % version), \
       f.co_filename, f.co_name, f.co_firstlineno, f.co_lnotab, f.co_freevars)
    algorithm_wrapper.func_code = c  
    
    globals()["%sDialog" % algorithm] = algorithm_wrapper
    
    # Register aliases
    for alias in _algm_object.alias().strip().split(' '):
        alias = alias.strip()
        if len(alias)>0:
            globals()["%sDialog" % alias] = algorithm_wrapper

def Load(*args, **kwargs):
    """
    Load is a more flexible algorithm than other Mantid algorithms.
    It's aim is to discover the correct loading algorithm for a
    given file. This flexibility comes at the expense of knowing the
    properties out right before the file is specified.
    
    The argument list for the Load function has to be more flexible to
    allow this searching to occur. Two arguments must be specified:
    
      - Filename :: The name of the file,
      - OutputWorkspace :: The name of the workspace,
    
    either as the first two arguments in the list or as keywords. Any other
    properties that the Load algorithm has can be specified by keyword only.
    
    Some common keywords are:
     - SpectrumMin,
     - SpectrumMax,
     - SpectrumList,
     - EntryNumber
    
    Example:
      # Simple usage, ISIS NeXus file
      Load('INSTR00001000.nxs', 'run_ws')
      
      # ISIS NeXus with SpectrumMin and SpectrumMax = 1
      Load('INSTR00001000.nxs', 'run_ws', SpectrumMin=1,SpectrumMax=1)
      
      # SNS Event NeXus with precount on
      Load('INSTR_1000_event.nxs', 'event_ws', Precount=True)
      
      # A mix of keyword and non-keyword is also possible
      Load('event_ws', Filename='INSTR_1000_event.nxs',Precount=True)
    """
    # Small inner function to grab the mandatory arguments and translate possible
    # exceptions
    def get_argument_value(key, kwargs):
        try:
            value = kwargs[key]
            del kwargs[key]
            return value
        except KeyError:
            raise RuntimeError('%s argument not supplied to Load function' % str(key))
    
    if len(args) == 2:
        filename = args[0]
        wkspace = args[1]
    elif len(args) == 1:
        if 'Filename' in kwargs:
            wkspace = args[0]
            filename = get_argument_value('Filename', kwargs)
        elif 'OutputWorkspace' in kwargs:
            filename = args[0]
            wkspace = get_argument_value('OutputWorkspace', kwargs)
        else:
            raise RuntimeError('Cannot find "Filename" or "OutputWorkspace" in key word list. '
                               'Cannot use single positional argument.')
    elif len(args) == 0:
        filename = get_argument_value('Filename', kwargs)
        wkspace = get_argument_value('OutputWorkspace', kwargs)
    else:
        raise RuntimeError('Load() takes at most 2 positional arguments, %d found.' % len(args))
    
    # Create and execute
    algm = framework_mgr.create_algorithm('Load')
    algm.set_property('Filename', filename) # Must be set first
    algm.set_property('OutputWorkspace', wkspace)
    for key, value in kwargs.iteritems():
        try:
            algm.set_property(key, value)
        except RuntimeError:
            mtd.sendWarningMessage("You've passed a property (%s) to Load() that doesn't apply to this filetype."% key)
    algm.execute()
    return algm

def LoadDialog(*args, **kwargs):
    """Popup a dialog for the Load algorithm. More help on the Load function
    is available via help(Load).

    Additional arguments available here (as keyword only) are:
      - Enable :: A CSV list of properties to keep enabled in the dialog
      - Disable :: A CSV list of properties to keep enabled in the dialog
      - Message :: An optional message string
    """
    raise RuntimeError("Load Dialog function not implemented yet")
    arguments = {}
    filename = None
    wkspace = None
    if len(args) == 2:
        filename = args[0]
        wkspace = args[1]
    elif len(args) == 1:
        if 'Filename' in kwargs:
            filename = kwargs['Filename']
            wkspace = args[0]
        elif 'OutputWorkspace' in kwargs:
            wkspace = kwargs['OutputWorkspace']
            filename = args[0]
    arguments['Filename'] = filename
    arguments['OutputWorkspace'] = wkspace
    arguments.update(kwargs)
    if 'Enable' not in arguments: arguments['Enable']=''
    if 'Disable' not in arguments: arguments['Disable']=''
    if 'Message' not in arguments: arguments['Message']=''
    algm = framework_mgr.create_algorithm('Load')
    algm.setPropertiesDialog(**arguments)
    algm.execute()

def translate():
    """
        Loop through the algorithms and register a function call 
        for each of them
    """
    from api import algorithm_factory, algorithm_mgr
     
    algs = algorithm_factory.get_registered_algorithms(True)
    for name, versions in algs.iteritems():
        if name == "Load":
            continue
        # Create the algorithm object
        _algm_object = algorithm_mgr.create_unmanaged(name, max(versions))
        _algm_object.initialize()
        create_algorithm(name, max(versions), _algm_object)
        #create_algorithm_dialog(name, max(versions), _algm_object)
            
# Create the algorithm functions on import
translate()

