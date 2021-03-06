#ifndef MANTID_API_IMDHISTOWORKSPACE_H_
#define MANTID_API_IMDHISTOWORKSPACE_H_

#include "MantidAPI/IMDHistoWorkspace_fwd.h"
#include "MantidAPI/IMDWorkspace.h"
#include "MantidAPI/MultipleExperimentInfos.h"
#include "MantidKernel/System.h"

namespace Mantid {
namespace API {

/** Abstract interface to MDHistoWorkspace,
  for use in exposing to Python.

  @date 2011-11-09

  Copyright &copy; 2011 ISIS Rutherford Appleton Laboratory, NScD Oak Ridge
  National Laboratory & European Spallation Source

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
class DLLExport IMDHistoWorkspace : public IMDWorkspace,
                                    public MultipleExperimentInfos {
public:
  IMDHistoWorkspace() = default;
  IMDHistoWorkspace &operator=(const IMDHistoWorkspace &) = delete;
  /// Returns a clone of the workspace
  IMDHistoWorkspace_uptr clone() const {
    return IMDHistoWorkspace_uptr(doClone());
  }
  /// Returns a default-initialized clone of the workspace
  IMDHistoWorkspace_uptr cloneEmpty() const {
    return IMDHistoWorkspace_uptr(doCloneEmpty());
  }
  /// See the MDHistoWorkspace definition for descriptions of these
  virtual coord_t getInverseVolume() const = 0;
  virtual signal_t *getSignalArray() const = 0;
  virtual signal_t *getErrorSquaredArray() const = 0;
  virtual signal_t *getNumEventsArray() const = 0;
  virtual void setTo(signal_t signal, signal_t errorSquared,
                     signal_t numEvents) = 0;
  virtual Mantid::Kernel::VMD getCenter(size_t linearIndex) const = 0;
  virtual void setSignalAt(size_t index, signal_t value) = 0;
  virtual void setErrorSquaredAt(size_t index, signal_t value) = 0;
  virtual signal_t getErrorAt(size_t index) const = 0;
  virtual signal_t getErrorAt(size_t index1, size_t index2) const = 0;
  virtual signal_t getErrorAt(size_t index1, size_t index2,
                              size_t index3) const = 0;
  virtual signal_t getErrorAt(size_t index1, size_t index2, size_t index3,
                              size_t index4) const = 0;
  virtual signal_t getSignalAt(size_t index) const = 0;
  virtual signal_t getSignalAt(size_t index1, size_t index2) const = 0;
  virtual signal_t getSignalAt(size_t index1, size_t index2,
                               size_t index3) const = 0;
  virtual signal_t getSignalAt(size_t index1, size_t index2, size_t index3,
                               size_t index4) const = 0;
  virtual signal_t getSignalNormalizedAt(size_t index) const = 0;
  virtual signal_t getSignalNormalizedAt(size_t index1,
                                         size_t index2) const = 0;
  virtual signal_t getSignalNormalizedAt(size_t index1, size_t index2,
                                         size_t index3) const = 0;
  virtual signal_t getSignalNormalizedAt(size_t index1, size_t index2,
                                         size_t index3,
                                         size_t index4) const = 0;
  virtual signal_t getErrorNormalizedAt(size_t index) const = 0;
  virtual signal_t getErrorNormalizedAt(size_t index1, size_t index2) const = 0;
  virtual signal_t getErrorNormalizedAt(size_t index1, size_t index2,
                                        size_t index3) const = 0;
  virtual signal_t getErrorNormalizedAt(size_t index1, size_t index2,
                                        size_t index3, size_t index4) const = 0;

  virtual signal_t &errorSquaredAt(size_t index) = 0;
  virtual signal_t &signalAt(size_t index) = 0;
  virtual size_t getLinearIndex(size_t index1, size_t index2) const = 0;
  virtual size_t getLinearIndex(size_t index1, size_t index2,
                                size_t index3) const = 0;
  virtual size_t getLinearIndex(size_t index1, size_t index2, size_t index3,
                                size_t index4) const = 0;

  virtual LinePlot
  getLineData(const Mantid::Kernel::VMD &start, const Mantid::Kernel::VMD &end,
              Mantid::API::MDNormalization normalize) const = 0;

  virtual double &operator[](const size_t &index) = 0;

  virtual void setCoordinateSystem(
      const Kernel::SpecialCoordinateSystem coordinateSystem) = 0;

  virtual void setDisplayNormalization(
      const Mantid::API::MDNormalization &preferredNormalization) = 0;

  // Check if this class has an oriented lattice on any sample object
  virtual bool hasOrientedLattice() const override {
    return MultipleExperimentInfos::hasOrientedLattice();
  }

protected:
  /// Protected copy constructor. May be used by childs for cloning.
  IMDHistoWorkspace(const IMDHistoWorkspace &) = default;

  const std::string toString() const override;

private:
  IMDHistoWorkspace *doClone() const override = 0;
  IMDHistoWorkspace *doCloneEmpty() const override = 0;
};

} // namespace API
} // namespace Mantid

#endif /* MANTID_API_IMDHISTOWORKSPACE_H_ */
