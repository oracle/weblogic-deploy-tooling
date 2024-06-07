"""
Copyright (c) 2019, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import re
from java.io import File

from oracle.weblogic.deploy.json import JsonException
from oracle.weblogic.deploy.json import JsonStreamTranslator
from oracle.weblogic.deploy.util import FileUtils
from oracle.weblogic.deploy.util import WLSDeployArchive

from wlsdeploy.aliases.model_constants import APPEND
from wlsdeploy.aliases.model_constants import EXPRESSION
from wlsdeploy.aliases.model_constants import PREPEND
from wlsdeploy.aliases.model_constants import REPLACE
from wlsdeploy.aliases.model_constants import UPDATE_MODE
from wlsdeploy.aliases.model_constants import WLS_ROLES
from wlsdeploy.aliases.model_constants import XACML_DOCUMENT
from wlsdeploy.aliases.model_constants import XACML_STATUS
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.exception_types import ExceptionType
from wlsdeploy.tool.util.archive_helper import ArchiveList
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import string_utils
from wlsdeploy.util import unicode_helper as str_helper
from wlsdeploy.util.weblogic_roles_helper import WebLogicRolesHelper

WLS_GLOBAL_ROLES = None
WLS_ROLE_UPDATE_OPERAND = '|'
XACML_STATUS_REGEX = re.compile(r'^[0-3]$')

class WLSRoles(object):
    """
    Handle the WLSRoles section from the model domainInfo
    """
    __class_name = 'WLSRoles'
    __DEFAULT_ROLES_PATH = 'oracle/weblogic/deploy/security/XACMLRoleMapperDefaults/'

    def __init__(self, domain_info, domain_home, model_context, exception_type, logger, validation_roles_map = None, archive_helper = None):
        global WLS_GLOBAL_ROLES

        self.logger = logger
        self._model_context = model_context
        self._wls_helper = model_context.get_weblogic_helper()
        self._exception_type = exception_type

        self._archive_helper = archive_helper
        if archive_helper is None:
            archive_file_name = model_context.get_archive_file_name()
            if archive_file_name is not None:
                self._archive_helper = ArchiveList(archive_file_name, model_context, self._exception_type)
        self._wls_roles_map = None
        self._domain_security_folder = None
        self._validation_roles_map = validation_roles_map

        if WLS_GLOBAL_ROLES is None:
            default_roles = self._load_default_roles()
            if default_roles:
                WLS_GLOBAL_ROLES = default_roles

        if domain_info is not None:
            if not dictionary_utils.is_empty_dictionary_element(domain_info, WLS_ROLES):
                self._wls_roles_map = domain_info[WLS_ROLES]
                self._domain_security_folder = File(domain_home, 'security').getPath()
                self._weblogic_roles_helper = WebLogicRolesHelper(logger, exception_type, self._domain_security_folder)

    def process_roles(self):
        """
        Process the WebLogic roles contained in the domainInfo section of the model when specified.
        """
        _method_name = 'process_roles'
        self.logger.entering(self._domain_security_folder, self._wls_roles_map,
                             class_name=self.__class_name, method_name=_method_name)

        if self._wls_roles_map is not None:
            role_expressions = self._process_roles_map(self._wls_roles_map)
            if role_expressions:
                self.logger.info('WLSDPLY-12500', role_expressions.keys(), class_name=self.__class_name, method_name=_method_name)
                self._weblogic_roles_helper.update_xacml_role_mapper(role_expressions)

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def validate_roles(self):
        """
        Validate the model-defined WLSRoles
        """
        global WLS_GLOBAL_ROLES

        _method_name = 'validate_roles'
        self.logger.entering(class_name=self.__class_name, method_name=_method_name)

        if self._validation_roles_map:
            for role_name, role_dict in self._validation_roles_map.iteritems():
                role_expression = dictionary_utils.get_element(role_dict, EXPRESSION)
                role_update_mode = dictionary_utils.get_element(role_dict, UPDATE_MODE)
                xacml_status = dictionary_utils.get_element(role_dict, XACML_STATUS, '3')
                if not isinstance(xacml_status, (str, unicode)):
                    xacml_status = str_helper.to_string(xacml_status)
                xacml_document = dictionary_utils.get_element(role_dict, XACML_DOCUMENT)

                if not string_utils.is_empty(xacml_status) and XACML_STATUS_REGEX.match(xacml_status) is None:
                    self.logger.severe('WLSDPLY-12501', role_name, XACML_STATUS, xacml_status,
                                       class_name=self.__class_name, method_name=_method_name)

                if not string_utils.is_empty(role_expression):
                    if not self._validate_update_mode_value(role_name, role_update_mode):
                        continue

                    if self._is_update_mode(role_update_mode) and role_name not in WLS_GLOBAL_ROLES:
                        self.logger.severe('WLSDPLY-12502', role_name, UPDATE_MODE, role_update_mode,
                                           class_name=self.__class_name, method_name=_method_name)
                elif not string_utils.is_empty(xacml_document):
                    if WLSDeployArchive.isPathIntoArchive(xacml_document) and \
                            (self._archive_helper is None or not self._archive_helper.contains_file(xacml_document)):
                        validate_configuration = self._model_context.get_validate_configuration()
                        if validate_configuration.allow_unresolved_archive_references():
                            log_method = self.logger.info
                        else:
                            log_method = self.logger.severe

                        log_method('WLSDPLY-12503', role_name, xacml_document,
                                   class_name=self.__class_name, method_name=_method_name)
                else:
                    self.logger.severe('WLSDPLY-12504', role_name, EXPRESSION, XACML_DOCUMENT,
                                       class_name=self.__class_name, method_name=_method_name)

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def _validate_update_mode_value(self, role_name, update_mode):
        _method_name = '_validate_update_mode_value'
        self.logger.entering(update_mode, class_name=self.__class_name, method_name=_method_name)

        is_valid = True
        if not string_utils.is_empty(update_mode):
            mode = update_mode.lower()
            if mode != REPLACE and mode != PREPEND and mode != APPEND:
                self.logger.severe('WLSDPLY-12505', role_name, UPDATE_MODE, update_mode, REPLACE, PREPEND, APPEND,
                                   class_name=self.__class_name, method_name=_method_name)
                is_valid = False

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name, result=is_valid)
        return is_valid

    def _process_roles_map(self, roles_map):
        """
        Loop through the WebLogic roles listed in the domainInfo and create a map of the role to the expression

        :param roles_map: the model-defined roles map
        :return: a roles dictionary ready for provisioning
        """
        global WLS_GLOBAL_ROLES

        _method_name = '_process_roles_map'
        self.logger.entering(class_name=self.__class_name, method_name=_method_name)

        result = {}
        for role_name, role_dict in roles_map.iteritems():
            role_expression = dictionary_utils.get_element(role_dict, EXPRESSION)
            role_update_mode = dictionary_utils.get_element(role_dict, UPDATE_MODE)
            xacml_status = dictionary_utils.get_element(role_dict, XACML_STATUS, '3')
            if not isinstance(xacml_status, (str, unicode)):
                xacml_status = str_helper.to_string(xacml_status)
            xacml_document = dictionary_utils.get_element(role_dict, XACML_DOCUMENT)

            role_map = {
                XACML_STATUS: xacml_status
            }
            if not string_utils.is_empty(role_expression):
                update_role = self._is_update_mode(role_update_mode)
                # Add the role and expression to the map of roles to be processed
                if update_role:
                    role_expression = self._update_role_expression(role_name, role_update_mode, role_expression)
                role_map[EXPRESSION] = role_expression
                result[role_name] = role_map
            elif not string_utils.is_empty(xacml_document):
                xacml_text = self._get_role_xacml_document_from_archive(role_name, xacml_document)
                if not string_utils.is_empty(xacml_text):
                    role_map[XACML_DOCUMENT] = xacml_text
                    result[role_name] = role_map
                else:
                    ex = exception_helper.create_create_exception('WLSDPLY-12506',
                                                                  role_name, XACML_DOCUMENT, xacml_document)
                    self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                    raise ex
            else:
                ex = exception_helper.create_create_exception('WLSDPLY-12507',
                                                              role_name, EXPRESSION, XACML_DOCUMENT)
                self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def _get_role_xacml_document_from_archive(self, role_name, xacml_path):
        _method_name = '_get_role_xacml_document_from_archive'

        if self._archive_helper is not None and self._archive_helper.is_path_into_archive(xacml_path):
            result = self._archive_helper.read_xacml_role_content(xacml_path)
        else:
            xacml_lines = self._get_lines_from_xacml_file(xacml_path)
            result = "".join(xacml_lines)

        return result

    def _get_lines_from_xacml_file(self, path):
        _method_name = '_get_lines_from_xacml_file'
        self.logger.entering(path, class_name=self.__class_name, method_name=_method_name)

        try:
            f = open(path, 'r')
            try:
                contents = f.read()
            finally:
                f.close()

            lines = contents.split('\n')
        except (IOError, Exception), ex:
            ex = exception_helper.create_create_exception('WLSDPLY-12508', path, str_helper.to_string(ex))
            self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return lines

    def _is_update_mode(self, mode):
        _method_name = '_is_update_mode'
        self.logger.entering(mode, class_name=self.__class_name, method_name=_method_name)

        result = False
        if not string_utils.is_empty(mode):
            mode = mode.lower()
            if APPEND == mode or PREPEND == mode:
                result = True

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def _update_role_expression(self, role_name, role_update_mode, expression_value):
        """
        Lookup the default role definition and logically OR the expression
        Based on the update mode the expression is appended or prepended
        :return: the updated role expression
        """
        global WLS_GLOBAL_ROLES

        result = expression_value
        if not string_utils.is_empty(role_update_mode):
            mode = role_update_mode.lower()
            if APPEND == mode:
                result = WLS_GLOBAL_ROLES[role_name] + WLS_ROLE_UPDATE_OPERAND + expression_value
            elif PREPEND == mode:
                result = expression_value + WLS_ROLE_UPDATE_OPERAND + WLS_GLOBAL_ROLES[role_name]
        return result

    def _load_default_roles(self):
        _method_name = '_load_default_roles'

        if self._wls_helper is not None:
            if self._wls_helper.is_weblogic_version_or_above('12.2.1'):
                file_name = '1412.json'
            else:
                file_name = '1213.json'
        else:
            # unit tests...
            file_name = '1412.json'

        defaults_file_path = '%s%s' % (self.__DEFAULT_ROLES_PATH, file_name)
        defaults_input_stream = FileUtils.getResourceAsStream(defaults_file_path)
        if defaults_input_stream is None:
            ex = exception_helper.create_create_exception('WLSDPLY-07106', 'XACMLRoleMapper', defaults_file_path)
            self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        try:
            json_translator = JsonStreamTranslator('%s/%s' % ('XACMLRoleMapper', file_name), defaults_input_stream)
            result = json_translator.parse()
        except JsonException, jex:
            ex = exception_helper.create_create_exception('WLSDPLY-07124', 'XACMLRoleMapper',
                                                   defaults_file_path, jex.getLocalizedMessage(), error=jex)
            self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result


def get_wls_roles_validator(model_context, roles_map, logger, archive_helper=None):
    """
    Obtain a WLSRoles helper only for the validation of the WLSRoles section
    """
    return WLSRoles(None, None, model_context, ExceptionType.VALIDATE, logger,
                    validation_roles_map = roles_map, archive_helper=archive_helper)
