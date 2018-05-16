#ifndef MANTID_ALGORITHMS_CalculatePoleFigure_H_
#define MANTID_ALGORITHMS_CalculatePoleFigure_H_

#include "MantidAPI/Algorithm.h"
#include "MantidAPI/MatrixWorkspace.h"
#include "MantidAPI/WorkspaceUnitValidator.h"
#include "MantidKernel/System.h"
#include "MantidAPI/ITableWorkspace.h"

namespace Mantid {
namespace Algorithms {

/** CalculatePoleFigure : Calcualte Pole Figure for engineering material
 */
class DLLExport CalculatePoleFigure : public API::Algorithm {
public:
  /// Algorithm's name for identification
  const std::string name() const override;
  /// Summary of algorithms purpose
  const std::string summary() const override {
    return "function (PDF). G(r) will be stored in another named workspace.";
  }

  /// Algorithm's version for identification
  int version() const override;
  /// Algorithm's category for identification
  const std::string category() const override;

private:
  /// Initialize the properties
  void init() override;
  /// Run the algorithm
  void exec() override;

  /// process inputs
  void processInputs();

  /// calculate pole figure
  void calculatePoleFigure();
  double
  calculatePeakIntensitySimple(size_t iws,
                               const std::pair<double, double> &peak_range);
  void convertCoordinates(Kernel::V3D unitQ, const double &hrot,
                          const double &omega, double &r_td, double &r_nd);

  /// calculate peaks' intensities
  void calculatePeaksIntensities();

  /// integrate event counts within a region of d-spacing
  void integrateEventCounts(double min_d, double max_d, std::vector<double> &events_counts_vec, std::vector<double> &estimated_bkgd_vec);

  /// generatae output workspace and set output properties
  void generateOutputs();

  /// fit peaks within given d range
  void fitPeaks(const double d_min, const double d_max);

  /// input workspace
  API::MatrixWorkspace_const_sptr m_inputWS;
  /// output workspace
  API::ITableWorkspace_sptr m_outputTableWS;

  /// sample log name
  std::string m_nameHROT;
  std::string m_nameOmega;

  /// range of dspacing
  std::pair<double, double> m_peakDRange;

  /// vector to record pole figure
  std::vector<double> m_poleFigureRTDVector;
  std::vector<double> m_poleFigureRNDVector;
  std::vector<double> m_poleFigurePeakIntensityVector;

  ///
};

} // namespace Mantid
} // namespace Algorithms

#endif /* MANTID_ALGORITHMS_CalculatePoleFigure_H_ */
