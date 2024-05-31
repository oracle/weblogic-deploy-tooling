"""
Copyright (c) 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from java.util import Properties

from oracle.weblogic.deploy.discover import DiscoverException
from oracle.weblogic.deploy.util import PyOrderedDict as OrderedDict

from wlsdeploy.aliases.alias_constants import PASSWORD_TOKEN
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import ADMIN_PASSWORD
from wlsdeploy.aliases.model_constants import ADMIN_USERNAME
from wlsdeploy.aliases.model_constants import AUTHENTICATION_PROVIDER
from wlsdeploy.aliases.model_constants import AUTHORIZER
from wlsdeploy.aliases.model_constants import CREDENTIAL_MAPPER
from wlsdeploy.aliases.model_constants import CROSS_DOMAIN
from wlsdeploy.aliases.model_constants import DEFAULT_AUTHENTICATOR
from wlsdeploy.aliases.model_constants import DEFAULT_CREDENTIAL_MAPPER
from wlsdeploy.aliases.model_constants import DEFAULT_REALM
from wlsdeploy.aliases.model_constants import DOMAIN_INFO
from wlsdeploy.aliases.model_constants import GROUP
from wlsdeploy.aliases.model_constants import REALM
from wlsdeploy.aliases.model_constants import REMOTE_RESOURCE
from wlsdeploy.aliases.model_constants import ROLE_MAPPER
from wlsdeploy.aliases.model_constants import SECURITY
from wlsdeploy.aliases.model_constants import SECURITY_CONFIGURATION
from wlsdeploy.aliases.model_constants import USER
from wlsdeploy.aliases.model_constants import WLS_USER_PASSWORD_CREDENTIAL_MAPPINGS
from wlsdeploy.aliases.model_constants import WLS_POLICIES
from wlsdeploy.aliases.model_constants import WLS_ROLES
from wlsdeploy.aliases.model_constants import XACML_AUTHORIZER
from wlsdeploy.aliases.model_constants import XACML_ROLE_MAPPER
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.exception_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.discover import discoverer
from wlsdeploy.tool.discover.discoverer import Discoverer
from wlsdeploy.tool.encrypt import encryption_utils
from wlsdeploy.util import string_utils
from wlsdeploy.util import unicode_helper as str_helper
from wlsdeploy.util.default_authenticator_ldift_helper import DefaultAuthenticatorLdift
from wlsdeploy.util.default_credential_mapper_ldift_helper import DefaultCredentialMapperLdift
from wlsdeploy.util.xacml_authorization_ldift_helper import XacmlAuthorizerLdift
from wlsdeploy.util.xacml_role_mapping_ldift_helper import XacmlRoleMapperLdift

_class_name = 'SecurityProviderDataDiscoverer'
_logger = PlatformLogger(discoverer.get_discover_logger_name())


class SecurityProviderDataDiscoverer(Discoverer):
    """
    Discover the weblogic resources that are common across global, resource group template, and
    partition resource group.

    """
    def __init__(self, model_context, model, base_location, wlst_mode=WlstModes.OFFLINE,
                 aliases=None, credential_injector=None):
        """
        The constructor
        :param model_context:
        :param model:
        :param base_location:
        :param wlst_mode:
        :param aliases:
        :param credential_injector:
        """
        Discoverer.__init__(self, model_context, base_location, wlst_mode, aliases, credential_injector)
        self._model = model
        self._domain_info_dictionary = model.get_model_domain_info()
        self._topology_dictionary = model.get_model_topology()
        self._security_provider_map = None
        self._default_realm_name = None
        self._default_realm_location = None

    def discover(self, security_provider_map):
        _method_name = 'discover'
        _logger.entering(security_provider_map, class_name=_class_name, method_name=_method_name)

        if self._wlst_mode == WlstModes.OFFLINE or self._model_context.is_remote() or \
                not self._model_context.is_discover_security_provider_data() or \
                security_provider_map is None:
            _logger.exiting(class_name=_class_name, method_name=_method_name)
            return
        else:
            self._security_provider_map = security_provider_map

        self._find_default_realm()
        self._export_tmp_directory, self._local_tmp_directory = self._create_tmp_directories('WDT-06903')

        try:
            self._discover_default_authenticator_data()
            self._discover_xacml_authorizer_data()
            self._discover_xacml_role_mapper_data()
            self._discover_default_credential_mapper_data()
        finally:
            self._clean_up_tmp_directories('WDT-06904')

        self._populate_admin_user_and_password()
        _logger.exiting(class_name=_class_name, method_name=_method_name)

    def _discover_default_authenticator_data(self):
        _method_name = '_discover_default_authenticator_data'
        _logger.entering(class_name=_class_name, method_name=_method_name)

        if not self._model_context.is_discover_default_authenticator_data() or \
                AUTHENTICATION_PROVIDER not in self._security_provider_map:
            _logger.exiting(class_name=_class_name, method_name=_method_name)
            return
        else:
            authentication_providers_map = self._security_provider_map[AUTHENTICATION_PROVIDER]

        default_authentication_provider_names = \
            _find_matching_provider_names(authentication_providers_map, DEFAULT_AUTHENTICATOR)

        if default_authentication_provider_names is not None:
            props = Properties()
            # Do not set the passwords property to cleartext since there is a bug in every pre-14.1.2
            # version that will make this generate bad hashed passwords.
            #
            # props.setProperty('passwords', 'cleartext')

            location = LocationContext(self._default_realm_location)
            location.append_location(AUTHENTICATION_PROVIDER)
            name_token = self._aliases.get_name_token(location)
            for default_authentication_provider_name in default_authentication_provider_names:
                location.add_name_token(name_token, default_authentication_provider_name)
                self._discover_default_authenticator_instance_data(location, default_authentication_provider_name, props)
                location.remove_name_token(name_token)
        else:
            _logger.info('WLSDPLY-06901', self._default_realm_name,
                         class_name=_class_name, method_name=_method_name)

        _logger.exiting(class_name=_class_name, method_name=_method_name)

    def _discover_default_authenticator_instance_data(self, location, provider_name, props):
        _method_name = '_discover_default_authenticator_instance_data'
        _logger.entering(str_helper.to_string(location), provider_name, props,
                         class_name=_class_name, method_name=_method_name)

        _logger.info('WLSDPLY-06902', provider_name, self._default_realm_name,
                     class_name=_class_name, method_name=_method_name)
        provider_mbean = self._get_provider_mbean(location)
        provider_file_name = 'DefaultAuthenticator_%s_Export.ldift' % provider_name
        export_file = self.path_helper.join(self._export_tmp_directory, provider_file_name)
        self._export_provider_data(provider_name, AUTHENTICATION_PROVIDER, DEFAULT_AUTHENTICATOR, provider_mbean,
                                   'DefaultAtn', export_file, props)

        if self._model_context.is_ssh():
            self.download_deployment_from_remote_server(export_file, self._local_tmp_directory, 'security')
            local_file = self.path_helper.local_join(self._local_tmp_directory, 'security', provider_file_name)
        else:
            local_file = export_file

        default_authenticator = \
            DefaultAuthenticatorLdift(local_file, self._model_context, self._aliases, self._credential_injector,
                                      exception_type=ExceptionType.DISCOVER,
                                      download_temporary_dir=self._local_tmp_directory)

        users = default_authenticator.get_users_dictionary()
        groups = default_authenticator.get_groups_dictionary()
        if users or groups:
            if SECURITY not in self._topology_dictionary:
                self._topology_dictionary[SECURITY] = dict()

            if users:
                self._topology_dictionary[SECURITY][USER] = users
            if groups:
                self._topology_dictionary[SECURITY][GROUP] = groups

        _logger.exiting(class_name=_class_name, method_name=_method_name)

    def _discover_xacml_authorizer_data(self):
        _method_name = '_discover_xacml_authorizer_data'
        _logger.entering(class_name=_class_name, method_name=_method_name)

        if not self._model_context.is_discover_xacml_authorizer_data() or \
            AUTHORIZER not in self._security_provider_map:
            _logger.exiting(class_name=_class_name, method_name=_method_name)
            return
        else:
            authorization_providers_map = self._security_provider_map[AUTHORIZER]

        xacml_authorization_provider_names = \
            _find_matching_provider_names(authorization_providers_map, XACML_AUTHORIZER)

        if xacml_authorization_provider_names is not None:
            props = Properties()

            location = LocationContext(self._default_realm_location)
            location.append_location(AUTHORIZER)
            name_token = self._aliases.get_name_token(location)
            for xacml_authorization_provider_name in xacml_authorization_provider_names:
                location.add_name_token(name_token, xacml_authorization_provider_name)
                self._discover_xacml_authorizer_instance_data(location, xacml_authorization_provider_name, props)
                location.remove_name_token(name_token)
        else:
            _logger.info('WLSDPLY-06901', self._default_realm_name,
                         class_name=_class_name, method_name=_method_name)

        _logger.exiting(class_name=_class_name, method_name=_method_name)

    def _discover_xacml_authorizer_instance_data(self, location, provider_name, props):
        _method_name = '_discover_xacml_authorizer_instance_data'
        _logger.entering(str_helper.to_string(location), provider_name, props,
                         class_name=_class_name, method_name=_method_name)

        _logger.info('WLSDPLY-06906', provider_name, self._default_realm_name,
                     class_name=_class_name, method_name=_method_name)
        provider_mbean = self._get_provider_mbean(location)
        provider_file_name = 'XACMLAuthorizer_%s_Export.ldift' % provider_name
        export_file = \
            self.path_helper.join(self._export_tmp_directory, provider_file_name)
        self._export_provider_data(provider_name, AUTHORIZER, XACML_AUTHORIZER, provider_mbean,
                                   'XACMLBoot', export_file, props)

        if self._model_context.is_ssh():
            self.download_deployment_from_remote_server(export_file, self._local_tmp_directory, 'security')
            local_file = self.path_helper.local_join(self._local_tmp_directory, 'security', provider_file_name)
        else:
            local_file = export_file

        xacml_authorizer = XacmlAuthorizerLdift(local_file, self._model_context, exception_type=ExceptionType.DISCOVER)
        policies_dict = xacml_authorizer.get_policies_dictionary()
        if policies_dict:
            self._domain_info_dictionary[WLS_POLICIES] = policies_dict

        _logger.exiting(class_name=_class_name, method_name=_method_name)

    def _discover_xacml_role_mapper_data(self):
        _method_name = '_discover_xacml_role_mapper_data'
        _logger.entering(class_name=_class_name, method_name=_method_name)

        if not self._model_context.is_discover_xacml_role_mapper_data() or \
                ROLE_MAPPER not in self._security_provider_map:
            _logger.exiting(class_name=_class_name, method_name=_method_name)
            return
        else:
            xacml_role_mapper_providers_map = self._security_provider_map[ROLE_MAPPER]

        xacml_role_mapper_provider_names = \
            _find_matching_provider_names(xacml_role_mapper_providers_map, XACML_ROLE_MAPPER)

        if xacml_role_mapper_provider_names is not None:
            props = Properties()

            location = LocationContext(self._default_realm_location)
            location.append_location(ROLE_MAPPER)
            name_token = self._aliases.get_name_token(location)
            for xacml_role_mapper_provider_name in xacml_role_mapper_provider_names:
                location.add_name_token(name_token, xacml_role_mapper_provider_name)
                self._discover_xacml_role_mapper_instance_data(location, xacml_role_mapper_provider_name, props)
                location.remove_name_token(name_token)
        else:
            _logger.info('WLSDPLY-06909', self._default_realm_name,
                         class_name=_class_name, method_name=_method_name)

        _logger.exiting(class_name=_class_name, method_name=_method_name)

    def _discover_xacml_role_mapper_instance_data(self, location, provider_name, props):
        _method_name = '_discover_xacml_role_mapper_instance_data'
        _logger.entering(str_helper.to_string(location), provider_name, props,
                         class_name=_class_name, method_name=_method_name)

        _logger.info('WLSDPLY-06910', provider_name, self._default_realm_name,
                     class_name=_class_name, method_name=_method_name)
        provider_mbean = self._get_provider_mbean(location)
        provider_file_name = 'XACMLRoleMapper_%s_Export.ldift' % provider_name
        export_file = \
            self.path_helper.join(self._export_tmp_directory, provider_file_name)
        self._export_provider_data(provider_name, ROLE_MAPPER, XACML_ROLE_MAPPER, provider_mbean,
                                   'XACMLBoot', export_file, props)

        if self._model_context.is_ssh():
            self.download_deployment_from_remote_server(export_file, self._local_tmp_directory, 'security')
            local_file = self.path_helper.local_join(self._local_tmp_directory, 'security', provider_file_name)
        else:
            local_file = export_file

        xacml_role_mapper = XacmlRoleMapperLdift(local_file, self._model_context, exception_type=ExceptionType.DISCOVER)
        role_mappings_dict = xacml_role_mapper.get_role_mappings_dictionary()
        if role_mappings_dict:
            self._domain_info_dictionary[WLS_ROLES] = role_mappings_dict

        _logger.exiting(class_name=_class_name, method_name=_method_name)

    def _discover_default_credential_mapper_data(self):
        _method_name = '_discover_default_credential_mapper_data'
        _logger.entering(class_name=_class_name, method_name=_method_name)

        if not self._model_context.is_discover_default_credential_mapper_data() or \
                CREDENTIAL_MAPPER not in self._security_provider_map:
            _logger.exiting(class_name=_class_name, method_name=_method_name)
            return
        else:
            default_credential_mapper_providers_map = self._security_provider_map[CREDENTIAL_MAPPER]

        default_credential_mapper_provider_names = \
            _find_matching_provider_names(default_credential_mapper_providers_map, DEFAULT_CREDENTIAL_MAPPER)

        if default_credential_mapper_provider_names is not None:
            props = Properties()
            location = LocationContext(self._default_realm_location)
            location.append_location(CREDENTIAL_MAPPER)
            name_token = self._aliases.get_name_token(location)
            for default_credential_mapper_provider_name in default_credential_mapper_provider_names:
                location.add_name_token(name_token, default_credential_mapper_provider_name)
                self._discover_default_credential_mapper_instance_data(location, default_credential_mapper_provider_name, props)
                location.remove_name_token(name_token)
        else:
            _logger.info('WLSDPLY-06913', self._default_realm_name,
                         class_name=_class_name, method_name=_method_name)

        _logger.exiting(class_name=_class_name, method_name=_method_name)

    def _discover_default_credential_mapper_instance_data(self, location, provider_name, props):
        _method_name = '_discover_default_credential_mapper_instance_data'
        _logger.entering(str_helper.to_string(location), provider_name, props,
                         class_name=_class_name, method_name=_method_name)

        _logger.info('WLSDPLY-06914', provider_name, self._default_realm_name,
                     class_name=_class_name, method_name=_method_name)
        provider_mbean = self._get_provider_mbean(location)
        provider_file_name = 'DefaultCredentialMapper_%s_Export.ldift' % provider_name
        export_file = \
            self.path_helper.join(self._export_tmp_directory, provider_file_name)
        self._export_provider_data(provider_name, CREDENTIAL_MAPPER, DEFAULT_CREDENTIAL_MAPPER, provider_mbean,
                                   'DefaultCreds', export_file, props)

        if self._model_context.is_ssh():
            self.download_deployment_from_remote_server(export_file, self._local_tmp_directory, 'security')
            local_file = self.path_helper.local_join(self._local_tmp_directory, 'security', provider_file_name)
        else:
            local_file = export_file

        credential_mapper = \
            DefaultCredentialMapperLdift(local_file, self._model_context, self._aliases, self._credential_injector,
                                         exception_type=ExceptionType.DISCOVER,
                                         download_temporary_dir=self._local_tmp_directory)
        cross_domain_credential_mappings_dict = credential_mapper.get_cross_domain_dictionary()
        remote_resource_credential_mapping_dict = credential_mapper.get_remote_resource_dictionary()

        if cross_domain_credential_mappings_dict or remote_resource_credential_mapping_dict:
            if WLS_USER_PASSWORD_CREDENTIAL_MAPPINGS not in self._domain_info_dictionary:
                self._domain_info_dictionary[WLS_USER_PASSWORD_CREDENTIAL_MAPPINGS] = OrderedDict()

            if cross_domain_credential_mappings_dict:
                self._domain_info_dictionary[WLS_USER_PASSWORD_CREDENTIAL_MAPPINGS][CROSS_DOMAIN] = \
                    cross_domain_credential_mappings_dict

            if remote_resource_credential_mapping_dict:
                self._domain_info_dictionary[WLS_USER_PASSWORD_CREDENTIAL_MAPPINGS][REMOTE_RESOURCE] = \
                    remote_resource_credential_mapping_dict

        _logger.exiting(class_name=_class_name, method_name=_method_name)

    def _populate_admin_user_and_password(self):
        _method_name = '_populate_admin_user_and_password'
        _logger.entering(class_name=_class_name, method_name=_method_name)

        if self._model_context.get_model_config().get_store_discover_admin_credentials():
            self._domain_info_dictionary[ADMIN_USERNAME] = self._model_context.get_admin_user()

            if self._model_context.is_encrypt_discovered_passwords():
                passphrase = self._model_context.get_encryption_passphrase()
                if not string_utils.is_empty(passphrase):
                    self._domain_info_dictionary[ADMIN_PASSWORD] = \
                        encryption_utils.encrypt_one_password(passphrase, self._model_context.get_admin_password())
                else:
                    _logger.warning('WLSDPLY-06915', ADMIN_PASSWORD, PASSWORD_TOKEN,
                                    class_name=_class_name, method_name=_method_name)
            else:
                self._domain_info_dictionary[ADMIN_PASSWORD] = self._model_context.get_admin_password()

            if self._credential_injector is not None:
                location = self._aliases.get_model_section_attribute_location(DOMAIN_INFO)
                self._credential_injector.check_and_tokenize(self._domain_info_dictionary, ADMIN_USERNAME, location)
                self._credential_injector.check_and_tokenize(self._domain_info_dictionary, ADMIN_PASSWORD, location)

        _logger.exiting(class_name=_class_name, method_name=_method_name)

    ###########################################################################
    #                            Utility Methods                              #
    ###########################################################################

    def _find_default_realm(self):
        _method_name = '_find_default_realm'
        _logger.entering(class_name=_class_name, method_name=_method_name)

        location = LocationContext(self._base_location)
        location.append_location(SECURITY_CONFIGURATION)
        name_token = self._aliases.get_name_token(location)
        location.add_name_token(name_token, self._model_context.get_domain_name())

        self._default_realm_name = self._find_default_realm_name(location)

        location.append_location(REALM)
        name_token = self._aliases.get_name_token(location)
        location.add_name_token(name_token, self._default_realm_name)
        self._default_realm_location = location
        _logger.exiting(class_name=_class_name, method_name=_method_name)

    def _find_default_realm_name(self, location):
        _method_name = '_find_default_realm_name'
        _logger.entering(str_helper.to_string(location), class_name=_class_name, method_name=_method_name)

        wlst_path = self._aliases.get_wlst_attributes_path(location)
        default_realm_attribute_name = self._aliases.get_wlst_attribute_name(location, DEFAULT_REALM)
        try:
            self._wlst_helper.cd(wlst_path)
            realm_mbean = self._wlst_helper.get(default_realm_attribute_name)
            realm_name = realm_mbean.getKeyProperty('Name')
        except DiscoverException, de:
            ex = exception_helper.create_discover_exception('WLSDPLY-06900', de.getLocalizedMessage(), error=de)
            _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=realm_name)
        return realm_name

    def _get_provider_mbean(self, location):
        _method_name = '_get_provider_mbean'
        _logger.entering(str_helper.to_string(location), class_name=_class_name, method_name=_method_name)

        wlst_mbean_path = self._aliases.get_wlst_attributes_path(location)
        mbean = self._wlst_helper.cd(wlst_mbean_path)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=mbean)
        return mbean

    def _export_provider_data(self, provider_name, provider_type, provider_subtype, provider_mbean,
                              export_format, export_file, export_constraints):
        _method_name = '_export_provider_data'
        _logger.entering(provider_name, provider_type, provider_subtype, provider_mbean, export_format,
                         export_file, export_constraints, class_name=_class_name, method_name=_method_name)

        self._wlst_helper.export_security_provider_data(provider_mbean, export_format, export_file, export_constraints)

        _logger.exiting(class_name=_class_name, method_name=_method_name)


def _find_matching_provider_names(providers_map, provider_subtype):
    _method_name = '_find_matching_provider_names'
    _logger.entering(providers_map, provider_subtype, class_name=_class_name, method_name=_method_name)

    matching_provider_names = list()
    for provider_name, provider_type in providers_map.iteritems():
        if provider_type == provider_subtype:
            matching_provider_names.append(provider_name)

    if len(matching_provider_names) == 0:
        matching_provider_names = None

    _logger.exiting(class_name=_class_name, method_name=_method_name, result=matching_provider_names)
    return matching_provider_names
