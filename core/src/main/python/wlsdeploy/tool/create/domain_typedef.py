"""
Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
import re

from java.lang import IllegalArgumentException

from oracle.weblogic.deploy.json import JsonException

from wlsdeploy.exception import exception_helper
from wlsdeploy.json.json_translator import JsonToPython
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util.targeting_types import TargetingType
from wlsdeploy.tool.util.topology_profiles import TopologyProfile
from wlsdeploy.util import path_utils
from wlsdeploy.util.exit_code import ExitCode
from wlsdeploy.util.weblogic_helper import WebLogicHelper

CREATE_DOMAIN = 'createDomain'
UPDATE_DOMAIN = 'updateDomain'
NOT_SUPPORTED = 'NOT_SUPPORTED'


class DomainTypedef(object):
    """
    The class that processes domain type definitions.
    """
    __class_name = 'DomainTypedef'

    __domain_typedef_extension = '.json'

    JRF_TEMPLATE_REGEX = "^(.*jrf_template[0-9._]*\\.jar)|^(Oracle JRF)$"
    RESTRICTED_JRF_TEMPLATE_REGEX = "^(Oracle Restricted JRF)$"
    JRF_SERVER_GROUP = 'JRF-MAN-SVR'

    def __init__(self, program_name, domain_type):
        """
        The DomainTypedef constructor.
        :param program_name: the name of the program create this object
        :param domain_type: the domain type
        """
        _method_name = '__init__'

        self._logger = PlatformLogger('wlsdeploy.create')
        self._program_name = program_name
        self._domain_type = domain_type
        self.wls_helper = WebLogicHelper(self._logger)

        file_name = domain_type + self.__domain_typedef_extension
        self._domain_typedef_filename = path_utils.find_config_path(os.path.join('typedefs', file_name))

        # No need to explicitly validate the filename since the JsonToPython constructor does that...
        try:
            json_parser = JsonToPython(self._domain_typedef_filename)
            self._domain_typedefs_dict = json_parser.parse()
        except IllegalArgumentException, iae:
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                                       'WLSDPLY-12300', self._program_name, self._domain_type,
                                                       self._domain_typedef_filename, iae.getLocalizedMessage(),
                                                       error=iae)
            self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        except JsonException, je:
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                                       'WLSDPLY-12301', self._program_name, self._domain_type,
                                                       self._domain_typedef_filename, je.getLocalizedMessage(),
                                                       error=je)
            self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        self._domain_typedef = self.__get_version_typedef()
        self._paths_resolved = False
        self._model_context = None
        self._version_typedef_name = None

        self._targeting_type = self._resolve_targeting_type()

        if 'system-elements' in self._domain_typedefs_dict:
            self._system_elements = self._domain_typedefs_dict['system-elements']
        else:
            self._system_elements = {}

        self._topology_profile = self._resolve_topology_profile()

    def set_model_context(self, model_context):
        """
        Set the model context object.
        :param model_context: the model context object to use
        :raises: CreateException: if an error occurs resolving the paths
        """
        if self._model_context is None:
            self._model_context = model_context
            self.__resolve_paths()

    def get_domain_type(self):
        """
        Get the name of the domain type, such as "WLS".
        :return: the name of the domain type
        """
        return self._domain_type

    def get_topology_profile(self):
        """
        Get the topology profile for the domain type, if any.
        :return: the topology profile or None if no topology profile is specified
        """
        return self._topology_profile

    def has_jrf_resources(self):
        """
        Determine if the domain type has domain resources from either the JRF or Restricted JRF templates.
        :return: True if the domain type has resources from one of the JRF type
        """
        return self.is_jrf_domain_type() or self.is_restricted_jrf_domain_type()

    def is_jrf_domain_type(self):
        """
        Determine if this is a JRF domain type by checking for the JRF extension template or
        JRF SVR GrOUP.
        This returns False for the Restricted JRF domain type.
        :return: True if the JRF template is present
        """
        if self.is_restricted_jrf_domain_type():
            return False
        for template in self.get_extension_templates():
            if re.match(self.JRF_TEMPLATE_REGEX, template):
                return True
        if self.JRF_SERVER_GROUP in self.get_server_groups_to_target():
            return True
        return False

    def is_restricted_jrf_domain_type(self):
        """
        Determine if this domain type applies the Restricted JRF template.
        :return: True if the Restricted JRF template is in the extension templates list
        """
        for template in self.get_extension_templates():
            if re.match(self.RESTRICTED_JRF_TEMPLATE_REGEX, template):
                return True
            return False

    def get_base_template(self):
        """
        Get the base template to use when create the domain.
        :return: the base template to use
        :raises: CreateException: if an error occurs resolving the paths
        """
        self.__resolve_paths()
        return self._domain_typedef['baseTemplate']

    def has_extension_templates(self):
        """
        Determine if the domain type has extension templates.
        :return: True if the domain type will apply extension templates
        """
        ets = self.get_extension_templates()
        return ets is not None and len(ets) > 0

    def get_extension_templates(self):
        """
        Get the list of extension templates to apply when create/extending the domain.
        :return: the list of extension templates, or an empty list if no extension templates are needed.
        :raises: CreateException: if an error occurs resolving the paths
        """
        self.__resolve_paths()
        return list(self._domain_typedef['extensionTemplates'])

    def get_custom_extension_templates(self):
        """
        Get the list of custom extension templates to apply when create/extending the domain.
        :return: the list of custom extension templates, or an empty list if no extension templates are needed.
        :raises: CreateException: if an error occurs resolving the paths
        """
        self.__resolve_paths()
        return list(self._domain_typedef['customExtensionTemplates'])

    def get_server_groups_to_target(self):
        """
        Get the list of server groups to target to the managed servers in the domain.
        :return: the list of server groups to target, or an empty list if there are none
        :raises: CreateException: if an error occurs resolving the paths
        """
        self.__resolve_paths()
        return list(self._domain_typedef['serverGroupsToTarget'])

    def get_dynamic_cluster_server_groups(self):
        """
        For versions of WebLogic Server less than 12.2.1.4 that support associating a single server group to
        the dynamic clusters in the domain. In 12.2.1.4 can associate more than one server group.
        :return: the server group to be targeted to a dynamic cluster, or None if no server group to target
        :raises: CreateException: if an error occurs resolving the paths
        """
        self.__resolve_paths()
        return list(self._domain_typedef['dynamicClusterServerGroupsToTarget'])

    def get_rcu_schemas(self):
        """
        Get the list of RCU schemas used by the domain type.
        :return: the list of RCU schemas to create
        """
        # No need to resolve the paths and we need this to work prior to
        # resolution for create.py argument processing.
        return list(self._domain_typedef['rcuSchemas'])

    def required_rcu(self):
        """
        Test whether it requires RCU components.
        :return: true if it requires rcu components
        """
        # No need to resolve the paths and we need this to work prior to
        # resolution for create.py argument processing.
        return 'rcuSchemas' in self._domain_typedef and len(self._domain_typedef['rcuSchemas']) > 0

    def get_targeting(self):
        """
        Get the targeting type for the domain, or None if not specified.
        :return: the TargetingType enum value for the domain, or None
        """
        return self._targeting_type

    def is_system_app(self, name):
        """
        Determine if the specified name matches a WLS system application.
        :param name: the name to be checked
        :return: True if the name matches a system application, False otherwise
        """
        return self._is_system_name(name, 'apps')

    def is_system_coherence_cluster(self, name):
        """
        Determine if the specified name matches a WLS system Coherence cluster.
        :param name: the name to be checked
        :return: True if the name matches a system Coherence cluster, False otherwise
        """
        return self._is_system_name(name, 'coherence-clusters')

    def is_system_datasource(self, name):
        """
        Determine if the specified name matches a WLS system datasource.
        :param name: the name to be checked
        :return: True if the name matches a system datasource, False otherwise
        """
        return self._is_system_name(name, 'datasources')

    def is_system_file_store(self, name):
        """
        Determine if the specified name matches a WLS system file store.
        :param name: the name to be checked
        :return: True if the name matches a system file store, False otherwise
        """
        return self._is_system_name(name, 'file-stores')

    def is_system_jms(self, name):
        """
        Determine if the specified name matches a WLS system JMS resource.
        :param name: the name to be checked
        :return: True if the name matches a system JMS resource, False otherwise
        """
        return self._is_system_name(name, 'jms')

    def is_system_jms_server(self, name):
        """
        Determine if the specified name matches a WLS system JMS server.
        :param name: the name to be checked
        :return: True if the name matches a system JMS server, False otherwise
        """
        return self._is_system_name(name, 'jms-servers')

    def is_system_shared_library(self, name):
        """
        Determine if the specified name matches a WLS system shared library.
        :param name: the name to be checked
        :return: True if the name matches a system shared library, False otherwise
        """
        return self._is_system_name(name, 'shared-libraries')

    def is_system_shutdown_class(self, name):
        """
        Determine if the specified name matches a WLS system shutdown class.
        :param name: the name to be checked
        :return: True if the name matches a system shutdown class, False otherwise
        """
        return self._is_system_name(name, 'shutdown-classes')

    def is_system_startup_class(self, name):
        """
        Determine if the specified name matches a WLS system startup class.
        :param name: the name to be checked
        :return: True if the name matches a system startup class, False otherwise
        """
        return self._is_system_name(name, 'startup-classes')

    def is_system_wldf(self, name):
        """
        Determine if the specified name matches a WLS system WLDF resource.
        :param name: the name to be checked
        :return: True if the name matches a system WLDF resource, False otherwise
        """
        return self._is_system_name(name, 'wldf')

    def is_security_configuration_supported(self):
        """
        Determine if the security configuration can be configured. Currently, update domain does not
        support configuration of the SecurityConfiguration, and 11g create domain does not support
        configuration of the SecurityConfiguration

        :return: True if the security realm can be configured
        """
        return self._program_name != UPDATE_DOMAIN

    def _is_system_name(self, name, key):
        """
        Determine if the specified name matches a WLS name of the specified type key.
        :param name: the name to be checked
        :param key: the key of the type to be checked against
        :return: True if the name matches a system name, False otherwise
        """
        if key in self._system_elements:
            system_names = self._system_elements[key]
            for system_name in system_names:
                matched = re.match(system_name, name)
                if matched is not None:
                    return True

        return False

    def __resolve_paths(self):
        """
        Resolve any tokens in the template paths.
        :raises: CreateException: if an error occurs resolving the paths
        """
        _method_name = '__resolve_paths'

        if not self._paths_resolved:
            if self._model_context is None:
                ex = exception_helper.create_create_exception('WLSDPLY-12302')
                self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex

            if 'baseTemplate' in self._domain_typedef:
                self._domain_typedef['baseTemplate'] = \
                    self._model_context.replace_token_string(self._domain_typedef['baseTemplate'])
            else:
                ex = exception_helper.create_create_exception('WLSDPLY-12303', self._domain_type,
                                                              self._domain_typedef_filename, self._version_typedef_name)
                self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex

            if 'extensionTemplates' in self._domain_typedef:
                extension_templates = self._domain_typedef['extensionTemplates']
                resolved_templates = []
                for extension_template in extension_templates:
                    resolved_templates.append(self._model_context.replace_token_string(extension_template))
                self._domain_typedef['extensionTemplates'] = resolved_templates
            else:
                self._domain_typedef['extensionTemplates'] = []

            if 'customExtensionTemplates' in self._domain_typedef:
                extension_templates = self._domain_typedef['customExtensionTemplates']
                resolved_templates = []
                for extension_template in extension_templates:
                    resolved_templates.append(self._model_context.replace_token_string(extension_template))
                self._domain_typedef['customExtensionTemplates'] = resolved_templates
            else:
                self._domain_typedef['customExtensionTemplates'] = []

            if 'serverGroupsToTarget' not in self._domain_typedef:
                self._domain_typedef['serverGroupsToTarget'] = []

            if 'dynamicClusterServerGroupsToTarget' not in self._domain_typedef:
                self._domain_typedef['dynamicClusterServerGroupsToTarget'] = []

            if 'rcuSchemas' not in self._domain_typedef:
                self._domain_typedef['rcuSchemas'] = []

            self._paths_resolved = True

    def __get_version_typedef(self):
        """
        Get the domain typedef that matches the current WLS version.
        :return: the version-specific domain typedef
        :raises: CreateException: if an error occurs resolving the paths
        """
        _method_name = '__get_version_typedef'

        if 'versions' not in self._domain_typedefs_dict:
            ex = exception_helper.create_create_exception('WLSDPLY-12304', self._domain_type,
                                                          self._domain_typedef_filename)
            self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        elif 'definitions' not in self._domain_typedefs_dict:
            ex = exception_helper.create_create_exception('WLSDPLY-12305', self._domain_type,
                                                          self._domain_typedef_filename)
            self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        self._version_typedef_name = self.__match_version_typedef(self._domain_typedefs_dict['versions'])

        if self._version_typedef_name in self._domain_typedefs_dict['definitions']:
            result = self._domain_typedefs_dict['definitions'][self._version_typedef_name]
        else:
            ex = exception_helper.create_create_exception('WLSDPLY-12306', self._domain_type,
                                                          self._domain_typedef_filename, self._version_typedef_name)
            self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result

    def __match_version_typedef(self, versions_dict):
        """
        Match the version typedef to the current WLS version
        :param versions_dict: the versions dictionary
        :return: the matching version typedef
        :raises: CreateException: if an error occurs resolving the paths
        """
        _method_name = '__match_version_typedef'

        self._logger.entering(versions_dict, class_name=self.__class_name, method_name=_method_name)
        if len(versions_dict) == 0:
            ex = exception_helper.create_create_exception('WLSDPLY-12307', self._domain_type,
                                                          self._domain_typedef_filename)
            self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        wls_version = self.wls_helper.get_actual_weblogic_version()
        self._logger.fine('WLSDPLY-12310', wls_version, class_name=self.__class_name, method_name=_method_name)

        result = None
        if wls_version in versions_dict:
            result = versions_dict[wls_version]
        else:
            new_version = self.wls_helper.get_next_higher_order_version_number(wls_version)
            while new_version is not None:
                if new_version in versions_dict:
                    result = versions_dict[new_version]
                    self._logger.finer('WLSDPLY-12308', self._domain_type, self._domain_typedef_filename,
                                       new_version, wls_version, class_name=self.__class_name, method_name=_method_name)
                    break
                else:
                    new_version = self.wls_helper.get_next_higher_order_version_number(new_version)

            if result is None:
                ex = exception_helper.create_create_exception('WLSDPLY-12309', self._domain_type,
                                                              self._domain_typedef_filename, wls_version)
                self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex
        if result == NOT_SUPPORTED:
            ex = exception_helper.create_create_exception('WLSDPLY-12313', self._domain_type, wls_version)
            self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        self._logger.exiting(self.__class_name, _method_name, result)
        return result

    def _resolve_targeting_type(self):
        """
        Determine the targeting type based on the value in the definition.
        Check for problems or incompatibilities.
        :return: the matching TargetType enum value
        :raises: ClaException: if there are problems or incompatibilities
        """
        _method_name = '_resolve_targeting_type'

        if 'targeting' not in self._domain_typedef:
            return None

        targeting_text = self._domain_typedef['targeting']

        # there are no valid targeting types for version 12c and up
        if self.wls_helper.is_set_server_groups_supported():
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                                       'WLSDPLY-12311', targeting_text, self._domain_typedef_filename,
                                                       self.wls_helper.get_weblogic_version())
            self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        # if specified, targeting must be one of the known types
        if targeting_text not in TargetingType:
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                                       'WLSDPLY-12312', targeting_text, self._domain_typedef_filename)
            self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        return TargetingType[targeting_text]

    def _resolve_topology_profile(self):
        """
        Determine the topology profile based on the value in the typedef file.

        :return: the matching topology profile enum value
        :raises: ClaException: if there are problems or incompatibilities
        """
        _method_name = '_resolve_topology_profile'

        if 'topologyProfile' not in self._domain_typedefs_dict:
            return None
        topology_profile = self._domain_typedefs_dict['topologyProfile'];

        # there are no valid topology profiles for versions 12.1.x and below
        if not self.wls_helper.is_topology_profile_supported():
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                                       'WLSDPLY-12314', topology_profile, self._domain_typedef_filename,
                                                       self.wls_helper.get_weblogic_version())
            self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        # if specified, toppology profile must be one of the known types
        if topology_profile not in TopologyProfile:
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                                       'WLSDPLY-12315', topology_profile, self._domain_typedef_filename)
            self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        return topology_profile
