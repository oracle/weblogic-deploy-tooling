"""
Copyright (c) 2020, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import unittest

import os
import shutil
import tempfile
from java.util.logging import Level
from oracle.weblogic.deploy.compare import CompareException
from oracle.weblogic.deploy.logging import SummaryHandler
from oracle.weblogic.deploy.util import PyWLSTException

from compare_model import ModelFileDiffer
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util.model_context import ModelContext
from wlsdeploy.util.model_translator import FileToPython


class CompareModelTestCase(unittest.TestCase):
    _resources_dir = '../../test-classes'
    _use_ordering = True

    def setUp(self):
        self.name = 'CompareModelTestCase'
        self._logger = PlatformLogger('wlsdeploy.compare_model')
        self._program_name = 'CompareModelTestCase'

        # add summary handler to validate logger to check results
        self._summary_handler = SummaryHandler()
        PlatformLogger('wlsdeploy.validate').logger.addHandler(self._summary_handler)

    def tearDown(self):
        # remove summary handler for next test suite
        PlatformLogger('wlsdeploy.validate').logger.removeHandler(self._summary_handler)

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
            # self._logger.severe('WLSDPLY-05709', te.getLocalizedMessage(), error=te,
            #                     class_name=self._program_name, method_name=_method_name)

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

            # expected parse error for model4, disable logging
            yaml_logger = PlatformLogger('wlsdeploy.yaml')
            yaml_level = yaml_logger.get_level()
            yaml_logger.set_level(Level.OFF)

            compare_logger = PlatformLogger('wlsdeploy.compare_model')
            compare_level = compare_logger.get_level()
            compare_logger.set_level(Level.OFF)

            return_code = obj.compare()

            # Restore original log levels
            yaml_logger.set_level(yaml_level)
            compare_logger.set_level(compare_level)

        except (CompareException, PyWLSTException), te:
            return_code = 2
            # self._logger.severe('WLSDPLY-05709', te.getLocalizedMessage(), error=te,
            #                     class_name=self._program_name, method_name=_method_name)

        if os.path.exists(_temp_dir):
            shutil.rmtree(_temp_dir)

        self.assertNotEqual(return_code, 0)

    def testDeleteModelAppDeployments(self):
        _method_name = 'testCompareModelFull'

        _variables_file = self._resources_dir + '/compare_model_model1.10.properties'
        _new_model_file = self._resources_dir + '/compare_model_model5.yaml'
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
            stdout_result = obj.get_compare_msgs()
            model_dictionary = FileToPython(yaml_result).parse()
            yaml_exists = os.path.exists(yaml_result)

            self.assertEqual(yaml_exists, True)
            self.assertEqual(len(stdout_result), 0)

            self.assertEqual(model_dictionary.has_key('appDeployments'), True)
            self.assertEqual(model_dictionary['appDeployments'].has_key('Library'), True)
            self.assertEqual(model_dictionary['appDeployments'].has_key('Application'), True)
            self.assertEqual(model_dictionary['appDeployments']['Application'].has_key('!myear'), True)
            self.assertEqual(model_dictionary['appDeployments']['Library'].has_key('!jax-rs#2.0@2.22.4.0'), True)
            self.assertEqual(model_dictionary['appDeployments']['Library'].has_key('!jsf#1.2@1.2.9.0'), True)

        except (CompareException, PyWLSTException), te:
            return_code = 2
            self._logger.severe('WLSDPLY-05709',
                                te.getLocalizedMessage(), error=te,
                                class_name=self._program_name, method_name=_method_name)

        if os.path.exists(_temp_dir):
            shutil.rmtree(_temp_dir)

        self.assertEqual(return_code, 0)

    def testCompareModelFull2(self):
        _method_name = 'testCompareModelFull2'

        _variables_file = self._resources_dir + '/compare_model_model1.10.properties'
        _new_model_file = self._resources_dir + '/compare_model_model7.yaml'
        _old_model_file = self._resources_dir + '/compare_model_model6.yaml'
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
            self.assertEqual(len(stdout_result), 0)

            self.assertEqual(model_dictionary.has_key('domainInfo'), True)
            self.assertEqual(model_dictionary['domainInfo'].has_key('AdminPassword'), True)
            self.assertEqual(model_dictionary['domainInfo']['AdminPassword'], 'welcome2')
            self.assertEqual(model_dictionary['domainInfo'].has_key('AdminUser'), False)
            self.assertEqual(model_dictionary['domainInfo'].has_key('RCUDbInfo'), True)
            self.assertEqual(model_dictionary['domainInfo']['RCUDbInfo'].has_key('rcu_admin_password'), True)
            self.assertEqual(len(model_dictionary['domainInfo']['RCUDbInfo']), 1)
            self.assertEqual(len(model_dictionary['domainInfo']), 2)
            self.assertEqual(model_dictionary.has_key('appDeployments'), True)
            self.assertEqual(model_dictionary['appDeployments'].has_key('Application'), True)
            self.assertEqual(model_dictionary['appDeployments']['Application'].has_key('!yourear'), True)
            self.assertEqual(len(model_dictionary['appDeployments']['Application']), 1)


        except (CompareException, PyWLSTException), te:
            return_code = 2
            self._logger.severe('WLSDPLY-05709',
                                te.getLocalizedMessage(), error=te,
                                class_name=self._program_name, method_name=_method_name)

        if os.path.exists(_temp_dir):
            shutil.rmtree(_temp_dir)

        self.assertEqual(return_code, 0)


if __name__ == '__main__':
    unittest.main()
