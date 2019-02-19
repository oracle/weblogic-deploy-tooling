"""
Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
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
from wlsdeploy.util import dictionary_utils


class SecurityProviderCreator(Creator):
    """
    The class that handles the default authentication providers, custom authentication providers and
    reordering of the active realm.

    This release of weblogic deploy tool handles security providers as outlined below:

    The update domain tool will not configure the SecurityConfiguration MBean.

    Custom Security Providers are supported in 12c releases only.

    Default providers in 11g have no name. Offline wlst returns 'Provider' as each provider name instead.
    The offline wlst will lose its way if you attempt to remove the MBean named provider, or if you rename
    the provider and attempt to rename the new provider and most of the time you can add

    The SecurityConfiguration is added if it does not exist. The default realm is added if it does not exist.

    In recap, the issues found for realms are as follows. These issues are handled in this release.
    1. The weblogic template in 11g installs default security providers with no name. In offline
       wlst, the names are represented as 'Provider'. There is no way to successfully fix the providers except to
       manually delete and re-add the default providers in the default realm.
    2. The 11g release does not support custom security providers in offline wlst.
    3. In 11g, the security realm must be configured after the domain home is created with the write, or the
       configuration will not be persisted to the domain configuration file.
    4. Offline wlst in 11g does not support rename and delete of security providers
    4. Offline wlst in 11g and 12c does not support reorder of the security providers with the set statement.

    """
    __class_name = 'SecurityProviderHelper'

    def __init__(self, model_dictionary, model_context, aliases, exception_type, logger):
        Creator.__init__(self, model_dictionary, model_context, aliases, exception_type, logger)

        self._topology = self.model.get_model_topology()
        self._domain_typedef = self.model_context.get_domain_typedef()

        return

    def create_security_configuration(self, location):
        """
        Create the /SecurityConfiguration folder objects, if any.
        Update is calling this method. The SecurityConfiguration should already be configured by create domain, but
        allow the method to create the default security configuration with the default realm if for some reason
        it does not exit. Then bypass any configuration of the update from the model. The update tool does not
        support configuration of the SecurityConfiguration in this release.
        :param location: the location to use
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = '__create_security_configuration'

        self.logger.entering(str(location), class_name=self.__class_name, method_name=_method_name)
        security_configuration_nodes = dictionary_utils.get_dictionary_element(self._topology, SECURITY_CONFIGURATION)

        # in WLS 11g, the SecurityConfiguration mbean is not created until the domain is written.
        # This is called after the domain is written, but check to make sure the mbean exists.
        # if missing, we will create it to initialize realm and default security providers.
        # This release does not support configuring 11g security providers beyond making sure the default
        # realm exists.
        config_location = LocationContext(location).append_location(SECURITY_CONFIGURATION)
        existing_names = deployer_utils.get_existing_object_list(config_location, self.alias_helper)
        if len(existing_names) == 0:
            mbean_type, mbean_name = self.alias_helper.get_wlst_mbean_type_and_name(config_location)
            self.wlst_helper.create(mbean_name, mbean_type)

        self.__handle_default_security_providers()
        # This will leave 11g with the 'Provider' names. If future update is allowed, the update should handle
        # the 'Provider' if update is merge to model. Else, put code here to delete and re-add if in create and
        # no security configuration found in model.
        if len(security_configuration_nodes) > 0 and self._configure_security_configuration():
            self._create_mbean(SECURITY_CONFIGURATION, security_configuration_nodes, location, log_created=True)

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def __handle_default_security_providers(self):
        _method_name = '__handle_default_security_providers'

        self.logger.entering(class_name=self.__class_name, method_name=_method_name)
        location, default_realm_name = self.__get_default_realm_location()
        #
        # Creating domains with the wls.jar template is busted for 11g domains with regards to the
        # names of the default authentication providers (both the DefaultAuthenticator and the
        # DefaultIdentityAsserter names are 'Provider', making it impossible to work with in WLST.
        if self.wls_helper.do_default_authentication_provider_names_need_fixing():
            # put a log here
            self._handle_default_provider(_get_default_adjudicators(), ADJUDICATOR, location)
            self._handle_default_provider(_get_default_auditors(), AUDITOR, location)
            self._handle_default_provider(_get_default_authentication_providers(), AUTHENTICATION_PROVIDER, location)
            self._handle_default_provider(_get_default_authorizers(), AUTHORIZER, location)
            self._handle_default_provider(_get_default_cert_path_providers(), CERT_PATH_PROVIDER, location)
            self._handle_default_provider(_get_default_credential_mappers(), CREDENTIAL_MAPPER, location)
            self._handle_default_provider(_get_default_password_validators(), PASSWORD_VALIDATOR, location)
            self._handle_default_provider(_get_default_role_mappers(), ROLE_MAPPER, location)

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

        default_security_realm_name = self.wls_helper.get_default_security_realm_name()
        if wlst_type not in existing_folder_names:
            if token_name is not None:
                location.add_name_token(token_name, default_security_realm_name)
            wlst_name = self.alias_helper.get_wlst_mbean_name(location)
            self.wlst_helper.create_and_cd(self.alias_helper, wlst_type, wlst_name, location)
        else:
            if token_name is not None:
                location.add_name_token(token_name, default_security_realm_name)
            wlst_attribute_path = self.alias_helper.get_wlst_attributes_path(location)
            self.wlst_helper.cd(wlst_attribute_path)
        return location, default_security_realm_name

    def _configure_security_configuration(self):
        """
        For this release, the update tool will not configure the security realm.
        :return: True if can configure the SecurityConfiguration mbean
        """
        if not self._domain_typedef.is_security_configuration_supported():
            # Do we bypass or end the update ?
            self.logger.warning('Unable to process SecurityConfiguration in update mode.')
            return False
        return True

    def _handle_default_provider(self, default_list, base_provider, base_location):
        location = LocationContext(base_location)
        location.append_location(base_provider)
        list_path = self.alias_helper.get_wlst_list_path(location)
        existing_folder_names = self._get_existing_folders(list_path)
        if len(existing_folder_names) > 0 and 'Provider' in existing_folder_names:
            create_path = self.alias_helper.get_wlst_create_path(location)
            self.wlst_helper.cd(create_path)
            for provider, provider_type in default_list.iteritems():
                self.wlst_helper.create(provider, provider_type, base_provider)
        return


def _get_default_adjudicators():
    return {DEFAULT_ADJUDICATOR_NAME: DEFAULT_ADJUDICATOR_TYPE}


def _get_default_auditors():
    return {DEFAULT_AUDITOR_NAME: DEFAULT_AUDITOR_TYPE}


def _get_default_authentication_providers():
    return {DEFAULT_AUTHENTICATOR_NAME: DEFAULT_AUTHENTICATOR_TYPE,
            DEFAULT_IDENTITY_ASSERTER_NAME: DEFAULT_IDENTITY_ASSERTER_TYPE}


def _get_default_authorizers():
    return {DEFAULT_AUTHORIZER_NAME: DEFAULT_AUTHORIZER_TYPE}


def _get_default_cert_path_providers():
    return {DEFAULT_CERT_PATH_PROVIDER_NAME: DEFAULT_CERT_PATH_PROVIDER_TYPE}


def _get_default_credential_mappers():
    return {DEFAULT_CREDENTIAL_MAPPER_NAME: DEFAULT_CREDENTIAL_MAPPER_TYPE}


def _get_default_password_validators():
    return {DEFAULT_PASSWORD_VALIDATOR_NAME: DEFAULT_PASSWORD_VALIDATOR_TYPE}


def _get_default_role_mappers():
    return {DEFAULT_ROLE_MAPPER_NAME: DEFAULT_ROLE_MAPPER_TYPE}
