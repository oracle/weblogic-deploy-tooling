"""
Copyright (c) 2020, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import unittest

import os, tempfile, traceback, sys, shutil

from wlsdeploy.util.model_context import ModelContext
from compare_model import ModelFileDiffer
from wlsdeploy.util.model_translator import FileToPython
from wlsdeploy.logging.platform_logger import PlatformLogger
from oracle.weblogic.deploy.compare import CompareException
from oracle.weblogic.deploy.util import PyWLSTException

class CompareModelTestCase(unittest.TestCase):
    _resources_dir = '../../test-classes'
    _use_ordering = True

    def setUp(self):
        self.name = 'CompareModelTestCase'
        self._logger = PlatformLogger('wlsdeploy.comparemodel')
        self._program_name = 'CompareModelTestCase'

    def testCompareModelFull(self):
        _method_name = 'testCompareModelFull'

        _variables_file = self._resources_dir + '/compare_model_model1.10.properties'
        _new_model_file = self._resources_dir + '/compare_model_model2.yaml'
        _old_model_file = self._resources_dir + '/compare_model_model1.yaml'
        _temp_dir = os.path.join(tempfile.gettempdir(), _method_name)

        if os.path.exists(_temp_dir):
            shutil.rmtree(_temp_dir)

        os.mkdir(_temp_dir)

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
            obj = ModelFileDiffer(_new_model_file, _old_model_file, model_context, _temp_dir)
            return_code = obj.compare()
            self.assertEqual(return_code, 0)

            yaml_result = _temp_dir + os.sep + 'diffed_model.yaml'
            json_result = _temp_dir + os.sep + 'diffed_model.json'
            stdout_result = obj.get_compare_msgs()
            model_dictionary = FileToPython(yaml_result).parse()
            yaml_exists = os.path.exists(yaml_result)
            json_exists = os.path.exists(json_result)

            self.assertEqual(yaml_exists, True)
            self.assertEqual(json_exists, True)
            self.assertEqual(len(stdout_result), 1)

            self.assertEqual(model_dictionary.has_key('resources'), True)
            self.assertEqual(model_dictionary.has_key('topology'), True)
            self.assertEqual(model_dictionary.has_key('appDeployments'), True)
            self.assertEqual(model_dictionary['topology'].has_key('ServerTemplate'), True)
            self.assertEqual(model_dictionary['topology'].has_key('Cluster'), True)
            self.assertEqual(model_dictionary['topology']['ServerTemplate'].has_key('cluster-1-template'), True)
            self.assertEqual(model_dictionary['topology']['Cluster'].has_key('cluster-2'), True)
            self.assertEqual(model_dictionary['appDeployments'].has_key('Library'), True)
            self.assertEqual(model_dictionary['appDeployments'].has_key('Application'), True)
            self.assertEqual(model_dictionary['appDeployments']['Application'].has_key('myear'), True)
            self.assertEqual(model_dictionary['resources'].has_key('JMSSystemResource'), True)
            self.assertEqual(model_dictionary['resources'].has_key('!WebAppContainer'), True)
            self.assertEqual(model_dictionary['resources']['JMSSystemResource'].has_key('MyJmsModule'), True)
            self.assertEqual(model_dictionary['resources'].has_key('!WebAppContainer'), True)
            self.assertEqual(model_dictionary['resources'].has_key('SingletonService'), True)
            self.assertEqual(model_dictionary['topology']['ServerTemplate']['cluster-1-template']
                             .has_key('!ServerStart'), True)
            self.assertEqual(model_dictionary['appDeployments']['Library'].has_key('!jax-rs#2.0@2.22.4.0'), True)
            self.assertEqual(model_dictionary['appDeployments']['Library'].has_key('!jsf#1.2@1.2.9.0'), True)
            self.assertEqual(model_dictionary['appDeployments']['Application']['myear'].has_key('ModuleType'), False)

        except (CompareException, PyWLSTException), te:
            return_code = 2
            self._logger.severe('WLSDPLY-05709',
                                te.getLocalizedMessage(), error=te,
                                class_name=self._program_name, method_name=_method_name)

        if os.path.exists(_temp_dir):
            shutil.rmtree(_temp_dir)

        self.assertEqual(return_code, 0)

    def testCompareModelInvalidModel(self):
        _method_name = 'testCompareModelInvalidModel'

        _variables_file = self._resources_dir + '/compare_model_model1.10.properties'
        _new_model_file = self._resources_dir + '/compare_model_model3.yaml'
        _old_model_file = self._resources_dir + '/compare_model_model1.yaml'
        _temp_dir = os.path.join(tempfile.gettempdir(), _method_name)

        if os.path.exists(_temp_dir):
            shutil.rmtree(_temp_dir)
        os.mkdir(_temp_dir)

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
            obj = ModelFileDiffer(_new_model_file, _old_model_file, model_context, _temp_dir)
            return_code = obj.compare()
        except (CompareException, PyWLSTException), te:
            return_code = 2
            self._logger.severe('WLSDPLY-05709',
                                te.getLocalizedMessage(), error=te,
                                class_name=self._program_name, method_name=_method_name)

        if os.path.exists(_temp_dir):
            shutil.rmtree(_temp_dir)

        self.assertNotEqual(return_code, 0)

    def testCompareModelInvalidFile(self):
        _method_name = 'testCompareModelInvalidFile'

        _variables_file = self._resources_dir + '/compare_model_model1.10.properties'
        _new_model_file = self._resources_dir + '/compare_model_model4.yaml'
        _old_model_file = self._resources_dir + '/compare_model_model1.yaml'
        _temp_dir = os.path.join(tempfile.gettempdir(), _method_name)

        if os.path.exists(_temp_dir):
            shutil.rmtree(_temp_dir)
        os.mkdir(_temp_dir)

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
            obj = ModelFileDiffer(_new_model_file, _old_model_file, model_context, _temp_dir)
            return_code = obj.compare()
        except (CompareException, PyWLSTException), te:
            return_code = 2
            self._logger.severe('WLSDPLY-05709',
                                te.getLocalizedMessage(), error=te,
                                class_name=self._program_name, method_name=_method_name)

        if os.path.exists(_temp_dir):
            shutil.rmtree(_temp_dir)

        self.assertNotEqual(return_code, 0)


if __name__ == '__main__':
    unittest.main()
