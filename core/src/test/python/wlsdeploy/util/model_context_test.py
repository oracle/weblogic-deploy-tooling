"""
Copyright (c) 2020, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
"""
import unittest

from wlsdeploy.aliases.model_constants import ALL
from wlsdeploy.aliases.model_constants import DEFAULT_AUTHENTICATOR
from wlsdeploy.aliases.model_constants import DEFAULT_CREDENTIAL_MAPPER
from wlsdeploy.aliases.model_constants import XACML_AUTHORIZER
from wlsdeploy.aliases.model_constants import XACML_ROLE_MAPPER
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.model_context import ModelContext


class ModelContextTest(unittest.TestCase):
    __program_name = 'ModelContextTest'

    def test_copy_model_context(self):
        __oracle_home = '/my/oracle/home'
        __model_file = 'my_model_file.yaml'

        arg_map = dict()
        arg_map[CommandLineArgUtil.ORACLE_HOME_SWITCH] = __oracle_home
        model_context = ModelContext(self.__program_name, arg_map)
        self.assertEquals(model_context.get_program_name(), self.__program_name)
        self.assertEquals(model_context.get_oracle_home(), __oracle_home)
        self.assertEquals(model_context.get_model_file(), None)

        arg_map = dict()
        arg_map[CommandLineArgUtil.MODEL_FILE_SWITCH] = __model_file
        model_context_copy = model_context.copy(arg_map)
        self.assertEquals(model_context_copy.get_program_name(), self.__program_name)
        self.assertEquals(model_context_copy.get_oracle_home(), __oracle_home)
        self.assertEquals(model_context_copy.get_model_file(), __model_file)

    def test_password_is_tokenized(self):
        __no_token_value = 'Welcome1'
        __complex_no_token_value = 'Abc@@def@@ghi'
        __secret_value = '@@SECRET:foo:username@@'
        __env_value = '@@ENV:FOO@@'
        __complex_token_value = '@@SECRET:foo:@@ENV:BAR@@@@'

        model_context = ModelContext(self.__program_name)
        self.assertEquals(model_context.password_is_tokenized(None), False)
        self.assertEquals(model_context.password_is_tokenized(__no_token_value), False)
        self.assertEquals(model_context.password_is_tokenized(__complex_no_token_value), False)

        self.assertEquals(model_context.password_is_tokenized(__secret_value), True)
        self.assertEquals(model_context.password_is_tokenized(__env_value), True)
        self.assertEquals(model_context.password_is_tokenized(__secret_value), True)
        self.assertEquals(model_context.password_is_tokenized(__complex_token_value), True)

    def test_discover_security_provider_data_scopes(self):
        # Some security provider types contain passwords, requiring extra configuration for discover
        self._try_security_provider_data_scope(True, DEFAULT_AUTHENTICATOR)
        self._try_security_provider_data_scope(True, DEFAULT_CREDENTIAL_MAPPER)
        self._try_security_provider_data_scope(True, ALL)
        self._try_security_provider_data_scope(False, XACML_AUTHORIZER, XACML_ROLE_MAPPER)
        self._try_security_provider_data_scope(True, XACML_AUTHORIZER, DEFAULT_CREDENTIAL_MAPPER)
        self._try_security_provider_data_scope(True, XACML_ROLE_MAPPER, DEFAULT_CREDENTIAL_MAPPER)

    def _try_security_provider_data_scope(self, expected_result, *args):
        scopes_text = ','.join(list(args))
        arg_map = {
            CommandLineArgUtil.DISCOVER_SECURITY_PROVIDER_DATA_SWITCH: scopes_text
        }
        model_context = ModelContext(self.__program_name, arg_map)

        test_text = "should not"
        if expected_result:
            test_text = "should"
        self.assertEquals(model_context.is_discover_security_provider_passwords(), expected_result,
                          "Security provider data scope " + scopes_text + " " + test_text + " discover passwords")
