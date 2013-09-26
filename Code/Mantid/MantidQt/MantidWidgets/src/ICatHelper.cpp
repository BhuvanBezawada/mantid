#include "MantidQtMantidWidgets/ICatHelper.h"
#include "MantidQtAPI/AlgorithmDialog.h"

#include <QCoreApplication>

namespace MantidQt
{
  namespace MantidWidgets
  {

    /**
     * Obtain the list of instruments from the ICAT Catalog algorithm.
     * @return A vector containing the list of all instruments available.
     */
    std::vector<std::string> ICatHelper::getInstrumentList()
    {
      Mantid::API::IAlgorithm_sptr catalogAlgorithm;
      try
      {
        catalogAlgorithm = Mantid::API::AlgorithmManager::Instance().create("CatalogListInstruments");
      }
      catch(std::runtime_error& exception)
      {
        exception.what();
      }

      catalogAlgorithm->execute();
      // return the vector containing the list of instruments available.
      return (catalogAlgorithm->getProperty("InstrumentList"));
    }

    /**
     * Obtain the list of investigation types from the ICAT Catalog algorithm.
     * @return A vector containing the list of all investigation types available.
     */
    std::vector<std::string> ICatHelper::getInvestigationTypeList()
    {
      Mantid::API::IAlgorithm_sptr catalogAlgorithm;
      try
      {
        catalogAlgorithm = Mantid::API::AlgorithmManager::Instance().create("CatalogListInvestigationTypes");
      }
      catch(std::runtime_error& exception)
      {
        exception.what();
      }

      catalogAlgorithm->execute();
      // return the vector containing the list of investigation types available.
      return (catalogAlgorithm->getProperty("InvestigationTypes"));
    }

    /**
     * Search the archive with the user input terms provided and save them to a workspace ("searchResults").
     * @param userInputFields :: A map containing all users' search fields - (key => FieldName, value => FieldValue).
     */
    void ICatHelper::executeSearch(std::map<std::string, std::string> userInputFields)
    {
      Mantid::API::IAlgorithm_sptr catalogAlgorithm;
      try
      {
        catalogAlgorithm = Mantid::API::AlgorithmManager::Instance().create("CatalogSearch");
      }
      catch(std::runtime_error& exception)
      {
        exception.what();
      }

      // This will be the workspace where the content of the search result is output to.
      catalogAlgorithm->setProperty("OutputWorkspace", "__searchResults");

      // Iterate over the provided map of user input fields. For each field that isn't empty (e.g. a value was input by the user)
      // then we will set the algorithm property with the key and value of that specific value.
      for ( std::map<std::string, std::string>::const_iterator it = userInputFields.begin(); it != userInputFields.end(); it++)
      {
        std::string value = it->second;
        // If the user has input any search terms.
        if (!value.empty())
        {
          // Set the property that the search algorithm uses to: (key => FieldName, value => FieldValue) (e.g., (Keywords, bob))
          catalogAlgorithm->setProperty(it->first, value);
        }
      }
      // Allow asynchronous execution to update label while search is being carried out.
      Poco::ActiveResult<bool> result(catalogAlgorithm->executeAsync());
      while( !result.available() )
      {
        QCoreApplication::processEvents();
      }
    }

    /**
     * Search the archives for all dataFiles related to an "investigation id" then save results to workspace ("dataFileResults").
     * @param investigationId :: The investigation id to use for the search.
     */
    void ICatHelper::executeGetDataFiles(int64_t investigationId)
    {
      Mantid::API::IAlgorithm_sptr catalogAlgorithm;
      try
      {
        catalogAlgorithm = Mantid::API::AlgorithmManager::Instance().create("CatalogGetDataFiles");
      }
      catch(std::runtime_error& exception)
      {
        exception.what();
      }

      // Search for all related dataFiles to this investigation id.
      catalogAlgorithm->setProperty("InvestigationId", investigationId);
      // This will be the workspace where the content of the search result is saved to.
      catalogAlgorithm->setPropertyValue("OutputWorkspace","__dataFileResults");

      // Allow asynchronous execution to update label(s) while search is being carried out.
      Poco::ActiveResult<bool> result(catalogAlgorithm->executeAsync());
      while( !result.available() )
      {
        QCoreApplication::processEvents();
      }
    }

  } // namespace MantidWidgets
} // namespace MantidQt
