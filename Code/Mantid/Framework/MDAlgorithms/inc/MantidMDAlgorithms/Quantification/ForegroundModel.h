#ifndef MANTID_MDALGORITHMS_FOREGROUNDMODEL_H_
#define MANTID_MDALGORITHMS_FOREGROUNDMODEL_H_
/**
  Copyright &copy; 2012 ISIS Rutherford Appleton Laboratory & NScD Oak Ridge National Laboratory

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

  File change history is stored at: <https://svn.mantidproject.org/mantid/trunk/Code/Mantid>.
  Code Documentation is available at: <http://doxygen.mantidproject.org>
*/
#include "MantidAPI/ExperimentInfo.h"
#include "MantidAPI/ParamFunctionAttributeHolder.h"
#include "MantidMDAlgorithms/Quantification/ForegroundModelFactory.h"

namespace Mantid
{
  namespace MDAlgorithms
  {
    /**
     * Defines an interface to a Foreground model that is
     * to be combined with a resolution calculation.
     *
     * A concrete model should override the following functions
     *  - declareParameters()         : Defines the parameters within the model
     *  - scatteringIntensity() : Returns a value for the cross section with the
     *                            current parameters
     */
    class DLLExport ForegroundModel: public API::ParamFunctionAttributeHolder
    {
    public:
      /// Type of model
      enum ModelType {Broad, Sharp};

      /// Default constructor required by factory
      ForegroundModel();
      /// Constructor taking the fitted function to access the current parameter values
      ForegroundModel(const API::IFunction & fittingFunction);

      /// Returns the type of model
      virtual ModelType modelType() const = 0;
      /// Calculates the intensity for the model for the current parameters, expt description & ND point
      virtual double scatteringIntensity(const API::ExperimentInfo & exptSetup, const std::vector<double> & point) const = 0;

      /// Set a reference to the convolved fitting function. Needed as we need a default constructor
      void setFunctionUnderMinimization(const API::IFunction & fitFunction);
      /// Declares the parameters
      void declareParameters();
      /// Return the initial value of the parameter according to the fit by index
      double getInitialParameterValue(size_t index) const;
      /// Return the initial value of the parameter according to the fit by name
      double getInitialParameterValue(const std::string& name) const;
      /// Return the current parameter according to the fit by index
      double getCurrentParameterValue(const size_t index) const;
      /// Return the current parameter according to the fit by name
      double getCurrentParameterValue(const std::string& name) const;

    protected:
      /// Returns a reference to the fitting function
      const API::IFunction & functionUnderMinimization() const;

    private:
      DISABLE_COPY_AND_ASSIGN(ForegroundModel);

      /// Required by the interface
      void function(const Mantid::API::FunctionDomain&, Mantid::API::FunctionValues&) const {}

      /// Hide these
      using ParamFunction::getParameter;

      /// A (non-owning) pointer to the function undergoing fitting
      const API::IFunction * m_fittingFunction;
      /// An offset for the number of parameters that were declared before this one
      size_t m_parOffset;
    };

    /// boost::shared_ptr typedef
    typedef boost::shared_ptr<ForegroundModel> ForegroundModel_sptr;
    /// boost::shared_ptr to const typedef
    typedef boost::shared_ptr<const ForegroundModel> ForegroundModel_const_sptr;

  }
}

/*
 * Register a class into the factory using a global RegistrationHelper
 * in an anonymous namespace. The comma operator is used to call the
 * factory's subscribe method.
 */
#define DECLARE_FOREGROUNDMODEL(classname) \
  namespace { \
    Mantid::Kernel::RegistrationHelper register_alg_##classname( \
      ((Mantid::MDAlgorithms::ForegroundModelFactory::Instance().subscribe<classname>(#classname)) \
          , 0)); \
}


#endif /* MANTID_MDALGORITHMS_FOREGROUNDMODEL_H_ */
