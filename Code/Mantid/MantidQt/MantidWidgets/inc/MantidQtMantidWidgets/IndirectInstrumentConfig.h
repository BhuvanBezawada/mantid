#ifndef MANTIDQTMANTIDWIDGETS_INDIRECTINSTRUMENTCONFIG_H_
#define MANTIDQTMANTIDWIDGETS_INDIRECTINSTRUMENTCONFIG_H_

#include "WidgetDllOption.h"
#include "ui_IndirectInstrumentConfig.h"

#include "MantidQtAPI/AlgorithmRunner.h"
#include "MantidQtAPI/MantidWidget.h"
#include "MantidQtMantidWidgets/InstrumentSelector.h"

#include <QWidget>

namespace MantidQt
{
  namespace MantidWidgets
  {
    /**
    Widget used to select an instrument configuration for indirect geometry spectrometers
    (i.e. and instrument, analyser and reflection).

    Instruments are populated using an InstrumentSelector widget, analysers and reflections
    are populated by loading an empty instrument.

    @author Dan Nixon

    Copyright &copy; 2011 ISIS Rutherford Appleton Laboratory, NScD Oak Ridge National Laboratory & European Spallation Source

    This file is part of Mantid.

    Mantid is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License, or
    (at your option) any later version.

    Mantid is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    File change history is stored at: <https://github.com/mantidproject/mantid>
    Code Documentation is available at: <http://doxygen.mantidproject.org>
    */

    class EXPORT_OPT_MANTIDQT_MANTIDWIDGETS IndirectInstrumentConfig: public API::MantidWidget
    {
      Q_OBJECT

      Q_PROPERTY(QStringList techniques READ getTechniques WRITE setTechniques)
      Q_PROPERTY(QStringList disabledInstruments READ getDisabledInstruments WRITE setDisabledInstruments)
      Q_PROPERTY(QString facility READ getFacility WRITE setFacility)
      Q_PROPERTY(bool enableDiffraction READ isDiffractionEnabled WRITE enableDiffraction)
      Q_PROPERTY(bool forceDiffraction READ isDiffractionForced WRITE forceDiffraction)
      Q_PROPERTY(bool autoLoadConfigurations READ willAutoLoadConfigurations WRITE autoLoadConfigurations)

    public:
      IndirectInstrumentConfig(QWidget *parent = 0, bool init = true);
      virtual ~IndirectInstrumentConfig();

      /* Getters and setters for Qt properties */
      QStringList getTechniques();
      void setTechniques(const QStringList & techniques);

      QStringList getDisabledInstruments();
      void setDisabledInstruments(const QStringList & instrumentNames);

      QString getFacility();
      void setFacility(const QString & facilityName);

      bool isDiffractionEnabled();
      void enableDiffraction(bool enabled);

      bool isDiffractionForced();
      void forceDiffraction(bool forced);

      bool willAutoLoadConfigurations();
      void autoLoadConfigurations(bool autoLoad);

      /// Gets the name of the selected instrument
      QString getInstrumentName();
      /// Gets the name of the selected analyser
      QString getAnalyserName();
      /// Gets the name of the selected reflection
      QString getReflectionName();

    private slots:
      /// Updates the list of analysers and reflections based on the selected instrument
      void updateInstrumentConfigurations(const QString & instrumentName);
      /// Updates the list of reflections when an analyser is selected
      void updateReflectionsList(int index);

    private:
      /// Member containing the widgets child widgets.
      Ui::IndirectInstrumentConfig m_uiForm;
      /// Algorithm Runner used to load empty instrument workspaces
      MantidQt::API::AlgorithmRunner m_algRunner;
      /// Instrument selector widget
      MantidQt::MantidWidgets::InstrumentSelector *m_instrumentSelector;

      QStringList m_disabledInstruments;
      bool m_removeDiffraction;
      bool m_forceDiffraction;
      bool m_autoLoad;

    };

  } /* namespace MantidWidgets */
} /* namespace MantidQt */

#endif /* INDIRECTINSTRUMENTCONFIG_H_ */
