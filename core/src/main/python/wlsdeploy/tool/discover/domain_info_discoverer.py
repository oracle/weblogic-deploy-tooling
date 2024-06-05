"""
Copyright (c) 2017, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import glob
import os

from java.lang import IllegalArgumentException

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
from wlsdeploy.util import path_helper

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
        self.get_wrc_extension()
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

    def get_wrc_extension(self):
        """
        Discover the WebLogic Remote Console Extension, if installed, and add it to the archive.
        """
        _method_name = 'discover_wrc_extension'
        _logger.entering(class_name=_class_name, method_name=_method_name)

        proceed = True
        if self._weblogic_helper.is_wrc_domain_extension_supported():
            if self._model_context.is_skip_archive():
                _logger.finer('WLSDPLY-06428')
                proceed = False
            elif self._model_context.is_remote():
                proceed = False
                domain_path = '%s/%s/*' % (self._model_context.get_domain_home(),
                                           WLSDeployArchive.WRC_EXTENSION_TARGET_DIR_NAME)
                archive_path = '%s/*' % WLSDeployArchive.ARCHIVE_WRC_EXTENSION_DIR
                self.add_to_remote_map(domain_path, archive_path,
                                       WLSDeployArchive.ArchiveEntryType.WEBLOGIC_REMOTE_CONSOLE_EXTENSION.name())
        else:
            proceed = False
            _logger.info('WLSDPLY-06429', self._model_context.get_effective_wls_version(),
                         class_name=_class_name, method_name=_method_name)

        if not proceed:
            _logger.exiting(class_name=_class_name, method_name=_method_name)
            return

        archive_file = self._model_context.get_archive_file()
        if self._model_context.is_ssh():
            _logger.info('WLSDPLY-06430', self._model_context.get_ssh_host(),
                         self._model_context.get_domain_home(), class_name=_class_name, method_name=_method_name)
            # Download the entire directory if it exists.
            #
            remote_dir = self.path_helper.remote_join(self._model_context.get_domain_home(),
                                                      WLSDeployArchive.WRC_EXTENSION_TARGET_DIR_NAME)
            ssh_client = self._model_context.get_ssh_context()
            if ssh_client.does_directory_exist(remote_dir):
                ssh_client.download(remote_dir, self.download_temporary_dir)
                local_dir = self.path_helper.local_join(self.download_temporary_dir,
                                                        WLSDeployArchive.WRC_EXTENSION_TARGET_DIR_NAME)
                dir_entries = os.listdir(local_dir)
                archive_file_name = archive_file.getArchiveFileName()
                for dir_entry in dir_entries:
                    abs_dir_entry = self.path_helper.local_join(local_dir, dir_entry)
                    if os.path.isfile(abs_dir_entry):
                        try:
                            archive_file.addWrcExtensionFile(abs_dir_entry, True)
                            _logger.info('WLSDPLY-06432', abs_dir_entry, self._model_context.get_ssh_host(),
                                         archive_file_name, class_name=_class_name, method_name=_method_name)
                        except (WLSDeployArchiveIOException, IllegalArgumentException), error:
                            ex = exception_helper.create_discover_exception('WLSDPLY-06433', abs_dir_entry,
                                                                            archive_file_name,
                                                                            error.getLocalizedMessage(), error=error)
                            _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                            raise ex
        else:
            _logger.info('WLSDPLY-06431', self._model_context.get_domain_home())
            install_dir = self.path_helper.local_join(self._model_context.get_domain_home(),
                                                      WLSDeployArchive.WRC_EXTENSION_TARGET_DIR_NAME)
            if os.path.exists(install_dir) and os.path.isdir(install_dir):
                dir_entries = os.listdir(install_dir)
                archive_file_name = archive_file.getArchiveFileName()
                for dir_entry in dir_entries:
                    abs_dir_entry = self.path_helper.local_join(install_dir, dir_entry)
                    if os.path.isfile(abs_dir_entry):
                        try:
                            archive_file.addWrcExtensionFile(abs_dir_entry, True)
                            _logger.info('WLSDPLY-06434', abs_dir_entry, archive_file_name,
                                         class_name=_class_name, method_name=_method_name)
                        except (WLSDeployArchiveIOException, IllegalArgumentException), error:
                            ex = exception_helper.create_discover_exception('WLSDPLY-06433', abs_dir_entry,
                                                                            archive_file.getArchiveFileName(),
                                                                            error.getLocalizedMessage(), error=error)
                            _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                            raise ex

        _logger.exiting(class_name=_class_name, method_name=_method_name)

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
        file_list = []
        if not self._model_context.is_skip_archive():
            if self._model_context.is_remote():
                self.add_to_remote_map("$DOMAIN_HOME/lib/*", "<remote domain home lib>/*",
                               WLSDeployArchive.ArchiveEntryType.DOMAIN_LIB.name())
            elif self._model_context.is_ssh():
                # execute remote command to find the domain libs
                results = self._model_context.get_ssh_context().get_directory_contents(self.path_helper.remote_join(
                    self._model_context.get_domain_home(), "lib"), True, '^.+\.jar$')
                for item in results:
                    file_list.append(item)

            elif os.path.isdir(domain_lib):
                file_list = os.listdir(domain_lib)
            _logger.finer('WLSDPLY-06420', domain_lib, class_name=_class_name, method_name=_method_name)

            for entry_path in file_list:
                if self.path_helper.is_relative_path(entry_path):
                    entry_path = self.path_helper.join(domain_lib, entry_path)
                if self.path_helper.is_jar_file(entry_path):
                    try:
                        if self._model_context.is_ssh():
                            entry_path = self.download_deployment_from_remote_server(entry_path,
                                                                                 self.download_temporary_dir,
                                                                                 "domainLib")

                        updated_name = archive_file.addDomainLibLibrary(entry_path)
                    except WLSDeployArchiveIOException, wioe:
                        de = exception_helper.create_discover_exception('WLSDPLY-06421', entry_path,
                                                                        wioe.getLocalizedMessage())
                        _logger.throwing(class_name=_class_name, method_name=_method_name, error=de)
                        raise de

                    entries.append(updated_name)
                    _logger.finer('WLSDPLY-06422', entry_path, updated_name, class_name=_class_name,
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
            if not self._model_context.is_skip_archive():
                file_list = None

                if self._model_context.is_remote():
                    # Tell user we won't be able to find them
                    self.add_to_remote_map("setUserOverrides*.*", "<remote domain home bin>/setUserOverrides*.*",
                                           WLSDeployArchive.ArchiveEntryType.DOMAIN_BIN.name())
                    file_list = None
                elif self._model_context.is_ssh():
                    file_list = []
                    # execute remote command to find the script
                    results = self._model_context.get_ssh_context().get_directory_contents(self.path_helper.remote_join(
                        self._model_context.get_domain_home(), "bin"), True, '^setUserOverrides.*\..+$')
                    if results:
                        for item in results:
                            file_list.append(item)

                elif os.path.isdir(domain_bin):
                    search_directory = \
                        self.path_helper.fixup_local_path(self.path_helper.local_join(domain_bin, "setUserOverrides*.*"))
                    _logger.finer('WLSDPLY-06425', search_directory, class_name=_class_name, method_name=_method_name)
                    file_list = glob.glob(search_directory)

                if isinstance(file_list, list):
                    _logger.finer('WLSDPLY-06423', domain_bin, class_name=_class_name, method_name=_method_name)
                    for entry in file_list:
                        try:
                            if self._model_context.is_ssh():
                                entry = self.download_deployment_from_remote_server(entry, self.download_temporary_dir,
                                                                                    "domainBin")
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
