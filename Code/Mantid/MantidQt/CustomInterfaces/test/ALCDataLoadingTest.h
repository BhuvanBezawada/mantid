#ifndef MANTID_CUSTOMINTERFACES_ALCDATALOADINGTEST_H_
#define MANTID_CUSTOMINTERFACES_ALCDATALOADINGTEST_H_

#include <cxxtest/TestSuite.h>
#include <gmock/gmock.h>

#include "MantidAPI/MatrixWorkspace.h"
#include "MantidAPI/FrameworkManager.h"

#include "MantidQtCustomInterfaces/Muon/IALCDataLoadingView.h"
#include "MantidQtCustomInterfaces/Muon/ALCDataLoadingPresenter.h"

using namespace MantidQt::CustomInterfaces;
using namespace testing;

class MockALCDataLoadingView : public IALCDataLoadingView
{
public:
  MOCK_METHOD0(initialize, void());
  MOCK_CONST_METHOD0(firstRun, std::string());
  MOCK_CONST_METHOD0(lastRun, std::string());
  MOCK_CONST_METHOD0(log, std::string());
  MOCK_METHOD1(displayData, void(MatrixWorkspace_const_sptr));
  MOCK_METHOD1(displayError, void(const std::string&));

  void requestLoading() { emit loadData(); }
};

class ALCDataLoadingTest : public CxxTest::TestSuite
{
  MockALCDataLoadingView* m_view;
  ALCDataLoadingPresenter* m_presenter;

public:
  // This pair of boilerplate methods prevent the suite being created statically
  // This means the constructor isn't called when running other tests
  static ALCDataLoadingTest *createSuite() { return new ALCDataLoadingTest(); }
  static void destroySuite( ALCDataLoadingTest *suite ) { delete suite; }

  ALCDataLoadingTest()
  {
    FrameworkManager::Instance(); // To make sure everything is initialized
  }

  void setUp()
  {
    m_view = new MockALCDataLoadingView();

    m_presenter = new ALCDataLoadingPresenter(m_view);
    m_presenter->initialize();
  }

  void tearDown()
  {
    delete m_view;
    delete m_presenter;
  }

  void test_basicLoading()
  {
    MatrixWorkspace_const_sptr loadedWs;

    EXPECT_CALL(*m_view, firstRun()).WillRepeatedly(Return("MUSR00015189.nxs"));
    EXPECT_CALL(*m_view, lastRun()).WillRepeatedly(Return("MUSR00015191.nxs"));
    EXPECT_CALL(*m_view, log()).WillRepeatedly(Return("sample_magn_field"));
    EXPECT_CALL(*m_view, displayData(_)).Times(1).WillOnce(SaveArg<0>(&loadedWs));

    m_view->requestLoading();

    TS_ASSERT(loadedWs);
    TS_ASSERT_EQUALS(loadedWs->getNumberHistograms(), 1);
    TS_ASSERT_EQUALS(loadedWs->blocksize(), 3);

    TS_ASSERT_DELTA(loadedWs->readX(0)[0], 1350, 1E-8);
    TS_ASSERT_DELTA(loadedWs->readX(0)[1], 1360, 1E-8);
    TS_ASSERT_DELTA(loadedWs->readX(0)[2], 1370, 1E-8);

    TS_ASSERT_DELTA(loadedWs->readY(0)[0], 0.150, 1E-3);
    TS_ASSERT_DELTA(loadedWs->readY(0)[1], 0.142, 1E-3);
    TS_ASSERT_DELTA(loadedWs->readY(0)[2], 0.128, 1E-3);
  }

  void test_loadingError()
  {
    // TODO: with algorithm being executed asynchronously, check that errors are caught propertly
  }

  void test_nonExistentFile()
  {
    EXPECT_CALL(*m_view, firstRun()).WillRepeatedly(Return("MUSR00015189.nxs"));
    EXPECT_CALL(*m_view, lastRun()).WillRepeatedly(Return("non-existent-file"));
    EXPECT_CALL(*m_view, log()).WillRepeatedly(Return("sample_magn_field"));
    EXPECT_CALL(*m_view, displayData(_)).Times(0);
    EXPECT_CALL(*m_view, displayError(_)).Times(1);

    m_view->requestLoading();
  }
};


#endif /* MANTID_CUSTOMINTERFACES_ALCDATALOADINGTEST_H_ */
