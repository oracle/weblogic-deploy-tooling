"""
Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

from wlsdeploy.aliases.model_constants import COHERENCE_CLUSTER_SYSTEM_RESOURCE
from wlsdeploy.aliases.model_constants import FILE_STORE
from wlsdeploy.aliases.model_constants import FOREIGN_JNDI_PROVIDER
from wlsdeploy.aliases.model_constants import JDBC_STORE
from wlsdeploy.aliases.model_constants import JMS_BRIDGE_DESTINATION
from wlsdeploy.aliases.model_constants import JMS_SERVER
from wlsdeploy.aliases.model_constants import JOLT_CONNECTION_POOL
from wlsdeploy.aliases.model_constants import MAIL_SESSION
from wlsdeploy.aliases.model_constants import MESSAGING_BRIDGE
from wlsdeploy.aliases.model_constants import OHS
from wlsdeploy.aliases.model_constants import PATH_SERVICE
from wlsdeploy.aliases.model_constants import SAF_AGENT
from wlsdeploy.aliases.model_constants import SELF_TUNING
from wlsdeploy.aliases.model_constants import WORK_MANAGER
from wlsdeploy.aliases.model_constants import WEBAPP_CONTAINER
from wlsdeploy.aliases.model_constants import WTC_SERVER
from wlsdeploy.aliases.model_constants import SINGLETON_SERVICE
from wlsdeploy.aliases.model_constants import SYSTEM_COMPONENT
from wlsdeploy.aliases.model_constants import MIME_MAPPING_FILE
from wlsdeploy.aliases.wlst_modes import WlstModes
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
    def _add_subfolders(self, model_nodes, location, excludes=None):
        """
        Override the base method for sub-folders of self-tuning.
        The work manager sub-folder must be processed last.
        """
        parent_type = self.get_location_type(location)
        if parent_type == SELF_TUNING:
            # add all sub-folders except work manager
            Deployer._add_subfolders(self, model_nodes, location, excludes=[WORK_MANAGER])

            # add the work manager sub-folder last
            watch_nodes = dictionary_utils.get_dictionary_element(model_nodes, WORK_MANAGER)
            self._add_named_elements(WORK_MANAGER, watch_nodes, location)
            return

        Deployer._add_subfolders(self, model_nodes, location, excludes=excludes)

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

    def add_self_tuning(self, parent_dict, location):
        """
        Deploy the self-tuning elements in the dictionary at the specified location.
        :param parent_dict: the dictionary possibly containing self-tuning elements
        :param location: the location to deploy the elements
        """
        self_tuning = dictionary_utils.get_dictionary_element(parent_dict, SELF_TUNING)
        if len(self_tuning) != 0:
            self._add_model_elements(SELF_TUNING, self_tuning, location)

    def add_coherence_clusters(self, parent_dict, location):
        """
        Deploy the coherence cluster elements in the dictionary at the specified location.
        :param parent_dict: the dictionary possibly containing coherence cluster elements
        :param location: the location to deploy the elements
        """
        file_stores = dictionary_utils.get_dictionary_element(parent_dict, COHERENCE_CLUSTER_SYSTEM_RESOURCE)
        self._add_named_elements(COHERENCE_CLUSTER_SYSTEM_RESOURCE, file_stores, location)

    def add_webapp_container(self, parent_dict, location):
        """
        Deploy the web-app-container in the dictionary at the specified location.
        :param parent_dict: the dictionary possibly containing web-app-container elements
        :param location: the location to deploy the elements
        """
        web_app_container = dictionary_utils.get_dictionary_element(parent_dict, WEBAPP_CONTAINER)
        if len(web_app_container) != 0:
            self._add_model_elements(WEBAPP_CONTAINER, web_app_container, location)
            if self.archive_helper is not None:
                if MIME_MAPPING_FILE in web_app_container:
                    file_path = web_app_container[MIME_MAPPING_FILE]
                    if self.archive_helper.contains_file(file_path):
                        self.archive_helper.extract_file(file_path)

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
