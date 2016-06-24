#ifndef MUONFITPROPERTYBROWSER_H_
#define MUONFITPROPERTYBROWSER_H_

#include "MantidQtMantidWidgets/FitPropertyBrowser.h"
#include "MantidQtMantidWidgets/IMuonFitFunctionControl.h"

/* Forward declarations */

class QtTreePropertyBrowser;
class QtGroupPropertyManager;
class QtDoublePropertyManager;
class QtIntPropertyManager;
class QtBoolPropertyManager;
class QtStringPropertyManager;
class QtEnumPropertyManager;
class QtProperty;
class QtBrowserItem;
class QVBoxLayout;

namespace Mantid {
namespace API {
class IFitFunction;
class IPeakFunction;
class CompositeFunction;
}
}

namespace MantidQt {
namespace MantidWidgets {
class PropertyHandler;

class EXPORT_OPT_MANTIDQT_MANTIDWIDGETS MuonFitPropertyBrowser
    : public MantidQt::MantidWidgets::FitPropertyBrowser,
      public MantidQt::MantidWidgets::IMuonFitFunctionControl {
  Q_OBJECT

public:
  /// Constructor.
  MuonFitPropertyBrowser(QWidget *parent = NULL, QObject *mantidui = NULL);
  /// Initialise the layout.
  void init() override;
  /// Set the input workspace name
  void setWorkspaceName(const QString &wsName) override;
  /// Called when the fit is finished
  void finishHandle(const Mantid::API::IAlgorithm *alg) override;
  /// Add an extra widget into the browser
  void addExtraWidget(QWidget *widget);
  /// Set function externally
  void setFunction(const QString &funcString) override;
  /// Run a non-sequential fit
  void runFit() override;
  /// Run a sequential fit
  void runSequentialFit() override;
  /// Get the fitting function
  Mantid::API::IFunction_sptr getFunction() const override {
    return getFittingFunction();
  }
  /// Set parameter value externally
  void setParameterValue(const QString &funcIndex, const QString &paramName,
                         double value) override;
  /// Set list of workspaces to fit
  void setWorkspaceNames(const QStringList &wsNames) override;

public slots:
  /// Perform the fit algorithm
  void fit() override;
  /// Open sequential fit dialog
  void sequentialFit() override;

signals:
  /// Emitted when sequential fit is requested by user
  void sequentialFitRequested();
  /// Emitted when function should be updated
  void functionUpdateRequested() override;
  /// Emitted when a fit or sequential fit is requested
  void functionUpdateAndFitRequested(bool sequential) override;
  /// Emitted when number of workspaces to fit is changed
  void workspacesToFitChanged(int n) override;

protected:
  void showEvent(QShowEvent *e) override;

private slots:
  void doubleChanged(QtProperty *prop) override;

private:
  /// Get the registered function names
  void populateFunctionNames() override;
  /// Check if the workspace can be used in the fit
  bool isWorkspaceValid(Mantid::API::Workspace_sptr) const override;
  /// Layout for extra widgets
  QVBoxLayout *m_additionalLayout;
  /// Names of workspaces to fit
  std::vector<std::string> m_workspacesToFit;
};

} // MantidQt
} // API

#endif /*MUONFITPROPERTYBROWSER_H_*/
