"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""

from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import ACTIVE_TYPE
from wlsdeploy.aliases.model_constants import ADJUDICATOR
from wlsdeploy.aliases.model_constants import AUDITOR
from wlsdeploy.aliases.model_constants import AUTHENTICATION_PROVIDER
from wlsdeploy.aliases.model_constants import AUTHORIZER
from wlsdeploy.aliases.model_constants import CERT_PATH_PROVIDER
from wlsdeploy.aliases.model_constants import CREDENTIAL_MAPPER
from wlsdeploy.aliases.model_constants import DEFAULT_ADJUDICATOR_NAME
from wlsdeploy.aliases.model_constants import DEFAULT_ADJUDICATOR_TYPE
from wlsdeploy.aliases.model_constants import DEFAULT_AUDITOR_NAME
from wlsdeploy.aliases.model_constants import DEFAULT_AUDITOR_TYPE
from wlsdeploy.aliases.model_constants import DEFAULT_AUTHENTICATOR_NAME
from wlsdeploy.aliases.model_constants import DEFAULT_AUTHENTICATOR_TYPE
from wlsdeploy.aliases.model_constants import DEFAULT_AUTHORIZER_NAME
from wlsdeploy.aliases.model_constants import DEFAULT_AUTHORIZER_TYPE
from wlsdeploy.aliases.model_constants import DEFAULT_CERT_PATH_PROVIDER_NAME
from wlsdeploy.aliases.model_constants import DEFAULT_CERT_PATH_PROVIDER_TYPE
from wlsdeploy.aliases.model_constants import DEFAULT_CREDENTIAL_MAPPER_NAME
from wlsdeploy.aliases.model_constants import DEFAULT_CREDENTIAL_MAPPER_TYPE
from wlsdeploy.aliases.model_constants import DEFAULT_IDENTITY_ASSERTER_NAME
from wlsdeploy.aliases.model_constants import DEFAULT_IDENTITY_ASSERTER_TYPE
from wlsdeploy.aliases.model_constants import DEFAULT_PASSWORD_VALIDATOR_NAME
from wlsdeploy.aliases.model_constants import DEFAULT_PASSWORD_VALIDATOR_TYPE
from wlsdeploy.aliases.model_constants import DEFAULT_ROLE_MAPPER_NAME
from wlsdeploy.aliases.model_constants import DEFAULT_ROLE_MAPPER_TYPE
from wlsdeploy.aliases.model_constants import PASSWORD_VALIDATOR
from wlsdeploy.aliases.model_constants import REALM
from wlsdeploy.aliases.model_constants import ROLE_MAPPER
from wlsdeploy.aliases.model_constants import SECURITY_CONFIGURATION
from wlsdeploy.tool.create.creator import Creator
from wlsdeploy.tool.deploy import deployer_utils
from wlsdeploy.tool.util.alias_helper import AliasHelper
from wlsdeploy.tool.util.wlst_helper import WlstHelper
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util.weblogic_helper import WebLogicHelper


class SecurityProviderCreator(Creator):
    """
    The class that drives security provider creation and updates.
    Shared by create domain and update domain.
    """
    __class_name = 'SecurityProviderHelper'

    def __init__(self, model_dictionary, model_context, aliases, exception_type, logger):
        Creator.__init__(self, model_dictionary, model_context, aliases, exception_type, logger)

        self.logger = logger
        self.alias_helper = AliasHelper(aliases, self.logger, exception_type)
        self.wlst_helper = WlstHelper(self.logger, exception_type)
        self.wls_helper = WebLogicHelper(self.logger)

        self._topology = self.model.get_model_topology()

        #
        # Creating domains with the wls.jar template is busted for pre-12.1.2 domains with regards to the
        # names of the default authentication providers (both the DefaultAuthenticator and the
        # DefaultIdentityAsserter names are 'Provider', making it impossible to work with in WLST.  If
        # the WLS version is earlier than fix this as part of domain creation...
        #
        self.__fix_default_authentication_provider_names = \
            self.wls_helper.do_default_authentication_provider_names_need_fixing()
        return

    def create_security_configuration(self, location):
        """
        Create the /SecurityConfiguration folder objects, if any.
        :param location: the location to use
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = '__create_security_configuration'

        self.logger.entering(str(location), class_name=self.__class_name, method_name=_method_name)
        security_configuration_nodes = dictionary_utils.get_dictionary_element(self._topology, SECURITY_CONFIGURATION)

        # in WLS 11g, the SecurityConfiguration mbean is not created until the domain is written.
        # if missing, we will create it to initialize realm and default security providers.
        config_location = LocationContext(location).append_location(SECURITY_CONFIGURATION)
        existing_names = deployer_utils.get_existing_object_list(config_location, self.alias_helper)
        if len(existing_names) == 0:
            mbean_type, mbean_name = self.alias_helper.get_wlst_mbean_type_and_name(config_location)
            self.wlst_helper.create(mbean_name, mbean_type)

        self.__handle_default_security_providers(location, security_configuration_nodes)
        if len(security_configuration_nodes) > 0:
            self._create_mbean(SECURITY_CONFIGURATION, security_configuration_nodes, location, log_created=True)
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def __handle_default_security_providers(self, base_location, security_configuration_dict):
        _method_name = '__handle_default_security_providers'

        self.logger.entering(str(base_location), class_name=self.__class_name, method_name=_method_name)
        location = self.__get_default_realm_location()
        if security_configuration_dict is None or len(security_configuration_dict) == 0:
            if self.__fix_default_authentication_provider_names:
                self.__handle_default_authentication_providers(location)
            self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
            return

        if REALM in security_configuration_dict and 'myrealm' in security_configuration_dict[REALM]:
            myrealm = security_configuration_dict[REALM]['myrealm']
            if ADJUDICATOR in myrealm:
                adj_providers = myrealm[ADJUDICATOR]
                self.__handle_default_adjudicators(location, adj_providers)
            if AUDITOR in myrealm:
                audit_providers = myrealm[AUDITOR]
                self.__handle_default_auditors(location, audit_providers)
            if AUTHENTICATION_PROVIDER in myrealm:
                atn_providers = myrealm[AUTHENTICATION_PROVIDER]
                self.__handle_default_authentication_providers(location, atn_providers)
            elif self.__fix_default_authentication_provider_names:
                self.__handle_default_authentication_providers(location)
            if AUTHORIZER in myrealm:
                atz_providers = myrealm[AUTHORIZER]
                self.__handle_default_authorizers(location, atz_providers)
            if CERT_PATH_PROVIDER in myrealm:
                cert_path_providers = myrealm[CERT_PATH_PROVIDER]
                self.__handle_default_cert_path_providers(location, cert_path_providers)
            if CREDENTIAL_MAPPER in myrealm:
                credential_mapping_providers = myrealm[CREDENTIAL_MAPPER]
                self.__handle_default_credential_mappers(location, credential_mapping_providers)
            if PASSWORD_VALIDATOR in myrealm:
                password_validation_providers = myrealm[PASSWORD_VALIDATOR]
                self.__handle_default_password_validators(location, password_validation_providers)
            if ROLE_MAPPER in myrealm:
                role_mapping_providers = myrealm[ROLE_MAPPER]
                self.__handle_default_role_mappers(location, role_mapping_providers)
        elif self.__fix_default_authentication_provider_names:
            self.__handle_default_authentication_providers(location)

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def __get_default_realm_location(self):
        """
        Ensure that the default realm exists and get the location object for it.
        :return: the location object to use to work on the default realm while creating a domain.
        """
        location = LocationContext().append_location(SECURITY_CONFIGURATION)

        # SecurityConfiguration is special since the subfolder name does not change when
        # you change the domain name.  It only changes once the domain is written and re-read...
        token_name = self.alias_helper.get_name_token(location)
        if token_name is not None:
            existing_names = deployer_utils.get_existing_object_list(location, self.alias_helper)
            if len(existing_names) > 0:
                domain_name = existing_names[0]
                location.add_name_token(token_name, domain_name)

        wlst_create_path = self.alias_helper.get_wlst_create_path(location)
        self.wlst_helper.cd(wlst_create_path)
        existing_folder_names = self.wlst_helper.get_existing_object_list(wlst_create_path)

        wlst_type, wlst_name = self.alias_helper.get_wlst_mbean_type_and_name(location)
        wlst_attribute_path = self.alias_helper.get_wlst_attributes_path(location)
        if wlst_type not in existing_folder_names:
            self.wlst_helper.create_and_cd(self.alias_helper, wlst_type, wlst_name, location, wlst_create_path)
        else:
            self.wlst_helper.cd(wlst_attribute_path)

        existing_folder_names = self.wlst_helper.get_existing_object_list(wlst_attribute_path)
        location.append_location(REALM)
        wlst_type = self.alias_helper.get_wlst_mbean_type(location)
        token_name = self.alias_helper.get_name_token(location)

        if wlst_type not in existing_folder_names:
            self.__default_security_realm_name = self.wls_helper.get_default_security_realm_name()
            if token_name is not None:
                location.add_name_token(token_name, self.__default_security_realm_name)
            wlst_name = self.alias_helper.get_wlst_mbean_name(location)
            self.wlst_helper.create_and_cd(self.alias_helper, wlst_type, wlst_name, location)
        else:
            wlst_list_path = self.alias_helper.get_wlst_list_path(location)
            existing_folder_names = self.wlst_helper.get_existing_object_list(wlst_list_path)
            if len(existing_folder_names) > 0:
                self.__default_security_realm_name = existing_folder_names[0]
            if token_name is not None:
                location.add_name_token(token_name, self.__default_security_realm_name)
            wlst_attribute_path = self.alias_helper.get_wlst_attributes_path(location)
            self.wlst_helper.cd(wlst_attribute_path)
        return location

    def __handle_default_adjudicators(self, base_location, adj_providers):
        if adj_providers is None or len(adj_providers) == 0 or DEFAULT_ADJUDICATOR_NAME is None:
            return

        if self.__need_to_delete_default_provider(adj_providers, DEFAULT_ADJUDICATOR_NAME, DEFAULT_ADJUDICATOR_TYPE):
            self.__delete_provider(base_location, DEFAULT_ADJUDICATOR_NAME, ADJUDICATOR)
        return

    def __handle_default_auditors(self, base_location, audit_providers):
        if audit_providers is None or len(audit_providers) == 0 or DEFAULT_AUDITOR_NAME is None:
            return

        if self.__need_to_delete_default_provider(audit_providers, DEFAULT_AUDITOR_NAME, DEFAULT_AUDITOR_TYPE):
            self.__delete_provider(base_location, DEFAULT_AUDITOR_NAME, AUDITOR)
        return

    def __handle_default_authentication_providers(self, base_location, atn_providers=None):
        _method_name = '__handle_default_authentication_providers'

        self.logger.entering(str(base_location), class_name=self.__class_name, method_name=_method_name)
        if atn_providers is None or len(atn_providers) == 0 or \
                (DEFAULT_AUTHENTICATOR_NAME is None and DEFAULT_IDENTITY_ASSERTER_NAME is None):
            if self.__fix_default_authentication_provider_names:
                # delete and recreate the default authenticator and default identity asserter with the correct names.
                self.__delete_and_recreate_provider(base_location, 'Provider', DEFAULT_AUTHENTICATOR_NAME,
                                                    AUTHENTICATION_PROVIDER, DEFAULT_AUTHENTICATOR_TYPE)
                self.__delete_and_recreate_provider(base_location, 'Provider', DEFAULT_IDENTITY_ASSERTER_NAME,
                                                    AUTHENTICATION_PROVIDER, DEFAULT_IDENTITY_ASSERTER_TYPE)
                self.__set_default_identity_asserter_attributes(base_location, DEFAULT_IDENTITY_ASSERTER_NAME,
                                                                AUTHENTICATION_PROVIDER,
                                                                DEFAULT_IDENTITY_ASSERTER_TYPE)
            self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
            return

        atn_names = atn_providers.keys()
        if atn_names[0] == DEFAULT_AUTHENTICATOR_NAME:
            default_authenticator = atn_providers[DEFAULT_AUTHENTICATOR_NAME]
            type_keys = default_authenticator.keys()
            if len(type_keys) == 0 or (len(type_keys) == 1 and type_keys[0] == DEFAULT_AUTHENTICATOR_TYPE):
                delete_default_authenticator = False
            else:
                delete_default_authenticator = True
        else:
            delete_default_authenticator = True

        if len(atn_names) > 1 and atn_names[1] == DEFAULT_IDENTITY_ASSERTER_NAME:
            default_identity_asserter = atn_providers
            type_keys = default_identity_asserter.keys()
            if len(type_keys) == 0 or (len(type_keys) == 1 and type_keys[0] == DEFAULT_IDENTITY_ASSERTER_TYPE):
                delete_default_identity_asserter = False
            else:
                delete_default_identity_asserter = True
        else:
            delete_default_identity_asserter = True

        if delete_default_authenticator:
            if self.__fix_default_authentication_provider_names:
                name = 'Provider'
            else:
                name = DEFAULT_AUTHENTICATOR_NAME
            self.__delete_provider(base_location, name, AUTHENTICATION_PROVIDER)
        elif self.__fix_default_authentication_provider_names:
            # delete and recreate the default authenticator with the correct name now.
            self.__delete_and_recreate_provider(base_location, 'Provider', DEFAULT_AUTHENTICATOR_NAME,
                                                AUTHENTICATION_PROVIDER, DEFAULT_AUTHENTICATOR_TYPE)

        if delete_default_identity_asserter:
            if self.__fix_default_authentication_provider_names:
                name = 'Provider'
            else:
                name = DEFAULT_IDENTITY_ASSERTER_NAME
            self.__delete_provider(base_location, name, AUTHENTICATION_PROVIDER)
            self.__fix_up_model_default_identity_asserter(base_location, DEFAULT_IDENTITY_ASSERTER_NAME,
                                                          AUTHENTICATION_PROVIDER, DEFAULT_IDENTITY_ASSERTER_TYPE,
                                                          atn_providers)
        elif self.__fix_default_authentication_provider_names:
            # delete and recreate the default identity asserter with the correct name now.
            self.__delete_and_recreate_provider(base_location, 'Provider', DEFAULT_IDENTITY_ASSERTER_NAME,
                                                AUTHENTICATION_PROVIDER, DEFAULT_IDENTITY_ASSERTER_TYPE)
            self.__set_default_identity_asserter_attributes(base_location, DEFAULT_IDENTITY_ASSERTER_NAME,
                                                            AUTHENTICATION_PROVIDER, DEFAULT_IDENTITY_ASSERTER_TYPE)

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def __handle_default_authorizers(self, base_location, authorization_providers):
        if authorization_providers is None or len(authorization_providers) == 0 or DEFAULT_AUTHORIZER_NAME is None:
            return

        if self.__need_to_delete_default_provider(authorization_providers, DEFAULT_AUTHORIZER_NAME,
                                                  DEFAULT_AUTHORIZER_TYPE):
            self.__delete_provider(base_location, DEFAULT_AUTHORIZER_NAME, AUTHORIZER)
        return

    def __handle_default_cert_path_providers(self, base_location, cert_path_providers):
        if cert_path_providers is None or len(cert_path_providers) == 0 or DEFAULT_CERT_PATH_PROVIDER_NAME is None:
            return

        if self.__need_to_delete_default_provider(cert_path_providers, DEFAULT_CERT_PATH_PROVIDER_NAME,
                                                  DEFAULT_CERT_PATH_PROVIDER_TYPE):
            self.__delete_provider(base_location, DEFAULT_CERT_PATH_PROVIDER_NAME, CERT_PATH_PROVIDER)
        return

    def __handle_default_credential_mappers(self, base_location, credential_mapping_providers):
        if credential_mapping_providers is None or len(credential_mapping_providers) == 0 or \
                DEFAULT_CREDENTIAL_MAPPER_NAME is None:
            return

        if self.__need_to_delete_default_provider(credential_mapping_providers, DEFAULT_CREDENTIAL_MAPPER_NAME,
                                                  DEFAULT_CREDENTIAL_MAPPER_TYPE):
            self.__delete_provider(base_location, DEFAULT_CREDENTIAL_MAPPER_NAME, CREDENTIAL_MAPPER)
        return

    def __handle_default_password_validators(self, base_location, password_validation_providers):
        if password_validation_providers is None or len(password_validation_providers) == 0 or \
                DEFAULT_PASSWORD_VALIDATOR_NAME is None:
            return

        if self.__need_to_delete_default_provider(password_validation_providers, DEFAULT_PASSWORD_VALIDATOR_NAME,
                                                  DEFAULT_PASSWORD_VALIDATOR_TYPE):
            self.__delete_provider(base_location, DEFAULT_PASSWORD_VALIDATOR_NAME, PASSWORD_VALIDATOR)
        return

    def __handle_default_role_mappers(self, base_location, role_mapping_providers):
        if role_mapping_providers is None or len(role_mapping_providers) == 0 or DEFAULT_ROLE_MAPPER_NAME is None:
            return

        if self.__need_to_delete_default_provider(role_mapping_providers, DEFAULT_ROLE_MAPPER_NAME,
                                                  DEFAULT_ROLE_MAPPER_TYPE):
            self.__delete_provider(base_location, DEFAULT_ROLE_MAPPER_NAME, ROLE_MAPPER)
        return

    def __need_to_delete_default_provider(self, providers_dict, default_name, default_type):
        provider_names = providers_dict.keys()
        if provider_names[0] == default_name:
            default_provider = providers_dict[default_name]
            type_keys = default_provider.keys()
            if len(type_keys) == 0 or (len(type_keys) == 1 and type_keys[0] == default_type):
                delete_default_provider = False
            else:
                delete_default_provider = True
        else:
            delete_default_provider = True
        return delete_default_provider

    def __delete_provider(self, base_location, model_name, model_base_type):
        location = LocationContext(base_location).append_location(model_base_type)
        token_name = self.alias_helper.get_name_token(location)
        if token_name is not None:
            location.add_name_token(token_name, model_name)

        wlst_create_path = self.alias_helper.get_wlst_create_path(location)
        wlst_type, wlst_name = self.alias_helper.get_wlst_mbean_type_and_name(location)
        self.wlst_helper.cd(wlst_create_path)
        self.wlst_helper.delete(wlst_name, wlst_type)
        return

    def __delete_and_recreate_provider(self, base_location, old_wlst_name, model_name, model_base_type, model_subtype):
        self.__delete_provider(base_location, old_wlst_name, model_base_type)

        location = LocationContext(base_location).append_location(model_base_type)
        token_name = self.alias_helper.get_name_token(location)
        if token_name is not None:
            location.add_name_token(token_name, model_name)

        wlst_create_path = self.alias_helper.get_wlst_create_path(location)
        wlst_base_type, wlst_name = self.alias_helper.get_wlst_mbean_type_and_name(location)
        location.append_location(model_subtype)
        wlst_type = self.alias_helper.get_wlst_mbean_type(location)
        self.wlst_helper.cd(wlst_create_path)
        self.wlst_helper.create(wlst_name, wlst_type, wlst_base_type)
        return

    def __set_default_identity_asserter_attributes(self, base_location, model_name, model_base_type, model_subtype):
        location = LocationContext(base_location).append_location(model_base_type)
        token_name = self.alias_helper.get_name_token(location)
        if token_name is not None:
            location.add_name_token(token_name, model_name)
        location.append_location(model_subtype)

        wlst_attribute_path = self.alias_helper.get_wlst_attributes_path(location)
        default_value = self.alias_helper.get_model_attribute_default_value(location, ACTIVE_TYPE)
        wlst_name = self.alias_helper.get_wlst_attribute_name(location, ACTIVE_TYPE)
        self.wlst_helper.cd(wlst_attribute_path)
        self.wlst_helper.set(wlst_name, default_value)
        return

    #
    # Since we are allowing the provider to be recreated, if needed, from the model,
    # we need to add the ActiveType attribute to the model if and only if no
    # attributes are specified in the model.
    #
    def __fix_up_model_default_identity_asserter(self, base_location, model_name, model_base_type,
                                                 model_subtype, atn_providers):
        if atn_providers is not None and DEFAULT_IDENTITY_ASSERTER_NAME in atn_providers:
            default_identity_asserter = \
                dictionary_utils.get_dictionary_element(atn_providers, DEFAULT_IDENTITY_ASSERTER_NAME)
            if DEFAULT_IDENTITY_ASSERTER_TYPE in default_identity_asserter:
                subtype_dict = dictionary_utils.get_dictionary_element(default_identity_asserter,
                                                                       DEFAULT_IDENTITY_ASSERTER_TYPE)
                if len(subtype_dict) == 0:
                    location = LocationContext(base_location).append_location(model_base_type)
                    token_name = self.alias_helper.get_name_token(location)
                    if token_name is not None:
                        location.add_name_token(token_name, model_name)
                    location.append_location(model_subtype)

                    default_value = self.alias_helper.get_model_attribute_default_value(location, ACTIVE_TYPE)
                    subtype_dict[ACTIVE_TYPE] = default_value
        return
