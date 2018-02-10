"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
import java.io.File as JFile

import wlsdeploy.util.dictionary_utils as dictionary_utils
import wlsdeploy.util.model_fields as model_fields
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import COHERENCE_CLUSTER_SYSTEM_RESOURCE
from wlsdeploy.aliases.model_constants import DIRECTORY
from wlsdeploy.aliases.model_constants import FILE_STORE
from wlsdeploy.aliases.model_constants import FOREIGN_JNDI_PROVIDER
from wlsdeploy.aliases.model_constants import JDBC_STORE
from wlsdeploy.aliases.model_constants import JMS_BRIDGE_DESTINATION
from wlsdeploy.aliases.model_constants import JMS_SERVER
from wlsdeploy.aliases.model_constants import MAIL_SESSION
from wlsdeploy.aliases.model_constants import MESSAGING_BRIDGE
from wlsdeploy.aliases.model_constants import PATH_SERVICE
from wlsdeploy.aliases.model_constants import SAF_AGENT
from wlsdeploy.aliases.model_constants import SELF_TUNING
from wlsdeploy.aliases.model_constants import TARGET
from wlsdeploy.aliases.model_constants import WORK_MANAGER
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.tool.deploy.applications_deployer import ApplicationsDeployer
from wlsdeploy.tool.deploy.datasource_deployer import DatasourceDeployer
from wlsdeploy.tool.deploy.deployer import Deployer
from wlsdeploy.tool.deploy.jms_resources_deployer import JmsResourcesDeployer
from wlsdeploy.tool.deploy.wldf_resources_deployer import WldfResourcesDeployer


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
        return

    def add_file_stores(self, parent_dict, location):
        """
        Deploy the file store elements in the dictionary at the specified location.
        :param parent_dict: the dictionary possibly containing file store elements
        :param location: the location to deploy the elements
        """
        file_stores = dictionary_utils.get_dictionary_element(parent_dict, FILE_STORE)
        self._add_named_elements(FILE_STORE, file_stores, location)

        # TODO(deploy): is this valid, especially online?  # create the directory for each file store
        for file_store_name in file_stores:
            store_nodes = dictionary_utils.get_dictionary_element(file_stores, file_store_name)
            target_val = dictionary_utils.get_element(store_nodes, TARGET)
            directory_val = dictionary_utils.get_element(store_nodes, DIRECTORY)
            self._create_file_store_directory(file_store_name, target_val, directory_val)
        return

    def add_foreign_jndi_providers(self, parent_dict, location):
        """
        Deploy the foreign JNDI provider elements in the dictionary at the specified location.
        :param parent_dict: the dictionary possibly containing foreign JNDI provider elements
        :param location: the location to deploy the elements
        """
        providers = dictionary_utils.get_dictionary_element(parent_dict, FOREIGN_JNDI_PROVIDER)
        self._add_named_elements(FOREIGN_JNDI_PROVIDER, providers, location)
        return

    def add_jdbc_stores(self, parent_dict, location):
        """
        Deploy the JDBC store elements in the dictionary at the specified location.
        :param parent_dict: the dictionary possibly containing JDBC store elements
        :param location: the location to deploy the elements
        """
        jdbc_stores = dictionary_utils.get_dictionary_element(parent_dict, JDBC_STORE)
        self._add_named_elements(JDBC_STORE, jdbc_stores, location)
        return

    def add_jms_bridge_destinations(self, parent_dict, location):
        """
        Deploy the JMS bridge destination elements in the dictionary at the specified location.
        :param parent_dict: the dictionary possibly containing foreign JMS bridge destination elements
        :param location: the location to deploy the elements
        """
        destinations = dictionary_utils.get_dictionary_element(parent_dict, JMS_BRIDGE_DESTINATION)
        self._add_named_elements(JMS_BRIDGE_DESTINATION, destinations, location)
        return

    def add_jms_bridges(self, parent_dict, location):
        """
        Deploy the JMS bridge elements in the dictionary at the specified location.
        :param parent_dict: the dictionary possibly containing foreign JMS bridge elements
        :param location: the location to deploy the elements
        """
        bridges = dictionary_utils.get_dictionary_element(parent_dict, MESSAGING_BRIDGE)
        self._add_named_elements(MESSAGING_BRIDGE, bridges, location)
        return

    def add_jms_servers(self, parent_dict, location):
        """
        Add each named JMS server from the specified nodes in WLST and set its attributes.
        :param parent_dict: the JMS server name nodes from the model
        :param location: the location where elements should be added
        """
        servers = dictionary_utils.get_dictionary_element(parent_dict, JMS_SERVER)
        self._add_named_elements(JMS_SERVER, servers, location)
        return

    def add_mail_sessions(self, parent_dict, location):
        """
        Deploy the mail session elements in the dictionary at the specified location.
        :param parent_dict: the dictionary possibly containing mail session elements
        :param location: the location to deploy the elements
        """
        sessions = dictionary_utils.get_dictionary_element(parent_dict, MAIL_SESSION)
        self._add_named_elements(MAIL_SESSION, sessions, location)
        return

    def add_path_services(self, parent_dict, location):
        """
        Deploy the path service elements in the dictionary at the specified location.
        :param parent_dict: the dictionary possibly containing foreign path service elements
        :param location: the location to deploy the elements
        """
        services = dictionary_utils.get_dictionary_element(parent_dict, PATH_SERVICE)
        self._add_named_elements(PATH_SERVICE, services, location)
        return

    def add_saf_agents(self, parent_dict, location):
        """
        Deploy the SAF agent elements in the dictionary at the specified location.
        :param parent_dict: the dictionary possibly containing SAF agent elements
        :param location: the location to deploy the elements
        """
        saf_agents = dictionary_utils.get_dictionary_element(parent_dict, SAF_AGENT)
        self._add_named_elements(SAF_AGENT, saf_agents, location)
        return

    def add_self_tuning(self, parent_dict, location):
        """
        Deploy the self-tuning elements in the dictionary at the specified location.
        :param parent_dict: the dictionary possibly containing self-tuning elements
        :param location: the location to deploy the elements
        """
        self_tuning = dictionary_utils.get_dictionary_element(parent_dict, SELF_TUNING)
        if len(self_tuning) != 0:
            self._add_model_elements(SELF_TUNING, self_tuning, location)
        return

    def add_coherence_clusters(self, parent_dict, location):
        """
        Deploy the coherence cluster elements in the dictionary at the specified location.
        :param parent_dict: the dictionary possibly containing coherence cluster elements
        :param location: the location to deploy the elements
        """
        file_stores = dictionary_utils.get_dictionary_element(parent_dict, COHERENCE_CLUSTER_SYSTEM_RESOURCE)
        self._add_named_elements(COHERENCE_CLUSTER_SYSTEM_RESOURCE, file_stores, location)

    # TODO(deploy): for multi-tenant, update to use aliases
    def add_resource_groups(self, parent_dict, parent_name, parent_type='Domain', base_path='/'):
        method_name = 'add_resource_groups'
        if dictionary_utils.is_empty_dictionary_element(parent_dict, 'ResourceGroup'):
            return

        if not self.wls_helper.is_weblogic_version_or_above('12.2.1'):
            deploy_ex = exception_helper.create_deploy_exception('WLSDPLY-09089', self.wls_helper.wl_version)
            self.logger.throwing(class_name=self._class_name, method_name=method_name, error=deploy_ex)
            raise deploy_ex

        is1221 = False
        if not self.wls_helper.is_weblogic_version_or_above('12.2.1.1'):
            is1221 = True

        # TODO(deploy): needs conversion to use aliases. For now, create root location to pass to deploy resources
        location = LocationContext()

        resource_groups = parent_dict['ResourceGroup']
        for resource_group in resource_groups:
            self.logger.info('Adding Resource Group {0} to {1} {2}', resource_group, parent_type, parent_name,
                             class_name=self._class_name, method_name='_add_resource_groups')

            self.wlst_helper.cd(base_path)
            self.wlst_helper.create(resource_group, 'ResourceGroup')
            rg_base_path = base_path + 'ResourceGroup/' +\
                           self.wlst_helper.get_quoted_name_for_wlst(resource_group) + '/'
            self.wlst_helper.cd(rg_base_path)
            for param in resource_groups[resource_group]:
                if param not in model_fields.RESOURCE_GROUP_SUBFOLDERS:
                    if is1221 and param in model_fields.RESOURCE_GROUP_ATTR_NOT_IN_1221:
                        message = 'Skip setting {0} on ResourceGroup {1} because it is not supported in ' + \
                                  'WebLogic Server 12.2.1'
                        self.logger.finer(message, param, resource_group)
                    else:
                        self.wlst_helper.set(param, resource_groups[resource_group][param])

            self.add_resource_group_resources(resource_groups[resource_group], location)
        return

    def add_resource_group_resources(self, parent_dict, location):
        """
        Add the resource elements in the dictionary at the specified location.
        :param parent_dict: the dictionary possibly containing resource elements
        :param location: the location to deploy the elements
        """

        data_source_deployer = DatasourceDeployer(self.model, self.model_context, self.aliases, self.wlst_mode)
        data_source_deployer.add_data_sources(parent_dict, location)

        self.add_foreign_jndi_providers(parent_dict, location)
        self.add_file_stores(parent_dict, location)
        self.add_jdbc_stores(parent_dict, location)
        self.add_jms_servers(parent_dict, location)
        self.add_saf_agents(parent_dict, location)
        self.add_path_services(parent_dict, location)

        jms_deployer = JmsResourcesDeployer(self.model, self.model_context, self.aliases)
        jms_deployer.add_jms_system_resources(parent_dict, location)

        self.add_jms_bridge_destinations(parent_dict, location)
        self.add_jms_bridges(parent_dict, location)
        self.add_mail_sessions(parent_dict, location)

        wldf_deployer = WldfResourcesDeployer(self.model, self.model_context, self.aliases)
        wldf_deployer.add_wldf_modules(parent_dict, location)

        self.add_coherence_clusters(parent_dict, location)

        applications_deployer = \
            ApplicationsDeployer(self.model, self.model_context, self.aliases, self.wlst_mode, location)
        applications_deployer.deploy()
        return

    # TODO(deploy): for multi-tenant, update to use aliases
    def add_partition_work_managers(self, parent_dict, parent_name, parent_type='Domain', base_path='/'):
        method_name = 'add_partition_work_managers'
        if dictionary_utils.is_empty_dictionary_element(parent_dict, 'PartitionWorkManager'):
            return

        if not self.wls_helper.is_weblogic_version_or_above('12.2.1'):
            deploy_ex = exception_helper.create_deploy_exception('WLSDPLY-09090', self.wls_helper.wl_version)
            self.logger.throwing(class_name=self._class_name, method_name=method_name, error=deploy_ex)
            raise deploy_ex

        partition_work_managers = parent_dict['PartitionWorkManager']
        for partition_work_manager in partition_work_managers:
            self.logger.info('Adding Partition Work Manager {0} to {1} {2}',
                             partition_work_manager, parent_type, parent_name,
                             class_name=self._class_name, method_name='add_partition_work_managers')

            self.wlst_helper.cd(base_path)
            self.wlst_helper.create(partition_work_manager, 'PartitionWorkManager')
            self.wlst_helper.cd('PartitionWorkManager/' +
                                self.wlst_helper.get_quoted_name_for_wlst(partition_work_manager))
            for param in partition_work_managers[partition_work_manager]:
                self.wlst_helper.set(param, partition_work_managers[partition_work_manager][param])

        return

    def _create_file_store_directory(self, file_store_name, target_name, directory_name):
        """
        Create the file store directory based on the file store, target, and directory names.
        :param file_store_name: the name of the file store
        :param target_name: the name of the target
        :param directory_name: the name of the directory
        """
        method_name = '_create_file_store_directory'

        stripped_target_name = target_name
        if target_name is None:
            stripped_target_name = "not_targeted"
        elif '(migratable)' in target_name:
            stripped_target_name = target_name.split()[0]

        if directory_name is not None:
            file_name = directory_name
        else:
            file_name = 'servers/' + stripped_target_name + '/data/store/' + file_store_name

        directory = JFile(file_name)
        if directory.isAbsolute():
            directory = directory.getCanonicalFile()
        else:
            directory = JFile(JFile(self.model_context.get_domain_home()), file_name)

        if directory.exists():
            if not directory.isDirectory():
                deploy_ex = exception_helper.create_deploy_exception('WLSDPLY-09086', file_store_name,
                                                                     str(directory.getPath()))
                self.logger.throwing(class_name=self._class_name, method_name=method_name, error=deploy_ex)
                raise deploy_ex
        else:
            created = directory.mkdirs()
            if created:
                self.logger.info('WLSDPLY-09087', file_store_name, str(directory.getPath()),
                                 class_name=self._class_name, method_name=method_name)
            else:
                deploy_ex = exception_helper.create_deploy_exception('WLSDPLY-09088', file_store_name,
                                                                     str(directory.getPath()))
                self.logger.throwing(class_name=self._class_name, method_name=method_name, error=deploy_ex)
                raise deploy_ex
        return
