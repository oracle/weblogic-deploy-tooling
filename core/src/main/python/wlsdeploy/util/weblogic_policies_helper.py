"""
Copyright (c) 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
import shutil

from java.io import File
from java.lang import String

from wlsdeploy.aliases.model_constants import POLICY
from wlsdeploy.aliases.model_constants import RESOURCE_ID
from wlsdeploy.exception import exception_helper
import wlsdeploy.util.unicode_helper as str_helper

import com.bea.common.security.utils.encoders.BASE64Encoder as BASE64Encoder
import com.bea.common.security.xacml.DocumentParseException as DocumentParseException
import com.bea.common.security.xacml.URISyntaxException as URISyntaxException
import com.bea.security.providers.xacml.entitlement.EntitlementConverter as EntitlementConverter
import com.bea.security.xacml.cache.resource.ResourcePolicyIdUtil as ResourcePolicyIdUtil

_DOMAIN_SECURITY_SUBDIR = 'security'
_WLS_XACML_AUTHORIZER_LDIFT_FILENAME = 'XACMLAuthorizerInit.ldift'
_WL_HOME_AUTHORIZER_LDIFT_FILE = os.path.join('server', 'lib', _WLS_XACML_AUTHORIZER_LDIFT_FILENAME)
_WLS_POLICY_DN_TEMPLATE = 'dn: cn=%s+xacmlVersion=1.0,ou=Policies,ou=XACMLAuthorization,ou=@realm@,dc=@domain@\n'

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
            self._target_xacml_authorizer_ldift_temp_file = '%s.new' % self._target_xacml_authorizer_ldift_file
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
        policy_entries_map = self._create_xacml_authorizer_entries(model_policies_dict)
        self._update_xacml_authorizer_ldift(policy_entries_map)
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

        try:
            shutil.copyfile(self._source_xacml_authorizer_ldift_file, self._target_xacml_authorizer_ldift_temp_file)
        except IOError, ioe:
            error = exception_helper.convert_error_to_exception()
            ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-02003',
                                                   self._target_xacml_authorizer_ldift_dir, error.getLocalizedMssage(),
                                                   error=error)
            self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        self._logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def _create_xacml_authorizer_entries(self, model_policies_map):
        _method_name = '_create_xacml_authorizer_entries'
        self._logger.entering(class_name=self.__class_name, method_name=_method_name)

        entries = dict()
        if model_policies_map is not None:
            for model_policy_name, model_policy_dict in model_policies_map.iteritems():
                model_policy_resource_id = model_policy_dict[RESOURCE_ID]
                model_policy_policy = model_policy_dict[POLICY]
                try:
                    policy = self._converter.convertResourceExpression(model_policy_resource_id, model_policy_policy)
                    scope = self._escaper.escapeString(String(model_policy_resource_id))
                    cn = self._escaper.escapeString(policy.getId().toString())
                    xacml = self._b64encoder.encodeBuffer(String(policy.toString()).getBytes('UTF-8'))
                    entry = [
                        _WLS_POLICY_DN_TEMPLATE % cn,
                        'objectclass: top\n',
                        'objectclass: xacmlEntry\n',
                        'objectclass: xacmlAuthorizationPolicy\n',
                        'objectclass: xacmlResourceScoping\n',
                        'cn: %s\n' % cn,
                        'xacmlResourceScope: %s\n' % scope,
                        'xacmlVersion: 1.0\n',
                        'xacmlStatus: 3\n',
                        'xacmlDocument:: %s\n' % xacml
                    ]
                    entries[model_policy_name] = entry
                except DocumentParseException, dpe:
                    ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-02004', model_policy_name,
                                                           RESOURCE_ID, model_policy_resource_id, POLICY,
                                                           model_policy_policy, dpe.getLocalizedMessage(), error=dpe)
                    self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                    raise ex
                except URISyntaxException, use:
                    ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-02005', model_policy_name,
                                                           RESOURCE_ID, model_policy_resource_id, POLICY,
                                                           model_policy_policy, use.getLocalizedMessage(), error=use)
                    self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                    raise ex

        self._logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return entries

    def _update_xacml_authorizer_ldift(self, policy_entries_map):
        _method_name = '_update_xacml_authorizer_ldift'
        self._logger.entering(class_name=self.__class_name, method_name=_method_name)

        self._logger.finer('WLSDPLY-02006', self._target_xacml_authorizer_ldift_temp_file,
                           class_name=self.__class_name, method_name=_method_name)
        ldift_temp_file = None
        try:
            try:
                ldift_temp_file = open(self._target_xacml_authorizer_ldift_temp_file, 'a')
                for model_policy_name, ldift_lines in policy_entries_map.iteritems():
                    self._logger.finer('WLSDPLY-02007', model_policy_name,
                                       class_name=self.__class_name, method_name=_method_name)
                    ldift_temp_file.write('\n')
                    ldift_temp_file.writelines(ldift_lines)
            except (ValueError,IOError,OSError), error:
                ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-02008',
                                                       str_helper.to_string(error), error=error)
                self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex
        finally:
            if ldift_temp_file is not None:
                ldift_temp_file.close()

        # Rename the temp file
        try:
            os.rename(self._target_xacml_authorizer_ldift_temp_file, self._target_xacml_authorizer_ldift_file)
        except OSError, ose:
            ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-02009',
                                                   self._target_xacml_authorizer_ldift_temp_file,
                                                   self._target_xacml_authorizer_ldift_file,
                                                   str_helper.to_string(ose), error=ose)
            self._logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        self._logger.exiting(class_name=self.__class_name, method_name=_method_name)
