"""
Copyright (c) 2017, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os.path
from java.lang import IllegalArgumentException

from oracle.weblogic.deploy.util import PyOrderedDict as OrderedDict
from oracle.weblogic.deploy.util import StringUtils
from oracle.weblogic.deploy.util import WLSDeployArchive
from oracle.weblogic.deploy.util import WLSDeployArchiveIOException

from wlsdeploy.aliases import model_constants
from wlsdeploy.aliases.alias_constants import PASSWORD_TOKEN
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_PATH_PROPERTIES
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.deploy import deployer_utils
from wlsdeploy.tool.discover import discoverer
from wlsdeploy.tool.discover.coherence_resources_discoverer import CoherenceResourcesDiscoverer
from wlsdeploy.tool.discover.discoverer import Discoverer
from wlsdeploy.tool.discover.jms_resources_discoverer import JmsResourcesDiscoverer
from wlsdeploy.util import dictionary_utils

_class_name = 'CommonResourcesDiscoverer'
_logger = PlatformLogger(discoverer.get_discover_logger_name())


class CommonResourcesDiscoverer(Discoverer):
    """
    Discover the weblogic resources that are common across global, resource group template, and
    partition resource group.
    """

    def __init__(self, model_context, resource_dictionary, base_location,
                 wlst_mode=WlstModes.OFFLINE, aliases=None, credential_injector=None):
        """

        :param model_context: context about the model for this instance of discover domain
        :param resource_dictionary: to populate the common resources. By default, populates the initialized resources
        :param base_location: to look for common weblogic resources. By default this is the global path or '/'
        """
        Discoverer.__init__(self, model_context, base_location, wlst_mode, aliases, credential_injector)
        self._dictionary = resource_dictionary
        self._add_att_handler(model_constants.PATH_TO_SCRIPT, self._add_wldf_script)

    def discover(self):
        """
        Discover weblogic resources from the on-premise domain.
        :return: resources: dictionary where to populate discovered domain resources
        """
        _method_name = 'discover'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        model_folder_name, folder_result = self.get_datasources()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, folder_result)
        model_folder_name, folder_result = self.get_foreign_jndi_providers()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, folder_result)
        model_folder_name, folder_result = self.get_mail_sessions()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, folder_result)
        model_folder_name, folder_result = self.get_file_stores()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, folder_result)
        model_folder_name, folder_result = self.get_jdbc_stores()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, folder_result)
        model_folder_name, folder_result = self.get_path_services()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, folder_result)
        JmsResourcesDiscoverer(self._model_context, self._dictionary, self._base_location, wlst_mode=self._wlst_mode,
                               aliases=self._aliases, credential_injector=self._get_credential_injector()).discover()
        model_folder_name, folder_result = self.get_wldf_system_resources()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, folder_result)
        model_folder_name, folder_result = self.get_system_component_resources()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, folder_result)
        model_folder_name, folder_result = self.get_ohs_resources()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, folder_result)
        CoherenceResourcesDiscoverer(self._model_context, self._dictionary, self._base_location,
                                     wlst_mode=self._wlst_mode, aliases=self._aliases,
                                     credential_injector=self._get_credential_injector()).discover()

        _logger.exiting(class_name=_class_name, method_name=_method_name)
        return self._dictionary

    def get_datasources(self):
        """
        Discover JDBC datasource information from the domain.
        :return: model name for the dictionary and the dictionary containing the datasources information
        """
        _method_name = 'get_datasources'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        result = OrderedDict()
        model_top_folder_name = model_constants.JDBC_SYSTEM_RESOURCE
        model_second_folder = model_constants.JDBC_RESOURCE
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        datasources = self._find_names_in_folder(location)
        collected_wallet = {}
        if datasources is not None:
            _logger.info('WLSDPLY-06340', len(datasources), class_name=_class_name, method_name=_method_name)
            typedef = self._model_context.get_domain_typedef()
            name_token = self._aliases.get_name_token(location)
            for datasource in datasources:
                if typedef.is_filtered(location, datasource):
                    _logger.info('WLSDPLY-06361', typedef.get_domain_type(), datasource, class_name=_class_name,
                                 method_name=_method_name)
                else:
                    _logger.info('WLSDPLY-06341', datasource, class_name=_class_name, method_name=_method_name)
                    result[datasource] = OrderedDict()
                    location.add_name_token(name_token, datasource)
                    self._populate_model_parameters(result[datasource], location)

                    location.append_location(model_second_folder)
                    deployer_utils.set_single_folder_token(location, self._aliases)
                    if self.wlst_cd(self._aliases.get_wlst_attributes_path(location), location):
                        result[datasource][model_second_folder] = OrderedDict()
                        resource_result = result[datasource][model_second_folder]
                        self._populate_model_parameters(resource_result, location)
                        self._discover_subfolders(resource_result, location)
                        self._collect_jdbc_driver_wallet(datasource, collected_wallet,
                                  result[datasource][model_constants.JDBC_RESOURCE][model_constants.JDBC_DRIVER_PARAMS])
                        location.remove_name_token(name_token)
                        location.pop_location()
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
        return model_top_folder_name, result

    def _collect_jdbc_driver_wallet(self, datasource, collected_wallet, driver_params):
        if not self._model_context.is_skip_archive() and \
                (isinstance(driver_params, dict) or isinstance(driver_params, OrderedDict)) and \
                model_constants.JDBC_DRIVER_PARAMS_PROPERTIES in driver_params:
            properties = driver_params[model_constants.JDBC_DRIVER_PARAMS_PROPERTIES]
            self._update_wallet_property_and_collect_files(collected_wallet, datasource, properties)

    def _update_wallet_property_and_collect_files(self, collected_wallet, datasource, properties):
        _method_name = '_update_wallet_property_and_collect_files'
        for connection_property in DRIVER_PARAMS_PATH_PROPERTIES:
            if connection_property in properties:
                qualified_property_value = properties[connection_property]['Value']
                if qualified_property_value:
                    if WLSDeployArchive.isPathIntoArchive(qualified_property_value):
                        qualified_property_value = self.path_helper.local_join(self._model_context.get_domain_home(),
                                                                               qualified_property_value)
                    if self._model_context.is_ssh():
                        qualified_property_value = self.download_deployment_from_remote_server(qualified_property_value,
                                                                                       self.download_temporary_dir,
                                                                                       "dbWallets-" + datasource)
                    if self.path_helper.is_relative_local_path(qualified_property_value):
                        #
                        # if the property value is a relative path at this point, it is relative to the
                        # domain home.  If this path is absolute already, get_local_canonical_path is a no-op.
                        #
                        qualified_property_value = \
                            self.path_helper.get_local_canonical_path(qualified_property_value,
                                                                      self._model_context.get_domain_home())
                    if os.path.exists(qualified_property_value):
                        fixed_path = self._add_wallet_directory_to_archive(datasource, collected_wallet,
                                                                           qualified_property_value)
                        _logger.info('WLSDPLY-06367', connection_property, fixed_path,
                                     class_name=_class_name, method_name=_method_name)
                        properties[connection_property]['Value'] = fixed_path
                    else:
                        de = exception_helper.create_discover_exception('WLSDPLY-06370', datasource,
                                                                        connection_property,
                                                                        properties[connection_property]['Value'])
                        _logger.throwing(class_name=_class_name, method_name=_method_name, error=de)
                        raise de

    def _add_wallet_directory_to_archive(self, datasource, collected_wallet_dictionary, property_value):
        # error if wallet parent path is at oracle home
        onprem_wallet_parent_path, wallet_name = self._get_wallet_name_and_path(datasource, property_value)

        if self._model_context.is_remote():
            fixed_path = WLSDeployArchive.getDatabaseWalletArchivePath(wallet_name, property_value)
            self.add_to_remote_map(property_value, fixed_path,
                                   WLSDeployArchive.ArchiveEntryType.DB_WALLET.name())
            return fixed_path

        onprem_wallet_dir_is_not_flat = self._is_on_prem_wallet_dir_flat(onprem_wallet_parent_path, property_value)
        archive_file = self._model_context.get_archive_file()

        # keep track of the wallet name and from where it is collected
        #  { <onprem_wallet_parentpath> : { 'wallet_name': <name>, 'path_into_archive': <wallet path into archive>,
        #      },
        #     .... }
        #
        if onprem_wallet_parent_path not in collected_wallet_dictionary:
            if onprem_wallet_dir_is_not_flat:
                # collect the specific file
                # 
                fixed_path = archive_file.addDatabaseWallet(wallet_name, property_value)
                path_into_archive = os.path.dirname(fixed_path)
            else:
                fixed_path = archive_file.addDatabaseWallet(wallet_name, onprem_wallet_parent_path)
                path_into_archive = fixed_path
                fixed_path = self.path_helper.local_join(fixed_path, self.path_helper.local_basename(property_value))

            collected_wallet_dictionary[onprem_wallet_parent_path] = \
                {'wallet_name' : wallet_name, 'path_into_archive': path_into_archive}
        else:
            # if the directory has already been visited before
            # check for the wallet to see if the file has already been collected on prem and add only the file
            check_path = os.path.join(
                collected_wallet_dictionary[onprem_wallet_parent_path]['path_into_archive'],
                self.path_helper.local_basename(property_value))
            if check_path not in archive_file.getArchiveEntries() and os.path.isfile(property_value):
                # only case is it is not flat directory if the particular file has not been collected before, add
                # it to the previous wallet
                fixed_path = archive_file.addDatabaseWallet(collected_wallet_dictionary[onprem_wallet_parent_path]['wallet_name'],
                                                        os.path.abspath(property_value))
            else:
                # already in archive just figure out the path
                if (os.path.isdir(property_value)):
                    fixed_path = collected_wallet_dictionary[onprem_wallet_parent_path]['path_into_archive']
                else:
                    fixed_path = os.path.join(collected_wallet_dictionary[onprem_wallet_parent_path]['path_into_archive'],
                                              self.path_helper.local_basename(property_value))

        return fixed_path

    def _get_wallet_name_and_path(self, datasource, property_value):
        _method_name = '_get_wallet_name_and_path'
        # fix up name just in case
        wallet_name = datasource.replace(' ', '').replace('(', '').replace(')', '')
        if os.path.isdir(property_value):
            onprem_wallet_parent_path = os.path.abspath(property_value)
        else:
            onprem_wallet_parent_path = os.path.dirname(os.path.abspath(property_value))
        if self._model_context.get_oracle_home() == onprem_wallet_parent_path:
            _logger.severe('WLSDPLY-06368', property_value, self._model_context.get_oracle_home())
            de = exception_helper.create_discover_exception('WLSDPLY-06368', property_value,
                                                            self._model_context.get_oracle_home())
            _logger.throwing(class_name=_class_name, method_name=_method_name, error=de)
            raise de
        return onprem_wallet_parent_path, wallet_name

    def _is_on_prem_wallet_dir_flat(self, onprem_wallet_parent_path, property_value):
        # info if wallet parent is not flat and only collect the particular file and not the entire directory
        dir_list = os.listdir(onprem_wallet_parent_path)
        onprem_wallet_dir_is_not_flat = False
        for item in dir_list:
            if os.path.isdir(os.path.join(onprem_wallet_parent_path, item)):
                onprem_wallet_dir_is_not_flat = True
                break
        # put out info for user only particular file is collected and not the entire wallet directory
        if onprem_wallet_dir_is_not_flat:
            _logger.info('WLSDPLY-06369', property_value)
        return onprem_wallet_dir_is_not_flat

    def get_foreign_jndi_providers(self):
        """
        Discover Foreign JNDI providers from the domain.
        :return: model name for the dictionary and the dictionary containing the foreign JNDI provider information
        """
        _method_name = 'get_foreign_jndi_providers'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        result = OrderedDict()
        model_top_folder_name = model_constants.FOREIGN_JNDI_PROVIDER
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        providers = self._find_names_in_folder(location)
        if providers is not None:
            _logger.info('WLSDPLY-06342', len(providers), class_name=_class_name, method_name=_method_name)
            typedef = self._model_context.get_domain_typedef()
            name_token = self._aliases.get_name_token(location)
            for provider in providers:
                if typedef.is_filtered(location, provider):
                    _logger.info('WLSDPLY-06375', typedef.get_domain_type(), provider, class_name=_class_name,
                                 method_name=_method_name)
                else:
                    _logger.info('WLSDPLY-06343', provider, class_name=_class_name, method_name=_method_name)
                    location.add_name_token(name_token, provider)
                    result[provider] = OrderedDict()
                    self._populate_model_parameters(result[provider], location)
                    self._discover_subfolders(result[provider], location)
                    location.remove_name_token(name_token)
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=model_top_folder_name)
        return model_top_folder_name, result

    def get_mail_sessions(self):
        """
        Discover the mail sessions from the domain.
        :return: model name for the dictionary and the dictionary containing the mail session information
        """
        _method_name = 'get_mail_sessions'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        result = OrderedDict()
        model_top_folder_name = model_constants.MAIL_SESSION
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        mail_sessions = self._find_names_in_folder(location)
        if mail_sessions is not None:
            _logger.info('WLSDPLY-06344', len(mail_sessions), class_name=_class_name, method_name=_method_name)
            typedef = self._model_context.get_domain_typedef()
            name_token = self._aliases.get_name_token(location)
            for mail_session in mail_sessions:
                if typedef.is_filtered(location, mail_session):
                    _logger.info('WLSDPLY-06374', typedef.get_domain_type(), mail_session, class_name=_class_name,
                                 method_name=_method_name)
                else:
                    _logger.info('WLSDPLY-06345', mail_session, class_name=_class_name, method_name=_method_name)
                    result[mail_session] = OrderedDict()
                    mail_session_result = result[mail_session]
                    location.add_name_token(name_token, mail_session)
                    self._populate_model_parameters(mail_session_result, location)
                    self._fix_passwords_in_mail_session_properties(mail_session_result)
                    location.remove_name_token(name_token)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=model_top_folder_name)
        return model_top_folder_name, result

    def get_file_stores(self):
        """
        Discover the file stores used for weblogic persistence
        :return: model folder name: dictionary with the discovered file stores
        """
        _method_name = 'get_file_stores'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        result = OrderedDict()
        model_top_folder_name = model_constants.FILE_STORE
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        file_stores = self._find_names_in_folder(location)
        if file_stores is not None:
            _logger.info('WLSDPLY-06346', len(file_stores), class_name=_class_name, method_name=_method_name)
            typedef = self._model_context.get_domain_typedef()
            name_token = self._aliases.get_name_token(location)
            for file_store in file_stores:
                if typedef.is_filtered(location, file_store):
                    _logger.info('WLSDPLY-06363', typedef.get_domain_type(), file_store, class_name=_class_name,
                                 method_name=_method_name)
                else:
                    _logger.info('WLSDPLY-06347', file_store, class_name=_class_name, method_name=_method_name)
                    result[file_store] = OrderedDict()
                    location.add_name_token(name_token, file_store)
                    self._populate_model_parameters(result[file_store], location)
                    self.archive_file_store_directory(file_store, result[file_store])
                    location.remove_name_token(name_token)
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
        return model_top_folder_name, result

    def archive_file_store_directory(self, file_store_name, file_store_dictionary):
        _method_name = 'archive_file_store_directory'
        _logger.entering(file_store_name, class_name=_class_name, method_name=_method_name)
        if file_store_name is not None and model_constants.DIRECTORY in file_store_dictionary:
            directory = file_store_dictionary[model_constants.DIRECTORY]
            if not StringUtils.isEmpty(directory):
                archive_file = self._model_context.get_archive_file()
                if self._model_context.is_remote():
                    new_name = WLSDeployArchive.getFileStoreArchivePath(file_store_name)
                    self.add_to_remote_map(file_store_name, new_name,
                                           WLSDeployArchive.ArchiveEntryType.FILE_STORE.name())
                elif not self._model_context.is_skip_archive():
                    try:
                        if self._model_context.is_ssh():
                            file_store_name = self.download_deployment_from_remote_server(file_store_name,
                                                                                     self.download_temporary_dir,
                                                                                     "fileStore")

                        new_source_name = archive_file.addFileStoreDirectory(file_store_name)
                    except WLSDeployArchiveIOException, wioe:
                        de = exception_helper.create_discover_exception('WLSDPLY-06348', file_store_name, directory,
                                                                        wioe.getLocalizedMessage())
                        _logger.throwing(class_name=_class_name, method_name=_method_name, error=de)
                        raise de
                    if new_source_name is not None:
                        _logger.info('WLSDPLY-06349', file_store_name, new_source_name, class_name=_class_name,
                                     method_name=_method_name)
                        file_store_dictionary[model_constants.DIRECTORY] = new_source_name

        _logger.exiting(class_name=_class_name, method_name=_method_name)

    def get_jdbc_stores(self):
        """
        Discover the JDBC stores used for weblogic persistence
        :return: model file name: dictionary containing discovered JDBC stores
        """
        _method_name = 'get_jdbc_stores'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        result = OrderedDict()
        model_top_folder_name = model_constants.JDBC_STORE
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        jdbc_stores = self._find_names_in_folder(location)
        if jdbc_stores is not None:
            _logger.info('WLSDPLY-06350', len(jdbc_stores), class_name=_class_name, method_name=_method_name)
            typedef = self._model_context.get_domain_typedef()
            name_token = self._aliases.get_name_token(location)
            for jdbc_store in jdbc_stores:
                if typedef.is_filtered(location, jdbc_store):
                    _logger.info('WLSDPLY-06373', typedef.get_domain_type(), jdbc_store, class_name=_class_name,
                                 method_name=_method_name)
                else:
                    _logger.info('WLSDPLY-06351', jdbc_store, class_name=_class_name, method_name=_method_name)
                    result[jdbc_store] = OrderedDict()
                    location.add_name_token(name_token, jdbc_store)
                    self._populate_model_parameters(result[jdbc_store], location)
                    self.archive_jdbc_create_script(jdbc_store, result[jdbc_store])
                    location.remove_name_token(name_token)
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
        return model_top_folder_name, result

    def archive_jdbc_create_script(self, jdbc_store_name, jdbc_store_dictionary):
        """
        Add the JDBC store create DDL file to the archive.
        :param jdbc_store_name: name of the JDBC Store
        :param jdbc_store_dictionary: dictionary containing the discovered store attributes
        """
        _method_name = 'get_jdbc_create_script'
        _logger.entering(jdbc_store_name, class_name=_class_name, method_name=_method_name)
        if model_constants.CREATE_TABLE_DDL_FILE in jdbc_store_dictionary:
            archive_file = self._model_context.get_archive_file()
            file_name = self._convert_path(jdbc_store_dictionary[model_constants.CREATE_TABLE_DDL_FILE])
            _logger.info('WLSDPLY-06352', jdbc_store_name, file_name, class_name=_class_name, method_name=_method_name)
            try:
                if self._model_context.is_ssh():
                    file_name = self.download_deployment_from_remote_server(file_name,
                                                                                   self.download_temporary_dir,
                                                                                   "jdbcScript")

                new_source_name = archive_file.addScript(file_name)
            except IllegalArgumentException, iae:
                _logger.warning('WLSDPLY-06353', jdbc_store_name, file_name,
                                iae.getLocalizedMessage(), class_name=_class_name,
                                method_name=_method_name)
                _logger.exiting(class_name=_class_name, method_name=_method_name)
                return
            except WLSDeployArchiveIOException, wioe:
                de = exception_helper.create_discover_exception('WLSDPLY-06354', jdbc_store_name, file_name,
                                                                wioe.getLocalizedMessage())
                _logger.throwing(class_name=_class_name, method_name=_method_name, error=de)
                raise de

            if new_source_name is None:
                new_source_name = file_name
            tokenized = self._model_context.tokenize_path(new_source_name)
            jdbc_store_dictionary[model_constants.CREATE_TABLE_DDL_FILE] = tokenized

        _logger.exiting(class_name=_class_name, method_name=_method_name)
        return

    def get_path_services(self):
        """
        Discover the path services for weblogic message grouping.
        :return: model file name: dictionary containing discovered path services
        """
        _method_name = 'get_path_services'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        result = OrderedDict()
        model_top_folder_name = model_constants.PATH_SERVICE
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        path_services = self._find_names_in_folder(location)
        if path_services is not None:
            _logger.info('WLSDPLY-06355', len(path_services), class_name=_class_name, method_name=_method_name)
            typedef = self._model_context.get_domain_typedef()
            name_token = self._aliases.get_name_token(location)
            for path_service in path_services:
                if typedef.is_filtered(location, path_service):
                    _logger.info('WLSDPLY-06372', typedef.get_domain_type(), path_service, class_name=_class_name,
                                 method_name=_method_name)
                else:
                    _logger.info('WLSDPLY-06356', path_service, class_name=_class_name, method_name=_method_name)
                    result[path_service] = OrderedDict()
                    location.add_name_token(name_token, path_service)
                    self._populate_model_parameters(result[path_service], location)
                    location.remove_name_token(name_token)
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
        return model_top_folder_name, result

    def get_wldf_system_resources(self):
        """
        Discover each WLDF system resource in the domain.
        :return: model name for the WLDF system resource:dictionary containing the discovered WLDF system resources
        """
        _method_name = 'get_wldf_system_resources'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        result = OrderedDict()
        model_top_folder_name = model_constants.WLDF_SYSTEM_RESOURCE
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        wldf_resources = self._find_names_in_folder(location)
        if wldf_resources is not None:
            _logger.info('WLSDPLY-06357', len(wldf_resources), class_name=_class_name, method_name=_method_name)
            typedef = self._model_context.get_domain_typedef()
            name_token = self._aliases.get_name_token(location)
            for wldf_resource in wldf_resources:
                if typedef.is_filtered(location, wldf_resource):
                    _logger.info('WLSDPLY-06362', typedef.get_domain_type(), wldf_resource, class_name=_class_name,
                                 method_name=_method_name)
                else:
                    _logger.info('WLSDPLY-06358', wldf_resource, class_name=_class_name, method_name=_method_name)
                    location.add_name_token(name_token, wldf_resource)
                    result[wldf_resource] = OrderedDict()
                    self._populate_model_parameters(result[wldf_resource], location)
                    self._discover_subfolders(result[wldf_resource], location)
                    location.remove_name_token(name_token)
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=model_top_folder_name)
        return model_top_folder_name, result

    def get_system_component_resources(self):
        """
        Discover each system component resource in the domain.
        :return: model name and dictionary for the discovered system component resources
        """
        _method_name = 'get_system_component_resources'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        name, dictionary = self._get_named_resources(model_constants.SYSTEM_COMPONENT)

        # for online, warn that any OHS configurations are not discovered
        if self._wlst_mode == WlstModes.ONLINE:
            for key, nodes in dictionary.iteritems():
                component_type = dictionary_utils.get_element(nodes, model_constants.COMPONENT_TYPE)
                if model_constants.OHS == component_type:
                    _logger.warning('WLSDPLY-06366', model_constants.OHS, model_constants.SYSTEM_COMPONENT, key,
                                    class_name=_class_name, method_name=_method_name)

        return name, dictionary

    def get_ohs_resources(self):
        """
        Discover each OHS resource in the domain.
        :return: model name and dictionary for the discovered OHS resources
        """
        _method_name = 'get_ohs_resources'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        return self._get_named_resources(model_constants.OHS)

    # private methods

    def _add_wldf_script(self, model_name, model_value, location):
        """
        Add the WLDF WatchNotification ScriptAction script for attribute PathToScript to the archive file.
        Modify the model_value to reflect the new name after the archive file has been deployed.
        :param model_name: name of the  attribute
        :param model_value: containing the Script Action script
        :param location: context containing the current location of the ScriptAction
        :return: modified model value reflecting new PathToScript location
        """
        _method_name = '_add_wldf_script'
        _logger.entering(model_name, class_name=_class_name, method_name=_method_name)
        new_script_name = model_value
        if model_value is not None:
            file_name = model_value
            if not self._model_context.is_remote():
                file_name = self._convert_path(model_value)
            _logger.info('WLSDPLY-06359', file_name, self._aliases.get_model_folder_path(location),
                         class_name=_class_name, method_name=_method_name)
            archive_file = self._model_context.get_archive_file()
            # Set model_value to None if unable to add it to archive file
            modified_name = None
            try:
                if self._model_context.is_remote():
                    new_file_name = WLSDeployArchive.getScriptArchivePath(file_name)
                    self.add_to_remote_map(file_name, new_file_name,
                                           WLSDeployArchive.ArchiveEntryType.SCRIPT.name())
                else:
                    if self._model_context.is_ssh():
                        file_name = self.download_deployment_from_remote_server(file_name,
                                                                                 self.download_temporary_dir,
                                                                                 "wldfScript")

                    modified_name = archive_file.addScript(file_name)
            except IllegalArgumentException, iae:
                _logger.warning('WLSDPLY-06360', self._aliases.get_model_folder_path(location), file_name,
                                iae.getLocalizedMessage(), class_name=_class_name,
                                method_name=_method_name)
            except WLSDeployArchiveIOException, wioe:
                de = exception_helper.create_discover_exception('WLSDPLY-06354',
                                                                self._aliases.get_model_folder_path(location),
                                                                file, wioe.getLocalizedMessage())
                _logger.throwing(class_name=_class_name, method_name=_method_name, error=de)
                raise de
            new_script_name = modified_name
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=new_script_name)
        return new_script_name

    def _get_named_resources(self, folder_name):
        """
        Discover each resource of the specified type in the domain.
        :return: model name and dictionary for the discovered resources
        """
        _method_name = '_get_named_resources'
        _logger.entering(folder_name, class_name=_class_name, method_name=_method_name)

        result = OrderedDict()
        model_top_folder_name = folder_name
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        resource_names = self._find_names_in_folder(location)
        if resource_names is not None:
            _logger.info('WLSDPLY-06364', len(resource_names), folder_name, class_name=_class_name,
                         method_name=_method_name)
            typedef = self._model_context.get_domain_typedef()
            name_token = self._aliases.get_name_token(location)
            for resource_name in resource_names:
                if typedef.is_filtered(location, resource_name):
                    _logger.info('WLSDPLY-06362', typedef.get_domain_type(), folder_name, resource_name,
                                 class_name=_class_name, method_name=_method_name)
                else:
                    _logger.info('WLSDPLY-06365', folder_name, resource_name, class_name=_class_name,
                                 method_name=_method_name)
                    location.add_name_token(name_token, resource_name)
                    result[resource_name] = OrderedDict()
                    self._populate_model_parameters(result[resource_name], location)
                    self._discover_subfolders(result[resource_name], location)
                    location.remove_name_token(name_token)
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=model_top_folder_name)
        return model_top_folder_name, result

    def _fix_passwords_in_mail_session_properties(self, mail_session_dict):
        """
        Look for password properties in the mail session properties string, and replace the password with a fix me token.
        :param mail_session_dict: containing the discovered mail session attributes
        """
        match_pattern = r'mail\.\w*\.?password'
        if model_constants.MAIL_SESSION_PROPERTIES in mail_session_dict and \
                not self._model_context.is_discover_passwords():
            # alias framework has converted properties to a dictionary by this point
            properties_dict = mail_session_dict[model_constants.MAIL_SESSION_PROPERTIES]
            for property_name in properties_dict:
                property_value = properties_dict[property_name]
                is_tokenized = property_value.startswith('@@')
                if StringUtils.matches(match_pattern, property_name) and not is_tokenized:
                    properties_dict[property_name] = PASSWORD_TOKEN
