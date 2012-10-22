/*WIKI*
TODO: Enter a full wiki-markup description of your algorithm here. You can then use the Build/wiki_maker.py script to generate your full wiki page.
*WIKI*/

#include "MantidAlgorithms/QueryPulseTimes.h"
#include "MantidDataObjects/EventWorkspace.h"
#include "MantidKernel/ArrayProperty.h"
#include "MantidKernel/RebinParamsValidator.h"
#include "MantidKernel/VectorHelper.h"
#include "MantidKernel/Unit.h"
#include <boost/make_shared.hpp>
#include <boost/assign/list_of.hpp>
#include <algorithm>

using namespace Mantid::Kernel;
using namespace Mantid::API;

namespace Mantid
{
namespace Algorithms
{

  /**
  Helper method to transform a MantidVector containing absolute times in nanoseconds to relative times in seconds given an offset.
  */
  class ConvertToRelativeTime : public std::unary_function<const MantidVec::value_type&, MantidVec::value_type>
  {
  private:
    double m_offSet;
  public: 
     ConvertToRelativeTime(const DateAndTime& offSet) : m_offSet(static_cast<double>(offSet.totalNanoseconds())*1e-9){}
     MantidVec::value_type operator()(const MantidVec::value_type& absTNanoSec)
     {
       return (absTNanoSec * 1e-9) - m_offSet;
     }
  };

  // Register the algorithm into the AlgorithmFactory
  DECLARE_ALGORITHM(QueryPulseTimes)

  //----------------------------------------------------------------------------------------------
  /** Constructor
   */
  QueryPulseTimes::QueryPulseTimes()
  {
  }
    
  //----------------------------------------------------------------------------------------------
  /** Destructor
   */
  QueryPulseTimes::~QueryPulseTimes()
  {
  }
  

  //----------------------------------------------------------------------------------------------
  /// Algorithm's name for identification. @see Algorithm::name
  const std::string QueryPulseTimes::name() const { return "QueryPulseTimes";};
  
  /// Algorithm's version for identification. @see Algorithm::version
  int QueryPulseTimes::version() const { return 1;};
  
  /// Algorithm's category for identification. @see Algorithm::category
  const std::string QueryPulseTimes::category() const { return "General";}

  //----------------------------------------------------------------------------------------------
  /// Sets documentation strings for this algorithm
  void QueryPulseTimes::initDocs()
  {
    this->setWikiSummary("Bins events according to pulse time. Binning parameters are specified relative to the start of the run.");
    this->setOptionalMessage("Bins events according to pulse time. Binning parameters are specified relative to the start of the run.");
  }

  //----------------------------------------------------------------------------------------------
  /** Initialize the algorithm's properties.
  */
  void QueryPulseTimes::init()
  {
    declareProperty(new API::WorkspaceProperty<API::IEventWorkspace>("InputWorkspace","",Direction::Input), "An input workspace.");
    declareProperty(
      new ArrayProperty<double>("Params", boost::make_shared<RebinParamsValidator>()),
      "A comma separated list of first bin boundary, width, last bin boundary. Optionally\n"
      "this can be followed by a comma and more widths and last boundary pairs.\n"
      "Negative width values indicate logarithmic binning.");
    declareProperty(new API::WorkspaceProperty<API::MatrixWorkspace>("OutputWorkspace","",Direction::Output), "An output workspace.");
  }

  //----------------------------------------------------------------------------------------------
  /** Execute the algorithm.
  */
  void QueryPulseTimes::exec()
  {
    using Mantid::DataObjects::EventWorkspace;
    IEventWorkspace_sptr inWS = getProperty("InputWorkspace");
    if(!boost::dynamic_pointer_cast<EventWorkspace>(inWS))
    {
      throw std::invalid_argument("QueryPulseTimes requires an EventWorkspace as an input.");
    }

    MatrixWorkspace_sptr outputWS = getProperty("OutputWorkspace"); // TODO: MUST BE A HISTOGRAM WORKSPACE!

    // retrieve the properties
    const std::vector<double> inParams =getProperty("Params");
    std::vector<double> rebinningParams;

    // workspace independent determination of length
    const int histnumber = static_cast<int>(inWS->getNumberHistograms());
    
    const uint64_t nanoSecondsInASecond = static_cast<uint64_t>(1e9);
    const DateAndTime runStartTime = inWS->run().startTime();
    // The validator only passes parameters with size 1, or 3xn.  
    if (inParams.size() >= 3)
    {
      // Use the start of the run to offset the times provided by the user. pulse time of the events are absolute.
      const DateAndTime startTime = runStartTime + inParams[0] ;
      const DateAndTime endTime = runStartTime + inParams[2] ;
      const double tStep = inParams[1] * nanoSecondsInASecond;
      // Rebinning params in nanoseconds.
      rebinningParams.push_back(static_cast<double>(startTime.totalNanoseconds()));
      rebinningParams.push_back(tStep);
      rebinningParams.push_back(static_cast<double>(endTime.totalNanoseconds()));
    } 
    else if (inParams.size() == 1)
    {
      const uint64_t xmin = inWS->getPulseTimeMin().totalNanoseconds();
      const uint64_t xmax = inWS->getPulseTimeMax().totalNanoseconds();

      rebinningParams.push_back(static_cast<double>(xmin));
      rebinningParams.push_back(inParams[0] * nanoSecondsInASecond);
      rebinningParams.push_back(static_cast<double>(xmax));
    }

    //Initialize progress reporting.
    Progress prog(this,0.0,1.0, histnumber);
    
    MantidVecPtr XValues_new;
    // create new X axis, with absolute times in seconds.
    const int ntcnew = VectorHelper::createAxisFromRebinParams(rebinningParams, XValues_new.access());

    ConvertToRelativeTime transformToRelativeT(runStartTime);

    // Transform the output into relative times in seconds.
    MantidVec OutXValues_scaled(XValues_new->size());
    std::transform(XValues_new->begin(), XValues_new->end(), OutXValues_scaled.begin(), transformToRelativeT);

    outputWS = WorkspaceFactory::Instance().create("Workspace2D",histnumber,ntcnew,ntcnew-1);
    WorkspaceFactory::Instance().initializeFromParent(inWS, outputWS, true);

    //Go through all the histograms and set the data
    //PARALLEL_FOR2(inWS, outputWS)
    for (int i=0; i < histnumber; ++i)
    {
      //PARALLEL_START_INTERUPT_REGION

      const IEventList* el = inWS->getEventListPtr(i);
      MantidVec y_data, e_data;
      // The EventList takes care of histogramming.
      el->generateHistogramPulseTime(*XValues_new, y_data, e_data);

      //Set the X axis for each output histogram
      outputWS->setX(i, OutXValues_scaled);

      //Copy the data over.
      outputWS->dataY(i).assign(y_data.begin(), y_data.end());
      outputWS->dataE(i).assign(e_data.begin(), e_data.end());

      //Report progress
      prog.report(name());
      //PARALLEL_END_INTERUPT_REGION
    }
    //PARALLEL_CHECK_INTERUPT_REGION

    //Copy all the axes
    for (int i=1; i<inWS->axes(); i++)
    {
      outputWS->replaceAxis( i, inWS->getAxis(i)->clone(outputWS.get()) );
      outputWS->getAxis(i)->unit() = inWS->getAxis(i)->unit();
    }

    // X-unit is relative time since the start of the run.
    outputWS->getAxis(0)->unit() = boost::make_shared<Units::Time>();

    //Copy the units over too.
    for (int i=1; i < outputWS->axes(); ++i)
    {
      outputWS->getAxis(i)->unit() = inWS->getAxis(i)->unit();
    }
    outputWS->setYUnit(inWS->YUnit());
    outputWS->setYUnitLabel(inWS->YUnitLabel());

    // Assign it to the output workspace property
    setProperty("OutputWorkspace", outputWS);

    return;
  }

} // namespace Algorithms
} // namespace Mantid