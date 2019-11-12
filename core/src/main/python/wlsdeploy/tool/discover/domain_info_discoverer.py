"""
Copyright (c) 2017, 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import glob
import os

from java.io import File

from oracle.weblogic.deploy.util import WLSDeployArchiveIOException
from oracle.weblogic.deploy.util import FileUtils

from wlsdeploy.aliases import alias_constants
from wlsdeploy.aliases import model_constants
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.discover import discoverer
from wlsdeploy.tool.discover.discoverer import Discoverer
from wlsdeploy.tool.util.variable_injector import STANDARD_PASSWORD_INJECTOR
from wlsdeploy.util import path_utils
_class_name = 'DomainInfoDiscoverer'
_logger = PlatformLogger(discoverer.get_discover_logger_name())


class DomainInfoDiscoverer(Discoverer):
    """
    Discover extra information about the domain. This information is not what is stored in domain
    configuration files, but extra information that is required for the completeness of the domain.
    """

    def __init__(self, model_context, domain_info_dictionary, base_location,
                 wlst_mode=WlstModes.OFFLINE, aliases=None, variable_injector=None):
        Discoverer.__init__(self, model_context, base_location, wlst_mode, aliases, variable_injector)
        self._dictionary = domain_info_dictionary

    def discover(self):
        """
        Discover the domain extra info resources. This information goes into a section of the model
        that does not contain the WLST mbean information that describes the weblogic domain.
        :return: dictionary containing the domain extra info
        """
        _method_name = 'discover'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        self.add_admin_credentials()
        model_top_folder_name, result = self.get_domain_libs()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_top_folder_name, result)
        model_top_folder_name, result = self.get_user_env_scripts()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_top_folder_name, result)
        _logger.exiting(class_name=_class_name, method_name=_method_name)
        return self._dictionary

    def add_admin_credentials(self):
        injector = self._get_variable_injector()
        self._dictionary[model_constants.ADMIN_USERNAME] = alias_constants.PASSWORD_TOKEN
        self._dictionary[model_constants.ADMIN_PASSWORD] = alias_constants.PASSWORD_TOKEN
        if injector is not None:
            location = LocationContext()
            injector.custom_injection(self._dictionary, model_constants.ADMIN_USERNAME, location,
                                      STANDARD_PASSWORD_INJECTOR)
            injector.custom_injection(self._dictionary, model_constants.ADMIN_PASSWORD, location,
                                      STANDARD_PASSWORD_INJECTOR)

    def get_domain_libs(self):
        """
        Add the java archive files stored in the domain lib into the archive file. Add the information for each
        domain library to the domain info dictionary.
        :raise DiscoverException: an unexpected exception occurred writing a jar file to the archive file
        """
        _method_name = 'get_domain_libs'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        archive_file = self._model_context.get_archive_file()
        domain_lib = self._convert_path('lib')
        entries = []
        if os.path.isdir(domain_lib):
            _logger.finer('WLSDPLY-06420', domain_lib, class_name=_class_name, method_name=_method_name)
            for entry in os.listdir(domain_lib):
                entry_path = os.path.join(domain_lib, entry)
                if path_utils.is_jar_file(entry_path):
                    try:
                        updated_name = archive_file.addDomainLibLibrary(File(entry_path))
                    except WLSDeployArchiveIOException, wioe:
                        de = exception_helper.create_discover_exception('WLSDPLY-06421', entry,
                                                                        wioe.getLocalizedMessage())
                        _logger.throwing(class_name=_class_name, method_name=_method_name, error=de)
                        raise de

                    entries.append(updated_name)
                    _logger.finer('WLSDPLY-06422', entry, updated_name, class_name=_class_name,
                                  method_name=_method_name)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=entries)
        return model_constants.DOMAIN_LIBRARIES, entries

    def get_user_env_scripts(self):
        """
        Look for the user overrides scripts run in setDomainEnv in the domain bin directory
        :raise: DiscoverException: an unexpected exception occurred writing a jar file to the archive file
        """
        _method_name = 'get_user_env_scripts'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        archive_file = self._model_context.get_archive_file()
        domain_bin = self._convert_path('bin')
        entries = []
        if os.path.isdir(domain_bin):
            search_directory = FileUtils.fixupFileSeparatorsForJython(os.path.join(domain_bin, "setUserOverrides*.*"))
            _logger.finer('WLSDPLY-06425', search_directory, class_name=_class_name, method_name=_method_name)
            file_list = glob.glob(search_directory)
            if file_list:
                _logger.finer('WLSDPLY-06423', domain_bin, class_name=_class_name, method_name=_method_name)
                for entry in file_list:
                    try:
                        updated_name = archive_file.addDomainBinScript(File(entry))
                    except WLSDeployArchiveIOException, wioe:
                        de = exception_helper.create_discover_exception('WLSDPLY-06426', entry,
                                                                        wioe.getLocalizedMessage())
                        _logger.throwing(class_name=_class_name, method_name=_method_name, error=de)
                        raise de

                    entries.append(updated_name)
                    _logger.finer('WLSDPLY-06424', entry, updated_name, class_name=_class_name,
                                  method_name=_method_name)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=entries)
        return model_constants.DOMAIN_SCRIPTS, entries
