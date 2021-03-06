#pylint: disable=invalid-name
"""
    Script used to start the HFIR SANS reduction gui from Mantidplot
"""
from __future__ import (absolute_import, division, print_function)
from reduction_application import ReductionGUI

reducer = ReductionGUI(instrument_list=["BIOSANS", "GPSANS", "EQSANS"])
if reducer.setup_layout(load_last=True):
    reducer.show()
