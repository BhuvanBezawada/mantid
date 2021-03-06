#ifndef MANTID_PYTHONINTERFACE_NDARRAYTOVECTORCONVERTER_H_
#define MANTID_PYTHONINTERFACE_NDARRAYTOVECTORCONVERTER_H_
/*
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

  File change history is stored at: <https://github.com/mantidproject/mantid>.
  Code Documentation is available at: <http://doxygen.mantidproject.org>
*/
#include "MantidKernel/System.h"
#include "MantidPythonInterface/kernel/NdArray.h"
#include <vector>

namespace Mantid {
namespace PythonInterface {
namespace Converters {
/**
 * Converter taking an input numpy array and converting it to a std::vector.
 * Multi-dimensional arrays are flattened and copied.
 */
template <typename DestElementType> struct DLLExport NDArrayToVector {
  // Alias definitions
  using TypedVector = std::vector<DestElementType>;
  using TypedVectorIterator = typename std::vector<DestElementType>::iterator;

  /// Constructor
  NDArrayToVector(const NumPy::NdArray &value);
  /// Create a new vector from the contents of the array
  const TypedVector operator()();
  /// Fill the container with data from the array
  void copyTo(TypedVector &dest) const;

private:
  void throwIfSizeMismatched(const TypedVector &dest) const;

  // reference to the held array
  NumPy::NdArray m_arr;
};
}
}
}

#endif /* MANTID_PYTHONINTERFACE_NDARRAYTOVECTORCONVERTER_H_ */
