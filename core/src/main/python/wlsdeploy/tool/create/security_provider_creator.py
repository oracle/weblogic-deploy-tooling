"""
Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

from oracle.weblogic.deploy.exception import BundleAwareException

from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import REALM
from wlsdeploy.aliases.model_constants import SECURITY_CONFIGURATION
from wlsdeploy.exception import exception_helper
from wlsdeploy.tool.create.creator import Creator
from wlsdeploy.tool.deploy import deployer_utils
from wlsdeploy.util import dictionary_utils
import wlsdeploy.util.unicode_helper as str_helper
from wlsdeploy.util.weblogic_helper import WebLogicHelper


class SecurityProviderCreator(Creator):
    """
    The class that handles the default authentication providers, custom authentication providers and
    reordering of the active realm.

    The WebLogic deploy tool handles security providers as outlined below:

    The update domain tool expects the security realm providers in the model to describe all non-default values of the
    existing domain realms.

    Custom Security Providers are supported in 12c releases only.

    Default providers in 11g have no name. Offline WLST returns 'Provider' as each provider name instead.
    By deleting and re-adding, the providers are added with the appropriate name field.

    In recap, the issues found for realms are as follows. These issues are handled in this release.
    1. The WebLogic template in 11g installs default security providers with no name. In offline
       WLST, the names are represented as 'Provider'. There is no way to successfully fix the providers except to
       manually delete and re-add the default providers in the default realm.
    2. The 11g release does not support custom security providers in offline WLST.
    3. In 11g, the security realm must be configured after the domain home is created with the write, or the
       configuration will not be persisted to the domain configuration file.
    4. Offline WLST in 11g and 12c does not support reorder of the security providers with the set statement.
    5. All 11g and 12c versions less than 12.2.1.2 cannot perform a delete on an Adjudicator object.

    The SecurityConfiguration is added if it does not exist. The default realm is added if it does not exist.
    If the model provides a user defined realm, the default realm is not removed. 
    
    """
    __class_name = 'SecurityProviderCreator'
    __adjudicator_type = 'Adjudicator'
    __default_adjudicator_name = 'DefaultAdjudicator'

    def __init__(self, model_dictionary, model_context, aliases, exception_type, logger):
        Creator.__init__(self, model_dictionary, model_context, aliases, exception_type, logger)

        self._topology = self.model.get_model_topology()
        self._domain_typedef = self.model_context.get_domain_typedef()
        self._wls_helper = WebLogicHelper(self.logger)

    def create_security_configuration(self, location):
        """
        Create the /SecurityConfiguration folder objects, if any.
        
        The SecurityConfiguration should already be configured by create domain, but
        allow the method to create the default security configuration with the default realm if for some reason
        it does not exist.  
        
        :param location: the location to use
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = '__create_security_configuration'

        self.logger.entering(str_helper.to_string(location), class_name=self.__class_name, method_name=_method_name)
        security_configuration_nodes = dictionary_utils.get_dictionary_element(self._topology, SECURITY_CONFIGURATION)

        # in WLS 11g, the SecurityConfiguration mbean is not created until the domain is written.
        # This is called after the domain is written, but check to make sure the mbean does exist.
        # It missing it will be created to initialize the default realm and security providers.
        config_location = LocationContext(location).append_location(SECURITY_CONFIGURATION)
        existing_names = deployer_utils.get_existing_object_list(config_location, self.aliases)
        if len(existing_names) == 0:
            mbean_type, mbean_name = self.aliases.get_wlst_mbean_type_and_name(config_location)
            self.wlst_helper.create(mbean_name, mbean_type)

        if len(security_configuration_nodes) > 0:
            self._create_mbean(SECURITY_CONFIGURATION, security_configuration_nodes, location, log_created=True)

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    # Override
    def _create_named_subtype_mbeans(self, type_name, model_nodes, base_location, log_created=False):
        """
        Create the MBeans for a single security provider type, such as "AuthenticationProvider".
        These are the only named subtype MBeans within security configuration, so no further checks are required.
        :param type_name: the model folder type
        :param model_nodes: the model dictionary of the specified model folder type
        :param base_location: the base location object to use to create the MBeans
        :param log_created: whether or not to log created at INFO level, by default it is logged at the FINE level
        :raises: CreateException: if an error occurs
        """
        _method_name = '_create_named_subtype_mbeans'
        self.logger.entering(type_name, str_helper.to_string(base_location), log_created,
                             class_name=self.__class_name,method_name=_method_name)

        if not self._is_type_valid(base_location, type_name):
            return

        # some providers may be skipped
        if not self._check_provider_type(type_name, model_nodes):
            return

        location = LocationContext(base_location).append_location(type_name)
        self._process_flattened_folder(location)

        # For create, delete the existing nodes, and re-add in order found in model in iterative code below
        self._delete_existing_providers(location)

        if model_nodes is None or len(model_nodes) == 0:
            return

        token_name = self.aliases.get_name_token(location)
        create_path = self.aliases.get_wlst_create_path(location)
        list_path = self.aliases.get_wlst_list_path(location)
        existing_folder_names = self._get_existing_folders(list_path)
        known_providers = self.aliases.get_model_subfolder_names(location)
        allow_custom = str_helper.to_string(self.aliases.is_custom_folder_allowed(location))

        for model_name in model_nodes:
            model_node = model_nodes[model_name]

            if model_node is None:
                # The node is empty so nothing to do... move to the next named node.
                continue

            if len(model_node) != 1:
                # there should be exactly one type folder under the name folder
                ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-12117', type_name, model_name,
                                                       len(model_node))
                self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex

            model_type_subfolder_name = list(model_node.keys())[0]
            child_nodes = dictionary_utils.get_dictionary_element(model_node, model_type_subfolder_name)

            # custom providers require special processing, they are not described in alias framework
            if allow_custom and (model_type_subfolder_name not in known_providers):
                self.custom_folder_helper.update_security_folder(base_location, type_name, model_type_subfolder_name,
                                                                 model_name, child_nodes)
                continue

            # for a known provider, process using aliases
            prov_location = LocationContext(location)
            name = self.wlst_helper.get_quoted_name_for_wlst(model_name)
            if token_name is not None:
                prov_location.add_name_token(token_name, name)

            wlst_base_provider_type, wlst_name = self.aliases.get_wlst_mbean_type_and_name(prov_location)

            prov_location.append_location(model_type_subfolder_name)
            wlst_type = self.aliases.get_wlst_mbean_type(prov_location)

            if wlst_name not in existing_folder_names:
                if log_created:
                    self.logger.info('WLSDPLY-12118', type_name, model_type_subfolder_name, name, create_path,
                                     class_name=self.__class_name, method_name=_method_name)
                else:
                    self.logger.fine('WLSDPLY-12118', type_name, model_type_subfolder_name, name, create_path,
                                     class_name=self.__class_name, method_name=_method_name)
                self.wlst_helper.cd(create_path)
                self.wlst_helper.create(wlst_name, wlst_type, wlst_base_provider_type)
            else:
                if log_created:
                    self.logger.info('WLSDPLY-12119', type_name, model_type_subfolder_name, name, create_path,
                                     class_name=self.__class_name, method_name=_method_name)
                else:
                    self.logger.fine('WLSDPLY-12119', type_name, model_type_subfolder_name, name, create_path,
                                     class_name=self.__class_name, method_name=_method_name)

            attribute_path = self.aliases.get_wlst_attributes_path(prov_location)
            self.wlst_helper.cd(attribute_path)

            self.logger.finest('WLSDPLY-12111', self.aliases.get_model_folder_path(prov_location),
                               self.wlst_helper.get_pwd(), class_name=self.__class_name, method_name=_method_name)
            self._set_attributes(prov_location, child_nodes)
            self._create_subfolders(prov_location, child_nodes)

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    # Override
    def _process_child_nodes(self, location, model_nodes):
        """
        Process the model nodes at the specified location.
        Override default behavior to process security configuration and realm sub-folders before attributes.
        Security configuration attribute DefaultRealm needs to get the MBean of the referenced realm.
        Realm attribute CertPathBuilder needs to get the MBean of the referenced certificate registry.
        :param location: the location where the nodes should be processed
        :param model_nodes: the model dictionary of the nodes to be processed
        :raises: CreateException: if an error occurs
        """
        _method_name = '_process_child_nodes'

        model_type, model_name = self.aliases.get_model_type_and_name(location)
        if model_type in [SECURITY_CONFIGURATION, REALM]:
            self.logger.finest('WLSDPLY-12143', self.aliases.get_model_folder_path(location),
                               self.wlst_helper.get_pwd(), class_name=self.__class_name, method_name=_method_name)

            self._create_subfolders(location, model_nodes)
            self.wlst_helper.cd(self.aliases.get_wlst_attributes_path(location))
            self._set_attributes(location, model_nodes)
            return

        Creator._process_child_nodes(self, location, model_nodes)

    def _delete_existing_providers(self, location):
        """
        The security realms providers in the model are processed as merge to the model. Each realm provider
        section must be complete and true to the resulting domain. Any existing provider not found in the
        model will be removed, and any provider in the model but not in the domain will be added. The resulting
        provider list will be ordered as listed in the model. If the provider type (i.e. AuthenticationProvider)
        is not in the model, it is assumed no configuration or ordering is needed, and the provider is skipped.
        If the provider type is in the model, but there is no MBean entry under the provider, then it is
        assumed that all providers for that provider type must be removed.

        For create, the default realm and default providers have been added by the WebLogic base template and any
        extension templates. They have default values. These providers will be removed from the domain. During
        the normal iteration through the provider list, the providers, if in the model, will be re-added in model
        order. Any attributes in the model that are not the default value are then applied to the the new provider.

        By deleting all providers and re-adding from the model, we are both merging to the model and ordering the
        providers. In offline WLST, the set<providertype>Providers(<provider_object_list>, which reorders existing
        providers, does not work. Deleting the providers and re-adding also has the added benefit of fixing the 11g
        problem where the providers have no name. They are returned with the name 'Provider'. In the authentication
        provider, there are two default providers, and just setting the name does not work. When we re-add we re-add
        with the correct name. And the DefaultAuthenticationProvider successfully re-adds with the correct default
        identity asserter.

        This release also supports updating the security configuration realms in both offline and online mode. This
        release requires a complete list of providers as described in the first paragraph.

        :param location: current context of the location pointing at the provider mbean
        """
        _method_name = '_delete_existing_providers'
        self.logger.entering(location.get_folder_path(), class_name=self.__class_name, method_name=_method_name)

        list_path = self.aliases.get_wlst_list_path(location)
        existing_folder_names = self._get_existing_folders(list_path)
        wlst_base_provider_type = self.aliases.get_wlst_mbean_type(location)
        if len(existing_folder_names) == 0:
            self.logger.finer('WLSDPLY-12136', wlst_base_provider_type, list_path, class_name=self.__class_name,
                              method_name=_method_name)
        else:
            create_path = self.aliases.get_wlst_create_path(location)
            self.wlst_helper.cd(create_path)
            for existing_folder_name in existing_folder_names:
                try:
                    self.logger.info('WLSDPLY-12135', existing_folder_name, wlst_base_provider_type, create_path,
                                     class_name=self.__class_name, method_name=_method_name)
                    self.wlst_helper.delete(existing_folder_name, wlst_base_provider_type)
                except BundleAwareException, bae:
                    ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-12134', existing_folder_name,
                                                           self.wls_helper.get_weblogic_version(),
                                                           wlst_base_provider_type, bae.getLocalizedMessage(),
                                                           error=bae)
                    self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                    raise ex

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def _check_provider_type(self, type_name, model_nodes):
        """
        Determine if the specified security configuration type should be updated.
        :param type_name: the model folder type
        :param model_nodes: the model dictionary of the specified model folder type
        :return: True if the provider type should be updated, False if it should be skipped
        """
        _method_name = '_check_provider_type'
        # there are problems re-configuring adjudicators, don't update them
        if type_name == self.__adjudicator_type and not self.is_adjudicator_changeable():
            if not self._is_default_adjudicator_configuration(model_nodes):
                self.logger.warning('WLSDPLY-12137', class_name=self.__class_name, method_name=_method_name)

            return False

        return True

    def _is_default_adjudicator_configuration(self, model_nodes):
        """
        Verify that the specified adjudicator nodes match the default configuration.
        Log any discrepancies at the FINE level.
        :param model_nodes: the model dictionary of the adjudicator section
        :return: True if the model nodes match the default configuration, False otherwise
        """
        _method_name = '_check_adjudicator_configuration'

        if len(model_nodes) != 1:
            self.logger.fine('WLSDPLY-12138', len(model_nodes), class_name=self.__class_name, method_name=_method_name)
            return False

        name = model_nodes.keys()[0]
        if name != self.__default_adjudicator_name:
            self.logger.fine('WLSDPLY-12139', name, class_name=self.__class_name, method_name=_method_name)
            return False

        subtypes = model_nodes[name]
        if len(subtypes) != 1:
            self.logger.fine('WLSDPLY-12140', len(subtypes), class_name=self.__class_name, method_name=_method_name)
            return False

        subtype = subtypes.keys()[0]
        if subtype != self.__default_adjudicator_name:
            self.logger.fine('WLSDPLY-12141', subtype, class_name=self.__class_name, method_name=_method_name)
            return False

        attributes = subtypes[subtype]
        if len(attributes) != 0:
            self.logger.fine('WLSDPLY-12142', len(attributes), class_name=self.__class_name, method_name=_method_name)
            return False

        return True

    def is_adjudicator_changeable(self):
        return self._wls_helper.is_weblogic_version_or_above('12.2.1.4')
