"""
Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import glob
import os

from java.io import File

from oracle.weblogic.deploy.util import WLSDeployArchive
from oracle.weblogic.deploy.util import WLSDeployArchiveIOException
from oracle.weblogic.deploy.util import FileUtils

from wlsdeploy.aliases import alias_constants
from wlsdeploy.aliases import model_constants
from wlsdeploy.aliases.model_constants import DOMAIN_INFO
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.discover import discoverer
from wlsdeploy.tool.discover.discoverer import Discoverer
from wlsdeploy.tool.util.variable_injector import STANDARD_PASSWORD_INJECTOR
from wlsdeploy.util import path_utils
_class_name = 'DomainInfoDiscoverer'
_logger = PlatformLogger(discoverer.get_discover_logger_name())

ROLE_NAME_LIST = {
    "AppTester": '?weblogic.entitlement.rules.OwnerIDDGroup(AppTesters)',
    'Operator':  '?weblogic.entitlement.rules.AdministrativeGroup(Operators)',
    'Admin':  '?weblogic.entitlement.rules.AdministrativeGroup(Administrators)',
    'Deployer':  '?weblogic.entitlement.rules.AdministrativeGroup(Deployers)',
    'Monitor':   '?weblogic.entitlement.rules.AdministrativeGroup(Monitors)',
    'OracleSystemRole': 'Grp(OracleSystemGroup)',
    'CrossDomainConnector':  '?weblogic.entitlement.rules.OwnerIDDGroup(CrossDomainConnectors)',
    'Anonymous':  'Grp(everyone)',
    'AdminChannelUser':  '?weblogic.entitlement.rules.OwnerIDDGroup(AdminChannelUsers)'

}
class DomainInfoDiscoverer(Discoverer):
    """
    Discover extra information about the domain. This information is not what is stored in domain
    configuration files, but extra information that is required for the completeness of the domain.
    """

    def __init__(self, model_context, domain_info_dictionary, base_location,
                 wlst_mode=WlstModes.OFFLINE, aliases=None, credential_injector=None):
        Discoverer.__init__(self, model_context, base_location, wlst_mode, aliases, credential_injector)
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
        model_top_folder_name, result = self.get_roles()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_top_folder_name, result)
        _logger.exiting(class_name=_class_name, method_name=_method_name)
        return self._dictionary

    def add_admin_credentials(self):
        injector = self._get_credential_injector()
        self._dictionary[model_constants.ADMIN_USERNAME] = alias_constants.PASSWORD_TOKEN
        self._dictionary[model_constants.ADMIN_PASSWORD] = alias_constants.PASSWORD_TOKEN
        if injector is not None:
            location = self._aliases.get_model_section_attribute_location(DOMAIN_INFO)
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
        if os.path.isdir(domain_lib) and not self._model_context.skip_archive():
            _logger.finer('WLSDPLY-06420', domain_lib, class_name=_class_name, method_name=_method_name)
            for entry in os.listdir(domain_lib):
                entry_path = os.path.join(domain_lib, entry)
                if path_utils.is_jar_file(entry_path):
                    try:
                        updated_name = archive_file.addDomainLibLibrary(entry_path)
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
        If discover is running with the -target <type> do not collect the domainBin scripts
        :raise: DiscoverException: an unexpected exception occurred writing a jar file to the archive file
        """
        _method_name = 'get_user_env_scripts'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        entries = []
        if self._model_context.get_target_configuration().exclude_domain_bin_contents():
            _logger.fine('WLSDPLY-06427', class_name=_class_name, method_name=_method_name)
        else:
            archive_file = self._model_context.get_archive_file()
            domain_bin = self._convert_path('bin')
            if os.path.isdir(domain_bin) and not self._model_context.skip_archive():
                search_directory = FileUtils.fixupFileSeparatorsForJython(os.path.join(domain_bin, "setUserOverrides*.*"))
                _logger.finer('WLSDPLY-06425', search_directory, class_name=_class_name, method_name=_method_name)
                file_list = glob.glob(search_directory)
                if file_list:
                    _logger.finer('WLSDPLY-06423', domain_bin, class_name=_class_name, method_name=_method_name)
                    for entry in file_list:
                        if self._model_context.is_remote():
                            new_source_name = archive_file.getDomainBinScriptArchivePath(entry)
                            self.add_to_remote_map(entry, new_source_name,
                                                   WLSDeployArchive.ArchiveEntryType.DOMAIN_BIN.name())
                        else:
                            try:
                                updated_name = archive_file.addDomainBinScript(entry)
                            except WLSDeployArchiveIOException, wioe:
                                de = exception_helper.create_discover_exception('WLSDPLY-06426', entry,
                                                                                wioe.getLocalizedMessage    ())
                                _logger.throwing(class_name=_class_name, method_name=_method_name, error=de)
                                raise de

                            entries.append(updated_name)
                            _logger.finer('WLSDPLY-06424', entry, updated_name, class_name=_class_name,
                                      method_name=_method_name)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=entries)
        return model_constants.DOMAIN_SCRIPTS, entries

    def get_roles(self):
        _method_name = 'get_roles'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        model = dict()
        model_folder = model_constants.WLS_ROLES
        if self._wlst_mode == WlstModes.ONLINE:
            props=[]

            cmo = self._wlst_helper.get_cmo()
            realms = cmo.getSecurityConfiguration().getRealms()
            for r in realms:
                rms=r.getRoleMappers()
                for rm in rms:
                    if rm.getName() == 'XACMLRoleMapper':
                        c=rm.listAllRoles(500)

                        while rm.haveCurrent(c):
                            props.append(rm.getCurrentProperties(c))
                            rm.advance(c)
                        rm.close(c)

            for entry in props:
                if 'RoleName' in entry and entry['RoleName'] != '**':
                    role_name = entry['RoleName']
                    role_expression = entry['Expression']
                    if role_name not in ROLE_NAME_LIST or ROLE_NAME_LIST[role_name] != role_expression:
                        # put it in the model
                        model[role_name] = dict()
                        model[role_name][model_constants.EXPRESSION] =  role_expression
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=model)
        return model_folder, model

