"""
Copyright (c) 2020, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import unittest

import os, tempfile, traceback, sys

from wlsdeploy.util.model_context import ModelContext
from model_diff import ModelFileDiffer
from wlsdeploy.util.model_translator import FileToPython
from wlsdeploy.logging.platform_logger import PlatformLogger
import oracle.weblogic.deploy.util.TranslateException as TranslateException

class CompareModelTestCase(unittest.TestCase):
    _resources_dir = '../../test-classes'
    _use_ordering = True
    _program_name ='compareModelTest'
    def setUp(self):
        self.name = 'CompareModelTestCase'
        self._logger = PlatformLogger('wlsdeploy.comparemodel')

        # create a context with resource directory as Oracle home, to support @@ORACLE_HOME@@ resolution
        #self.model_context = ModelContext("test", {'-oracle_home': self._resources_dir})

    def testCompareModelFull(self):
        _method_name = 'testModelValidation'

        _variables_file = self._resources_dir + '/compare_model_model1.10.properties'
        _new_model_file = self._resources_dir + '/compare_model_model2.yaml'
        _old_model_file = self._resources_dir + '/compare_model_model1.yaml'
        _temp_dir = tempfile.gettempdir()

        mw_home = os.environ['MW_HOME']
        args_map = {
            '-oracle_home': mw_home,
            '-variable_file': _variables_file,
            '-output_dir' : _temp_dir,
            '-domain_type' : 'WLS',
            '-trailing_arguments': [ _new_model_file, _old_model_file ]
        }

        try:
            model_context = ModelContext('CompareModelTestCase', args_map)
            obj = ModelFileDiffer(_new_model_file, _old_model_file, model_context, tempfile.gettempdir())
            return_code = obj.compare()
            self.assertEqual(return_code, 0)

            yaml_result = _temp_dir + os.sep + 'diffed_model.yaml'
            json_result = _temp_dir + os.sep + 'diffed_model.json'
            stdout_result = _temp_dir + os.sep + "model_diff_stdout"
            model_dictionary = FileToPython(yaml_result).parse()
            yaml_exists = os.path.exists(yaml_result)
            json_exists = os.path.exists(json_result)
            stdout_exists = os.path.exists(stdout_result)

            self.assertEqual(yaml_exists, 1)
            self.assertEqual(json_exists, 1)
            self.assertEqual(stdout_exists, 1)

            self.assertEqual(model_dictionary.has_key('resources'), 1)
            self.assertEqual(model_dictionary.has_key('topology'), 1)
            self.assertEqual(model_dictionary.has_key('appDeployments'), 1)
            self.assertEqual(model_dictionary['topology'].has_key('ServerTemplate'), 1)
            self.assertEqual(model_dictionary['topology'].has_key('Cluster'), 1)
            self.assertEqual(model_dictionary['topology']['ServerTemplate'].has_key('cluster-1-template'), 1)
            self.assertEqual(model_dictionary['topology']['Cluster'].has_key('cluster-2'), 1)
            self.assertEqual(model_dictionary['appDeployments'].has_key('Library'), 1)
            self.assertEqual(model_dictionary['appDeployments'].has_key('Application'), 1)
            self.assertEqual(model_dictionary['appDeployments']['Application'].has_key('myear'), 1)
            self.assertEqual(model_dictionary['resources'].has_key('JMSSystemResource'), 1)
            self.assertEqual(model_dictionary['resources'].has_key('!WebAppContainer'), 1)
            self.assertEqual(model_dictionary['resources']['JMSSystemResource'].has_key('MyJmsModule'), 1)
            self.assertEqual(model_dictionary['resources'].has_key('!WebAppContainer'), 1)
            self.assertEqual(model_dictionary['resources'].has_key('SingletonService'), 1)
            self.assertEqual(model_dictionary['topology']['ServerTemplate']['cluster-1-template']
                             .has_key('!ServerStart'), 1)
            self.assertEqual(model_dictionary['appDeployments']['Library'].has_key('!jax-rs#2.0@2.22.4.0'), 1)
            self.assertEqual(model_dictionary['appDeployments']['Library'].has_key('!jsf#1.2@1.2.9.0'), 1)
            self.assertEqual(model_dictionary['appDeployments']['Application']['myear'].has_key('ModuleType'), 0)

        except TranslateException, te:
            return_code = -1
            self._logger.severe('WLSDPLY-20009',
                                self._program_name,
                                yaml_result,
                                te.getLocalizedMessage(), error=te,
                                class_name=self._class_name, method_name=_method_name)

        self.assertEqual(return_code, 0)

    def testCompareModelInvalidModel(self):
        _method_name = 'testModelValidation'

        _variables_file = self._resources_dir + '/compare_model_model1.10.properties'
        _new_model_file = self._resources_dir + '/compare_model_model3.yaml'
        _old_model_file = self._resources_dir + '/compare_model_model1.yaml'
        _temp_dir = tempfile.gettempdir()

        mw_home = os.environ['MW_HOME']
        args_map = {
            '-oracle_home': mw_home,
            '-variable_file': _variables_file,
            '-output_dir' : _temp_dir,
            '-domain_type' : 'WLS',
            '-trailing_arguments': [ _new_model_file, _old_model_file ]
        }

        model_context = ModelContext('CompareModelTestCase', args_map)
        obj = ModelFileDiffer(_new_model_file, _old_model_file, model_context, tempfile.gettempdir())
        return_code = obj.compare()
        self.assertNotEqual(return_code, 0)

    def testCompareModelInvalidFile(self):
        _method_name = 'testModelValidation'

        _variables_file = self._resources_dir + '/compare_model_model1.10.properties'
        _new_model_file = self._resources_dir + '/compare_model_model4.yaml'
        _old_model_file = self._resources_dir + '/compare_model_model1.yaml'
        _temp_dir = tempfile.gettempdir()

        mw_home = os.environ['MW_HOME']
        args_map = {
            '-oracle_home': mw_home,
            '-variable_file': _variables_file,
            '-output_dir' : _temp_dir,
            '-domain_type' : 'WLS',
            '-trailing_arguments': [ _new_model_file, _old_model_file ]
        }

        model_context = ModelContext('CompareModelTestCase', args_map)
        obj = ModelFileDiffer(_new_model_file, _old_model_file, model_context, tempfile.gettempdir())
        return_code = obj.compare()
        self.assertNotEqual(return_code, 0)


if __name__ == '__main__':
    unittest.main()
