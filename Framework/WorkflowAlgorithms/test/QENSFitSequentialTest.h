#ifndef MANTID_ALGORITHMS_QENSFITSEQUENTIALTEST_H_
#define MANTID_ALGORITHMS_QENSFITSEQUENTIALTEST_H_

#include <cxxtest/TestSuite.h>

#include "MantidAPI/Axis.h"
#include "MantidAPI/FrameworkManager.h"
#include "MantidAPI/WorkspaceFactory.h"
#include "MantidAPI/WorkspaceGroup.h"

#include "MantidDataHandling/Load.h"

#include "MantidWorkflowAlgorithms/QENSFitSequential.h"

#include "MantidDataObjects/Workspace2D.h"
#include "MantidKernel/TimeSeriesProperty.h"
#include "MantidTestHelpers/WorkspaceCreationHelper.h"

using Mantid::Algorithms::QENSFitSequential;
using namespace Mantid::API;
using namespace Mantid::DataObjects;
using Mantid::Kernel::make_cow;
using Mantid::HistogramData::BinEdges;
using Mantid::HistogramData::Counts;
using Mantid::HistogramData::CountStandardDeviations;

class QENSFitSequentialTest : public CxxTest::TestSuite {
public:
  // This pair of boilerplate methods prevent the suite being created statically
  // This means the constructor isn't called when running other tests
  static QENSFitSequentialTest *createSuite() {
    return new QENSFitSequentialTest();
  }
  static void destroySuite(QENSFitSequentialTest *suite) { delete suite; }

  QENSFitSequentialTest() { FrameworkManager::Instance(); }

  void test_set_valid_fit_function() {
    Mantid::Algorithms::QENSFitSequential alg;
    TS_ASSERT_THROWS_NOTHING(alg.initialize());
    TS_ASSERT_THROWS_NOTHING(alg.setProperty(
        "Function", "name=DeltaFunction,Height=1,Centre=0;name="
                    "Lorentzian,Amplitude=1,PeakCentre=0,FWHM=0;"));
  }

  void test_empty_function_is_not_allowed() {
    Mantid::Algorithms::QENSFitSequential alg;
    TS_ASSERT_THROWS_NOTHING(alg.initialize());

    TS_ASSERT_THROWS(alg.setPropertyValue("Function", ""),
                     std::invalid_argument);
  }

  void test_convolution_fit() {
    const int totalBins = 6;
    const int totalHist = 5;
    auto inputWorkspace = createReducedWorkspace(totalBins, totalHist);
    auto resolution =
        createResolutionWorkspace(totalBins, totalHist, "__QENS_Resolution");

    auto outputBaseName = runConvolutionFit(inputWorkspace, resolution);

    WorkspaceGroup_sptr groupWorkspace;

    TS_ASSERT_THROWS_NOTHING(
        AnalysisDataService::Instance().retrieveWS<ITableWorkspace>(
            outputBaseName + "_Parameters"));
    TS_ASSERT_THROWS_NOTHING(
        groupWorkspace =
            AnalysisDataService::Instance().retrieveWS<WorkspaceGroup>(
                outputBaseName + "_Workspaces"));
    TS_ASSERT_THROWS_NOTHING(
        AnalysisDataService::Instance().retrieveWS<MatrixWorkspace>(
            outputBaseName + "_Result"));

    TS_ASSERT_EQUALS(groupWorkspace->size(),
                     inputWorkspace->getNumberHistograms());

    AnalysisDataService::Instance().clear();
  }

private:
  std::string runConvolutionFit(MatrixWorkspace_sptr inputWorkspace,
                                MatrixWorkspace_sptr resolution) {
    Mantid::Algorithms::QENSFitSequential alg;
    TS_ASSERT_THROWS_NOTHING(alg.initialize());

    alg.setProperty("InputWorkspace", inputWorkspace);
    alg.setProperty("Function", convolutionFunction(resolution->getName()));
    alg.setProperty("StartX", 0.0);
    alg.setProperty("EndX", 3.0);
    alg.setProperty("SpecMin", 0);
    alg.setProperty("SpecMax", 5);
    alg.setProperty("ConvolveMembers", true);
    alg.setProperty("Minimizer", "Levenberg-Marquardt");
    alg.setProperty("MaxIterations", 500);
    alg.setProperty("OutputWorkspace",
                    "ReductionWs_conv_1LFixF_s0_to_5_Result");
    TS_ASSERT_THROWS_NOTHING(alg.execute());
    TS_ASSERT(alg.isExecuted());

    return "ReductionWs_conv_1LFixF_s0_to_5";
  }

  std::string convolutionFunction(const std::string &resolutionName) {
    return "name=LinearBackground,A0=0,A1=0,ties=(A0=0.000000,A1=0.0);("
           "composite=Convolution,FixResolution=true,NumDeriv=true;name="
           "Resolution,Workspace=" +
           resolutionName +
           ",WorkspaceIndex=0;((composite=ProductFunction,NumDeriv=false;name="
           "Lorentzian,Amplitude=1,PeakCentre=0,FWHM=0.0175)))";
  }

  MatrixWorkspace_sptr createReducedWorkspace(int xlen, int ylen) {
    auto ws = WorkspaceCreationHelper::create2DWorkspaceWithFullInstrument(
        xlen, xlen - 1, false, false, true, "testInst");
    ws->initialize(ylen, xlen, xlen - 1);
    addBinsAndCountsToWorkspace(ws, xlen, xlen - 1, 1.0, 3.0);

    ws->getAxis(0)->setUnit("DeltaE");

    for (int i = 0; i < xlen; i++)
      ws->setEFixed((i + 1), 0.50);

    auto &run = ws->mutableRun();
    auto timeSeries =
        new Mantid::Kernel::TimeSeriesProperty<std::string>("TestTimeSeries");
    timeSeries->addValue("2010-09-14T04:20:12", "0.02");
    run.addProperty(timeSeries);
    return ws;
  }

  MatrixWorkspace_sptr createResolutionWorkspace(std::size_t totalBins,
                                                 std::size_t totalHist,
                                                 const std::string &name) {
    auto resolution =
        createWorkspace<Workspace2D>(totalHist + 1, totalBins + 1, totalBins);
    addBinsAndCountsToWorkspace(resolution, totalBins + 1, totalBins, 0.0, 3.0);
    AnalysisDataService::Instance().addOrReplace(name, resolution);
    return resolution;
  }

  void addBinsAndCountsToWorkspace(Workspace2D_sptr workspace,
                                   std::size_t totalBinEdges,
                                   std::size_t totalCounts, double binValue,
                                   double countValue) {
    BinEdges x1(totalBinEdges, binValue);
    Counts y1(totalCounts, countValue);
    CountStandardDeviations e1(totalCounts, sqrt(countValue));

    int j = 0;
    std::generate(begin(x1), end(x1), [&j] { return 0.5 + 0.75 * j++; });

    for (auto i = 0u; i < workspace->getNumberHistograms(); ++i) {
      workspace->setBinEdges(i, x1);
      workspace->setCounts(i, y1);
      workspace->setCountStandardDeviations(i, e1);
    }
  }
};

#endif /* MANTID_ALGORITHMS_CONVOLUTIONFITSEQUENTIALTEST_H_ */