"""
Copyright (c) 2017, 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from java.lang import IllegalArgumentException

from oracle.weblogic.deploy.discover import DiscoverException
from oracle.weblogic.deploy.util import PyOrderedDict as OrderedDict
from oracle.weblogic.deploy.util import PyRealBoolean
from oracle.weblogic.deploy.util import PyWLSTException
from oracle.weblogic.deploy.util import StringUtils
from oracle.weblogic.deploy.util import WLSDeployArchive
from oracle.weblogic.deploy.util import WLSDeployArchiveIOException

from wlsdeploy.aliases import alias_utils
from wlsdeploy.aliases import model_constants
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import MODEL_LIST_DELIMITER
from wlsdeploy.aliases.model_constants import KSS_KEYSTORE_FILE_INDICATOR
from wlsdeploy.aliases.model_constants import UNIX_MACHINE_ATTRIBUTE
from wlsdeploy.aliases.validation_codes import ValidationCodes
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.exception_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.discover import discoverer
from wlsdeploy.tool.discover.discoverer import Discoverer
from wlsdeploy.tool.util.saml2_security_helper import Saml2SecurityHelper
from wlsdeploy.tool.util.variable_injector import VARIABLE_SEP
from wlsdeploy.tool.util.wlst_helper import WlstHelper
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import string_utils
import wlsdeploy.util.unicode_helper as str_helper


_class_name = 'TopologyDiscoverer'
_logger = PlatformLogger(discoverer.get_discover_logger_name())

# these are used to correct unreliable isSet() results
DOMAIN_INHERITED_DEFAULT_MAPPINGS = {
    "/Server/AdministrationPort": "AdministrationPort",
    "/Server/AdministrationPortEnabled": "AdministrationPortEnabled",
    "/Server/AdministrationProtocol": "AdministrationProtocol",
    "/Server/ListenPortEnabled": "ListenPortEnabled",
    "/Server/SSL/Enabled": "SSLEnabled",
    "/ServerTemplate/AdministrationPort": "AdministrationPort",
    "/ServerTemplate/AdministrationPortEnabled": "AdministrationPortEnabled",
    "/ServerTemplate/AdministrationProtocol": "AdministrationProtocol",
    "/ServerTemplate/ListenPortEnabled": "ListenPortEnabled",
    "/ServerTemplate/SSL/Enabled": "SSLEnabled",
}

class TopologyDiscoverer(Discoverer):
    """
    Discover the topology part of the model. The resulting data dictionary describes the topology of the domain,
    including clusters, servers, server templates, machines and migratable targets,
    """

    def __init__(self, model_context, topology_dictionary, base_location,
                 wlst_mode=WlstModes.OFFLINE, aliases=None, credential_injector=None):
        """
        Instantiate an instance of the TopologyDiscoverer class with the runtime information provided by
        the init parameters.
        :param model_context: containing the arguments for this discover
        :param topology_dictionary: dictionary in which to add discovered topology information
        :param wlst_mode: indicates whether this discover is run in online or offline mode
        """
        Discoverer.__init__(self, model_context, base_location, wlst_mode, aliases, credential_injector)
        self._dictionary = topology_dictionary
        self._add_att_handler(model_constants.CLASSPATH, self._add_classpath_libraries_to_archive)
        self._add_att_handler(model_constants.CREATE_TABLE_DDL_FILE,
                              self._add_jdbc_transaction_log_create_table_ddl_file_to_archive)
        self._add_att_handler(model_constants.CUSTOM_IDENTITY_KEYSTORE_FILE, self._add_keystore_file_to_archive)
        self._add_att_handler(model_constants.CUSTOM_TRUST_KEYSTORE_FILE, self._add_keystore_file_to_archive)

        self._add_att_handler(model_constants.ADMINISTRATION_PORT, self._handle_inherited_default)
        self._add_att_handler(model_constants.ADMINISTRATION_PORT_ENABLED, self._handle_inherited_default)
        self._add_att_handler(model_constants.ADMINISTRATION_PROTOCOL, self._handle_inherited_default)
        self._add_att_handler(model_constants.LISTEN_PORT_ENABLED, self._handle_inherited_default)
        self._add_att_handler(model_constants.ENABLED, self._handle_inherited_default)

        self._wlst_helper = WlstHelper(ExceptionType.DISCOVER)

        self._domain_inherited_values = None  # lazy load if needed for unreliable isSet()

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

        current_tree = None
        if self._wlst_mode == WlstModes.ONLINE:
            current_tree = self._wlst_helper.current_tree()
            self._wlst_helper.edit()

        try:
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

            # make sure this is after discovery of machines / node managers as we will do some massaging
            model_top_folder_name, security_configuration = self.discover_security_configuration()
            discoverer.add_to_model_if_not_empty(self._dictionary, model_top_folder_name, security_configuration)

            model_top_folder_name, embedded_ldap_configuration = self.get_embedded_ldap_configuration()
            discoverer.add_to_model_if_not_empty(self._dictionary, model_top_folder_name, embedded_ldap_configuration)

            model_folder_name, folder_result = self._get_log_filters()
            discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, folder_result)

            model_folder_name, folder_result = self._get_reliable_delivery_policies()
            discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, folder_result)

            model_folder_name, folder_result = self._get_virtual_hosts()
            discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, folder_result)

            model_folder_name, folder_result = self._get_xml_entity_caches()
            discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, folder_result)

            model_folder_name, folder_result = self._get_xml_registries()
            discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, folder_result)

            model_folder_name, folder_result = self._get_ws_securities()
            discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, folder_result)

            model_top_folder_name, callouts = self.get_callouts()
            discoverer.add_to_model_if_not_empty(self._dictionary, model_top_folder_name, callouts)
        finally:
            if current_tree is not None:
                current_tree()

        saml2_security_helper = Saml2SecurityHelper(self._model_context,
                                                    ExceptionType.DISCOVER)
        saml2_security_helper.discover_initialization_files(self._model_context.get_archive_file(), self)

        _logger.exiting(class_name=_class_name, method_name=_method_name)
        return self._dictionary, self._security_provider_map

    def get_callouts(self):
        """
        Discover the Callouts in the domain.
        :return:  model name for the dictionary and the dictionary containing the cluster information
        """
        _method_name = 'get_callouts'
        _logger.entering(class_name=_class_name, method_name=_method_name)

        result = OrderedDict()
        model_top_folder_name = model_constants.CALLOUT
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        callouts = self._find_names_in_folder(location)
        if callouts is not None:
            _logger.info('WLSDPLY-06671', len(callouts), class_name=_class_name, method_name=_method_name)
            typedef = self._model_context.get_domain_typedef()
            name_token = self._aliases.get_name_token(location)
            for callout in callouts:
                if typedef.is_filtered(location, callout):
                    _logger.info('WLSDPLY-06673', typedef.get_domain_type(), callout, class_name=_class_name,
                                 method_name=_method_name)
                else:
                    _logger.info('WLSDPLY-06672', callout, class_name=_class_name, method_name=_method_name)
                    location.add_name_token(name_token, callout)
                    result[callout] = OrderedDict()
                    self._populate_model_parameters(result[callout], location)
                    location.remove_name_token(name_token)
            location.pop_location()

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=model_top_folder_name)
        return model_top_folder_name, result


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
            typedef = self._model_context.get_domain_typedef()
            name_token = self._aliases.get_name_token(location)
            for cluster in clusters:
                if typedef.is_filtered(location, cluster):
                    _logger.info('WLSDPLY-06657', typedef.get_domain_type(), cluster, class_name=_class_name,
                                 method_name=_method_name)
                else:
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
            typedef = self._model_context.get_domain_typedef()
            name_token = self._aliases.get_name_token(location)
            for server in servers:
                if typedef.is_filtered(location, server):
                    _logger.info('WLSDPLY-06658', typedef.get_domain_type(), server, class_name=_class_name,
                                 method_name=_method_name)
                else:
                    location.add_name_token(name_token, server)
                    if not self._dynamic_server(server, location):
                        _logger.info('WLSDPLY-06604', server, class_name=_class_name, method_name=_method_name)
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
            typedef = self._model_context.get_domain_typedef()
            name_token = self._aliases.get_name_token(location)
            for template in templates:
                if typedef.is_filtered(location, template):
                    _logger.info('WLSDPLY-06659', typedef.get_domain_type(), template, class_name=_class_name,
                                 method_name=_method_name)
                else:
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
            typedef = self._model_context.get_domain_typedef()
            name_token = self._aliases.get_name_token(location)
            for target in targets:
                if typedef.is_filtered(location, target):
                    _logger.info('WLSDPLY-06659', typedef.get_domain_type(), target, class_name=_class_name,
                                 method_name=_method_name)
                else:
                    if not self._dynamic_target(target, location):
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
            typedef = self._model_context.get_domain_typedef()
            name_token = self._aliases.get_name_token(location)
            for machine in machines:
                if typedef.is_filtered(location, machine):
                    _logger.info('WLSDPLY-06660', typedef.get_domain_type(), machine, class_name=_class_name,
                                 method_name=_method_name)
                else:
                    location.add_name_token(name_token, machine)
                    wlst_path = self._aliases.get_wlst_attributes_path(location)
                    self.wlst_cd(wlst_path, location)
                    wlst_lsa_params = self._get_attributes_for_current_location(location)
                    if UNIX_MACHINE_ATTRIBUTE not in wlst_lsa_params:
                        location.remove_name_token(name_token)
                        continue
                    _logger.info('WLSDPLY-06610', machine, class_name=_class_name, method_name=_method_name)
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
            name_token = self._aliases.get_name_token(location)
            for unix_machine in unix_machines:
                if unix_machine in machines:
                    machines.remove(unix_machine)
            typedef = self._model_context.get_domain_typedef()
            _logger.info('WLSDPLY-06611', len(machines), class_name=_class_name, method_name=_method_name)
            for machine in machines:
                if typedef.is_filtered(location, machine):
                    _logger.info('WLSDPLY-06661', typedef.get_domain_type(), machine, class_name=_class_name,
                                 method_name=_method_name)
                else:
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
        domain_home = '/'
        location = LocationContext(self._base_location)
        # This is temporary until a do not ignore is created for DomainName
        success, wlst_value = self._get_attribute_value_with_get(model_constants.DOMAIN_NAME, domain_home)
        if success and wlst_value:
            self._dictionary[model_constants.DOMAIN_NAME] = wlst_value

        self._populate_model_parameters(self._dictionary, location)

        model_folder_name, folder_result = self.discover_domain_mbean(model_constants.ADMIN_CONSOLE)
        discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, folder_result)
        model_folder_name, folder_result = self.discover_domain_mbean(model_constants.ALLOW_LIST)
        discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, folder_result)
        model_folder_name, folder_result = self.discover_domain_mbean(model_constants.CDI_CONTAINER)
        discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, folder_result)
        model_folder_name, folder_result = self.discover_domain_mbean(model_constants.JMX)
        discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, folder_result)
        model_folder_name, folder_result = self.discover_domain_mbean(model_constants.JPA)
        discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, folder_result)
        model_folder_name, folder_result = self.discover_domain_mbean(model_constants.JTA)
        discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, folder_result)
        model_folder_name, folder_result = self.discover_domain_mbean(model_constants.LOG)
        discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, folder_result)
        model_folder_name, folder_result = self._get_nm_properties()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, folder_result)
        model_folder_name, folder_result = self.discover_domain_mbean(model_constants.REMOTE_CONSOLE_HELPER)
        discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, folder_result)
        model_folder_name, folder_result = self.discover_domain_mbean(model_constants.RESTFUL_MANAGEMENT_SERVICES)
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
            location.add_name_token(self._aliases.get_name_token(location), security_configuration)
            self._populate_model_parameters(result, location)
            self._massage_security_credential(result, location)
            #Security Configuration has 2 subfolders, SecureMode and Realm
            #Realm needs to be handled with special code, so discover SecureMode manually
            location.append_location(model_constants.SECURE_MODE)
            secure_mode = self._find_singleton_name_in_folder(location)
            if secure_mode is not None:
                location.add_name_token(self._aliases.get_name_token(location), secure_mode)
                secure_mode = OrderedDict()
                self._populate_model_parameters(secure_mode, location)
                if len(secure_mode) > 0:
                    result[model_constants.SECURE_MODE] = secure_mode
            location.pop_location()
            location.append_location(model_constants.REALM)
            result[model_constants.REALM] = OrderedDict()
            realms = self._find_names_in_folder(location)
            for realm in realms:
                name_token = self._aliases.get_name_token(location)
                location.add_name_token(name_token, realm)
                result[model_constants.REALM][realm] = OrderedDict()
                self._populate_model_parameters(result[model_constants.REALM][realm], location)
                if realm == 'myrealm':
                    check_order=True
                else:
                    check_order=False
                try:
                    self._discover_subfolders(result[model_constants.REALM][realm], location, check_order)
                    location.remove_name_token(name_token)
                except DiscoverException, de:
                    wlst_path = self._aliases.get_wlst_attributes_path(location)
                    _logger.warning('WLSDPLY-06200', wlst_path, self._wls_version, de.getLocalizedMessage(),
                                    class_name=_class_name, method_name=_method_name, error=de)
                    result = OrderedDict()

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=model_top_folder_name)
        return model_top_folder_name, self._slim_security_config(result)

    def _slim_security_config(self, sc_dict):
        """
        Check the default realm 'myrealm' for any customization. Remove the parts of the SecurityConfiguration that
        are defaulted to the way installed by the WLS template. If the entire SecurityConfiguration is the default,
        remove the SecurityConfiguration section.
        :param sc_dict: SecurityConfiguration section of model
        :return: converted_dictionary with defaults removed
        """
        realm_dict = dictionary_utils.get_dictionary_element(sc_dict, model_constants.REALM)
        if 'myrealm' in realm_dict and dictionary_utils.is_empty_dictionary_element(realm_dict, 'myrealm'):
            del sc_dict[model_constants.REALM]['myrealm']
        if model_constants.REALM in sc_dict and \
                dictionary_utils.is_empty_dictionary_element(sc_dict, model_constants.REALM):
            del sc_dict[model_constants.REALM]
        return sc_dict

    def get_embedded_ldap_configuration(self):
        """
        Get the Embedded LDAP server configuration for the domain and only return the configuration
        when there are non-default settings other than the credential value.
        :return: name for the model:dictionary containing the discovered Embedded LDAP configuration
        """
        _method_name = 'get_embedded_ldap_configuration'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        result = OrderedDict()
        model_top_folder_name = model_constants.EMBEDDED_LDAP
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        embedded_ldap_configuration = self._find_singleton_name_in_folder(location)
        if embedded_ldap_configuration is not None:
            location.add_name_token(self._aliases.get_name_token(location), embedded_ldap_configuration)
            self._populate_model_parameters(result, location)
            # IFF credential is the only attribute, skip adding the Embedded LDAP server configuration
            if not self._model_context.is_discover_passwords():
                if len(result) == 1 and model_constants.CREDENTIAL_ENCRYPTED in result:
                    injector = self._get_credential_injector()
                    if injector is not None:
                        injector.remove_from_cache(location, model_constants.CREDENTIAL_ENCRYPTED)
                    result = OrderedDict()
                    _logger.info('WLSDPLY-06639', class_name=_class_name, method_name=_method_name)
                else:
                    _logger.info('WLSDPLY-06640', class_name=_class_name, method_name=_method_name)
            else:
                _logger.info('WLSDPLY-06640', class_name=_class_name, method_name=_method_name)

        _logger.exiting(class_name=_class_name, method_name=_method_name)
        return model_top_folder_name, result

    # Private methods

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
            typedef = self._model_context.get_domain_typedef()
            name_token = self._aliases.get_name_token(location)
            for logfilter in filters:
                if typedef.is_filtered(location, logfilter):
                    _logger.info('WLSDPLY-06662', typedef.get_domain_type(), logfilter, class_name=_class_name,
                                 method_name=_method_name)
                else:
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
            typedef = self._model_context.get_domain_typedef()
            name_token = self._aliases.get_name_token(location)
            for policy in policies:
                if typedef.is_filtered(location, policy):
                    _logger.info('WLSDPLY-06663', typedef.get_domain_type(), policy, class_name=_class_name,
                                 method_name=_method_name)
                else:
                    _logger.info('WLSDPLY-06631', policy, class_name=_class_name, method_name=_method_name)
                    location.add_name_token(name_token, policy)
                    result[policy] = OrderedDict()
                    self._populate_model_parameters(result[policy], location)
                    location.remove_name_token(name_token)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=model_top_folder_name)
        return model_top_folder_name, result

    def _get_virtual_hosts(self):
        """
        Discover the virtual hosts that are present in the domain.
        :return: model name for the folder: dictionary containing the discovered virtual hosts
        """
        _method_name = '_get_virtual_hosts'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        model_top_folder_name = model_constants.VIRTUAL_HOST
        result = OrderedDict()
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        vhosts = self._find_names_in_folder(location)
        if vhosts is not None:
            _logger.info('WLSDPLY-06647', len(vhosts), class_name=_class_name, method_name=_method_name)
            typedef = self._model_context.get_domain_typedef()
            name_token = self._aliases.get_name_token(location)
            for vhost in vhosts:
                if typedef.is_filtered(location, vhost):
                    _logger.info('WLSDPLY-06664', typedef.get_domain_type(), vhost, class_name=_class_name,
                                 method_name=_method_name)
                else:
                    _logger.info('WLSDPLY-06648', vhost, class_name=_class_name, method_name=_method_name)
                    location.add_name_token(name_token, vhost)
                    result[vhost] = OrderedDict()
                    self._populate_model_parameters(result[vhost], location)
                    self._discover_subfolders(result[vhost], location)
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
            typedef = self._model_context.get_domain_typedef()
            name_token = self._aliases.get_name_token(location)
            for cache in caches:
                if typedef.is_filtered(location, cache):
                    _logger.info('WLSDPLY-06665', typedef.get_domain_type(), cache, class_name=_class_name,
                                 method_name=_method_name)
                else:
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
            typedef = self._model_context.get_domain_typedef()
            name_token = self._aliases.get_name_token(location)
            for registry in registries:
                if typedef.is_filtered(location, registry):
                    _logger.info('WLSDPLY-06666', typedef.get_domain_type(), registry, class_name=_class_name,
                                 method_name=_method_name)
                else:
                    _logger.info('WLSDPLY-06635', registry, class_name=_class_name, method_name=_method_name)
                    location.add_name_token(name_token, registry)
                    result[registry] = OrderedDict()
                    self._populate_model_parameters(result[registry], location)
                    location.remove_name_token(name_token)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=model_top_folder_name)
        return model_top_folder_name, result

    def _get_ws_securities(self):
        """
        Discover the Webservice Security configuration for the domain
        :return: model name for the folder: dictionary containing the discovered webservice security
        """
        _method_name = '_get_ws_securities'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        model_top_folder_name = model_constants.WEB_SERVICE_SECURITY
        result = OrderedDict()
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        wssecurities = self._find_names_in_folder(location)
        if wssecurities is not None:
            _logger.info('WLSDPLY-06649', len(wssecurities), class_name=_class_name, method_name=_method_name)
            typedef = self._model_context.get_domain_typedef()
            name_token = self._aliases.get_name_token(location)
            for wssecurity in wssecurities:
                if typedef.is_filtered(location, wssecurity):
                    _logger.info('WLSDPLY-06670', typedef.get_domain_type(), wssecurity, class_name=_class_name,
                                 method_name=_method_name)
                else:
                    _logger.info('WLSDPLY-06650', wssecurity, class_name=_class_name, method_name=_method_name)
                    location.add_name_token(name_token, wssecurity)
                    result[wssecurity] = OrderedDict()
                    self._populate_model_parameters(result[wssecurity], location)
                    self._discover_subfolders(result[wssecurity], location)
                    location.remove_name_token(name_token)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=model_top_folder_name)
        return model_top_folder_name, result

    def _massage_security_credential(self, result, location):
        _method_name = 'massage_security_credential'
        # Determine if the SecurityConfiguration/CredentialEncrypted can be removed
        pass_cache = OrderedDict()
        short_name = ''
        if self._credential_injector is not None:
            pass_cache = self._credential_injector.get_variable_cache()
            short_name = self._credential_injector.get_folder_short_name(location)
        if model_constants.SECURITY_CONFIGURATION_PASSWORD in result:
            # default is false
            cd_enabled_raw = dictionary_utils.get_element(result, model_constants.SECURITY_CONFIGURATION_CD_ENABLED)
            cd_enabled = alias_utils.convert_boolean(cd_enabled_raw)
            if not cd_enabled:
                # Hard code it here or hard code it later. The target code will bypass tokenize of variable
                cache_name = short_name + VARIABLE_SEP + model_constants.SECURITY_CONFIGURATION_PASSWORD
                if cache_name in pass_cache:
                    del pass_cache[cache_name]
                del result[model_constants.SECURITY_CONFIGURATION_PASSWORD]
                _logger.fine('WLSDPLY-06616', class_name=_class_name, method_name=_method_name)
            else:
                _logger.finer('WLSDPLY-06615', class_name=_class_name, method_name=_method_name)
        # Determine if the SecurityConfiguration/NodeManagerEncryptedPassword can be removed
        if model_constants.SECURITY_CONFIGURATION_NM_PASSWORD in result:
            if model_constants.MACHINE in self._dictionary or model_constants.UNIX_MACHINE in self._dictionary:
                _logger.finer('WLSDPLY-06645', class_name=_class_name, method_name=_method_name)
            else:
                cache_name = short_name + VARIABLE_SEP + model_constants.SECURITY_CONFIGURATION_NM_PASSWORD
                if cache_name in pass_cache:
                    del pass_cache[cache_name]
                del result[model_constants.SECURITY_CONFIGURATION_NM_PASSWORD]
                _logger.finer('WLSDPLY-06646', class_name=_class_name, method_name=_method_name)

    def _has_machines_folder(self, base_folder):
        """
        This is a private method.

        In WLST offline, the Machine folder does not always show up even though it is there so
        this method determines whether the machines folder is really there or not.
        :param base_folder: the folder name to check
        :return: true, if the Machine folder exists, false otherwise
        """
        if base_folder in self._wlst_helper.lsc():
            result = True
        elif self._wlst_mode == WlstModes.OFFLINE:
            try:
                self._wlst_helper.cd(base_folder)
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
        :param model_name: attribute for the server's server start classpath attribute
        :param model_value: classpath value in domain
        :param location: context containing current location information
        :return model
        """
        _method_name = 'add_classpath_libraries_to_archive'
        server_name = self._get_server_name_from_location(location)
        _logger.entering(server_name, model_name, model_value, class_name=_class_name, method_name=_method_name)

        classpath_string = None
        if not StringUtils.isEmpty(model_value):
            # model values are comma-separated
            classpath_entries = model_value.split(MODEL_LIST_DELIMITER)

            if classpath_entries:
                classpath_list = []
                for classpath_entry in classpath_entries:
                    classpath_entry = self._model_context.replace_token_string(classpath_entry)
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
        if self._is_file_to_exclude_from_archive(classpath_name):
            _logger.info('WLSDPLY-06618', classpath_name, server_name, class_name=_class_name, method_name=_method_name)
            return_name = self._model_context.tokenize_path(classpath_name)
        else:
            _logger.finer('WLSDPLY-06619', classpath_name, server_name, class_name=_class_name,
                          method_name=_method_name)
            archive_file = self._model_context.get_archive_file()
            file_name_path = classpath_name
            if not self._model_context.is_remote():
                file_name_path = self._convert_path(classpath_name)
            new_source_name = None
            if self._model_context.is_remote():
                new_source_name = WLSDeployArchive.getClasspathArchivePath(file_name_path)
                self.add_to_remote_map(file_name_path, new_source_name,
                                       WLSDeployArchive.ArchiveEntryType.CLASSPATH_LIB.name())
            elif not self._model_context.is_skip_archive():
                try:
                    if self._model_context.is_ssh():
                        file_name_path = self.download_deployment_from_remote_server(file_name_path,
                                                                                      self.download_temporary_dir,
                                                                                      "classPathLibraries")
                    new_source_name = archive_file.addClasspathLibrary(file_name_path)
                except IllegalArgumentException, iae:
                    _logger.warning('WLSDPLY-06620', server_name, file_name_path, iae.getLocalizedMessage(),
                                    class_name=_class_name, method_name=_method_name, error=iae)
                except WLSDeployArchiveIOException, wioe:
                    de = exception_helper.create_discover_exception('WLSDPLY-06621', server_name, file_name_path,
                                                                    wioe.getLocalizedMessage(), error=wioe)
                    _logger.throwing(class_name=_class_name, method_name=_method_name, error=de)
                    raise de

            if new_source_name is not None:
                return_name = new_source_name
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=return_name)
        return return_name

    def _add_jdbc_transaction_log_create_table_ddl_file_to_archive(self, model_name, model_value, location):
        """
        Add JDBC transaction log's create table DDL file to the archive.
        :param model_name: attribute name in the model
        :param model_value: converted model value for the attribute
        :param location: context containing the current location information
        :return: modified location and name for the model create table DDL file
        """
        _method_name = '_add_jdbc_transaction_log_create_table_ddl_file_to_archive'
        _logger.entering(model_name, model_value, str_helper.to_string(location),
                         class_name=_class_name, method_name=_method_name)

        new_name = None
        if not string_utils.is_empty(model_value):
            entity_type, entity_name = self._get_server_or_template_name_from_location(location)
            archive_file = self._model_context.get_archive_file()

            if self._model_context.is_skip_archive():
                new_name = model_value
            elif self._model_context.is_remote():
                new_name = WLSDeployArchive.getScriptArchivePath(model_value)
                self.add_to_remote_map(model_value, new_name, WLSDeployArchive.ArchiveEntryType.SCRIPT.name())
            else:
                file_path = self._convert_path(model_value)
                try:
                    if self._model_context.is_ssh():
                        file_path = \
                            self.download_deployment_from_remote_server(file_path, self.download_temporary_dir,
                                                                        "jdbcTXLogCreateTableDDLFile-%s" % entity_name)

                    new_name = archive_file.addScript(file_path)
                except IllegalArgumentException, iae:
                    _logger.warning('WLSDPLY-06674', file_path, entity_type, entity_name, iae.getLocalizedMessage(),
                                    class_name=_class_name, method_name=_method_name, error=iae)
                except WLSDeployArchiveIOException, wioe:
                    de = exception_helper.create_discover_exception('WLSDPLY-06675', file_path, entity_type,
                                                                    entity_name, wioe.getLocalizedMessage(), error=wioe)
                    _logger.throwing(class_name=_class_name, method_name=_method_name, error=de)
                    raise de

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=new_name)
        return new_name

    def _add_keystore_file_to_archive(self, model_name, model_value, location):
        """
        Add the custom trust or identity keystore file to the archive.
        :param model_name: attribute name in the model
        :param model_value: converted model value for the attribute
        :param location: context containing the current location information
        :return: modified location and name for the model keystore file
        """
        _method_name = '_add_keystore_file_to_archive'
        _logger.entering(model_name, str_helper.to_string(location), class_name=_class_name, method_name=_method_name)
        new_name = None
        if not string_utils.is_empty(model_value):
            _logger.finer('WLSDPLY-06641', location.get_folder_path(), model_value,
                          class_name=_class_name, method_name=_method_name)
            if _kss_file_type(model_value):
                _logger.warning('WLSDPLY-06642', model_value, location.get_folder_path(),
                                class_name=_class_name, method_name=_method_name)
            else:
                entity_type, entity_name = self._get_server_or_template_name_from_location(location)
                archive_file = self._model_context.get_archive_file()
                file_path = model_value
                if not self._model_context.is_remote():
                    file_path = self._convert_path(model_value)

                if entity_type in [model_constants.SERVER, model_constants.SERVER_TEMPLATE]:
                    new_name = self._add_server_keystore_file_to_archive(model_name, entity_type, entity_name, file_path)
                else:
                    new_name = self._add_node_manager_keystore_file_to_archive(archive_file, file_path)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=new_name)
        return new_name

    def _add_server_keystore_file_to_archive(self, attribute_name, server_type, server_name, file_path):
        """
        Add the Server custom trust or identity keystore file to the archive.
        :param attribute_name: The name of the attribute in the server
        :param server_type: the type of the server (Server or ServerTemplate)
        :param server_name: the name of the server whose attribute refers to the file
        :param file_path: context containing the current location information
        :return: modified location and name for the model keystore file
        """
        _method_name = '_add_server_keystore_file_to_archive'
        _logger.entering(server_name, file_path, class_name=_class_name, method_name=_method_name)
        _logger.finer('WLSDPLY-06623', file_path, server_type, server_name, class_name=_class_name,
                      method_name=_method_name)
        new_name = file_path

        archive_type = WLSDeployArchive.ArchiveEntryType.SERVER_KEYSTORE
        if server_type == model_constants.SERVER_TEMPLATE:
            archive_type = WLSDeployArchive.ArchiveEntryType.SERVER_TEMPLATE_KEYSTORE

        if self._model_context.is_remote():
            new_name = WLSDeployArchive.getArchiveTypeEntryPath(archive_type, server_name, file_path)
            self.add_to_remote_map(file_path, new_name, archive_type.name())
        elif not self._model_context.is_skip_archive():
            try:
                if self._model_context.is_ssh():
                    file_path = self.download_deployment_from_remote_server(file_path, self.download_temporary_dir,
                                                                            "keyStoreFile-%s" % server_name)

                archive_file = self._model_context.get_archive_file()
                if server_type == model_constants.SERVER_TEMPLATE:
                    new_name = archive_file.addServerTemplateKeyStoreFile(server_name, file_path)
                else:
                    new_name = archive_file.addServerKeyStoreFile(server_name, file_path)
            except IllegalArgumentException, iae:
                _logger.warning('WLSDPLY-06624', attribute_name, file_path, server_type, server_name,
                                iae.getLocalizedMessage(), class_name=_class_name, method_name=_method_name, error=iae)
            except WLSDeployArchiveIOException, wioe:
                de = exception_helper.create_discover_exception(
                    'WLSDPLY-06625', attribute_name, file_path, server_type, server_name,
                    wioe.getLocalizedMessage(), error=wioe)
                _logger.throwing(class_name=_class_name, method_name=_method_name, error=de)
                raise de

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=new_name)
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
        if self._model_context.is_remote():
            new_name = WLSDeployArchive.getNodeManagerKeyStoreArchivePath(file_path)
            self.add_to_remote_map(file_path, new_name,
                                   WLSDeployArchive.ArchiveEntryType.NODE_MANAGER_KEY_STORE.name())

        elif not self._model_context.is_skip_archive():
            try:
                if self._model_context.is_ssh():
                    file_path = self.download_deployment_from_remote_server(file_path, self.download_temporary_dir,
                                                                            "nodeManagerKeyStore")
                new_name = archive_file.addNodeManagerKeyStoreFile(file_path)
            except IllegalArgumentException, iae:
                _logger.warning('WLSDPLY-06637', file_path, iae.getLocalizedMessage(), class_name=_class_name,
                                method_name=_method_name, error=iae)
            except WLSDeployArchiveIOException, wioe:
                de = exception_helper.create_discover_exception('WLSDPLY-06638', file_path, wioe.getLocalizedMessage(),
                                                                error=wioe)
                _logger.throwing(class_name=_class_name, method_name=_method_name, error=de)
                raise de

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=new_name)
        return new_name

    def _handle_inherited_default(self, model_name, model_value, location):
        """
        An att_handler that checks against defaults that are inherited from the domain level.
        If the defaults match, None will be returned, and the attribute will be removed from the model.
        This is only for cases where the results from WLST offline isSet() are unreliable (WLS 14.1.2).
        :param model_name: the name of the attribute
        :param model_value: the calculated value for the model
        :param location: the location of the attribute
        :return: the revised attribute for the model
        """
        _method_name = '_handle_inherited_default'
        result = model_value
        offline = self._wlst_mode == WlstModes.OFFLINE
        if offline and self._weblogic_helper.are_offline_inherited_defaults_calculated():
            model_path = location.get_folder_path() + '/' + model_name
            domain_attribute = dictionary_utils.get_element(DOMAIN_INHERITED_DEFAULT_MAPPINGS, model_path)
            if domain_attribute is not None:
                domain_values = self._get_domain_inherited_values()
                domain_value = dictionary_utils.get_element(domain_values, domain_attribute)
                if isinstance(model_value, PyRealBoolean):
                    model_value = model_value.getValue()
                if domain_value == model_value:
                    _logger.fine('WLSDPLY-06678', model_path, model_value, domain_attribute,
                                 domain_value, class_name=_class_name, method_name=_method_name)
                    result = None  # remove from model
        return result

    def _get_domain_inherited_values(self):
        """
        Returns a map of domain attributes and their values for use as default values
        to compare with attributes whose WLST offline isSet() values are unreliable (WLS 14.1.2).
        Lazy load this map the first time this method is called.
        :return: a map of domain attributes and their values
        """
        if not self._domain_inherited_values:
            self._domain_inherited_values = {}
            attribute_map = self._wlst_helper.lsa('/')
            for domain_attribute in DOMAIN_INHERITED_DEFAULT_MAPPINGS.values():
                if domain_attribute not in self._domain_inherited_values:
                    attribute_value = dictionary_utils.get_element(attribute_map, domain_attribute)
                    self._domain_inherited_values[domain_attribute] = attribute_value
        return self._domain_inherited_values

    def _get_server_name_from_location(self, location):
        """
        Retrieve the server name from the location context.
        :param location: context containing the server information
        :return: server name
        """
        temp = LocationContext()
        temp.append_location(model_constants.SERVER)
        return location.get_name_for_token(self._aliases.get_name_token(temp))

    def _get_server_or_template_name_from_location(self, location):
        """
        Retrieve the name for the server or server template from the location context.
        :param location: context containing either a server ot server template information
        :return: the name of the server or server template
        """
        location_folders = location.get_model_folders()
        temp = LocationContext()
        if location_folders[0] == model_constants.SERVER:
            entity_type = model_constants.SERVER
            temp.append_location(model_constants.SERVER)
        else:
            entity_type = model_constants.SERVER_TEMPLATE
            temp.append_location(model_constants.SERVER_TEMPLATE)
        entity_name = location.get_name_for_token(self._aliases.get_name_token(temp))
        return entity_type, entity_name

    def _dynamic_target(self, target, location):
        """
        Determine if the Migratable Target is connected to a dynamic server. This is determined in online mode
        only when the dynamic server and dynamic migratable target are created.
        :param target: migratable target to test for connection to dynamic server
        :param location: current location context
        :return: True if a dynamic server Migratable Target
        """
        if target.endswith('(migratable)'):
            server_name = target.split('(migratable)')[0].strip()
            server_location = LocationContext()
            server_location.append_location(model_constants.SERVER)
            server_location.add_name_token(self._aliases.get_name_token(server_location), server_name)
            wlst_path = self._aliases.get_wlst_attributes_path(server_location)
            if self._wlst_helper.path_exists(wlst_path):
                return self._dynamic_server(server_name, server_location)
        return False

    def _dynamic_server(self, server, location):
        """
        If this is online discover, determine if the server is part of a dynamic cluster.
        :param server: name of the server
        :param location: current location of the server
        :return: True if dynamic server
        """
        _method_name = '_dynamic_server'
        if self._wlst_mode == WlstModes.ONLINE and self._weblogic_helper.is_dynamic_clusters_supported():
            wlst_path = self._aliases.get_wlst_attributes_path(location)
            self._wlst_helper.cd(wlst_path)
            cluster_attr = self._aliases.get_wlst_attribute_name(location, model_constants.CLUSTER)
            cluster = self._wlst_helper.get(cluster_attr)
            if cluster is not None:
                __, cluster_name = self._aliases.get_model_attribute_name_and_value(location, cluster_attr, cluster)
                cluster_location = LocationContext()
                cluster_location.append_location(model_constants.CLUSTER)
                cluster_location.add_name_token(self._aliases.get_name_token(cluster_location), cluster_name)
                cluster_location.append_location(model_constants.DYNAMIC_SERVERS)
                cluster_location.add_name_token(self._aliases.get_name_token(cluster_location), cluster_name)
                wlst_path = self._aliases.get_wlst_attributes_path(cluster_location)
                if self._wlst_helper.path_exists(wlst_path):
                    _logger.fine('WLSDPLY-06613', server, class_name=_class_name, method_name=_method_name)
                    self._wlst_helper.cd(wlst_path)
                    present, __ = self._aliases.is_valid_model_attribute_name(location,
                                                                              model_constants.DYNAMIC_CLUSTER_SIZE)
                    if present == ValidationCodes.VALID:
                        attr_name = self._aliases.get_wlst_attribute_name(cluster_location,
                                                                          model_constants.DYNAMIC_CLUSTER_SIZE)
                    else:
                        attr_name = self._aliases.get_wlst_attribute_name(cluster_location,
                                                                          model_constants.MAX_DYNAMIC_SERVER_COUNT)
                    dynamic_size = self._wlst_helper.get(attr_name)

                    attr_name = self._aliases.get_wlst_attribute_name(cluster_location,
                                                                      model_constants.SERVER_NAME_PREFIX)
                    prefix = self._wlst_helper.get(attr_name)
                    starting = 1
                    present, __ = self._aliases.is_valid_model_attribute_name(location,
                                                                              model_constants.SERVER_NAME_START_IDX)
                    if present == ValidationCodes.VALID:
                        attr_name = self._aliases.get_model_attribute_name(cluster_location,
                                                                           model_constants.SERVER_NAME_START_IDX)
                        starting = self._wlst_helper.get(attr_name)
                    return check_against_server_list(server, dynamic_size, prefix, starting)
        _logger.finer('WLSDPLY-06614', server, class_name=_class_name, method_name=_method_name)
        return False


def check_against_server_list(server_name, dynamic_size, prefix, starting):
    if dynamic_size > 0 and prefix is not None and server_name.startswith(prefix):
        split_it = server_name.split(prefix)
        if len(split_it) == 2:
            number = StringUtils.stringToInteger(split_it[1].strip())
            if number is not None and starting <= number < (dynamic_size + starting):
                return True
    return False


def _kss_file_type(file_name):
    if file_name.startswith(KSS_KEYSTORE_FILE_INDICATOR):
        return True
    return False
