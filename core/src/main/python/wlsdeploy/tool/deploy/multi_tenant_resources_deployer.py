"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
import com.oracle.cie.domain.script.jython.WLSTException as WLSTException
import java.util.Properties as JProperties

import wlsdeploy.util.dictionary_utils as dictionary_utils
import wlsdeploy.util.model_fields as model_fields
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import RESOURCE_GROUP_TEMPLATE
from wlsdeploy.tool.deploy.common_resources_deployer import CommonResourcesDeployer
from wlsdeploy.tool.deploy.deployer import Deployer


class MultiTenantResourcesDeployer(Deployer):
    """
    class docstring
    """
    CLASS_NAME = "MultiTenantResourcesDeployer"

    def __init__(self, model, model_context, aliases, wlst_mode=WlstModes.OFFLINE):
        Deployer.__init__(self, model, model_context, aliases, wlst_mode)
        self._resources = self.model.get_model_resources()

        self.common_deployer = \
            CommonResourcesDeployer(self.model, self.model_context, self.aliases, wlst_mode=self.wlst_mode)

    def add_multi_tenant_objects(self):
        self._add_resource_management()
        self._add_resource_group_templates()
        self.common_deployer.add_resource_groups(self._resources, self.model_context.get_domain_name())
        self.common_deployer.add_partition_work_managers(self._resources, self.model_context.get_domain_name())
        self._add_partitions()
        return

    def _add_coherence_partition_cache_configs(self, partition_dict, partition_name, partition_path):
        folder_name = 'CoherencePartitionCacheConfig'
        if dictionary_utils.is_empty_dictionary_element(partition_dict, folder_name):
            return

        property_folder = 'CoherencePartitionCacheProperty'

        cache_configs = partition_dict[folder_name]
        for cache_config in cache_configs:
            self.logger.info('Adding Coherence Partition Cache Config {0} to Partition {1}',
                             cache_config, partition_name, class_name=self.CLASS_NAME,
                             method_name='_add_coherence_partition_cache_configs')

            self.wlst_helper.cd(partition_path)
            self.wlst_helper.create(cache_config, folder_name)
            cache_config_folder = folder_name + '/' + self.wlst_helper.get_quoted_name_for_wlst(cache_config)
            self.wlst_helper.cd(cache_config_folder)
            for param in cache_configs[cache_config]:
                if param != property_folder:
                    self.wlst_helper.set(param, cache_configs[cache_config][param])

            if property_folder in cache_configs[cache_config]:
                for prop in cache_configs[cache_config][property_folder]:
                    self.wlst_helper.create(prop, property_folder)
                    self.wlst_helper.cd(property_folder + '/' + self.wlst_helper.get_quoted_name_for_wlst(prop))
                    cache_config_property_dict = cache_configs[cache_config][property_folder][prop]
                    for param in cache_config_property_dict:
                        self.wlst_helper.set(param, cache_config_property_dict[param])
                    self.wlst_helper.cd('../..')

        return

    def _add_foreign_jndi_provider_overrides(self, partition_dict, partition_name, partition_path):
        if dictionary_utils.is_empty_dictionary_element(partition_dict, 'ForeignJndiProviderOverride'):
            return

        jndi_overrides = partition_dict['ForeignJndiProviderOverride']
        for jndi_override in jndi_overrides:
            self.logger.info('Adding Foreign JNDI Provider Override {0} to Partition {1}', jndi_override,
                             partition_name, class_name=self.CLASS_NAME,
                             method_name='_add_foreign_jndi_provider_overrides')

            self.wlst_helper.cd(partition_path)
            self.wlst_helper.create(jndi_override, 'ForeignJndiProviderOverride')
            self.wlst_helper.cd('ForeignJndiProviderOverride/' + self.wlst_helper.get_quoted_name_for_wlst(jndi_override))
            for param in jndi_overrides[jndi_override]:
                if not param == 'ForeignJNDILink':
                    self.wlst_helper.set(param, jndi_overrides[jndi_override][param])

            if 'ForeignJNDILink' in jndi_overrides[jndi_override]:
                links = jndi_overrides[jndi_override]['ForeignJNDILink']
                for link in links:
                    self.wlst_helper.create(link, 'ForeignJNDILink')
                    self.wlst_helper.cd('ForeignJNDILink/' + self.wlst_helper.get_quoted_name_for_wlst(link))
                    for param in links[link]:
                        self.wlst_helper.set(param, links[link][param])
                    self.wlst_helper.cd('../..')

        return

    def _add_jdbc_system_resource_overrides(self, partition_dict, partition_name, partition_path):
        if dictionary_utils.is_empty_dictionary_element(partition_dict, 'JdbcSystemResourceOverride'):
            return

        is1221 = False
        if not self.wls_helper.is_weblogic_version_or_above('12.2.1.1'):
            is1221 = True

        ds_overrides = partition_dict['JdbcSystemResourceOverride']
        for ds_override in ds_overrides:
            self.logger.info('Adding JDBC System Resource Override {0} to Partition {1}',
                             ds_override, partition_name, class_name=self.CLASS_NAME,
                             method_name='_add_jdbc_system_resource_overrides')

            self.wlst_helper.cd(partition_path)
            self.wlst_helper.create(ds_override, 'JdbcSystemResourceOverride')
            self.wlst_helper.cd('JdbcSystemResourceOverride/' + self.wlst_helper.get_quoted_name_for_wlst(ds_override))
            for param in ds_overrides[ds_override]:
                if is1221 and param in model_fields.JDBC_SYSTEM_RESOURCE_OVERRIDE_ATTR_NOT_IN_1221:
                    message = 'Skip setting {0} on partition {1} JdbcSystemResourceOverride {2} because it ' + \
                              'is not supported in WebLogic Server 12.2.1'
                    self.logger.finer(message, param, partition_name, ds_override,
                                      class_name=self.CLASS_NAME,
                                      method_name='_add_jdbc_system_resource_overrides')
                else:
                    self.wlst_helper.set(param, ds_overrides[ds_override][param])

        return

    def _add_jms_system_resource_overrides(self, partition_dict, partition_name, partition_path):
        if dictionary_utils.is_empty_dictionary_element(partition_dict, 'JmsSystemResourceOverride'):
            return

        jms_overrides = partition_dict['JmsSystemResourceOverride']
        for jms_override in jms_overrides:
            self.logger.info('Adding JMS System Resource Override {0} to Partition {1}',
                             jms_override, partition_name, class_name=self.CLASS_NAME,
                             method_name='_add_jms_system_resource_overrides')

            self.wlst_helper.cd(partition_path)
            self.wlst_helper.create(jms_override, 'JmsSystemResourceOverride')
            self.wlst_helper.cd('JmsSystemResourceOverride/' + self.wlst_helper.get_quoted_name_for_wlst(jms_override))
            for param in jms_overrides[jms_override]:
                if not param == 'ForeignServer':
                    self.wlst_helper.set(param, jms_overrides[jms_override][param])

            if 'ForeignServer' in jms_overrides[jms_override]:
                foreign_servers = jms_overrides[jms_override]['ForeignServer']
                for foreign_server in foreign_servers:
                    self.wlst_helper.create(foreign_server, 'ForeignServer')
                    self.wlst_helper.cd('ForeignServer/' + self.wlst_helper.get_quoted_name_for_wlst(foreign_server))
                    for param in foreign_servers[foreign_server]:
                        if param not in model_fields.JMS_FOREIGN_SERVER_OVERRIDE_SUBFOLDERS:
                            if param == 'JndiPropertiesCredentialEncrypted':
                                encrypted = self.wls_helper.encrypt(foreign_servers[foreign_server][param],
                                                                    self.model_context.get_domain_home())
                                self.wlst_helper.set(param, encrypted)
                            else:
                                self.wlst_helper.set(param, foreign_servers[foreign_server][param])

                    for folder in model_fields.JMS_FOREIGN_SERVER_OVERRIDE_SUBFOLDERS:
                        if folder in foreign_servers[foreign_server]:
                            #
                            # FIXME- The self.wlst_helper.create() function is broken for JndiProperty so it is currently
                            # not possible to provision a domain with a JndiProperty.
                            #
                            # See Bugs 25558332 and 25560048
                            #
                            if folder == 'JndiProperty':
                                message = 'ERROR: JmsSystemResourceOverride ' + jms_override + 'Foreign Server ' + \
                                          foreign_server + ' provided a JndiProperty folder. WLST Offline Bugs ' + \
                                          '25558332 and 25560048 prevent this from being provisioned!'
                                raise WLSTException(self.wls_helper.get_wlst_exception_content(message))

                            resources = foreign_servers[foreign_server][folder]
                            for resource in resources:
                                self.wlst_helper.create(resource, folder)
                                self.wlst_helper.cd(folder + '/' + self.wlst_helper.get_quoted_name_for_wlst(resource))
                                for param in resources[resource]:
                                    if param == 'PasswordEncrypted':
                                        encrypted = self.wls_helper.encrypt(resources[resource][param],
                                                                            self.model_context.get_domain_home())
                                        self.wlst_helper.set(param, encrypted)
                                    else:
                                        self.wlst_helper.set(param, resources[resource][param])
                                self.wlst_helper.cd('../..')
                    self.wlst_helper.cd('../..')

        return

    def _add_mail_session_overrides(self, partition_dict, partition_name, partition_path):
        if dictionary_utils.is_empty_dictionary_element(partition_dict, 'MailSessionOverride'):
            return

        mail_overrides = partition_dict['MailSessionOverride']
        for mail_override in mail_overrides:
            self.logger.info('Adding Mail Session Override {0} to Partition {1}', mail_override, partition_name,
                             class_name=self.CLASS_NAME, method_name='_add_mail_session_overrides')

            self.wlst_helper.cd(partition_path)
            self.wlst_helper.create(mail_override, 'MailSessionOverride')
            self.wlst_helper.cd('MailSessionOverride/' + self.wlst_helper.get_quoted_name_for_wlst(mail_override))
            #
            # Bug 25565231 prevents the MailSessionOverrides from having an encrypted password field.
            #
            for param in mail_overrides[mail_override]:
                if not param == 'Properties':
                    self.wlst_helper.set(param, mail_overrides[mail_override][param])

            if not dictionary_utils.is_empty_dictionary_element(mail_overrides[mail_override], 'Properties'):
                properties = mail_overrides[mail_override]['Properties']
                new_props = JProperties()
                for key in properties:
                    new_props.setProperty(key, str(properties[key]))

                self.wlst_helper.set('Properties', new_props)

        return

    def _add_partitions(self):
        if dictionary_utils.is_empty_dictionary_element(self._resources, 'Partition'):
            return

        if not self.wls_helper.is_weblogic_version_or_above('12.2.1'):
            message = 'Partition was specified in the test file but are not supported in ' + \
                      'Weblogic Server version ' + self.wls_helper.wl_version
            raise WLSTException(self.wls_helper.get_wlst_exception_content(message))

        partitions = self._resources['Partition']
        for partition in partitions:
            self.logger.info('Adding Partition {0}', partition,
                             class_name=self.CLASS_NAME, method_name='_add_partitions')

            self.wlst_helper.cd('/')
            self.wlst_helper.create(partition, 'Partition')
            base_path = '/Partition/' + self.wlst_helper.get_quoted_name_for_wlst(partition) + '/'
            self.wlst_helper.cd(base_path)
            for param in partitions[partition]:
                if param not in model_fields.PARTITION_SUBFOLDERS:
                    if param == 'Realm':
                        realm_path = '/SecurityConfiguration/' + self.model_context.get_domain_name() + '/Realm/' + \
                                     self.wlst_helper.get_quoted_name_for_wlst(partitions[partition][param])
                        self.wlst_helper.get_cmo().setRealm(self.wlst_helper.get_mbean_for_wlst_path(realm_path))
                    elif param == 'AvailableTargets':
                        self._set_partition_available_targets(partition, partitions[partition][param])
                    elif param == 'DefaultTargets':
                        self._set_partition_default_targets(partition, partitions[partition][param])
                    elif param == 'ResourceManagerRef':
                        path = '/ResourceManagement/' + \
                               self.wlst_helper.get_quoted_name_for_wlst(self.model_context.get_domain_name()) + \
                               '/ResourceManager/' + \
                               self.wlst_helper.get_quoted_name_for_wlst(partitions[partition][param])
                        self.wlst_helper.set(param, self.wlst_helper.get_mbean_for_wlst_path(path))
                    else:
                        self.logger.info('Setting Partition {0} param {1} to value {2}', partition, param,
                                         partitions[partition][param], class_name=self.CLASS_NAME,
                                         method_name='_add_partitions')
                        self.wlst_helper.set(param, partitions[partition][param])

            location = LocationContext()  # TODO: use partition location instead of base_path

            self.common_deployer.add_partition_work_managers(partitions[partition], partition, 'Partition', base_path)
            self.common_deployer.add_self_tuning(partitions[partition], location)
            self._add_coherence_partition_cache_configs(partitions[partition], partition, base_path)
            self.common_deployer.add_resource_groups(partitions[partition], partition, 'Partition', base_path)
            self._add_jdbc_system_resource_overrides(partitions[partition], partition, base_path)
            self._add_jms_system_resource_overrides(partitions[partition], partition, base_path)
            self._add_mail_session_overrides(partitions[partition], partition, base_path)
            self._add_foreign_jndi_provider_overrides(partitions[partition], partition, base_path)
            self._add_system_file_system(partitions[partition], partition, base_path)
            self._add_user_file_system(partitions[partition], partition, base_path)
            self._add_resource_managers(partitions[partition], partition, 'Partition', base_path)

        return

    def _add_resource_group_templates(self):
        if dictionary_utils.is_empty_dictionary_element(self._resources, 'ResourceGroupTemplate'):
            return

        if not self.wls_helper.is_weblogic_version_or_above('12.2.1'):
            message = 'ResourceGroupTemplate was specified in the test file but are not supported in ' + \
                      'Weblogic Server version ' + self.wls_helper.wl_version
            raise WLSTException(self.wls_helper.get_wlst_exception_content(message))

        # TODO: needs conversion to use aliases. For now, create root location to pass to deploy resources
        location = LocationContext().append_location(RESOURCE_GROUP_TEMPLATE)
        token_name = self.alias_helper.get_name_token(location)
        resource_group_templates = self._resources['ResourceGroupTemplate']
        for resource_group_template in resource_group_templates:
            self.logger.info('Adding Resource Group Template {0}', resource_group_template,
                             class_name=self.CLASS_NAME, method_name='_add_resource_group_templates')

            location.add_name_token(token_name, resource_group_template)
            self.wlst_helper.cd('/')
            self.wlst_helper.create(resource_group_template, 'ResourceGroupTemplate')
            base_path = '/ResourceGroupTemplate/' + self.wlst_helper.get_quoted_name_for_wlst(resource_group_template) + '/'
            self.wlst_helper.cd(base_path)
            for param in resource_group_templates[resource_group_template]:
                if param not in model_fields.RESOURCE_GROUP_TEMPLATE_SUBFOLDERS:
                    self.wlst_helper.set(param, resource_group_templates[resource_group_template][param])

            self.common_deployer.add_resource_group_resources(resource_group_templates[resource_group_template],
                                                              location)
            location.remove_name_token(token_name)
        return

    def _add_resource_management(self):
        if dictionary_utils.is_empty_dictionary_element(self._resources, 'ResourceManagement'):
            return

        if not self.wls_helper.is_weblogic_version_or_above('12.2.1'):
            message = 'ResourceManagement was specified in the test file but are not supported in ' + \
                      'Weblogic Server version ' + self.wls_helper.wl_version
            raise WLSTException(self.wls_helper.get_wlst_exception_content(message))

        resource_managements = self._resources['ResourceManagement']
        if len(resource_managements) > 1:
            number_managements = len(resource_managements)
            message = 'Domain ' + self.model_context.get_domain_name() + ' defined ' + str(number_managements) + \
                      ' ResourceManagement objects but only one is allowed'
            raise WLSTException(self.wls_helper.get_wlst_exception_content(message))

        self.wlst_helper.cd('/')
        self.wlst_helper.create(self.model_context.get_domain_name(), 'ResourceManagement')

        if len(resource_managements['ResourceManager']) > 0:
            base_path = '/ResourceManagement/' + self.model_context.get_domain_name()
            self._add_resource_managers(resource_managements, 'ResourceManagement', 'Domain', base_path)

        return

    def _add_resource_managers(self, parent_dict, parent_name, parent_type, base_path):
        if dictionary_utils.is_empty_dictionary_element(parent_dict, 'ResourceManager'):
            return

        resource_managers = parent_dict['ResourceManager']
        #
        # In a partition, only one ResourceManager is allowed but the domain level
        # ResourceManagement section allows multiple.
        #
        if parent_type != 'ResourceManagement' and len(resource_managers) > 1:
            message = parent_type + ' ' + parent_name + ' specified ' + str(len(resource_managers)) + \
                      ' ResourceManagers but only one is allowed'
            raise WLSTException(self.wls_helper.get_wlst_exception_content(message))

        for resource_manager in resource_managers:
            self.logger.info('Adding Resource Manager {0} to {1} {2}', resource_manager, parent_type, parent_name,
                             class_name=self.CLASS_NAME, method_name='_add_resource_managers')

            self.wlst_helper.cd(base_path)
            self.wlst_helper.create(resource_manager, 'ResourceManager')
            self.wlst_helper.cd('ResourceManager/' + self.wlst_helper.get_quoted_name_for_wlst(resource_manager))
            for param in resource_managers[resource_manager]:
                if param not in model_fields.RESOURCE_MANAGER_SUBFOLDERS:
                    self.wlst_helper.set(param, resource_managers[resource_manager][param])

            if 'CpuUtilization' in resource_managers[resource_manager]:
                cpus = resource_managers[resource_manager]['CpuUtilization']
                if len(cpus) > 1:
                    message = 'ResourceManager ' + resource_manager + ' defined ' + str(len(cpus)) + \
                              ' CpuUtilization policies but only one is allowed'
                    raise WLSTException(self.wls_helper.get_wlst_exception_content(message))

                for cpu in cpus:
                    self.wlst_helper.create(cpu, 'CpuUtilization')
                    self.wlst_helper.cd('CpuUtilization/' + self.wlst_helper.get_quoted_name_for_wlst(cpu))
                    for param in cpus[cpu]:
                        if not (param == 'Trigger' or param == 'FairShareConstraint'):
                            self.wlst_helper.set(param, cpus[cpu][param])

                    cpu_utilization = cpus[cpu]
                    if 'FairShareConstraint' in cpu_utilization:
                        constraints = cpu_utilization['FairShareConstraint']
                        if len(constraints) > 1:
                            message = 'ResourceManager ' + resource_manager + ' defined CpuUtilization policy ' + \
                                      cpu + ' with ' + str(len(constraints)) + \
                                      ' FairShareConstraints but only one is allowed'
                            raise WLSTException(self.wls_helper.get_wlst_exception_content(message))

                        for constraint in constraints:
                            self.wlst_helper.create(constraint, 'FairShareConstraint')
                            self.wlst_helper.cd('FairShareConstraint/' + self.wlst_helper.get_quoted_name_for_wlst(constraint))
                            for param in constraints[constraint]:
                                self.wlst_helper.set(param, constraints[constraint][param])
                            self.wlst_helper.cd('../..')

                    if 'Trigger' in cpu_utilization:
                        triggers = cpu_utilization['Trigger']
                        for trigger in triggers:
                            self.wlst_helper.create(trigger, 'Trigger')
                            self.wlst_helper.cd('Trigger/' + self.wlst_helper.get_quoted_name_for_wlst(trigger))
                            for param in triggers[trigger]:
                                self.wlst_helper.set(param, triggers[trigger][param])
                            self.wlst_helper.cd('../..')

                    self.wlst_helper.cd('../..')

            if 'FileOpen' in resource_managers[resource_manager]:
                files_open = resource_managers[resource_manager]['FileOpen']
                if len(files_open) > 1:
                    message = 'ResourceManager ' + resource_manager + ' defined ' + str(len(files_open)) + \
                              ' FileOpen policies but only one is allowed'
                    raise WLSTException(self.wls_helper.get_wlst_exception_content(message))

                for file_open in files_open:
                    self.wlst_helper.create(file_open, 'FileOpen')
                    self.wlst_helper.cd('FileOpen/' + self.wlst_helper.get_quoted_name_for_wlst(file_open))
                    for param in files_open[file_open]:
                        if not param == 'Trigger':
                            self.wlst_helper.set(param, files_open[file_open][param])

                    if 'Trigger' in files_open[file_open]:
                        triggers = files_open[file_open]['Trigger']
                        for trigger in triggers:
                            self.wlst_helper.create(trigger, 'Trigger')
                            self.wlst_helper.cd('Trigger/' + self.wlst_helper.get_quoted_name_for_wlst(trigger))
                            for param in triggers[trigger]:
                                self.wlst_helper.set(param, triggers[trigger][param])
                            self.wlst_helper.cd('../..')
                    self.wlst_helper.cd('../..')

            if 'HeapRetained' in resource_managers[resource_manager]:
                heaps_retained = resource_managers[resource_manager]['HeapRetained']
                if len(heaps_retained) > 1:
                    message = 'ResourceManager ' + resource_manager + ' defined ' + str(len(heaps_retained)) + \
                              ' HeapRetained policies but only one is allowed'
                    raise WLSTException(self.wls_helper.get_wlst_exception_content(message))

                for heap_retained in heaps_retained:
                    self.wlst_helper.create(heap_retained, 'HeapRetained')
                    self.wlst_helper.cd('HeapRetained/' + self.wlst_helper.get_quoted_name_for_wlst(heap_retained))
                    for param in heaps_retained[heap_retained]:
                        if not (param == 'Trigger' or param == 'FairShareConstraint'):
                            self.wlst_helper.set(param, heaps_retained[heap_retained][param])

                    if 'FairShareConstraint' in heaps_retained[heap_retained]:
                        constraints = heaps_retained[heap_retained]['FairShareConstraint']
                        if len(constraints) > 1:
                            message = 'ResourceManager ' + resource_manager + ' defined HeapRetained policy ' + \
                                      heap_retained + ' with ' + str(len(constraints)) + \
                                      ' FairShareConstraints but only one is allowed'
                            raise WLSTException(self.wls_helper.get_wlst_exception_content(message))

                        for constraint in constraints:
                            self.wlst_helper.create(constraint, 'FairShareConstraint')
                            self.wlst_helper.cd('FairShareConstraint/' + self.wlst_helper.get_quoted_name_for_wlst(constraint))
                            for param in constraints[constraint]:
                                self.wlst_helper.set(param, constraints[constraint][param])
                            self.wlst_helper.cd('../..')

                    if 'Trigger' in heaps_retained[heap_retained]:
                        triggers = heaps_retained[heap_retained]['Trigger']
                        for trigger in triggers:
                            self.wlst_helper.create(trigger, 'Trigger')
                            self.wlst_helper.cd('Trigger/' + self.wlst_helper.get_quoted_name_for_wlst(trigger))
                            for param in triggers[trigger]:
                                self.wlst_helper.set(param, triggers[trigger][param])
                            self.wlst_helper.cd('../..')
                    self.wlst_helper.cd('../..')

            if 'RestartLoopProtection' in resource_managers[resource_manager]:
                protections = resource_managers[resource_manager]['RestartLoopProtection']
                if len(protections) > 1:
                    message = 'ResourceManager ' + resource_manager + ' defined ' + str(len(protections)) + \
                              ' RestartLoopProtection policies but only one is allowed'
                    raise WLSTException(self.wls_helper.get_wlst_exception_content(message))

                for protection in protections:
                    self.wlst_helper.create(protection, 'RestartLoopProtection')
                    self.wlst_helper.cd('RestartLoopProtection/' + self.wlst_helper.get_quoted_name_for_wlst(protection))
                    for param in protections[protection]:
                        self.wlst_helper.set(param, protections[protection][param])
                    self.wlst_helper.cd('../..')

        return

    def _add_system_file_system(self, partition_dict, partition_name, partition_path):
        # In WLS 12.2.1, self.wlst_helper.create() fails so skip it
        if dictionary_utils.is_empty_dictionary_element(partition_dict, 'SystemFileSystem') or \
                not self.wls_helper.is_weblogic_version_or_above('12.2.1.1'):
            return

        file_systems = partition_dict['SystemFileSystem']
        if len(file_systems) > 1:
            message = 'Partition + ' + partition_name + ' specified ' + str(len(file_systems)) + \
                      ' SystemFileSystems but only one is allowed'
            raise WLSTException(self.wls_helper.get_wlst_exception_content(message))

        for file_system in file_systems:
            self.logger.info('Adding System File System {0} to Partition {1}', file_system, partition_name,
                             class_name=self.CLASS_NAME, method_name='_add_system_file_system')

            self.wlst_helper.cd(partition_path)
            self.wlst_helper.create(file_system, 'SystemFileSystem')
            self.wlst_helper.cd('SystemFileSystem/' + self.wlst_helper.get_quoted_name_for_wlst(file_system))
            for param in file_systems[file_system]:
                if param == 'Root':
                    self.wlst_helper.set(param, self.model_context.replace_token_string(file_systems[file_system][param]))
                else:
                    self.wlst_helper.set(param, file_systems[file_system][param])

        return

    def _add_user_file_system(self, partition_dict, partition_name, partition_path):
        # In WLS 12.2.1, self.wlst_helper.create() fails so skip it
        if dictionary_utils.is_empty_dictionary_element(partition_dict, 'UserFileSystem') or \
                not self.wls_helper.is_weblogic_version_or_above('12.2.1.1'):
            return

        file_systems = partition_dict['UserFileSystem']
        if len(file_systems) > 1:
            message = 'Partition + ' + partition_name + ' specified ' + str(len(file_systems)) + \
                      ' UserFileSystems but only one is allowed'
            raise WLSTException(self.wls_helper.get_wlst_exception_content(message))

        for file_system in file_systems:
            self.logger.info('Adding User File System {0} to Partition {1}', file_system, partition_name,
                             class_name=self.CLASS_NAME, method_name='_add_user_file_system')

            self.wlst_helper.cd(partition_path)
            self.wlst_helper.create(file_system, 'UserFileSystem')
            self.wlst_helper.cd('UserFileSystem/' + self.wlst_helper.get_quoted_name_for_wlst(file_system))
            for param in file_systems[file_system]:
                if param == 'Root':
                    self.wlst_helper.set(param, self.model_context.replace_token_string(file_systems[file_system][param]))
                else:
                    self.wlst_helper.set(param, file_systems[file_system][param])

        return

    def _set_partition_available_targets(self, partition_name, available_targets):
        if available_targets is None or len(available_targets) == 0:
            return

        self.logger.entering(partition_name, available_targets,
                             class_name=self.CLASS_NAME, method_name='_set_partition_available_targets')
        #
        # In 12.2.1.0, self.wlst_helper.set() with a comma-separated string does not work.
        # The workaround is to use cmo.setAvailableTargets(), which takes a list of MBeans.
        #
        if self.wls_helper.is_weblogic_version_or_above('12.2.1.1'):
            self.wlst_helper.set('AvailableTargets', available_targets)
        else:
            targets = []
            for target in available_targets.split(','):
                targets.append(self.wlst_helper.get_mbean_for_wlst_path("/VirtualTarget/" +
                                                                        self.wlst_helper.get_quoted_name_for_wlst(target)))
            self.wlst_helper.get_cmo().setAvailableTargets(targets)

        self.logger.exiting(class_name=self.CLASS_NAME, method_name='_set_partition_available_targets')
        return

    def _set_partition_default_targets(self, partition_name, default_targets):
        if default_targets is None or len(default_targets) == 0:
            return

        self.logger.entering(partition_name, default_targets,
                             class_name=self.CLASS_NAME, method_name='_set_partition_default_targets')
        #
        # In 12.2.1.0, self.wlst_helper.set() with a comma-separated string does not work.
        # The workaround is to use cmo.setDefaultTargets(), which takes a list of MBeans.
        #
        if self.wls_helper.is_weblogic_version_or_above('12.2.1.1'):
            self.wlst_helper.set('DefaultTargets', default_targets)
        else:
            targets = []
            for target in default_targets.split(','):
                targets.append(self.wlst_helper.get_mbean_for_wlst_path("/VirtualTarget/" +
                                                                        self.wlst_helper.get_quoted_name_for_wlst(target)))
            self.wlst_helper.get_cmo().setDefaultTargets(targets)

        self.logger.exiting(class_name=self.CLASS_NAME, method_name='_set_partition_default_targets')
        return
