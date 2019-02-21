"""
Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""

from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import REALM
from wlsdeploy.aliases.model_constants import SECURITY_CONFIGURATION
from wlsdeploy.tool.create.creator import Creator
from wlsdeploy.tool.deploy import deployer_utils
from wlsdeploy.util import dictionary_utils
import oracle.weblogic.deploy.util.WebLogicDeployToolingVersion as WDTVersion


class SecurityProviderCreator(Creator):
    """
    The class that handles the default authentication providers, custom authentication providers and
    reordering of the active realm.

    This release of weblogic deploy tool handles security providers as outlined below:

    The update domain tool expects the security realm providers in the model to describe all non-default values of the
    existing domain realms.

    Custom Security Providers are supported in 12c releases only.

    Default providers in 11g have no name. Offline wlst returns 'Provider' as each provider name instead.
    By deleting and re-adding, the providers are added with the appropriate name field.

    In recap, the issues found for realms are as follows. These issues are handled in this release.
    1. The weblogic template in 11g installs default security providers with no name. In offline
       wlst, the names are represented as 'Provider'. There is no way to successfully fix the providers except to
       manually delete and re-add the default providers in the default realm.
    2. The 11g release does not support custom security providers in offline wlst.
    3. In 11g, the security realm must be configured after the domain home is created with the write, or the
       configuration will not be persisted to the domain configuration file.
    4. Offline wlst in 11g and 12c does not support reorder of the security providers with the set statement.
    5. All 11g and 12c versions less than 12.2.1.2 cannot perform a delete on an Adjudicator object.

    The SecurityConfiguration is added if it does not exist. The default realm is added if it does not exist.
    If the model provides a user defined realm, the default realm is not removed. 
    
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

        # This will leave 11g asis with the default security realm for the current release. No configuration
        # will be done to the 11g default security realm.
        if len(security_configuration_nodes) > 0: # and self._configure_security_configuration():
            self._create_mbean(SECURITY_CONFIGURATION, security_configuration_nodes, location, log_created=True)

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
        _method_name = '_configure_security_configuration'
        if not self.wls_helper.is_configure_security_configuration_supported():
            # Do we bypass or end the update ?
            self.logger.warning('WLSDPLY-12232', self.wls_helper.get_weblogic_version(),
                                WDTVersion.getVersion(), class_name=self.__class_name, method_name=_method_name)
            return False
        return True
