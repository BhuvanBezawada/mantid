#include "MantidKernel/InstrumentInfo.h"
#include "MantidKernel/FacilityInfo.h"
#include "MantidPythonInterface/kernel/StlExportDefinitions.h"

#include <boost/python/class.hpp>
#include <boost/python/copy_const_reference.hpp>
#include <boost/python/overloads.hpp>

using Mantid::Kernel::InstrumentInfo;
using namespace boost::python;

namespace {
// To support default arguments
#ifdef __clang__
#pragma clang diagnostic ignored "-Wunused-local-typedef"
#endif
BOOST_PYTHON_MEMBER_FUNCTION_OVERLOADS(liveListener_overloads, liveListener, 0,
                                       1)
BOOST_PYTHON_MEMBER_FUNCTION_OVERLOADS(liveDataAddress_overloads,
                                       liveDataAddress, 0, 1)
BOOST_PYTHON_MEMBER_FUNCTION_OVERLOADS(liveListenerInfo_overloads,
                                       liveListenerInfo, 0, 1)
#ifdef __clang__
#pragma clang diagnostic pop
#endif
}

void export_InstrumentInfo() {
  using namespace Mantid::PythonInterface;
  std_vector_exporter<InstrumentInfo>::wrap("std_vector_InstrumentInfo");

  class_<InstrumentInfo>("InstrumentInfo", no_init)
      .def("name", &InstrumentInfo::name, arg("self"),
           ""
           "Returns the full name of the instrument as defined in the "
           "Facilites.xml file")

      .def("shortName", &InstrumentInfo::shortName, arg("self"),
           "Returns the abbreviated name of the instrument as definined in the "
           "Facilites.xml file")

      .def("__str__", &InstrumentInfo::shortName, arg("self"),
           "Returns the abbreviated name of the instrument as definined in the "
           "Facilites.xml file")

      .def("zeroPadding", &InstrumentInfo::zeroPadding,
           (arg("self"), arg("runNumber")),
           "Returns zero padding for this instrument")

      .def("filePrefix", &InstrumentInfo::filePrefix,
           (arg("self"), arg("runNumber")),
           "Returns file prefix for this instrument")

      .def("delimiter", &InstrumentInfo::delimiter, arg("self"),
           "Returns the delimiter "
           "between the instrument "
           "name and the run number.")

      .def("techniques", &InstrumentInfo::techniques, arg("self"),
           return_value_policy<copy_const_reference>(),
           "Return list of techniques this instrument supports")

      .def("facility", &InstrumentInfo::facility, arg("self"),
           return_value_policy<copy_const_reference>(),
           "Returns the facility that contains this instrument.")

      .def("liveListener", &InstrumentInfo::liveListener,
           liveListener_overloads(
               args("self", "name"),
               "Returns the name of the specific LiveListener class that is "
               "used "
               "by the given connection name. If no name is provided, the "
               "default connection is used."))

      // Unclear why this is named "instdae", leaving in case legacy req'd
      .def("instdae", &InstrumentInfo::liveDataAddress, arg("self"),
           "Returns the host name and the port of the machine hosting DAE and "
           "providing port to connect to for a live data stream")

      .def("liveDataAddress", &InstrumentInfo::liveDataAddress,
           liveDataAddress_overloads(
               args("self", "name"),
               "Returns the Address string of a live data connection on this "
               "instrument. If no connection name is provided, the default "
               "connection is used."))

      .def("liveListenerInfo", &InstrumentInfo::liveListenerInfo,
           return_value_policy<copy_const_reference>(),
           liveListenerInfo_overloads(
               args("self", "name"), "Returns a LiveListenerInfo instance for"))

      .def("hasLiveListenerInfo", &InstrumentInfo::hasLiveListenerInfo,
           arg("self"),
           "Returns true if this instrument has at least one LiveListenerInfo")

      .def("liveListenerInfoList", &InstrumentInfo::liveListenerInfoList,
           return_value_policy<copy_const_reference>(), arg("self"),
           "Returns all available LiveListenerInfo instances as a vector")

      ;
}
