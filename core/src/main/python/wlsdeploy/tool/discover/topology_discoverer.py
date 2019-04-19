"""
Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
from java.io import File
from java.lang import IllegalArgumentException

from oracle.weblogic.deploy.discover import DiscoverException
from oracle.weblogic.deploy.util import PyOrderedDict as OrderedDict
from oracle.weblogic.deploy.util import PyWLSTException
from oracle.weblogic.deploy.util import StringUtils
from oracle.weblogic.deploy.util import WLSDeployArchiveIOException

from wlsdeploy.aliases import model_constants
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import MODEL_LIST_DELIMITER
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.discover import discoverer
from wlsdeploy.tool.discover.discoverer import Discoverer
from wlsdeploy.util import path_utils
from wlsdeploy.util import string_utils
from wlsdeploy.util import wlst_helper

_class_name = 'TopologyDiscoverer'
_logger = PlatformLogger(discoverer.get_discover_logger_name())


class TopologyDiscoverer(Discoverer):
    """
    Discover the topology part of the model. The resulting data dictionary describes the topology of the domain,
    including clusters, servers, server templates, machines and migratable targets,
    """

    def __init__(self, model_context, topology_dictionary, base_location, wlst_mode=WlstModes.OFFLINE, aliases=None):
        """
        Instantiate an instance of the TopologyDiscoverer class with the runtime information provided by
        the init parameters.
        :param model_context: containing the arguments for this discover
        :param topology_dictionary: dictionary in which to add discovered topology information
        :param wlst_mode: indicates whether this discover is run in online or offline mode
        """
        Discoverer.__init__(self, model_context, base_location, wlst_mode, aliases)
        self._dictionary = topology_dictionary
        self._add_att_handler(model_constants.CLASSPATH, self._add_classpath_libraries_to_archive)
        self._add_att_handler(model_constants.CUSTOM_IDENTITY_KEYSTORE_FILE, self._add_keystore_file_to_archive)
        self._add_att_handler(model_constants.CUSTOM_TRUST_KEYSTORE_FILE, self._add_keystore_file_to_archive)

    def discover(self):
        """
        Discover the clusters, servers and machines that describe the domain's topology and return
        the resulting topology data dictionary. Add any pertinent libraries referenced by a server's
        start classpath to the archive file.
        :return: topology data dictionary
        """
        _method_name = 'discover'
        _logger.entering(class_name=_class_name, method_name=_method_name)

        _logger.info('WLSDPLY-06600', class_name=_class_name, method_name=_method_name)

        self.discover_domain_parameters()

        model_top_folder_name, clusters = self.get_clusters()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_top_folder_name, clusters)

        model_top_folder_name, servers = self.get_servers()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_top_folder_name, servers)

        model_top_folder_name, migratable_targets = self.get_migratable_targets()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_top_folder_name, migratable_targets)

        model_top_folder_name, templates = self.get_server_templates()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_top_folder_name, templates)

        model_top_folder_name, unix_machines = self.get_unix_machines()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_top_folder_name, unix_machines)

        model_top_folder_name, machines = self.get_machines(unix_machines)
        discoverer.add_to_model_if_not_empty(self._dictionary, model_top_folder_name, machines)

        model_top_folder_name, security_configuration = self.discover_security_configuration()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_top_folder_name, security_configuration)

        _logger.exiting(class_name=_class_name, method_name=_method_name)
        return self._dictionary

    def get_clusters(self):
        """
        Discover the Clusters in the domain.
        :return:  model name for the dictionary and the dictionary containing the cluster information
        """
        _method_name = 'get_clusters'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        result = OrderedDict()
        model_top_folder_name = model_constants.CLUSTER
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        clusters = self._find_names_in_folder(location)
        if clusters is not None:
            _logger.info('WLSDPLY-06601', len(clusters), class_name=_class_name, method_name=_method_name)
            name_token = self._alias_helper.get_name_token(location)
            for cluster in clusters:
                _logger.info('WLSDPLY-06602', cluster, class_name=_class_name, method_name=_method_name)
                location.add_name_token(name_token, cluster)
                result[cluster] = OrderedDict()
                self._populate_model_parameters(result[cluster], location)
                self._discover_subfolders(result[cluster], location)
                location.remove_name_token(name_token)
            location.pop_location()

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=model_top_folder_name)
        return model_top_folder_name, result

    def get_servers(self):
        """
        Discover Servers in the domain.
        :return: model name for the dictionary and the dictionary containing the server information
        """
        _method_name = 'get_servers'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        result = OrderedDict()
        model_top_folder_name = model_constants.SERVER
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        servers = self._find_names_in_folder(location)
        if servers is not None:
            _logger.info('WLSDPLY-06603', len(servers), class_name=_class_name, method_name=_method_name)
            name_token = self._alias_helper.get_name_token(location)
            for server in servers:
                _logger.info('WLSDPLY-06604', server, class_name=_class_name, method_name=_method_name)
                location.add_name_token(name_token, server)
                result[server] = OrderedDict()
                self._populate_model_parameters(result[server], location)
                self._discover_subfolders(result[server], location)
                location.remove_name_token(name_token)
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
        return model_top_folder_name, result

    def get_server_templates(self):
        """
        Discover Server Templates in the domain.
        :return: model name for the dictionary and the dictionary containing the server template information
        """
        _method_name = 'get_server_templates'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        result = OrderedDict()
        model_top_folder_name = model_constants.SERVER_TEMPLATE
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        templates = self._find_names_in_folder(location)
        if templates is not None:
            _logger.info('WLSDPLY-06605', len(templates), class_name=_class_name, method_name=_method_name)
            name_token = self._alias_helper.get_name_token(location)
            for template in templates:
                _logger.info('WLSDPLY-06606', template, class_name=_class_name, method_name=_method_name)
                location.add_name_token(name_token, template)
                result[template] = OrderedDict()
                self._populate_model_parameters(result[template], location)
                self._discover_subfolders(result[template], location)
                location.remove_name_token(name_token)
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
        return model_top_folder_name, result

    def get_migratable_targets(self):
        """
        Discover the migratable targets for the domain, including auto generated migratable targets for the server.
        :return: model name for the folder: dictionary containing the discovered migratable targets
        """
        _method_name = 'get_migratable_targets'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        model_top_folder_name = model_constants.MIGRATABLE_TARGET
        result = OrderedDict()
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        targets = self._find_names_in_folder(location)
        if targets is not None:
            _logger.info('WLSDPLY-06607', len(targets), class_name=_class_name, method_name=_method_name)
            name_token = self._alias_helper.get_name_token(location)
            for target in targets:
                _logger.info('WLSDPLY-06608', target, class_name=_class_name, method_name=_method_name)
                location.add_name_token(name_token, target)
                result[target] = OrderedDict()
                self._populate_model_parameters(result[target], location)
                self._discover_subfolders(result[target], location)
                location.remove_name_token(name_token)

        _logger.exiting(class_name=_class_name, method_name=_method_name)
        return model_top_folder_name, result

    def get_unix_machines(self):
        """
        Discover the Machines in the domains that represent unix machines.
        :return: dictionary with the unix machine and node manager information
        """
        _method_name = 'get_unix_machines'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        result = OrderedDict()
        model_top_folder_name = model_constants.UNIX_MACHINE
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        machines = self._find_names_in_folder(location)
        if machines is not None:
            _logger.info('WLSDPLY-06609', len(machines), class_name=_class_name, method_name=_method_name)
            name_token = self._alias_helper.get_name_token(location)
            for machine in machines:
                _logger.info('WLSDPLY-06610', machine, class_name=_class_name, method_name=_method_name)
                location.add_name_token(name_token, machine)
                result[machine] = OrderedDict()
                self._populate_model_parameters(result[machine], location)
                self._discover_subfolders(result[machine], location)
                location.remove_name_token(name_token)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
        return model_top_folder_name, result

    def get_machines(self, unix_machines=None):
        """
        Discover the Machines that the domain servers are mapped to. Remove any machines from the domain machine list
        that are contained in the unix machines dictionary. These machines are represented in a separate unix machine
        section of the model.
        :return: model name of the machine section:dictionary containing the discovered node manager information
        """
        _method_name = 'get_machines'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        if unix_machines is None:
            # did not like a mutable default value in method signature
            unix_machines = OrderedDict()
        result = OrderedDict()
        model_top_folder_name = model_constants.MACHINE
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        machines = self._find_names_in_folder(location)
        if machines is not None:
            name_token = self._alias_helper.get_name_token(location)
            for unix_machine in unix_machines:
                if unix_machine in machines:
                    machines.remove(unix_machine)
            _logger.info('WLSDPLY-06611', len(machines), class_name=_class_name, method_name=_method_name)
            for machine in machines:
                _logger.info('WLSDPLY-06612', machine, class_name=_class_name, method_name=_method_name)
                location.add_name_token(name_token, machine)
                result[machine] = OrderedDict()
                self._populate_model_parameters(result[machine], location)
                self._discover_subfolders(result[machine], location)
                location.remove_name_token(name_token)
        _logger.exiting(class_name=_class_name, method_name=_method_name)
        return model_top_folder_name, result

    def discover_domain_parameters(self):
        """
        Discover the domain attributes and non-resource domain subfolders.
        """
        _method_name = 'discover_domain_parameters'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        location = LocationContext(self._base_location)
        self._populate_model_parameters(self._dictionary, location)

        model_folder_name, folder_result = self._get_admin_console()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, folder_result)
        model_folder_name, folder_result = self._get_jta()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, folder_result)
        model_folder_name, folder_result = self._get_jmx()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, folder_result)
        model_folder_name, folder_result = self._get_restful_management_services()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, folder_result)
        model_folder_name, folder_result = self._get_log_filters()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, folder_result)
        model_folder_name, folder_result = self._get_reliable_delivery_policies()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, folder_result)
        model_folder_name, folder_result = self._get_xml_entity_caches()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, folder_result)
        model_folder_name, folder_result = self._get_xml_registries()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, folder_result)
        model_folder_name, folder_result = self._get_domain_log()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, folder_result)
        model_folder_name, folder_result = self._get_nm_properties()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, folder_result)

        _logger.exiting(class_name=_class_name, method_name=_method_name)

    def discover_security_configuration(self):
        """
        Discover the security configuration for the domain.
        :return: name for the model:dictionary containing the discovered security configuration
        """
        _method_name = 'discover_security_configuration'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        result = OrderedDict()
        model_top_folder_name = model_constants.SECURITY_CONFIGURATION
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        security_configuration = self._find_singleton_name_in_folder(location)
        if security_configuration is not None:
            _logger.info('WLSDPLY-06622', class_name=_class_name, method_name=_method_name)
            location.add_name_token(self._alias_helper.get_name_token(location), security_configuration)
            self._populate_model_parameters(result, location)
            try:
                self._discover_subfolders(result, location)
            except DiscoverException, de:
                _logger.warning('WLSDPLY-06200', self._wls_version, de.getLocalizedMessage(),
                                class_name=_class_name, method_name=_method_name)
                result = OrderedDict()
        _logger.exiting(class_name=_class_name, method_name=_method_name)
        return model_top_folder_name, result

    # Private methods

    def _get_admin_console(self):
        """
        Discover the domain level admin console configuration attributes.
        :return: model name for JTA:dictionary containing the discovered JTA attributes
        """
        _method_name = '_get_admin_console'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        model_top_folder_name = model_constants.ADMIN_CONSOLE
        result = OrderedDict()
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        name = self._find_singleton_name_in_folder(location)
        if name is not None:
            _logger.info('WLSDPLY-06613', class_name=_class_name, method_name=_method_name)
            location.add_name_token(self._alias_helper.get_name_token(location), name)
            self._populate_model_parameters(result, location)
        _logger.exiting(class_name=_class_name, method_name=_method_name)
        return model_top_folder_name, result

    def _get_jta(self):
        """
        Discover the domain level JTA configuration attributes.
        :return: model name for JTA:dictionary containing the discovered JTA attributes
        """
        _method_name = '_get_jta'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        model_top_folder_name = model_constants.JTA
        result = OrderedDict()
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        name = self._find_singleton_name_in_folder(location)
        if name is not None:
            _logger.info('WLSDPLY-06614', class_name=_class_name, method_name=_method_name)
            location.add_name_token(self._alias_helper.get_name_token(location), name)
            self._populate_model_parameters(result, location)
        _logger.exiting(class_name=_class_name, method_name=_method_name)
        return model_top_folder_name, result

    def _get_jmx(self):
        """
        Discover the JMX agents configured in the domain.
        :return: model name for JMX:dictionary containing the discovered JMX attributes
        """
        _method_name = '_get_jmx'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        model_top_folder_name = model_constants.JMX
        result = OrderedDict()
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        name = self._find_singleton_name_in_folder(location)
        if name is not None:
            _logger.info('WLSDPLY-06615', class_name=_class_name, method_name=_method_name)
            location.add_name_token(self._alias_helper.get_name_token(location), name)
            self._populate_model_parameters(result, location)
        _logger.exiting(class_name=_class_name, method_name=_method_name)
        return model_top_folder_name, result

    def _get_domain_log(self):
        """
        Discover the domain log attributes.
        :return: model name for the Log:dictionary containing the discovered Log attributes
        """
        _method_name = '_get_domain_log'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        model_top_folder_name = model_constants.LOG
        result = OrderedDict()
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        name = self._find_singleton_name_in_folder(location)
        if name is not None:
            _logger.info('WLSDPLY-06626', class_name=_class_name, method_name=_method_name)
            location.add_name_token(self._alias_helper.get_name_token(location), name)
            self._populate_model_parameters(result, location)
            self._discover_subfolders(result, location)

        return model_top_folder_name, result

    def _get_log_filters(self):
        """
        Discover the log filters that are used in the different types of Logs in the domain.
        :return: model name for the folder: dictionary containing the discovered log filters
        """
        _method_name = '_get_log_filters'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        model_top_folder_name = model_constants.LOG_FILTER
        result = OrderedDict()
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        filters = self._find_names_in_folder(location)
        if filters is not None:
            _logger.info('WLSDPLY-06628', len(filters), class_name=_class_name, method_name=_method_name)
            name_token = self._alias_helper.get_name_token(location)
            for logfilter in filters:
                _logger.info('WLSDPLY-06629', logfilter, class_name=_class_name, method_name=_method_name)
                location.add_name_token(name_token, logfilter)
                result[logfilter] = OrderedDict()
                self._populate_model_parameters(result[logfilter], location)
                location.remove_name_token(name_token)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=model_top_folder_name)
        return model_top_folder_name, result

    def _get_reliable_delivery_policies(self):
        """
        Discover the reliable delivery policies that are used for soap message delivery in the servers.
        :return: model name for the folder: dictionary containing the discovered ws reliable delivery policies
        """
        _method_name = '_get_reliable_delivery_policies'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        model_top_folder_name = model_constants.WS_RELIABLE_DELIVERY_POLICY
        result = OrderedDict()
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        policies = self._find_names_in_folder(location)
        if policies is not None:
            _logger.info('WLSDPLY-06630', len(policies), class_name=_class_name, method_name=_method_name)
            name_token = self._alias_helper.get_name_token(location)
            for policy in policies:
                _logger.info('WLSDPLY-06631', policy, class_name=_class_name, method_name=_method_name)
                location.add_name_token(name_token, policy)
                result[policy] = OrderedDict()
                self._populate_model_parameters(result[policy], location)
                location.remove_name_token(name_token)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=model_top_folder_name)
        return model_top_folder_name, result

    def _get_xml_entity_caches(self):
        """
        Discover the XML entity caches that are used by the servers in the domain.
        :return: model name for the folder: dictionary containing the discovered xml entity caches
        """
        _method_name = '_get_xml_entity_caches'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        model_top_folder_name = model_constants.XML_ENTITY_CACHE
        result = OrderedDict()
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        caches = self._find_names_in_folder(location)
        if caches is not None:
            _logger.info('WLSDPLY-06632', len(caches), class_name=_class_name, method_name=_method_name)
            name_token = self._alias_helper.get_name_token(location)
            for cache in caches:
                _logger.info('WLSDPLY-06633', cache, class_name=_class_name, method_name=_method_name)
                location.add_name_token(name_token, cache)
                result[cache] = OrderedDict()
                self._populate_model_parameters(result[cache], location)
                location.remove_name_token(name_token)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=model_top_folder_name)
        return model_top_folder_name, result

    def _get_xml_registries(self):
        """
        Discover the XML registries that are used by the servers.
        :return: model name for the folder: dictionary containing the discovered log xml registries
        """
        _method_name = '_get_xml_registries'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        model_top_folder_name = model_constants.XML_REGISTRY
        result = OrderedDict()
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        registries = self._find_names_in_folder(location)
        if registries is not None:
            _logger.info('WLSDPLY-06634', len(registries), class_name=_class_name, method_name=_method_name)
            name_token = self._alias_helper.get_name_token(location)
            for registry in registries:
                _logger.info('WLSDPLY-06635', registry, class_name=_class_name, method_name=_method_name)
                location.add_name_token(name_token, registry)
                result[registry] = OrderedDict()
                self._populate_model_parameters(result[registry], location)
                location.remove_name_token(name_token)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=model_top_folder_name)
        return model_top_folder_name, result

    def _get_nm_properties(self):
        """
        Discover the NMProperties attributes.
        :return: model name for the Log:dictionary containing the discovered NMProperties attributes
        """
        _method_name = '_get_nm_properties'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        model_top_folder_name = model_constants.NM_PROPERTIES
        result = OrderedDict()
        location = LocationContext(self._base_location)
        if self._topfolder_exists(model_top_folder_name):
            _logger.info('WLSDPLY-06627', class_name=_class_name, method_name=_method_name)
            location.append_location(model_top_folder_name)
            self._populate_model_parameters(result, location)
        _logger.exiting(class_name=_class_name, method_name=_method_name)
        return model_top_folder_name, result

    def _get_restful_management_services(self):
        """
        Discover the wlst restful management services enablement for the domain.
        :return: model name for the mbean:dictionary containing the discovered restful management services mbean
        """
        _method_name = '_get_restful_management_services'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        model_top_folder_name = model_constants.RESTFUL_MANAGEMENT_SERVICES
        result = OrderedDict()
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        name = self._find_singleton_name_in_folder(location)
        if name is not None:
            _logger.info('WLSDPLY-06616', class_name=_class_name, method_name=_method_name)
            location.add_name_token(self._alias_helper.get_name_token(location), name)
            self._populate_model_parameters(result, location)
        _logger.exiting(class_name=_class_name, method_name=_method_name)
        return model_top_folder_name, result

    def _has_machines_folder(self, base_folder):
        """
        This is a private method.

        In WLST offline, the Machine folder does not always show up even though it is there so
        this method determines whether the machines folder is really there or not.
        :param base_folder: the folder name to check
        :return: true, if the Machine folder exists, false otherwise
        """
        if base_folder in wlst_helper.lsc():
            result = True
        elif self._wlst_mode == WlstModes.OFFLINE:
            try:
                wlst_helper.cd(base_folder)
                result = True
            except PyWLSTException:
                result = False
        else:
            result = False
        return result

    def _add_classpath_libraries_to_archive(self, model_name, model_value, location):
        """
        This is a private method.

        Add the server files and directories listed in the server classpath attribute to the archive file.
        File locations in the oracle_home will be removed from the classpath and will not be added to the archive file.
        :param model_name: attribute for the server server start classpath attribute
        :param model_value: classpath value in domain
        :param location: context containing current location information
        :return model
        """
        _method_name = 'add_classpath_libraries_to_archive'
        server_name = self._get_server_name_from_location(location)
        _logger.entering(server_name, model_name, model_value, class_name=_class_name, method_name=_method_name)

        classpath_string = None
        if not StringUtils.isEmpty(model_value):
            classpath = path_utils.fixup_path(model_value)

            # model values are comma-separated
            classpath_entries = classpath.split(MODEL_LIST_DELIMITER)

            if classpath_entries:
                classpath_list = []
                for classpath_entry in classpath_entries:
                    new_source_name = self._add_library(server_name, classpath_entry)
                    if new_source_name is not None:
                        classpath_list.append(new_source_name)

                classpath_string = StringUtils.getStringFromList(classpath_list, MODEL_LIST_DELIMITER)
                _logger.fine('WLSDPLY-06617', server_name, classpath_string, class_name=_class_name,
                             method_name=_method_name)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=classpath_string)
        return classpath_string

    def _add_library(self, server_name, classpath_name):
        """
        This is a private method.

        Collect the binary and directories from the classpath string into the archive file.
        If the binary or directory cannot be collected into the archive file, the entry will remain in the
        classpath string, but a warning will be logged about the problem.
        :param server_name: for the classpath files being collected
        :param classpath_name: string containing the classpath entries
        :return: original name modified for the new location and tokenized
        """
        _method_name = '_add_library'
        _logger.entering(server_name, classpath_name, class_name=_class_name, method_name=_method_name)
        return_name = classpath_name
        if self._is_oracle_home_file(classpath_name):
            _logger.info('WLSDPLY-06618', classpath_name, server_name, class_name=_class_name, method_name=_method_name)
            return_name = self._model_context.tokenize_path(classpath_name)
        else:
            _logger.finer('WLSDPLY-06619', classpath_name, server_name, class_name=_class_name,
                          method_name=_method_name)
            archive_file = self._model_context.get_archive_file()
            file_name_path = self._convert_path(classpath_name)
            new_source_name = None
            try:
                new_source_name = archive_file.addClasspathLibrary(File(file_name_path))
            except IllegalArgumentException, iae:
                _logger.warning('WLSDPLY-06620', server_name, file_name_path, iae.getLocalizedMessage(),
                                class_name=_class_name, method_name=_method_name)
            except WLSDeployArchiveIOException, wioe:
                de = exception_helper.create_discover_exception('WLSDPLY-06621', server_name, file_name_path,
                                                                wioe.getLocalizedMessage())
                _logger.throwing(class_name=_class_name, method_name=_method_name, error=de)
                raise de
            if new_source_name is not None:
                return_name = new_source_name
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=return_name)
        return return_name

    def _add_keystore_file_to_archive(self, model_name, model_value, location):
        """
        Add the custom trust or identity keystore file to the archive.
        :param model_name: attribute name in the model
        :param model_value: converted model value for the attribute
        :param location: context containing the current location information
        :return: modified location and name for the model keystore file
        """
        _method_name = '_add_keystore_file_to_archive'
        _logger.entering(model_name, str(location), class_name=_class_name, method_name=_method_name)
        new_name = None
        if not string_utils.is_empty(model_value):
            server_name = self._get_server_name_from_location(location)
            archive_file = self._model_context.get_archive_file()
            file_path = self._convert_path(model_value)
            if server_name:
                new_name = self._add_server_keystore_file_to_archive(server_name, archive_file, file_path)
            else:
                new_name = self._add_node_manager_keystore_file_to_archive(archive_file, file_path)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=new_name)
        return new_name

    def _add_server_keystore_file_to_archive(self, server_name, archive_file, file_path):
        """
        Add the Server custom trust or identity keystore file to the archive.
        :param server_name: attribute name in the model
        :param archive_file: converted model value for the attribute
        :param file_path: context containing the current location information
        :return: modified location and name for the model keystore file
        """
        _method_name = '_add_server_keystore_file_to_archive'
        _logger.entering(server_name, archive_file, file_path, class_name=_class_name, method_name=_method_name)
        _logger.finer('WLSDPLY-06623', file_path, server_name, class_name=_class_name, method_name=_method_name)
        new_name = None

        try:
            new_name = archive_file.addServerKeyStoreFile(server_name, File(file_path))
        except IllegalArgumentException, iae:
            _logger.warning('WLSDPLY-06624', server_name, file_path, iae.getLocalizedMessage(),
                            class_name=_class_name, method_name=_method_name)
        except WLSDeployArchiveIOException, wioe:
            de = exception_helper.create_discover_exception('WLSDPLY-06625', server_name, file_path,
                                                            wioe.getLocalizedMessage())
            _logger.throwing(class_name=_class_name, method_name=_method_name, error=de)
            raise de
        return new_name

    def _add_node_manager_keystore_file_to_archive(self, archive_file, file_path):
        """
        Add the node manager custom trust or identity keystore file to the archive.
        :param archive_file: converted model value for the attribute
        :param file_path: context containing the current location information
        :return: modified location and name for the model keystore file
        """
        _method_name = '_add_node_manager_keystore_file_to_archive'
        _logger.entering(archive_file, file_path, class_name=_class_name, method_name=_method_name)
        _logger.finer('WLSDPLY-06636', file_path, class_name=_class_name, method_name=_method_name)
        new_name = None

        try:
            new_name = archive_file.addNodeManagerKeyStoreFile(File(file_path))
        except IllegalArgumentException, iae:
            _logger.warning('WLSDPLY-06637', file_path, iae.getLocalizedMessage(), class_name=_class_name,
                            method_name=_method_name)
        except WLSDeployArchiveIOException, wioe:
            de = exception_helper.create_discover_exception('WLSDPLY-06638', file_path, wioe.getLocalizedMessage())
            _logger.throwing(class_name=_class_name, method_name=_method_name, error=de)
            raise de
        return new_name

    def _get_server_name_from_location(self, location):
        """
        Retrieve the server name from the location context file.
        :param location: context containing the server information
        :return: server name
        """
        temp = LocationContext()
        temp.append_location(model_constants.SERVER)
        return location.get_name_for_token(self._alias_helper.get_name_token(temp))
