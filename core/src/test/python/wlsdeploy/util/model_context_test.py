"""
Copyright (c) 2020, 2023, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
"""
import unittest

from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.model_context import ModelContext


class ClaHelperTest(unittest.TestCase):

    def test_copy_model_context(self):
        __program_name = 'model_context_test'
        __oracle_home = '/my/oracle/home'
        __model_file = 'my_model_file.yaml'

        arg_map = dict()
        arg_map[CommandLineArgUtil.ORACLE_HOME_SWITCH] = __oracle_home
        model_context = ModelContext(__program_name, arg_map)
        self.assertEquals(model_context.get_program_name(), __program_name)
        self.assertEquals(model_context.get_oracle_home(), __oracle_home)
        self.assertEquals(model_context.get_model_file(), None)

        arg_map = dict()
        arg_map[CommandLineArgUtil.MODEL_FILE_SWITCH] = __model_file
        model_context_copy = model_context.copy(arg_map)
        self.assertEquals(model_context_copy.get_program_name(), __program_name)
        self.assertEquals(model_context_copy.get_oracle_home(), __oracle_home)
        self.assertEquals(model_context_copy.get_model_file(), __model_file)

    def test_password_is_tokenized(self):
        __program_name = 'model_context_test'

        __no_token_value = 'Welcome1'
        __complex_no_token_value = 'Abc@@def@@ghi'
        __secret_value = '@@SECRET:foo:username@@'
        __env_value = '@@ENV:FOO@@'
        __complex_token_value = '@@SECRET:foo:@@ENV:BAR@@@@'

        model_context = ModelContext(__program_name)
        self.assertEquals(model_context.password_is_tokenized(None), False)
        self.assertEquals(model_context.password_is_tokenized(__no_token_value), False)
        self.assertEquals(model_context.password_is_tokenized(__complex_no_token_value), False)

        self.assertEquals(model_context.password_is_tokenized(__secret_value), True)
        self.assertEquals(model_context.password_is_tokenized(__env_value), True)
        self.assertEquals(model_context.password_is_tokenized(__secret_value), True)
        self.assertEquals(model_context.password_is_tokenized(__complex_token_value), True)
