class FunctionalConfig(object):
    """
    All pre-processing options required to run a tomographic reconstruction
    """

    DEFAULT_TOOL = 'tomopy'
    DEFAULT_ALGORITHM = 'gridrec'

    def __init__(self):
        """
        Builds a default post-processing configuration with a sensible choice of parameters

        find_cor: Currently a boolean, TODO will be an int so that we can use different methods

        verbosity: Default 2, existing levels:
            0 - Silent, no output at all (not recommended)
            1 - Low verbosity, will output each step that is being performed
            2 - Normal verbosity, will output each step and execution time
            3 - High verbosity, will output the step name, execution time and memory usage before and after each step

        crash_on_failed_import: Default True, this option tells if the program should stop execution if an import
                                fails and a step cannot be executed:
            True - Raise an exception and stop execution immediately
            False - Note the failure to import but continue execution without applying the filter
        """
        self.input_dir = None
        self.input_dir_flat = None
        self.input_dir_dark = None
        self.output_dir = None
        self.cor = None
        self.find_cor = None
        self.verbosity = 3  # default 2
        self.crash_on_failed_import = True  # default True

        self.tool = self.DEFAULT_TOOL
        self.algorithm = self.DEFAULT_ALGORITHM
        self.num_iter = None
        self.regularization = None

    def __str__(self):
        return "Input dir:{0}\nFlat dir:{1}\nDark dir:{2}\nOutput dir:{3}\nCOR:{4}\nFind_COR:{5}\nTool:{6}\n" \
                "Algorithm:{7}\nNum iter:{8}\nRegularization:{9}".format(str(self.input_dir),
                                                                         str(self.input_dir_flat),
                                                                         str(self.input_dir_dark),
                                                                         str(self.output_dir), str(self.cor),
                                                                         str(self.find_cor), str(self.tool),
                                                                         str(self.algorithm), str(self.num_iter),
                                                                         str(self.regularization))
