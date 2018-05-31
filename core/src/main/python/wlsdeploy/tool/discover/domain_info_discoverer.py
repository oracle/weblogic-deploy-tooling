"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
import javaos as os

from java.io import File

from oracle.weblogic.deploy.util import WLSDeployArchiveIOException

from wlsdeploy.aliases import model_constants
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.discover import discoverer
from wlsdeploy.tool.discover.discoverer import Discoverer
from wlsdeploy.util import path_utils

_class_name = 'DomainInfoDiscoverer'
_logger = PlatformLogger(discoverer.get_discover_logger_name())


class DomainInfoDiscoverer(Discoverer):
    """
    Discover extra information about the domain. This information is not what is stored in domain
    configuration files, but extra information that is required for the completeness of the domain.
    """

    def __init__(self, model_context, domain_info_dictionary, base_location, wlst_mode=WlstModes.OFFLINE, aliases=None):
        Discoverer.__init__(self, model_context, base_location, wlst_mode, aliases)
        self._dictionary = domain_info_dictionary

    def discover(self):
        """
        Discover the domain extra info resources. This information goes into a section of the model
        that does not contain the WLST mbean information that describes the weblogic domain.
        :return: dictionary containing the domain extra info
        """
        _method_name = 'discover'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        model_top_folder_name, result = self.get_domain_libs()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_top_folder_name, result)
        _logger.exiting(class_name=_class_name, method_name=_method_name)
        return self._dictionary

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
