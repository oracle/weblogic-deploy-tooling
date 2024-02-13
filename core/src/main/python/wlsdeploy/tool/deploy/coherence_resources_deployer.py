"""
Copyright (c) 2017, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os, shutil

from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import COHERENCE_CACHE_CONFIG
from wlsdeploy.aliases.model_constants import COHERENCE_CACHE_CONFIG_FILE
from wlsdeploy.aliases.model_constants import COHERENCE_CLUSTER_SYSTEM_RESOURCE
from wlsdeploy.aliases.model_constants import COHERENCE_CUSTOM_CLUSTER_CONFIGURATION
from wlsdeploy.aliases.model_constants import COHERENCE_RESOURCE
from wlsdeploy.aliases.model_constants import COHERENCE_RUNTIME_CACHE_CONFIG_URI
from wlsdeploy.aliases.model_constants import COHERENCE_USE_CUSTOM_CLUSTER_CONFIG
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.tool.deploy.deployer import Deployer
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import unicode_helper as str_helper


class CoherenceResourcesDeployer(Deployer):
    _class_name = "CoherenceResourcesDeployer"

    def __init__(self, model, model_context, aliases, wlst_mode=WlstModes.OFFLINE):
        Deployer.__init__(self, model, model_context, aliases, wlst_mode)

    def add_coherence_cluster_system_resources(self, parent_dict, location):
        coherence_clusters = dictionary_utils.get_dictionary_element(parent_dict, COHERENCE_CLUSTER_SYSTEM_RESOURCE)
        self._add_named_elements(COHERENCE_CLUSTER_SYSTEM_RESOURCE, coherence_clusters, location)

        # For online mode, we are currently using the MBean's importCustomClusterConfigurationFile()
        # operation which handles copying the file to where it needs to be.  That code is in
        # attribute_setter.py
        #
        # For offline, we are unable to do this as we go from the overriden set_attributes() method below
        # since it does not have access to the CoherenceClusterSystemResource-level model dictionary...
        #
        if self.wlst_mode == WlstModes.OFFLINE:
            self._make_coh_cluster_custom_config_available(coherence_clusters)

    # Override
    def set_attributes(self, location, model_nodes, excludes=None):
        _method_name = 'set_attributes'
        model_type, model_name = self.aliases.get_model_type_and_name(location)
        if model_type != COHERENCE_CACHE_CONFIG:
            Deployer.set_attributes(self, location, model_nodes, excludes)
            return

        cluster_location = LocationContext(location)
        cluster_location.pop_location()
        cluster_name_token = self.aliases.get_name_token(cluster_location)
        cluster_name = location.get_name_tokens()[cluster_name_token]

        # Only need to special case the handling of CacheConfigurationFile and RuntimeCacheConfigurationUri
        #
        self.logger.fine('WLSDPLY-09414', cluster_name, model_name,
                         class_name=self._class_name, method_name=_method_name)
        if self.wlst_mode == WlstModes.OFFLINE:
            model_nodes_copy = self._fix_up_cache_config_file(location, cluster_name, model_name, model_nodes)
            Deployer.set_attributes(self, location, model_nodes_copy)
        else:
            Deployer.set_attributes(self, location, model_nodes)
            model_nodes_copy = self._fix_up_cache_config_file(location, cluster_name, model_name, model_nodes)
            self._import_cache_config_file(location, cluster_name, model_name, model_nodes_copy)

    #
    # This code is used by both online and offline to get the cache config file-related settings
    # to the desired value for processing.
    #
    def _fix_up_cache_config_file(self, location, cluster_name, cache_config_name, cache_config_dict):
        _method_name = '_fix_up_cache_config_file'
        self.logger.entering(str_helper.to_string(location), cluster_name, cache_config_name,
                             class_name=self._class_name, method_name=_method_name)

        # Is the RuntimeCacheConfigurationUri visible with this WLS version and WLST mode?
        attribute_names = self.aliases.get_model_attribute_names(location)
        has_runtime_attribute = COHERENCE_RUNTIME_CACHE_CONFIG_URI in attribute_names
        self.logger.fine('WLSDPLY-09423', location.get_folder_path(), attribute_names, has_runtime_attribute,
                         class_name=self._class_name, method_name=_method_name)

        #
        # To handle existing domains that were created incorrectly, we have to determine the use case regarding
        # the RuntimeCacheConfigurationUri value:
        #
        # 1. Is a path into the extracted archive directory: Fix up the path so that the server accepts it
        # 2. Is a relative path not into the archive directory: Assume that the path is correct and do nothing
        # 3. Is an absolute path: Assume that the path is correct and do nothing
        # 4. Is not set: Look at the CacheConfigurationFile attribute, determine the correct value (using the
        #    rules from 1, 2, and 3), and set RuntimeCacheConfigurationUri to the same value
        #
        result = cache_config_dict.copy()
        use_cache_config_file = True
        if has_runtime_attribute:
            runtime_cache_config_uri = result[COHERENCE_RUNTIME_CACHE_CONFIG_URI]

            if runtime_cache_config_uri is not None and not self.archive_helper.is_path_into_archive(runtime_cache_config_uri):
                # Use cases 2 and 3
                self.logger.fine('WLSDPLY-09416', cluster_name, cache_config_name, runtime_cache_config_uri,
                                 class_name=self._class_name, method_name=_method_name)
                self.logger.exiting(class_name=self._class_name, method_name=_method_name)
                return cache_config_dict

            if runtime_cache_config_uri is not None:
                # Use case 1
                domain_home = self.model_context.get_domain_home()
                result[COHERENCE_RUNTIME_CACHE_CONFIG_URI] = self.path_helper.join(domain_home, runtime_cache_config_uri)
                use_cache_config_file = False

        if use_cache_config_file:
            # Use case 4
            cache_configuration_file = result[COHERENCE_CACHE_CONFIG_FILE]
            self.logger.fine('WLSDPLY-09417', cluster_name, cache_config_name, cache_configuration_file,
                             class_name=self._class_name, method_name=_method_name)
            if cache_configuration_file is None:
                self.logger.notification('WLSDPLY-09418', cluster_name, cache_config_name,
                                         class_name=self._class_name, method_name=_method_name)
                self.logger.exiting(class_name=self._class_name, method_name=_method_name)
                return cache_config_dict
            elif self.path_helper.is_absolute_path(cache_configuration_file):
                value_to_use = cache_configuration_file
                self.logger.fine('WLSDPLY-09419', cluster_name, cache_config_name, cache_configuration_file,
                                 class_name=self._class_name, method_name=_method_name)
            elif self.archive_helper.is_path_into_archive(cache_configuration_file):
                domain_home = self.model_context.get_domain_home()
                value_to_use = os.path.join(domain_home, cache_configuration_file)
                self.logger.fine('WLSDPLY-09420', cluster_name, cache_config_name, cache_configuration_file,
                                 value_to_use, class_name=self._class_name, method_name=_method_name)
            else:
                self.logger.fine('WLSDPLY-09421', cluster_name, cache_config_name, cache_configuration_file,
                                 class_name=self._class_name, method_name=_method_name)
                value_to_use = cache_configuration_file

            result[COHERENCE_RUNTIME_CACHE_CONFIG_URI] = value_to_use

        self.logger.exiting(class_name=self._class_name, method_name=_method_name)
        return result

    # This code only runs in online mode.
    def _import_cache_config_file(self, location, cluster_name, cache_config_name, cache_config_dict):
        _method_name = '_import_cache_config_file'
        self.logger.entering(location, cluster_name, cache_config_name,
                             class_name=self._class_name, method_name=_method_name)

        # Is the RuntimeCacheConfigurationUri visible with this WLS version?
        attribute_names = self.aliases.get_model_attribute_names(location)
        has_runtime_attribute = COHERENCE_RUNTIME_CACHE_CONFIG_URI in attribute_names

        cache_configuration_file = cache_config_dict[COHERENCE_CACHE_CONFIG_FILE]
        if has_runtime_attribute:
            cache_configuration_file = cache_config_dict[COHERENCE_RUNTIME_CACHE_CONFIG_URI]

        if cache_configuration_file is None:
            return

        cache_config_mbean = self.wlst_helper.get_cmo()
        if cache_config_mbean is not None:
            try:
                self.logger.info("WLSDPLY-09415", cache_configuration_file, cluster_name, cache_config_name,
                                 class_name=self._class_name, method_name=_method_name)
                cache_config_mbean.importCacheConfigurationFile(cache_configuration_file)
            except Exception,ex:
                message = exception_helper.get_error_message_from_exception(ex)
                self.logger.severe("WLSDPLY-09422", cache_configuration_file, cluster_name, cache_config_name, message,
                                   error=ex, class_name=self._class_name, method_name=_method_name)
        self.logger.exiting(class_name=self._class_name, method_name=_method_name)

    def _make_coh_cluster_custom_config_available(self, coherence_clusters):
        # The coherence cluster custom configuration file must be within the config/coherence/<cluster>
        # We will copy the config file over, at this point the model's attribute value is still the original value

        _method_name = '_make_coh_cluster_custom_config_available'
        domain_home = self.model_context.get_domain_home()

        for coherence_cluster_name in coherence_clusters:
            cluster_dict = coherence_clusters[coherence_cluster_name]
            use_custom_config = dictionary_utils.get_boolean_element(cluster_dict, COHERENCE_USE_CUSTOM_CLUSTER_CONFIG)
            if use_custom_config:
                try:
                    self._copy_custom_config_file_to_destination(cluster_dict, coherence_cluster_name, domain_home)
                except Exception, e:
                    message = exception_helper.get_error_message_from_exception(e)
                    ex = exception_helper.create_deploy_exception('WLSDPLY-09406', e, message)
                    self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                    raise ex

    def _copy_custom_config_file_to_destination(self, cluster_dict, coherence_cluster_name, domain_home):
        _method_name = '_copy_custom_config_file_to_destination'
        self.logger.entering(coherence_cluster_name, domain_home, class_name=self._class_name, method_name=_method_name)

        coh_resource = dictionary_utils.get_dictionary_element(cluster_dict, COHERENCE_RESOURCE)
        if coh_resource:
            model_path = dictionary_utils.get_element(coh_resource, COHERENCE_CUSTOM_CLUSTER_CONFIGURATION)

            if isinstance(model_path, (str, unicode)) and len(model_path) > 0:
                coh_cluster_config_path = \
                    self.path_helper.join(domain_home, 'config', 'coherence', coherence_cluster_name)
                if self.model_context.is_ssh():
                    self.logger.fine("WLSDPLY-09425", model_path, coh_cluster_config_path,
                                     class_name=self._class_name, method_name=_method_name)
                else:
                    self.logger.fine("WLSDPLY-09407", model_path, coh_cluster_config_path,
                                     class_name=self._class_name, method_name=_method_name)
                    if not os.path.exists(coh_cluster_config_path):
                        self.logger.finer("WLSDPLY-09408", coh_cluster_config_path,
                                          class_name=self._class_name, method_name=_method_name)
                        os.mkdir(coh_cluster_config_path)

                config_filepath = \
                    self._get_custom_cluster_config_filepath(model_path, coh_cluster_config_path, domain_home)
                self._move_custom_cluster_config_file(model_path, config_filepath, coh_cluster_config_path)

        self.logger.exiting(class_name=self._class_name, method_name=_method_name)

    def _get_custom_cluster_config_filepath(self, model_path, coh_cluster_config_path, domain_home):
        _method_name = '_get_custom_cluster_config_filepath'
        self.logger.entering(model_path, coh_cluster_config_path, domain_home,
                             class_name=self._class_name, method_name=_method_name)

        if self.archive_helper.is_path_into_archive(model_path):
            # this is the extracted path from the archive
            if self.model_context.is_ssh():
                config_filepath = self.path_helper.local_join(self.upload_temporary_dir, model_path)
            else:
                config_filepath = self.path_helper.local_join(domain_home, model_path)
        elif self.path_helper.is_absolute_local_path(model_path):
            # absolute path
            config_filepath = model_path
        else:
            # what to do with a relative path that is not in the exploded Archive location?
            coh_domain_config_path_prefix = self.path_helper.local_join(domain_home, 'config')
            self.logger.info("WLSDPLY-09411", model_path, coh_domain_config_path_prefix,
                             class_name=self._class_name, method_name=_method_name)
            config_filepath = self.path_helper.local_join(coh_domain_config_path_prefix, model_path)

        self.logger.exiting(class_name=self._class_name, method_name=_method_name, result=config_filepath)
        return config_filepath

    def _move_custom_cluster_config_file(self, model_path, config_filepath, coh_cluster_config_path):
        """
        Move the Coherence custom cluster config file into place.

        :param model_path:              the path from the model
        :param config_filepath:         the local path to the file
        :param coh_cluster_config_path: the target directory
        """
        _method_name = '_move_custom_cluster_config_file'
        self.logger.entering(model_path, config_filepath, coh_cluster_config_path,
                             class_name=self._class_name, method_name=_method_name)

        if os.path.exists(config_filepath):
            if self.model_context.is_ssh():
                self.logger.info("WLSDPLY-09424", config_filepath, coh_cluster_config_path,
                                 class_name=self._class_name, method_name=_method_name)
                self.model_context.get_ssh_context().create_directories_if_not_exist(coh_cluster_config_path)
                self.model_context.get_ssh_context().upload(config_filepath, coh_cluster_config_path)
            elif config_filepath.startswith(coh_cluster_config_path + "/"):
                self.logger.info("WLSDPLY-09412", config_filepath, coh_cluster_config_path,
                                 class_name=self._class_name, method_name=_method_name)
            else:
                self.logger.fine("WLSDPLY-09409", config_filepath, coh_cluster_config_path,
                                 class_name=self._class_name, method_name=_method_name)
                shutil.copy(config_filepath, coh_cluster_config_path)
                if self.archive_helper.is_path_into_archive(model_path):
                    self.logger.info("WLSDPLY-09410", config_filepath, coh_cluster_config_path,
                                     class_name=self._class_name, method_name=_method_name)
                    os.remove(config_filepath)
        else:
            self.logger.warning("WLSDPLY-09413", model_path, config_filepath,
                                class_name=self._class_name, method_name=_method_name)

        self.logger.exiting(class_name=self._class_name, method_name=_method_name)