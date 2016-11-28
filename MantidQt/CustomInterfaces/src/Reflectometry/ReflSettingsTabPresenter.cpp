#include "MantidQtCustomInterfaces/Reflectometry/ReflSettingsTabPresenter.h"
#include "MantidQtCustomInterfaces/Reflectometry/IReflMainWindowPresenter.h"
#include "MantidQtCustomInterfaces/Reflectometry/ReflSettingsPresenter.h"
#include "MantidQtMantidWidgets/AlgorithmHintStrategy.h"
#include "MantidAPI/AlgorithmManager.h"
#include "MantidAPI/MatrixWorkspace.h"

namespace MantidQt {
namespace CustomInterfaces {

using namespace Mantid::API;
using namespace MantidQt::MantidWidgets;

/** Constructor
*
* @param view :: The view we are handling
*/
ReflSettingsTabPresenter::ReflSettingsTabPresenter(
    std::vector<IReflSettingsPresenter *> presenters)
    : m_mainPresenter(), m_settingsPresenters(presenters) {}

/** Destructor
*
*/
ReflSettingsTabPresenter::~ReflSettingsTabPresenter() {}

/** Accept a main presenter
*
* @param mainPresenter :: [input] The main presenter
*/
void ReflSettingsTabPresenter::acceptMainPresenter(
    IReflMainWindowPresenter *mainPresenter) {
  m_mainPresenter = mainPresenter;
}

/** Sets the current instrument name and changes accessibility status of
* the polarisation corrections option in the view accordingly
*
* @param instName :: [input] The name of the instrument to set to
*/
void ReflSettingsTabPresenter::setInstrumentName(const std::string &instName) {
  for (auto presenter : m_settingsPresenters)
    presenter->setInstrumentName(instName);
}

/** Returns global options for 'CreateTransmissionWorkspaceAuto'
*
* @param group :: The group from which to get the options
* @return :: Global options for 'CreateTransmissionWorkspaceAuto'
*/
std::string ReflSettingsTabPresenter::getTransmissionOptions(int group) const {

  return m_settingsPresenters.at(group)->getTransmissionOptions();
}

/** Returns global options for 'ReflectometryReductionOneAuto'
*
* @param group :: The group from which to get the options
* @return :: Global options for 'ReflectometryReductionOneAuto'
*/
std::string ReflSettingsTabPresenter::getReductionOptions(int group) const {

  return m_settingsPresenters.at(group)->getReductionOptions();
}

/** Returns global options for 'Stitch1DMany'
*
* @param group :: The group from which to get the options
* @return :: Global options for 'Stitch1DMany'
*/
std::string ReflSettingsTabPresenter::getStitchOptions(int group) const {

  return m_settingsPresenters.at(group)->getStitchOptions();
}
}
}