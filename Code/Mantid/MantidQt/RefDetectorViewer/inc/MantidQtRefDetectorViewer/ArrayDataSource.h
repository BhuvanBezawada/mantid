#ifndef ARRAY_DATA_SOURCE_H
#define ARRAY_DATA_SOURCE_H

#include <cstddef>
#include "MantidQtImageViewer/DataArray.h"
#include "MantidQtImageViewer/ImageDataSource.h"

/**
    @class ArrayDataSource 
  
       This class provides a wrapper around a simple 2-D array of doubles
    stored in row-major order in a 1-D array, so that the array can be
    viewed using the ImageView data viewer.
 
    @author Dennis Mikkelson 
    @date   2012-05-14 
     
    Copyright © 2012 ORNL, STFC Rutherford Appleton Laboratories
  
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
    
    Code Documentation is available at 
                 <http://doxygen.mantidproject.org>
 */

namespace MantidQt
{
namespace RefDetectorViewer
{

class EXPORT_OPT_MANTIDQT_IMAGEVIEWER ArrayDataSource: public ImageView::ImageDataSource
{
  public:

    /// Construct a DataSource object based on the specified array of floats
    ArrayDataSource( double total_xmin, double total_xmax,
                     double total_ymin, double total_ymax,
                     size_t total_rows, size_t total_cols,
                     float* data );

    ~ArrayDataSource();

    /// Get DataArray covering full range of data in x, and y directions
    ImageView::DataArray * GetDataArray( bool is_log_x );

    /// Get DataArray covering restricted range of data 
    ImageView::DataArray * GetDataArray( double  xmin,
                              double  xmax,
                              double  ymin,
                              double  ymax,
                              size_t  n_rows,
                              size_t  n_cols,
                              bool    is_log_x );

    /// Get a list containing pairs of strings with information about x,y
    void GetInfoList( double x,
                      double y,
                      std::vector<std::string> &list );
  private:
    float* data;  
};

} // namespace MantidQt 
} // namespace ImageView 

#endif // ARRAY_DATA_SOURCE_H
