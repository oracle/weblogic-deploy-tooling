"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
import javaos as os

from java.lang import IllegalArgumentException

from oracle.weblogic.deploy.json import JsonException

from wlsdeploy.exception import exception_helper
from wlsdeploy.json.json_translator import JsonToPython
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.weblogic_helper import WebLogicHelper


class DomainTypedef(object):
    """
    The class that processes domain type definitions.
    """
    __class_name = 'DomainTypedef'

    __domain_typedefs_location = os.path.join(os.environ.get('WLSDEPLOY_HOME'), 'lib', 'typedefs')
    __domain_typedef_extension = '.json'

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

        self._domain_typedef_filename = \
            os.path.join(self.__domain_typedefs_location, domain_type + self.__domain_typedef_extension)
        # No need to explicitly validate the filename since the JsonToPython constructor does that...
        try:
            json_parser = JsonToPython(self._domain_typedef_filename)
            self._domain_typedefs_dict = json_parser.parse()
        except IllegalArgumentException, iae:
            ex = exception_helper.create_cla_exception('WLSDPLY-12300', self._program_name, self._domain_type,
                                                       self._domain_typedef_filename, iae.getLocalizedMessage(),
                                                       error=iae)
            ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        except JsonException, je:
            ex = exception_helper.create_cla_exception('WLSDPLY-12301', self._program_name, self._domain_type,
                                                       self._domain_typedef_filename, je.getLocalizedMessage(),
                                                       error=je)
            ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        self._domain_typedef = self.__get_version_typedef()
        self._paths_resolved = False
        self._model_context = None
        self._version_typedef_name = None
        return

    def set_model_context(self, model_context):
        """
        Set the model context object.
        :param model_context: the model context object to use
        :raises: CreateException: if an error occurs resolving the paths
        """
        if self._model_context is None:
            self._model_context = model_context
            self.__resolve_paths()
        return

    def get_base_template(self):
        """
        Get the base template to use when create the domain.
        :return: the base template to use
        :raises: CreateException: if an error occurs resolving the paths
        """
        self.__resolve_paths()
        return self._domain_typedef['baseTemplate']

    def get_extension_templates(self):
        """
        Get the list of extension templates to apply when create/extending the domain.
        :return: the list of extension templates, or an empty list if no extension templates are needed.
        :raises: CreateException: if an error occurs resolving the paths
        """
        self.__resolve_paths()
        return list(self._domain_typedef['extensionTemplates'])

    def get_server_groups_to_target(self):
        """
        Get the list of server groups to target to the managed servers in the domain.
        :return: the list of server groups to target, or an empty list if there are none
        :raises: CreateException: if an error occurs resolving the paths
        """
        self.__resolve_paths()
        return list(self._domain_typedef['serverGroupsToTarget'])

    def get_rcu_schemas(self):
        """
        Get the list of RCU schemas used by the domain type.
        :return: the list of RCU schemas to create
        """
        # No need to resolve the paths and we need this to work prior to
        # resolution for create.py argument processing.
        return list(self._domain_typedef['rcuSchemas'])

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

            if 'serverGroupsToTarget' not in self._domain_typedef:
                self._domain_typedef['serverGroupsToTarget'] = []

            if 'rcuSchemas' not in self._domain_typedef:
                self._domain_typedef['rcuSchemas'] = []

            self._paths_resolved = True
        return

    def __get_version_typedef(self):
        """
        Get the domain typedef that matches the current WLS version.
        :return: the version-specific domain typedef
        :raises: CreateException: if an error occurs resolving the paths
        """
        _method_name = '__get_version_typedef'

        if not 'versions' in self._domain_typedefs_dict:
            ex = exception_helper.create_create_exception('WLSDPLY-12304', self._domain_type,
                                                          self._domain_typedef_filename)
            self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        elif not 'definitions' in self._domain_typedefs_dict:
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

        wls_helper = WebLogicHelper(self._logger)
        wls_version = wls_helper.get_actual_weblogic_version()
        self._logger.fine('WLSDPLY-12310', wls_version, class_name=self.__class_name, method_name=_method_name)

        result = None
        if wls_version in versions_dict:
            result = versions_dict[wls_version]
        else:
            new_version = wls_helper.get_next_higher_order_version_number(wls_version)
            while new_version is not None:
                if new_version in versions_dict:
                    result = versions_dict[new_version]
                    self._logger.finer('WLSDPLY-12308', self._domain_type, self._domain_typedef_filename,
                                       new_version, wls_version, class_name=self.__class_name, method_name=_method_name)
                    break
                else:
                    new_version = wls_helper.get_next_higher_order_version_number(new_version)

            if result is None:
                ex = exception_helper.create_create_exception('WLSDPLY-12309', self._domain_type,
                                                              self._domain_typedef_filename, wls_version)
                self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex
        self._logger.exiting(self.__class_name, _method_name, result)
        return result
