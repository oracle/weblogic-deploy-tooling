"""
Copyright (c) 2017, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from wlsdeploy.aliases.model_constants import CUSTOM_RESOURCE
from wlsdeploy.aliases.model_constants import DESCRIPTOR_BEAN_CLASS
from wlsdeploy.aliases.model_constants import DESCRIPTOR_FILE_NAME
from wlsdeploy.aliases.model_constants import EJB_CONTAINER
from wlsdeploy.aliases.model_constants import FILE_STORE
from wlsdeploy.aliases.model_constants import FOREIGN_JNDI_PROVIDER
from wlsdeploy.aliases.model_constants import JDBC_STORE
from wlsdeploy.aliases.model_constants import JMS_BRIDGE_DESTINATION
from wlsdeploy.aliases.model_constants import JMS_SERVER
from wlsdeploy.aliases.model_constants import JOLT_CONNECTION_POOL
from wlsdeploy.aliases.model_constants import MAIL_SESSION
from wlsdeploy.aliases.model_constants import MESSAGING_BRIDGE
from wlsdeploy.aliases.model_constants import OHS
from wlsdeploy.aliases.model_constants import OPTIONAL_FEATURE_DEPLOYMENT
from wlsdeploy.aliases.model_constants import PATH_SERVICE
from wlsdeploy.aliases.model_constants import RESOURCE_CLASS
from wlsdeploy.aliases.model_constants import SAF_AGENT
from wlsdeploy.aliases.model_constants import SELF_TUNING
from wlsdeploy.aliases.model_constants import SNMP_AGENT
from wlsdeploy.aliases.model_constants import SNMP_AGENT_DEPLOYMENT
from wlsdeploy.aliases.model_constants import WORK_MANAGER
from wlsdeploy.aliases.model_constants import WEBAPP_CONTAINER
from wlsdeploy.aliases.model_constants import WTC_SERVER
from wlsdeploy.aliases.model_constants import SINGLETON_SERVICE
from wlsdeploy.aliases.model_constants import SYSTEM_COMPONENT

from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.tool.deploy.deployer import Deployer
from wlsdeploy.util import dictionary_utils

class CommonResourcesDeployer(Deployer):
    """
    class docstring
    Deploy resources that are common to domain and partition
    """
    _class_name = "CommonResourcesDeployer"

    def __init__(self, model, model_context, aliases, wlst_mode=WlstModes.OFFLINE):
        """
        Construct a deployer with the specified arguments.
        :param model: the model to be deployed
        :param model_context: context information for the model deployment
        :param aliases: the aliases to use for deployment
        :param wlst_mode: the WLST mode to use for deployment
        """
        Deployer.__init__(self, model, model_context, aliases, wlst_mode)
        self._resources = self.model.get_model_resources()

    # Override
    def _add_subfolders(self, model_nodes, location, excludes=None, delete_now=True):
        """
        Override the base method for sub-folders of self-tuning.
        The work manager sub-folder must be processed last.
        """
        parent_type = self.get_location_type(location)
        if parent_type == SELF_TUNING:
            # add all sub-folders except work manager
            Deployer._add_subfolders(self, model_nodes, location, excludes=[WORK_MANAGER], delete_now=delete_now)

            # add the work manager sub-folder last
            watch_nodes = dictionary_utils.get_dictionary_element(model_nodes, WORK_MANAGER)
            self._add_named_elements(WORK_MANAGER, watch_nodes, location, delete_now=delete_now)
            return

        Deployer._add_subfolders(self, model_nodes, location, excludes=excludes, delete_now=delete_now)

    # Override
    def _create_and_cd(self, location, existing_names, child_nodes):
        """
        Override the base method for custom resources.
        These have to be created using cmo.createCustomResource(...) .
        """
        parent_type = self.get_location_type(location)
        if parent_type == CUSTOM_RESOURCE and (self.wlst_mode == WlstModes.ONLINE):
            self.__create_custom_resource_online_and_cd(location, existing_names, child_nodes)
        else:
            Deployer._create_and_cd(self, location, existing_names, child_nodes)

    def add_custom_resources(self, parent_dict, location):
        """
        Deploy the custom resource elements in the dictionary at the specified location.
        :param parent_dict: the dictionary possibly containing custom resource elements
        :param location: the location to deploy the elements
        """
        resources = dictionary_utils.get_dictionary_element(parent_dict, CUSTOM_RESOURCE)
        self._add_named_elements(CUSTOM_RESOURCE, resources, location)

    def add_ejb_container(self, parent_dict, location):
        """
        Deploy the EJB container elements in the dictionary at the specified location.
        :param parent_dict: the dictionary possibly containing EJB container elements
        :param location: the location to deploy the elements
        """
        ejb_container = dictionary_utils.get_dictionary_element(parent_dict, EJB_CONTAINER)
        if len(ejb_container) != 0:
            self._add_model_elements(EJB_CONTAINER, ejb_container, location)

    def add_file_stores(self, parent_dict, location):
        """
        Deploy the file store elements in the dictionary at the specified location.
        :param parent_dict: the dictionary possibly containing file store elements
        :param location: the location to deploy the elements
        """
        file_stores = dictionary_utils.get_dictionary_element(parent_dict, FILE_STORE)
        self._add_named_elements(FILE_STORE, file_stores, location)

    def add_foreign_jndi_providers(self, parent_dict, location):
        """
        Deploy the foreign JNDI provider elements in the dictionary at the specified location.
        :param parent_dict: the dictionary possibly containing foreign JNDI provider elements
        :param location: the location to deploy the elements
        """
        providers = dictionary_utils.get_dictionary_element(parent_dict, FOREIGN_JNDI_PROVIDER)
        self._add_named_elements(FOREIGN_JNDI_PROVIDER, providers, location)

    def add_jdbc_stores(self, parent_dict, location):
        """
        Deploy the JDBC store elements in the dictionary at the specified location.
        :param parent_dict: the dictionary possibly containing JDBC store elements
        :param location: the location to deploy the elements
        """
        jdbc_stores = dictionary_utils.get_dictionary_element(parent_dict, JDBC_STORE)
        self._add_named_elements(JDBC_STORE, jdbc_stores, location)

    def add_jms_bridge_destinations(self, parent_dict, location):
        """
        Deploy the JMS bridge destination elements in the dictionary at the specified location.
        :param parent_dict: the dictionary possibly containing foreign JMS bridge destination elements
        :param location: the location to deploy the elements
        """
        destinations = dictionary_utils.get_dictionary_element(parent_dict, JMS_BRIDGE_DESTINATION)
        self._add_named_elements(JMS_BRIDGE_DESTINATION, destinations, location)

    def add_jms_bridges(self, parent_dict, location):
        """
        Deploy the JMS bridge elements in the dictionary at the specified location.
        :param parent_dict: the dictionary possibly containing foreign JMS bridge elements
        :param location: the location to deploy the elements
        """
        bridges = dictionary_utils.get_dictionary_element(parent_dict, MESSAGING_BRIDGE)
        self._add_named_elements(MESSAGING_BRIDGE, bridges, location)

    def add_jms_servers(self, parent_dict, location):
        """
        Add each named JMS server from the specified nodes in WLST and set its attributes.
        :param parent_dict: the JMS server name nodes from the model
        :param location: the location where elements should be added
        """
        servers = dictionary_utils.get_dictionary_element(parent_dict, JMS_SERVER)
        self._add_named_elements(JMS_SERVER, servers, location)

    def add_jolt_connection_pools(self, parent_dict, location):
        """
        Add each named Jolt connection pool from the specified nodes in WLST and set its attributes.
        :param parent_dict: the Jolt connection pool nodes from the model
        :param location: the location where elements should be added
        """
        servers = dictionary_utils.get_dictionary_element(parent_dict, JOLT_CONNECTION_POOL)
        self._add_named_elements(JOLT_CONNECTION_POOL, servers, location)

    def add_mail_sessions(self, parent_dict, location):
        """
        Deploy the mail session elements in the dictionary at the specified location.
        :param parent_dict: the dictionary possibly containing mail session elements
        :param location: the location to deploy the elements
        """
        sessions = dictionary_utils.get_dictionary_element(parent_dict, MAIL_SESSION)
        self._add_named_elements(MAIL_SESSION, sessions, location)

    def add_path_services(self, parent_dict, location):
        """
        Deploy the path service elements in the dictionary at the specified location.
        :param parent_dict: the dictionary possibly containing foreign path service elements
        :param location: the location to deploy the elements
        """
        services = dictionary_utils.get_dictionary_element(parent_dict, PATH_SERVICE)
        self._add_named_elements(PATH_SERVICE, services, location)

    def add_saf_agents(self, parent_dict, location):
        """
        Deploy the SAF agent elements in the dictionary at the specified location.
        :param parent_dict: the dictionary possibly containing SAF agent elements
        :param location: the location to deploy the elements
        """
        saf_agents = dictionary_utils.get_dictionary_element(parent_dict, SAF_AGENT)
        self._add_named_elements(SAF_AGENT, saf_agents, location)

    def add_snmp_agent(self, parent_dict, location):
        """
        Deploy the SNMP agent elements in the dictionary at the specified location.
        :param parent_dict: the dictionary possibly containing SNMP agent elements
        :param location: the location to deploy the elements
        """
        snmp_agent = dictionary_utils.get_dictionary_element(parent_dict, SNMP_AGENT)
        if len(snmp_agent) != 0:
            self._add_model_elements(SNMP_AGENT, snmp_agent, location)

    def add_snmp_agent_deployments(self, parent_dict, location):
        """
        Deploy the SNMP agent deployment elements in the dictionary at the specified location.
        :param parent_dict: the dictionary possibly containing SNMP agent deployment elements
        :param location: the location to deploy the elements
        """
        deployments = dictionary_utils.get_dictionary_element(parent_dict, SNMP_AGENT_DEPLOYMENT)
        self._add_named_elements(SNMP_AGENT_DEPLOYMENT, deployments, location)

    def add_optional_features(self, parent_dict, location):
        """
        Deploy the Optional Features elements in the dictionary at the specified location.
        :param parent_dict: the dictionary possibly containing Optional Feature Deployment deployment elements
        :param location: the location to deploy the elements
        """
        optional_feature_deployment = dictionary_utils.get_dictionary_element(parent_dict, OPTIONAL_FEATURE_DEPLOYMENT)
        if len(optional_feature_deployment) != 0:
            self._add_model_elements(OPTIONAL_FEATURE_DEPLOYMENT, optional_feature_deployment, location)

    def add_self_tuning(self, parent_dict, location):
        """
        Deploy the self-tuning elements in the dictionary at the specified location.
        :param parent_dict: the dictionary possibly containing self-tuning elements
        :param location: the location to deploy the elements
        """
        self_tuning = dictionary_utils.get_dictionary_element(parent_dict, SELF_TUNING)
        if len(self_tuning) != 0:
            self._add_model_elements(SELF_TUNING, self_tuning, location)

    def add_webapp_container(self, parent_dict, location):
        """
        Deploy the web-app-container in the dictionary at the specified location.
        :param parent_dict: the dictionary possibly containing web-app-container elements
        :param location: the location to deploy the elements
        """
        web_app_container = dictionary_utils.get_dictionary_element(parent_dict, WEBAPP_CONTAINER)
        if len(web_app_container) != 0:
            self._add_model_elements(WEBAPP_CONTAINER, web_app_container, location)
            # No need to extract file again

    def add_wtc_servers(self, parent_dict, location):
        """
        Deploy the WTC server elements in the dictionary at the specified location.
        :param parent_dict: the dictionary possibly containing WTC server elements
        :param location: the location to deploy the elements
        """
        wtc_servers = dictionary_utils.get_dictionary_element(parent_dict, WTC_SERVER)
        self._add_named_elements(WTC_SERVER, wtc_servers, location)

    def add_singleton_service(self, parent_dict, location):
        """
        Deploy the singleton service in the dictionary at the specified location.
        :param parent_dict: the dictionary possibly containing singleton service elements
        :param location: the location to deploy the elements
        """
        singleton_services = dictionary_utils.get_dictionary_element(parent_dict, SINGLETON_SERVICE)
        self._add_named_elements(SINGLETON_SERVICE, singleton_services, location)

    def add_system_components(self, parent_dict, location):
        """
        Deploy the system components in the dictionary at the specified location.
        :param parent_dict: the dictionary possibly containing system component elements
        :param location: the location to deploy the elements
        """
        system_components = dictionary_utils.get_dictionary_element(parent_dict, SYSTEM_COMPONENT)
        self._add_named_elements(SYSTEM_COMPONENT, system_components, location)

    def add_ohs_components(self, parent_dict, location):
        """
        Deploy the OHS components in the dictionary at the specified location.
        :param parent_dict: the dictionary possibly containing OHS component elements
        :param location: the location to deploy the elements
        """
        _method_name = 'add_ohs_components'

        system_components = dictionary_utils.get_dictionary_element(parent_dict, OHS)
        if (len(system_components) != 0) and (self.wlst_mode == WlstModes.ONLINE):
            self.logger.warning('WLSDPLY-09405', OHS, class_name=self._class_name, method_name=_method_name)
        else:
            self._add_named_elements(OHS, system_components, location)

    def __create_custom_resource_online_and_cd(self, location, existing_names, child_nodes):
        """
        Create the custom resource at the specified location if it does not exist,
        and change to the new directory.
        :param location: the location of the custom resource to create
        :param existing_names: existing names at the specified location
        :param child_nodes: used to gather information to create
        """
        _method_name = '__create_custom_resource_online_and_cd'

        mbean_name = self.aliases.get_wlst_mbean_name(location)
        if mbean_name not in existing_names:
            create_path = self.aliases.get_wlst_create_path(location)
            self.wlst_helper.cd(create_path)
            resource_class = dictionary_utils.get_element(child_nodes, RESOURCE_CLASS)
            if not resource_class:
                ex = exception_helper.create_deploy_exception(
                    'WLSDPLY-09426', CUSTOM_RESOURCE, mbean_name, RESOURCE_CLASS)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

            bean_descriptor_class = dictionary_utils.get_element(child_nodes, DESCRIPTOR_BEAN_CLASS)
            if not bean_descriptor_class:
                ex = exception_helper.create_deploy_exception(
                     'WLSDPLY-09426', CUSTOM_RESOURCE, mbean_name, DESCRIPTOR_BEAN_CLASS)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

            descriptor_file_name = dictionary_utils.get_element(child_nodes, DESCRIPTOR_FILE_NAME)
            self.wlst_helper.create_custom_resource(mbean_name, resource_class, bean_descriptor_class,
                                                    descriptor_file_name)

        wlst_path = self.aliases.get_wlst_attributes_path(location)
        self.wlst_helper.cd(wlst_path)
