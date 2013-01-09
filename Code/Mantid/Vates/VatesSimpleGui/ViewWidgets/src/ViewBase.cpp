#include "MantidVatesSimpleGuiViewWidgets/ViewBase.h"

#include <pqActiveObjects.h>
#include <pqAnimationManager.h>
#include <pqAnimationScene.h>
#include <pqApplicationCore.h>
#include <pqDataRepresentation.h>
#include <pqObjectBuilder.h>
#include <pqPipelineSource.h>
#include <pqPipelineRepresentation.h>
#include <pqPVApplicationCore.h>
#include <pqRenderView.h>
#include <pqServer.h>
#include <pqServerManagerModel.h>
#include <vtkSMDoubleVectorProperty.h>
#include <vtkSMPropertyHelper.h>
#include <vtkSMPropertyIterator.h>
#include <vtkSMProxy.h>
#include <vtkSMSourceProxy.h>

#include <QHBoxLayout>
#include <QPointer>

namespace Mantid
{
namespace Vates
{
namespace SimpleGui
{

/**
 * Default constructor.
 * @param parent the parent widget for the view
 */
ViewBase::ViewBase(QWidget *parent) : QWidget(parent)
{
}

/**
 * This function creates a single standard ParaView view instance.
 * @param widget the UI widget to associate the view with
 * @return the created view
 */
pqRenderView* ViewBase::createRenderView(QWidget* widget, QString viewName)
{
  QHBoxLayout *hbox = new QHBoxLayout(widget);
  hbox->setMargin(0);

  if (viewName == QString(""))
  {
    viewName = pqRenderView::renderViewType();
  }

  // Create a new render view.
  pqObjectBuilder* builder = pqApplicationCore::instance()->getObjectBuilder();
  pqRenderView *view = qobject_cast<pqRenderView*>(\
        builder->createView(viewName,
                            pqActiveObjects::instance().activeServer()));
  pqActiveObjects::instance().setActiveView(view);

  // Place the widget for the render view in the frame provided.
  hbox->addWidget(view->getWidget());
  return view;
}

/**
 * This function removes all filters of a given name: i.e. Slice.
 * @param builder the ParaView object builder
 * @param name the class name of the filters to remove
 */
void ViewBase::destroyFilter(pqObjectBuilder *builder, const QString &name)
{
  pqServer *server = pqActiveObjects::instance().activeServer();
  pqServerManagerModel *smModel = pqApplicationCore::instance()->getServerManagerModel();
  QList<pqPipelineSource *> sources;
  QList<pqPipelineSource *>::Iterator source;
  sources = smModel->findItems<pqPipelineSource *>(server);
  for (source = sources.begin(); source != sources.end(); ++source)
  {
    const QString sourceName = (*source)->getSMName();
    if (sourceName.startsWith(name))
    {
      builder->destroy(*source);
    }
  }
}

/**
 * This function is responsible for setting the color scale range from the
 * full extent of the data.
 */
void ViewBase::onAutoScale()
{
  QPair <double, double> range = this->colorUpdater.autoScale(this->getRep());
  this->renderAll();
  emit this->dataRange(range.first, range.second);
}

/**
 * This function sets the requested color map on the data.
 * @param model the color map to use
 */
void ViewBase::onColorMapChange(const pqColorMapModel *model)
{
  this->colorUpdater.colorMapChange(this->getRep(), model);
  this->renderAll();
}

/**
 * This function sets the data color scale range to the requested bounds.
 * @param min the minimum bound for the color scale
 * @param max the maximum bound for the color scale
 */
void ViewBase::onColorScaleChange(double min, double max)
{
  this->colorUpdater.colorScaleChange(this->getRep(), min, max);
  this->renderAll();
}

/**
 * This function sets logarithmic color scaling on the data.
 * @param state flag to determine whether or not to use log color scaling
 */
void ViewBase::onLogScale(int state)
{
  this->colorUpdater.logScale(this->getRep(), state);
  this->renderAll();
}

/**
 * This function is used to correct post-accept visibility issues. Most
 * views won't need to do anything.
 */
void ViewBase::correctVisibility(pqPipelineBrowserWidget *pbw)
{
  UNUSED_ARG(pbw);
}

/**
 * This function checks a pqPipelineSource (either from a file or workspace)
 * to see if it is derived from a PeaksWorkspace.
 * @param src the pipeline source to check
 * @return true if the pipeline source is derived from PeaksWorkspace
 */
bool ViewBase::isPeaksWorkspace(pqPipelineSource *src)
{
  if (NULL == src)
  {
    return false;
  }
  QString wsType(vtkSMPropertyHelper(src->getProxy(),
                                     "WorkspaceTypeName", true).GetAsString());
  // This must be a Mantid rebinner filter if the property is empty.
  if (wsType.isEmpty())
  {
    wsType = src->getSMName();
  }
  return wsType.contains("PeaksWorkspace");
}

/**
 * This function retrieves the active pqPipelineRepresentation object according
 * to ParaView's ActiveObjects mechanism.
 * @return the currently active representation
 */
pqPipelineRepresentation *ViewBase::getPvActiveRep()
{
  pqDataRepresentation *drep = pqActiveObjects::instance().activeRepresentation();
  return qobject_cast<pqPipelineRepresentation *>(drep);
}

/**
 * This function creates a ParaView source from a given plugin name and
 * workspace name. This is used in the plugin mode of the simple interface.
 * @param pluginName name of the ParaView plugin
 * @param wsName name of the Mantid workspace to pass to the plugin
 */
void ViewBase::setPluginSource(QString pluginName, QString wsName)
{
  // Create the source from the plugin
  pqObjectBuilder* builder = pqApplicationCore::instance()->getObjectBuilder();
  pqServer *server = pqActiveObjects::instance().activeServer();
  pqPipelineSource *src = builder->createSource("sources", pluginName,
                                                server);
  vtkSMPropertyHelper(src->getProxy(),
                      "Mantid Workspace Name").Set(wsName.toStdString().c_str());

  // Update the source so that it retrieves the data from the Mantid workspace
  vtkSMSourceProxy *srcProxy = vtkSMSourceProxy::SafeDownCast(src->getProxy());
  srcProxy->UpdateVTKObjects();
  srcProxy->Modified();
  srcProxy->UpdatePipelineInformation();
  src->updatePipeline();
}

/**
 * This function retrieves the active pqPipelineSource object according to ParaView's
 * ActiveObjects mechanism.
 * @return the currently active source
 */
pqPipelineSource *ViewBase::getPvActiveSrc()
{
  return pqActiveObjects::instance().activeSource();
}

/**
 * This function sets the status for the view mode control buttons. This
 * implementation looks at the original source for a view. Views may override
 * this function to provide alternate checks.
 */
void ViewBase::checkView()
{
  if (this->isMDHistoWorkspace(this->origSrc))
  {
    emit this->setViewsStatus(true);
    emit this->setViewStatus(ModeControlWidget::SPLATTERPLOT, false);
  }
  else if (this->isPeaksWorkspace(this->origSrc))
  {
    emit this->setViewsStatus(false);
  }
  else
  {
    emit this->setViewsStatus(true);
  }
}

/**
 * This function sets the status for the view mode control buttons when the
 * view switches.
 */
void ViewBase::checkViewOnSwitch()
{
  if (this->isMDHistoWorkspace(this->origSrc))
  {
    emit this->setViewStatus(ModeControlWidget::SPLATTERPLOT, false);
  }
}

/**
 * This function is responsible for checking if a pipeline source has time
 * step information. If not, it will disable the animation controls. If the
 * pipeline source has time step information, the animation controls will be
 * enabled and the start, stop and number of time steps updated for the
 * animation scene. If the withUpdate flag is used (default off), then the
 * original pipeline source is updated with the number of "time" steps.
 * @param withUpdate update the original source with "time" step info
 */
void ViewBase::setTimeSteps(bool withUpdate)
{
  pqPipelineSource *src = this->getPvActiveSrc();
  unsigned int numSrcs = this->getNumSources();
  if (!withUpdate && this->isPeaksWorkspace(src))
  {
    if (1 == numSrcs)
    {
      emit this->setAnimationControlState(false);
      return;
    }
    if (2 <= numSrcs)
    {
      return;
    }
  }
  vtkSMSourceProxy *srcProxy1 = vtkSMSourceProxy::SafeDownCast(src->getProxy());
  srcProxy1->Modified();
  srcProxy1->UpdatePipelineInformation();
  vtkSMDoubleVectorProperty *tsv = vtkSMDoubleVectorProperty::SafeDownCast(\
                                     srcProxy1->GetProperty("TimestepValues"));
  this->handleTimeInfo(tsv, withUpdate);
}

/**
 * This function looks through the ParaView server manager model and finds
 * those pipeline sources whose server manager group name is "sources". It
 * returns the total count of those present;
 * @return the number of true pipeline sources
 */
unsigned int ViewBase::getNumSources()
{
  unsigned int count = 0;
  pqServer *server = pqActiveObjects::instance().activeServer();
  pqServerManagerModel *smModel = pqApplicationCore::instance()->getServerManagerModel();
  QList<pqPipelineSource *> sources;
  QList<pqPipelineSource *>::Iterator source;
  sources = smModel->findItems<pqPipelineSource *>(server);
  for (source = sources.begin(); source != sources.end(); ++source)
  {
    const QString srcProxyName = (*source)->getProxy()->GetXMLGroup();
    if (srcProxyName == QString("sources"))
    {
      count++;
    }
  }
  return count;
}

/**
 * This function takes the incoming property and determines the start "time",
 * end "time" and the number of "time" steps. It also enables/disables the
 * animation controls widget based on the number of "time" steps.
 * @param dvp the vector property containing the "time" information
 * @param doUpdate flag to update original source with "time" step info
 */
void ViewBase::handleTimeInfo(vtkSMDoubleVectorProperty *dvp, bool doUpdate)
{
  if (NULL == dvp)
  {
    // This is a normal filter and therefore has no timesteps.
    return;
  }
  const int numTimesteps = static_cast<int>(dvp->GetNumberOfElements());
  if (0 != numTimesteps)
  {
    if (doUpdate)
    {
      vtkSMSourceProxy *srcProxy = vtkSMSourceProxy::SafeDownCast(\
                                     this->origSrc->getProxy());
      vtkSMPropertyHelper(srcProxy, "TimestepValues").Set(dvp->GetElements(),
                                                          numTimesteps);
    }
    double tStart = dvp->GetElement(0);
    double tEnd = dvp->GetElement(dvp->GetNumberOfElements() - 1);
    emit this->setAnimationControlState(true);
    emit this->setAnimationControlInfo(tStart, tEnd, numTimesteps);
  }
  else
  {
    emit this->setAnimationControlState(false);
  }
}

/**
 * This function is lifted directly from ParaView. It allows the center of
 * rotation of the view to be placed at the center of the mesh associated
 * with the visualized data.
 */
void ViewBase::onResetCenterToData()
{
  pqRenderView *renderView = this->getPvActiveView();
  pqDataRepresentation* repr = pqActiveObjects::instance().activeRepresentation();
  if (!repr || !renderView)
  {
    //qDebug() << "Active source not shown in active view. Cannot set center.";
    return;
  }

  double bounds[6];
  if (repr->getDataBounds(bounds))
  {
    double center[3];
    center[0] = (bounds[1]+bounds[0])/2.0;
    center[1] = (bounds[3]+bounds[2])/2.0;
    center[2] = (bounds[5]+bounds[4])/2.0;
    renderView->setCenterOfRotation(center);
    renderView->render();
  }
}

/**
 * This function takes a given set of coordinates and resets the center of
 * rotation of the view to that given point.
 * @param x the x coordinate of the center point
 * @param y the y coordinate of the center point
 * @param z the z coordinate of the center point
 */
void ViewBase::onResetCenterToPoint(double x, double y, double z)
{
  pqRenderView *renderView = this->getPvActiveView();
  pqDataRepresentation* repr = pqActiveObjects::instance().activeRepresentation();
  if (!repr || !renderView)
  {
    //qDebug() << "Active source not shown in active view. Cannot set center.";
    return;
  }
  double center[3];
  center[0] = x;
  center[1] = y;
  center[2] = z;
  renderView->setCenterOfRotation(center);
  renderView->render();
}

/**
 * This function will handle axis scale updates. Most views will not do this,
 * so the default is to do nothing.
 */
void ViewBase::setAxisScales()
{
}

/**
 * This function is used to set the current state of the view between a
 * parallel projection and the normal projection.
 * @param state whether or not to use parallel projection
 */
void ViewBase::onParallelProjection(bool state)
{
  pqRenderView *cview = this->getPvActiveView();
  vtkSMProxy *proxy = cview->getProxy();
  vtkSMPropertyHelper(proxy, "CameraParallelProjection").Set(state);
  proxy->UpdateVTKObjects();
  cview->render();
}

/**
 * This function retrieves the active pqRenderView object according to
 * ParaView's ActiveObjects mechanism.
 * @return the currently active view
 */
pqRenderView *ViewBase::getPvActiveView()
{
  return qobject_cast<pqRenderView*>(pqActiveObjects::instance().activeView());
}

/**
 * This function checks the original pipeline object for the WorkspaceName
 * property. This will get an empty string if the simple interface is
 * launched in standalone mode.
 * @return the workspace name for the original pipeline object
 */
QString ViewBase::getWorkspaceName()
{
  pqServerManagerModel *smModel = pqApplicationCore::instance()->getServerManagerModel();
  pqPipelineSource *src = smModel->getItemAtIndex<pqPipelineSource *>(0);
  QString wsName(vtkSMPropertyHelper(src->getProxy(),
                                     "WorkspaceName",
                                     true).GetAsString());
  return wsName;
}

/**
 * This function gets a property iterator from the source proxy and iterates
 * over the properties, printing out the keys.
 * @param src pqPipelineSource to print properties from
 */
void ViewBase::printProxyProps(pqPipelineSource *src)
{
  std::cout << src->getSMName().toStdString() << " Properties:" << std::endl;
  vtkSMPropertyIterator *piter = src->getProxy()->NewPropertyIterator();
  while ( !piter->IsAtEnd() )
  {
    std::cout << piter->GetKey() << std::endl;
    piter->Next();
  }
}

/**
 * This function iterrogates the pqPipelineSource for the TimestepValues
 * property. It then checks to see if the number of timesteps is non-zero.
 * @param src pqPipelineSource to check for timesteps
 * @return true if pqPipelineSource has a non-zero number of timesteps
 */
bool ViewBase::srcHasTimeSteps(pqPipelineSource *src)
{
  vtkSMSourceProxy *srcProxy1 = vtkSMSourceProxy::SafeDownCast(src->getProxy());
  srcProxy1->Modified();
  srcProxy1->UpdatePipelineInformation();
  vtkSMDoubleVectorProperty *tsv = vtkSMDoubleVectorProperty::SafeDownCast(\
                                     srcProxy1->GetProperty("TimestepValues"));
  const unsigned int numTimesteps = tsv->GetNumberOfElements();
  return 0 < numTimesteps;
}

/**
 * This function retrieves the current timestep as determined by ParaView's
 * AnimationManager.
 * @return the current timestep from the animation scene
 */
double ViewBase::getCurrentTimeStep()
{
  pqAnimationManager* mgr = pqPVApplicationCore::instance()->animationManager();
  pqAnimationScene *scene = mgr->getActiveScene();
  return scene->getAnimationTime();
}

/**
 * This function will close view generated sub-windows. Most views will not
 * reimplement this function, so the default is to do nothing.
 */
void ViewBase::closeSubWindows()
{
}

/**
 * This function returns the representation appropriate for the request. It
 * checks the ParaView active representation first. If that can't be found, the
 * fallback is to check the original representation associated with the view.
 * @return the discovered representation
 */
pqPipelineRepresentation *ViewBase::getRep()
{
  pqPipelineRepresentation *rep = this->getPvActiveRep();
  if (NULL == rep)
  {
    rep = this->origRep;
  }
  return rep;
}

/**
 * This function checks if a pqPipelineSource is a MDHistoWorkspace.
 * @return true if the source is a MDHistoWorkspace
 */
bool ViewBase::isMDHistoWorkspace(pqPipelineSource *src)
{
  if (NULL == src)
  {
    return false;
  }
  QString wsType(vtkSMPropertyHelper(src->getProxy(),
                                     "WorkspaceTypeName", true).GetAsString());
  // This must be a Mantid rebinner filter if the property is empty.
  if (wsType.isEmpty())
  {
    wsType = src->getSMName();
  }
  return wsType.contains("MDHistoWorkspace");
}

/**
 * This function is where one specifies updates to the UI components for a
 * view.
 */
void ViewBase::updateUI()
{
}

/**
 * This function checks the current pipeline for a filter with the specified
 * name. The function works for generic filter names only.
 * @param name the name of the filter to search for
 * @return true if the filter is found
 */
bool ViewBase::hasFilter(const QString &name)
{
  pqServer *server = pqActiveObjects::instance().activeServer();
  pqServerManagerModel *smModel = pqApplicationCore::instance()->getServerManagerModel();
  QList<pqPipelineSource *> sources;
  QList<pqPipelineSource *>::Iterator source;
  sources = smModel->findItems<pqPipelineSource *>(server);
  for (source = sources.begin(); source != sources.end(); ++source)
  {
    const QString sourceName = (*source)->getSMName();
    if (sourceName.startsWith(name))
    {
      return true;
    }
  }
  return false;
}

} // namespace SimpleGui
} // namespace Vates
} // namespace Mantid
