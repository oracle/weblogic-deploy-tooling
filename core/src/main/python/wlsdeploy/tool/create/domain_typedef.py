"""
Copyright (c) 2017, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
import re

from java.lang import IllegalArgumentException
from java.io import File

from oracle.weblogic.deploy.json import JsonException

from wlsdeploy.exception import exception_helper
from wlsdeploy.json.json_translator import JsonToPython
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util.targeting_types import TargetingType
from wlsdeploy.tool.util.topology_profiles import TopologyProfile
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import path_helper
from wlsdeploy.util.exit_code import ExitCode
from wlsdeploy.util.weblogic_helper import WebLogicHelper

IS_WINDOWS = File.separatorChar == '\\'

CREATE_DOMAIN = 'createDomain'
DISCOVER_DOMAIN = 'discoverDomain'
NOT_SUPPORTED = 'NOT_SUPPORTED'

POST_CREATE_RCU_SCHEMAS_LIFECYCLE_HOOK = exception_helper.get_message('WLSDPLY-12323')
POST_CREATE_DOMAIN_LIFECYCLE_HOOK = exception_helper.get_message('WLSDPLY-12324')

def _get_logger_name(program_name):
    logger_name = 'wlsdeploy.create'
    if program_name == DISCOVER_DOMAIN:
        logger_name = 'wlsdeploy.discover'
    return logger_name


class DomainTypedef(object):
    """
    The class that processes domain type definitions.
    """
    __class_name = 'DomainTypedef'

    __domain_typedef_extension = '.json'

    JRF_TEMPLATE_REGEX = "^(.*jrf_template[0-9._]*\\.jar)|^(Oracle JRF)$"
    RESTRICTED_JRF_TEMPLATE_REGEX = "^(Oracle Restricted JRF)$"
    JRF_SERVER_GROUP = 'JRF-MAN-SVR'

    __key_mapping_table = {
        'apps': '/Application',
        'coherence-clusters': '/CoherenceClusterSystemResource',
        'datasources': '/JDBCSystemResource',
        'file-stores': '/FileStore',
        'jms': '/JMSSystemResource',
        'jms-server': '/JMSServer',
        'shared-libraries': '/Library',
        'shutdown-classes': '/ShutdownClass',
        'startup-classes': '/StartupClass',
        'wldf': '/WLDFSystemResource'
    }

    def __init__(self, program_name, domain_type, exit_context=False):
        """
        The DomainTypedef constructor.
        :param program_name: the name of the program create this object
        :param domain_type: the domain type
        :param exit_context: if the typedef is being created only in the context of the
            exit model_context where the actual domain type is not yet known and has been
            defaulted to WLS.  In this situation, we should suppress logging about the
            domain type.
        """
        _method_name = '__init__'

        self._logger = PlatformLogger(_get_logger_name(program_name))
        self._program_name = program_name
        self._domain_type = domain_type
        self._initialization_finished = False
        self.wls_helper = None

        file_name = domain_type + self.__domain_typedef_extension
        _path_helper = path_helper.get_path_helper()
        self._domain_typedef_filename = \
            _path_helper.find_local_config_path(_path_helper.local_join('typedefs', file_name))

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

        self._version_typedef_name = None
        self._paths_resolved = False
        self._model_context = None
        self._offline_wls_version = None

        self._domain_typedef = None
        self._targeting_type = None
        self._post_create_rcu_schemas_script_dict = None
        self._post_create_domain_script_dict = None
        self._excluded_locations_binaries_to_archive = list()
        self._discover_filters = {}
        self._topology_profile = None

        if exit_context:
            self._initialization_finished = True
        elif program_name == 'createDomain':
            # createDomain needs access to the rcuSchemas list from the typedef during process_args.
            # Since createDomain is always a local operation, just set the wls_helper and call the
            # code needed to prepare the typedef enough for process_args to complete successfully.
            # tool_main will force re-initialization after process_args completes.
            self.wls_helper = WebLogicHelper(self._logger)
            self._domain_typedef = self.__get_version_typedef()

        # else: caller is responsible for calling finish_initialization() once the model_context
        # object has the remote server's version.  This is typically handled by the
        # model_context object's complete_initialization() method.

    def finish_initialization(self, model_context):
        _method_name = '__finish_initialization'
        if not self._initialization_finished:
            self._model_context = model_context
            self.wls_helper = self._model_context.get_weblogic_helper()
            self._domain_typedef = self.__get_version_typedef()
            self._targeting_type = self._resolve_targeting_type()
            self.__resolve_paths()

            if 'postCreateRcuSchemasScript' in self._domain_typedef:
                if 'rcuSchemas' in self._domain_typedef and len(self._domain_typedef['rcuSchemas']) > 0:
                    self._logger.info('WLSDPLY-12326', self._domain_type, self._domain_typedef_filename,
                                      self._version_typedef_name, class_name=self.__class_name, method_name=_method_name)
                    self._post_create_rcu_schemas_script_dict = self._domain_typedef['postCreateRcuSchemasScript']
                else:
                    self._logger.info('WLSDPLY-12327', self._domain_type, self._domain_typedef_filename,
                                      self._version_typedef_name, class_name=self.__class_name, method_name=_method_name)

            else:
                self._logger.info('WLSDPLY-12328', self._domain_type, self._domain_typedef_filename,
                                  self._version_typedef_name, class_name=self.__class_name, method_name=_method_name)
                self._post_create_rcu_schemas_script_dict = None


            if 'postCreateDomainScript' in self._domain_typedef:
                self._logger.info('WLSDPLY-12320', self._domain_type, self._domain_typedef_filename,
                                  self._version_typedef_name, class_name=self.__class_name, method_name=_method_name)
                self._post_create_domain_script_dict = self._domain_typedef['postCreateDomainScript']
            else:
                self._logger.info('WLSDPLY-12321', self._domain_type, self._domain_typedef_filename,
                                  self._version_typedef_name, class_name=self.__class_name, method_name=_method_name)
                self._post_create_domain_script_dict = None

            if 'discoverExcludedBinariesList' in self._domain_typedef and \
                    len(self._domain_typedef['discoverExcludedBinariesList']) > 0:
                self._logger.info('WLSDPLY-12330', self._domain_type, self._domain_typedef_filename,
                                  self._version_typedef_name, len(self._domain_typedef['discoverExcludedBinariesList']),
                                  class_name=self.__class_name, method_name=_method_name)
                self._excluded_locations_binaries_to_archive = self._domain_typedef['discoverExcludedBinariesList']
            else:
                self._logger.info('WLSDPLY-12331', self._domain_type, self._domain_typedef_filename,
                                  self._version_typedef_name, class_name=self.__class_name, method_name=_method_name)
                self._excluded_locations_binaries_to_archive = list()

            if 'discover-filters' in self._domain_typedefs_dict:
                if 'system-elements' in self._domain_typedefs_dict:
                    self._logger.notification('WLSDPLY-12317', self._domain_typedef_filename)
                self._discover_filters = self._domain_typedefs_dict['discover-filters']
            elif 'system-elements' in self._domain_typedefs_dict:
                # Leave this until at least WDT 5.0 - rpatrick
                self._logger.deprecation('WLSDPLY-12318', self._domain_typedef_filename)
                self._discover_filters = self._translate_system_elements(self._domain_typedefs_dict['system-elements'])
            else:
                self._discover_filters = {}

            self._topology_profile = self._resolve_topology_profile()
            self._initialization_finished = True

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

    def is_jrf_installed(self):
        """
        Determine if this is domain type has JRF installed, based on a flag in the typedef file.
        If this is not specified in the typedef file, the default is True.
        :return: the value of the "isJrfInstalled" flag, or True if not specified
        """
        jrf_installed = dictionary_utils.get_element(self._domain_typedef, 'isJrfInstalled')
        if jrf_installed is None:
            jrf_installed = True
        return jrf_installed

    def has_jrf_with_file_store(self):
        """
        Determine if this domain type has JRF installed and uses a file store.
        :return: True if the domain type has JRF installed and uses a file store, False otherwise
        """
        return self.is_jrf_installed() and not self.get_rcu_schemas()

    def has_jrf_with_database_store(self):
        """
        Determine if this domain type has JRF installed and uses a database store.
        :return: True if the domain type has JRF installed and uses a database store, False otherwise
        """
        return self.is_jrf_installed() and bool(self.get_rcu_schemas())

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

    def requires_rcu(self):
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

    def get_post_create_rcu_schemas_script(self):
        """
        Get the script to run after RCU schema creation is finished.
        :return: the platform-specific script to run, or None
        """
        _method_name = 'get_post_create_domain_script'

        self._logger.entering(class_name=self.__class_name, method_name=_method_name)
        result = None
        if self._post_create_rcu_schemas_script_dict is None:
            return result

        if self._model_context is None:
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-12302')
            self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        if IS_WINDOWS:
            if 'windowsScript' in self._post_create_rcu_schemas_script_dict:
                script = self._post_create_rcu_schemas_script_dict['windowsScript']
                result = self._model_context.replace_token_string(script)
                self._logger.info('WLSDPLY-12329', self._domain_type, self._domain_typedef_filename,
                                  self._version_typedef_name, 'windowsScript', script, result,
                                  class_name=self.__class_name, method_name=_method_name)
            else:
                self._logger.info('WLSDPLY-12325', self._domain_type, self._domain_typedef_filename,
                                  self._version_typedef_name, 'windowsScript',
                                  class_name=self.__class_name, method_name=_method_name)
        else:
            if 'unixScript' in self._post_create_rcu_schemas_script_dict:
                script = self._post_create_rcu_schemas_script_dict['unixScript']
                result = self._model_context.replace_token_string(script)
                self._logger.info('WLSDPLY-12329', self._domain_type, self._domain_typedef_filename,
                                  self._version_typedef_name, 'unixScript', script, result,
                                  class_name=self.__class_name, method_name=_method_name)
            else:
                self._logger.info('WLSDPLY-12325', self._domain_type, self._domain_typedef_filename,
                                  self._version_typedef_name, 'unixScript',
                                  class_name=self.__class_name, method_name=_method_name)

        self._logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def get_post_create_domain_script(self):
        """
        Get the script to run after domain creation is finished.
        :return: the platform-specific script to run, or None
        """
        _method_name = 'get_post_create_domain_script'

        self._logger.entering(class_name=self.__class_name, method_name=_method_name)
        result = None
        if self._post_create_domain_script_dict is None:
            return result

        if self._model_context is None:
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-12302')
            self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        if IS_WINDOWS:
            if 'windowsScript' in self._post_create_domain_script_dict:
                script = self._post_create_domain_script_dict['windowsScript']
                result = self._model_context.replace_token_string(script)
                self._logger.info('WLSDPLY-12322', self._domain_type, self._domain_typedef_filename,
                                  self._version_typedef_name, 'windowsScript', script, result,
                                  class_name=self.__class_name, method_name=_method_name)
            else:
                self._logger.info('WLSDPLY-12319', self._domain_type, self._domain_typedef_filename,
                                  self._version_typedef_name, 'windowsScript',
                                  class_name=self.__class_name, method_name=_method_name)
        else:
            if 'unixScript' in self._post_create_domain_script_dict:
                script = self._post_create_domain_script_dict['unixScript']
                result = self._model_context.replace_token_string(script)
                self._logger.info('WLSDPLY-12322', self._domain_type, self._domain_typedef_filename,
                                  self._version_typedef_name, 'unixScript', script, result,
                                  class_name=self.__class_name, method_name=_method_name)
            else:
                self._logger.info('WLSDPLY-12319', self._domain_type, self._domain_typedef_filename,
                                  self._version_typedef_name, 'unixScript',
                                  class_name=self.__class_name, method_name=_method_name)

        self._logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def should_archive_excluded_app(self, source_path):
        """
        Whether the source_path is listed in the discoverExcludedBinariesList list
        :param source_path: the source_path from the app, which typically will be tokenized
        :return: True, if the source path is included in the discoverExcludedBinariesList; False otherwise
        """
        return source_path in self._excluded_locations_binaries_to_archive

    def is_filtered(self, location, name=None):
        """
        Determine if the named object at the specified location is filtered.

        :param location: the alias location object
        :param name: the name of the object
        :return: true, if the object should be filtered; false otherwise
        """
        key = location.get_folder_path()
        if key in self._discover_filters:
            # Global filter to remove the entire section
            if name is None:
                return True

            discover_filters = self._discover_filters[key]
            for discover_filter in discover_filters:
                matched = re.match(discover_filter, name)
                if matched is not None:
                    return True
        return False

    def _translate_system_elements(self, system_elements_dict):
        """
        Convert the old system-elements format to the new discover-filters format.

        :param system_elements_dict: the system-elements dictionary
        :return:
        """
        discover_filters_dict = dict()
        for key, value in system_elements_dict.iteritems():
            new_key = self._convert_system_elements_key_name(key)
            discover_filters_dict[new_key] = value
        return discover_filters_dict

    def _convert_system_elements_key_name(self, key):
        """
        Convert the old system-elements key names to the new discover-filters key names.
        :param key: the system-elements key
        :return: the equivalent discover-filters key
        """
        if key in self.__key_mapping_table:
            return self.__key_mapping_table[key]
        else:
            if self._program_name == DISCOVER_DOMAIN:
                ex = exception_helper.create_discover_exception('WLSDPLY-12316', key, self._domain_typedef_filename)
            else:
                ex = exception_helper.create_create_exception('WLSDPLY-12316', key, self._domain_typedef_filename)
            raise ex

    def __resolve_paths(self):
        """
        Resolve any tokens in the template paths.
        :raises: CreateException: if an error occurs resolving the paths
        """
        _method_name = '__resolve_paths'

        if not self._paths_resolved:
            if self._model_context is None:
                ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-12302')
                self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex

            if 'baseTemplate' in self._domain_typedef:
                self._domain_typedef['baseTemplate'] = \
                    self._model_context.replace_token_string(self._domain_typedef['baseTemplate'])
            else:
                ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-12303',
                                                           self._domain_type, self._domain_typedef_filename,
                                                           self._version_typedef_name)
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
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-12304',
                                                       self._domain_type, self._domain_typedef_filename)
            self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        elif 'definitions' not in self._domain_typedefs_dict:
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-12305',
                                                       self._domain_type, self._domain_typedef_filename)
            self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        self._version_typedef_name = self.__match_version_typedef(self._domain_typedefs_dict['versions'])

        if self._version_typedef_name in self._domain_typedefs_dict['definitions']:
            result = self._domain_typedefs_dict['definitions'][self._version_typedef_name]
        else:
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-12306',
                                                       self._domain_type, self._domain_typedef_filename,
                                                       self._version_typedef_name)
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
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-12307',
                                                       self._domain_type, self._domain_typedef_filename)
            self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        if self._model_context is not None:
            wls_version = self._model_context.get_effective_wls_version()
        else:
            wls_version = self.wls_helper.get_weblogic_version()
        self._logger.fine('WLSDPLY-12310', wls_version,
                          class_name=self.__class_name, method_name=_method_name)

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
                ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-12309',
                                                           self._domain_type, self._domain_typedef_filename,
                                                           wls_version)
                self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex
        if result == NOT_SUPPORTED:
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-12313',
                                                       self._domain_type, wls_version)
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
        topology_profile = self._domain_typedefs_dict['topologyProfile']

        # there are no valid topology profiles for versions 12.1.x and below
        if not self.wls_helper.is_topology_profile_supported():
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                                       'WLSDPLY-12314', topology_profile, self._domain_typedef_filename,
                                                       self.wls_helper.get_weblogic_version())
            self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        # if specified, topology profile must be one of the known types
        if topology_profile not in TopologyProfile:
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                                       'WLSDPLY-12315', topology_profile, self._domain_typedef_filename)
            self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        return topology_profile
