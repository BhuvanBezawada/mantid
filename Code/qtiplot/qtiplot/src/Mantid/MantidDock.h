#ifndef MANTIDDOCK_H
#define MANTIDDOCK_H

#include <QDockWidget>
#include <QTreeWidget>
#include <QComboBox>
#include <QPoint>
#include <QVector>
#include "MantidAPI/MatrixWorkspace.h"
#include "MantidAPI/WorkspaceGroup.h"
#include "MantidAPI/ITableWorkspace.h"

class MantidUI;
class ApplicationWindow;
class MantidTreeWidget;
class QLabel;
class QMenu;
class QPushButton;
class QTreeWidget;
class QProgressBar;
class QVBoxLayout;
class QHBoxLayout;
class QSignalMapper;

class MantidDockWidget: public QDockWidget
{
  Q_OBJECT
public:
  MantidDockWidget(MantidUI *mui, ApplicationWindow *parent);
  QString getSelectedWorkspaceName() const;
  Mantid::API::Workspace_sptr getSelectedWorkspace() const;

public slots:
  void clickedWorkspace(QTreeWidgetItem*, int);
  void deleteWorkspaces();
  void renameWorkspace();
  void populateChildData(QTreeWidgetItem* item);

protected slots:
  void popupMenu(const QPoint & pos);
  void workspaceSelected();

private slots:
  void addTreeEntry(const QString &, Mantid::API::Workspace_sptr);
  void replaceTreeEntry(const QString &, Mantid::API::Workspace_sptr);
  void unrollWorkspaceGroup(const QString &,Mantid::API::Workspace_sptr);
  void removeWorkspaceEntry(const QString &);
  void treeSelectionChanged();
  void groupingButtonClick();
  void plotSpectra();

private:
  QString findParentName(const QString & ws_name, Mantid::API::Workspace_sptr workspace);
  void setItemIcon(QTreeWidgetItem* ws_item,  Mantid::API::Workspace_sptr workspace);
  QTreeWidgetItem *createEntry(const QString & ws_name, Mantid::API::Workspace_sptr workspace);
  void updateWorkspaceEntry(const QString & ws_name, Mantid::API::Workspace_sptr workspace);
  void updateWorkspaceGroupEntry(const QString & ws_name, Mantid::API::WorkspaceGroup_sptr workspace);
  void populateMatrixWorkspaceData(Mantid::API::MatrixWorkspace_sptr workspace, QTreeWidgetItem* ws_item);
  void populateWorkspaceGroupData(Mantid::API::WorkspaceGroup_sptr workspace, QTreeWidgetItem* ws_item);
  void populateTableWorkspaceData(Mantid::API::ITableWorkspace_sptr workspace, QTreeWidgetItem* ws_item);
  
protected:
  MantidTreeWidget * m_tree;
  friend class MantidUI;

private:
  MantidUI * const m_mantidUI;
  QPushButton *m_loadButton;
  QMenu *m_loadMenu;
  QPushButton *m_deleteButton;
  QPushButton *m_groupButton;
  QSignalMapper *m_loadMapper;

  static Mantid::Kernel::Logger& logObject;
  QSet<QString> m_known_groups;
};


class MantidTreeWidget:public QTreeWidget
{
  Q_OBJECT

public:
  MantidTreeWidget(QWidget *w, MantidUI *mui);
  void mousePressEvent (QMouseEvent *e);
  void mouseMoveEvent(QMouseEvent *e);
  void mouseDoubleClickEvent(QMouseEvent *e);

  QList<QString> getSelectedWorkspaceNames() const;
  QMultiMap<QString,int> chooseSpectrumFromSelected() const;
  
private:
  QPoint m_dragStartPosition;
  MantidUI *m_mantidUI;
  static Mantid::Kernel::Logger& logObject;
};

class FindAlgComboBox:public QComboBox
{
    Q_OBJECT
signals:
    void enterPressed();
protected:
    void keyPressEvent(QKeyEvent *e);
};

class AlgorithmDockWidget: public QDockWidget
{
    Q_OBJECT
public:
    AlgorithmDockWidget(MantidUI *mui, ApplicationWindow *w);
public slots:
    void update();
    void findAlgTextChanged(const QString& text);
    void treeSelectionChanged();
    void selectionChanged(const QString& algName);
    void updateProgress(void* alg, const int p, const QString& msg);
    void algorithmStarted(void* alg);
    void algorithmFinished(void* alg);
protected:
    void showProgressBar();
    void hideProgressBar();

    QTreeWidget *m_tree;
    FindAlgComboBox* m_findAlg;
    QPushButton *m_runningButton;
    QProgressBar* m_progressBar;
    QHBoxLayout * m_runningLayout;
    bool m_treeChanged;
    bool m_findAlgChanged;
    QVector<void*> m_algID;
    friend class MantidUI;
private:
    MantidUI *m_mantidUI;
};


class AlgorithmTreeWidget:public QTreeWidget
{
    Q_OBJECT
public:
    AlgorithmTreeWidget(QWidget *w, MantidUI *mui):QTreeWidget(w),m_mantidUI(mui){}
    void mousePressEvent (QMouseEvent *e);
    void mouseMoveEvent(QMouseEvent *e);
    void mouseDoubleClickEvent(QMouseEvent *e);
private:
    QPoint m_dragStartPosition;
    MantidUI *m_mantidUI;
};

#endif
