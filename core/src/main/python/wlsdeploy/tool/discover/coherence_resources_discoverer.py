"""
Copyright (c) 2017, 2023, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from java.lang import IllegalArgumentException

from oracle.weblogic.deploy.util import PyOrderedDict as OrderedDict
from oracle.weblogic.deploy.util import WLSDeployArchive
from oracle.weblogic.deploy.util import WLSDeployArchiveIOException

from wlsdeploy.aliases import model_constants
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import COHERENCE_CACHE_CONFIG_FILE
from wlsdeploy.aliases.model_constants import COHERENCE_RUNTIME_CACHE_CONFIG_URI
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.deploy import deployer_utils
from wlsdeploy.tool.discover import discoverer
from wlsdeploy.tool.discover.discoverer import Discoverer
from wlsdeploy.util import dictionary_utils
import wlsdeploy.util.unicode_helper as str_helper

_class_name = 'CoherenceResourcesDiscoverer'
_logger = PlatformLogger(discoverer.get_discover_logger_name())


class CoherenceResourcesDiscoverer(Discoverer):
    """
    Discover the weblogic coherence resources from the domain.
    """

    def __init__(self, model_context, resource_dictionary, base_location,
                 wlst_mode=WlstModes.OFFLINE, aliases=None, credential_injector=None):
        """
        Initialize this discoverer instance with the specific information needed to discover coherence resources.
        :param model_context: context about the model for this instance of discover domain
        :param resource_dictionary: was provided on the discover call, else use initialized resources
        :param base_location: current context for discover or new context if not provided
        """
        Discoverer.__init__(self, model_context, base_location, wlst_mode, aliases, credential_injector)
        self._dictionary = resource_dictionary
        self._add_att_handler(model_constants.COHERENCE_CUSTOM_CLUSTER_CONFIGURATION,
                              self._add_custom_configuration_to_archive)
        self._add_att_handler(model_constants.COHERENCE_ACTIVE_DIRECTORY, self._add_active_directory)
        self._add_att_handler(model_constants.COHERENCE_SNAPSHOT_DIRECTORY, self._add_snapshot_directory)
        self._add_att_handler(model_constants.COHERENCE_TRASH_DIRECTORY, self._add_trash_directory)

    def discover(self):
        """
        discover the global, resource group template and partition coherence resources.
        :return: model name for coherence cluster:resources dictionary containing discovered coherence clusters
        """
        _method_name = 'discover'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        _logger.fine('WLSDPLY-06310', class_name=_class_name, method_name=_method_name)
        model_top_folder_name, result = self.get_coherence_clusters()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_top_folder_name, result)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=model_top_folder_name)
        return model_top_folder_name, self._dictionary

    def get_coherence_clusters(self):
        """
        Discover the Coherence clusters and archive the necessary coherence artifacts.
        :return: model folder name: dictionary with the discovered coherence clusters
        """
        _method_name = '_get_coherence_clusters'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        result = OrderedDict()
        model_top_folder_name = model_constants.COHERENCE_CLUSTER_SYSTEM_RESOURCE
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        coherence_clusters = self._find_names_in_folder(location)
        if coherence_clusters is not None:
            _logger.info('WLSDPLY-06311', len(coherence_clusters), class_name=_class_name, method_name=_method_name)
            typedef = self._model_context.get_domain_typedef()
            name_token = self._aliases.get_name_token(location)
            for coherence_cluster in coherence_clusters:
                if typedef.is_filtered(location, coherence_cluster):
                    _logger.info('WLSDPLY-06322', typedef.get_domain_type(), coherence_cluster, class_name=_class_name,
                                 method_name=_method_name)
                else:
                    _logger.info('WLSDPLY-06312', coherence_cluster, class_name=_class_name, method_name=_method_name)
                    location.add_name_token(name_token, coherence_cluster)
                    result[coherence_cluster] = OrderedDict()
                    self._populate_model_parameters(result[coherence_cluster], location)
                    model_subfolder_name, subfolder_result = self.get_coherence_cache_config(coherence_cluster, location)
                    discoverer.add_to_model_if_not_empty(result[coherence_cluster], model_subfolder_name,
                                                         subfolder_result)
                    model_subfolder_name, subfolder_result = self.get_coherence_resource(location)
                    discoverer.add_to_model_if_not_empty(result[coherence_cluster], model_subfolder_name,
                                                         subfolder_result)
                    location.remove_name_token(name_token)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
        return model_top_folder_name, result

    #  private methods

    def get_coherence_cache_config(self, coherence_cluster_name, location):
        """
        Discover the coherence cache config for the coherence cluster. Add coherence cluster cache config to
        archive file.
        :param coherence_cluster_name: the name of the containing CoherenceClusterSystemResource
        :param location: containing current context information for the location
        :return: model name for the coherence cache config: resource dictionary containing the discovered cache config
        """
        _method_name = '_get_coherence_cache_config'
        _logger.entering(coherence_cluster_name, str_helper.to_string(location),
                         class_name=_class_name, method_name=_method_name)
        result = OrderedDict()
        model_top_folder_name = model_constants.COHERENCE_CACHE_CONFIG
        location.append_location(model_top_folder_name)
        cache_configs = self._find_names_in_folder(location)
        if cache_configs is not None:
            name_token = self._aliases.get_name_token(location)
            attr_names = self._aliases.get_model_attribute_names(location)
            for cache_config in cache_configs:
                location.add_name_token(name_token, cache_config)

                if self._wlst_mode == WlstModes.ONLINE and COHERENCE_RUNTIME_CACHE_CONFIG_URI not in attr_names:
                    _logger.warning('WLSDPLY-06323', cache_config, coherence_cluster_name,
                                    class_name=_class_name, method_name=_method_name)
                    continue

                _logger.fine('WLSDPLY-06313', cache_config, coherence_cluster_name,
                             class_name=_class_name, method_name=_method_name)
                result[cache_config] = OrderedDict()
                self._populate_model_parameters(result[cache_config], location)
                self._workaround_cache_config_issue(coherence_cluster_name, cache_config, result[cache_config])
                self._discover_subfolders(result[cache_config], location)
                location.remove_name_token(name_token)
        location.pop_location()
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
        return model_top_folder_name, result

    def _workaround_cache_config_issue(self, cluster_name, cache_config_name, cache_config_dict):
        """
        Coherence Cache Config objects contain two attributes related to the cache config file:
        CacheConfigurationFile and RuntimeCacheConfigurationUri.  The RuntimeCacheConfigurationUri
        attribute contains the actual value of file being used by the domain while the
        CacheConfigurationFile may point to the actual file or the file used to import the one
        being used (which may no longer exist).  In either case, we only need to import the actual
        file being used and set the attribute(s) in the model to reference the imported file for
        discovery.  Create/Update also has special handling code to make sure all of this works.
        :param cache_config_dict: the cache_config dictionary object containing the discovered value
        :param cache_config_name: the name of this cache_config object.
        """
        _method_name = '_workaround_cache_config_issue'
        _logger.entering(cluster_name, cache_config_name, cache_config_dict,
                         class_name=_class_name, method_name=_method_name)

        cache_config_file_name = \
            dictionary_utils.get_element(cache_config_dict, COHERENCE_RUNTIME_CACHE_CONFIG_URI)
        if cache_config_file_name is None:
            cache_config_file_name = \
                dictionary_utils.get_element(cache_config_dict, COHERENCE_CACHE_CONFIG_FILE)

        if cache_config_file_name is not None:
            success, url, file_name = \
                self._get_from_url('Coherence Cluster %s Cache Configuration' % cluster_name, cache_config_file_name)
            archive_file = self._model_context.get_archive_file()
            if success:
                if url is not None:
                    new_name = self.get_coherence_url(cluster_name, url, archive_file)
                elif file_name is not None:
                    new_name = self.get_coherence_config_file(cluster_name, file_name, archive_file)
                else:
                    # Impossible condition
                    new_name = None
                    _logger.severe('WLSDPLY-06324', cluster_name, cache_config_name,
                                   cache_config_file_name, class_name=_class_name, method_name=_method_name)

                if new_name is not None:
                    _logger.finer('WLSDPLY-06326', cluster_name, cache_config_name,
                                  COHERENCE_RUNTIME_CACHE_CONFIG_URI, new_name,
                                  class_name=_class_name, method_name=_method_name)
                    cache_config_dict[COHERENCE_RUNTIME_CACHE_CONFIG_URI] = new_name
                    if COHERENCE_CACHE_CONFIG_FILE in cache_config_dict:
                        _logger.finer('WLSDPLY-06327', cluster_name, cache_config_name,
                                      COHERENCE_CACHE_CONFIG_FILE, cache_config_dict[COHERENCE_CACHE_CONFIG_FILE],
                                      class_name=_class_name, method_name=_method_name)
                        cache_config_dict[COHERENCE_CACHE_CONFIG_FILE] = new_name
                # else: Nothing to do because warning/error has already been logged
            # else: Nothing to do here since the warning has been logged in the _get_from_url() method
        else:
            _logger.severe('WLSDPLY-06325', cluster_name, cache_config_name,
                           class_name=_class_name, method_name=_method_name)

        _logger.exiting(class_name=_class_name, method_name=_method_name)

    def get_coherence_resource(self, location):
        """
        Discover the coherence resources for the domain. Collect custom configuration files and persistence
        directories into the archive file.
        :param location: context containing the current location information
        :return: model name for coherence resource: dictionary containing coherence resources.
        """
        _method_name = '_get_coherence_resource'
        _logger.entering(str_helper.to_string(location), class_name=_class_name, method_name=_method_name)
        result = OrderedDict()
        model_top_folder_name = model_constants.COHERENCE_RESOURCE
        location.append_location(model_top_folder_name)
        deployer_utils.set_single_folder_token(location, self._aliases)
        self._populate_model_parameters(result, location)
        self._discover_subfolders(result, location)
        location.pop_location()
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
        return model_top_folder_name, result

    # Private methods

    def _add_custom_configuration_to_archive(self, model_name, model_value, location):
        """
        Add custom configuration file to the archive. Modify the configuration file name in the model.
        :param model_name: attribute name of the custom configuration
        :param model_value: value containing the custom configuration file name
        :param location: context containing current location information
        :return: update custom configuration file name
        """
        _method_name = '_add_custom_configuration_to_archive'
        temp = LocationContext()
        temp.append_location(model_constants.COHERENCE_CLUSTER_SYSTEM_RESOURCE)
        cluster_name = location.get_name_for_token(self._aliases.get_name_token(temp))
        _logger.entering(cluster_name, model_name, model_value, class_name=_class_name, method_name=_method_name)

        custom_config_path_into_archive = model_value
        if model_value is not None:
            archive_file = self._model_context.get_archive_file()
            config_path_in_model = model_value
            if not self._model_context.is_remote():
                #  Get the actual full path
                config_path_in_model = self._convert_path(config_path_in_model, True)
                if not self._model_context.is_skip_archive():
                    try:
                        if self._model_context.is_ssh():
                            config_path_in_model = \
                                self.download_deployment_from_remote_server(config_path_in_model,
                                                                            self.download_temporary_dir,
                                                                            "coherenceCustomConfig-" + cluster_name)

                        custom_config_path_into_archive = \
                            archive_file.addCoherenceConfigFile(cluster_name, config_path_in_model)
                        _logger.finer('WLSDPLY-06315', config_path_in_model, class_name=_class_name,
                                      method_name=_method_name)
                    except (IllegalArgumentException, WLSDeployArchiveIOException), wioe:
                        _logger.warning('WLSDPLY-06316', cluster_name, config_path_in_model,
                                        wioe.getLocalizedMessage(), class_name=_class_name, method_name=_method_name)
                        custom_config_path_into_archive = None
            else:
                custom_config_path_into_archive = WLSDeployArchive.getCoherenceConfigArchivePath(cluster_name,
                                                                                    custom_config_path_into_archive)
                self.add_to_remote_map(config_path_in_model, custom_config_path_into_archive,
                                   WLSDeployArchive.ArchiveEntryType.COHERENCE_CONFIG.name())


        _logger.exiting(class_name=_class_name, method_name=_method_name, result=custom_config_path_into_archive)
        return custom_config_path_into_archive

    def get_coherence_url(self, cluster_name, url, archive_file):
        _method_name = 'get_coherence_url'
        _logger.entering(cluster_name, url, class_name=_class_name, method_name=_method_name)

        if self._model_context.is_remote():
            new_name = WLSDeployArchive.getCoherenceURLArchivePath(cluster_name, url)
            self.add_to_remote_map(url, new_name, WLSDeployArchive.ArchiveEntryType.COHERENCE_CONFIG.name())
        elif self._model_context.is_skip_archive():
            new_name = url
        else:
            try:
                new_name = archive_file.addCoherenceConfigFileFromUrl(cluster_name, url)
                _logger.info('WLSDPLY-06317', cluster_name, url, new_name, class_name=_class_name,
                             method_name=_method_name)
            except (IllegalArgumentException, WLSDeployArchiveIOException), wioe:
                _logger.warning('WLSDPLY-06328', cluster_name, 'url', url, wioe.getLocalizedMessage(),
                                error=wioe, class_name=_class_name, method_name=_method_name)
                new_name = None

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=new_name)
        return new_name

    def get_coherence_config_file(self, cluster_name, file_name, archive_file):
        _method_name = 'get_coherence_config_file'

        if self._model_context.is_remote():
            new_name = WLSDeployArchive.getCoherenceConfigArchivePath(file_name)
            self.add_to_remote_map(file_name, new_name, WLSDeployArchive.ArchiveEntryType.COHERENCE_CONFIG.name())
        elif self._model_context.is_skip_archive():
            new_name = self._convert_path(file_name, True)
        else:
            file_name = self._convert_path(file_name, True)
            try:

                if self._model_context.is_ssh():
                    file_name = self.download_deployment_from_remote_server(file_name,
                                                                             self.download_temporary_dir,
                                                                             "coherenceConfig-" + cluster_name)


                new_name = archive_file.addCoherenceConfigFile(cluster_name, file_name)
                _logger.info('WLSDPLY-06319', cluster_name, file_name, new_name,
                             class_name=_class_name, method_name=_method_name)
            except (IllegalArgumentException, WLSDeployArchiveIOException), wioe:
                _logger.warning('WLSDPLY-06328', cluster_name, 'file', file_name,  wioe.getLocalizedMessage(),
                                error=wioe, class_name=_class_name, method_name=_method_name)
                new_name = None
        return new_name

    def _add_active_directory(self, model_name, model_value, location):
        return self._add_persistence_directory(model_name, model_value, location, 'active')

    def _add_snapshot_directory(self, model_name, model_value, location):
        return self._add_persistence_directory(model_name, model_value, location, 'snapshot')

    def _add_trash_directory(self, model_name, model_value, location):
        return self._add_persistence_directory(model_name, model_value, location, 'trash')

    def _add_persistence_directory(self, model_name, model_value, location, dir_type):
        """
        Add a directory to the archive file for the type of persistence directory. Return the updated location
        of the directory after deployment of the archive file.
        :param model_name: model name for the persistence directory attribute
        :param model_value: value of the current persistence directory location
        :param location: context containing current location information
        :param dir_type: type of persistence directory used to create the new directory name in the archive
        :return: updated model value for the new persistence directory location
        """
        _method_name = '_add_persistence_directory'
        temp = LocationContext()
        temp.append_location(model_constants.COHERENCE_CLUSTER_SYSTEM_RESOURCE)
        cluster_name = location.get_name_for_token(self._aliases.get_name_token(temp))
        _logger.entering(cluster_name, model_name, model_value, class_name=_class_name, method_name=_method_name)
        new_name = model_value
        if model_value is not None:
            archive_file = self._model_context.get_archive_file()
            if self._model_context.is_remote():
                new_name = WLSDeployArchive.getCoherencePersistArchivePath(cluster_name, dir_type)
                self.add_to_remote_map(model_value, new_name,
                                      WLSDeployArchive.ArchiveEntryType.COHERENCE_PERSISTENCE_DIR.name())
            elif not self._model_context.is_skip_archive():
                try:
                    new_name = archive_file.addCoherencePersistenceDirectory(cluster_name, dir_type)
                    _logger.info('WLSDPLY-06320', cluster_name, model_value, dir_type, class_name=_class_name,
                                 method_name=_method_name)
                except WLSDeployArchiveIOException, wioe:
                    _logger.warning('WLSDPLY-06318', cluster_name, model_value, dir_type, wioe.getLocalizedMessage(),
                                    class_name=_class_name, method_name=_method_name)
                    new_name = None

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=new_name)
        return new_name
