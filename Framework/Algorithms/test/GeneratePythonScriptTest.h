#ifndef MANTID_ALGORITHMS_GENERATEPYTHONSCRIPTTEST_H_
#define MANTID_ALGORITHMS_GENERATEPYTHONSCRIPTTEST_H_

#include <cxxtest/TestSuite.h>

#include "MantidAlgorithms/GeneratePythonScript.h"
#include "MantidAlgorithms/CreateWorkspace.h"
#include "MantidAlgorithms/CropWorkspace.h"
#include "MantidAlgorithms/Power.h"
#include "MantidAPI/AlgorithmManager.h"
#include "MantidAPI/FrameworkManager.h"
#include "MantidAPI/MatrixWorkspace.h"
#include "MantidAPI/WorkspaceHistory.h"
#include "MantidKernel/make_unique.h"
#include "MantidKernel/Timer.h"
#include "MantidKernel/System.h"

#include <boost/regex.hpp>
#include <Poco/File.h>

#include <fstream>

using namespace Mantid;
using namespace Mantid::Algorithms;
using namespace Mantid::API;

class NonExistingAlgorithm : public Algorithm {

public:
  const std::string name() const override { return "NonExistingAlgorithm"; }
  /// Algorithm's version for identification overriding a virtual method
  int version() const override { return 1; }
  /// Algorithm's category for identification overriding a virtual method
  const std::string category() const override { return "Rubbish"; }
  /// Summary of algorithms purpose
  const std::string summary() const override {
    return "I do not exist, or do I?";
  }

  void init() override {
    declareProperty(
        Kernel::make_unique<WorkspaceProperty<API::MatrixWorkspace>>(
            "InputWorkspace", "", Kernel::Direction::Input),
        "A workspace with units of TOF");
    declareProperty(
        Kernel::make_unique<WorkspaceProperty<API::MatrixWorkspace>>(
            "OutputWorkspace", "", Kernel::Direction::Output),
        "The name to use for the output workspace");
    declareProperty("MissingProperty", "rubbish", Kernel::Direction::Input);
  };
  void exec() override{

  };
};

class GeneratePythonScriptTest : public CxxTest::TestSuite {
public:
  void test_Init() {
    GeneratePythonScript alg;
    TS_ASSERT_THROWS_NOTHING(alg.initialize())
    TS_ASSERT(alg.isInitialized())
  }

  void test_exec() {
    // Create test workspace
    std::string workspaceName = "testGeneratePython";
    create_test_workspace(workspaceName);

    std::string result[] = {
        "#####################################################################"
        "#",
        "#Python Script Generated by GeneratePythonScript Algorithm",
        "#####################################################################"
        "#",
        "NonExistingAlgorithm()", "CreateWorkspace(OutputWorkspace='"
                                  "testGeneratePython', DataX='1,2,3,5,6', "
                                  "DataY='7,9,16,4,3', DataE='2,3,4,2,1', "
                                  "WorkspaceTitle='Test Workspace')",
        "CropWorkspace(InputWorkspace='testGeneratePython', "
        "OutputWorkspace='testGeneratePython', XMin=2, XMax=5)",
        "Power(InputWorkspace='testGeneratePython', "
        "OutputWorkspace='testGeneratePython', Exponent=1.5)",
        ""};

    // Set up and execute the algorithm.
    GeneratePythonScript alg;
    TS_ASSERT_THROWS_NOTHING(alg.initialize());
    TS_ASSERT(alg.isInitialized());
    TS_ASSERT_THROWS_NOTHING(
        alg.setPropertyValue("InputWorkspace", workspaceName));
    TS_ASSERT_THROWS_NOTHING(
        alg.setPropertyValue("Filename", "GeneratePythonScriptTest.py"));
    TS_ASSERT_THROWS_NOTHING(alg.setPropertyValue("ScriptText", ""));
    TS_ASSERT_THROWS_NOTHING(alg.execute(););
    TS_ASSERT(alg.isExecuted());

    // Compare the contents of the file to the expected result line-by-line.
    std::string filename = alg.getProperty("Filename");
    std::ifstream file(filename.c_str(), std::ifstream::in);
    std::string scriptLine;
    int lineCount = 0;

    while (std::getline(file, scriptLine)) {
      TS_ASSERT_EQUALS(result[lineCount], scriptLine)
      lineCount++;
    }

    // Verify that if we set the content of ScriptText that it is set correctly.
    alg.setPropertyValue("ScriptText", result[5]);
    TS_ASSERT_EQUALS(alg.getPropertyValue("ScriptText"),
                     "CropWorkspace(InputWorkspace='testGeneratePython', "
                     "OutputWorkspace='testGeneratePython', XMin=2, XMax=5)");

    file.close();
    if (Poco::File(filename).exists())
      Poco::File(filename).remove();
  }

  void create_test_workspace(const std::string &wsName) {
    Mantid::Algorithms::CreateWorkspace creator;
    Mantid::Algorithms::CropWorkspace cropper;
    Mantid::Algorithms::Power powerer;

    // Set up and execute creation of the workspace
    creator.initialize();
    creator.setPropertyValue("OutputWorkspace", wsName);
    creator.setPropertyValue("DataX", "1,2,3,5,6");
    creator.setPropertyValue("DataY", "7,9,16,4,3");
    creator.setPropertyValue("DataE", "2,3,4,2,1");
    creator.setPropertyValue("WorkspaceTitle", "Test Workspace");
    creator.setRethrows(true);
    TS_ASSERT_THROWS_NOTHING(creator.execute());
    TS_ASSERT_EQUALS(creator.isExecuted(), true);

    // Set up and execute the cropping of the workspace
    cropper.initialize();
    cropper.setPropertyValue("InputWorkspace", wsName);
    cropper.setPropertyValue("OutputWorkspace", wsName);
    cropper.setPropertyValue("XMin", "2");
    cropper.setPropertyValue("XMax", "5");
    cropper.setRethrows(true);
    TS_ASSERT_THROWS_NOTHING(cropper.execute());
    TS_ASSERT_EQUALS(cropper.isExecuted(), true);

    // Set up and execute Power algorithm on the workspace
    powerer.initialize();
    powerer.setPropertyValue("InputWorkspace", wsName);
    powerer.setPropertyValue("OutputWorkspace", wsName);
    powerer.setPropertyValue("Exponent", "1.5");
    powerer.setRethrows(true);
    TS_ASSERT_THROWS_NOTHING(powerer.execute());
    TS_ASSERT_EQUALS(powerer.isExecuted(), true);

    // set up history for the algorithn which is presumably removed from Mantid
    auto ws = API::FrameworkManager::Instance().getWorkspace(wsName);
    API::WorkspaceHistory &history = ws->history();
    auto pAlg = Mantid::Kernel::make_unique<NonExistingAlgorithm>();
    pAlg->initialize();
    history.addHistory(boost::make_shared<AlgorithmHistory>(
        API::AlgorithmHistory(pAlg.get())));

    pAlg.reset(NULL);
  }
};

#endif /* MANTID_ALGORITHMS_GENERATEPYTHONSCRIPTTEST_H_ */
