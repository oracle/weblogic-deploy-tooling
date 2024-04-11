"""
Copyright (c) 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os

from com.bea.common.security.utils.encoders import BASE64Encoder
from com.bea.common.security.xacml import DocumentParseException
from com.bea.common.security.xacml import URISyntaxException
from com.bea.security.providers.xacml.entitlement import EntitlementConverter
from com.bea.security.xacml.cache.resource import ResourcePolicyIdUtil
from java.io import File
from java.lang import String

from wlsdeploy.aliases.model_constants import POLICY
from wlsdeploy.aliases.model_constants import RESOURCE_ID
from wlsdeploy.aliases.model_constants import WLS_POLICIES
from wlsdeploy.exception import exception_helper
from wlsdeploy.tool.util import ldif_entry
from wlsdeploy.tool.util.ldif_entry import LDIFEntry
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import unicode_helper as str_helper

_DOMAIN_SECURITY_SUBDIR = 'security'
_WLS_XACML_AUTHORIZER_LDIFT_FILENAME = 'XACMLAuthorizerInit.ldift'
_WL_HOME_AUTHORIZER_LDIFT_FILE = os.path.join('server', 'lib', _WLS_XACML_AUTHORIZER_LDIFT_FILENAME)
_WLS_POLICY_DN_TEMPLATE = 'dn: cn=%s+xacmlVersion=1.0,ou=Policies,ou=XACMLAuthorization,ou=@realm@,dc=@domain@'


class WebLogicPoliciesHelper(object):
    """
    Helper functions for handling WebLogic Policies
    """
    __class_name = 'WebLogicPoliciesHelper'

    def __init__(self, model_context, logger, exception_type):
        _method_name = '__init__'
        logger.entering(class_name=self.__class_name, method_name=_method_name)

        self._model_context = model_context
        self._logger = logger
        self._exception_type = exception_type
        wl_home = self._model_context.get_wl_home()
        if isinstance(wl_home, (str, unicode)):
            self._source_xacml_authorizer_ldift_file = os.path.join(wl_home, _WL_HOME_AUTHORIZER_LDIFT_FILE)
        else:
            ex = exception_helper.create_exception(exception_type, 'WLSDPLY-02000')
            self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        domain_home = self._model_context.get_domain_home()
        if isinstance(domain_home, (str, unicode)):
            self._target_xacml_authorizer_ldift_dir = os.path.join(domain_home, _DOMAIN_SECURITY_SUBDIR)
            self._target_xacml_authorizer_ldift_file = \
                os.path.join(self._target_xacml_authorizer_ldift_dir, _WLS_XACML_AUTHORIZER_LDIFT_FILENAME)
        else:
            ex = exception_helper.create_exception(exception_type, 'WLSDPLY-02001')
            self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        self._b64encoder = BASE64Encoder()
        self._escaper = ResourcePolicyIdUtil.getEscaper()
        self._converter = EntitlementConverter(None)
        self._logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def update_xacml_authorizer(self, model_policies_dict):
        _method_name = 'update_xacml_authorizer'
        self._logger.entering(class_name=self.__class_name, method_name=_method_name)

        if model_policies_dict is None or len(model_policies_dict) == 0:
            return

        self._ensure_source_file_and_target_dir()
        self._update_xacml_authorizer_ldift(model_policies_dict)
        self._logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def _ensure_source_file_and_target_dir(self):
        _method_name = '_ensure_source_file_and_target_dir'
        self._logger.entering(class_name=self.__class_name, method_name=_method_name)

        if not os.path.isfile(self._source_xacml_authorizer_ldift_file):
            ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-02002',
                                                   self._source_xacml_authorizer_ldift_file)
            self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        target_dir = File(self._target_xacml_authorizer_ldift_dir)
        if not target_dir.isDirectory() and not target_dir.mkdirs():
            ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-02003',
                                                   self._target_xacml_authorizer_ldift_dir)
            self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        self._logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def _update_xacml_authorizer_ldift(self, model_policies_dict):
        _method_name = '_update_xacml_authorizer_ldift'
        self._logger.entering(class_name=self.__class_name, method_name=_method_name)

        self._logger.finer('WLSDPLY-02006', self._target_xacml_authorizer_ldift_file,
                           class_name=self.__class_name, method_name=_method_name)

        target_ldift_file = None
        try:
            try:
                existing_policies = ldif_entry.read_entries(File(self._source_xacml_authorizer_ldift_file))

                # build a map of resource IDs to existing policies
                existing_policy_map = {}
                for policy in existing_policies:
                    cn = policy.get_single_value('cn')
                    if cn:
                        policy_id = self._escaper.unescapeString(cn)
                        resource_id = ResourcePolicyIdUtil.getResourceId(policy_id)
                        resource_key = _get_resource_key(resource_id)
                        existing_policy_map[resource_key] = policy

                # for each model policy, update an existing policy, or add a new one
                new_policies = []
                for model_policy_name, model_policy_dict in model_policies_dict.iteritems():
                    model_resource_id = model_policy_dict[RESOURCE_ID]
                    model_policy = model_policy_dict[POLICY]
                    resource_key = _get_resource_key(model_resource_id)
                    existing_policy = dictionary_utils.get_element(existing_policy_map, resource_key)  # type: LDIFEntry
                    if existing_policy:
                        self._update_policy_from_model(existing_policy, model_policy, model_policy_name)
                    else:
                        new_policy = self._create_policy_from_model(model_resource_id, model_policy, model_policy_name)
                        new_policies.append(new_policy)

                target_ldift_file = open(self._target_xacml_authorizer_ldift_file, 'w')
                first = True
                all_policies = existing_policies + new_policies
                for policy in all_policies:
                    if not first:
                        target_ldift_file.write('\n')
                    lines_text = '\n'.join(policy.get_assignment_lines()) + '\n'
                    target_ldift_file.writelines(lines_text)
                    first = False

            except (ValueError,IOError,OSError), error:
                ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-02008',
                                                       str_helper.to_string(error), error=error)
                self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex
        finally:
            if target_ldift_file is not None:
                target_ldift_file.close()

        self._logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def _update_policy_from_model(self, policy_entry, model_policy, model_policy_name):
        _method_name = '_update_policy_from_model'

        self._logger.info('WLSDPLY-02010', model_policy_name, class_name=self.__class_name, method_name=_method_name)

        self._logger.notification('WLSDPLY-02011', WLS_POLICIES, model_policy_name,
                                  class_name=self.__class_name, method_name=_method_name)

        scope = policy_entry.get_single_value('xacmlResourceScope')
        resource_id = self._escaper.unescapeString(scope)
        policy = self._convert_resource_expression(resource_id, model_policy, model_policy_name)
        xacml = self._b64encoder.encodeBuffer(String(policy.toString()).getBytes('UTF-8'))

        policy_entry.update_single_field('xacmlDocument:', xacml)  # double colon assignment

    def _create_policy_from_model(self, model_resource_id, model_policy, model_policy_name):
        _method_name = '_create_policy_from_model'

        self._logger.info('WLSDPLY-02007', model_policy_name, class_name=self.__class_name, method_name=_method_name)

        policy = self._convert_resource_expression(model_resource_id, model_policy, model_policy_name)
        scope = self._escaper.escapeString(String(model_resource_id))
        cn = self._escaper.escapeString(policy.getId().toString())
        xacml = self._b64encoder.encodeBuffer(String(policy.toString()).getBytes('UTF-8'))

        policy_entry = LDIFEntry()
        policy_entry.add_assignment_line(_WLS_POLICY_DN_TEMPLATE % cn)
        policy_entry.add_assignment('objectclass', 'top')
        policy_entry.add_assignment('objectclass', 'xacmlEntry')
        policy_entry.add_assignment('objectclass', 'xacmlAuthorizationPolicy')
        policy_entry.add_assignment('objectclass', 'xacmlResourceScoping')
        policy_entry.add_assignment('cn', cn)
        policy_entry.add_assignment('xacmlResourceScope', scope)
        policy_entry.add_assignment('xacmlVersion', '1.0')
        policy_entry.add_assignment('xacmlStatus', 3)
        policy_entry.add_assignment('xacmlDocument:', xacml)  # double colon assignment
        return policy_entry

    def _convert_resource_expression(self, model_resource_id, model_policy, model_policy_name):
        _method_name = '_convert_resource_expression'

        try:
            return self._converter.convertResourceExpression(model_resource_id, model_policy)

        except DocumentParseException, dpe:
            ex = exception_helper.create_exception(
                self._exception_type, 'WLSDPLY-02004', model_policy_name, RESOURCE_ID,
                model_resource_id, POLICY, model_policy, dpe.getLocalizedMessage(), error=dpe)
            self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        except URISyntaxException, use:
            ex = exception_helper.create_exception(
                self._exception_type, 'WLSDPLY-02005', model_policy_name, RESOURCE_ID,
                model_resource_id, POLICY, model_policy, use.getLocalizedMessage(), error=use)
            self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex


def _get_resource_key(resource_id):
    """
    Create a key from the specified resource ID that can be used for comparison,
    accounting for differences in spaces and ordering.
    *** This key is for comparison and lookup only, don't use it as resource ID ***
    :param resource_id: the resource ID for the key
    :return: the resulting key
    """
    parts = resource_id.split(', ')  # don't split path={weblogic,common,T3Services}
    just_parts = []
    for part in parts:
        just_parts.append(part.strip())  # clear any whitespace around the assignment
    just_parts.sort()  # put assignments in alpha order in the key only
    return ', '.join(just_parts)
